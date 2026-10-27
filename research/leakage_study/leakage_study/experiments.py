"""Experiment orchestration: Exp 1 (real Pima), Exp 2 (canary), Exp 3 (diagnostics), Exp 4 (simulation)."""
from __future__ import annotations

import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from joblib import Parallel, delayed
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split

from .canary import canary_flags, run_canary
from .data import FEATURES
from .metrics import leak_attribution_share, summarise
from .models import make_model
from .regimes import apply_regime, fill_median
from .runner import SEED_MOD, run_grid
from .simulate import calibrate, simulate_dataset
from .splits import make_splits
from .stats import nb_corrected_ci, plain_ci, wilson


def load_config(path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def save_df(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, compression="gzip" if path.suffix == ".gz" else None)


# --------------------------------------------------------------------------- Exp 1
def paired_series(metrics: pd.DataFrame, model: str, metric: str, a: tuple[str, str], b: tuple[str, str]) -> pd.Series:
    """Per-split paired difference metric[a] - metric[b] for one model; a, b = (regime, eval)."""
    m = metrics[metrics["model"] == model]
    pa = m[(m["regime"] == a[0]) & (m["eval"] == a[1])].set_index("split")[metric]
    pb = m[(m["regime"] == b[0]) & (m["eval"] == b[1])].set_index("split")[metric]
    return (pa - pb).dropna()


def contrast_table(metrics: pd.DataFrame, n_train: int, n_test: int, metric: str = "auc") -> pd.DataFrame:
    """E1-E4 contrasts with Nadeau-Bengio corrected CIs, per model."""
    specs = {
        "E1_apparent_inflation_Reg-3_vs_Reg-0": (("Reg-3", "app"), ("Reg-0", "app")),
        "E4_label_effect_Reg-2_vs_Reg-0": (("Reg-2", "app"), ("Reg-0", "app")),
        "E4_scope_effect_Reg-1_vs_Reg-0": (("Reg-1", "app"), ("Reg-0", "app")),
        "E2_gap_Reg-0": (("Reg-0", "app"), ("Reg-0", "dep")),
        "E2_gap_Reg-1": (("Reg-1", "app"), ("Reg-1", "dep")),
        "E2_gap_Reg-2": (("Reg-2", "app"), ("Reg-2", "dep")),
        "E2_gap_Reg-3": (("Reg-3", "app"), ("Reg-3", "dep")),
        "E3_harm_Reg-1": (("Reg-1", "dep"), ("Reg-0", "dep")),
        "E3_harm_Reg-2": (("Reg-2", "dep"), ("Reg-0", "dep")),
        "E3_harm_Reg-3": (("Reg-3", "dep"), ("Reg-0", "dep")),
    }
    rows = []
    for model in sorted(metrics["model"].unique()):
        for name, (a, b) in specs.items():
            s = paired_series(metrics, model, metric, a, b)
            if len(s) >= 2:
                rows.append({"model": model, "contrast": name, "metric": metric, **nb_corrected_ci(s.to_numpy(), n_train, n_test)})
        # E4 interaction
        i3 = paired_series(metrics, model, metric, ("Reg-3", "app"), ("Reg-2", "app"))
        i1 = paired_series(metrics, model, metric, ("Reg-1", "app"), ("Reg-0", "app"))
        inter = (i3 - i1).dropna()
        if len(inter) >= 2:
            rows.append({"model": model, "contrast": "E4_interaction", "metric": metric, **nb_corrected_ci(inter.to_numpy(), n_train, n_test)})
    # H2: model dependence of E1 (RF-default minus LR)
    if {"RF-default", "LR"} <= set(metrics["model"]):
        e_rf = paired_series(metrics, "RF-default", metric, ("Reg-3", "app"), ("Reg-0", "app"))
        e_lr = paired_series(metrics, "LR", metric, ("Reg-3", "app"), ("Reg-0", "app"))
        dd = (e_rf - e_lr).dropna()
        if len(dd) >= 2:
            rows.append({"model": "RF-default minus LR", "contrast": "H2_E1_difference", "metric": metric, **nb_corrected_ci(dd.to_numpy(), n_train, n_test)})
    return pd.DataFrame(rows)


def run_exp1(X, y, cfg: dict) -> dict:
    splits = make_splits(y, cfg["n_splits"], cfg["master_seed"], cfg.get("test_size", 0.2))
    preds, imp, timing = run_grid(X, y, splits, cfg["regimes"], cfg["models"], tuple(cfg.get("importance_models", ())),
                                  cfg.get("importance_repeats", 10), cfg.get("n_jobs", 1), FEATURES)
    metrics = summarise(preds)
    n_test = len(splits[0].test_idx)
    contrasts = contrast_table(metrics, len(splits[0].train_idx), n_test)
    return {"splits": splits, "preds": preds, "metrics": metrics, "importance": imp, "timing": timing, "contrasts": contrasts}


# --------------------------------------------------------------------------- Exp 2
def run_exp2(X, y, cfg: dict) -> dict:
    splits = make_splits(y, cfg["n_splits_total"], cfg["master_seed"], cfg.get("test_size", 0.2))[: cfg["n_splits_used"]]
    df = run_canary(X, y, splits, cfg["regimes"], cfg["models"], cfg["n_perm"], cfg["master_seed"], cfg.get("n_jobs", 1))
    flags = canary_flags(df)
    det = []
    for (model, regime), g in flags.groupby(["model", "regime"]):
        k, n = int(g["flagged"].sum()), len(g)
        lo, hi = wilson(k, n)
        det.append({"model": model, "regime": regime, "flagged": k, "n_splits": n, "rate": k / n, "wilson_lo": lo, "wilson_hi": hi,
                    "mean_perm_auc": float(g["mean_perm_auc"].mean())})
    return {"permuted": df, "flags": flags, "detection": pd.DataFrame(det)}


# --------------------------------------------------------------------------- Exp 3
def run_exp3(exp1: dict) -> pd.DataFrame:
    """Leak-attribution share (from permutation importance) and calibration slope by regime and model."""
    imp = exp1["importance"]
    if imp.empty:
        return pd.DataFrame()
    rows = []
    for (s, r, m), g in imp.groupby(["split", "regime", "model"]):
        vec = g.set_index("feature").loc[FEATURES, "importance"].to_numpy()
        rows.append({"split": s, "regime": r, "model": m, "LAS": leak_attribution_share(vec)})
    las = pd.DataFrame(rows)
    app = exp1["metrics"][exp1["metrics"]["eval"] == "app"][["split", "regime", "model", "cal_slope", "cal_intercept", "brier"]]
    return las.merge(app, on=["split", "regime", "model"], how="left")


# --------------------------------------------------------------------------- Exp 4
def sim_replicate(params, n: int, pi: float, mechanism: str, models, regimes, seed_seq, truth_n: int, cell_id: int, rep: int) -> list[dict]:
    rng = np.random.default_rng(seed_seq)
    sim = simulate_dataset(params, n, pi, mechanism, rng)
    sp_seed = int(rng.integers(0, SEED_MOD))
    tr, te = train_test_split(np.arange(n), test_size=0.2, stratify=sim.y, random_state=sp_seed)
    truth = simulate_dataset(params, truth_n, pi, mechanism, np.random.default_rng(int(rng.integers(0, 2**62))))
    oracle = float(roc_auc_score(truth.y, truth.eta))
    rows = []
    for regime in regimes:
        imp = apply_regime(regime, sim.X, sim.y, tr, te)
        x_truth = fill_median(truth.X, imp.med_train)  # deployment: label-free training medians
        for model in models:
            pipe = make_model(model, sp_seed)
            pipe.fit(imp.X_train, sim.y[tr])
            p_app = pipe.predict_proba(imp.X_test_app)[:, 1]
            p_dep = pipe.predict_proba(imp.X_test_dep)[:, 1]
            p_tru = pipe.predict_proba(x_truth)[:, 1]
            yt = sim.y[te]
            rows.append({"cell": cell_id, "rep": rep, "n": n, "pi": pi, "mechanism": mechanism, "target_auc": params.target_auc, "regime": regime, "model": model,
                         "auc_app": float(roc_auc_score(yt, p_app)), "auc_dep": float(roc_auc_score(yt, p_dep)), "auc_truth": float(roc_auc_score(truth.y, p_tru)),
                         "brier_app": float(brier_score_loss(yt, p_app)), "brier_truth": float(brier_score_loss(truth.y, p_tru)), "oracle_auc_truth": oracle,
                         "miss_frac_high": float(np.isnan(sim.X[:, 3]).mean())})
    return rows


def run_exp4(corr: np.ndarray, cfg: dict) -> dict:
    cells = list(itertools.product(cfg["pi"], cfg["mechanism"], cfg["target_auc"], cfg["n"]))
    params_cache = {a: calibrate(corr, a, cfg.get("prevalence", 0.35)) for a in cfg["target_auc"]}
    tasks = []
    for cid, (pi, mech, auc, n) in enumerate(cells):
        seqs = np.random.SeedSequence([cfg["master_seed"], 4, cid]).spawn(cfg["reps"])
        for rep, sq in enumerate(seqs):
            tasks.append((params_cache[auc], n, pi, mech, sq, cid, rep))
    res = Parallel(n_jobs=cfg.get("n_jobs", 1))(delayed(sim_replicate)(p, n, pi, mech, cfg["models"], cfg["regimes"], sq, cfg.get("truth_n", 20000), cid, rep)
                                                for p, n, pi, mech, sq, cid, rep in tasks)
    runs = pd.DataFrame([r for chunk in res for r in chunk]).sort_values(["cell", "rep", "regime", "model"], kind="mergesort").reset_index(drop=True)
    return {"runs": runs, "contrasts": sim_contrasts(runs), "calibration": {str(a): {"kappa": p.kappa, "b0": p.b0} for a, p in params_cache.items()}}


def sim_contrasts(runs: pd.DataFrame) -> pd.DataFrame:
    keys = ["cell", "n", "pi", "mechanism", "target_auc", "model"]
    rows = []
    for key, g in runs.groupby(keys):
        w = g.pivot(index="rep", columns="regime", values=["auc_app", "auc_dep", "auc_truth"])
        base = {k: v for k, v in zip(keys, key, strict=True)}
        specs = {"E1_inflation_Reg-3_vs_Reg-0": w["auc_app"]["Reg-3"] - w["auc_app"]["Reg-0"], "E1_label_Reg-2_vs_Reg-0": w["auc_app"]["Reg-2"] - w["auc_app"]["Reg-0"],
                 "E1_scope_Reg-1_vs_Reg-0": w["auc_app"]["Reg-1"] - w["auc_app"]["Reg-0"],
                 "E2_gap_Reg-3": w["auc_app"]["Reg-3"] - w["auc_truth"]["Reg-3"], "E3_harm_Reg-3": w["auc_truth"]["Reg-3"] - w["auc_truth"]["Reg-0"]}
        for name, s in specs.items():
            if s.notna().sum() >= 2:
                rows.append({**base, "contrast": name, **plain_ci(s.to_numpy())})
    return pd.DataFrame(rows)


def write_json(obj, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, default=str), encoding="utf-8")

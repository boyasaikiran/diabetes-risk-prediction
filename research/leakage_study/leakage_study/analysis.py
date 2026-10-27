"""Pre-registered decision rules (PREREG_DRAFT.md section 4) as code. Written and tested BEFORE the full-run results were inspected.

Where the frozen plan's wording left room, the operationalisation below was fixed before unblinding and is listed in
FULL_RUN_REPORT.md under 'Operationalisations of the frozen plan':
  * SESOI = 0.02 ROC-AUC (as frozen).
  * H1 uses the Nadeau-Bengio-corrected 95% CI of E1 for RF-default: confirmed if lower > SESOI, refuted if upper < SESOI, else inconclusive.
  * H2: confirmed if the corrected CI of E1(RF-default) - E1(LR) excludes 0 on the positive side; refuted if its upper bound <= 0.
  * H3: confirmed if the CI of (label effect - scope effect) for RF-default is above 0 AND the CI of the interaction lies within +/- SESOI.
  * H4: confirmed if E2 (RF-default) has lower bound > SESOI for Reg-2 and Reg-3 AND the CIs for Reg-0 and Reg-1 lie within +/- SESOI.
  * H5: confirmed if mean E1 at pi = 0 is within +/- 0.005 in every simulation group AND, for RF-default and HGB, mean E1 is non-decreasing in pi in every group (LR descriptive).
  * H6: 'flexible' models = RF-default, RF-regularised, HGB. Confirmed if, for every flexible model, detection rate >= 0.90 for Reg-2 and Reg-3 and <= 0.05 for Reg-0 and Reg-1.
  * Holm family (supplementary): one-sided Nadeau-Bengio t-test p-values for H2, H3, H4(Reg-2), H4(Reg-3) (against their stated bounds). H6 and H5 are decision-rule based and outside the Holm family.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as sps

from .experiments import paired_series
from .stats import holm, nb_corrected_ci

SESOI = 0.02
FLEXIBLE = ("RF-default", "RF-regularised", "HGB")


def h1_status(lo: float, hi: float, sesoi: float = SESOI) -> str:
    if lo > sesoi:
        return "confirmed"
    if hi < sesoi:
        return "refuted"
    return "inconclusive"


def p_one_sided(diffs, n_train: int, n_test: int, null: float = 0.0) -> float:
    """One-sided (greater than `null`) Nadeau-Bengio-corrected t-test p-value for the mean of paired per-split differences."""
    ci = nb_corrected_ci(diffs, n_train, n_test)
    t = (ci["mean"] - null) / ci["se_corrected"]
    return float(1 - sps.t.cdf(t, ci["J"] - 1))


def within(lo: float, hi: float, bound: float = SESOI) -> bool:
    return lo >= -bound and hi <= bound


def sim_contrasts_correct(runs: pd.DataFrame) -> pd.DataFrame:
    """Simulation contrasts recomputed from the raw runs, preserving the dataset size `n`.

    The frozen `experiments.sim_contrasts` (code tag leakage-code-v0.1.1) has a labelling defect: `plain_ci` returns a key `n`
    (number of replicates) that overwrites the dataset size `n` in the output table. The per-cell numbers (mean, CIs) are correct;
    only the `n` column of results/exp4/contrasts.csv is wrong. Found by the independent report verifier on toy data, before any
    full-run result was inspected. This function is used for all reported Exp 4 analysis instead.
    """
    from .stats import plain_ci

    keys = ["cell", "n", "pi", "mechanism", "target_auc", "model"]
    rows = []
    for key, g in runs.groupby(keys):
        w = g.pivot(index="rep", columns="regime", values=["auc_app", "auc_dep", "auc_truth"])
        base = dict(zip(keys, key, strict=True))
        specs = {"E1_inflation_Reg-3_vs_Reg-0": w["auc_app"]["Reg-3"] - w["auc_app"]["Reg-0"], "E1_label_Reg-2_vs_Reg-0": w["auc_app"]["Reg-2"] - w["auc_app"]["Reg-0"],
                 "E1_scope_Reg-1_vs_Reg-0": w["auc_app"]["Reg-1"] - w["auc_app"]["Reg-0"],
                 "E2_gap_Reg-3": w["auc_app"]["Reg-3"] - w["auc_truth"]["Reg-3"], "E3_harm_Reg-3": w["auc_truth"]["Reg-3"] - w["auc_truth"]["Reg-0"]}
        for name, s in specs.items():
            if s.notna().sum() >= 2:
                ci = plain_ci(s.to_numpy())
                rows.append({**base, "contrast": name, "mean": ci["mean"], "sd": ci["sd"], "se": ci["se"], "lo": ci["lo"], "hi": ci["hi"], "n_reps": ci["n"]})
    return pd.DataFrame(rows)


def exp1_decisions(metrics: pd.DataFrame, n_train: int, n_test: int, metric: str = "auc") -> dict:
    """H1-H4 on the real-data metrics table (columns split, regime, model, eval, <metric>)."""
    ps = lambda m, a, b: paired_series(metrics, m, metric, a, b)  # noqa: E731
    out: dict = {}
    e1 = {m: ps(m, ("Reg-3", "app"), ("Reg-0", "app")) for m in sorted(metrics["model"].unique())}
    c = nb_corrected_ci(e1["RF-default"].to_numpy(), n_train, n_test)
    out["H1"] = {"contrast": "E1 RF-default (Reg-3 app - Reg-0 app), ROC-AUC", **c, "status": h1_status(c["lo"], c["hi"])}

    d2 = (e1["RF-default"] - e1["LR"]).dropna()
    c2 = nb_corrected_ci(d2.to_numpy(), n_train, n_test)
    out["H2"] = {"contrast": "E1(RF-default) - E1(LR)", **c2, "p_one_sided": p_one_sided(d2.to_numpy(), n_train, n_test),
                 "status": "confirmed" if c2["lo"] > 0 else ("refuted" if c2["hi"] <= 0 else "inconclusive")}

    rf = "RF-default"
    label = ps(rf, ("Reg-2", "app"), ("Reg-0", "app"))
    scope = ps(rf, ("Reg-1", "app"), ("Reg-0", "app"))
    inter = (ps(rf, ("Reg-3", "app"), ("Reg-2", "app")) - scope).dropna()
    d3 = (label - scope).dropna()
    c3, ci3 = nb_corrected_ci(d3.to_numpy(), n_train, n_test), nb_corrected_ci(inter.to_numpy(), n_train, n_test)
    ok3 = c3["lo"] > 0 and within(ci3["lo"], ci3["hi"])
    out["H3"] = {"label_minus_scope": c3, "interaction": ci3, "p_one_sided": p_one_sided(d3.to_numpy(), n_train, n_test),
                 "status": "confirmed" if ok3 else ("refuted" if c3["hi"] <= 0 else "not confirmed")}

    gaps = {r: ps(rf, (r, "app"), (r, "dep")) for r in ("Reg-0", "Reg-1", "Reg-2", "Reg-3")}
    gc = {r: nb_corrected_ci(s.to_numpy(), n_train, n_test) for r, s in gaps.items()}
    ok4 = gc["Reg-2"]["lo"] > SESOI and gc["Reg-3"]["lo"] > SESOI and within(gc["Reg-0"]["lo"], gc["Reg-0"]["hi"]) and within(gc["Reg-1"]["lo"], gc["Reg-1"]["hi"])
    out["H4"] = {"gap_ci": gc, "p_reg2_gt_sesoi": p_one_sided(gaps["Reg-2"].to_numpy(), n_train, n_test, SESOI),
                 "p_reg3_gt_sesoi": p_one_sided(gaps["Reg-3"].to_numpy(), n_train, n_test, SESOI), "status": "confirmed" if ok4 else "not confirmed"}
    fam = [out["H2"]["p_one_sided"], out["H3"]["p_one_sided"], out["H4"]["p_reg2_gt_sesoi"], out["H4"]["p_reg3_gt_sesoi"]]
    adj = holm(fam)
    out["holm"] = {"family": ["H2", "H3", "H4_Reg-2", "H4_Reg-3"], "raw_p": fam, "adjusted_p": adj}
    return out


def exp2_decision(detection: pd.DataFrame) -> dict:
    """H6 on the detection table (columns model, regime, flagged, n_splits, rate, wilson_lo, wilson_hi)."""
    rows, ok = [], True
    for m in FLEXIBLE:
        d = detection[detection["model"] == m].set_index("regime")
        tpr = {r: float(d.loc[r, "rate"]) for r in ("Reg-2", "Reg-3")}
        fpr = {r: float(d.loc[r, "rate"]) for r in ("Reg-0", "Reg-1")}
        good = all(v >= 0.90 for v in tpr.values()) and all(v <= 0.05 for v in fpr.values())
        ok &= good
        rows.append({"model": m, "tpr": tpr, "fpr": fpr, "meets_thresholds": good})
    return {"flexible_models": rows, "status": "confirmed" if ok else "not confirmed"}


def exp4_h5(contrasts: pd.DataFrame) -> dict:
    """H5 on simulation contrasts (columns n, pi, mechanism, target_auc, model, contrast, mean, ...)."""
    c = contrasts[contrasts["contrast"] == "E1_inflation_Reg-3_vs_Reg-0"]
    groups, bad_zero, bad_mono = [], [], []
    for (n, mech, auc, model), g in c.groupby(["n", "mechanism", "target_auc", "model"]):
        g = g.sort_values("pi")
        means = g["mean"].to_numpy()
        zero_ok = abs(float(g[g["pi"] == 0.0]["mean"].iloc[0])) <= 0.005
        mono_ok = bool(np.all(np.diff(means) >= 0))
        groups.append({"n": int(n), "mechanism": mech, "target_auc": float(auc), "model": model, "zero_ok": zero_ok, "monotone_nondecreasing": mono_ok})
        if not zero_ok:
            bad_zero.append((n, mech, auc, model))
        if not mono_ok and model in ("RF-default", "HGB"):
            bad_mono.append((n, mech, auc, model))
    return {"groups": groups, "n_groups": len(groups), "pi0_violations": bad_zero, "monotone_violations_flexible": bad_mono,
            "status": "confirmed" if not bad_zero and not bad_mono else "not confirmed"}

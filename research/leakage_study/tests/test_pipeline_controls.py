"""Test groups 5 (determinism), 6 (negative controls), 7 (canary on noise), 9 (round trip) and experiment plumbing."""
import numpy as np
import pandas as pd
import pytest
from leakage_study.canary import canary_flags, run_canary
from leakage_study.data import complete_case_mask, load_pima
from leakage_study.experiments import contrast_table, run_exp1, run_exp3
from leakage_study.metrics import summarise
from leakage_study.regimes import REGIMES, apply_regime
from leakage_study.runner import run_grid
from leakage_study.splits import make_splits

FOUR = ["Reg-0", "Reg-1", "Reg-2", "Reg-3"]


# ---------------- 5. determinism
def test_same_seed_same_predictions_and_parallelism_does_not_matter(toy):
    X, y = toy
    sp = make_splits(y, 2, 7)
    a, _, _ = run_grid(X, y, sp, FOUR, ["LR", "RF-regularised"], n_jobs=1)
    b, _, _ = run_grid(X, y, sp, FOUR, ["LR", "RF-regularised"], n_jobs=2)
    pd.testing.assert_frame_equal(a, b)
    c, _, _ = run_grid(X, y, make_splits(y, 2, 8), FOUR, ["LR", "RF-regularised"])
    assert not np.array_equal(a["p"].to_numpy(), c["p"].to_numpy())


# ---------------- 6. negative controls
def _identical_across_regimes(preds):
    wide = preds.pivot_table(index=["split", "model", "eval", "row"], columns="regime", values="p")
    return float(wide.sub(wide["Reg-0"], axis=0).abs().to_numpy().max())


def test_no_missing_cells_means_all_regimes_coincide(toy_complete):
    X, y = toy_complete
    sp = make_splits(y, 2, 3)
    for name in REGIMES:
        r = apply_regime(name, X, y, sp[0].train_idx, sp[0].test_idx)
        r0 = apply_regime("Reg-0", X, y, sp[0].train_idx, sp[0].test_idx)
        assert np.array_equal(r.X_train, r0.X_train) and np.array_equal(r.X_test_app, r0.X_test_app)
    preds, _, _ = run_grid(X, y, sp, FOUR, ["LR", "RF-regularised"])
    assert _identical_across_regimes(preds) == 0.0


def test_real_pima_complete_cases_coincide_across_regimes():
    try:
        X, y = load_pima()
    except FileNotFoundError:
        pytest.skip("Pima data not downloaded")
    cc = complete_case_mask(X)
    preds, _, _ = run_grid(X[cc], y[cc], make_splits(y[cc], 2, 4), FOUR, ["LR"])
    assert _identical_across_regimes(preds) == 0.0


# ---------------- 7. canary
def _noise(n=300, miss=0.0, seed=0):
    rng = np.random.default_rng(seed)
    X, y = rng.normal(size=(n, 8)), (rng.random(n) < 0.4).astype(int)
    for j in (3, 4):
        X[rng.random(n) < miss, j] = np.nan
    return X, y


def test_canary_is_chance_on_noise_without_missing_values():
    X, y = _noise()
    sp = make_splits(y, 1, 1)
    df = run_canary(X, y, sp, FOUR, ["LR", "RF-regularised"], n_perm=12, master_seed=5)
    assert (df.groupby(["model", "regime"])["auc"].mean() - 0.5).abs().max() < 0.07


def test_canary_detects_label_aware_imputation_for_flexible_model_only():
    X, y = _noise(miss=0.5)
    sp = make_splits(y, 1, 1)
    df = run_canary(X, y, sp, FOUR, ["RF-default"], n_perm=6, master_seed=5)
    m = df.groupby("regime")["auc"].mean()
    assert m["Reg-3"] > 0.7 and m["Reg-2"] > 0.7        # label-aware: leaks even though labels are noise
    assert m["Reg-0"] < 0.6 and m["Reg-1"] < 0.6        # label-free: chance


def test_canary_flag_rule():
    rows = [{"split": 0, "regime": r, "model": "M", "perm": i, "auc": a + 0.01 * (i % 3 - 1)} for r, a in [("Reg-0", 0.5), ("Reg-1", 0.5), ("Reg-3", 0.8)] for i in range(10)]
    f = canary_flags(pd.DataFrame(rows))
    assert f.set_index("regime")["flagged"].to_dict() == {"Reg-0": False, "Reg-1": False, "Reg-3": True}


# ---------------- 9. round trip and plumbing
def test_metrics_recomputable_from_saved_predictions(toy, tmp_path):
    X, y = toy
    preds, _, _ = run_grid(X, y, make_splits(y, 2, 11), FOUR, ["LR", "RF-regularised"])
    m1 = summarise(preds)
    preds.to_csv(tmp_path / "p.csv.gz", index=False, compression="gzip")
    m2 = summarise(pd.read_csv(tmp_path / "p.csv.gz"))
    pd.testing.assert_frame_equal(m1.reset_index(drop=True), m2.reset_index(drop=True), check_exact=False, atol=1e-12)


def test_exp1_contrasts_and_diagnostics_run(toy):
    X, y = toy
    cfg = {"n_splits": 4, "master_seed": 2, "regimes": FOUR, "models": ["LR", "RF-default"], "importance_models": ["LR"], "importance_repeats": 2, "n_jobs": 1}
    r = run_exp1(X, y, cfg)
    assert {"E1_apparent_inflation_Reg-3_vs_Reg-0", "E2_gap_Reg-3", "E3_harm_Reg-3", "E4_interaction"} <= set(r["contrasts"]["contrast"])
    assert {"LR", "RF-default minus LR"} <= set(r["contrasts"]["model"])
    d = run_exp3(r)
    assert {"LAS", "cal_slope"} <= set(d.columns) and len(d) == 4 * 4
    assert contrast_table(r["metrics"], 240, 60)["se_corrected"].notna().all()

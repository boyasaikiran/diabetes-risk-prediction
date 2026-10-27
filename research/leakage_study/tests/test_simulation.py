"""Test group 8: generator checks (prevalence, oracle AUC, missing fractions, MCAR vs MNAR) and Exp 4 plumbing."""
import numpy as np
import pytest
from leakage_study.experiments import run_exp4
from leakage_study.simulate import BETA, calibrate, mnar_probs, sigmoid, simulate_dataset
from sklearn.metrics import roc_auc_score

CORR = 0.3 ** np.abs(np.subtract.outer(np.arange(8), np.arange(8)))   # AR(1) correlation


@pytest.fixture(scope="module")
def params():
    return calibrate(CORR, 0.80, 0.35, n_aux=100_000)


def test_oracle_auc_and_prevalence(params):
    sim = simulate_dataset(params, 60_000, 0.0, "MCAR", np.random.default_rng(1))
    assert abs(sim.y.mean() - 0.35) < 0.01
    assert abs(roc_auc_score(sim.y, sim.eta) - 0.80) < 0.01
    assert BETA.shape == (8,) and 0 < sigmoid(0.0) < 1


def test_pi_zero_has_no_missing_cells(params):
    for mech in ("MCAR", "MNAR"):
        assert not np.isnan(simulate_dataset(params, 5000, 0.0, mech, np.random.default_rng(2)).X).any()


def test_missing_fractions_and_mechanisms(params):
    mc = simulate_dataset(params, 60_000, 0.5, "MCAR", np.random.default_rng(3))
    mn = simulate_dataset(params, 60_000, 0.5, "MNAR", np.random.default_rng(4))
    for s in (mc, mn):
        assert abs(np.isnan(s.X[:, 3]).mean() - 0.5) < 0.02 and abs(np.isnan(s.X[:, 4]).mean() - 0.5) < 0.02
        assert abs(np.isnan(s.X[:, 1]).mean() - 0.03) < 0.01 and np.isnan(s.X[:, 0]).sum() == 0
    r1, r0 = np.isnan(mc.X[mc.y == 1, 3]).mean(), np.isnan(mc.X[mc.y == 0, 3]).mean()
    assert abs(r1 - r0) < 0.02                                   # MCAR: no outcome dependence
    m1, m0 = np.isnan(mn.X[mn.y == 1, 3]).mean(), np.isnan(mn.X[mn.y == 0, 3]).mean()
    assert abs((m1 / (1 - m1)) / (m0 / (1 - m0)) - 1.5) < 0.15   # MNAR: odds ratio 1.5


def test_mnar_probs_hit_target_rate():
    p0, p1 = mnar_probs(0.4, 0.35)
    assert 0.65 * p0 + 0.35 * p1 == pytest.approx(0.4, abs=1e-9)
    assert (p1 / (1 - p1)) / (p0 / (1 - p0)) == pytest.approx(1.5, rel=1e-6)


def test_exp4_plumbing_and_negative_control_a():
    cfg = {"master_seed": 3, "pi": [0.0, 0.5], "mechanism": ["MCAR"], "target_auc": [0.8], "n": [400], "regimes": ["Reg-0", "Reg-1", "Reg-2", "Reg-3"],
           "models": ["LR", "RF-regularised"], "reps": 3, "truth_n": 2000, "prevalence": 0.35, "n_jobs": 1}
    out = run_exp4(CORR, cfg)
    runs = out["runs"]
    z = runs[runs["pi"] == 0.0].pivot_table(index=["rep", "model"], columns="regime", values="auc_app")
    assert float(z.sub(z["Reg-0"], axis=0).abs().to_numpy().max()) < 1e-12      # negative control A
    assert {"E1_inflation_Reg-3_vs_Reg-0", "E2_gap_Reg-3", "E3_harm_Reg-3"} <= set(out["contrasts"]["contrast"])
    assert len(runs) == 2 * 3 * 4 * 2


def test_frozen_sim_contrasts_n_defect_is_pinned_and_corrected_version_fixes_it():
    """Pins the known labelling defect in the frozen summary code and checks the corrected recomputation."""
    from leakage_study.analysis import sim_contrasts_correct

    cfg = {"master_seed": 4, "pi": [0.5], "mechanism": ["MCAR"], "target_auc": [0.8], "n": [400, 500], "regimes": ["Reg-0", "Reg-1", "Reg-2", "Reg-3"],
           "models": ["LR"], "reps": 3, "truth_n": 1000, "prevalence": 0.35, "n_jobs": 1}
    out = run_exp4(CORR, cfg)
    frozen, fixed = out["contrasts"], sim_contrasts_correct(out["runs"])
    assert set(frozen["n"]) == {3}                       # defect: replicate count instead of dataset size
    assert set(fixed["n"]) == {400, 500} and set(fixed["n_reps"]) == {3}
    cols = ["cell", "pi", "mechanism", "target_auc", "model", "contrast", "mean", "sd", "lo", "hi"]
    a = frozen[cols].sort_values(cols[:6]).reset_index(drop=True)
    b = fixed[cols].sort_values(cols[:6]).reset_index(drop=True)
    assert a.equals(b) or np.allclose(a[["mean", "sd", "lo", "hi"]].to_numpy(), b[["mean", "sd", "lo", "hi"]].to_numpy(), atol=1e-15)

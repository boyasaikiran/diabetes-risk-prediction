"""Smoke test of audit-free analysis + independent report verification on SYNTHETIC toy results (never on study output)."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from leakage_study.experiments import run_exp1, run_exp2, run_exp3, run_exp4, save_df, write_json  # noqa: E402

CORR = 0.3 ** np.abs(np.subtract.outer(np.arange(8), np.arange(8)))


@pytest.fixture(scope="module")
def mini_results(tmp_path_factory, toy):
    X, y = toy
    res = tmp_path_factory.mktemp("results")
    c1 = {"master_seed": 5, "n_splits": 8, "test_size": 0.2, "regimes": ["Reg-0", "Reg-1", "Reg-2", "Reg-3"], "models": ["LR", "RF-default"], "importance_models": ["LR"], "importance_repeats": 2, "n_jobs": 1}
    r = run_exp1(X, y, c1)
    save_df(r["preds"], res / "exp1/predictions.csv.gz")
    for k in ("metrics", "importance", "timing", "contrasts"):
        save_df(r[k], res / f"exp1/{k}.csv")
    save_df(run_exp3(r), res / "exp1/exp3_diagnostics.csv")
    write_json({"config": c1}, res / "exp1/run_config.json")
    c2 = {"master_seed": 5, "n_splits_total": 8, "n_splits_used": 4, "test_size": 0.2, "n_perm": 6, "regimes": c1["regimes"], "models": ["LR", "RF-default", "RF-regularised", "HGB"], "n_jobs": 1}
    e2 = run_exp2(X, y, c2)
    save_df(e2["permuted"], res / "exp2/permuted_auc.csv.gz")
    save_df(e2["flags"], res / "exp2/flags.csv")
    save_df(e2["detection"], res / "exp2/detection.csv")
    write_json({"config": c2}, res / "exp2/run_config.json")
    c4 = {"master_seed": 5, "pi": [0.0, 0.5], "mechanism": ["MCAR", "MNAR"], "target_auc": [0.8], "n": [300, 400], "regimes": c1["regimes"], "models": ["LR", "RF-default", "HGB"],
          "reps": 3, "truth_n": 1000, "prevalence": 0.35, "n_jobs": 1}
    e4 = run_exp4(CORR, c4)
    save_df(e4["runs"], res / "exp4/runs.csv.gz")
    save_df(e4["contrasts"], res / "exp4/contrasts.csv")
    write_json(e4["calibration"], res / "exp4/calibration.json")
    write_json({"config": c4}, res / "exp4/run_config.json")
    return res


def test_analysis_chain_and_independent_verification(mini_results, tmp_path):
    import analyze
    import verify_report

    out, reports = tmp_path / "analysis", tmp_path / "reports"
    analyze.main(mini_results, out, reports, n_total=300, test_mode=True)
    for f in ("EXP1_REPORT.md", "EXP2_REPORT.md", "EXP4_REPORT.md", "FULL_RUN_REPORT.md"):
        txt = (reports / f).read_text(encoding="utf-8")
        assert "TEST MODE" in txt and len(txt) > 500
    assert (out / "decisions.json").exists() and (out / "figures/fig2_exp1_apparent_vs_deployment.png").exists()
    dec = json.loads((out / "decisions.json").read_text(encoding="utf-8"))
    assert dec["H1"]["status"] in ("confirmed", "refuted", "inconclusive")
    assert verify_report.main(mini_results, reports, out, 300) == 0
    summary = json.loads((out / "REPORT_VERIFICATION.json").read_text(encoding="utf-8"))
    assert summary["n_checks"] >= 25 and summary["n_failed"] == 0


def test_analyze_refuses_to_run_without_a_passing_audit(mini_results, tmp_path):
    import analyze

    with pytest.raises(SystemExit):
        analyze.main(mini_results, tmp_path / "a", tmp_path / "r", n_total=300, test_mode=False)

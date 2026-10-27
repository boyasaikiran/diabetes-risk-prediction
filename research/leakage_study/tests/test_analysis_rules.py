"""Tests of the frozen decision rules on synthetic inputs (run before unblinding the full-run results)."""
import numpy as np
import pandas as pd
import pytest
from leakage_study.analysis import exp1_decisions, exp2_decision, exp4_h5, h1_status, p_one_sided, within


def test_h1_three_way_rule():
    assert h1_status(0.03, 0.12) == "confirmed"
    assert h1_status(0.005, 0.015) == "refuted"
    assert h1_status(0.01, 0.05) == "inconclusive"
    assert h1_status(0.02, 0.05) == "inconclusive"   # lower bound exactly at SESOI is not "> SESOI"


def test_within_bounds():
    assert within(-0.01, 0.015) and not within(-0.03, 0.01) and not within(-0.01, 0.03)


def test_one_sided_p_values_behave():
    d = np.random.default_rng(0).normal(0.1, 0.01, 100)
    assert p_one_sided(d, 614, 154) < 1e-6
    assert p_one_sided(-d, 614, 154) > 0.99
    assert 0.0 < p_one_sided(d, 614, 154, null=0.1) < 1.0


def _metrics(effect_rf, effect_lr, label_share=1.0, gap_rf=None):
    rng = np.random.default_rng(1)
    rows = []
    for s in range(60):
        base = 0.84 + rng.normal(0, 0.005)
        for model, eff in (("RF-default", effect_rf), ("LR", effect_lr)):
            e = eff + rng.normal(0, 0.005)
            vals = {("Reg-0", "app"): base, ("Reg-0", "dep"): base, ("Reg-1", "app"): base, ("Reg-1", "dep"): base,
                    ("Reg-2", "app"): base + e * label_share, ("Reg-2", "dep"): base - (gap_rf if gap_rf is not None else e),
                    ("Reg-3", "app"): base + e, ("Reg-3", "dep"): base - (gap_rf if gap_rf is not None else e)}
            # make Reg-2/3 deployment gap equal to the apparent inflation when gap_rf is None
            if gap_rf is None:
                vals[("Reg-2", "dep")] = base
                vals[("Reg-3", "dep")] = base
            for (reg, ev), v in vals.items():
                rows.append({"split": s, "regime": reg, "model": model, "eval": ev, "auc": v})
    return pd.DataFrame(rows)


def test_exp1_decisions_confirm_a_large_flexible_model_effect():
    d = exp1_decisions(_metrics(0.10, 0.02), 614, 154)
    assert d["H1"]["status"] == "confirmed" and d["H2"]["status"] == "confirmed"
    assert d["H3"]["status"] == "confirmed" and d["H4"]["status"] == "confirmed"
    assert len(d["holm"]["adjusted_p"]) == 4 and all(a >= r for a, r in zip(d["holm"]["adjusted_p"], d["holm"]["raw_p"], strict=True))


def test_exp1_decisions_refute_when_effect_is_negligible():
    assert exp1_decisions(_metrics(0.001, 0.001), 614, 154)["H1"]["status"] == "refuted"


def test_exp1_h2_not_confirmed_when_models_equal():
    assert exp1_decisions(_metrics(0.10, 0.10), 614, 154)["H2"]["status"] != "confirmed"


def test_h6_rule():
    rows = []
    for m in ("RF-default", "RF-regularised", "HGB"):
        for r, rate in (("Reg-0", 0.0), ("Reg-1", 0.0), ("Reg-2", 1.0), ("Reg-3", 1.0)):
            rows.append({"model": m, "regime": r, "rate": rate})
    det = pd.DataFrame(rows)
    assert exp2_decision(det)["status"] == "confirmed"
    det.loc[(det["model"] == "HGB") & (det["regime"] == "Reg-3"), "rate"] = 0.8
    assert exp2_decision(det)["status"] == "not confirmed"


def test_h5_rule():
    rows = []
    for model in ("RF-default", "HGB", "LR"):
        for pi, mean in zip([0, 0.1, 0.25, 0.5, 0.75], [0.0, 0.03, 0.07, 0.12, 0.2], strict=True):
            rows.append({"n": 768, "mechanism": "MCAR", "target_auc": 0.8, "model": model, "pi": pi, "contrast": "E1_inflation_Reg-3_vs_Reg-0", "mean": mean})
    c = pd.DataFrame(rows)
    assert exp4_h5(c)["status"] == "confirmed"
    c.loc[(c["model"] == "RF-default") & (c["pi"] == 0.5), "mean"] = 0.01
    assert exp4_h5(c)["status"] == "not confirmed"
    c2 = pd.DataFrame(rows)
    c2.loc[(c2["model"] == "LR") & (c2["pi"] == 0.0), "mean"] = 0.03
    assert exp4_h5(c2)["status"] == "not confirmed"
    assert pytest.approx(0.0) == 0.0

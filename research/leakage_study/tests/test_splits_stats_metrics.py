"""Test groups 3 (split integrity), 4 (metric references) and the statistics helpers."""
import math

import numpy as np
import pytest
from leakage_study.metrics import calibration_intercept_slope, leak_attribution_share, metric_row, sens_spec
from leakage_study.splits import make_splits
from leakage_study.stats import holm, nb_corrected_ci, plain_ci, wilson
from scipy import stats as sps


# ---------------- splits
def test_split_integrity(toy):
    _, y = toy
    sp = make_splits(y, 10, 5, 0.2)
    for s in sp:
        assert len(set(s.train_idx) & set(s.test_idx)) == 0
        assert len(s.train_idx) + len(s.test_idx) == len(y)
        assert abs(y[s.train_idx].mean() - y[s.test_idx].mean()) < 0.03   # stratified
        assert len(s.test_idx) == round(0.2 * len(y))


def test_splits_reproducible_and_distinct(toy):
    _, y = toy
    a, b, c = make_splits(y, 5, 5), make_splits(y, 5, 5), make_splits(y, 5, 6)
    assert all(np.array_equal(x.test_idx, z.test_idx) for x, z in zip(a, b, strict=True))
    assert not all(np.array_equal(x.test_idx, z.test_idx) for x, z in zip(a, c, strict=True))
    assert len({s.seed for s in a}) == 5
    assert not np.array_equal(a[0].test_idx, a[1].test_idx)


def test_prefix_of_splits_is_stable(toy):
    """Exp 2 uses the first splits of the Exp 1 list: the list must not depend on how many are requested."""
    _, y = toy
    assert np.array_equal(make_splits(y, 3, 9)[2].test_idx, make_splits(y, 10, 9)[2].test_idx)


# ---------------- metric references
def test_reference_auc_pr_brier():
    y, p = np.array([0, 0, 1, 1]), np.array([0.1, 0.4, 0.35, 0.8])
    m = metric_row(y, p, 0.5)
    assert m["auc"] == pytest.approx(0.75)
    assert m["pr_auc"] == pytest.approx(5 / 6)
    assert m["brier"] == pytest.approx(((0.1) ** 2 + (0.4) ** 2 + (0.65) ** 2 + (0.2) ** 2) / 4)


def test_sens_spec_hand_example():
    y, p = np.array([1, 1, 0, 0, 0]), np.array([0.9, 0.4, 0.6, 0.2, 0.1])
    assert sens_spec(y, p, 0.5) == (pytest.approx(0.5), pytest.approx(2 / 3))


def test_calibration_slope_ideal_and_overconfident():
    rng = np.random.default_rng(0)
    p = rng.uniform(0.05, 0.95, 40000)
    y = (rng.random(40000) < p).astype(int)
    a, b = calibration_intercept_slope(y, p)
    assert abs(a) < 0.1 and abs(b - 1) < 0.1
    logit = np.log(p / (1 - p))
    over = 1 / (1 + np.exp(-2 * logit))
    assert abs(calibration_intercept_slope(y, over)[1] - 0.5) < 0.1


def test_leak_attribution_share():
    names = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"]
    imp = np.array([0.1, 0.4, 0.0, 0.2, 0.1, 0.1, 0.0, 0.1])
    assert leak_attribution_share(imp, names) == pytest.approx(0.3 / 1.0)
    assert math.isnan(leak_attribution_share(np.zeros(8), names))


# ---------------- statistics
def test_nadeau_bengio_known_values():
    d = [0.1, 0.2, 0.3]
    r = nb_corrected_ci(d, n_train=80, n_test=20)
    se = math.sqrt((1 / 3 + 0.25) * 0.01)
    t = sps.t.ppf(0.975, 2)
    assert r["mean"] == pytest.approx(0.2) and r["se_corrected"] == pytest.approx(se)
    assert r["lo"] == pytest.approx(0.2 - t * se) and r["hi"] == pytest.approx(0.2 + t * se)


def test_nb_is_wider_than_naive_interval():
    d = np.random.default_rng(1).normal(0.1, 0.02, 100)
    naive = plain_ci(d)
    nb = nb_corrected_ci(d, 614, 154)
    assert (nb["hi"] - nb["lo"]) > 2.5 * (naive["hi"] - naive["lo"])


def test_wilson_and_holm():
    lo, hi = wilson(0, 10)
    assert lo == pytest.approx(0.0, abs=1e-9) and hi == pytest.approx(0.2775, abs=1e-3)
    assert holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])

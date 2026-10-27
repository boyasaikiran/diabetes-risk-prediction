import numpy as np

from src.evaluate import bootstrap_ci, compute_metrics
from src.train import choose_threshold


def test_metrics_known_values():
    m = compute_metrics([0, 0, 1, 1], [0.1, 0.6, 0.4, 0.9], 0.5)
    assert m["confusion_matrix"] == {"tn": 1, "fp": 1, "fn": 1, "tp": 1}
    assert m["accuracy"] == 0.5 and m["specificity"] == 0.5 and m["recall_sensitivity"] == 0.5


def test_threshold_meets_target_sensitivity():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 400)
    p = np.clip(y * 0.3 + rng.uniform(0, 0.7, 400), 0, 1)
    t = choose_threshold(y, p, 0.8)
    assert ((p >= t) & (y == 1)).sum() / (y == 1).sum() >= 0.8


def test_bootstrap_ci_brackets_estimate():
    rng = np.random.default_rng(1)
    y = rng.integers(0, 2, 200)
    p = np.clip(y * 0.4 + rng.uniform(0, 0.6, 200), 0, 1)
    lo, hi = bootstrap_ci(y, p, 0.5, n=200)["roc_auc"]
    assert lo <= compute_metrics(y, p, 0.5)["roc_auc"] <= hi

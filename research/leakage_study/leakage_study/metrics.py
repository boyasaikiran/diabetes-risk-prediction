"""Metrics (STAGE6_DESIGN.md section 5)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score

from .data import FEATURES, LEAK_FEATURES


def calibration_intercept_slope(y: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    """Logistic recalibration logit P(y=1) = a + b*logit(p). Ideal: a = 0, b = 1."""
    p = np.clip(np.asarray(p, float), 1e-6, 1 - 1e-6)
    z = np.log(p / (1 - p)).reshape(-1, 1)
    lr = LogisticRegression(penalty=None, max_iter=1000).fit(z, y)
    return float(lr.intercept_[0]), float(lr.coef_[0, 0])


def sens_spec(y: np.ndarray, p: np.ndarray, tau: float) -> tuple[float, float]:
    pred = p >= tau
    pos, neg = y == 1, y == 0
    sens = float((pred & pos).sum() / pos.sum()) if pos.any() else float("nan")
    spec = float((~pred & neg).sum() / neg.sum()) if neg.any() else float("nan")
    return sens, spec


def metric_row(y: np.ndarray, p: np.ndarray, train_prev: float) -> dict:
    a, b = calibration_intercept_slope(y, p)
    s5, c5 = sens_spec(y, p, 0.5)
    sp, cp = sens_spec(y, p, train_prev)
    return {"auc": float(roc_auc_score(y, p)), "pr_auc": float(average_precision_score(y, p)), "brier": float(brier_score_loss(y, p)),
            "cal_intercept": a, "cal_slope": b, "sens_0.5": s5, "spec_0.5": c5, "sens_prev": sp, "spec_prev": cp}


KEYS = ["split", "regime", "model", "eval"]


def summarise(preds: pd.DataFrame) -> pd.DataFrame:
    """Metrics per (split, regime, model, eval) from the per-row prediction table (so anything is recomputable)."""
    rows = []
    for key, g in preds.groupby(KEYS, sort=True):
        rows.append({**dict(zip(KEYS, key, strict=True)), **metric_row(g["y"].to_numpy(), g["p"].to_numpy(), float(g["train_prev"].iloc[0]))})
    return pd.DataFrame(rows)


def importance_mean(pipe, X_test: np.ndarray, y_test: np.ndarray, n_repeats: int, seed: int) -> np.ndarray:
    """Mean ROC-AUC drop when each feature is shuffled on the held-out rows."""
    r = permutation_importance(pipe, X_test, y_test, scoring="roc_auc", n_repeats=n_repeats, random_state=seed, n_jobs=1)
    return r.importances_mean


def leak_attribution_share(imp: np.ndarray, feature_names: list[str] | None = None) -> float:
    """(importance of Insulin + SkinThickness, floored at 0) / (sum of positive importances)."""
    names = feature_names or FEATURES
    pos = np.clip(imp, 0, None)
    total = pos.sum()
    if total <= 0:
        return float("nan")
    return float(sum(pos[names.index(f)] for f in LEAK_FEATURES) / total)

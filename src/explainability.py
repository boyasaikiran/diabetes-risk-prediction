"""Local explanations of individual predictions.

SHAP (permutation explainer) is applied to the *full* saved pipeline's
predicted probability, so attributions correspond to the actual model output.
Attributions are additive in probability units relative to the average
prediction over a training background sample. They describe how the model
used each input, NOT causes of diabetes.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from src.validation import FIELD_SPECS

log = logging.getLogger(__name__)


def _occlusion(model, x: pd.DataFrame, background: pd.DataFrame) -> np.ndarray:
    """Fallback: effect of replacing each feature by the background median."""
    base = float(model.predict_proba(x)[0, 1])
    med = background.median()
    out = []
    for c in x.columns:
        xc = x.copy()
        xc[c] = med[c]
        out.append(base - float(model.predict_proba(xc)[0, 1]))
    return np.asarray(out)


def explain_prediction(model, x: pd.DataFrame, background: pd.DataFrame, seed: int = 42) -> dict:
    """Return per-feature probability contributions for a single-row frame."""
    cols = list(x.columns)
    method = "shap-permutation"
    try:
        import shap

        def f(a: np.ndarray) -> np.ndarray:
            return model.predict_proba(pd.DataFrame(a, columns=cols))[:, 1]

        masker = shap.maskers.Independent(background[cols].to_numpy(float), max_samples=100)
        ex = shap.explainers.Permutation(f, masker, seed=seed)
        sv = ex(x.to_numpy(float), max_evals=20 * len(cols) + 1)
        contrib = np.asarray(sv.values)[0]
        base = float(np.asarray(sv.base_values).ravel()[0])
    except Exception:  # noqa: BLE001 - degrade gracefully, never expose internals
        log.warning("SHAP unavailable; using occlusion fallback", exc_info=True)
        method = "occlusion"
        contrib = _occlusion(model, x, background)
        base = float(model.predict_proba(x)[0, 1] - contrib.sum())

    items = []
    for c, v in zip(cols, contrib, strict=True):
        val = x.iloc[0][c]
        items.append({
            "feature": c,
            "label": FIELD_SPECS[c].label,
            "value": None if pd.isna(val) else float(val),
            "contribution": float(v),
            "direction": "raises" if v > 0 else "lowers" if v < 0 else "neutral",
            "imputed": bool(pd.isna(val)),
        })
    items.sort(key=lambda d: abs(d["contribution"]), reverse=True)
    return {"method": method, "base_value": base, "contributions": items,
            "plain_language": plain_language(items)}


def plain_language(items: list[dict], top: int = 3) -> str:
    """Short, non-causal summary of the largest contributions."""
    parts = []
    for it in items[:top]:
        if abs(it["contribution"]) < 0.005:
            continue
        note = " (not provided; typical value assumed)" if it["imputed"] else ""
        parts.append(
            f"{it['label']}{note} {it['direction']} the model's estimate by about "
            f"{abs(it['contribution']) * 100:.0f} percentage points"
        )
    if not parts:
        return "No single input moved the model's estimate noticeably."
    return ("; ".join(parts) + ". These are statistical associations learned by the model "
            "from one specific dataset, not causes.")

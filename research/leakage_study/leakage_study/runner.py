"""Fit each (split, regime, model) once; evaluate on both the apparent (App) and deployment (Dep) held-out matrices."""
from __future__ import annotations

import time

import pandas as pd
from joblib import Parallel, delayed

from .metrics import importance_mean
from .models import make_model
from .regimes import apply_regime
from .splits import Split

SEED_MOD = 2**31 - 1


def fit_task(X, y, split: Split, regime: str, model: str, importance: bool, n_repeats: int) -> dict:
    t0 = time.perf_counter()
    imp = apply_regime(regime, X, y, split.train_idx, split.test_idx)
    pipe = make_model(model, split.seed % SEED_MOD)
    pipe.fit(imp.X_train, y[split.train_idx])
    t_fit = time.perf_counter() - t0
    y_te = y[split.test_idx]
    prev = float(y[split.train_idx].mean())
    out = {"preds": [], "imp": None, "timing": (split.index, regime, model, t_fit, 0.0)}
    for ev, Xe in (("app", imp.X_test_app), ("dep", imp.X_test_dep)):
        p = pipe.predict_proba(Xe)[:, 1]
        out["preds"].append(pd.DataFrame({"split": split.index, "regime": regime, "model": model, "eval": ev, "row": split.test_idx, "y": y_te, "p": p, "train_prev": prev}))
    if importance:
        t1 = time.perf_counter()
        out["imp"] = (split.index, regime, model, importance_mean(pipe, imp.X_test_app, y_te, n_repeats, split.seed % SEED_MOD))
        out["timing"] = (split.index, regime, model, t_fit, time.perf_counter() - t1)
    return out


def run_grid(X, y, splits, regimes, models, importance_models=(), n_repeats: int = 10, n_jobs: int = 1, feature_names=None):
    """Returns (preds, importance, timing) DataFrames; output order is deterministic and independent of n_jobs."""
    tasks = [(s, r, m) for s in splits for r in regimes for m in models]
    res = Parallel(n_jobs=n_jobs)(delayed(fit_task)(X, y, s, r, m, m in importance_models, n_repeats) for s, r, m in tasks)
    preds = pd.concat([d for out in res for d in out["preds"]], ignore_index=True)
    preds = preds.sort_values(["split", "regime", "model", "eval", "row"], kind="mergesort").reset_index(drop=True)
    names = feature_names or [f"f{j}" for j in range(X.shape[1])]
    imp_rows = []
    for out in res:
        if out["imp"] is not None:
            s, r, m, v = out["imp"]
            imp_rows += [{"split": s, "regime": r, "model": m, "feature": names[j], "importance": float(v[j])} for j in range(len(v))]
    importance = pd.DataFrame(imp_rows)
    timing = pd.DataFrame([o["timing"] for o in res], columns=["split", "regime", "model", "fit_s", "importance_s"])
    return preds, importance, timing

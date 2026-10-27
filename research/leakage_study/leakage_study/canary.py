"""Label-permutation canary (STAGE6_DESIGN.md Exp 2).

Permute the outcome labels globally, then apply the regime and the split exactly as in Exp 1. A pipeline whose
preprocessing does not use labels should score about 0.5 on permuted labels; label-dependent preprocessing lets a
flexible model score well above 0.5 even though the labels are noise.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.metrics import roc_auc_score

from .models import make_model
from .regimes import apply_regime
from .splits import Split

SEED_MOD = 2**31 - 1


def permuted_label_aucs(X, y, split: Split, regime: str, model: str, n_perm: int, master_seed: int) -> list[dict]:
    rows = []
    for i in range(n_perm):
        # identical permutation for every regime/model given (split, i): comparisons are paired
        rng = np.random.default_rng(np.random.SeedSequence([master_seed, 2, split.index, i]))
        yp = rng.permutation(y)
        imp = apply_regime(regime, X, yp, split.train_idx, split.test_idx)
        pipe = make_model(model, split.seed % SEED_MOD)
        pipe.fit(imp.X_train, yp[split.train_idx])
        yt = yp[split.test_idx]
        auc = float(roc_auc_score(yt, pipe.predict_proba(imp.X_test_app)[:, 1])) if len(np.unique(yt)) == 2 else float("nan")
        rows.append({"split": split.index, "regime": regime, "model": model, "perm": i, "auc": auc})
    return rows


def run_canary(X, y, splits, regimes, models, n_perm: int, master_seed: int, n_jobs: int = 1) -> pd.DataFrame:
    res = Parallel(n_jobs=n_jobs)(delayed(permuted_label_aucs)(X, y, s, r, m, n_perm, master_seed) for s in splits for r in regimes for m in models)
    df = pd.DataFrame([r for chunk in res for r in chunk])
    return df.sort_values(["model", "regime", "split", "perm"], kind="mergesort").reset_index(drop=True)


def canary_flags(df: pd.DataFrame, k: float = 2.0, reference: str = "Reg-0") -> pd.DataFrame:
    """Pre-registered rule: for each model, mu0 and sigma0 are the mean and SD of permuted-label AUC for the Reg-0 reference;
    a (split, regime, model) cell is flagged if its mean permuted AUC over permutations exceeds mu0 + k*sigma0."""
    out = []
    for model, g in df.groupby("model"):
        ref = g[g["regime"] == reference]["auc"].dropna()
        mu0, sd0 = float(ref.mean()), float(ref.std(ddof=1))
        thr = mu0 + k * sd0
        for (regime, split), h in g.groupby(["regime", "split"]):
            m = float(h["auc"].mean())
            out.append({"model": model, "regime": regime, "split": split, "mean_perm_auc": m, "threshold": thr, "flagged": bool(m > thr)})
    return pd.DataFrame(out)

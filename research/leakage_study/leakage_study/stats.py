"""Statistical helpers (STAGE6_DESIGN.md section 6)."""
from __future__ import annotations

import math

import numpy as np
from scipy import stats as sps


def nb_corrected_ci(diffs, n_train: int, n_test: int, alpha: float = 0.05) -> dict:
    """Nadeau-Bengio corrected CI for the mean of paired per-split differences from J repeated random subsampling splits.
    Var_corrected = (1/J + n_test/n_train) * s^2 ; t with J-1 degrees of freedom."""
    d = np.asarray(diffs, float)
    d = d[~np.isnan(d)]
    j = len(d)
    if j < 2:
        raise ValueError("need at least 2 splits")
    s2 = float(d.var(ddof=1))
    se = math.sqrt((1 / j + n_test / n_train) * s2)
    t = float(sps.t.ppf(1 - alpha / 2, j - 1))
    m = float(d.mean())
    return {"mean": m, "sd": math.sqrt(s2), "se_corrected": se, "lo": m - t * se, "hi": m + t * se, "J": j}


def plain_ci(values, alpha: float = 0.05) -> dict:
    """Ordinary CI for the mean of INDEPENDENT replicates (simulation)."""
    v = np.asarray(values, float)
    v = v[~np.isnan(v)]
    n = len(v)
    se = float(v.std(ddof=1) / math.sqrt(n))
    t = float(sps.t.ppf(1 - alpha / 2, n - 1))
    return {"mean": float(v.mean()), "sd": float(v.std(ddof=1)), "se": se, "lo": float(v.mean() - t * se), "hi": float(v.mean() + t * se), "n": n}


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return centre - half, centre + half


def holm(pvals) -> list[float]:
    """Holm-adjusted p-values (monotone)."""
    p = np.asarray(pvals, float)
    order = np.argsort(p)
    m = len(p)
    adj = np.empty(m)
    run = 0.0
    for rank, i in enumerate(order):
        run = max(run, (m - rank) * p[i])
        adj[i] = min(1.0, run)
    return adj.tolist()

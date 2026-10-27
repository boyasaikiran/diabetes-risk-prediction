"""Controlled simulation generator (STAGE6_DESIGN.md section 8). Synthetic data: no clinical claims.

Features ~ multivariate normal (correlation matrix supplied; for the study it is estimated from Pima complete cases,
parameters only, no rows copied). Outcome ~ Bernoulli(sigmoid(b0 + kappa * beta'x)); kappa is calibrated so that the
oracle (complete-data) AUC equals the target and b0 so that prevalence equals the target prevalence.
Missingness: features 3,4 (skin-fold, insulin analogues) at rate pi; features 1,2,5 at LOW_RATE (0 when pi == 0, so
pi = 0 is a true no-missing negative control). Mechanism MCAR, or outcome-dependent MNAR (odds ratio 1.5 for positives).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.metrics import roc_auc_score

# standardised LR coefficient pattern from the project's saved model (Stage 1/5): order = data.FEATURES
BETA = np.array([0.309, 0.992, 0.025, 0.071, 0.024, 0.575, 0.248, 0.188])
HIGH_IDX = (3, 4)
LOW_IDX = (1, 2, 5)
LOW_RATE = 0.03
MNAR_ODDS_RATIO = 1.5


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


@dataclass
class SimParams:
    corr: np.ndarray
    kappa: float
    b0: float
    target_auc: float
    prevalence: float


@dataclass
class Simulated:
    X: np.ndarray   # observed (NaN = missing)
    y: np.ndarray
    eta: np.ndarray  # true linear predictor (log-odds)


def estimate_corr(X: np.ndarray) -> np.ndarray:
    """Correlation matrix of the complete-case rows of X (parameters only)."""
    cc = X[~np.isnan(X).any(axis=1)]
    return np.corrcoef(cc, rowvar=False)


def _b0_for(kappa: float, s: np.ndarray, prevalence: float) -> float:
    lo, hi = -20.0, 20.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if sigmoid(mid + kappa * s).mean() < prevalence:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def calibrate(corr: np.ndarray, target_auc: float, prevalence: float = 0.35, n_aux: int = 200_000, seed: int = 12345) -> SimParams:
    rng = np.random.default_rng(seed)
    z = rng.multivariate_normal(np.zeros(corr.shape[0]), corr, n_aux)
    s = z @ BETA
    u = rng.random(n_aux)

    def oracle_auc(kappa: float) -> float:
        p = sigmoid(_b0_for(kappa, s, prevalence) + kappa * s)
        return float(roc_auc_score(u < p, p))

    lo, hi = 0.05, 8.0
    for _ in range(30):
        mid = (lo + hi) / 2
        if oracle_auc(mid) < target_auc:
            lo = mid
        else:
            hi = mid
    kappa = (lo + hi) / 2
    return SimParams(corr, kappa, _b0_for(kappa, s, prevalence), target_auc, prevalence)


def mnar_probs(pi: float, q: float, odds_ratio: float = MNAR_ODDS_RATIO) -> tuple[float, float]:
    """(p0, p1): missingness probabilities for y=0 / y=1 so that the overall rate is pi and the odds ratio is `odds_ratio`."""
    if pi <= 0:
        return 0.0, 0.0

    def p1_of(p0: float) -> float:
        return odds_ratio * p0 / ((1 - p0) + odds_ratio * p0)

    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if (1 - q) * mid + q * p1_of(mid) < pi:
            lo = mid
        else:
            hi = mid
    p0 = (lo + hi) / 2
    return p0, p1_of(p0)


def simulate_dataset(params: SimParams, n: int, pi: float, mechanism: str, rng: np.random.Generator) -> Simulated:
    if mechanism not in ("MCAR", "MNAR"):
        raise ValueError("mechanism must be MCAR or MNAR")
    z = rng.multivariate_normal(np.zeros(params.corr.shape[0]), params.corr, n)
    eta = params.b0 + params.kappa * (z @ BETA)
    y = (rng.random(n) < sigmoid(eta)).astype(int)
    X = z.copy()
    if mechanism == "MCAR":
        p0 = p1 = pi
    else:
        p0, p1 = mnar_probs(pi, float(y.mean()))
    pm = np.where(y == 1, p1, p0)
    for j in HIGH_IDX:
        X[rng.random(n) < pm, j] = np.nan
    low = LOW_RATE if pi > 0 else 0.0
    for j in LOW_IDX:
        X[rng.random(n) < low, j] = np.nan
    return Simulated(X, y, eta)

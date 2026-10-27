"""The five imputation regimes (PREREG_DRAFT.md section 2).

All functions operate on a float matrix X that already has NaN for missing cells.

Regime        statistics fitted on    uses held-out row's true label?
Reg-0         train rows              no     (valid reference)
Reg-1         all rows                no     (scope leak only)
Reg-2         train rows              YES    (label leak only)
Reg-3         all rows                YES    (published 'group median before split' practice)
Reg-4         train rows              no     (predicted class; deployable, exploratory)

Each regime returns the imputed training matrix and two versions of the held-out matrix:
  X_test_app  imputed by the regime's own rule (what a researcher using the regime would evaluate on)
  X_test_dep  imputed with label-free medians of the TRAINING rows (what happens for new patients)
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

REGIMES = ("Reg-0", "Reg-1", "Reg-2", "Reg-3", "Reg-4")


@dataclass
class Imputed:
    X_train: np.ndarray
    X_test_app: np.ndarray
    X_test_dep: np.ndarray
    med_train: np.ndarray  # label-free medians of the observed training values


def nanmedian(A: np.ndarray) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        return np.nanmedian(A, axis=0)


def fill_median(A: np.ndarray, med: np.ndarray) -> np.ndarray:
    out = A.copy()
    r, c = np.where(np.isnan(out))
    out[r, c] = med[c]
    return out


def class_medians(A: np.ndarray, labels: np.ndarray, fallback: np.ndarray) -> np.ndarray:
    """Per-class column medians of the observed values; shape (2, p). Empty cells fall back to `fallback`."""
    med = np.empty((2, A.shape[1]))
    for k in (0, 1):
        sub = A[labels == k]
        m = nanmedian(sub) if len(sub) else np.full(A.shape[1], np.nan)
        med[k] = np.where(np.isnan(m), fallback, m)
    return med


def fill_class(A: np.ndarray, labels: np.ndarray, med: np.ndarray) -> np.ndarray:
    out = A.copy()
    r, c = np.where(np.isnan(out))
    out[r, c] = med[labels[r], c]
    return out


def apply_regime(name: str, X: np.ndarray, y: np.ndarray, train_idx: np.ndarray, test_idx: np.ndarray) -> Imputed:
    """Impute according to a regime for one split. `y` is read ONLY where the regime says labels are used."""
    if name not in REGIMES:
        raise ValueError(f"unknown regime {name!r}")
    Xtr_raw, Xte_raw = X[train_idx], X[test_idx]
    med_train = nanmedian(Xtr_raw)
    if np.isnan(med_train).any():
        raise ValueError("a column is entirely missing in the training rows")
    dep = fill_median(Xte_raw, med_train)

    if name == "Reg-0":
        Xtr, app = fill_median(Xtr_raw, med_train), dep.copy()
    elif name == "Reg-1":
        med_all = nanmedian(X)
        Xtr, app = fill_median(Xtr_raw, med_all), fill_median(Xte_raw, med_all)
    elif name == "Reg-2":
        mc = class_medians(Xtr_raw, y[train_idx], med_train)
        Xtr, app = fill_class(Xtr_raw, y[train_idx], mc), fill_class(Xte_raw, y[test_idx], mc)  # held-out TRUE labels
    elif name == "Reg-3":
        mc = class_medians(X, y, med_train)  # all rows, all labels
        Xtr, app = fill_class(Xtr_raw, y[train_idx], mc), fill_class(Xte_raw, y[test_idx], mc)
    else:  # Reg-4: held-out class is PREDICTED from observed (median-filled) features only
        mc = class_medians(Xtr_raw, y[train_idx], med_train)
        first = StandardScaler().fit(fill_median(Xtr_raw, med_train))
        clf = LogisticRegression(C=1.0, max_iter=5000).fit(first.transform(fill_median(Xtr_raw, med_train)), y[train_idx])
        pred_class = clf.predict(first.transform(dep)).astype(int)
        Xtr, app = fill_class(Xtr_raw, y[train_idx], mc), fill_class(Xte_raw, pred_class, mc)
        dep = app.copy()
    if np.isnan(Xtr).any() or np.isnan(app).any() or np.isnan(dep).any():
        raise AssertionError("imputation left missing values")
    return Imputed(Xtr, app, dep, med_train)

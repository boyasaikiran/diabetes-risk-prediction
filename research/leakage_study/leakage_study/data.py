"""Data access: Pima Indians Diabetes Database with impossible zeros converted to NaN."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FEATURES = ["Pregnancies", "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI", "DiabetesPedigreeFunction", "Age"]
ZERO_COLS = ["Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"]
LEAK_FEATURES = ["Insulin", "SkinThickness"]
TARGET = "Outcome"


def load_pima(verify_hash: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """Return (X with NaN for impossible zeros, y as 0/1). Verifies the CSV against the recorded SHA-256."""
    csv = PROJECT_ROOT / "data" / "raw" / "pima_diabetes.csv"
    if verify_hash:
        prov = json.loads((PROJECT_ROOT / "data" / "raw" / "provenance.json").read_text(encoding="utf-8"))
        got = hashlib.sha256(csv.read_bytes()).hexdigest()
        if got != prov["sha256"]:
            raise ValueError("Pima CSV does not match the recorded SHA-256; refusing to run.")
    df = pd.read_csv(csv)
    X = df[FEATURES].to_numpy(float).copy()
    for c in ZERO_COLS:
        j = FEATURES.index(c)
        X[X[:, j] == 0, j] = np.nan
    return X, df[TARGET].to_numpy(int)


def complete_case_mask(X: np.ndarray) -> np.ndarray:
    """Rows with no missing cells (used for negative control B)."""
    return ~np.isnan(X).any(axis=1)

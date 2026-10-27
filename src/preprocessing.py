"""Preprocessing pipeline shared by training and inference.

In the Pima dataset a value of 0 for Glucose, BloodPressure, SkinThickness,
Insulin and BMI is physiologically impossible and denotes a missing
measurement. Pregnancies == 0 is valid and is left untouched.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.data_loader import FEATURES

ZERO_AS_MISSING: tuple[str, ...] = ("Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI")


class ZeroToNaN(BaseEstimator, TransformerMixin):
    """Convert impossible zeros to NaN for the configured columns (stateless)."""

    def __init__(self, columns: tuple[str, ...] = ZERO_AS_MISSING):
        self.columns = columns

    def fit(self, X, y=None):
        self.feature_names_in_ = np.asarray(list(X.columns), dtype=object)
        return self

    def transform(self, X):
        X = pd.DataFrame(X).copy()
        for c in self.columns:
            if c in X.columns:
                X.loc[X[c] == 0, c] = np.nan
        return X

    def get_feature_names_out(self, input_features=None):
        return np.asarray(self.feature_names_in_, dtype=object)


def build_preprocessor() -> Pipeline:
    """Zero->NaN, median imputation and scaling. Fit on training data only."""
    numeric = Pipeline(
        [("impute", SimpleImputer(strategy="median")), ("scale", StandardScaler())]
    )
    return Pipeline(
        [
            ("zero_to_nan", ZeroToNaN()),
            (
                "columns",
                ColumnTransformer([("num", numeric, FEATURES)], remainder="drop"),
            ),
        ]
    )


def build_model_pipeline(estimator) -> Pipeline:
    """Full pipeline: preprocessing + classifier, saved/loaded as one object."""
    return Pipeline([("prep", build_preprocessor()), ("clf", estimator)])

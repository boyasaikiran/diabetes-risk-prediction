"""Shared fixtures. All data here is SYNTHETIC, for software tests only;
it says nothing about clinical performance."""
import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from src.data_loader import FEATURES, TARGET
from src.preprocessing import build_model_pipeline


def synthetic_frame(n: int = 300, seed: int = 0) -> pd.DataFrame:
    r = np.random.default_rng(seed)
    df = pd.DataFrame({
        "Pregnancies": r.integers(0, 12, n), "Glucose": r.normal(120, 30, n).clip(50, 250),
        "BloodPressure": r.normal(70, 12, n).clip(40, 120), "SkinThickness": r.normal(25, 8, n).clip(8, 70),
        "Insulin": r.normal(100, 50, n).clip(15, 500), "BMI": r.normal(32, 6, n).clip(18, 60),
        "DiabetesPedigreeFunction": r.uniform(0.1, 1.5, n), "Age": r.integers(21, 70, n),
    }).astype(float)
    df[TARGET] = ((df.Glucose - 120) / 30 + r.normal(0, 1, n) > 0.3).astype(int)
    df.loc[df.sample(20, random_state=1).index, "Insulin"] = 0.0
    return df[[*FEATURES, TARGET]]


@pytest.fixture(scope="session")
def synth():
    return synthetic_frame()


@pytest.fixture(scope="session")
def model_dir(tmp_path_factory, synth):
    d = tmp_path_factory.mktemp("model")
    pipe = build_model_pipeline(LogisticRegression(max_iter=500)).fit(synth[FEATURES], synth[TARGET])
    meta = {
        "model_version": "test", "selected_model": "Logistic Regression", "calibrated": False,
        "feature_order": FEATURES, "threshold": 0.3, "training_prevalence": float(synth[TARGET].mean()),
        "feature_ranges": {f: [float(synth[f].min()), float(synth[f].max())] for f in FEATURES},
    }
    joblib.dump({"model": pipe, "background": synth[FEATURES].head(50), "metadata": meta}, d / "model.joblib")
    return d


@pytest.fixture(scope="session")
def predictor(model_dir):
    from src.predict import Predictor
    return Predictor(model_dir)


VALID = {"Pregnancies": 2, "Glucose": 130, "BloodPressure": 70, "SkinThickness": "", "Insulin": "",
         "BMI": 30.5, "DiabetesPedigreeFunction": 0.4, "Age": 40}

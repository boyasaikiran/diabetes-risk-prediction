"""Fixed, untuned model settings (STAGE6_DESIGN.md section 4)."""
from __future__ import annotations

from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

MODEL_NAMES = ("LR", "RF-default", "RF-regularised", "HGB", "SVM-RBF")


def make_model(name: str, seed: int) -> Pipeline:
    """Standard scaler (fitted on the imputed training rows) followed by the classifier."""
    if name == "LR":
        est = LogisticRegression(C=1.0, max_iter=5000)
    elif name == "RF-default":
        est = RandomForestClassifier(n_estimators=300, random_state=seed, n_jobs=1)
    elif name == "RF-regularised":
        est = RandomForestClassifier(n_estimators=300, max_depth=5, min_samples_leaf=8, random_state=seed, n_jobs=1)
    elif name == "HGB":
        est = HistGradientBoostingClassifier(random_state=seed)
    elif name == "SVM-RBF":
        est = CalibratedClassifierCV(SVC(C=1.0, gamma="scale", random_state=seed), method="sigmoid", ensemble=False, cv=3)
    else:
        raise ValueError(f"unknown model {name!r}")
    return Pipeline([("scale", StandardScaler()), ("clf", est)])

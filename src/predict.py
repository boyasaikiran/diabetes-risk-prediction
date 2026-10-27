"""Inference engine. Loads the saved pipeline; never trains at startup."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

import joblib
import pandas as pd

from src.config import load_config, resolve
from src.explainability import explain_prediction
from src.validation import validate_inputs

log = logging.getLogger(__name__)


class ModelNotFoundError(FileNotFoundError):
    """The trained model artifact is missing or unreadable."""


class InvalidInputError(ValueError):
    """Inputs failed validation; message is safe to show to users."""

    def __init__(self, message: str, errors: dict[str, str]):
        super().__init__(message)
        self.errors = errors


@dataclass
class Prediction:
    probability: float
    threshold: float
    above_threshold: bool
    inputs: dict[str, float]
    warnings: list[str] = field(default_factory=list)
    model_version: str = ""
    model_name: str = ""
    explanation: dict | None = None


class Predictor:
    def __init__(self, model_dir: Path | str | None = None):
        d = Path(model_dir) if model_dir else resolve(load_config()["paths"]["model_dir"])
        path = d / "model.joblib"
        if not path.exists():
            raise ModelNotFoundError(
                f"Trained model not found at {path}. Run `python -m src.train` first.")
        try:
            bundle = joblib.load(path)
            self.model = bundle["model"]
            self.background: pd.DataFrame = bundle["background"]
            self.metadata: dict = bundle["metadata"]
        except Exception as exc:  # noqa: BLE001
            log.error("Model load failed: %s", type(exc).__name__)
            raise ModelNotFoundError("The model file could not be loaded; retrain it.") from exc
        self.features: list[str] = self.metadata["feature_order"]

    def _frame(self, values: dict[str, float]) -> pd.DataFrame:
        return pd.DataFrame([[values[f] for f in self.features]], columns=self.features)

    def _range_warnings(self, values: dict[str, float]) -> list[str]:
        out = []
        for f, v in values.items():
            lo, hi = self.metadata["feature_ranges"][f]
            if pd.notna(v) and not lo <= v <= hi:
                out.append(f"{f} is outside the range seen in training data "
                           f"({lo:g}–{hi:g}); the estimate is less reliable.")
        missing = [f for f, v in values.items() if pd.isna(v)]
        if missing:
            out.append("Not provided (replaced by training-set medians): " + ", ".join(missing))
        return out

    def predict(self, raw: dict, explain: bool = True) -> Prediction:
        res = validate_inputs(raw)
        if not res.ok:
            raise InvalidInputError(res.message(), res.errors)
        x = self._frame(res.values)
        proba = float(self.model.predict_proba(x)[0, 1])
        thr = float(self.metadata["threshold"])
        pred = Prediction(
            probability=proba, threshold=thr, above_threshold=proba >= thr,
            inputs=res.values, warnings=self._range_warnings(res.values),
            model_version=self.metadata["model_version"],
            model_name=self.metadata["selected_model"],
        )
        if explain:
            pred.explanation = explain_prediction(self.model, x, self.background)
        return pred

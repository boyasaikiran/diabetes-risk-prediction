import pytest

from src.data_loader import FEATURES
from src.explainability import _occlusion, explain_prediction
from src.predict import InvalidInputError, ModelNotFoundError, Predictor
from tests.conftest import VALID


def test_missing_model_artifact(tmp_path):
    with pytest.raises(ModelNotFoundError):
        Predictor(tmp_path)


def test_corrupt_model_artifact(tmp_path):
    (tmp_path / "model.joblib").write_bytes(b"junk")
    with pytest.raises(ModelNotFoundError):
        Predictor(tmp_path)


def test_feature_order_matches_schema(predictor):
    assert predictor.features == FEATURES
    assert list(predictor._frame({f: 1.0 for f in FEATURES}).columns) == FEATURES


def test_probability_in_range_and_threshold(predictor):
    r = predictor.predict(VALID, explain=False)
    assert 0.0 <= r.probability <= 1.0
    assert r.above_threshold == (r.probability >= r.threshold)


def test_invalid_input_raises_readable_error(predictor):
    with pytest.raises(InvalidInputError, match="Plasma glucose"):
        predictor.predict({**VALID, "Glucose": 9999})


def test_higher_glucose_not_lower_probability(predictor):
    lo = predictor.predict({**VALID, "Glucose": 90}, explain=False).probability
    hi = predictor.predict({**VALID, "Glucose": 200}, explain=False).probability
    assert hi > lo


def test_missing_optional_generates_warning(predictor):
    assert any("Not provided" in w for w in predictor.predict(VALID, explain=False).warnings)


def test_out_of_training_range_warns(predictor):
    r = predictor.predict({**VALID, "Glucose": 399}, explain=False)
    assert any("outside the range" in w for w in r.warnings)


def test_explanation_is_additive_and_matches_prediction(predictor):
    r = predictor.predict(VALID)
    ex = r.explanation
    assert {c["feature"] for c in ex["contributions"]} == set(FEATURES)
    total = ex["base_value"] + sum(c["contribution"] for c in ex["contributions"])
    assert total == pytest.approx(r.probability, abs=1e-6)
    assert "not causes" in ex["plain_language"]


def test_occlusion_fallback_runs(predictor):
    x = predictor._frame(predictor.predict(VALID, explain=False).inputs)
    assert len(_occlusion(predictor.model, x, predictor.background)) == len(FEATURES)


def test_shap_failure_falls_back(predictor, monkeypatch):
    import shap

    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(shap.explainers, "Permutation", boom)
    x = predictor._frame(predictor.predict(VALID, explain=False).inputs)
    assert explain_prediction(predictor.model, x, predictor.background)["method"] == "occlusion"

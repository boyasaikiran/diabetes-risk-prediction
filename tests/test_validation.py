import pytest

from src.validation import FIELD_SPECS, validate_inputs
from tests.conftest import VALID


def test_valid_input_ok():
    r = validate_inputs(VALID)
    assert r.ok and r.values["Glucose"] == 130
    assert r.values["Insulin"] != r.values["Insulin"]  # NaN, not zero


def test_missing_required_fields():
    r = validate_inputs({})
    assert set(r.errors) == {n for n, s in FIELD_SPECS.items() if s.required}


@pytest.mark.parametrize("field,val", [("Glucose", "abc"), ("Glucose", True), ("Age", float("nan")),
                                       ("BMI", float("inf")), ("Age", [1])])
def test_invalid_types_rejected(field, val):
    assert field in validate_inputs({**VALID, field: val}).errors


@pytest.mark.parametrize("field,val", [("Glucose", 5), ("Glucose", 900), ("BMI", 1), ("Age", 15),
                                       ("Age", 150), ("Pregnancies", -1)])
def test_out_of_range_rejected(field, val):
    assert field in validate_inputs({**VALID, field: val}).errors


def test_fractional_integer_rejected():
    assert "Age" in validate_inputs({**VALID, "Age": 40.5}).errors


def test_zero_not_silently_accepted_for_glucose():
    assert "Glucose" in validate_inputs({**VALID, "Glucose": 0}).errors


def test_unknown_fields_rejected():
    r = validate_inputs({**VALID, "Smoker": "yes"})
    assert not r.ok and r.unknown_fields == ["Smoker"]

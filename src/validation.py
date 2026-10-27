"""Input schema and validation for inference.

Ranges are plausibility limits for rejecting typos/unit errors, not clinical
reference ranges. Age is limited to 21+ because the training population is
adults aged 21 and over.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from src.data_loader import FEATURES


@dataclass(frozen=True)
class FieldSpec:
    name: str
    label: str
    unit: str
    help: str
    minimum: float
    maximum: float
    default: float
    required: bool
    integer: bool = False
    step: float = 1.0


FIELD_SPECS: dict[str, FieldSpec] = {
    s.name: s
    for s in [
        FieldSpec("Pregnancies", "Number of pregnancies", "count",
                  "Times pregnant. Dataset contains females only.", 0, 20, 1, True, True),
        FieldSpec("Glucose", "Plasma glucose (2-h OGTT)", "mg/dL",
                  "Glucose 2 hours after an oral glucose tolerance test. "
                  "Not the same as a fasting or random reading.", 40, 400, 110, True),
        FieldSpec("BloodPressure", "Diastolic blood pressure", "mm Hg",
                  "Optional. Leave blank if unknown.", 30, 140, 70, False),
        FieldSpec("SkinThickness", "Triceps skin-fold thickness", "mm",
                  "Optional. Rarely measured outside research; leave blank if unknown.",
                  5, 100, 20, False),
        FieldSpec("Insulin", "2-hour serum insulin", "mu U/ml",
                  "Optional. Leave blank if unknown.", 10, 900, 80, False),
        FieldSpec("BMI", "Body mass index", "kg/m²",
                  "Weight (kg) divided by height (m) squared.", 12, 70, 28, True, step=0.1),
        FieldSpec("DiabetesPedigreeFunction", "Diabetes pedigree function", "score",
                  "Optional. A study-specific score of diabetes in relatives; "
                  "not a standard clinical measure.", 0.05, 2.5, 0.4, False, step=0.01),
        FieldSpec("Age", "Age", "years",
                  "Training data covers adults aged 21 and over.", 21, 100, 35, True, True),
    ]
}
assert list(FIELD_SPECS) == FEATURES, "FIELD_SPECS must follow training feature order"


@dataclass
class ValidationResult:
    values: dict[str, float] = field(default_factory=dict)  # NaN = not provided
    errors: dict[str, str] = field(default_factory=dict)
    unknown_fields: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors and not self.unknown_fields

    def message(self) -> str:
        parts = [f"{FIELD_SPECS[k].label}: {v}" for k, v in self.errors.items()]
        if self.unknown_fields:
            parts.append(f"Unexpected fields: {', '.join(self.unknown_fields)}")
        return "; ".join(parts)


def _is_blank(v) -> bool:
    return v is None or (isinstance(v, str) and v.strip() == "") or (
        isinstance(v, float) and math.isnan(v)
    )


def validate_inputs(raw: dict) -> ValidationResult:
    """Validate a raw input mapping. Never silently substitutes zero."""
    res = ValidationResult()
    res.unknown_fields = sorted(set(raw) - set(FIELD_SPECS))
    for name, spec in FIELD_SPECS.items():
        v = raw.get(name)
        if _is_blank(v):
            if spec.required:
                res.errors[name] = "this field is required."
            res.values[name] = float("nan")
            continue
        if isinstance(v, bool):
            res.errors[name] = "must be a number."
            continue
        try:
            x = float(v)
        except (TypeError, ValueError):
            res.errors[name] = "must be a number."
            continue
        if math.isnan(x) or math.isinf(x):
            res.errors[name] = "must be a finite number."
        elif not spec.minimum <= x <= spec.maximum:
            res.errors[name] = (
                f"{x:g} is outside the accepted range {spec.minimum:g}–{spec.maximum:g} "
                f"{spec.unit}. Please check the value and unit."
            )
        elif spec.integer and x != int(x):
            res.errors[name] = "must be a whole number."
        else:
            res.values[name] = x
    return res

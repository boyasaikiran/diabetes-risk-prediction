"""Dataset acquisition, schema checking and profiling (Pima Indians Diabetes)."""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.config import load_config, resolve, setup_logging

log = logging.getLogger(__name__)

FEATURES: list[str] = [
    "Pregnancies",
    "Glucose",
    "BloodPressure",
    "SkinThickness",
    "Insulin",
    "BMI",
    "DiabetesPedigreeFunction",
    "Age",
]
TARGET = "Outcome"

# OpenML names -> project names
_OPENML_RENAME = {
    "preg": "Pregnancies",
    "plas": "Glucose",
    "pres": "BloodPressure",
    "skin": "SkinThickness",
    "insu": "Insulin",
    "mass": "BMI",
    "pedi": "DiabetesPedigreeFunction",
    "age": "Age",
    "class": TARGET,
}


class DatasetError(ValueError):
    """Raised when a dataset is empty or does not match the expected schema."""


def check_schema(df: pd.DataFrame, target: str = TARGET) -> None:
    """Validate that df has the expected columns, numeric types and binary target."""
    if df is None or df.empty:
        raise DatasetError("Dataset is empty.")
    missing = [c for c in [*FEATURES, target] if c not in df.columns]
    if missing:
        raise DatasetError(f"Dataset is missing expected columns: {missing}")
    for c in FEATURES:
        if not pd.api.types.is_numeric_dtype(df[c]):
            raise DatasetError(f"Column '{c}' must be numeric, got {df[c].dtype}.")
    if set(df[target].dropna().unique()) - {0, 1}:
        raise DatasetError(f"Target '{target}' must be binary 0/1.")
    if df[target].nunique() < 2:
        raise DatasetError("Target has only one class; cannot train a classifier.")


def download_pima(openml_id: int = 37) -> pd.DataFrame:
    """Download the dataset from OpenML (mirror of the UCI Pima database)."""
    from sklearn.datasets import fetch_openml

    bunch = fetch_openml(data_id=openml_id, as_frame=True, parser="auto")
    df = bunch.frame.rename(columns=_OPENML_RENAME)
    df[TARGET] = (df[TARGET].astype(str) == "tested_positive").astype(int)
    return df[[*FEATURES, TARGET]].astype({c: float for c in FEATURES})


def load_dataset(path: Path | str | None = None, download: bool = True) -> pd.DataFrame:
    """Load the dataset from disk, downloading and caching it if absent."""
    cfg = load_config()
    csv = Path(path) if path else resolve(cfg["paths"]["raw_data"])
    if not csv.exists():
        if not download:
            raise FileNotFoundError(f"Dataset not found at {csv}")
        log.info("Dataset not found locally; downloading from OpenML")
        df = download_pima(cfg["data"]["openml_id"])
        csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv, index=False)
        _write_provenance(csv, cfg["data"]["openml_id"], df)
    df = pd.read_csv(csv)
    check_schema(df)
    return df


def _write_provenance(csv: Path, openml_id: int, df: pd.DataFrame) -> None:
    info = {
        "name": "Pima Indians Diabetes Database",
        "original_owner": "National Institute of Diabetes and Digestive and Kidney Diseases",
        "donor": "Vincent Sigillito (Johns Hopkins APL), 1990",
        "obtained_via": f"OpenML data id {openml_id} (mirror of UCI)",
        "source_url": f"https://www.openml.org/d/{openml_id}",
        "uci_url": "https://archive.ics.uci.edu/ml/datasets/pima+indians+diabetes",
        "openml_license_field": "Public (verify terms at source before redistribution)",
        "downloaded_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "sha256": hashlib.sha256(csv.read_bytes()).hexdigest(),
        "rows": len(df),
    }
    (csv.parent / "provenance.json").write_text(json.dumps(info, indent=2), encoding="utf-8")


def profile_dataset(df: pd.DataFrame, zero_is_missing: list[str]) -> dict:
    """Data-quality profile: missing/zero counts, duplicates, class balance, ranges."""
    check_schema(df)
    zeros = {c: int((df[c] == 0).sum()) for c in FEATURES}
    return {
        "rows": int(len(df)),
        "duplicate_rows": int(df.duplicated().sum()),
        "null_cells": {c: int(df[c].isna().sum()) for c in FEATURES},
        "zero_counts": zeros,
        "zeros_treated_as_missing": {c: zeros[c] for c in zero_is_missing},
        "class_counts": {int(k): int(v) for k, v in df[TARGET].value_counts().items()},
        "prevalence": float(df[TARGET].mean()),
        "feature_summary": {
            c: {
                "min": float(df[c].min()),
                "median": float(df[c].median()),
                "max": float(df[c].max()),
            }
            for c in FEATURES
        },
    }


if __name__ == "__main__":
    setup_logging()
    data = load_dataset()
    print(json.dumps(profile_dataset(data, load_config()["data"]["zero_is_missing"]), indent=2))

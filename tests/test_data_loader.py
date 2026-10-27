import pandas as pd
import pytest

from src.data_loader import DatasetError, check_schema, load_dataset, profile_dataset


def test_load_from_csv(tmp_path, synth):
    p = tmp_path / "d.csv"
    synth.to_csv(p, index=False)
    assert len(load_dataset(p, download=False)) == len(synth)


def test_missing_file_without_download(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_dataset(tmp_path / "nope.csv", download=False)


def test_empty_dataset_rejected():
    with pytest.raises(DatasetError):
        check_schema(pd.DataFrame())


def test_unexpected_schema_rejected(synth):
    with pytest.raises(DatasetError, match="missing"):
        check_schema(synth.drop(columns=["Glucose"]))


def test_non_numeric_and_nonbinary_rejected(synth):
    bad = synth.copy()
    bad["Age"] = "x"
    with pytest.raises(DatasetError):
        check_schema(bad)
    bad = synth.copy()
    bad["Outcome"] = 2
    with pytest.raises(DatasetError):
        check_schema(bad)


def test_profile_counts_zeros_and_duplicates(synth):
    prof = profile_dataset(synth, ["Insulin"])
    assert prof["zeros_treated_as_missing"]["Insulin"] == 20
    assert prof["duplicate_rows"] == 0

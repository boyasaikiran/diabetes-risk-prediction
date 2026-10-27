import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from leakage_study.splits import make_splits  # noqa: E402


@pytest.fixture(scope="session")
def toy():
    """Synthetic toy data (NOT clinical): features 3 and 4 differ by class and have 45% missing cells."""
    rng = np.random.default_rng(0)
    n, p = 300, 8
    y = (rng.random(n) < 0.4).astype(int)
    X = rng.normal(size=(n, p))
    X[:, 3] += 1.5 * y
    X[:, 4] += 2.0 * y
    for j in (3, 4):
        X[rng.random(n) < 0.45, j] = np.nan
    X[rng.random(n) < 0.05, 1] = np.nan
    return X, y


@pytest.fixture(scope="session")
def toy_split(toy):
    return make_splits(toy[1], 1, 123)[0]


@pytest.fixture(scope="session")
def toy_complete(toy):
    """Same toy data with every missing cell replaced by 0: no missing values at all."""
    X, y = toy
    return np.nan_to_num(X, nan=0.0), y

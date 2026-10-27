"""Paired, reproducible stratified splits (design section 2.3)."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from sklearn.model_selection import train_test_split


@dataclass(frozen=True)
class Split:
    index: int
    seed: int
    train_idx: np.ndarray
    test_idx: np.ndarray


def make_splits(y: np.ndarray, n_splits: int, master_seed: int, test_size: float = 0.2) -> list[Split]:
    """`n_splits` stratified random train/test splits with seeds spawned from one master seed.
    The same list is reused for every regime and model (pairing)."""
    children = np.random.SeedSequence(master_seed).spawn(n_splits)
    out = []
    for i, child in enumerate(children):
        seed = int(child.generate_state(1)[0])
        tr, te = train_test_split(np.arange(len(y)), test_size=test_size, stratify=y, random_state=seed)
        out.append(Split(i, seed, np.sort(tr), np.sort(te)))
    return out

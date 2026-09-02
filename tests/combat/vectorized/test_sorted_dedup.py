"""Invariante O(n) de dedup sobre arrays ascendentes (optimización del motor vectorial)."""
from __future__ import annotations

import numpy as np

from mordheim_combat.vectorized import _run_starts


def test_run_starts_equals_unique_on_sorted_inputs() -> None:
    rng = np.random.default_rng(7)
    for size in (0, 1, 2, 10, 1_000):
        values = np.sort(rng.integers(0, size, size=size)).astype(np.int64)
        starts = _run_starts(values)
        assert np.array_equal(values[starts], np.unique(values))
        if size >= 2:
            expected = np.flatnonzero(np.r_[True, values[1:] != values[:-1]])
            assert np.array_equal(starts, expected)


def test_run_starts_single_and_empty() -> None:
    assert _run_starts(np.array([], dtype=np.int64)).size == 0
    assert _run_starts(np.array([5], dtype=np.int64)).tolist() == [0]


def test_run_starts_duplicated_runs() -> None:
    values = np.array([3, 3, 3, 7, 7, 9], dtype=np.int64)
    assert _run_starts(values).tolist() == [0, 3, 5]
    assert values[_run_starts(values)].tolist() == [3, 7, 9]
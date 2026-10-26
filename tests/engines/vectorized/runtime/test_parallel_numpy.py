"""NumPy driver: per-batch streams make process splits bit-for-bit identical."""
from __future__ import annotations

from mordheim_combat.vectorized import simulate_duel
from mordheim_combat.vectorized import simulate_duel_parallel
from mordheim_combat.vectorized._driver import _batch_sizes
from mordheim_combat.vectorized._driver import _batch_seed
from mordheim_core.models import DuelRequest
import pytest


def test_batch_plan_and_seeds_are_canonical_and_deterministic():
    assert _batch_sizes(1000, 300) == (300, 300, 300, 100)
    assert _batch_sizes(300, 300) == (300,)
    assert _batch_sizes(5, 300) == (5,)
    # Batch 0 keeps the seed; later batches derive from it deterministically.
    assert _batch_seed(2026, 0) != _batch_seed(2026, 1)
    assert _batch_seed(2026, 1) == _batch_seed(2026, 1)
    assert _batch_seed(2026, 1) != _batch_seed(2027, 1)


def test_parallel_numpy_matches_the_sequential_driver_exactly(vector_case):
    case = vector_case("test_parallel_numpy/test_parallel_numpy_matches_the_sequential_driver_exactly-0-0")
    first, second = case.first, case.second
    simulations, batch_size = 800, 250  # four whole batches
    request = DuelRequest(
        first, second, simulations, seed=2026, batch_size=batch_size,
        maximum_rounds=15,
    )
    sequential = simulate_duel(request, backend="numpy")
    assert sequential.first_wins + sequential.second_wins + sequential.unresolved == simulations
    for workers in (1, 2, 4):
        pooled = simulate_duel_parallel(request, workers=workers)
        assert pooled == sequential
    # Reproducible across separate calls with the same split.
    again = simulate_duel_parallel(request, workers=2)
    assert again == sequential


def test_single_batch_samples_are_unchanged_by_the_parallel_path(vector_case):
    case = vector_case("test_parallel_numpy/test_single_batch_samples_are_unchanged_by_the_parallel_path-0-0")
    first, second = case.first, case.second
    request = DuelRequest(
        first, second, 500, seed=7, batch_size=1000, maximum_rounds=15,
    )
    sequential = simulate_duel(request, backend="numpy")
    pooled = simulate_duel_parallel(request, workers=2)
    assert pooled == sequential

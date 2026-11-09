"""NumPy driver: whole-batch splits are bit-for-bit identical; split batches reproducible."""
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
    for workers in (1, 2):
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


def test_parallel_plan_splits_batches_only_when_workers_outnumber_them():
    from mordheim_combat.vectorized import PARALLEL_MIN_PART, parallel_plan

    def shape(simulations, batch_size, workers):
        return [(u.batch_index, u.parts, u.count)
                for u in parallel_plan(simulations, batch_size, workers)]

    # Enough batches: the canonical whole-batch plan.
    assert shape(400_000, 100_000, 4) == [(i, 1, 100_000) for i in range(4)]
    assert shape(300_000, 100_000, 4) == [(i, 1, 100_000) for i in range(3)]
    # One or two batches over four workers: equal parts, one per worker.
    assert shape(100_000, 100_000, 4) == [(0, 4, 25_000)] * 4
    assert shape(200_000, 100_000, 4) == [(0, 2, 50_000)] * 2 + [(1, 2, 50_000)] * 2
    # Never narrower than the minimum part; too small to cut stays whole.
    assert shape(100_000, 100_000, 64) == [(0, 8, PARALLEL_MIN_PART)] * 8
    assert shape(PARALLEL_MIN_PART, 100_000, 4) == [(0, 1, PARALLEL_MIN_PART)]
    for args in ((150_001, 100_000, 4), (99_999, 100_000, 3), (5, 300, 2)):
        assert sum(u.count for u in parallel_plan(*args)) == args[0]


def test_split_streams_are_reproducible_and_independent(vector_case, monkeypatch):
    import numpy as np
    import mordheim_combat.vectorized._driver as driver
    from mordheim_combat.vectorized import ParallelUnit

    case = vector_case("test_parallel_numpy/test_single_batch_samples_are_unchanged_by_the_parallel_path-0-0")
    # Workers receive whole units, so the parent's plan decides the split.
    monkeypatch.setattr(driver, "PARALLEL_MIN_PART", 100)
    request = DuelRequest(case.first, case.second, 600, seed=7, batch_size=1000, maximum_rounds=15)
    assert {u.parts for u in driver.parallel_plan(600, 1000, 2)} == {2}
    pooled = simulate_duel_parallel(request, workers=2)
    assert pooled.first_wins + pooled.second_wins + pooled.unresolved == 600
    assert simulate_duel_parallel(request, workers=2) == pooled
    # Every split part draws its own stream, distinct from the canonical batch.
    first_draws = [driver._unit_rng(7, ParallelUnit(0, parts, part, 1)).random()
                   for parts, part in ((1, 0), (2, 0), (2, 1), (4, 0))]
    assert len(set(first_draws)) == len(first_draws)
    assert np.isfinite(first_draws).all()


def test_a_caller_owned_executor_is_reused_and_left_open(vector_case, monkeypatch):
    from concurrent.futures import ProcessPoolExecutor
    import mordheim_combat.vectorized._driver as driver

    case = vector_case("test_parallel_numpy/test_single_batch_samples_are_unchanged_by_the_parallel_path-0-0")
    monkeypatch.setattr(driver, "PARALLEL_MIN_PART", 100)
    request = DuelRequest(case.first, case.second, 600, seed=7, batch_size=1000, maximum_rounds=15)
    owned = simulate_duel_parallel(request, workers=2)
    with ProcessPoolExecutor(max_workers=2) as pool:
        assert simulate_duel_parallel(request, workers=2, executor=pool) == owned
        # The pool is the caller's: still usable after the call.
        assert simulate_duel_parallel(request, executor=pool) == owned

"""Process-pool oracle: bit-for-bit equivalence with the sequential simulator."""
from __future__ import annotations

from mordheim_combat.modular.duel import simulate_duel_reference
from mordheim_combat.modular.parallel import chunk_ranges
from mordheim_combat.modular.parallel import resolve_oracle_workers
from mordheim_combat.modular.parallel import run_oracle_sample
from mordheim_combat.modular.parallel import simulate_duel_reference_parallel
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import FighterBuild


def fighter(**changes):
    options = dict(
        ruleset="mordheim",
        characteristics=Characteristics(3, 3, 3, 1, 3, 1),
    )
    options.update(changes)
    return compile_fighter(FighterBuild(**options))


def test_chunk_ranges_partition_contiguously_and_exactly():
    ranges = chunk_ranges(13, 4)
    assert ranges == ((0, 4), (4, 3), (7, 3), (10, 3))
    assert [index for start, count in ranges for index in range(start, start + count)] == list(range(13))
    assert chunk_ranges(10, 1) == ((0, 10),)
    assert chunk_ranges(3, 9) == ((0, 1), (1, 1), (2, 1))


def test_resolve_oracle_workers_gates_auto_by_estimated_time():
    # auto: pool only samples whose estimated sequential time is >= ~20 s.
    assert resolve_oracle_workers(None, 10_000, 50, cpu=8) is None      # ~10 s
    assert resolve_oracle_workers(None, 100_000, 50, cpu=8) == 8         # ~100 s
    assert resolve_oracle_workers(None, 1_000, 75, cpu=8) is None        # ~13 s
    assert resolve_oracle_workers(None, 2_000, 75, cpu=8) == 8           # ~26 s
    assert resolve_oracle_workers("auto", 100_000, 50, cpu=8) == 8
    assert resolve_oracle_workers("auto", 100_000, 50, cpu=1) is None   # one core
    # explicit counts are honored, capped to the machine; 1 stays sequential.
    assert resolve_oracle_workers(4, 100, 50, cpu=8) == 4
    assert resolve_oracle_workers(1, 1_000_000, 50, cpu=8) is None
    assert resolve_oracle_workers(99, 100_000, 50, cpu=8) == 8


def test_parallel_oracle_matches_the_sequential_oracle_exactly():
    first = fighter(characteristics=Characteristics(3, 4, 3, 1, 4, 2))
    second = fighter()
    sequential = simulate_duel_reference(first, second, 500, seed=2026, maximum_rounds=15)
    parallel = simulate_duel_reference_parallel(
        first, second, 500, seed=2026, maximum_rounds=15, workers=2,
    )
    assert parallel == sequential
    assert parallel.first_wins + parallel.second_wins + parallel.unresolved == 500
    # A different chunking must not change a single duel outcome.
    re_chunked = simulate_duel_reference_parallel(
        first, second, 500, seed=2026, maximum_rounds=15, workers=3, chunks=7,
    )
    assert re_chunked == sequential
    # The resolved-policy entry point dispatches to the same pooled path.
    pooled = run_oracle_sample(
        first, second, 500, seed=2026, maximum_rounds=15, workers=2,
    )
    assert pooled == sequential
    # A shared executor across several samples stays exact per sample.
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(max_workers=2) as pool:
        forward = run_oracle_sample(
            first, second, 250, seed=2026, maximum_rounds=15, workers=2,
            executor=pool,
        )
        reversed_duels = run_oracle_sample(
            second, first, 250, seed=2026, maximum_rounds=15, workers=2,
            executor=pool,
        )
    assert forward == simulate_duel_reference(
        first, second, 250, seed=2026, maximum_rounds=15)
    assert reversed_duels == simulate_duel_reference(
        second, first, 250, seed=2026, maximum_rounds=15)

"""Parallel scalar oracle: partition the independent duel streams across processes.

The scalar simulator is embarrassingly parallel by construction: duel ``i``
uses ``SeededDice(seed + i)``, never touches the others, and the outcome
counts (wins / losses / unresolved) are additive.  Partitioning the index
range ``[seed, seed + simulations)`` into contiguous chunks, running each
chunk through the exact same ``simulate_duel_reference`` on its own process,
and summing the ``DuelResult`` counts therefore reproduces the sequential
oracle **duel for duel** — bit-for-bit identical totals, independent of how
many workers or chunks are used.

Threads would buy nothing here (pure Python holds the GIL), so the pool uses
processes; the default start method is ``spawn`` on Windows and ``fork`` on
POSIX, both supported by this module because the worker is a top-level
function and every argument (compiled fighters, results) is a plain frozen
dataclass.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
import os

from mordheim_combat.modular.duel import simulate_duel_reference
from mordheim_core.dice import DecisionPolicy
from mordheim_core.models import CompiledFighter
from mordheim_core.models import DuelResult
from mordheim_core.models import SimulationCancelled


def chunk_ranges(total: int, chunks: int) -> tuple[tuple[int, int], ...]:
    """Split ``[0, total)`` into ``chunks`` contiguous, balanced ranges.

    Returns ``(start, count)`` pairs covering every index exactly once.  The
    balance only affects wall time (the executor finishes with the longest
    chunk); the simulation outcome is independent of the split.
    """
    if total < 0 or chunks < 1:
        raise ValueError("total and chunks must be positive")
    chunks = min(chunks, total) if total else 1
    base, extra = divmod(total, chunks)
    ranges = []
    start = 0
    for index in range(chunks):
        count = base + (1 if index < extra else 0)
        ranges.append((start, count))
        start += count
    return tuple(ranges)


def _run_chunk(first: CompiledFighter, second: CompiledFighter,
               start: int, count: int, seed: int, maximum_rounds: int,
               decisions: DecisionPolicy | None) -> DuelResult:
    """Run one contiguous chunk through the identical sequential code path."""
    return simulate_duel_reference(
        first, second, count, seed=seed + start,
        maximum_rounds=maximum_rounds, decisions=decisions,
    )


# Calibration of the scalar oracle used by the auto gate: roughly 1000
# duels/s on the five standard scenarios and 76 duels/s on the 75-round
# ``long`` scenario (measured 2026-09-04 on Windows, CPython 3.10).
_ORACLE_RATE_STANDARD = 1000.0
_ORACLE_RATE_LONG = 76.0

# A bulk sample is pooled only when the sequential oracle would take at least
# this long; below it the spawn/import overhead makes the pool slower.
ORACLE_PARALLEL_MIN_SECONDS = 20.0


def _estimated_oracle_rate(maximum_rounds: int) -> float:
    """Rough single-core throughput of the scalar oracle for a scenario."""
    return _ORACLE_RATE_LONG if maximum_rounds > 50 else _ORACLE_RATE_STANDARD


def resolve_oracle_workers(workers: object | None, simulations: int,
                           maximum_rounds: int, *, cpu: int | None = None,
                           ) -> int | None:
    """Map a worker policy onto a concrete process count for one sample.

    ``workers`` is ``None``/``"auto"`` for the threshold gate, or an explicit
    positive integer.  The gate pools only when the estimated sequential
    oracle time exceeds ``ORACLE_PARALLEL_MIN_SECONDS``; explicit counts are
    honored as-is (capped to the machine), and ``1`` stays sequential.
    Returns ``None`` when the sample should run sequentially.
    """
    available = cpu if cpu is not None else os.cpu_count() or 1
    if isinstance(workers, str) and workers.casefold() == "auto":
        workers = None
    if workers is None:
        if simulations / _estimated_oracle_rate(maximum_rounds) < ORACLE_PARALLEL_MIN_SECONDS:
            return None
        return available if available > 1 else None
    count = int(workers)
    if count < 2 or available < 2:
        return None
    return min(count, available)


def _run_chunks(first: CompiledFighter, second: CompiledFighter,
                simulations: int, *, seed: int, maximum_rounds: int,
                decisions: DecisionPolicy | None, units: int,
                executor, cancel_event: object | None) -> DuelResult:
    """Submit one chunk per unit on an existing executor and sum the counts."""
    ranges = chunk_ranges(simulations, units)
    futures = [
        executor.submit(_run_chunk, first, second, start, count, seed,
                        maximum_rounds, decisions)
        for start, count in ranges
    ]
    first_wins = second_wins = unresolved = 0
    try:
        for future in as_completed(futures):
            if cancel_event is not None and getattr(cancel_event, "is_set")():
                raise SimulationCancelled("parallel scalar simulation cancelled")
            result = future.result()
            first_wins += result.first_wins
            second_wins += result.second_wins
            unresolved += result.unresolved
    finally:
        for future in futures:
            future.cancel()
    return DuelResult(first_wins, second_wins, unresolved, simulations)


def simulate_duel_reference_parallel(
    first: CompiledFighter, second: CompiledFighter, simulations: int,
    *, seed: int = 0, maximum_rounds: int = 50,
    decisions: DecisionPolicy | None = None,
    workers: int | None = None,
    chunks: int | None = None,
    cancel_event: object | None = None,
) -> DuelResult:
    """Bit-for-bit parallel equivalent of ``simulate_duel_reference``.

    ``workers`` caps the pool size (default: ``os.cpu_count()``).  ``chunks``
    controls how many work units are submitted (default: one per worker);
    more chunks than workers smooths the tail when duels have uneven lengths,
    at the cost of pickling the fighters once per chunk.
    """
    if min(simulations, maximum_rounds) < 1:
        raise ValueError("simulation limits must be positive")
    available = workers if workers is not None else os.cpu_count() or 1
    if available < 1:
        raise ValueError("workers must be positive")
    units = chunks if chunks is not None else available
    if units < 1:
        raise ValueError("chunks must be positive")
    with ProcessPoolExecutor(max_workers=min(available, units)) as pool:
        return _run_chunks(
            first, second, simulations, seed=seed,
            maximum_rounds=maximum_rounds, decisions=decisions,
            units=units, executor=pool, cancel_event=cancel_event,
        )


def run_oracle_sample(
    first: CompiledFighter, second: CompiledFighter, simulations: int,
    *, seed: int = 0, maximum_rounds: int = 50,
    decisions: DecisionPolicy | None = None,
    workers: int | None = None, executor=None,
    cancel_event: object | None = None,
) -> DuelResult:
    """Run one bulk oracle sample under a resolved worker policy.

    ``workers`` is the **resolved** count from ``resolve_oracle_workers``
    (``None`` means sequential; ``>= 2`` pools).  Passing an existing
    ``executor`` reuses one pool across several samples so the workers are
    spawned once per run instead of once per sample; otherwise a pool is
    created and torn down around this sample.  Always returns the same
    ``DuelResult`` the sequential oracle would produce.
    """
    if workers is None or workers < 2:
        return simulate_duel_reference(
            first, second, simulations, seed=seed,
            maximum_rounds=maximum_rounds, decisions=decisions,
            cancel_event=cancel_event,
        )
    if executor is not None:
        return _run_chunks(
            first, second, simulations, seed=seed,
            maximum_rounds=maximum_rounds, decisions=decisions,
            units=workers, executor=executor, cancel_event=cancel_event,
        )
    with ProcessPoolExecutor(max_workers=workers) as pool:
        return _run_chunks(
            first, second, simulations, seed=seed,
            maximum_rounds=maximum_rounds, decisions=decisions,
            units=workers, executor=pool, cancel_event=cancel_event,
        )

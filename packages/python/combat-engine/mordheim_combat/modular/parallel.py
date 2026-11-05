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
processes; the default start method is ``spawn`` on Windows and macOS and,
since Python 3.14, ``forkserver`` on Linux (``fork`` before).  All are
supported because the worker is a top-level function and every argument
(compiled fighters, results) is a plain frozen dataclass.  With ``spawn`` and
``forkserver`` the workers import the engine afresh from ``sys.path``, so they
run the parent's engine only if both resolve the same package copy; callers
that label results with an engine digest must check that (see
``tools.verification.parity_samples``).
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import as_completed
import os

from mordheim_combat.modular.duel import simulate_duel_reference
from mordheim_core.dice import DecisionPolicy
from mordheim_core.models import DuelContext
from mordheim_core.models import CompiledFighter
from mordheim_core.models import DuelResult
from mordheim_core.models import SimulationCancelled


def _engine_files() -> tuple[str, str]:
    """Files the engine packages of this process were imported from."""
    import mordheim_combat
    import mordheim_core

    return mordheim_combat.__file__, mordheim_core.__file__


def _check_worker_engine(expected: tuple[str, str]) -> None:
    """Pool initializer: a worker must run the parent's engine copy.

    Spawned and forkserver workers re-import from ``sys.path``; a worker that
    resolved another copy would merge another engine's duels into the
    sample, so it fails (the pool breaks) instead of running.
    """
    actual = _engine_files()
    if actual != expected:
        raise RuntimeError(
            f"oracle worker imported another engine copy ({actual}); the parent runs {expected}"
        )


def _pool(workers: int) -> ProcessPoolExecutor:
    return ProcessPoolExecutor(max_workers=workers, initializer=_check_worker_engine,
                               initargs=(_engine_files(),))


def oracle_pool(workers: int) -> ProcessPoolExecutor:
    """A process pool whose workers are checked to run this engine copy.

    Callers that run several oracle samples (campaigns, time-to-solution
    studies) create one pool here and pass it to ``run_oracle_sample`` as
    ``executor`` so the spawn cost is paid once per run.
    """
    if workers < 1:
        raise ValueError("workers must be positive")
    return _pool(workers)


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
               decisions: DecisionPolicy | None,
               context: DuelContext | None = None) -> DuelResult:
    """Run one contiguous chunk through the identical sequential code path."""
    return simulate_duel_reference(
        first, second, count, seed=seed + start,
        maximum_rounds=maximum_rounds, decisions=decisions, context=context,
    )


# Calibration of the scalar oracle used by the auto gate: roughly 400
# duels/s on the standard 50-round scenarios and 18 duels/s on the 75-round
# ``long`` grind (measured 2026-11-05 on Linux, CPython 3.14). These are
# coarse order-of-magnitude figures for the pooling threshold only; refresh
# them when the modular engine's throughput changes materially.
_ORACLE_RATE_STANDARD = 400.0
_ORACLE_RATE_LONG = 18.0

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
                executor, cancel_event: object | None,
                context: DuelContext | None = None) -> DuelResult:
    """Submit one chunk per unit on an existing executor and sum the counts."""
    ranges = chunk_ranges(simulations, units)
    futures = [
        executor.submit(_run_chunk, first, second, start, count, seed,
                        maximum_rounds, decisions, context)
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
    context: DuelContext | None = None,
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
    with _pool(min(available, units)) as pool:
        return _run_chunks(
            first, second, simulations, seed=seed,
            maximum_rounds=maximum_rounds, decisions=decisions, context=context,
            units=units, executor=pool, cancel_event=cancel_event,
        )


def run_oracle_sample(
    first: CompiledFighter, second: CompiledFighter, simulations: int,
    *, seed: int = 0, maximum_rounds: int = 50,
    decisions: DecisionPolicy | None = None,
    workers: int | None = None, executor=None,
    cancel_event: object | None = None,
    context: DuelContext | None = None,
    chunks: int | None = None,
) -> DuelResult:
    """Run one bulk oracle sample under a resolved worker policy.

    ``workers`` is the **resolved** count from ``resolve_oracle_workers``
    (``None`` means sequential; ``>= 2`` pools).  Passing an existing
    ``executor`` reuses one pool across several samples so the workers are
    spawned once per run instead of once per sample; otherwise a pool is
    created and torn down around this sample.  ``chunks`` sets how many work
    units the sample is split into (default: one per worker); more chunks
    than workers smooths the tail when duel lengths are uneven, at the cost
    of pickling the fighters once per chunk.  Always returns the same
    ``DuelResult`` the sequential oracle would produce.
    """
    if workers is None or workers < 2:
        return simulate_duel_reference(
            first, second, simulations, seed=seed,
            maximum_rounds=maximum_rounds, decisions=decisions, context=context,
            cancel_event=cancel_event,
        )
    units = chunks if chunks is not None else workers
    if units < 1:
        raise ValueError("chunks must be positive")
    if executor is not None:
        return _run_chunks(
            first, second, simulations, seed=seed,
            maximum_rounds=maximum_rounds, decisions=decisions, context=context,
            units=units, executor=executor, cancel_event=cancel_event,
        )
    with _pool(workers) as pool:
        return _run_chunks(
            first, second, simulations, seed=seed,
            maximum_rounds=maximum_rounds, decisions=decisions, context=context,
            units=units, executor=pool, cancel_event=cancel_event,
        )

"""Benchmark suite and CLI presenters for the combat backends.

Runs the maintained end-to-end scenarios against the modular, NumPy and
native engines, supports single-configuration runs (with baseline
comparison gates) and size sweeps over simulation counts and batch
sizes, and renders results as console tables, JSON, CSV or Markdown.

Baseline gate (:func:`gate_against_baseline`): the stored ``configuration``
is the *measurement design* — simulations, batch size, seed, warmups,
repeats, processes, pool start method and backend list. Any recorded field
that differs makes the two measurements incomparable and is an error. The
``provenance`` block (CPU count, platform, Python/NumPy, per-engine source
digests, native build hash, source revision) describes *where* it was
measured: differences only raise a ``PROVENANCE WARNING`` recorded in the
gate, because old baselines are reused on purpose. A baseline (scenario,
backend) result with no current result fails the gate explicitly.
"""
from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime, timezone
from functools import lru_cache
import csv
import json
from pathlib import Path
import platform
from statistics import median
from time import perf_counter
from typing import Callable
from typing import Iterable
from typing import Mapping
from typing import Sequence

import numpy as np

from mordheim_combat.modular.duel import simulate_duel as simulate_modular_duel
from mordheim_combat.vectorized import simulate_duel
from mordheim_core.models import Characteristics
from mordheim_core.models import CompiledFighter
from mordheim_core.models import DuelRequest
from mordheim_core.models import FighterBuild



@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    scenario: str
    backend: str
    simulations: int
    batch_size: int
    repeats: int
    samples_seconds: tuple[float, ...]
    median_seconds: float
    simulations_per_second: float
    #: Wall seconds spent in the untimed warm-up executions, so command
    #: summaries can separate them from genuine setup overhead.
    warmup_seconds: float = 0.0


@dataclass(frozen=True, slots=True)
class BenchmarkComparison:
    scenario: str
    backend: str
    baseline_simulations_per_second: float
    current_simulations_per_second: float
    change_ratio: float
    status: str


@dataclass(frozen=True, slots=True)
class BenchmarkMissing:
    """A baseline (scenario, backend) result the current run did not produce."""
    scenario: str
    backend: str
    reason: str


@dataclass(frozen=True, slots=True)
class BenchmarkGate:
    """Outcome of the baseline gate.

    ``missing`` lists baseline results without a current counterpart (each
    one fails the gate); ``provenance_warnings`` records the provenance
    differences that were reported but did not block the comparison.
    """
    passed: bool
    improved: bool
    regressed: bool
    comparisons: tuple[BenchmarkComparison, ...]
    detail: str
    missing: tuple[BenchmarkMissing, ...] = ()
    provenance_warnings: tuple[str, ...] = ()


BENCHMARK_SCHEMA = "mordheim-combat-benchmark/v1"
SWEEP_SCHEMA = "mordheim-combat-benchmark-sweep/v1"
TTS_SCHEMA = "mordheim-combat-benchmark-tts/v1"

ENGINE_LABELS = {"modular": "Modular", "numpy": "Vectorized", "native": "Native"}




from mordheim_combat_lab.cli.scenarios import (  # noqa: E402
    BenchmarkScenario,
    benchmark_scenarios,
    select_scenarios,
)


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    """One runnable duel of a benchmark: what ``--scenarios`` selected.

    ``id`` is the precompiled scenario name (so stored baselines keep matching)
    or the E2E / battery key; the fighters and context are the frozen inputs.
    """

    id: str
    first: CompiledFighter
    second: CompiledFighter
    maximum_rounds: int
    context: object = None


def benchmark_cases(
    scenarios, default: str = "small",
) -> tuple[tuple[BenchmarkCase, ...], tuple[tuple[str, str], ...]]:
    """Resolve ``--scenarios`` values; return the runnable cases and the
    ``(key, reason)`` of every selected case the engines cannot run.
    Raises ``ValueError`` for a value that selects nothing."""
    from mordheim_combat_lab.cli.scenarios import load_checkout_module

    catalog = load_checkout_module("tools.verification.parity_catalog")
    runnable, rejected, _ = catalog.resolve(tuple(scenarios or (default,)))
    return tuple(
        BenchmarkCase(
            item.name if item.kind == "scenario" else item.key,
            item.case.first, item.case.second,
            item.case.limits.maximum_rounds, item.case.context,
        )
        for item in runnable
    ), rejected


def compile_benchmark_fighters(scenario) -> tuple[CompiledFighter, CompiledFighter]:
    """The frozen fighters of a benchmark case or a precompiled scenario."""
    if isinstance(scenario, BenchmarkCase):
        return scenario.first, scenario.second
    from mordheim_combat_lab.cli.scenarios import scenario_key

    case = _frozen_scenarios()[scenario_key(scenario.id)]
    return case.first, case.second


@lru_cache(maxsize=1)
def _frozen_scenarios():
    from mordheim_knowledge.paths import project_root
    from mordheim_combat_lab.cli.scenarios import load_checkout_module

    load_cases = load_checkout_module("tools.verification.compiled_cases").load_cases
    return load_cases(project_root() / "tests/engines/fixtures/compiled-cases.json")


def run_benchmark(
    scenario: BenchmarkScenario, *, simulations: int, batch_size: int,
    seed: int, backend: str, warmups: int, repeats: int,
    on_progress: Callable[[], None] | None = None,
    profiler=None,
    fighters: tuple[CompiledFighter, CompiledFighter] | None = None,
) -> BenchmarkResult:
    """Measure one (scenario, backend) configuration.

    ``profiler`` is an optional ``cProfile.Profile``: when given, every timed
    repeat runs under it (warm-ups stay unprofiled). Profiler instrumentation
    slows the engine, so profiled timings describe where the time goes, not
    how fast the engine is — the caller must not feed them to a baseline gate.
    ``fighters`` supplies the scenario's precompiled pair; pool workers get
    it from the parent so they never load the frozen catalogue themselves.
    """
    if backend not in {"modular", "numpy", "native"}:
        raise ValueError(f"unknown benchmark backend: {backend}")
    first, second = fighters or compile_benchmark_fighters(scenario)
    request = DuelRequest(
        first, second, simulations, seed=seed, batch_size=batch_size,
        maximum_rounds=scenario.maximum_rounds,
        context=getattr(scenario, "context", None),
    )

    def execute() -> None:
        if backend == "modular":
            simulate_modular_duel(request)
        else:
            simulate_duel(request, backend=backend)

    warmup_started = perf_counter()
    for _ in range(warmups):
        execute()
        if on_progress is not None:
            on_progress()
    warmup_seconds = perf_counter() - warmup_started if warmups else 0.0
    samples = []
    for _ in range(repeats):
        started = perf_counter()
        if profiler is not None:
            profiler.enable()
        try:
            execute()
        finally:
            if profiler is not None:
                profiler.disable()
        samples.append(perf_counter() - started)
        if on_progress is not None:
            on_progress()
    middle = median(samples)
    return BenchmarkResult(
        scenario.id, backend, simulations, batch_size, repeats, tuple(samples),
        middle, simulations / middle, warmup_seconds,
    )


def write_profile(profiler, path: Path) -> None:
    """Dump one backend's collected profile as a ``pstats`` file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    profiler.dump_stats(str(path))


def render_profile(profiler, *, limit: int = 15) -> str:
    """Top functions of one backend's collected profile, by cumulative time."""
    import io
    import pstats

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative").print_stats(limit)
    return stream.getvalue().rstrip()


# Time-to-solution (--strategies): the workload is fixed and whole execution
# strategies are compared by the wall time of solving it completely —
# throughput rows diagnose *why* one strategy wins, this mode decides *which*
# one to use. Every strategy runs the same per-batch streams, so the
# deterministic win/loss/unresolved totals double as a correctness gate.


@dataclass(frozen=True, slots=True)
class TtsStrategyResult:
    """One full workload pass under one execution strategy and backend.

    ``wall_seconds`` covers everything from pool startup to the reduced
    result (spawns included) — it is the number a user waits for; with
    ``repeats > 1`` it is the median of the repeat walls. ``engine_seconds``
    sums the per-scenario pass times. ``totals`` are the workload's
    deterministic (first_wins, second_wins, unresolved) counts.
    """
    strategy: str
    mode: str  # "sequential" | "scenario-pool" | "batch-pool"
    processes: int
    wall_seconds: float
    engine_seconds: float
    totals: tuple[int, int, int]
    per_scenario_seconds: tuple[tuple[str, float], ...]
    backend: str = "numpy"
    repeat_walls: tuple[float, ...] = ()

    @property
    def overhead_seconds(self) -> float:
        return max(0.0, self.wall_seconds - self.engine_seconds)

    @property
    def label(self) -> str:
        return f"{self.backend}/{self.strategy}"


def parse_tts_strategies(value: str | None) -> tuple[str, ...]:
    """Parse the ``--strategies`` list into canonical strategy tokens.

    Accepts ``sequential``, ``processes=N`` (one scenario per worker),
    ``parallel=N`` (each scenario split inside a pool of N) and
    ``parallel=N:C`` (the same, with the sample split into C chunks instead
    of N; modular only, where more chunks than workers smooths uneven duel
    lengths). N >= 2; N=1 canonicalizes to ``sequential``. Defaults to the
    three-way comparison.
    """
    if value is None or not value.strip():
        return ("sequential", "processes=4", "parallel=4")
    strategies: list[str] = []
    for token in value.split(","):
        token = token.strip().lower()
        if not token:
            continue
        if token == "sequential":
            strategies.append(token)
            continue
        mode, separator, number = token.partition("=")
        number, colon, chunks = number.strip().partition(":")
        chunks = chunks.strip()
        if (not separator or mode not in {"processes", "parallel"}
                or not number.isdigit() or int(number) < 1
                or (colon and (mode != "parallel" or not chunks.isdigit()
                               or int(chunks) < 1))):
            raise ValueError(
                f"invalid TTS strategy {token!r}; use 'sequential', "
                f"'processes=N', 'parallel=N' or 'parallel=N:C'")
        if int(number) == 1 and not chunks:
            strategies.append("sequential")
            continue
        if chunks and int(chunks) < int(number):
            raise ValueError(
                f"invalid TTS strategy {token!r}: the chunk count must be at "
                f"least the worker count")
        strategies.append(
            f"{mode}={int(number)}" + (f":{int(chunks)}" if chunks else ""))
    if not strategies:
        raise ValueError("no TTS strategies provided")
    return tuple(dict.fromkeys(strategies))


def parse_tts_strategy(strategy: str) -> tuple[str, int, int | None]:
    """Split a canonical token into ``(mode, processes, chunks)``.

    ``sequential`` maps to ``("sequential", 1, None)``; ``chunks`` is only
    set for ``parallel=N:C``.
    """
    if strategy == "sequential":
        return "sequential", 1, None
    mode, _, rest = strategy.partition("=")
    number, _, chunks = rest.partition(":")
    return mode, int(number), (int(chunks) if chunks else None)


def tts_strategy_applies(strategy: str, backend: str) -> bool:
    """Whether a backend can execute a strategy.

    ``sequential`` and ``processes=N`` apply to every engine. ``parallel=N``
    splits one scenario's sample inside a pool: the NumPy driver splits its
    batch plan, the modular oracle its duel index range (bit-for-bit equal
    to the sequential sample), so both apply; the native engine runs whole
    samples only. Explicit chunk counts (``parallel=N:C``) exist only for
    the modular split — the NumPy split is fixed by the batch size.
    """
    mode, _processes, chunks = parse_tts_strategy(strategy)
    if mode != "parallel":
        return True
    if backend == "modular":
        return True
    return backend == "numpy" and chunks is None


def _tts_sequential_worker(
    scenario: BenchmarkScenario, *, simulations: int, batch_size: int, seed: int,
    backend: str = "numpy",
    fighters: tuple[CompiledFighter, CompiledFighter] | None = None,
) -> tuple[float, tuple[int, int, int]]:
    """One workload pass for one scenario in-process; returns (wall, totals).

    Module-level so the scenario-pool strategy can submit it directly; the
    pool passes ``fighters`` so workers never load the frozen catalogue.
    """
    first, second = fighters or compile_benchmark_fighters(scenario)
    request = DuelRequest(
        first, second, simulations, seed=seed, batch_size=batch_size,
        maximum_rounds=scenario.maximum_rounds,
        context=getattr(scenario, "context", None),
    )
    started = perf_counter()
    if backend == "modular":
        result = simulate_modular_duel(request)
    else:
        result = simulate_duel(request, backend=backend)
    return perf_counter() - started, (
        result.first_wins, result.second_wins, result.unresolved)


def _tts_modular_chunk_pass(
    scenarios: Sequence[BenchmarkScenario], *, simulations: int, seed: int,
    processes: int, chunks: int | None,
    on_progress: Callable[[], None] | None = None,
) -> tuple[float, list[tuple[str, float]], list[int]]:
    """One modular workload pass with every scenario split over one pool.

    Mirrors how a campaign runs the oracle: the pool is spawned once per pass
    (its cost is inside the wall) and each scenario's duel range is split
    into ``chunks`` units (default: one per worker) through the parallel
    oracle, which reproduces the sequential totals duel for duel.
    """
    from mordheim_combat.modular.parallel import oracle_pool, run_oracle_sample

    per_scenario: list[tuple[str, float]] = []
    totals = [0, 0, 0]
    started = perf_counter()
    with oracle_pool(processes) as pool:
        for scenario in scenarios:
            first, second = compile_benchmark_fighters(scenario)
            scenario_started = perf_counter()
            result = run_oracle_sample(
                first, second, simulations, seed=seed,
                maximum_rounds=scenario.maximum_rounds, workers=processes,
                executor=pool, chunks=chunks,
                context=getattr(scenario, "context", None),
            )
            per_scenario.append((scenario.id, perf_counter() - scenario_started))
            totals[0] += result.first_wins
            totals[1] += result.second_wins
            totals[2] += result.unresolved
            if on_progress is not None:
                on_progress()
    return perf_counter() - started, per_scenario, totals


def _tts_parallel_scenario_worker(
    scenario: BenchmarkScenario, *, simulations: int, batch_size: int, seed: int,
    processes: int,
) -> tuple[float, tuple[int, int, int]]:
    """One workload pass for one scenario split over a batch pool.

    Wall-timed end to end (pool startup included) and reduced to the same
    deterministic totals as the sequential worker.
    """
    from concurrent.futures import ProcessPoolExecutor
    from mordheim_combat.vectorized import batch_plan, batch_segment

    first, second = compile_benchmark_fighters(scenario)
    sizes = batch_plan(simulations, batch_size)
    workers = max(1, min(processes, len(sizes)))
    base, extra = divmod(len(sizes), workers)
    segments = []
    start = 0
    for index in range(workers):
        count = base + (1 if index < extra else 0)
        segments.append((start, start + count))
        start += count
    totals = [0, 0, 0]
    started = perf_counter()
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(
                batch_segment, first, second, first_batch, stop,
                simulations, batch_size, seed, scenario.maximum_rounds, None,
                getattr(scenario, "context", None),
            )
            for first_batch, stop in segments if stop > first_batch
        ]
        for future in futures:
            wins, losses, unresolved = future.result()
            totals[0] += wins
            totals[1] += losses
            totals[2] += unresolved
    return perf_counter() - started, tuple(totals)


def run_tts_strategy(
    strategy: str, scenarios: Sequence[BenchmarkScenario], *,
    simulations: int, batch_size: int, seed: int,
    on_progress: Callable[[], None] | None = None,
    backend: str = "numpy", repeats: int = 1,
) -> TtsStrategyResult:
    """Run the whole workload under ``strategy``, wall-timed end to end.

    Each repeat is one full pass per scenario (no warmups: TTS compares
    total solving time, not per-sample stability); ``wall_seconds`` reports
    the median of the repeat walls. The strategy token selects how the
    workload parallelizes: not at all (``sequential``), scenario by scenario
    in a process pool (``processes=N``), or each scenario split inside a
    pool (``parallel=N``): the NumPy driver splits its batch plan, the
    modular oracle its duel range into ``C`` chunks (``parallel=N:C``,
    default one per worker) on one pool spawned per pass.
    """
    if repeats < 1:
        raise ValueError("repeats must be >= 1")
    if not tts_strategy_applies(strategy, backend):
        raise ValueError(f"strategy {strategy!r} does not apply to the {backend} engine")
    mode, processes, chunks = parse_tts_strategy(strategy)

    def one_pass() -> tuple[float, list[tuple[str, float]], list[int]]:
        if strategy == "sequential":
            per_scenario = []
            totals = [0, 0, 0]
            started = perf_counter()
            for scenario in scenarios:
                seconds, counts = _tts_sequential_worker(
                    scenario, simulations=simulations, batch_size=batch_size,
                    seed=seed, backend=backend,
                )
                per_scenario.append((scenario.id, seconds))
                for index, value in enumerate(counts):
                    totals[index] += value
                if on_progress is not None:
                    on_progress()
            return perf_counter() - started, per_scenario, totals
        if mode == "processes":
            from concurrent.futures import ProcessPoolExecutor
            started = perf_counter()
            with ProcessPoolExecutor(max_workers=processes) as pool:
                futures = {
                    pool.submit(
                        _tts_sequential_worker, scenario,
                        simulations=simulations, batch_size=batch_size,
                        seed=seed, backend=backend,
                        fighters=compile_benchmark_fighters(scenario),
                    ): scenario
                    for scenario in scenarios
                }
                per_scenario = []
                totals = [0, 0, 0]
                for future in futures:
                    seconds, counts = future.result()
                    per_scenario.append((futures[future].id, seconds))
                    for index, value in enumerate(counts):
                        totals[index] += value
                    if on_progress is not None:
                        on_progress()
            return perf_counter() - started, per_scenario, totals
        if mode == "parallel":
            if backend == "modular":
                return _tts_modular_chunk_pass(
                    scenarios, simulations=simulations, seed=seed,
                    processes=processes, chunks=chunks, on_progress=on_progress,
                )
            per_scenario = []
            totals = [0, 0, 0]
            started = perf_counter()
            for scenario in scenarios:
                seconds, counts = _tts_parallel_scenario_worker(
                    scenario, simulations=simulations, batch_size=batch_size,
                    seed=seed, processes=processes,
                )
                per_scenario.append((scenario.id, seconds))
                for index, value in enumerate(counts):
                    totals[index] += value
                if on_progress is not None:
                    on_progress()
            return perf_counter() - started, per_scenario, totals
        raise ValueError(f"unknown TTS strategy: {strategy!r}")

    walls = []
    per_scenario = totals = None
    engine = 0.0
    for _ in range(repeats):
        wall, per_scenario, totals = one_pass()
        walls.append(wall)
        engine += sum(seconds for _name, seconds in per_scenario)
    assert totals is not None and per_scenario is not None
    mode_label = "sequential" if mode == "sequential" else mode + "-pool"
    return TtsStrategyResult(
        strategy, mode_label, processes,
        median(walls), engine / repeats,
        tuple(totals), tuple(per_scenario),
        backend=backend, repeat_walls=tuple(walls),
    )


def tts_determinism_gate(
    results: Sequence[TtsStrategyResult],
) -> dict[str, object] | None:
    """All strategies must agree on the workload's deterministic totals.

    Every strategy executes the same per-batch streams, so any disagreement
    is a correctness bug, not a timing artifact. ``None`` with fewer than two
    strategies (nothing to cross-check).
    """
    if len(results) < 2:
        return None
    distinct = sorted({result.totals for result in results})
    return {
        "passed": len(distinct) == 1,
        "distinct_totals": [list(totals) for totals in distinct],
    }


def tts_ranking(
    results: Sequence[TtsStrategyResult], *, baseline: str = "sequential",
) -> list[dict[str, object]]:
    """Rank strategies by wall time; speedup against the baseline wall."""
    reference = next(
        (item.wall_seconds for item in results if item.strategy == baseline), None)
    rows = []
    for item in sorted(results, key=lambda entry: entry.wall_seconds):
        rows.append({
            "strategy": item.strategy, "mode": item.mode,
            "processes": item.processes, "wall_seconds": item.wall_seconds,
            "engine_seconds": item.engine_seconds,
            "overhead_seconds": item.overhead_seconds,
            "speedup_vs_sequential": (
                reference / item.wall_seconds
                if reference and item.wall_seconds > 0 else None),
        })
    return rows


def tts_strategy_label(result: TtsStrategyResult) -> str:
    """Cell-unique combination label: backend + strategy."""
    return result.label


def tts_backend_parity(results: Sequence[TtsStrategyResult]) -> dict[str, object]:
    """Determinism gate per backend, across that backend's strategies.

    Strategies of the same backend execute identical per-batch streams, so
    their totals must agree bit for bit. Totals are deliberately NOT
    compared across backends: each engine derives its per-batch streams from
    the seed in its own way, so equal totals are not expected between numpy
    and native — rate parity between engines is the parity command's job,
    not a wall-time benchmark's.
    """
    backends: dict[str, object] = {}
    passed = True
    for backend in dict.fromkeys(item.backend for item in results):
        same = [item for item in results if item.backend == backend]
        distinct = sorted({item.totals for item in same})
        backend_passed = len(distinct) == 1
        passed = passed and backend_passed
        backends[backend] = {
            "passed": backend_passed,
            "distinct_totals": [list(totals) for totals in distinct],
        }
    return {"passed": passed, "backends": backends}


def tts_backend_rates(
    results: Sequence[TtsStrategyResult], *, simulations: int,
    scenario_count: int,
) -> list[dict[str, float | str]]:
    """Informational win/loss/unresolved rates per backend (one cell).

    Cross-backend rates should land within sampling noise of each other;
    anything larger is a parity problem the parity command certifies.
    """
    rates: list[dict[str, float | str]] = []
    for backend in dict.fromkeys(item.backend for item in results):
        same = [item for item in results if item.backend == backend]
        # Every result repeats the whole workload, so the denominator scales
        # with the number of summed results.
        total = max(1, simulations * scenario_count * len(same))
        wins = sum(item.totals[0] for item in same)
        losses = sum(item.totals[1] for item in same)
        unresolved = sum(item.totals[2] for item in same)
        rates.append({
            "backend": backend, "first": wins / total,
            "second": losses / total, "unresolved": unresolved / total,
        })
    return rates


def run_tts_study_cell(
    strategies: Sequence[str], backends: Sequence[str],
    scenarios: Sequence[BenchmarkScenario], *, simulations: int, batch_size: int,
    seed: int, repeats: int,
    on_progress: Callable[[], None] | None = None,
) -> tuple[TtsStrategyResult, ...]:
    """Run every applicable (strategy, backend) combination on one cell.

    Strategies a backend cannot execute (:func:`tts_strategy_applies`) are
    skipped; the results are the rows of the cell's ranking. Within one
    backend every strategy executes the same duel streams, so the totals
    must agree — the caller cross-checks them as a parity gate.
    """
    results: list[TtsStrategyResult] = []
    for backend in backends:
        for strategy in strategies:
            if not tts_strategy_applies(strategy, backend):
                continue
            results.append(run_tts_strategy(
                strategy, scenarios, simulations=simulations,
                batch_size=batch_size, seed=seed, backend=backend,
                repeats=repeats, on_progress=on_progress,
            ))
    return tuple(results)


def tts_study_payload(
    cells: Sequence[dict[str, object]], *, simulations: Sequence[int],
    batch_sizes: Sequence[int], seed: int, strategies: Sequence[str],
    backends: Sequence[str], repeats: int, scenario_count: int,
    scenarios: str | None = None, elapsed_seconds: float | None = None,
    parity: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build the durable time-to-solution *study* artifact.

    One JSON document with a cell per (simulations, batch size): every cell
    carries the strategy x backend ranking plus the winners summary.
    """
    payload: dict[str, object] = {
        "schema": TTS_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": _environment(),
        "configuration": {
            "simulation_sizes": list(simulations),
            "batch_sizes": list(batch_sizes), "seed": seed,
            "strategies": list(strategies), "backends": list(backends),
            "repeats": repeats, "scenarios": scenario_count,
        },
        "cells": list(cells),
    }
    if scenarios is not None:
        payload["scenarios"] = scenarios
    if parity is not None:
        payload["parity"] = parity
    if elapsed_seconds is not None:
        payload["elapsed_seconds"] = elapsed_seconds
    return payload


def tts_cell_payload(cell: dict[str, object]) -> dict[str, object]:
    """JSON-safe projection of one study cell's results."""
    results: Sequence[TtsStrategyResult] = cell["results"]  # type: ignore[assignment]
    return {
        "simulations": cell["simulations"], "batch_size": cell["batch_size"],
        "winners": cell["winners"],
        "rates": cell.get("rates", []),
        "results": [{
            "backend": item.backend, "strategy": item.strategy,
            "mode": item.mode, "processes": item.processes,
            "wall_seconds": item.wall_seconds,
            "repeat_walls_seconds": list(item.repeat_walls),
            "engine_seconds": item.engine_seconds,
            "totals": list(item.totals),
            "per_scenario_seconds": [
                [name, seconds] for name, seconds in item.per_scenario_seconds
            ],
        } for item in results],
    }


def tts_cell_winners(
    results: Sequence[TtsStrategyResult], *, scenario_count: int,
    simulations: int,
) -> list[dict[str, object]]:
    """Per-backend winners (first by wall time) plus the overall champion."""
    winners: list[dict[str, object]] = []
    ordered = sorted(results, key=lambda item: item.wall_seconds)
    for backend in dict.fromkeys(item.backend for item in ordered):
        best = next(item for item in ordered if item.backend == backend)
        throughput = (scenario_count * simulations / best.wall_seconds
                      if best.wall_seconds > 0 else 0.0)
        winners.append({
            "backend": backend, "strategy": best.strategy,
            "wall_seconds": best.wall_seconds,
            "suite_sim_per_second": throughput,
        })
    best = ordered[0]
    winners.append({
        "backend": best.backend, "strategy": best.strategy,
        "wall_seconds": best.wall_seconds, "overall": True,
    })
    return winners


def print_tts_study_summary(
    cells: Sequence[dict[str, object]], *, scenarios: str | None = None,
) -> None:
    """Final console table: per cell and engine, the best strategy.

    Each row answers the planning question for one engine — how to split
    this workload — with the best strategy's wall time, its speedup over
    that engine's sequential pass (when measured) and the runner-up. The
    overall fastest engine/strategy of the cell is marked with ``*``.
    """
    scope = f" (scenarios {scenarios})" if scenarios else ""
    print(f"Time-to-solution study{scope}: "
          f"{len(cells)} cell(s), best strategy per engine:")
    headers = ["Simulations", "Batch", "Engine", "Best strategy", "Wall (s)",
               "vs sequential", "Runner-up", "Wall (s)"]
    rows = []
    for cell in cells:
        results: Sequence[TtsStrategyResult] = cell["results"]  # type: ignore[assignment]
        ordered = sorted(results, key=lambda item: item.wall_seconds)
        overall = ordered[0] if ordered else None
        for backend in dict.fromkeys(item.backend for item in ordered):
            same = [item for item in ordered if item.backend == backend]
            best = same[0]
            runner_up = same[1] if len(same) > 1 else None
            sequential = next(
                (item for item in same if item.strategy == "sequential"), None)
            speedup = (
                f"{sequential.wall_seconds / best.wall_seconds:.2f}x"
                if sequential is not None and best.wall_seconds > 0 else "-")
            rows.append([
                f"{cell['simulations']:,}", f"{cell['batch_size']:,}",
                backend + (" *" if best is overall else ""),
                best.strategy, f"{best.wall_seconds:.2f}", speedup,
                runner_up.strategy if runner_up is not None else "-",
                f"{runner_up.wall_seconds:.2f}" if runner_up is not None else "-",
            ])
    _print_ascii_table(headers, rows)


def _pool_start_method() -> str:
    """Start method a default ``ProcessPoolExecutor`` uses, without fixing it."""
    import multiprocessing

    return (multiprocessing.get_start_method(allow_none=True)
            or multiprocessing.get_all_start_methods()[0])


def benchmark_payload(
    results: tuple[BenchmarkResult, ...] | list[BenchmarkResult],
    unavailable: tuple[dict[str, str], ...] | list[dict[str, str]], *,
    simulations: int, batch_size: int, seed: int, warmups: int, repeats: int,
    processes: int = 1, backends: Sequence[str] | None = None,
) -> dict[str, object]:
    """Build a durable single-configuration benchmark artifact.

    ``configuration`` is the measurement design the baseline gate requires to
    match: besides the sizes it records ``processes`` (pooled units contend
    for cores, which changes per-unit throughput), the pool ``start_method``
    (``None`` when sequential) and the requested ``backends`` (sorted; when
    omitted, derived from the results and unavailable entries, which together
    name every requested backend). ``provenance`` records where it ran
    (:func:`mordheim_combat_lab.application.settings.measurement_provenance`).
    """
    from mordheim_combat_lab.application.settings import measurement_provenance

    if backends is None:
        backends = [item.backend for item in results]
        backends += [str(row["backend"]) for row in unavailable if "backend" in row]
    backend_list = sorted(set(backends))
    return {
        "schema": BENCHMARK_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": _environment(),
        "configuration": {
            "simulations": simulations, "batch_size": batch_size, "seed": seed,
            "warmups": warmups, "repeats": repeats, "processes": processes,
            "start_method": _pool_start_method() if processes > 1 else None,
            "backends": backend_list,
        },
        "provenance": measurement_provenance(backend_list),
        "results": [asdict(item) for item in results],
        "unavailable": list(unavailable),
    }


@dataclass(frozen=True, slots=True)
class BenchmarkUnit:
    """One parallelizable benchmark work unit: a scenario measurement.

    Everything the worker needs is embedded. ``fighters`` carries the
    scenario's precompiled pair (plain frozen dataclasses) so a pool worker
    never parses the frozen catalogue — that load costs seconds and would
    otherwise be paid once per worker process and distort pooled timings.
    ``batch`` is the unit's label in the pooled-execution report
    (:func:`speedup_payload`).
    """
    scenario: BenchmarkScenario
    backend: str
    simulations: int
    batch_size: int
    seed: int
    warmups: int
    repeats: int
    batch: str = ""
    fighters: tuple[CompiledFighter, CompiledFighter] | None = None


def _unit_worker(unit: BenchmarkUnit) -> BenchmarkResult:
    """Process-pool entry point; spawns import the CLI entry module first."""
    return run_benchmark(
        unit.scenario, simulations=unit.simulations, batch_size=unit.batch_size,
        seed=unit.seed, backend=unit.backend, warmups=unit.warmups,
        repeats=unit.repeats, fighters=unit.fighters,
    )


def run_benchmark_units(
    units: Sequence[BenchmarkUnit], *, processes: int = 1,
    on_progress: Callable[[], None] | None = None,
) -> tuple[tuple[BenchmarkResult, ...], tuple[tuple[str, float], ...],
           tuple[tuple[BenchmarkUnit, str], ...]]:
    """Run units sequentially, or through a process pool when ``processes > 1``.

    Returns ``(results, timings, failures)``. ``timings`` pairs ``unit.batch``
    names with each unit's engine-sample seconds (sum of its timed repeats,
    measured inside the worker; 0.0 if the unit failed). Warmups, pickling
    and IPC are not in it. ``failures`` pairs the failed units with their
    ``RuntimeError`` message so callers can report them like the sequential
    path does.

    Workers run ``unit.simulations`` duels; every unit gets the same ``seed`",
    so a unit measured sequentially and in pool mode produces the same
    ``BenchmarkResult`` (identical deterministic totals — only the timing
    metadata may differ between runs).
    """
    if processes < 1:
        raise ValueError("processes must be >= 1")
    if processes == 1:
        results = []
        timings = []
        failures = []
        for unit in units:
            try:
                result = run_benchmark(
                    unit.scenario, simulations=unit.simulations,
                    batch_size=unit.batch_size, seed=unit.seed,
                    backend=unit.backend, warmups=unit.warmups,
                    repeats=unit.repeats,
                    on_progress=on_progress,
                )
            except RuntimeError as error:
                failures.append((unit, str(error)))
                timings.append((unit.batch, 0.0))
                continue
            results.append(result)
            timings.append((unit.batch, sum(result.samples_seconds)))
        return (
            tuple(item for item in results if item is not None),
            tuple(timings), tuple(failures),
        )
    from concurrent.futures import ProcessPoolExecutor
    from concurrent.futures import as_completed

    if not units:
        return (), (), ()
    workers = max(1, min(processes, len(units)))
    results: list[BenchmarkResult | None] = [None] * len(units)
    timings: list[tuple[str, float]] = [("", 0.0)] * len(units)
    failures: list[tuple[BenchmarkUnit, str]] = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(_unit_worker, unit): index
            for index, unit in enumerate(units)
        }
        try:
            for future in as_completed(futures):
                index = futures[future]
                unit = units[index]
                try:
                    result = future.result()
                except RuntimeError as error:
                    failures.append((unit, str(error)))
                    continue
                results[index] = result
                timings[index] = (unit.batch, sum(result.samples_seconds))
                if on_progress is not None:
                    on_progress()
        finally:
            for future in futures:
                future.cancel()
    return (
        tuple(item for item in results if item is not None),
        tuple(timings), tuple(failures),
    )


def speedup_payload(
    timings: Sequence[tuple[str, float]], *, pool_wall: float, processes: int,
) -> dict[str, object] | None:
    """Report what a pooled execution measured — and nothing it did not.

    ``timings`` carries each unit's engine-sample seconds (worker-side);
    ``pool_wall`` is the measured wall time of the whole pooled execution.
    Rows list each unit's ``worker_seconds`` only: no sequential run is made,
    so no per-unit sequential time or speedup is known. The single pool-level
    figure is ``sample_concurrency`` = ``engine_sample_seconds / wall_seconds``
    — the average number of timed engine samples in flight. It is *not* a
    speedup over a sequential run: it ignores warmups and setup, and pooled
    samples run slower than sequential ones under contention.

    Returns ``None`` when there is no timing data (all units failed, or zero
    wall time).
    """
    worker_totals = {
        name: seconds for name, seconds in timings if name and seconds > 0
    }
    total = sum(worker_totals.values())
    if total <= 0 or pool_wall <= 0:
        return None
    concurrency = total / pool_wall
    return {
        "mode": "pooled-sample-concurrency", "processes": processes,
        "wall_seconds": pool_wall, "engine_sample_seconds": total,
        "sample_concurrency": concurrency,
        "rows": [{"unit": name, "worker_seconds": seconds}
                 for name, seconds in sorted(worker_totals.items())],
    }


def format_parallel_summary(report: Mapping[str, object]) -> str:
    """Console line for a :func:`speedup_payload` report."""
    return (
        f"Pooled execution: {report['processes']} processes; "
        f"{report['engine_sample_seconds']:.2f}s of engine samples in "
        f"{report['wall_seconds']:.2f}s wall -> sample concurrency "
        f"{report['sample_concurrency']:.2f} (not a speedup over a sequential run)"
    )


def sweep_payload(
    results: tuple[BenchmarkResult, ...] | list[BenchmarkResult],
    unavailable: tuple[dict[str, str], ...] | list[dict[str, str]], *,
    simulation_sizes: tuple[int, ...], batch_sizes: tuple[int, ...],
    seed: int, warmups: int, repeats: int,
) -> dict[str, object]:
    """Build a durable multi-configuration sweep artifact."""
    payload = {
        "schema": SWEEP_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": _environment(),
        "configuration": {
            "simulation_sizes": list(simulation_sizes),
            "batch_sizes": list(batch_sizes),
            "seed": seed, "warmups": warmups, "repeats": repeats,
        },
        "results": [asdict(item) for item in results],
        "unavailable": list(unavailable),
    }
    return payload


def _environment() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "processor": platform.processor(),
    }


def load_benchmark_payload(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != BENCHMARK_SCHEMA:
        raise ValueError(f"unsupported benchmark schema: {payload.get('schema')!r}")
    if not isinstance(payload.get("results"), list):
        raise ValueError("benchmark report has no results list")
    return payload


def write_report(path: Path, payload: dict[str, object]) -> None:
    """Write a benchmark or sweep payload as JSON, CSV or Markdown."""
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.casefold()
    results = payload.get("results", [])
    if suffix == ".csv":
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, delimiter=";")
            writer.writerow([
                "scenario", "engine", "simulations", "batch_size", "repeats",
                "median_seconds", "simulations_per_second",
            ])
            for item in results:
                writer.writerow([
                    item["scenario"], item["backend"], item["simulations"],
                    item["batch_size"], item["repeats"],
                    f"{item['median_seconds']:.6f}",
                    f"{item['simulations_per_second']:.1f}",
                ])
        return
    if suffix in {".md", ".markdown"}:
        path.write_text(
            _markdown_report(payload) + "\n", encoding="utf-8")
        return
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _markdown_report(payload: dict[str, object]) -> str:
    lines = ["# Combat benchmark report", ""]
    configuration = payload.get("configuration", {})
    lines.append(f"- generated: {payload.get('generated_at', '')}")
    environment = payload.get("environment", {})
    lines.append(
        f"- environment: python {environment.get('python')}, "
        f"numpy {environment.get('numpy')}"
    )
    lines.append(f"- configuration: {json.dumps(configuration)}")
    lines.append("")
    if payload.get("scenarios") is not None:
        lines.append(f"- scenarios: {payload['scenarios']}")
    if payload.get("comparison") is not None:
        comparison = payload["comparison"]
        lines.append(f"## Gate: {'PASS' if comparison['passed'] else 'FAIL'}")
        lines.append(f"{comparison['detail']}")
        for row in comparison["comparisons"]:
            lines.append(
                f"- {row['scenario']}/{row['backend']}: "
                f"{row['change_ratio']:+.2%} [{row['status']}]"
            )
        for row in comparison.get("missing", ()):
            lines.append(
                f"- {row['scenario']}/{row['backend']}: [MISSING] {row['reason']}")
        for warning in comparison.get("provenance_warnings", ()):
            lines.append(f"- {warning}")
        lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append("| scenario | engine | simulations | batch_size | repeats | median (s) | sim/s |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for item in payload.get("results", []):
        lines.append(
            f"| {item['scenario']} | {ENGINE_LABELS.get(item['backend'], item['backend'])} "
            f"| {item['simulations']:,} | {item['batch_size']:,} | {item['repeats']} "
            f"| {item['median_seconds']:.4f} | {item['simulations_per_second']:,.0f} |"
        )
    return "\n".join(lines)


def _missing_reason(scenario: str, backend: str,
                    unavailable: Sequence[Mapping[str, object]]) -> str:
    for row in unavailable:
        if row.get("backend") == backend and row.get("scenario") == scenario:
            return str(row.get("reason", "failed"))
    for row in unavailable:
        if row.get("backend") == backend and "scenario" not in row:
            return str(row.get("reason", "backend unavailable"))
    return "not measured in the current run"


def compare_with_baseline(
    results: tuple[BenchmarkResult, ...] | list[BenchmarkResult],
    baseline: dict[str, object], *, improvement_threshold: float = .10,
    regression_threshold: float = .05,
    unavailable: Sequence[Mapping[str, object]] = (),
) -> BenchmarkGate:
    """Apply the agreed optimization gate to every comparable engine result.

    All three engines participate: modular results gate modular optimization
    work exactly like the NumPy/native ones. Every (scenario, backend) result
    of the baseline must have a current counterpart: one that is missing —
    the unit raised, the backend is not compiled, the scenario was not run —
    fails the gate, with the reason taken from ``unavailable`` when it names
    the pair or backend.
    """
    previous = {
        (str(item["scenario"]), str(item["backend"])): float(item["simulations_per_second"])
        for item in baseline["results"]
    }
    measured = {(item.scenario, item.backend) for item in results}
    missing = tuple(
        BenchmarkMissing(scenario, backend,
                         _missing_reason(scenario, backend, unavailable))
        for scenario, backend in sorted(previous)
        if (scenario, backend) not in measured
    )
    comparisons = []
    for item in results:
        if (item.scenario, item.backend) not in previous:
            continue
        old = previous[(item.scenario, item.backend)]
        if old <= 0:
            raise ValueError(f"invalid baseline throughput for {item.scenario}/{item.backend}")
        change = item.simulations_per_second / old - 1.0
        status = (
            "IMPROVED" if change >= improvement_threshold else
            "REGRESSED" if change < -regression_threshold else "STABLE"
        )
        comparisons.append(BenchmarkComparison(
            item.scenario, item.backend, old, item.simulations_per_second, change, status,
        ))
    improved = any(item.status == "IMPROVED" for item in comparisons)
    regressed = any(item.status == "REGRESSED" for item in comparisons)
    if missing:
        detail = (
            f"{len(missing)} baseline result(s) have no current measurement: "
            + "; ".join(f"{item.scenario}/{item.backend} ({item.reason})"
                        for item in missing)
        )
    elif not comparisons:
        detail = "no comparable engine results found in baseline"
    elif regressed:
        detail = "at least one scenario exceeds the allowed regression"
    elif not improved:
        detail = "no scenario reaches the required improvement"
    else:
        detail = "required improvement reached without disallowed regressions"
    return BenchmarkGate(
        bool(comparisons) and improved and not regressed and not missing,
        improved, regressed, tuple(comparisons), detail, missing,
    )


def check_baseline_configuration(
    current: Mapping[str, object], recorded: object,
) -> list[str]:
    """Validate the measurement design; return the fields the baseline lacks.

    Raises ``ValueError`` when a field both configurations record differs:
    such measurements are not comparable. Fields the current run records but
    an older baseline does not are returned so the caller can warn — they
    are assumed to match.
    """
    if not isinstance(recorded, Mapping):
        raise ValueError("baseline has no configuration block")
    differing = [key for key in current
                 if key in recorded and recorded[key] != current[key]]
    differing += [key for key in recorded if key not in current]
    if differing:
        raise ValueError(
            "baseline measurement design differs from the current benchmark in "
            f"{', '.join(differing)}; the measurements are not comparable: "
            f"expected {dict(current)}, found {dict(recorded)}"
        )
    return [key for key in current if key not in recorded]


def baseline_provenance_warnings(
    payload: Mapping[str, object], baseline: Mapping[str, object], *,
    unrecorded_design: Sequence[str] = (), stream=None,
) -> tuple[str, ...]:
    """Print and return the provenance warnings of a baseline comparison.

    One warning for design fields the baseline predates (``unrecorded_design``)
    and one for a missing or differing ``provenance`` block; never raises.
    """
    from mordheim_combat_lab.application.settings import provenance_differences
    from mordheim_combat_lab.provenance import provenance_warning

    advice = (
        "Throughput changes may reflect that rather than the code under test; the "
        "gate still runs. Save a new baseline here (--output .json) for a "
        "like-for-like comparison."
    )
    warnings = []
    if unrecorded_design:
        configuration = payload.get("configuration")
        configuration = configuration if isinstance(configuration, Mapping) else {}
        assumed = ", ".join(f"{key}={configuration.get(key)!r}" for key in unrecorded_design)
        warnings.append(provenance_warning(
            "the benchmark baseline predates recording "
            f"{', '.join(unrecorded_design)}; assuming they match the current run "
            f"({assumed}), which cannot be verified.", stream=stream))
    current_provenance = payload.get("provenance")
    current_provenance = current_provenance if isinstance(current_provenance, Mapping) else {}
    recorded = baseline.get("provenance")
    if not isinstance(recorded, Mapping):
        warnings.append(provenance_warning(
            "the benchmark baseline records no provenance, so the machine, engine "
            f"sources and native build it was measured on are unknown. {advice}",
            stream=stream))
    else:
        differences = provenance_differences(recorded, current_provenance)
        if differences:
            warnings.append(provenance_warning(
                "the benchmark baseline was measured on another machine or engine: "
                + "; ".join(differences) + f". {advice}", stream=stream))
    return tuple(warnings)


def gate_against_baseline(
    payload: Mapping[str, object], baseline: Mapping[str, object],
    results: tuple[BenchmarkResult, ...] | list[BenchmarkResult], *,
    improvement_threshold: float = .10, regression_threshold: float = .05,
    stream=None,
) -> BenchmarkGate:
    """Full baseline gate for one single-configuration run.

    Raises ``ValueError`` when the measurement designs differ
    (:func:`check_baseline_configuration`). Provenance differences and
    design fields an older baseline does not record are printed as
    ``PROVENANCE WARNING`` and recorded in ``provenance_warnings``; they never
    fail the gate. Missing current results do (:func:`compare_with_baseline`).
    """
    configuration = payload["configuration"]
    assert isinstance(configuration, Mapping)
    unrecorded = check_baseline_configuration(configuration, baseline.get("configuration"))
    warnings = baseline_provenance_warnings(
        payload, baseline, unrecorded_design=unrecorded, stream=stream)
    gate = compare_with_baseline(
        results, dict(baseline), improvement_threshold=improvement_threshold,
        regression_threshold=regression_threshold,
        unavailable=payload.get("unavailable", ()),  # type: ignore[arg-type]
    )
    return replace(gate, provenance_warnings=warnings)


def _render_rows(results, unavailable) -> tuple[list[list[str]], list[str]]:
    """Return (aligned text rows, width hints) for a results table."""
    by_key = {(item.scenario, item.backend, item.simulations, item.batch_size): item
              for item in results}
    rows: list[list[str]] = []
    keys = sorted(by_key)
    for key in keys:
        item = by_key[key]
        rows.append([
            item.scenario,
            ENGINE_LABELS.get(item.backend, item.backend),
            f"{item.simulations:,}", f"{item.batch_size:,}", str(item.repeats),
            f"{item.simulations_per_second:,.0f}",
            f"{item.median_seconds * 1_000:.1f} ms",
        ])
    notes = [f"{row.get('engine', row['backend'])} not available: {row['reason']}"
             for row in unavailable]
    return rows, notes


def print_results_table(
    results: Iterable[BenchmarkResult], unavailable,
    *, simulations: int, batch_size: int, seed: int, repeats: int,
) -> None:
    items = list(results)
    headers = ["Scenario", "Engine", "Simulations", "Batch size", "Repeats",
               "sim/s", "Median"]
    rows, notes = _render_rows(items, unavailable)
    print(
        f"Benchmark: {simulations:,} simulations per scenario and engine "
        f"(batch size {batch_size:,}, seed {seed}, median of {repeats} repeats)."
    )
    _print_ascii_table(headers, rows)
    for note in notes:
        print(note)


def print_sweep_table(
    results: Iterable[BenchmarkResult], unavailable,
    *, simulation_sizes: tuple[int, ...], batch_sizes: tuple[int, ...],
    seed: int, repeats: int,
) -> None:
    items = list(results)
    headers = ["Scenario", "Engine", "Simulations", "Batch size", "Repeats",
               "sim/s", "Median"]
    rows, notes = _render_rows(items, unavailable)
    print(
        "Benchmark sweep: "
        + ", ".join(f"{value:,} simulations" for value in simulation_sizes)
        + "; batch sizes "
        + ", ".join(f"{value:,}" for value in batch_sizes)
        + f" (seed {seed}, median of {repeats} repeats)."
    )
    _print_ascii_table(headers, rows)
    for note in notes:
        print(note)


def _print_ascii_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [max([len(headers[index])] + [len(row[index]) for row in rows])
              for index in range(len(headers))]
    def line(values: list[str]) -> str:
        return " | ".join(f"{value:<{widths[index]}}" for index, value in enumerate(values))
    print(line(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(line(row))


def print_gate(gate: BenchmarkGate, *, improvement: float, regression: float) -> None:
    print(
        f"Comparison with baseline (required improvement {improvement:g} %, "
        f"maximum regression {regression:g} %):"
    )
    for item in gate.comparisons:
        print(
            f"  {item.scenario}/{item.backend}: {item.change_ratio:+.2%} "
            f"[{item.status}]"
        )
    for item in gate.missing:
        print(f"  {item.scenario}/{item.backend}: [MISSING] {item.reason}")
    if gate.provenance_warnings:
        print(f"  ({len(gate.provenance_warnings)} provenance warning(s) recorded "
              "in the report; see above)")
    print(f"Performance gate: {'PASS' if gate.passed else 'FAIL'} - {gate.detail}")


def print_elapsed_summary(
    *, elapsed_seconds: float, engine_seconds: float, processes: int = 1,
    warmup_seconds: float = 0.0,
) -> None:
    """Console summary of the whole command's wall time vs engine samples.

    ``engine_seconds`` sums every timed repeat execution and
    ``warmup_seconds`` the untimed warm-up executions, so the sequential
    remainder is genuine setup/overhead (interpreter start, catalogue load),
    not hidden engine work. In pool mode the samples ran concurrently and
    their sum may legitimately exceed the wall time.
    """
    if processes > 1:
        print(
            f"Total wall time: {elapsed_seconds:.2f}s ({processes} processes; "
            f"the {engine_seconds:.2f}s of engine samples ran concurrently)."
        )
        return
    overhead = max(0.0, elapsed_seconds - engine_seconds - warmup_seconds)
    warmups = f"{warmup_seconds:.2f}s in warm-ups, " if warmup_seconds else ""
    print(
        f"Total wall time: {elapsed_seconds:.2f}s (sequential; "
        f"{engine_seconds:.2f}s in engine samples, {warmups}"
        f"{overhead:.2f}s setup and overhead)."
    )


class BenchmarkProgress:
    """Minimal progress bar for already-completed work units."""

    def __init__(self, total: int) -> None:
        self.total = total
        self.completed = 0
        self.rendered = False
        self._render()

    def advance(self) -> None:
        self.completed += 1
        self._render()

    def finish(self) -> None:
        if self.rendered:
            print()

    def _render(self) -> None:
        if not self.total:
            return
        width = 24
        completed = min(self.completed, self.total)
        filled = round(width * completed / self.total)
        percent = completed * 100 // self.total
        print(
            f"\rProgress: [{'#' * filled}{'-' * (width - filled)}] "
            f"{percent:3}% ({completed}/{self.total})",
            end="", flush=True,
        )
        self.rendered = True

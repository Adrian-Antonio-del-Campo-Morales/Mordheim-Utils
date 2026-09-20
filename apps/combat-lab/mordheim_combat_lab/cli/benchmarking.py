"""Benchmark suite and CLI presenters for the combat backends.

Runs the maintained end-to-end scenarios against the modular, NumPy and
native engines, supports single-configuration runs (with baseline
comparison gates) and size sweeps over simulation counts and batch
sizes, and renders results as console tables, JSON, CSV or Markdown.
"""
from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime, timezone
import csv
import json
from pathlib import Path
import platform
from statistics import median
from time import perf_counter
from typing import Callable
from typing import Iterable
from typing import Sequence

import numpy as np

from mordheim_combat.modular.duel import simulate_duel as simulate_modular_duel
from mordheim_combat.vectorized import simulate_duel
from mordheim_construction.compiler import compile_fighter
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


@dataclass(frozen=True, slots=True)
class BenchmarkComparison:
    scenario: str
    backend: str
    baseline_simulations_per_second: float
    current_simulations_per_second: float
    change_ratio: float
    status: str


@dataclass(frozen=True, slots=True)
class BenchmarkGate:
    passed: bool
    improved: bool
    regressed: bool
    comparisons: tuple[BenchmarkComparison, ...]
    detail: str


BENCHMARK_SCHEMA = "mordheim-combat-benchmark/v1"
SWEEP_SCHEMA = "mordheim-combat-benchmark-sweep/v1"
TTS_SCHEMA = "mordheim-combat-benchmark-tts/v1"

ENGINE_LABELS = {"modular": "Modular", "numpy": "Vectorized", "native": "Native"}




# ---------------------------------------------------------------------------
# Scenario definitions (pure data) live in `scenarios.py`; this module
# re-exports them so every historical import path keeps working
# (`benchmarking.DEEP_SCENARIOS`, ...).
# ---------------------------------------------------------------------------
from mordheim_combat_lab.cli.scenarios import (  # noqa: E402
    DEEP_SCENARIOS,
    DEEP_SCENARIO_SET_IDS,
    FAST_DEEP_SCENARIO_IDS,
    FULL_DEEP_SCENARIO_IDS,
    MINI_DEEP_SCENARIO_IDS,
    BenchmarkScenario,
    deep_test_scenarios,
    benchmark_scenarios,
    _build,
)
def compile_benchmark_fighters(
    scenario: BenchmarkScenario,
) -> tuple[CompiledFighter, CompiledFighter]:
    """Compile a matrix scenario, applying only its benchmark attack tags.

    The tags are deliberately applied after normal construction.  This keeps
    synthetic coverage probes out of the engine and KB while still sending
    the exact resulting ``EffectSet`` through modular, NumPy and native.
    """
    compiled = []
    for build, tags in (
        (scenario.first, scenario.first_attack_tags),
        (scenario.second, scenario.second_attack_tags),
    ):
        fighter = compile_fighter(build)
        if tags:
            weapon = replace(
                fighter.main_weapon,
                tags=tuple(dict.fromkeys((*fighter.main_weapon.tags, *tags))),
            )
            fighter = replace(fighter, main_weapon=weapon)
        compiled.append(fighter)
    return compiled[0], compiled[1]


def deep_test_scenarios(pair_set: str = "full") -> tuple[BenchmarkScenario, ...]:
    """Return one of the maintained deep-testing pair sets.

    ``full`` is the maintained 42-pair matrix. ``fast`` is a 30-pair
    coverage-oriented subset: it retains every distinct non-default compiled
    effect axis represented by the current full matrix (including the
    synthetic blessed boundary), the long-round timing representative, the
    high-value orchestration amplifiers and every newly added rule-family
    boundary, while omitting redundant baselines and mirrors. It deliberately
    keeps ``heavy-grind`` and ``ithilmar-duel`` because they add the only
    long-round and Ithilmar axes otherwise lost from the fast set.

    ``mini`` is a 10-pair performance-survey subset: one cheap-to-expensive
    representative per cost axis (batch overhead, typical pool, 75-round
    grind) and per behaviour family (conditional attacks, special saves,
    stacked saves, poison, frenzy, pool manipulation, random
    characteristics).

    The set selection is benchmark metadata only. It does not alter fighter
    construction or any combat/KB implementation. ``blessed-vs-regen`` still
    uses the benchmark-only ``attack.blessed`` tag described above.
    """
    try:
        selected_ids = DEEP_SCENARIO_SET_IDS[pair_set]
    except KeyError as error:
        raise ValueError(
            f"unknown deep pair set {pair_set!r}; choose 'mini', 'fast' or 'full'"
        ) from error
    by_id = {scenario.id: scenario for scenario in DEEP_SCENARIOS}
    return tuple(by_id[scenario_id] for scenario_id in selected_ids)


@dataclass(frozen=True, slots=True)
class DeepBenchmarkPlan:
    """Runs for a ``--deep`` benchmark: a small modular reference plus the
    vectorized grid. The modular oracle is deliberately only measured at the
    reference size so deep sweeps stay feasible."""
    vector_sizes: tuple[int, ...]
    batch_sizes: tuple[int, ...]
    modular_simulations: int
    modular_backend: str | None
    vector_backends: tuple[str, ...]
    runs: tuple[tuple[str, str, int, int], ...]  # (scenario id, backend, simulations, batch_size)
    excluded: tuple[dict[str, str], ...]


def deep_benchmark_plan(
    scenarios: tuple[BenchmarkScenario, ...], *,
    vector_sizes: tuple[int, ...], batch_sizes: tuple[int, ...],
    modular_simulations: int, backends: tuple[str, ...], installed: tuple[str, ...],
) -> DeepBenchmarkPlan:
    """Plan a deep benchmark run without executing anything.

    Policy: the modular engine is measured only at ``modular_simulations``
    (a reference point; it is the slow oracle). The optimized backends
    (NumPy and, when compiled, native) are swept over the full size and
    batch-size grid. Only requested backends are included; modular is never
    part of the large grid.
    """
    requested = backends
    excluded = []
    vector_backends = []
    for backend in ("numpy", "native"):
        if backend not in requested:
            continue
        if backend not in installed:
            excluded.append({"backend": backend,
                             "reason": "backend is not compiled in this environment"})
            continue
        vector_backends.append(backend)
    vector_backends = tuple(vector_backends)
    runs = []
    if "modular" in requested:
        for scenario in scenarios:
            runs.append((scenario.id, "modular", modular_simulations, batch_sizes[0]))
    for scenario in scenarios:
        for simulations in vector_sizes:
            for batch_size in batch_sizes:
                for backend in vector_backends:
                    runs.append((scenario.id, backend, simulations, batch_size))
    return DeepBenchmarkPlan(
        vector_sizes, batch_sizes, modular_simulations,
        "modular" if "modular" in requested else None,
        vector_backends, tuple(runs), tuple(excluded),
    )


def print_deep_benchmark_header(
    plan: DeepBenchmarkPlan, *, pair_set: str | None = None,
) -> None:
    label = f"{pair_set} pair set; " if pair_set else ""
    print(
        "Deep benchmark: " + label
        + (f"modular reference at {plan.modular_simulations:,} duels/scenario; "
           if plan.modular_backend else "")
        + f"{', '.join(plan.vector_backends)} swept over sizes "
        f"{', '.join(f'{size:,}' for size in plan.vector_sizes)} x batches "
        f"{', '.join(f'{size:,}' for size in plan.batch_sizes)} "
        f"across {sum(run[1] == 'modular' for run in plan.runs):,} scenarios."
    )


def parse_sizes(value: str | None, default: int) -> tuple[int, ...]:
    """Parse a size list such as "1k,10k 100k" into positive integers."""
    if not value or not value.strip():
        return (default,)
    sizes = []
    for token in value.replace(";", ",").replace(" ", ",").split(","):
        token = token.strip().lower()
        if not token:
            continue
        multiplier = 1
        if token.endswith("k"):
            multiplier, token = 1_000, token[:-1]
        elif token.endswith("m"):
            multiplier, token = 1_000_000, token[:-1]
        try:
            parsed = int(token) * multiplier
        except ValueError as error:
            raise ValueError(
                f"invalid size token {token!r}; use plain integers or k/m suffixes"
            ) from error
        if parsed < 1:
            raise ValueError("benchmark sizes must be positive")
        sizes.append(parsed)
    if not sizes:
        raise ValueError("no benchmark sizes provided")
    return tuple(dict.fromkeys(sizes))


def run_benchmark(
    scenario: BenchmarkScenario, *, simulations: int, batch_size: int,
    seed: int, backend: str, warmups: int, repeats: int,
    on_progress: Callable[[], None] | None = None,
) -> BenchmarkResult:
    if backend not in {"modular", "numpy", "native"}:
        raise ValueError(f"unknown benchmark backend: {backend}")
    first, second = compile_benchmark_fighters(scenario)
    request = DuelRequest(
        first, second, simulations, seed=seed, batch_size=batch_size,
        maximum_rounds=scenario.maximum_rounds,
    )

    def execute() -> None:
        if backend == "modular":
            simulate_modular_duel(request)
        else:
            simulate_duel(request, backend=backend)

    for _ in range(warmups):
        execute()
        if on_progress is not None:
            on_progress()
    samples = []
    for _ in range(repeats):
        started = perf_counter()
        execute()
        samples.append(perf_counter() - started)
        if on_progress is not None:
            on_progress()
    middle = median(samples)
    return BenchmarkResult(
        scenario.id, backend, simulations, batch_size, repeats, tuple(samples),
        middle, simulations / middle,
    )


# ---------------------------------------------------------------------------
# Time-to-solution (--tts): the workload is fixed and whole execution
# strategies are compared by the wall time of solving it completely —
# throughput rows diagnose *why* one strategy wins, this mode decides *which*
# one to use. Every strategy runs the same per-batch streams, so the
# deterministic win/loss/unresolved totals double as a correctness gate.
# ---------------------------------------------------------------------------


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
    """Parse the ``--tts`` strategy list into canonical strategy tokens.

    Accepts ``sequential``, ``processes=N`` and ``parallel=N`` (N >= 2; N=1
    canonicalizes to ``sequential``). Defaults to the three-way comparison.
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
        number = number.strip()
        if (not separator or mode not in {"processes", "parallel"}
                or not number.isdigit() or int(number) < 1):
            raise ValueError(
                f"invalid TTS strategy {token!r}; use 'sequential', "
                f"'processes=N' or 'parallel=N'")
        if int(number) == 1:
            strategies.append("sequential")
            continue
        strategies.append(f"{mode}={int(number)}")
    if not strategies:
        raise ValueError("no TTS strategies provided")
    return tuple(dict.fromkeys(strategies))


def _tts_sequential_worker(
    scenario: BenchmarkScenario, *, simulations: int, batch_size: int, seed: int,
    backend: str = "numpy",
) -> tuple[float, tuple[int, int, int]]:
    """One workload pass for one scenario in-process; returns (wall, totals).

    Module-level so the scenario-pool strategy can submit it directly.
    """
    first, second = compile_benchmark_fighters(scenario)
    request = DuelRequest(
        first, second, simulations, seed=seed, batch_size=batch_size,
        maximum_rounds=scenario.maximum_rounds,
    )
    started = perf_counter()
    result = simulate_duel(request, backend=backend)
    return perf_counter() - started, (
        result.first_wins, result.second_wins, result.unresolved)


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
    in a process pool (``processes=N``), or — NumPy only — each scenario's
    batch plan split over a pool (``parallel=N``).
    """
    if repeats < 1:
        raise ValueError("repeats must be >= 1")

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
        mode, _, number = strategy.partition("=")
        processes = int(number)
        if mode == "processes":
            from concurrent.futures import ProcessPoolExecutor
            started = perf_counter()
            with ProcessPoolExecutor(max_workers=processes) as pool:
                futures = {
                    pool.submit(
                        _tts_sequential_worker, scenario,
                        simulations=simulations, batch_size=batch_size,
                        seed=seed, backend=backend,
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
    mode_label = ("sequential" if strategy == "sequential"
                  else strategy.partition("=")[0] + "-pool")
    return TtsStrategyResult(
        strategy, mode_label,
        1 if strategy == "sequential" else int(strategy.partition("=")[2]),
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
    """Run every (strategy, backend) combination on one workload cell.

    ``parallel=N`` is skipped for non-NumPy backends (it is a NumPy-driver
    pool); the results are the rows of the cell's ranking. All combinations
    execute the same per-batch streams, so their totals must agree — the
    caller cross-checks them as a parity gate.
    """
    results: list[TtsStrategyResult] = []
    for backend in backends:
        for strategy in strategies:
            if strategy.startswith("parallel=") and backend != "numpy":
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
    pair_set: str | None = None, elapsed_seconds: float | None = None,
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
    if pair_set is not None:
        payload["pair_set"] = pair_set
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
    cells: Sequence[dict[str, object]], *, pair_set: str | None = None,
) -> None:
    """Final console table: one row per study cell with its winners."""
    scope = f" ({pair_set} pair set)" if pair_set else ""
    print(f"Time-to-solution study{scope}: "
          f"{len(cells)} cell(s), winners per cell:")
    headers = ["Simulations", "Batch", "Winner", "Wall (s)",
               "Runner-up", "Wall (s)"]
    rows = []
    for cell in cells:
        winners: list[dict[str, object]] = cell["winners"]  # type: ignore[assignment]
        overall = next(
            (item for item in winners if item.get("overall")), winners[0])
        runner_up = next(
            (item for item in winners
             if item is not overall and item.get("backend") != overall["backend"]),
            None)
        if runner_up is None:
            runner_up = next(
                (item for item in winners if item is not overall), None)
        rows.append([
            f"{cell['simulations']:,}", f"{cell['batch_size']:,}",
            f"{overall['backend']}/{overall['strategy']}",
            f"{overall['wall_seconds']:.2f}",
            (f"{runner_up['backend']}/{runner_up['strategy']}"
             if runner_up is not None else "-"),
            (f"{runner_up['wall_seconds']:.2f}"
             if runner_up is not None else "-"),
        ])
    _print_ascii_table(headers, rows)


def benchmark_payload(
    results: tuple[BenchmarkResult, ...] | list[BenchmarkResult],
    unavailable: tuple[dict[str, str], ...] | list[dict[str, str]], *,
    simulations: int, batch_size: int, seed: int, warmups: int, repeats: int,
) -> dict[str, object]:
    """Build a durable single-configuration benchmark artifact."""
    return {
        "schema": BENCHMARK_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": _environment(),
        "configuration": {
            "simulations": simulations, "batch_size": batch_size, "seed": seed,
            "warmups": warmups, "repeats": repeats,
        },
        "results": [asdict(item) for item in results],
        "unavailable": list(unavailable),
    }


@dataclass(frozen=True, slots=True)
class BenchmarkUnit:
    """One parallelizable benchmark work unit: a scenario measurement.

    Everything the worker needs is embedded (fighters are compiled there, so
    the payload stays plain data). ``batch`` names the unit in the speedup
    report and reuses the request's ``batch_size`` semantics.
    """
    scenario: BenchmarkScenario
    backend: str
    simulations: int
    batch_size: int
    seed: int
    warmups: int
    repeats: int
    batch: str = ""


def _unit_worker(unit: BenchmarkUnit) -> BenchmarkResult:
    """Process-pool entry point; spawns import the CLI entry module first."""
    return run_benchmark(
        unit.scenario, simulations=unit.simulations, batch_size=unit.batch_size,
        seed=unit.seed, backend=unit.backend, warmups=unit.warmups,
        repeats=unit.repeats,
    )


def run_benchmark_units(
    units: Sequence[BenchmarkUnit], *, processes: int = 1,
    on_progress: Callable[[], None] | None = None,
) -> tuple[tuple[BenchmarkResult, ...], tuple[tuple[str, float], ...]]:
    """Run units sequentially, or through a process pool when ``processes > 1``.

    Returns ``(results, timings, failures)``. ``timings`` pairs ``unit.batch`` names with
    each unit's measured wall seconds (sum of its samples; 0.0 if the unit
    failed) — in pool mode the pool transport (pickling + IPC) is included,
    so reported speedup is what the machine actually delivered.
    ``failures`` pairs the failed units with their ``RuntimeError`` message so
    callers can report them like the sequential path does.

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
    """Assemble the real-speedup report from pooled per-unit worker samples.

    ``timings`` carries each unit's measured engine seconds (worker-side);
    ``pool_wall`` is the measured wall time of the whole pooled execution.
    The sequential equivalent of every unit is estimated by splitting the
    wall by each unit's share of the total worker samples — re-running the
    identical sweep sequentially would double the wall time of full deep
    profiles, so the estimate is reused instead. Returns ``None`` when there
    is no comparable timing data (all units failed, or zero wall time).
    """
    worker_totals = {
        name: seconds for name, seconds in timings if name and seconds > 0
    }
    total = sum(worker_totals.values())
    if total <= 0 or pool_wall <= 0:
        return None
    rows = []
    for name, seconds in sorted(worker_totals.items()):
        sequential_estimate = pool_wall * seconds / total
        rows.append({
            "unit": name, "worker_seconds": seconds,
            "estimated_sequential_seconds": sequential_estimate,
            "speedup": seconds / sequential_estimate,
        })
    return {
        "mode": "worker-estimate-vs-wall", "processes": processes,
        "wall_seconds": pool_wall, "speedup": total / pool_wall,
        "rows": rows,
    }


def sweep_payload(
    results: tuple[BenchmarkResult, ...] | list[BenchmarkResult],
    unavailable: tuple[dict[str, str], ...] | list[dict[str, str]], *,
    simulation_sizes: tuple[int, ...], batch_sizes: tuple[int, ...],
    seed: int, warmups: int, repeats: int,
    pair_set: str | None = None,
) -> dict[str, object]:
    """Build a durable multi-configuration sweep artifact.

    ``pair_set`` is recorded only for the deep pair-matrix profile; ordinary
    five-scenario benchmark sweeps keep the historical payload shape.
    """
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
    if pair_set is not None:
        payload["pair_set"] = pair_set
    return payload


def _environment() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "processor": platform.processor(),
    }


def write_benchmark_payload(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


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
    if payload.get("pair_set") is not None:
        lines.append(f"- pair set: {payload['pair_set']}")
    if payload.get("comparison") is not None:
        comparison = payload["comparison"]
        lines.append(f"## Gate: {'PASS' if comparison['passed'] else 'FAIL'}")
        lines.append(f"{comparison['detail']}")
        for row in comparison["comparisons"]:
            lines.append(
                f"- {row['scenario']}/{row['backend']}: "
                f"{row['change_ratio']:+.2%} [{row['status']}]"
            )
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


def compare_with_baseline(
    results: tuple[BenchmarkResult, ...] | list[BenchmarkResult],
    baseline: dict[str, object], *, improvement_threshold: float = .10,
    regression_threshold: float = .05,
) -> BenchmarkGate:
    """Apply the agreed optimization gate to comparable NumPy/native results."""
    previous = {
        (str(item["scenario"]), str(item["backend"])): float(item["simulations_per_second"])
        for item in baseline["results"]
    }
    comparisons = []
    for item in results:
        if item.backend == "modular" or (item.scenario, item.backend) not in previous:
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
    if not comparisons:
        detail = "no comparable NumPy/native results found in baseline"
    elif regressed:
        detail = "at least one scenario exceeds the allowed regression"
    elif not improved:
        detail = "no scenario reaches the required improvement"
    else:
        detail = "required improvement reached without disallowed regressions"
    return BenchmarkGate(bool(comparisons) and improved and not regressed,
                         improved, regressed, tuple(comparisons), detail)


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
    print(f"Performance gate: {'PASS' if gate.passed else 'FAIL'} - {gate.detail}")


def print_elapsed_summary(
    *, elapsed_seconds: float, engine_seconds: float, processes: int = 1,
) -> None:
    """Console summary of the whole command's wall time vs engine samples.

    ``engine_seconds`` sums every timed repeat execution (warmups are not
    recorded in ``samples_seconds``). Sequentially it can never exceed the
    wall time, so the remainder is genuine setup/overhead; in pool mode the
    samples ran concurrently and may legitimately exceed it.
    """
    if processes > 1:
        print(
            f"Total wall time: {elapsed_seconds:.2f}s ({processes} processes; "
            f"the {engine_seconds:.2f}s of engine samples ran concurrently)."
        )
        return
    overhead = max(0.0, elapsed_seconds - engine_seconds)
    print(
        f"Total wall time: {elapsed_seconds:.2f}s (sequential; "
        f"{engine_seconds:.2f}s in engine samples, "
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

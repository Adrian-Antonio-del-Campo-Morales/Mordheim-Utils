"""calibrate: measure this machine's optima and install a calibration profile.

Sweeps the deep scenario matrix — every duel type the certification suite
knows — across the three configuration axes the Combat Lab resolves at run
time, for both engines, and writes ``calibration.json`` next to the user
preferences. The app loads that profile at startup
(:func:`mordheim_combat_lab.application.settings.apply_calibration`), so the
measured optima of *this* machine replace the reference-machine constants.

Measured axes (candidates in parentheses):

* sequential batch — ``application.settings.DEFAULT_BATCH_SIZES``
  (native 2.5k/5k/10k/20k; numpy 25k/50k/100k, sized so every candidate
yields at least three batches at the sweep size)
* pooled batch — ``POOLED_BATCH_SIZES``
  (native 2.5k/5k/10k/20k; numpy 12.5k/25k/50k/100k)
* pool workers — ``POOL_WORKERS``
  (native 8/10/12/14/16; numpy 4/6/8/10)
* pool spawn cost — ``POOL_SPAWN_SECONDS`` (median of repeated spawns)

The raw evidence also yields the machine's **pool speedup curve**:
``application.settings.measured_pool_speedups`` turns the sequential/pooled
per-duel ratios of every measured worker count into the segment → speedup
model the app installs, so the pool decision runs on this machine's measured
parallel efficiency instead of the shared conservative fit.

Coverage and budget (defaults on the reference machine, ~8-10 minutes):
native sweeps run the full 42-pair matrix at 1M samples/fighter; NumPy sweeps
run the stratified 30-pair set at a quarter/half of the sizes, because its
duels cost ~3-5x more. ``--pairs mini`` trades coverage for a ~2 minute run.
Every candidate is scored by the geometric mean of its per-pair ratio to the
best candidate, so all duel types weigh the same regardless of absolute cost;
a candidate within 2% of the best never displaces the reference value, so run
noise does not churn the profile.
"""

from __future__ import annotations

import json
import os
import platform
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from mordheim_combat.vectorized import available_backends
from mordheim_combat.vectorized import batch_plan
from mordheim_combat.vectorized import simulate_duel
from mordheim_combat_lab.application.settings import (
    CALIBRATION_SCHEMA,
    DEFAULT_BATCH_SIZES,
    POOLED_BATCH_SIZES,
    POOL_SPAWN_SECONDS,
    POOL_WORKERS,
    DuelExecutionSettings,
    apply_calibration,
    measured_pool_speedups,
    simulate_battery,
    split_battery,
)
from mordheim_combat_lab.cli.scenarios import deep_test_scenarios
from mordheim_construction.compiler import compile_fighter

#: Batch candidates for the sequential sweep (the engines disagree: native
#: collapses with large batches, numpy with small ones). The numpy sample size
#: below guarantees at least three batches per candidate — a candidate larger
#: than the sample degenerates to a single batch and only measures per-duel
#: cost, not the batch plan.
SEQUENTIAL_BATCH_CANDIDATES = {
    "native": (2_500, 5_000, 10_000, 20_000),
    "numpy": (25_000, 50_000, 100_000),
}

#: Batch candidates for the pooled sweep.
POOLED_BATCH_CANDIDATES = {
    "native": (2_500, 5_000, 10_000, 20_000),
    "numpy": (12_500, 25_000, 50_000, 100_000),
}

#: Worker candidates per backend (numpy regresses past 8: memory bandwidth).
WORKER_CANDIDATES = {
    "native": (8, 10, 12, 14, 16),
    "numpy": (4, 6, 8, 10),
}

#: Sample sizes per sweep before the user scale factors (numpy costs ~3-5x
#: per duel, so its sweeps run smaller). The numpy sequential size is anchored
#: to its largest batch candidate (three batches minimum) and capped so a
#: wide run stays inside the time budget.
SEQUENTIAL_SAMPLES = 500_000
POOLED_SAMPLES = 1_000_000
NUMPY_POOLED_FACTOR = 2
NUMPY_SEQUENTIAL_CEILING = 300_000
NUMPY_SEQUENTIAL_FLOOR = 50_000
MINIMUM_SAMPLES = 10_000

#: A candidate within this factor of the best score never displaces the
#: reference value: cheap-pair noise is 3-30%, so sub-2% wins are not signal.
TIE_TOLERANCE = 1.02


def _clock(seconds: float) -> str:
    minutes, rest = divmod(int(seconds), 60)
    return f"{minutes}m {rest:02d}s" if minutes else f"{rest}s"


def _geomean(values) -> float:
    values = [value for value in values if value > 0]
    if not values:
        return 1.0
    return statistics.geometric_mean(values)


def _pairs(pair_set: str):
    """Compiled (first, second, maximum_rounds, id) rows for one pair set."""
    return [
        (compile_fighter(scenario.first), compile_fighter(scenario.second),
         scenario.maximum_rounds or 50, scenario.id)
        for scenario in deep_test_scenarios(pair_set)
    ]


def _scores(table: dict) -> dict:
    """Per-candidate score: geometric mean of its per-pair ratio to the best.

    Normalising per pair keeps a 5 µs grind from drowning out a 0.7 µs duel:
    every duel type weighs the same when the winner is chosen.
    """
    keys = list(table)
    if not keys:
        return {}
    width = len(next(iter(table.values())))
    result = {}
    for key in keys:
        ratios = []
        for index in range(width):
            best = min(table[other][index] for other in keys if table[other][index] > 0)
            ratios.append(table[key][index] / best)
        result[key] = round(_geomean(ratios), 4)
    return result


def _winner(scores: dict, reference):
    """Best-scoring candidate, keeping the reference value inside the noise."""
    best = min(scores, key=scores.get)
    if reference in scores and scores[reference] <= scores[best] * TIE_TOLERANCE:
        return reference
    return best


def _sequential_walls(pairs, backend, samples, batch, seed):
    walls = []
    for first, second, rounds, _identifier in pairs:
        settings = DuelExecutionSettings(samples, seed, batch, rounds)
        started = time.perf_counter()
        simulate_duel(settings.request(first, second), backend=backend)
        walls.append(time.perf_counter() - started)
    return walls


def _pooled_walls(pairs, backend, samples, batch, workers, seed):
    segments = len(split_battery(samples, batch, workers))
    executor = ProcessPoolExecutor(max_workers=segments)
    walls = []
    try:
        for first, second, rounds, _identifier in pairs:
            settings = DuelExecutionSettings(samples, seed, batch, rounds)
            started = time.perf_counter()
            simulate_battery(first, second, settings, workers=workers,
                             pool=executor, backend=backend)
            walls.append(time.perf_counter() - started)
    finally:
        executor.shutdown()
    return walls


def _spawn_probe(_index):
    return 0


def measure_spawn(workers: int, repetitions: int = 3) -> float:
    """Median wall seconds of creating, feeding and tearing down one pool."""
    walls = []
    for _ in range(max(1, repetitions)):
        started = time.perf_counter()
        with ProcessPoolExecutor(max_workers=max(1, workers)) as executor:
            list(executor.map(_spawn_probe, range(max(1, workers))))
        walls.append(time.perf_counter() - started)
    return round(statistics.median(walls), 4)


#: Progress clock shared by the sweeps: completed work units, total units
#: and the start time, so every candidate line can print an ETA.
_PROGRESS = {"completed": 0, "total": 0, "started": 0.0}


def _sweep(label, pairs, candidates, measure, log) -> dict:
    """Run one candidate sweep, logging progress and returning the raw table."""
    table: dict = {}
    for candidate in candidates:
        table[candidate] = measure(candidate)
        total = sum(table[candidate])
        _PROGRESS["completed"] += len(pairs)
        eta = ""
        if _PROGRESS["total"]:
            spent = time.perf_counter() - _PROGRESS["started"]
            remaining = spent / _PROGRESS["completed"] * (
                _PROGRESS["total"] - _PROGRESS["completed"])
            eta = f", ETA {_clock(remaining)}"
        log(f"  {label} {candidate:>8,}: {total:7.2f}s "
            f"(elapsed {_clock(time.perf_counter() - _PROGRESS['started'])}{eta})")
    return table


def run_calibration(pair_set: str = "full", *, seed: int = 7,
                    sequential_samples: int = SEQUENTIAL_SAMPLES,
                    pooled_samples: int = POOLED_SAMPLES,
                    sequential_batches=None, pooled_batches=None,
                    worker_candidates=None, spawn_repetitions: int = 3,
                    log=print) -> dict:
    """Measure this machine and return the calibration payload.

    The keyword overrides exist for tests (small sizes) and future re-tuning;
    the CLI maps its arguments to the defaults above.
    """
    backends = set(available_backends())
    native_available = "native" in backends
    numpy_set = "mini" if pair_set == "mini" else "fast"
    sets = {"native": pair_set, "numpy": numpy_set if native_available else pair_set}
    pairs = {backend: _pairs(name) for backend, name in sets.items()}
    candidates = {
        "sequential_batch": sequential_batches or SEQUENTIAL_BATCH_CANDIDATES,
        "pooled_batch": pooled_batches or POOLED_BATCH_CANDIDATES,
        "workers": worker_candidates or WORKER_CANDIDATES,
    }
    samples = {
        "native": {"sequential": sequential_samples, "pooled": pooled_samples},
        "numpy": {
            "sequential": min(
                NUMPY_SEQUENTIAL_CEILING,
                max(NUMPY_SEQUENTIAL_FLOOR,
                    4 * max(candidates["sequential_batch"]["numpy"]),
                    sequential_samples // 4),
            ),
            "pooled": max(MINIMUM_SAMPLES, pooled_samples // NUMPY_POOLED_FACTOR),
        },
    }
    if not native_available:
        log("native backend unavailable: calibrating the numpy fallback only")
    order = [backend for backend in ("native", "numpy") if backend in backends]
    # Work units per phase, for the progress ETA (candidates x pairs).
    units = sum(
        len(candidates["sequential_batch"][backend]) * len(pairs[backend])
        + len(candidates["pooled_batch"][backend]) * len(pairs[backend])
        + len(candidates["workers"][backend]) * len(pairs[backend])
        for backend in order
    )
    _PROGRESS.update(completed=0, total=units, started=time.perf_counter())

    evidence: dict = {}
    winners: dict = {"batch_sizes": {}, "pooled_batch_sizes": {},
                     "pool_workers": {}, "spawn_seconds": {}}
    for backend in order:
        backend_pairs = pairs[backend]
        backend_samples = samples[backend]
        row = {}
        log(f"{backend}: {len(backend_pairs)} duel types, "
            f"sequential at {backend_samples['sequential']:,}, "
            f"pooled at {backend_samples['pooled']:,}")

        # One pass per axis, with a deliberate order: the pooled batch is
        # measured under the reference worker count, then the workers are
        # tuned against the winning batch — iterating to a fixed point would
        # multiply the runtime for a second-order correction.
        sequential = _sweep(
            "sequential batch", backend_pairs,
            candidates["sequential_batch"][backend],
            lambda batch: _sequential_walls(
                backend_pairs, backend, backend_samples["sequential"], batch, seed),
            log)
        row["sequential_batch"] = {"seconds": {str(key): value for key, value in sequential.items()},
                                   "scores": {str(key): value for key, value in _scores(sequential).items()}}
        scores = _scores(sequential)
        winner = _winner(scores, DEFAULT_BATCH_SIZES[backend])
        winners["batch_sizes"][backend] = int(winner)

        pooled = _sweep(
            "pooled batch", backend_pairs,
            candidates["pooled_batch"][backend],
            lambda batch: _pooled_walls(
                backend_pairs, backend, backend_samples["pooled"], batch,
                POOL_WORKERS[backend], seed),
            log)
        row["pooled_batch"] = {"seconds": {str(key): value for key, value in pooled.items()},
                               "scores": {str(key): value for key, value in _scores(pooled).items()}}
        scores = _scores(pooled)
        winner = _winner(scores, POOLED_BATCH_SIZES[backend])
        winners["pooled_batch_sizes"][backend] = int(winner)

        # Worker counts above the batch count split identically (the plan caps
        # segments at batches), so they measure pool size, not parallelism.
        pooled_batch = winners["pooled_batch_sizes"][backend]
        batches = len(batch_plan(backend_samples["pooled"], pooled_batch))
        worker_options = tuple(
            count for count in candidates["workers"][backend] if count <= batches)
        if len(worker_options) < len(candidates["workers"][backend]):
            log(f"  (workers above {batches} batches are indistinguishable at this "
                f"sample size; skipped)")
        if not worker_options:
            worker_options = (max(1, min(candidates["workers"][backend][0], batches)),)
        workers = _sweep(
            "pool workers", backend_pairs, worker_options,
            lambda count: _pooled_walls(
                backend_pairs, backend, backend_samples["pooled"],
                pooled_batch, count, seed),
            log)
        row["pooled_workers"] = {"seconds": {str(key): value for key, value in workers.items()},
                                 "scores": {str(key): value for key, value in _scores(workers).items()}}
        scores = _scores(workers)
        winner = _winner(scores, POOL_WORKERS[backend])
        winners["pool_workers"][backend] = int(winner)

        spawn = measure_spawn(int(winner), repetitions=spawn_repetitions)
        row["spawn"] = {"workers": int(winner), "seconds": spawn}
        winners["spawn_seconds"][backend] = spawn
        log(f"  spawn ({winner} workers): {spawn:.3f}s")

        evidence[backend] = row

    payload = {
        "schema": CALIBRATION_SCHEMA,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor(),
            "cpu_count": os.cpu_count(),
        },
        "method": {
            "pair_sets": sets,
            "pair_ids": {backend: [row[3] for row in pairs[backend]] for backend in order},
            "samples": samples,
            "candidates": {key: {backend: list(value[backend]) for backend in order}
                           for key, value in candidates.items()},
        },
        "batch_sizes": winners["batch_sizes"],
        "pooled_batch_sizes": winners["pooled_batch_sizes"],
        "pool_workers": winners["pool_workers"],
        "spawn_seconds": winners["spawn_seconds"],
        "evidence": evidence,
        "elapsed_seconds": round(time.perf_counter() - _PROGRESS["started"], 2),
    }
    return payload


def _reference_value(section: str, backend: str):
    return {"batch_sizes": DEFAULT_BATCH_SIZES, "pooled_batch_sizes": POOLED_BATCH_SIZES,
            "pool_workers": POOL_WORKERS, "spawn_seconds": POOL_SPAWN_SECONDS}[section][backend]


def print_summary(payload: dict, log=print) -> None:
    """Human-readable comparison of the measured winners against the defaults."""
    log("")
    log(f"measured optima ({payload['elapsed_seconds']:.0f}s total):")
    for section in ("batch_sizes", "pooled_batch_sizes", "pool_workers", "spawn_seconds"):
        values = payload.get(section, {})
        for backend, value in values.items():
            reference = _reference_value(section, backend)
            marker = "=" if value == reference else "->"
            log(f"  {backend:>6} {section:<18} {reference} {marker} {value}")
    curves = measured_pool_speedups(payload)
    if curves:
        log("measured pool speedup curve (segments -> speedup):")
        for backend, points in curves.items():
            rendered = " ".join(
                f"{segments}:{speedup:.2f}x" for segments, speedup in sorted(points.items()))
            log(f"  {backend:>6} {rendered}")


def calibration_command(args) -> int:
    """CLI handler: measure, install the profile and report the effect."""
    from mordheim_combat_lab.persistence.calibration import clear_calibration
    from mordheim_combat_lab.persistence.calibration import load_calibration
    from mordheim_combat_lab.persistence.calibration import save_calibration

    if getattr(args, "reset", False):
        removed = clear_calibration()
        print("calibration profile removed" if removed else "no calibration profile installed")
        return 0
    payload = run_calibration(
        args.pairs, seed=args.seed, sequential_samples=args.sample_size,
        pooled_samples=args.pool_sample_size)
    print_summary(payload)
    path = None
    if getattr(args, "no_install", False):
        print("profile not installed (--no-install)")
    else:
        path = save_calibration(payload)
        if path is None:
            print("could not write the calibration profile; use --output to save it elsewhere",
                  file=sys.stderr)
            if not args.output:
                return 1
        else:
            print(f"profile installed at {path}")
    if args.output:
        report = Path(args.output)
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(f"full report written to {report}")
    applied = apply_calibration(payload)
    print(f"applied sections: {', '.join(sorted(applied)) or 'none'}")
    if path is not None and apply_calibration(load_calibration()) != applied:
        print("warning: the installed profile did not round-trip", file=sys.stderr)
    if args.json:
        print(json.dumps(payload, indent=2))
    if path is not None:
        print("restart the Combat Lab to run with the measured profile")
    return 0

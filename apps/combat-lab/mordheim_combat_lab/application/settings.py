"""application: Execution settings use cases."""
from __future__ import annotations

import math as math
from dataclasses import dataclass, replace
from mordheim_core.models import DuelContext
from mordheim_core.models import DuelRequest
from threading import Event
from typing import Mapping


#: Schema of the machine calibration profile written by
#: ``mordheim-combat-lab calibrate`` (see ``cli/calibration.py``).
CALIBRATION_SCHEMA = "mordheim-combat-lab-calibration/v1"

#: Measured overrides layered on top of the reference-machine constants below.
_CALIBRATION: dict[str, dict] = {}

#: Provenance warnings raised by the last :func:`apply_calibration` call.
_CALIBRATION_WARNINGS: tuple[str, ...] = ()

#: Engines whose sources and build a calibration profile describes.
CALIBRATION_ENGINES = ("numpy", "native")


def measurement_provenance(engines, *, emit: bool = True) -> dict[str, object]:
    """Machine and engine identity a timing measurement depends on.

    The shared :func:`run_provenance` block (revision, imported package
    directories, per-engine source digests, native build hash, warnings)
    plus the machine: CPU count, platform and the Python/NumPy versions.
    ``emit`` prints the block's own warnings (dirty tree, foreign imports).
    """
    import os
    import platform

    import numpy
    from mordheim_combat_lab.provenance import run_provenance
    from mordheim_knowledge.paths import project_root

    block = run_provenance(project_root(), tuple(engines), emit=emit)
    block.update({
        "cpu_count": os.cpu_count(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "numpy": numpy.__version__,
    })
    return block


def provenance_differences(recorded: Mapping[str, object],
                           current: Mapping[str, object]) -> list[str]:
    """Readable differences between a stored and the current provenance.

    Compares the machine (CPU count, platform, Python, NumPy), the source
    digest of every engine both blocks describe, the native build hash and
    the revision (commit and dirty state). A field the stored block lacks is
    reported as unrecorded: an unknown origin is a difference too.
    """
    from mordheim_combat_lab.provenance import describe_difference

    notes: list[str] = []
    for key, label in (("cpu_count", "CPU count"), ("platform", "platform"),
                       ("python", "Python version"), ("numpy", "NumPy version"),
                       ("native_build_sha256", "native build")):
        if key not in recorded:
            notes.append(f"{label} not recorded")
            continue
        note = describe_difference(label, recorded[key], current.get(key))
        if note:
            notes.append(note)
    old_digests = recorded.get("engine_digests")
    new_digests = current.get("engine_digests")
    new_digests = new_digests if isinstance(new_digests, Mapping) else {}
    if not isinstance(old_digests, Mapping):
        notes.append("engine source digests not recorded")
    else:
        for engine in sorted(new_digests):
            if engine not in old_digests:
                notes.append(f"{engine} source digest not recorded")
                continue
            note = describe_difference(f"{engine} engine sources",
                                       old_digests[engine], new_digests[engine])
            if note:
                notes.append(note)
    old_revision = recorded.get("revision")
    new_revision = current.get("revision")
    new_revision = new_revision if isinstance(new_revision, Mapping) else {}
    if not isinstance(old_revision, Mapping):
        notes.append("source revision not recorded")
    else:
        for key, label in (("commit", "commit"), ("dirty", "uncommitted-changes flag")):
            note = describe_difference(label, old_revision.get(key), new_revision.get(key))
            if note:
                notes.append(note)
    return notes


def calibration_provenance_warnings() -> tuple[str, ...]:
    """Provenance warnings recorded when the installed profile was applied."""
    return _CALIBRATION_WARNINGS


def _check_calibration_provenance(payload: Mapping[str, object]) -> tuple[str, ...]:
    """Warn (never refuse) when a profile was measured on another machine/engine."""
    from mordheim_combat_lab.provenance import provenance_warning

    consequence = (
        "It is applied anyway, but its timings may not describe this setup, and "
        "its batch sizes change the per-batch random streams: NumPy/native sampled "
        "results differ from runs under the reference defaults or another profile. "
        "Re-run `mordheim-combat-lab calibrate` to measure this machine and engine."
    )
    recorded = payload.get("provenance")
    if not isinstance(recorded, Mapping):
        return (provenance_warning(
            "the calibration profile records no provenance (written before machine "
            "and engine identity were stored), so the machine and engine build it "
            f"was measured on are unknown. {consequence}"),)
    try:
        current = measurement_provenance(CALIBRATION_ENGINES, emit=False)
    except Exception as error:  # startup must never break on a provenance probe
        return (provenance_warning(
            f"could not determine this machine's provenance ({error}) to check the "
            f"calibration profile against it. {consequence}"),)
    differences = provenance_differences(recorded, current)
    if not differences:
        return ()
    return (provenance_warning(
        "the calibration profile was measured on another machine or engine build: "
        + "; ".join(differences) + f". {consequence}"),)


def _strict_int(value):
    """Integer coercion that rejects fractional values instead of truncating."""
    if isinstance(value, float) and value != int(value):
        raise ValueError("non-integral value")
    return int(value)


def _bounded(value, minimum, maximum, cast):
    """Coerce one calibration value into range, or ``None`` to ignore it."""
    try:
        parsed = cast(value)
    except (TypeError, ValueError):
        return None
    return parsed if minimum <= parsed <= maximum else None


def _calibrated_value(section: str, backend: str, fallback):
    return _CALIBRATION.get(section, {}).get(backend, fallback)


def apply_calibration(payload: Mapping[str, object] | None) -> dict:
    """Layer a measured machine profile over the reference constants.

    ``payload`` is the JSON document written by the ``calibrate`` command
    (schema :data:`CALIBRATION_SCHEMA`). Recognised sections: ``batch_sizes``,
    ``pool_workers`` and ``spawn_seconds`` — each maps
    backend names (``auto``/``native``/``numpy``) to values clamped to a sane
    range. The pool speedup curve is not a stored section: it is re-derived
    per backend from the profile's raw ``evidence``
    (:func:`measured_pool_speedups`), so the decision runs on this machine's
    measured parallel efficiency instead of the shared conservative fit.
    Unknown keys, foreign schemas and out-of-range values are ignored: an
    edited or truncated file must never break startup; the ``pooled_batch_sizes``
    section of older profiles is ignored too (comparisons never switch batch
    when they pool). Passing ``None`` or an
    empty payload restores the reference defaults; both return the applied
    sections so callers can report what took effect.

    Provenance is checked, never enforced: when the profile's recorded
    ``provenance`` (CPU count, platform, Python/NumPy, engine source digests,
    native build, revision) differs from this process — or is missing — a
    ``PROVENANCE WARNING`` is printed and kept in
    :func:`calibration_provenance_warnings`, and the profile is still applied.
    """
    global _CALIBRATION, _CALIBRATION_WARNINGS
    _CALIBRATION = {}
    _CALIBRATION_WARNINGS = ()
    if not isinstance(payload, Mapping) or payload.get("schema") != CALIBRATION_SCHEMA:
        return {}
    applied: dict[str, dict] = {}
    for section, defaults, cast, low, high in (
        ("batch_sizes", DEFAULT_BATCH_SIZES, _strict_int, 500, 2_000_000),
        ("pool_workers", POOL_WORKERS, _strict_int, 2, 64),
        ("spawn_seconds", POOL_SPAWN_SECONDS, float, 0.01, 10.0),
    ):
        raw = payload.get(section)
        if not isinstance(raw, Mapping):
            continue
        clean = {}
        for backend in defaults:
            if backend in raw:
                value = _bounded(raw[backend], low, high, cast)
                if value is not None:
                    clean[backend] = value
        if clean:
            _CALIBRATION[section] = clean
            applied[section] = clean
    curves = measured_pool_speedups(payload)
    if curves:
        _CALIBRATION["pool_speedups"] = curves
        applied["pool_speedups"] = curves
    if applied:
        _CALIBRATION_WARNINGS = _check_calibration_provenance(payload)
    return applied


# Measured per-engine defaults (TTS studies on the reference machine, see
# docs/guides/develop-and-release.md): native wins with small batches (its
# scalar loop keeps the working set in cache), numpy with large ones (per-op
# overhead collapses below ~10k rows). ``auto`` resolves to the driver's
# preferred backend (native when the extension is compatible).
DEFAULT_BATCH_SIZES = {"auto": 5_000, "native": 5_000, "numpy": 100_000}


def default_batch_size(backend: str) -> int:
    """Return the measured default batch for one backend selection.

    The machine calibration supersedes the reference-machine value when one
    is installed (see :func:`apply_calibration`).
    """
    try:
        fallback = DEFAULT_BATCH_SIZES[backend]
    except KeyError:
        raise ValueError(f"unknown backend: {backend}") from None
    return int(_calibrated_value("batch_sizes", backend, fallback))


LEGACY_GLOBAL_BATCH_SIZE = 100_000


def resolve_battery_settings(settings: "DuelExecutionSettings", backend: str) -> "DuelExecutionSettings":
    """Resolve the app-wide batch default to the per-backend optimum.

    A batch left at the global default (100k) means "no explicit choice": it
    becomes the measured optimum for the selected engine. An explicit value
    is honoured unchanged.
    """
    if settings.batch_size != LEGACY_GLOBAL_BATCH_SIZE:
        return settings
    return replace(settings, batch_size=default_batch_size(backend))


def resolve_fighter_settings(settings: "DuelExecutionSettings", first, second) -> tuple["DuelExecutionSettings", str]:
    """Resolve the real engine for a pair and the global batch default.

    The backend is always resolved ("native" when the plan is eligible for
    the native kernel, "numpy" otherwise) so telemetry records the engine
    that actually executes the duels. Plans that fall back to NumPy must not
    inherit the native batch optimum: small batches collapse the vectorized
    driver — so a legacy global default batch (100k) is rewritten to the
    resolved engine's optimum, while explicit batch values stand.
    """
    backend = "native" if _native_segment_eligible(first, second) else "numpy"
    if settings.batch_size != LEGACY_GLOBAL_BATCH_SIZE:
        return settings, backend
    return replace(settings, batch_size=default_batch_size(backend)), backend


@dataclass(frozen=True, slots=True)
class DuelExecutionSettings:
    """UI-owned values mapped directly to the runtime request contract."""

    simulations: int
    seed: int
    batch_size: int
    maximum_rounds: int

    def __post_init__(self) -> None:
        if min(self.simulations, self.batch_size, self.maximum_rounds) < 1:
            raise ValueError("Simulation count, batch size, and maximum rounds must be positive.")

    def request(self, first, second, cancel_event: Event | None = None, *,
                context: DuelContext | None = None) -> DuelRequest:
        return DuelRequest(first, second, self.simulations, self.seed, self.batch_size, self.maximum_rounds, cancel_event, context=context)

    def large_battery_processes(self, backend: str = "auto") -> int | None:
        """Process-pool workers for large batteries (``None`` = sequential).

        Sample-size-only fallback for direct :func:`simulate_battery` calls:
        measured optima are native 14 workers, numpy 8 (memory-bandwidth
        bound). Comparisons use :func:`battery_pool_plan` instead, which
        measures the run's real per-duel cost before deciding.
        """
        if self.simulations < LARGE_BATTERY_UNIT_SIMULATIONS:
            return None
        return pool_workers(backend)


LARGE_BATTERY_UNIT_SIMULATIONS = 1_000_000

# Pool economics measured on the reference machine (crossover table in
# docs/guides/develop-and-release.md). Spawning a pool costs
# ~0.24s (native) / ~0.20s (numpy) per run, and the realised speedup lags the
# segment count badly: 2 segments -> 1.5-1.8x, 5 -> 3.4-4.7x, 12 -> 5.8-8.0x
# native, while numpy plateaus near 4x on memory bandwidth. The helpers below
# stay on the conservative side of those measurements: they decide, they never
# promise.
# Overhead and margin are deliberately small: the retune came from a 30-pair
# study (see the doc) where a 10ms per-battery overhead erased the whole
# per-fighter saving of light duels and pushed the crossover to 2-4x the ideal
# width (p90 regret 1.44x, now 1.09x). The shared ``pool_speedup`` curve is
# already fitted below the reference measurements, so a second helping of
# conservatism only bought misses. That curve is superseded per machine when a
# calibration profile is installed: ``measured_pool_speedups`` derives the
# speedup curve from the profile's raw worker sweep.
# Native workers: a sweep at app pool shapes (200k duels, batch 5k, two duel
# types) peaks at 14 — 12 -> 14 buys 9-15%, 16 is level, 18-20 regress. Run
# noise on cheap pairs is 3-30%, so the 12-16 plateau is flat within noise and
# 14 is the measured middle. Numpy: 8 confirmed twice (10 regresses 6-14%).
POOL_WORKERS = {"auto": 14, "native": 14, "numpy": 8}
POOL_SPAWN_SECONDS = {"auto": 0.24, "native": 0.24, "numpy": 0.20}
POOL_PER_BATTERY_OVERHEAD_SECONDS = 0.002  # submits, pickling and drains
POOL_SAFETY_FACTOR = 1.25  # spawn must be beaten by this margin

#: Backends with a pooled battery path (and so a measured speedup curve).
POOL_BACKENDS = ("native", "numpy")

#: Pooled batches older calibration profiles swept their workers at when the
#: profile carries no ``pooled_batch_sizes`` entry. Read only to interpret old
#: evidence: comparisons pool at the fighters' own batch (the batch selects
#: the per-batch random streams, so the baseline and every candidate share it
#: whatever the pool decision), and a curve measured at another batch does not
#: describe the configuration that runs.
_LEGACY_POOLED_BATCH_SIZES = {"native": 5_000, "numpy": 25_000}


def pool_workers(backend: str) -> int:
    """Workers for pooled batteries (calibrated when a profile is installed)."""
    key = backend if backend in POOL_WORKERS else "auto"
    fallback = POOL_WORKERS[key]
    if key == "auto":  # ``auto`` follows the native measurement it resolves to
        fallback = _calibrated_value("pool_workers", "native", fallback)
    return int(_calibrated_value("pool_workers", key, fallback))


def pool_spawn_seconds(backend: str) -> float:
    """Spawn cost of one process pool (calibrated when installed)."""
    key = backend if backend in POOL_SPAWN_SECONDS else "auto"
    fallback = POOL_SPAWN_SECONDS[key]
    if key == "auto":
        fallback = _calibrated_value("spawn_seconds", "native", fallback)
    return float(_calibrated_value("spawn_seconds", key, fallback))


def _geometric_mean(values) -> float:
    return math.exp(sum(math.log(value) for value in values) / len(values))


def measured_pool_speedups(payload: Mapping[str, object]) -> dict[str, dict[int, float]]:
    """Per-machine pool speedup curves derived from a profile's raw evidence.

    The calibration's worker sweep measures the *same* pairs sequentially and
    pooled for every worker candidate, both at the calibrated sequential batch
    — the batch comparisons run, pooled or not — so each pair yields a
    per-duel ratio of sequential cost to pooled cost and each worker count
    yields one curve point: the geometric mean of those ratios, keyed by the
    pool's segment count. Points are clamped to ``[1, segments]`` — a pool
    cannot outrun its own segment count, and a measured loss is recorded as
    "no gain" (the policy then stays sequential).

    The sweep batch is ``method.worker_sweep_batch``; older profiles swept at
    their pooled batch (``pooled_batch_sizes``). A backend whose sweep batch
    differs from its sequential batch yields no curve — that measurement
    describes a configuration comparisons no longer run — and the shared
    conservative curve applies instead.

    Returns ``{backend: {segments: speedup}}``, empty when the payload carries
    no usable evidence (foreign schema, missing sweeps, degenerate walls).
    """
    if not isinstance(payload, Mapping) or payload.get("schema") != CALIBRATION_SCHEMA:
        return {}
    evidence = payload.get("evidence")
    method = payload.get("method")
    if not isinstance(evidence, Mapping) or not isinstance(method, Mapping):
        return {}
    samples = method.get("samples")
    samples = samples if isinstance(samples, Mapping) else {}
    sequential_batches = payload.get("batch_sizes")
    sequential_batches = sequential_batches if isinstance(sequential_batches, Mapping) else {}
    sweep_batches = method.get("worker_sweep_batch")
    legacy_batches = payload.get("pooled_batch_sizes")
    if not isinstance(sweep_batches, Mapping):
        sweep_batches = None
        legacy_batches = legacy_batches if isinstance(legacy_batches, Mapping) else {}

    curves: dict[str, dict[int, float]] = {}
    for backend, row in evidence.items():
        if backend not in POOL_BACKENDS or not isinstance(row, Mapping):
            continue
        backend_samples = samples.get(backend)
        backend_samples = backend_samples if isinstance(backend_samples, Mapping) else {}
        sequential_samples = _bounded(backend_samples.get("sequential"), 1, 1 << 40, _strict_int)
        pooled_samples = _bounded(backend_samples.get("pooled"), 1, 1 << 40, _strict_int)
        sequential_batch = _bounded(sequential_batches.get(backend), 1, 2_000_000, _strict_int)
        if sequential_batch is None:
            sequential_batch = DEFAULT_BATCH_SIZES[backend]
        if sweep_batches is not None:
            sweep_batch = _bounded(sweep_batches.get(backend), 1, 2_000_000, _strict_int)
        else:
            sweep_batch = _bounded(legacy_batches.get(backend), 1, 2_000_000, _strict_int)
            if sweep_batch is None:
                sweep_batch = _LEGACY_POOLED_BATCH_SIZES[backend]
        if sweep_batch != sequential_batch:
            continue
        sequential_table = row.get("sequential_batch")
        pooled_table = row.get("pooled_workers")
        if sequential_samples is None or pooled_samples is None:
            continue
        if not isinstance(sequential_table, Mapping) or not isinstance(pooled_table, Mapping):
            continue
        sequential_seconds = sequential_table.get("seconds")
        pooled_seconds = pooled_table.get("seconds")
        if not isinstance(sequential_seconds, Mapping) or not isinstance(pooled_seconds, Mapping):
            continue
        sequential_walls = sequential_seconds.get(str(sequential_batch))
        if not isinstance(sequential_walls, (list, tuple)):
            continue

        points: dict[int, float] = {}
        for key, pooled_walls in pooled_seconds.items():
            workers = _bounded(key, 2, 256, _strict_int)
            if workers is None or not isinstance(pooled_walls, (list, tuple)):
                continue
            if len(pooled_walls) != len(sequential_walls):
                continue
            segments = len(split_battery(pooled_samples, sweep_batch, workers))
            if segments < 2:
                continue
            ratios = []
            for sequential_wall, pooled_wall in zip(sequential_walls, pooled_walls):
                try:
                    sequential_wall = float(sequential_wall)
                    pooled_wall = float(pooled_wall)
                except (TypeError, ValueError):
                    continue
                if (sequential_wall <= 0 or pooled_wall <= 0
                        or not math.isfinite(sequential_wall) or not math.isfinite(pooled_wall)):
                    continue
                ratios.append((sequential_wall / sequential_samples) / (pooled_wall / pooled_samples))
            if not ratios:
                continue
            speedup = _geometric_mean(ratios)
            points[segments] = round(min(max(speedup, 1.0), float(segments)), 4)
        if points:
            curves[str(backend)] = points
    return curves


def _curve_points(raw) -> dict[int, float]:
    """Normalise one stored curve (JSON keys are strings) into integer keys."""
    if not isinstance(raw, Mapping):
        return {}
    points: dict[int, float] = {}
    for key, value in raw.items():
        try:
            segments = int(key)
            speedup = float(value)
        except (TypeError, ValueError):
            continue
        if segments >= 2 and speedup > 0 and math.isfinite(speedup):
            points[segments] = speedup
    return points


def calibrated_pool_speedups(backend: str) -> dict[int, float]:
    """Measured speedup curve installed for a backend (empty when uncalibrated).

    ``auto`` resolves like the other pool helpers: the native measurement is
    the app's actual default, with numpy as the fallback when only the numpy
    engine was calibrated.
    """
    section = _CALIBRATION.get("pool_speedups")
    if not isinstance(section, Mapping):
        return {}
    if backend in POOL_BACKENDS:
        keys = (backend,)
    elif backend == "auto":
        keys = ("native", "numpy")
    else:
        return {}
    for key in keys:
        points = _curve_points(section.get(key))
        if points:
            return points
    return {}


def _speedup_from_points(points: Mapping[int, float], segments: int) -> float:
    """Piecewise model of a measured curve at one segment count.

    Anchors are the measured worker counts. Below the lowest measured count no
    evidence exists, so its efficiency (speedup per segment) is held — the
    conservative reading of less contention. Above the highest measured count
    the largest measurement is held: with the installed constants the plan
    cannot reach those segment counts anyway. The result never exceeds the
    segment count (a pool cannot beat its own parallelism).
    """
    ordered = sorted(points.items())
    low_segments, low_speedup = ordered[0]
    if segments < low_segments:
        value = segments * (low_speedup / low_segments)
    elif segments >= ordered[-1][0]:
        value = ordered[-1][1]
    else:
        value = ordered[-1][1]
        for (first_segments, first_speedup), (next_segments, next_speedup) in zip(ordered, ordered[1:]):
            if first_segments <= segments <= next_segments:
                share = (segments - first_segments) / (next_segments - first_segments)
                value = first_speedup + share * (next_speedup - first_speedup)
                break
    return float(min(max(value, 1.0), float(segments)))


def pool_speedup(segments: int, backend: str | None = None) -> float:
    """Realised speedup of a pooled battery of ``segments``.

    With a machine profile installed the backend's **measured curve** is used
    (:func:`measured_pool_speedups`): the calibration's worker sweep anchors
    every measured worker count, values interpolate linearly between anchors,
    the lowest anchor's efficiency is held below the measured range and the
    largest measurement above it — always clamped to the segment count.

    Without a profile the shared conservative curve applies, fitted under the
    reference measurements: efficiency decays as workers contend for cores and
    memory (``0.85`` per segment down to a ``0.4`` floor). Across the 30 fast
    pairs it stayed under every measured point (2 segments measured 1.4-1.8x,
    5 segments 4.7x, 12 segments 6.1-6.9x native).
    """
    if segments < 2:
        return 1.0
    points = calibrated_pool_speedups(backend) if backend is not None else {}
    if points:
        return _speedup_from_points(points, segments)
    return segments * max(0.40, 0.85 - 0.05 * segments)


def battery_pool_plan(baseline_seconds: float, settings: "DuelExecutionSettings",
                      backend: str, fighters: int) -> int | None:
    """Workers for the remaining fighters, or ``None`` to run sequentially.

    ``baseline_seconds`` is the wall time of the baseline battery, which runs
    sequentially precisely to measure the real per-duel cost of *this* pair —
    a heavy grind costs several times a simple duel, so a fixed sample-size
    threshold cannot serve every comparison. The pool engages only when the
    estimated saving across the remaining fighters comfortably beats its
    spawn cost (measured constants; this machine's measured speedup curve when
    a calibration profile is installed, the shared conservative one otherwise).

    Segments are counted with ``settings.batch_size`` — the batch the pooled
    fighters really run, since comparisons keep the baseline's batch — and the
    calibrated speedup curve was measured at that same (calibrated sequential)
    batch, so the estimate describes the configuration that runs. The
    spawn cost is charged here exactly once: the calibration warms its pools
    before timing, so the measured speedup curve excludes worker spawn and
    engine imports, and ``pool_spawn_seconds`` carries them alone.
    """
    if fighters < 1 or settings.simulations < 2:
        return None
    workers = pool_workers(backend)
    segments = len(split_battery(settings.simulations, settings.batch_size, workers))
    if segments < 2:
        return None
    saving = (baseline_seconds * (1.0 - 1.0 / pool_speedup(segments, backend))
              - POOL_PER_BATTERY_OVERHEAD_SECONDS)
    spawn = pool_spawn_seconds(backend)
    if saving <= 0 or fighters * saving <= POOL_SAFETY_FACTOR * spawn:
        return None
    return workers


def _native_segment_eligible(first, second, context=None) -> bool:
    """Mirror ``simulate_duel(auto)``'s native selection for one plan."""
    from mordheim_combat.vectorized import available_backends

    if available_backends()[0] != "native":
        return False
    try:
        from mordheim_combat import _combat_native
        from mordheim_combat.kernel import compile_duel_plan
    except ImportError:
        return False
    plan = compile_duel_plan(first, second, context=context, backend="native")
    if context is not None and getattr(_combat_native, "CONTEXT_VERSION", None) != 1:
        return False
    if not plan.optimization_eligible:
        return False
    return bool(getattr(_combat_native, "supports_plan", lambda _plan: False)(plan))

def split_battery(simulations: int, batch_size: int, workers: int) -> tuple[tuple[int, int], ...]:
    """Split the batch plan into ``<= workers`` (first_batch, stop) segments."""
    if workers < 1:
        raise ValueError("workers must be positive")
    full, remainder = divmod(simulations, batch_size)
    batches = full + (1 if remainder else 0)
    workers = min(workers, batches)
    base, extra = divmod(batches, workers)
    segments = []
    first = 0
    for index in range(workers):
        count = base + (1 if index < extra else 0)
        segments.append((first, first + count))
        first += count
    return tuple(segments)


def _battery_worker_numpy(first, second, first_batch: int, stop: int,
                          simulations: int, batch_size: int, seed: int, maximum_rounds: int, context=None):
    """Simulate plan batches ``[first_batch, stop)`` on the NumPy driver."""
    from mordheim_combat.vectorized import batch_segment

    return batch_segment(
        first, second, first_batch, stop, simulations, batch_size,
        seed, maximum_rounds, None, context,
    )


def _battery_worker_native(first, second, simulations: int, batch_size: int,
                           seed: int, maximum_rounds: int, context=None):
    """Simulate one segment as a whole sample with a shifted seed.

    The native engine derives batch ``i``'s stream as ``seed + i*salt`` in
    64-bit arithmetic, so a sample seeded ``seed + k*salt`` replays the
    whole run's batches ``k..`` bit for bit. Runs without the parent's
    cancel event: it cannot cross the process boundary (same trade-off as
    the CLI and driver pools).
    """
    from mordheim_combat.vectorized import simulate_duel

    request = DuelRequest(first, second, simulations, seed=seed,
                          batch_size=batch_size, maximum_rounds=maximum_rounds, context=context)
    result = simulate_duel(request, backend="native")
    return result.first_wins, result.second_wins, result.unresolved




def simulate_battery(first, second, settings: DuelExecutionSettings,
                     cancel_event: Event | None = None, workers: int | None = None,
                     pool=None, backend: str | None = None, *, context: DuelContext | None = None):
    """Run one duel sample, optionally through a per-batch process pool.

    ``workers`` overrides the battery policy (``0`` forces the in-process
    path, ``None`` applies the measured thresholds). Sequential samples take
    the plain in-process path. Pooled samples split the batch plan by worker
    and keep every stream identical to the sequential run: NumPy segments
    replay explicit plan indices, native segments shift the seed by
    ``first_batch * salt`` (the engine's own per-batch derivation) — pooled
    totals are bit-for-bit the sequential ones for both backends.

    ``pool`` accepts a caller-owned executor to reuse across many batteries
    (process spawn costs ~0.4s per pool on the reference machine, so runs
    with dozens of fighters must amortize a single pool).

    ``backend`` forces one engine (``"numpy"`` measures the fallback path of
    a native-eligible plan — the calibration sweeps use it); ``None`` mirrors
    the app and picks native when the plan is eligible. Forcing ``"native"``
    on an ineligible plan raises instead of simulating wrongly.
    """
    if workers is None:
        workers = settings.large_battery_processes(backend or "auto")
    if not workers or settings.simulations < 2:
        from mordheim_combat.vectorized import simulate_duel
        return simulate_duel(settings.request(first, second, cancel_event, context=context),
                             backend=backend or "auto")
    from concurrent.futures import ProcessPoolExecutor
    from mordheim_combat.vectorized import batch_plan
    from mordheim_core.models import DuelResult

    sizes = batch_plan(settings.simulations, settings.batch_size)
    segments = split_battery(settings.simulations, settings.batch_size, workers)
    native = _native_segment_eligible(first, second, context)
    if backend in ("native", "numpy"):
        if backend == "native" and not native:
            raise ValueError("the native backend does not support this plan")
        native = backend == "native"
    salt = 0x9E3779B97F4A7C15  # both drivers' per-batch stream constant

    def _submit(executor):
        if native:
            return [
                executor.submit(
                    _battery_worker_native, first, second,
                    sum(sizes[first_batch:stop]), settings.batch_size,
                    (settings.seed + first_batch * salt) % (1 << 64),
                    settings.maximum_rounds, context,
                )
                for first_batch, stop in segments
            ]
        return [
            executor.submit(
                _battery_worker_numpy, first, second, first_batch, stop,
                settings.simulations, settings.batch_size, settings.seed,
                settings.maximum_rounds, context,
            )
            for first_batch, stop in segments
        ]

    def _drain(futures):
        totals = [0, 0, 0]
        for future in futures:
            wins, losses, unresolved = future.result()
            totals[0] += wins
            totals[1] += losses
            totals[2] += unresolved
        return totals

    if pool is None:
        with ProcessPoolExecutor(max_workers=len(segments)) as owned:
            totals = _drain(_submit(owned))
    else:
        totals = _drain(_submit(pool))
    return DuelResult(totals[0], totals[1], totals[2], settings.simulations)

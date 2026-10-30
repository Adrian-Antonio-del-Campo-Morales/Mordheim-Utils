"""Independent command: sample each engine separately and compare the stored samples.

The campaign (:mod:`tools.verification.parity_campaign`) samples the modular
oracle and the native candidate in one process and compares them immediately.
While the native engine is being debugged that couples the expensive oracle
sample to every native rebuild.  This command splits the campaign into three
steps that persist on disk:

``sample --engine modular``
    Run the oracle for the selected scenarios and store its outcome counts.
``sample --engine native``
    Run the compiled engine for the selected scenarios and store its counts.
``sample --engine numpy``
    Run the vectorized engine and store canonical NumPy batches.
``compare --backend numpy`` (or ``native``, the default)
    Decide the stored pairs with the unchanged six-sigma gate and write the
    usual campaign report (``parity-campaign.json`` / ``.md``).

Every sample is written in **chunks**: one record per scenario and engine,
re-written atomically after each chunk, so an interrupted run keeps every
chunk that finished and the next run only executes the missing ones.  Chunks
reproduce the engines' own sampling exactly:

- the modular chunk starting at duel ``start`` is
  ``simulate_duel_reference(..., seed=seed + start)``, which is how the
  sequential oracle and the process pool already split a sample, so the stored
  total equals the sequential oracle duel for duel;
- the native chunk with index ``k`` is one batch seeded
  ``seed + 1_000_003 + k * 0x9E3779B97F4A7C15``, the extension's own per-batch
  stream, so the stored total equals ``native.simulate_duel(DuelRequest(N,
  seed + 1_000_003, batch_size=chunk))``;
- NumPy chunks use the canonical ``batch_segment`` stream for their batch
  index, matching a NumPy request with ``batch_size=chunk``.

A record names the fighters it sampled (the corpus ``inputs_sha256`` of the
case) and the engine it ran as a source digest.  The modular digest covers
only the modular engine and the shared core, so a change confined to the
native sources never invalidates an oracle sample; the native digest covers
the native sources, the kernel boundary and the built extension.  A stored
record whose identity no longer matches is refused rather than silently
extended; ``--replace`` discards it.

Usage (from the repository root)::

    python -m tools.verification.parity_samples sample --engine modular \
        --level long --simulations 10000 --workers 4 --store reports/parity-store
    python -m tools.verification.parity_samples sample --engine native \
        --level long --simulations 10000 --store reports/parity-store
    python -m tools.verification.parity_samples compare \
        --level long --store reports/parity-store --output reports/parity-store/compare
    python -m tools.verification.parity_samples status --level long --store reports/parity-store

Exit codes: ``sample`` returns 0 when every selected scenario reached the
requested width, 1 when something is still missing (including after an
interruption), 2 for a configuration or corpus error; ``compare`` returns the
campaign's codes (0 complete, 1 incomplete, 2 configuration error).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import sys
import time
import signal
import threading
from concurrent.futures import FIRST_COMPLETED
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import wait
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from mordheim_core.models import DuelRequest

from tools.verification.compiled_cases import CompiledCaseError
from tools.verification.compiled_cases import load_cases
from tools.verification.parity_campaign import campaign_markdown
from tools.verification.parity_campaign import campaign_payload
from tools.verification.parity_catalog import CORPUS
from tools.verification.parity_catalog import LEVELS
from tools.verification.parity_catalog import CampaignScenario
from tools.verification.parity_catalog import load
from tools.verification.parity_catalog import select
from mordheim_combat_lab.verification.parity import ParityRow
from mordheim_combat_lab.verification.parity import parity_row
from mordheim_combat_lab.verification.parity import compare_samples

SCHEMA = "mordheim-combat-parity-sample/v1"
ENGINES = ("modular", "native", "numpy")

#: The candidate seed offset of ``compare_statistical_parity``.
NATIVE_SEED_OFFSET = 1_000_003
#: The extension's per-batch seed stride (``_combat_native.simulate_duel``).
NATIVE_BATCH_STRIDE = 0x9E3779B97F4A7C15
_UINT64 = 0xFFFFFFFFFFFFFFFF

#: Default duels per chunk; a chunk is the unit of persistence and of pooling.
DEFAULT_CHUNK = 250

_ROOT = Path(__file__).resolve().parents[2]
_COMBAT = _ROOT / "packages" / "python" / "combat-engine" / "mordheim_combat"
_CORE = _ROOT / "packages" / "python" / "core" / "mordheim_core"


class SampleStoreError(ValueError):
    """A stored sample cannot be used as requested."""


# ---------------------------------------------------------------------------
# Engine digests
# ---------------------------------------------------------------------------

def _digest_files(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(set(paths)):
        # The built native extension is resolved through its import location,
        # which need not sit under ``_ROOT`` (an out-of-tree build, or a test
        # that repoints ``_ROOT``). Fall back to the bare file name so the
        # digest stays machine-independent; the contents are hashed below
        # either way.
        try:
            label = path.relative_to(_ROOT).as_posix()
        except ValueError:
            label = path.name
        digest.update(label.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes() if path.exists() else b"<missing>")
        digest.update(b"\0")
    return digest.hexdigest()


def _modular_sources() -> tuple[Path, ...]:
    return (
        *sorted((_COMBAT / "modular").glob("*.py")),
        _COMBAT / "phases.py",
        *sorted(_CORE.glob("*.py")),
    )


def _native_sources() -> tuple[Path, ...]:
    built: list[Path] = []
    try:
        from mordheim_combat import _combat_native
    except ImportError:
        pass
    else:
        built.append(Path(_combat_native.__file__))
    return (
        *sorted((_COMBAT / "native").glob("*.py")),
        *sorted((_COMBAT / "native").glob("*.pyx")),
        *sorted((_COMBAT / "native").glob("*.pxd")),
        _COMBAT / "kernel.py",
        _COMBAT / "phases.py",
        *sorted(_CORE.glob("*.py")),
        *built,
    )


def engine_digest(engine: str) -> str:
    """Source digest of one engine: what a stored sample was produced by.

    ``modular`` hashes the modular package, the shared phase library and the
    core models; ``native`` hashes the native package (Python, Cython and the
    built extension), the kernel boundary, the phase library and the core.
    NumPy hashes its vectorized package, kernel, shared phases and core.
    The native digest deliberately excludes ``modular/*.py`` so that a native
    rebuild is the only thing that moves it; the modular digest excludes the
    native package and the kernel so a native change never moves it.
    """
    if engine == "modular":
        return _digest_files(_modular_sources())
    if engine == "numpy":
        return _digest_files((*sorted((_COMBAT / "vectorized").glob("*.py")),
                              _COMBAT / "kernel.py", _COMBAT / "phases.py",
                              *sorted(_CORE.glob("*.py"))))
    if engine == "native":
        return _digest_files(_native_sources())
    raise ValueError(f"unknown engine {engine!r}; choose one of {', '.join(ENGINES)}")


def _environment() -> dict[str, object]:
    import numpy

    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "cpu_count": os.cpu_count(),
    }


# ---------------------------------------------------------------------------
# Records
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SampleChunk:
    """Outcome counts of the duels ``[start, start + count)`` of one sample."""

    start: int
    count: int
    first: int
    second: int
    unresolved: int
    seconds: float
    completed_at: str

    def __post_init__(self) -> None:
        if self.start < 0 or self.count < 1:
            raise ValueError("a chunk covers a positive range")
        if self.first + self.second + self.unresolved != self.count:
            raise ValueError("chunk counts must add up to its width")


@dataclass(frozen=True, slots=True)
class SampleRecord:
    """One engine's stored sample of one scenario, chunk by chunk."""

    engine: str
    corpus_key: str
    scenario: str
    seed: int
    maximum_rounds: int
    chunk_size: int
    inputs_sha256: str
    engine_digest: str
    environment: Mapping[str, object]
    chunks: tuple[SampleChunk, ...] = ()
    created_at: str = ""

    @property
    def engine_seed(self) -> int:
        """The seed the engine receives (candidate engines add the offset)."""
        return self.seed + (NATIVE_SEED_OFFSET if self.engine in ("native", "numpy") else 0)

    def coverage(self) -> int:
        """Duels covered from index 0 without a gap (a usable sample width)."""
        covered = 0
        for chunk in sorted(self.chunks, key=lambda item: item.start):
            if chunk.start != covered:
                break
            covered += chunk.count
        return covered

    def prefix(self, simulations: int) -> tuple[SampleChunk, ...]:
        """The chunks that tile exactly ``[0, simulations)``."""
        if simulations < 1:
            raise SampleStoreError("a sample needs at least one duel")
        chosen: list[SampleChunk] = []
        covered = 0
        for chunk in sorted(self.chunks, key=lambda item: item.start):
            if covered >= simulations:
                break
            if chunk.start != covered:
                break
            chosen.append(chunk)
            covered += chunk.count
        if covered < simulations:
            raise SampleStoreError(
                f"{self.engine} sample of {self.corpus_key} covers "
                f"{covered} duel(s), fewer than the {simulations} requested"
            )
        if covered > simulations:
            boundaries = sorted({c.start + c.count for c in chosen})
            raise SampleStoreError(
                f"{self.engine} sample of {self.corpus_key} cannot be cut at "
                f"{simulations}: chunk boundaries are {boundaries}"
            )
        return tuple(chosen)

    def counts(self, simulations: int) -> tuple[int, int, int]:
        chunks = self.prefix(simulations)
        return (
            sum(c.first for c in chunks),
            sum(c.second for c in chunks),
            sum(c.unresolved for c in chunks),
        )

    def seconds(self, simulations: int) -> float:
        """Summed engine time of the prefix (sequential-equivalent, not wall)."""
        return sum(c.seconds for c in self.prefix(simulations))

    def to_json(self) -> dict[str, object]:
        body = asdict(self)
        body["chunks"] = [asdict(chunk) for chunk in sorted(
            self.chunks, key=lambda item: item.start,
        )]
        return {"schema": SCHEMA, **body}

    @classmethod
    def from_json(cls, raw: Mapping[str, object], where: str = "<record>") -> "SampleRecord":
        if raw.get("schema") != SCHEMA:
            raise SampleStoreError(f"{where}: not a {SCHEMA} document")
        try:
            chunks = tuple(SampleChunk(**chunk) for chunk in raw["chunks"])
            return cls(
                engine=str(raw["engine"]), corpus_key=str(raw["corpus_key"]),
                scenario=str(raw["scenario"]), seed=int(raw["seed"]),
                maximum_rounds=int(raw["maximum_rounds"]),
                chunk_size=int(raw["chunk_size"]),
                inputs_sha256=str(raw["inputs_sha256"]),
                engine_digest=str(raw["engine_digest"]),
                environment=dict(raw.get("environment", {})),
                chunks=chunks, created_at=str(raw.get("created_at", "")),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise SampleStoreError(f"{where}: malformed sample record: {error}") from error


def sample_path(store: Path, engine: str, corpus_key: str) -> Path:
    """``<store>/<engine>/<scenario>.json`` for a uniform corpus key."""
    if engine not in ENGINES:
        raise ValueError(f"unknown engine {engine!r}")
    name = ("e2e__" + hashlib.sha256(corpus_key.encode()).hexdigest()
            if corpus_key.startswith("e2e/") else corpus_key.replace("/", "__"))
    return Path(store) / engine / f"{name}.json"


def load_sample(path: Path) -> SampleRecord | None:
    """Return the record at ``path`` or ``None`` when there is none yet."""
    path = Path(path)
    if not path.exists():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise SampleStoreError(f"{path}: unreadable sample: {error}") from error
    return SampleRecord.from_json(raw, str(path))


def save_sample(path: Path, record: SampleRecord) -> None:
    """Write the record atomically (temporary file then rename)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(record.to_json(), ensure_ascii=True, indent=1) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


# ---------------------------------------------------------------------------
# Chunk planning
# ---------------------------------------------------------------------------

def required_chunks(simulations: int, chunk_size: int) -> tuple[tuple[int, int], ...]:
    """``(start, count)`` of every chunk a sample of ``simulations`` needs."""
    if simulations < 1 or chunk_size < 1:
        raise ValueError("simulations and chunk size must be positive")
    return tuple(
        (index * chunk_size, min(chunk_size, simulations - index * chunk_size))
        for index in range(math.ceil(simulations / chunk_size))
    )


def missing_chunks(record: SampleRecord, simulations: int) -> tuple[tuple[int, int], ...]:
    """The required chunks the record does not hold with identical bounds.

    A stored chunk with the same start but another width (the tail of a
    narrower earlier request) is re-run whole and replaced, so the stored
    sample is always the tiling the engine itself would have produced.
    """
    stored = {(chunk.start, chunk.count) for chunk in record.chunks}
    return tuple(
        item for item in required_chunks(simulations, record.chunk_size)
        if item not in stored
    )


def _with_chunk(record: SampleRecord, chunk: SampleChunk) -> SampleRecord:
    kept = tuple(item for item in record.chunks if item.start != chunk.start)
    return replace(record, chunks=(*kept, chunk))


# ---------------------------------------------------------------------------
# Chunk execution (top-level functions so a process pool can pickle them)
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_modular_chunk(first, second, start: int, count: int, seed: int,
                      maximum_rounds: int, context=None) -> SampleChunk:
    """Duels ``[start, start + count)`` of the sequential oracle sample."""
    from mordheim_combat.modular.duel import simulate_duel_reference

    started = time.perf_counter()
    result = simulate_duel_reference(
        first, second, count, seed=seed + start, maximum_rounds=maximum_rounds,
        context=context,
    )
    return SampleChunk(
        start, count, result.first_wins, result.second_wins, result.unresolved,
        time.perf_counter() - started, _now(),
    )


def run_native_chunk(first, second, start: int, count: int, seed: int,
                     chunk_size: int, maximum_rounds: int, context=None) -> SampleChunk:
    """Batch ``start // chunk_size`` of the native sample seeded ``seed``.

    ``seed`` is the engine seed (already offset).  The batch seed mirrors the
    extension's ``seed + batch_index * stride`` in 64-bit arithmetic, and
    ``batch_size=count`` keeps the batch whole, so the stored total equals one
    native request with ``batch_size=chunk_size``.
    """
    from mordheim_combat.vectorized import simulate_duel

    if start % chunk_size:
        raise ValueError("a native chunk must start on a batch boundary")
    index = start // chunk_size
    batch_seed = ((seed & _UINT64) + index * NATIVE_BATCH_STRIDE) & _UINT64
    started = time.perf_counter()
    result = simulate_duel(DuelRequest(
        first, second, count, seed=batch_seed, batch_size=count,
        maximum_rounds=maximum_rounds, context=context,
    ), backend="native")
    return SampleChunk(
        start, count, result.first_wins, result.second_wins, result.unresolved,
        time.perf_counter() - started, _now(),
    )


def run_numpy_chunk(first, second, start: int, count: int, seed: int,
                    chunk_size: int, maximum_rounds: int, context=None) -> SampleChunk:
    """Persist one canonical NumPy batch, preserving its independent stream."""
    from mordheim_combat.vectorized import batch_segment

    if start % chunk_size:
        raise ValueError("a numpy chunk must start on a batch boundary")
    index = start // chunk_size
    started = time.perf_counter()
    first_wins, second_wins, unresolved = batch_segment(
        first, second, index, index + 1, start + count, chunk_size, seed,
        maximum_rounds, None, context,
    )
    return SampleChunk(
        start, count, first_wins, second_wins, unresolved,
        time.perf_counter() - started, _now(),
    )


# ---------------------------------------------------------------------------
# Sampling one scenario with persistence
# ---------------------------------------------------------------------------

def _fresh_record(engine: str, scenario: CampaignScenario, *, seed: int,
                  maximum_rounds: int, chunk_size: int) -> SampleRecord:
    return SampleRecord(
        engine=engine, corpus_key=scenario.key, scenario=scenario.name,
        seed=seed, maximum_rounds=maximum_rounds, chunk_size=chunk_size,
        inputs_sha256=str(scenario.case.fingerprints.get("inputs_sha256", "")),
        engine_digest=engine_digest(engine), environment=_environment(),
        created_at=_now(),
    )


def _identity_mismatch(stored: SampleRecord, wanted: SampleRecord) -> str | None:
    for field in ("engine", "corpus_key", "seed", "maximum_rounds", "chunk_size",
                  "inputs_sha256"):
        if getattr(stored, field) != getattr(wanted, field):
            return f"{field} {getattr(stored, field)!r} != {getattr(wanted, field)!r}"
    if stored.engine_digest != wanted.engine_digest:
        return (
            f"{stored.engine} engine digest changed "
            f"({stored.engine_digest[:12]} -> {wanted.engine_digest[:12]})"
        )
    return None


def open_sample(
    engine: str, scenario: CampaignScenario, store: Path, *, seed: int,
    maximum_rounds: int, chunk_size: int, replace_stale: bool = False,
) -> tuple[Path, SampleRecord]:
    """Load the record to extend, or start a fresh one.

    A stored record whose identity (inputs, seed, rounds, chunk size or engine
    digest) differs from the request is an error unless ``replace_stale``.
    """
    path = sample_path(store, engine, scenario.key)
    wanted = _fresh_record(
        engine, scenario, seed=seed, maximum_rounds=maximum_rounds,
        chunk_size=chunk_size,
    )
    stored = load_sample(path)
    if stored is None:
        return path, wanted
    mismatch = _identity_mismatch(stored, wanted)
    if mismatch is None:
        return path, stored
    if replace_stale:
        return path, wanted
    raise SampleStoreError(
        f"{path}: stored sample does not match this request ({mismatch}); "
        "pass --replace to discard it, or use another --store"
    )


def sample_scenarios(
    engine: str, scenarios: Iterable[CampaignScenario], store: Path, *, simulations: int,
    seed: int, maximum_rounds: int | None = None, chunk_size: int = DEFAULT_CHUNK,
    executor: ProcessPoolExecutor | None = None, workers: int = 1,
    replace_stale: bool = False, stop: threading.Event | None = None, log=None,
):
    """Yield saved records using one bounded chunk queue across all scenarios.

    Only the parent writes records. Each scenario's mutable record is shared
    by its in-flight jobs, and released once its last chunk has been saved.
    A graceful stop drains in-flight work without opening further scenarios.
    """
    stopped = lambda: stop is not None and stop.is_set()
    run_chunk = {
        "modular": run_modular_chunk,
        "native": run_native_chunk,
        "numpy": run_numpy_chunk,
    }[engine]

    def jobs():
        for scenario in scenarios:
            if stopped():
                return
            rounds = maximum_rounds or scenario.case.limits.maximum_rounds
            path, record = open_sample(
                engine, scenario, store, seed=seed, maximum_rounds=rounds,
                chunk_size=chunk_size, replace_stale=replace_stale,
            )
            pending = missing_chunks(record, simulations)
            # Shared only by this scenario's jobs; updated by the parent.
            state = [record, 0]
            if log:
                log(f"{engine:7} {scenario.key}: {len(pending)} chunk(s) to run "
                    f"({sum(count for _start, count in pending)} duels)")
            if not pending:
                if log:
                    log(f"{engine:7} {scenario.key}: stored coverage {record.coverage()} "
                        f">= {simulations}, nothing to run")
                yield scenario, path, state, len(pending), None
            for start, count in pending:
                options = (() if engine == "modular" else (chunk_size,)) + (
                    rounds, scenario.case.context,
                )
                arguments = (scenario.case.first, scenario.case.second, start, count,
                             record.engine_seed, *options)
                yield scenario, path, state, len(pending), arguments

    def save(job, chunk):
        scenario, path, state, total, _arguments = job
        record = _with_chunk(state[0], chunk)
        save_sample(path, record)
        state[0] = record
        state[1] += 1
        if log:
            log(f"{engine:7} {scenario.key}: chunk {chunk.start}+{chunk.count} "
                f"saved ({state[1]}/{total}, {chunk.seconds:.2f}s)")
        return scenario, record

    queue = iter(jobs())
    in_flight = {}
    exhausted = False
    try:
        while True:
            while not exhausted and not stopped() and len(in_flight) < max(1, workers):
                job = next(queue, None)
                if job is None:
                    exhausted = True
                    break
                if job[4] is None:
                    yield job[0], job[2][0]
                elif executor is None:
                    yield save(job, run_chunk(*job[4]))
                else:
                    in_flight[executor.submit(run_chunk, *job[4])] = job
            if not in_flight:
                break
            finished, _running = wait(in_flight, return_when=FIRST_COMPLETED)
            for future in finished:
                job = in_flight.pop(future)
                yield save(job, future.result())
    finally:
        for future in in_flight:
            future.cancel()


def sample_scenario(
    engine: str, scenario: CampaignScenario, store: Path, *, simulations: int,
    seed: int, maximum_rounds: int, chunk_size: int = DEFAULT_CHUNK,
    executor: ProcessPoolExecutor | None = None, workers: int = 1,
    replace_stale: bool = False, stop: threading.Event | None = None, log=None,
) -> SampleRecord:
    """Bring one scenario up to the target with the shared chunk scheduler."""
    record = None
    for _scenario, record in sample_scenarios(
        engine, (scenario,), store, simulations=simulations, seed=seed,
        maximum_rounds=maximum_rounds, chunk_size=chunk_size, executor=executor,
        workers=workers, replace_stale=replace_stale, stop=stop, log=log,
    ):
        pass
    if record is None:
        _path, record = open_sample(
            engine, scenario, store, seed=seed, maximum_rounds=maximum_rounds,
            chunk_size=chunk_size, replace_stale=replace_stale,
        )
    return record


# ---------------------------------------------------------------------------
# Comparing stored samples
# ---------------------------------------------------------------------------

def _not_run(key: str, maximum_rounds: int, simulations: int, detail: str, *, backend: str = "native") -> ParityRow:
    return ParityRow(
        case=key, backend=backend, maximum_rounds=maximum_rounds,
        simulations=simulations, status="NOT_RUN", detail=f"NOT_RUN:store: {detail}",
    )


def compare_stored(
    scenario: CampaignScenario, store: Path, *, simulations: int | None = None, backend: str = "native",
    reference_store: Path | None = None,
) -> tuple[ParityRow, dict[str, object]]:
    """Decide one scenario from its two stored samples.

    ``simulations`` selects the compared prefix; by default the widest prefix
    both samples cover.  Returns the row and a provenance record naming the
    files, digests and coverage that produced it.  A missing, mismatched or
    too-narrow sample yields a ``NOT_RUN`` row, never a verdict.
    """
    if backend not in ("native", "numpy"):
        raise ValueError(f"unsupported candidate backend: {backend}")
    case = scenario.case
    rounds = case.limits.maximum_rounds
    records: dict[str, SampleRecord | None] = {}
    provenance: dict[str, object] = {"corpus_key": scenario.key}
    for engine in ("modular", backend):
        engine_store = reference_store if engine == "modular" and reference_store is not None else store
        path = sample_path(engine_store, engine, scenario.key)
        try:
            record = load_sample(path)
        except SampleStoreError as error:
            return _not_run(scenario.key, rounds, simulations or 0, str(error), backend=backend), provenance
        records[engine] = record
        provenance[engine] = None if record is None else {
            "path": path.as_posix(), "coverage": record.coverage(),
            "seed": record.seed, "maximum_rounds": record.maximum_rounds,
            "chunk_size": record.chunk_size, "engine_digest": record.engine_digest,
            "inputs_sha256": record.inputs_sha256,
            "current_engine_digest": engine_digest(engine),
        }
    missing = [engine for engine, record in records.items() if record is None]
    if missing:
        return _not_run(
            scenario.key, rounds, simulations or 0,
            f"no stored {' and '.join(missing)} sample under {Path(store).as_posix()}", backend=backend,
        ), provenance
    modular, candidate = records["modular"], records[backend]
    assert modular is not None and candidate is not None
    expected = str(case.fingerprints.get("inputs_sha256", ""))
    problems = []
    for record in (modular, candidate):
        if record.inputs_sha256 != expected:
            problems.append(f"{record.engine} sample was taken on other fighters")
    if modular.maximum_rounds != candidate.maximum_rounds:
        problems.append(
            f"round budgets differ (modular {modular.maximum_rounds}, "
            f"{backend} {candidate.maximum_rounds})"
        )
    if modular.seed != candidate.seed:
        problems.append(f"seeds differ (modular {modular.seed}, {backend} {candidate.seed})")
    if problems:
        return _not_run(scenario.key, rounds, simulations or 0, "; ".join(problems), backend=backend), provenance
    width = simulations if simulations is not None else min(
        modular.coverage(), candidate.coverage(),
    )
    if width < 1:
        return _not_run(scenario.key, modular.maximum_rounds, 0, "a stored sample is empty", backend=backend), provenance
    try:
        result = compare_samples(
            scenario.key, width, modular.counts(width), candidate.counts(width),
            reference_seconds=modular.seconds(width),
            candidate_seconds=candidate.seconds(width), backend=backend,
        )
    except SampleStoreError as error:
        return _not_run(scenario.key, modular.maximum_rounds, width, str(error), backend=backend), provenance
    provenance["compared_simulations"] = width
    return parity_row(result, maximum_rounds=modular.maximum_rounds), provenance


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return number


def _add_selection(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("scenario selection")
    group.add_argument(
        "--level", choices=(*LEVELS, "e2e"), default="small",
        help="cumulative scenario level: small, normal, long; or all E2E deliveries (default: small)",
    )
    group.add_argument(
        "--id", dest="ids", action="append", default=[], metavar="KEY",
        help="uniform corpus key to keep, repeatable; must belong to the level",
    )
    parser.add_argument(
        "--store", default="reports/parity-store", metavar="DIR",
        help="directory holding <engine>/<scenario>.json samples "
             "(default: reports/parity-store)",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.verification.parity_samples",
        description="Sample the modular, native and NumPy engines separately, persist "
                    "the samples chunk by chunk, and compare them later.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    sample = commands.add_parser("sample", help="run one engine and store its counts")
    _add_selection(sample)
    sample.add_argument("--engine", choices=ENGINES, required=True)
    sample.add_argument(
        "--simulations", type=_positive, default=1_000, metavar="DUELS",
        help="target duels per scenario; existing chunks are kept (default: 1000)",
    )
    sample.add_argument("--seed", type=int, default=2_026,
                        help="oracle seed; candidate samples use seed + 1000003 (default: 2026)")
    sample.add_argument("--rounds", type=_positive, default=None, metavar="N",
                        help="override every scenario's round budget (default: 50 for E2E, frozen limits otherwise)")
    sample.add_argument("--chunk", type=_positive, default=DEFAULT_CHUNK, metavar="DUELS",
                        help=f"duels per stored chunk / candidate batch (default: {DEFAULT_CHUNK})")
    sample.add_argument("--workers", type=_positive, default=1, metavar="N",
                        help="worker processes for any engine (default: 1)")
    sample.add_argument("--replace", action="store_true",
                        help="discard a stored sample whose identity or engine digest differs")

    compare = commands.add_parser("compare", help="decide stored pairs and write the report")
    _add_selection(compare)
    compare.add_argument("--backend", choices=("native", "numpy"), default="native",
                         help="candidate to compare against modular (default: native)")
    compare.add_argument("--reference-store", default=None, metavar="DIR",
                         help="separate store for saved modular samples (default: --store)")
    compare.add_argument("--simulations", type=_positive, default=None, metavar="DUELS",
                         help="compared prefix width (default: widest common coverage)")
    compare.add_argument("--output", default=None, metavar="DIR",
                         help="report directory (default: <store>/compare)")

    status = commands.add_parser("status", help="list stored coverage per scenario and engine")
    _add_selection(status)
    return parser


def _selection(args) -> tuple[tuple[CampaignScenario, ...], tuple[tuple[str, str], ...], tuple[tuple[str, str], ...]]:
    if args.level == "e2e":
        from tools.verification import e2e_parity

        index, defects = e2e_parity.discover()
        if defects or not index:
            raise SampleStoreError("; ".join(defects) or "the E2E delivery catalogue is empty")
        try:
            deliveries = e2e_parity.select(index, args.ids or list(index))
        except e2e_parity.SelectionError as error:
            raise SampleStoreError(str(error)) from error
        scenarios, rejected, chosen = [], [], []
        policy = e2e_parity.decision_policy_evidence()
        for delivery in deliveries:
            chosen.append((delivery.case_key, delivery.test_id))
            validation = e2e_parity.validate(delivery)
            admission = e2e_parity.admit(
                delivery.with_validation(validation), policy_corresponds=policy["corresponds"],
            )
            if admission.state == "admitted":
                case = replace(admission.case, limits=replace(
                    admission.case.limits, maximum_rounds=e2e_parity.CAMPAIGN_MAXIMUM_ROUNDS,
                ))
                scenarios.append(CampaignScenario(delivery.case_key, delivery.test_id, case))
            else:
                rejected.append((delivery.case_key, f"{admission.state}: {admission.detail}"))
        return tuple(scenarios), tuple(rejected), tuple(chosen)
    chosen = select(level=args.level, keys=args.ids)
    cases = load_cases(CORPUS)
    scenarios, rejected = load(chosen, cases)
    return scenarios, rejected, chosen


def _log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


def _run_sample(args) -> int:
    if args.engine == "native":
        try:
            from mordheim_combat.vectorized import available_backends
        except ImportError:
            print("parity samples: this checkout does not provide the native engine; "
                  "integrate and build it before sampling native", file=sys.stderr)
            return 2

        if "native" not in available_backends():
            print("parity samples: the native combat extension is not available; "
                  "rebuild it and run again", file=sys.stderr)
            return 2
    scenarios, rejected, _chosen = _selection(args)
    for key, reason in rejected:
        print(f"NOT_RUN: {key}: {reason}", file=sys.stderr)
    store = Path(args.store)
    _log(f"{args.engine} digest {engine_digest(args.engine)[:12]}; store {store.as_posix()}; "
         f"{len(scenarios)} scenario(s), target {args.simulations} duels, chunk {args.chunk}")
    pool = None
    if args.workers > 1:
        pool = ProcessPoolExecutor(max_workers=args.workers)

    # First SIGINT/SIGTERM: stop submitting, save the in-flight chunks, exit
    # 130.  Second one: abandon the in-flight chunks (they are not saved).
    stop = threading.Event()

    def _request_stop(signum, _frame):
        if stop.is_set():
            raise KeyboardInterrupt
        stop.set()
        _log(f"stop requested ({signal.Signals(signum).name}): finishing in-flight "
             "chunk(s), nothing new is started; repeat to abort immediately")

    previous = {sig: signal.signal(sig, _request_stop) for sig in (signal.SIGINT, signal.SIGTERM)}
    incomplete = {key for key, _reason in rejected} | {scenario.key for scenario in scenarios}
    aborted = False
    try:
        try:
            for scenario, record in sample_scenarios(
                args.engine, scenarios, store, simulations=args.simulations,
                seed=args.seed, maximum_rounds=args.rounds, chunk_size=args.chunk,
                executor=pool, workers=args.workers, replace_stale=args.replace,
                stop=stop, log=_log,
            ):
                if record.coverage() >= args.simulations:
                    incomplete.discard(scenario.key)
        except SampleStoreError as error:
            print(f"parity samples: {error}", file=sys.stderr)
            return 2
    except KeyboardInterrupt:
        aborted = True
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
        if pool is not None:
            pool.shutdown(wait=not aborted, cancel_futures=True)
    if aborted or stop.is_set():
        _log("stopped: finished chunks are stored; rerun the same command to resume"
             + (" (in-flight chunks were abandoned)" if aborted else ""))
        return 130
    if incomplete:
        _log(f"incomplete: {', '.join(sorted(incomplete))}")
        return 1
    _log(f"complete: {len(scenarios)} scenario(s) at >= {args.simulations} duels")
    return 0


def _run_compare(args) -> int:
    scenarios, rejected, chosen = _selection(args)
    store = Path(args.store)
    started = time.perf_counter()
    rows: list[ParityRow] = []
    provenance: list[dict[str, object]] = []
    for scenario in scenarios:
        row, record = compare_stored(scenario, store, simulations=args.simulations, backend=args.backend,
                                     reference_store=Path(args.reference_store) if args.reference_store else None)
        rows.append(row)
        provenance.append(record)
    corpus = CORPUS
    if args.level == "e2e":
        from tools.verification import e2e_parity

        corpus = e2e_parity.deliveries_directory()
    corpus_digest = (_digest_files(corpus.glob("*.json")) if corpus.is_dir()
                     else hashlib.sha256(corpus.read_bytes()).hexdigest())
    config = {
        "level": args.level,
        "scenario_keys": [key for key, _name in chosen],
        "simulations": args.simulations if args.simulations is not None else "stored coverage",
        "seed": sorted({
            item["modular"]["seed"] for item in provenance
            if isinstance(item.get("modular"), dict)
        }) or None,
        "maximum_rounds": None,
        "workers": "stored samples",
        "corpus": corpus.relative_to(_ROOT).as_posix(),
        "corpus_sha256": corpus_digest,
        "store": store.as_posix(),
        "candidate_backend": args.backend,
        "modular_digest": engine_digest("modular"),
        f"{args.backend}_digest": engine_digest(args.backend),
    }
    payload = campaign_payload(
        rows, config=config, rejected=rejected,
        elapsed_seconds=time.perf_counter() - started,
    )
    payload["source"] = "stored samples (tools.verification.parity_samples)"
    payload["samples"] = provenance
    output = Path(args.output) if args.output else store / "compare"
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "parity-campaign.json"
    markdown_path = output / "parity-campaign.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(campaign_markdown(payload), encoding="utf-8")
    coverage = payload["coverage"]
    assert isinstance(coverage, dict)
    print(
        f"parity samples: {coverage['selected']} selected, "
        f"{coverage['compared']} compared, {coverage['approved']} approved, "
        f"{coverage['divergent']} divergent, {coverage['not_run']} not run"
    )
    for row in payload["scenarios"]:
        if row["verdict"] != "pass":
            print(f"{row['status']}: {row['corpus_key']}: {row['detail']}")
    print(f"complete={payload['complete']}")
    print(f"report={json_path.as_posix()}")
    print(f"report={markdown_path.as_posix()}")
    return 0 if payload["complete"] else 1


def _run_status(args) -> int:
    scenarios, rejected, _chosen = _selection(args)
    store = Path(args.store)
    current = {engine: engine_digest(engine) for engine in ENGINES}
    print(f"store: {store.as_posix()}")
    for engine in ENGINES:
        print(f"current {engine} digest: {current[engine][:12]}")
    print(f"{'corpus key':42} {'engine':7} {'coverage':>8} {'chunk':>6} {'seed':>8} {'rounds':>6} digest       state")
    for scenario in scenarios:
        for engine in ENGINES:
            path = sample_path(store, engine, scenario.key)
            try:
                record = load_sample(path)
            except SampleStoreError as error:
                print(f"{scenario.key:42} {engine:7} {'-':>8} {'-':>6} {'-':>8} {'-':>6} {'-':12} unreadable: {error}")
                continue
            if record is None:
                print(f"{scenario.key:42} {engine:7} {0:>8} {'-':>6} {'-':>8} {'-':>6} {'-':12} absent")
                continue
            state = "current" if record.engine_digest == current[engine] else "STALE engine"
            expected = str(scenario.case.fingerprints.get("inputs_sha256", ""))
            if record.inputs_sha256 != expected:
                state += ", OTHER FIGHTERS"
            print(
                f"{scenario.key:42} {engine:7} {record.coverage():>8} {record.chunk_size:>6} "
                f"{record.seed:>8} {record.maximum_rounds:>6} {record.engine_digest[:12]} {state}"
            )
    for key, reason in rejected:
        print(f"{key:42} NOT_RUN {reason}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "sample":
            return _run_sample(args)
        if args.command == "compare":
            return _run_compare(args)
        return _run_status(args)
    except ValueError as error:
        # Unknown keys, out-of-level keys and corpus errors are configuration.
        if isinstance(error, (CompiledCaseError, SampleStoreError)) or "scenario key" in str(error):
            print(f"parity samples: {error}", file=sys.stderr)
            return 2
        raise
    except OSError as error:
        print(f"parity samples: {error}", file=sys.stderr)
        return 2


__all__ = (
    "DEFAULT_CHUNK",
    "ENGINES",
    "NATIVE_BATCH_STRIDE",
    "NATIVE_SEED_OFFSET",
    "SCHEMA",
    "SampleChunk",
    "SampleRecord",
    "SampleStoreError",
    "compare_stored",
    "engine_digest",
    "load_sample",
    "missing_chunks",
    "open_sample",
    "required_chunks",
    "run_modular_chunk",
    "run_native_chunk",
    "sample_path",
    "sample_scenario",
    "save_sample",
)


if __name__ == "__main__":  # pragma: no cover - command entry point
    raise SystemExit(main())

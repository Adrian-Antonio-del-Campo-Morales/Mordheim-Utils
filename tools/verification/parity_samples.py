"""Independent command: sample each engine separately and compare the stored samples.

The campaign (:mod:`tools.verification.parity_campaign`) samples the modular
oracle and the native candidate in one process and compares them immediately.
While the native engine is being debugged that couples the expensive oracle
sample to every native rebuild.  This command splits the campaign into three
steps that persist on disk:

``sample --backend modular``
    Run the oracle for the selected scenarios and store its outcome counts.
``sample --backend native``
    Run the compiled engine for the selected scenarios and store its counts.
``sample --backend numpy``
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
  seed + 1_000_003, batch_size=batch))``, with ``batch`` = ``--batch-size``;
- NumPy chunks use the canonical ``batch_segment`` stream for their batch
  index, matching a NumPy request with the same ``--batch-size``.

Stores accept plain JSON and losslessly compressed ``.json.gz`` records.
New records are written compressed; resuming an existing record preserves its
format.

A record names the fighters it sampled (the corpus ``inputs_sha256`` of the
case) and the engine it ran as a source digest of everything that engine
executes (``mordheim_combat_lab.provenance.engine_sources``): a
change confined to the native sources never moves the modular digest, while a
modular change moves all three, because the candidates import modular helpers.
The record's environment also keeps the source commit, whether the checkout
was dirty and, for native, the built extension's SHA-256.

Old samples are meant to be reused, so provenance never blocks: ``compare``
decides stored pairs produced by other engine versions and reports every
difference as a prominent warning (stderr and report), and ``sample`` extends
such a record with a warning, each new chunk recording its own provenance
(``--replace`` discards the record instead).  Only a different experiment
identity (fighters, seed, rounds or batch size) is refused.  The engine is
digested where it was imported from; pool workers must import exactly the
parent's engine, or the run stops, because that would mix engines inside one
sample.

Usage (from the repository root)::

    python tools/mordheim-utils.py check samples sample --backend modular --scenarios big --workers 4
    python tools/mordheim-utils.py check samples sample --backend native --scenarios big
    python tools/mordheim-utils.py check samples compare --backend native --scenarios big
    python tools/mordheim-utils.py check samples status --scenarios big

(the store defaults to ``outputs/parity-store``; ``python -m
tools.verification.parity_samples`` runs the same tool directly)

Exit codes: ``sample`` returns 0 when every selected scenario reached the
requested width, 1 when something is still missing (including after an
interruption), 2 for a configuration or corpus error; ``compare`` returns the
campaign's codes (0 complete, 1 incomplete, 2 configuration error).
"""
from __future__ import annotations

import argparse
import gzip
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
from concurrent.futures.process import BrokenProcessPool
from dataclasses import asdict
from dataclasses import dataclass
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from tools.verification.e2e_parity import bootstrap_paths
from tools.verification.e2e_parity import repository_root

# Before any engine import: the digests below hash this checkout, so the parent
# and every pool worker must import the engine from it too.
bootstrap_paths(repository_root())

from mordheim_core.models import DuelRequest

from mordheim_combat_lab.cli.options import add_scenarios, size
from mordheim_combat_lab.provenance import digest_files
from mordheim_combat_lab.provenance import engine_sources
from mordheim_combat_lab.provenance import native_build_sha256
from mordheim_combat_lab.provenance import provenance_warning
from mordheim_combat_lab.provenance import source_revision

from tools.verification.compiled_cases import CompiledCaseError
from tools.verification.parity_campaign import campaign_markdown
from tools.verification.parity_campaign import campaign_payload
from tools.verification.parity_catalog import CORPUS
from tools.verification.parity_catalog import CampaignScenario
from tools.verification.parity_catalog import resolve
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
# Engine digests and provenance
# ---------------------------------------------------------------------------

def _digest_files(paths: Iterable[Path]) -> str:
    return digest_files(paths, _ROOT)


def _modular_sources() -> tuple[Path, ...]:
    return engine_sources("modular", _COMBAT, _CORE)


def _native_sources() -> tuple[Path, ...]:
    return engine_sources("native", _COMBAT, _CORE)


def engine_digest(engine: str) -> str:
    """Source digest of one engine: what a stored sample was produced by.

    It hashes every source the engine executes (``provenance.engine_sources``),
    including what a candidate imports from the other engines: a native-only
    change never moves the modular or NumPy digests, but a modular change moves
    all three.  The built native extension is not part of it: its bytes differ
    between machines for identical sources, so records keep it separately as
    ``environment.native_build_sha256``.
    """
    if engine not in ENGINES:
        raise ValueError(f"unknown engine {engine!r}; choose one of {', '.join(ENGINES)}")
    return _digest_files(engine_sources(engine, _COMBAT, _CORE))


_REVISION: dict[str, object] | None = None


def _revision() -> dict[str, object]:
    """Commit and dirty state of this checkout, read once per run."""
    global _REVISION
    if _REVISION is None:
        revision = source_revision(_ROOT)
        _REVISION = {"commit": revision["commit"], "dirty": revision["dirty"]}
    return _REVISION


def _environment(engine: str | None = None) -> dict[str, object]:
    import numpy

    revision = _revision()
    environment: dict[str, object] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "cpu_count": os.cpu_count(),
        "commit": revision["commit"],
        "dirty": revision["dirty"],
    }
    if engine == "native":
        environment["native_build_sha256"] = native_build_sha256()
    return environment


#: What a chunk's provenance names; a chunk records it only when it differs
#: from the record it was added to (an older record extended by a newer run).
PROVENANCE_FIELDS = ("engine_digest", "native_build_sha256", "commit", "dirty")


def current_provenance(engine: str) -> dict[str, object]:
    """The provenance a chunk run now would carry."""
    environment = _environment(engine)
    return {
        "engine_digest": engine_digest(engine),
        **{name: environment.get(name) for name in PROVENANCE_FIELDS[1:]
           if name != "native_build_sha256" or engine == "native"},
    }


def record_provenance(record: "SampleRecord") -> dict[str, object]:
    """The provenance a record was created with (``None`` where unrecorded)."""
    return {
        "engine_digest": record.engine_digest,
        **{name: record.environment.get(name) for name in PROVENANCE_FIELDS[1:]
           if name != "native_build_sha256" or record.engine == "native"},
    }


def engine_origins(engine: str) -> dict[str, str]:
    """Resolved files of the engine modules this process actually imported."""
    import mordheim_combat
    import mordheim_core

    origins = {"mordheim_combat": mordheim_combat.__file__, "mordheim_core": mordheim_core.__file__}
    if engine == "native":
        from mordheim_combat import _combat_native

        origins["mordheim_combat._combat_native"] = _combat_native.__file__
    return {name: str(Path(path).resolve()) for name, path in origins.items()}


def check_engine_origins(engine: str) -> dict[str, str]:
    """Digest the engine that was actually imported, warning when it is foreign.

    ``engine_digest`` hashes the sources under ``_COMBAT``/``_CORE``.  When the
    packages were imported from elsewhere (another checkout, an installed
    copy) the digest roots are moved to the imported packages, so records
    describe the engine that ran, and the difference is reported prominently.
    """
    global _COMBAT, _CORE
    origins = engine_origins(engine)
    for name in ("mordheim_combat", "mordheim_core"):
        imported = Path(origins[name]).parent
        root = (_COMBAT if name == "mordheim_combat" else _CORE).resolve()
        if imported != root:
            provenance_warning(
                f"{name} was imported from {imported.as_posix()}, not from this "
                f"checkout ({root.as_posix()}); samples are digested and labelled "
                "with the imported copy"
            )
            if name == "mordheim_combat":
                _COMBAT = imported
            else:
                _CORE = imported
    return origins


def _check_worker_origins(engine: str, expected: dict[str, str]) -> None:
    """Pool initializer: a worker must run the very engine the parent digested."""
    actual = engine_origins(engine)
    if actual != expected:
        differing = ", ".join(
            f"{name}: worker {actual.get(name)} != parent {expected.get(name)}"
            for name in sorted(set(actual) | set(expected))
            if actual.get(name) != expected.get(name)
        )
        raise RuntimeError(f"worker imported a different engine ({differing})")


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
    #: Set only when this chunk was produced under another provenance than
    #: its record's (``PROVENANCE_FIELDS``); ``None`` means "as the record".
    provenance: Mapping[str, object] | None = None

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
        body["chunks"] = [
            {name: value for name, value in asdict(chunk).items()
             if name != "provenance" or value is not None}
            for chunk in sorted(self.chunks, key=lambda item: item.start)
        ]
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
    """Resolve an existing JSON/gzip sample, or a new JSON path."""
    if engine not in ENGINES:
        raise ValueError(f"unknown engine {engine!r}")
    name = ("e2e__" + hashlib.sha256(corpus_key.encode()).hexdigest()
            if corpus_key.startswith("e2e/") else corpus_key.replace("/", "__"))
    path = Path(store) / engine / f"{name}.json"
    compressed = path.with_suffix(".json.gz")
    return compressed if not path.exists() and compressed.exists() else path


def load_sample(path: Path) -> SampleRecord | None:
    """Return the record at ``path`` or ``None`` when there is none yet."""
    path = Path(path)
    if not path.exists() and path.suffix == ".json":
        path = path.with_suffix(".json.gz")
    if not path.exists():
        return None
    try:
        data = path.read_bytes()
        if data.startswith(b"\x1f\x8b"):
            data = gzip.decompress(data)
        raw = json.loads(data.decode("utf-8"))
    except (OSError, EOFError, ValueError) as error:
        raise SampleStoreError(f"{path}: unreadable sample: {error}") from error
    return SampleRecord.from_json(raw, str(path))


def save_sample(path: Path, record: SampleRecord) -> None:
    """Write atomically, tolerating brief Windows access/sharing locks."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    data = (json.dumps(record.to_json(), ensure_ascii=True, indent=1) + "\n").encode("utf-8")
    if path.suffix == ".gz":
        data = gzip.compress(data, compresslevel=9, mtime=0)
    temporary.write_bytes(data)
    # A reader or scanner can briefly deny replacement on Windows. Keep the
    # closed temporary file and retry only the rename, never the simulation.
    for delay in (0.05, 0.1, 0.2, 0.4, 0.8, 1.0, None):
        try:
            os.replace(temporary, path)
            return
        except PermissionError as error:
            if getattr(error, "winerror", None) not in (5, 32, 33) or delay is None:
                raise
            time.sleep(delay)


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
        engine_digest=engine_digest(engine), environment=_environment(engine),
        created_at=_now(),
    )


def _identity_mismatch(stored: SampleRecord, wanted: SampleRecord) -> str | None:
    """The experiment-identity field that differs; chunks cannot be pooled then."""
    for field in ("engine", "corpus_key", "seed", "maximum_rounds", "chunk_size",
                  "inputs_sha256"):
        if getattr(stored, field) != getattr(wanted, field):
            return f"{field} {getattr(stored, field)!r} != {getattr(wanted, field)!r}"
    return None


def provenance_changes(recorded: Mapping[str, object], current: Mapping[str, object]) -> list[str]:
    """Human descriptions of every provenance field that differs."""
    changes = []
    for name in PROVENANCE_FIELDS:
        if name not in recorded and name not in current:
            continue
        before, after = recorded.get(name), current.get(name)
        if before is None and name != "dirty":
            changes.append(f"{name} not recorded")
        elif before != after:
            show = (lambda value: value[:12] if isinstance(value, str) else repr(value))
            changes.append(f"{name} {show(before)} -> {show(after)}")
    return changes


def open_sample(
    engine: str, scenario: CampaignScenario, store: Path, *, seed: int,
    maximum_rounds: int, chunk_size: int, replace_stale: bool = False,
    compress: bool = False,
) -> tuple[Path, SampleRecord]:
    """Load the record to extend, or start a fresh one.

    A stored record whose experiment identity (inputs, seed, rounds or chunk
    size) differs from the request is an error unless ``replace_stale``.  A
    record produced by another engine version is extended with a provenance
    warning (its new chunks carry their own provenance), or discarded when
    ``replace_stale``.
    """
    path = sample_path(store, engine, scenario.key)
    wanted = _fresh_record(
        engine, scenario, seed=seed, maximum_rounds=maximum_rounds,
        chunk_size=chunk_size,
    )
    stored = load_sample(path)
    if stored is None:
        if compress:
            path = path.with_suffix(".json.gz")
        return path, wanted
    mismatch = _identity_mismatch(stored, wanted)
    changes = provenance_changes(record_provenance(stored), record_provenance(wanted))
    if mismatch is None and not changes:
        return path, stored
    if replace_stale:
        return path, wanted
    if mismatch is not None:
        raise SampleStoreError(
            f"{path}: stored sample does not match this request ({mismatch}); "
            "pass --replace to discard it, or use another --store"
        )
    return path, stored


def sample_scenarios(
    engine: str, scenarios: Iterable[CampaignScenario], store: Path, *, simulations: int,
    seed: int, maximum_rounds: int | None = None, chunk_size: int = DEFAULT_CHUNK,
    executor: ProcessPoolExecutor | None = None, workers: int = 1,
    replace_stale: bool = False, stop: threading.Event | None = None, log=None,
    verbose: bool = False, compress: bool = False,
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
    # Every chunk of this run is attributed to the provenance current when it
    # started (pool workers import the engine once); a source change seen at
    # a later save is flagged on the chunks saved after it.
    started_with = current_provenance(engine)
    changed_during_run: list[str] = []

    def jobs():
        for scenario in scenarios:
            if stopped():
                return
            started = time.perf_counter()
            rounds = maximum_rounds or scenario.case.limits.maximum_rounds
            path, record = open_sample(
                engine, scenario, store, seed=seed, maximum_rounds=rounds,
                chunk_size=chunk_size, replace_stale=replace_stale, compress=compress,
            )
            pending = missing_chunks(record, simulations)
            changes = provenance_changes(record_provenance(record), started_with)
            if pending and changes:
                provenance_warning(
                    f"extending the {engine} sample of {scenario.key}, which was "
                    f"produced under another provenance ({'; '.join(changes)}); "
                    "the new chunks record their own provenance, so this record "
                    "mixes engine versions (pass --replace to discard it instead)"
                )
            # Shared only by this scenario's jobs; updated by the parent.
            state = [record, 0, started]
            if log:
                detail = f"; {len(pending)} chunk(s) to run" if verbose else ""
                log(f"{engine:7} {scenario.key}: started "
                    f"({sum(count for _start, count in pending)} duels remaining{detail})")
            if not pending:
                if log:
                    log(f"{engine:7} {scenario.key}: complete in "
                        f"{time.perf_counter() - started:.2f}s; stored coverage "
                        f"{record.coverage()} >= {simulations}, nothing to run")
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
        provenance = dict(started_with)
        now = engine_digest(engine)
        if now != started_with["engine_digest"]:
            if not changed_during_run:
                changed_during_run.append(now)
                provenance_warning(
                    f"the {engine} engine sources changed during this run "
                    f"({started_with['engine_digest'][:12]} -> {now[:12]}); chunks "
                    "saved from now on may come from either version and are marked "
                    "sources_changed_during_run"
                )
            provenance.update(sources_changed_during_run=True, engine_digest_at_save=now)
        if provenance_changes(record_provenance(state[0]), provenance) or len(provenance) > len(started_with):
            chunk = replace(chunk, provenance=provenance)
        record = _with_chunk(state[0], chunk)
        save_sample(path, record)
        state[0] = record
        state[1] += 1
        if log and verbose:
            log(f"{engine:7} {scenario.key}: chunk {chunk.start}+{chunk.count} "
                f"saved ({state[1]}/{total}, {chunk.seconds:.2f}s)")
        if log and state[1] == total:
            log(f"{engine:7} {scenario.key}: complete in "
                f"{time.perf_counter() - state[2]:.2f}s; coverage {record.coverage()}")
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
    verbose: bool = False, compress: bool = False,
) -> SampleRecord:
    """Bring one scenario up to the target with the shared chunk scheduler."""
    record = None
    for _scenario, record in sample_scenarios(
        engine, (scenario,), store, simulations=simulations, seed=seed,
        maximum_rounds=maximum_rounds, chunk_size=chunk_size, executor=executor,
        workers=workers, replace_stale=replace_stale, stop=stop, log=log, verbose=verbose, compress=compress,
    ):
        pass
    if record is None:
        _path, record = open_sample(
            engine, scenario, store, seed=seed, maximum_rounds=maximum_rounds,
            chunk_size=chunk_size, replace_stale=replace_stale, compress=compress,
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


def _record_warnings(record: SampleRecord, current: Mapping[str, object]) -> list[str]:
    """Why a stored record may not describe the current engine (never fatal)."""
    recorded = record_provenance(record)
    warnings = []
    if recorded["engine_digest"] != current["engine_digest"]:
        warnings.append(f"produced by another {record.engine} engine version "
                        f"(digest {recorded['engine_digest'][:12]}, current "
                        f"{current['engine_digest'][:12]})")
    if record.engine == "native" and recorded.get("native_build_sha256") not in (
            None, current.get("native_build_sha256")):
        warnings.append("produced by another native build (expected across machines "
                        "and compilers; sources are compared by the engine digest)")
    if recorded.get("commit") is None:
        warnings.append("no source revision recorded (sampled before revisions were kept)")
    if recorded.get("dirty"):
        warnings.append(f"produced from a checkout with uncommitted changes "
                        f"(commit {str(recorded.get('commit'))[:12]}); it matches no commit")
    mixed = [chunk for chunk in record.chunks if chunk.provenance is not None]
    if mixed:
        changed = sum(1 for chunk in mixed if chunk.provenance.get("sources_changed_during_run"))
        warnings.append(f"{len(mixed)} of {len(record.chunks)} chunk(s) were added under "
                        "another provenance than the record's"
                        + (f", {changed} while the sources were changing" if changed else ""))
    return warnings


def compare_stored(
    scenario: CampaignScenario, store: Path, *, simulations: int | None = None, backend: str = "native",
    reference_store: Path | None = None, current: Mapping[str, Mapping[str, object]] | None = None,
    reference: str = "modular",
) -> tuple[ParityRow, dict[str, object]]:
    """Decide one scenario from its two stored samples.

    ``reference`` is the engine whose sample the candidate ``backend`` is
    judged against: the modular oracle by default, or a candidate -- NumPy
    against its own earlier sample (``reference_store``) to show a change
    moved nothing, or native against NumPy.  ``simulations`` selects the
    compared prefix; by default the widest prefix both samples cover.  Returns
    the row and a provenance record naming the files, digests and coverage
    that produced it.  A missing, mismatched or too-narrow sample yields a
    ``NOT_RUN`` row, never a verdict.

    Samples produced by another engine version than ``current`` (the current
    provenance per engine, computed here when omitted) are still compared:
    each difference is listed in the engine's ``warnings`` so the caller can
    report it, but it never changes the verdict.
    """
    if backend not in ("native", "numpy"):
        raise ValueError(f"unsupported candidate backend: {backend}")
    if reference not in ENGINES:
        raise ValueError(f"unsupported reference engine: {reference}")
    case = scenario.case
    rounds = case.limits.maximum_rounds
    # Keyed by engine name, except a reference of the candidate's own engine.
    roles = {"reference": reference if reference != backend else f"{reference}-reference",
             "candidate": backend}
    engines = {"reference": reference, "candidate": backend}
    records: dict[str, SampleRecord | None] = {}
    provenance: dict[str, object] = {"corpus_key": scenario.key}
    for role in ("reference", "candidate"):
        engine = engines[role]
        engine_store = (reference_store if role == "reference" and reference_store is not None
                        else store)
        path = sample_path(engine_store, engine, scenario.key)
        try:
            record = load_sample(path)
        except SampleStoreError as error:
            return _not_run(scenario.key, rounds, simulations or 0, str(error), backend=backend), provenance
        records[role] = record
        now = (current or {}).get(engine) or current_provenance(engine)
        provenance[roles[role]] = None if record is None else {
            "path": path.as_posix(), "coverage": record.coverage(),
            "seed": record.seed, "maximum_rounds": record.maximum_rounds,
            "chunk_size": record.chunk_size, "engine_digest": record.engine_digest,
            "inputs_sha256": record.inputs_sha256,
            "current_engine_digest": now["engine_digest"],
            "recorded": record_provenance(record),
            "warnings": _record_warnings(record, now),
        }
    missing = [roles[role] for role, record in records.items() if record is None]
    if missing:
        return _not_run(
            scenario.key, rounds, simulations or 0,
            f"no stored {' and '.join(missing)} sample under {Path(store).as_posix()}", backend=backend,
        ), provenance
    oracle, candidate = records["reference"], records["candidate"]
    assert oracle is not None and candidate is not None
    expected = str(case.fingerprints.get("inputs_sha256", ""))
    problems = []
    for role, record in (("reference", oracle), ("candidate", candidate)):
        if record.inputs_sha256 != expected:
            problems.append(f"{roles[role]} sample was taken on other fighters")
    if oracle.maximum_rounds != candidate.maximum_rounds:
        problems.append(
            f"round budgets differ ({roles['reference']} {oracle.maximum_rounds}, "
            f"{backend} {candidate.maximum_rounds})"
        )
    if oracle.seed != candidate.seed:
        problems.append(f"seeds differ ({roles['reference']} {oracle.seed}, {backend} {candidate.seed})")
    if problems:
        return _not_run(scenario.key, rounds, simulations or 0, "; ".join(problems), backend=backend), provenance
    width = simulations if simulations is not None else min(
        oracle.coverage(), candidate.coverage(),
    )
    if width < 1:
        return _not_run(scenario.key, oracle.maximum_rounds, 0, "a stored sample is empty", backend=backend), provenance
    try:
        result = compare_samples(
            scenario.key, width, oracle.counts(width), candidate.counts(width),
            reference_seconds=oracle.seconds(width),
            candidate_seconds=candidate.seconds(width), backend=backend,
        )
    except SampleStoreError as error:
        return _not_run(scenario.key, oracle.maximum_rounds, width, str(error), backend=backend), provenance
    provenance["compared_simulations"] = width
    row = parity_row(result, maximum_rounds=oracle.maximum_rounds)
    if reference == backend:
        # The same engine on the same seed and batch draws the same duels: a
        # change meant to preserve results must reproduce the counts exactly,
        # which the six-sigma gate alone would not show.
        before, after = tuple(oracle.counts(width)), tuple(candidate.counts(width))
        provenance["identical_counts"] = before == after
        note = ("identical counts" if before == after
                else f"counts differ (first/second/unresolved {before} -> {after})")
        row = replace(row, detail=f"{note}; {row.detail}" if row.detail else note)
    return row, provenance


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return number


def _add_selection(parser: argparse.ArgumentParser) -> None:
    group = parser.add_argument_group("what runs")
    add_scenarios(group, default="small")
    parser.add_argument(
        "--store", default="outputs/parity-store", metavar="DIR",
        help="directory holding <engine>/<scenario>.json[.gz] samples "
             "(default: outputs/parity-store)",
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python tools/mordheim-utils.py check samples",
        description="Sample one engine at a time into a store, chunk by chunk "
                    "(resumable), and compare stored samples later without "
                    "running either engine again.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    sample = commands.add_parser("sample", help="run one engine and store its counts")
    _add_selection(sample)
    sample.add_argument("--backend", choices=ENGINES, required=True,
                        help="engine to sample")
    sample.add_argument(
        "--simulations", type=size, default=10_000, metavar="N",
        help="target duels per scenario; k/m suffixes; stored chunks are kept "
             "(default: 10000)")
    sample.add_argument("--seed", type=int, default=2_026,
                        help="random seed; candidate samples use seed + 1000003 (default: 2026)")
    sample.add_argument("--rounds", type=size, default=None, metavar="N",
                        help="round limit replacing each scenario's own")
    sample.add_argument("--batch-size", type=size, default=DEFAULT_CHUNK, metavar="N",
                        help="duels per engine batch, which is also the stored chunk; "
                             "the batch selects the random streams, so a re-sample "
                             f"must repeat it (default: {DEFAULT_CHUNK})")
    sample.add_argument("--workers", type=_positive, default=1, metavar="N",
                        help="worker processes, for any engine (default: 1)")
    sample.add_argument("--replace", action="store_true",
                        help="discard a stored sample whose identity or engine digest differs")

    compare = commands.add_parser("compare", help="decide stored pairs and write the report")
    _add_selection(compare)
    compare.add_argument("--backend", choices=("native", "numpy"), default="numpy",
                         help="candidate engine (default: numpy)")
    compare.add_argument(
        "--reference", choices=ENGINES, default="modular",
        help="engine the candidate is judged against: modular (the oracle), or "
             "numpy -- the candidate's own earlier sample in --reference-store "
             "shows a change moved nothing, native against numpy cross-checks "
             "the port (default: modular)")
    compare.add_argument("--reference-store", default=None, metavar="DIR",
                         help="store holding the reference samples (default: --store)")
    compare.add_argument("--simulations", type=size, default=None, metavar="N",
                         help="compared prefix width (default: widest common coverage)")
    compare.add_argument("--output", default=None, metavar="DIR",
                         help="report directory (default: <store>/compare)")

    status = commands.add_parser("status", help="list stored coverage per scenario and engine")
    _add_selection(status)
    return parser


def _selection(args):
    """``(runnable cases, rejected, selected entries)`` for ``--scenarios``."""
    try:
        return resolve(args.scenarios or ("small",))
    except ValueError as error:
        raise SampleStoreError(str(error)) from error


def _log(message: str) -> None:
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}", flush=True)


def _run_sample(args) -> int:
    if args.backend == "native":
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
    global _REVISION
    _REVISION = None
    origins = check_engine_origins(args.backend)
    _log(f"{args.backend} digest {engine_digest(args.backend)[:12]}; store {store.as_posix()}; "
         f"{len(scenarios)} scenario(s), target {args.simulations} duels, batch {args.batch_size}")
    pool = None
    if args.workers > 1:
        pool = ProcessPoolExecutor(max_workers=args.workers, initializer=_check_worker_origins,
                                   initargs=(args.backend, origins))

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
                args.backend, scenarios, store, simulations=args.simulations,
                seed=args.seed, maximum_rounds=args.rounds, chunk_size=args.batch_size,
                executor=pool, workers=args.workers, replace_stale=args.replace,
                stop=stop, log=_log, compress=True,
            ):
                if record.coverage() >= args.simulations:
                    incomplete.discard(scenario.key)
        except SampleStoreError as error:
            print(f"parity samples: {error}", file=sys.stderr)
            return 2
        except BrokenProcessPool as error:
            # A worker whose engine differs from the parent's fails its
            # initializer (reported above); nothing it ran was saved.
            print(f"parity samples: worker pool failed: {error}", file=sys.stderr)
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
    current = {engine: current_provenance(engine) for engine in (args.reference, args.backend)}
    reference_key = (args.reference if args.reference != args.backend
                     else f"{args.reference}-reference")
    for scenario in scenarios:
        row, record = compare_stored(scenario, store, simulations=args.simulations, backend=args.backend,
                                     reference_store=Path(args.reference_store) if args.reference_store else None,
                                     current=current, reference=args.reference)
        rows.append(row)
        provenance.append(record)
    warnings = _grouped_warnings(provenance)
    for message in warnings:
        provenance_warning(message)
    from tools.verification import e2e_parity

    kinds = {entry.kind for entry in chosen}
    sources = [path for kind, path in (
        ("scenario", CORPUS),
        ("e2e", e2e_parity.deliveries_directory()),
        ("battery", _ROOT / "apps/combat-lab/mordheim_combat_lab/verification/parity/_battery_cases.py"),
    ) if kind in kinds]
    corpus_digest = _digest_files(
        file for path in sources
        for file in (sorted(path.glob("*.json")) if path.is_dir() else (path,)))
    config = {
        "scenarios": list(args.scenarios or ("small",)),
        "scenario_keys": [entry.key for entry in chosen],
        "simulations": args.simulations if args.simulations is not None else "stored coverage",
        "seed": sorted({
            item[reference_key]["seed"] for item in provenance
            if isinstance(item.get(reference_key), dict)
        }) or None,
        "maximum_rounds": None,
        "workers": "stored samples",
        "corpus": ", ".join(path.relative_to(_ROOT).as_posix() for path in sources),
        "corpus_sha256": corpus_digest,
        "store": store.as_posix(),
        "candidate_backend": args.backend,
        "reference": args.reference,
        # The engines that produced the compared samples, and today's engines.
        "recorded_engine_digests": {
            engine: sorted({item[engine]["engine_digest"] for item in provenance
                            if isinstance(item.get(engine), dict)})
            for engine in current
        },
        "current_engine_digests": {engine: value["engine_digest"] for engine, value in current.items()},
        "current_revision": _revision(),
    }
    payload = campaign_payload(
        rows, config=config, rejected=rejected,
        elapsed_seconds=time.perf_counter() - started,
    )
    payload["source"] = "stored samples (tools.verification.parity_samples)"
    payload["provenance_warnings"] = warnings
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
        f"{coverage['underpowered']} underpowered, "
        f"{coverage['divergent']} divergent, {coverage['not_run']} not run"
    )
    for row in payload["scenarios"]:
        if row["verdict"] != "pass":
            print(f"{row['status']}: {row['corpus_key']}: {row['detail']}")
    if warnings:
        print(f"parity samples: {len(warnings)} provenance warning(s); see above and the report")
    print(f"complete={payload['complete']}")
    print(f"report={json_path.as_posix()}")
    print(f"report={markdown_path.as_posix()}")
    return 0 if payload["complete"] else 1


def _grouped_warnings(provenance: Sequence[Mapping[str, object]]) -> list[str]:
    """One line per distinct (engine, warning), with the number of samples it hits."""
    groups: dict[tuple[str, str], int] = {}
    for item in provenance:
        for engine, block in item.items():
            if isinstance(block, dict):
                for message in block.get("warnings", ()):
                    groups[(engine, message)] = groups.get((engine, message), 0) + 1
    return [f"{count} stored {engine} sample(s) {message}"
            for (engine, message), count in groups.items()]


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
            if any(chunk.provenance is not None for chunk in record.chunks):
                state += ", MIXED chunk provenance"
            if record.environment.get("dirty"):
                state += ", from uncommitted sources"
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

"""Export reviewed execution inputs to the versioned precompiled corpus.

The exporter is the only producer of ``mordheim-compiled-cases`` documents.  It
compiles explicit ``FighterBuild`` inputs through the construction compiler and
then delegates every structural, fingerprint and canonical-JSON decision to the
T02 codec.  It never runs combat, never invents observations and never derives
expectations from engine output: an expectation channel is copied only when the
case spec declares it explicitly.

Input shape
-----------

``specs`` is either a mapping with ``cases`` (plus optional ``revision`` and
``files`` metadata) or an iterable of case mappings.  Each case accepts::

    case_key | key, origin, fighters, context | duel_context, initial_state,
    dice | rolls, decisions, limits, maximum_rounds, benchmark,
    expectations, expect_* (the reviewed channels)

``origin`` is ``{kind, node_id, path, sha256}``; when ``sha256`` is omitted the
file at ``path`` (relative to the repository root) is hashed.  Any other field,
and every prose field, is rejected so a descriptive note cannot silently become
part of the frozen corpus.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
from typing import Iterable, Mapping

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import CompiledFighter
from mordheim_core.models import DuelContext
from mordheim_core.models import FighterBuild
from mordheim_core.models import LocalParticipant
from tools.verification import compiled_cases as codec


GENERATOR = {"name": "export-compiled-cases", "version": 1}

_CASE_FIELDS = frozenset({
    "case_key", "key", "origin", "fighters", "context", "duel_context",
    "auxiliary_participants", "initial_state", "dice", "rolls", "decisions", "limits", "maximum_rounds",
    "benchmark", "expectations", "expect_initial", "expect_rounds", "expect_final",
    "expect_events", "expect_fighters", "expect_error", "expect", "distribution",
})
_EXPECTATION_FIELDS = (
    "expect_initial", "expect_rounds", "expect_final", "expect_events",
    "expect_fighters", "expect_error", "expect", "distribution",
)
_ORIGIN_FIELDS = frozenset({"kind", "node_id", "path", "sha256"})
_PROSE_FIELDS = frozenset({
    "description", "prose", "comment", "comments", "note", "notes", "summary",
    "text", "rationale", "title",
})
_TUPLE_FIELDS = (
    "defence_ids", "skill_ids", "preparation_ids", "special_rule_ids",
    "variant_ids", "condition_ids", "owned_item_ids",
)


class ExportError(ValueError):
    """A case plan cannot be represented without inventing data."""


@dataclass(frozen=True, slots=True)
class ExportReceipt:
    path: str
    case_count: int
    case_hashes: Mapping[str, str]
    corpus_sha256: str


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _repository_root(kb_root: Path) -> Path:
    resolved = kb_root.resolve()
    if resolved.parent.name == "sources":
        return resolved.parent.parent
    return resolved.parent


def _relative(value: Path, root: Path) -> str:
    try:
        return value.resolve().relative_to(root.resolve()).as_posix()
    except ValueError as error:
        raise ExportError(f"{value}: outside the repository root") from error


def _origin(raw, case_key: str, root: Path) -> codec.CaseOrigin:
    if not isinstance(raw, Mapping):
        raise ExportError(f"{case_key}: origin must be a mapping")
    unknown = sorted(set(raw) - _ORIGIN_FIELDS)
    if unknown:
        raise ExportError(f"{case_key}: unknown origin field(s): {unknown}")
    kind = raw.get("kind", "unit")
    node_id = raw.get("node_id")
    path = raw.get("path")
    digest = raw.get("sha256")
    if not isinstance(node_id, str) or not node_id.strip():
        raise ExportError(f"{case_key}: origin.node_id must be a non-empty string")
    if not isinstance(path, str) or not path.strip():
        raise ExportError(f"{case_key}: origin.path must be a non-empty string")
    if digest is None:
        source = root / path
        if not source.is_file():
            raise ExportError(f"{case_key}: origin source does not exist: {path}")
        digest = _sha256_bytes(source.read_bytes())
    return codec.CaseOrigin(kind=kind, node_id=node_id, path=path, sha256=digest)


def _characteristics(raw) -> Characteristics:
    if isinstance(raw, Characteristics):
        return raw
    if not isinstance(raw, Mapping):
        raise ExportError("characteristics must be a mapping")
    return Characteristics(**raw)


def _fighter(raw, case_key: str, field: str, root: Path, kb_root: Path | None = None) -> CompiledFighter:
    if isinstance(raw, CompiledFighter):
        return raw
    if not isinstance(raw, Mapping):
        raise ExportError(f"{case_key}: {field} must be a mapping or CompiledFighter")
    values = dict(raw)
    if "characteristics" in values:
        values["characteristics"] = _characteristics(values["characteristics"])
    elif not values.get("profile_id"):
        values["characteristics"] = Characteristics(3, 3, 3, 3, 3, 1)
    for name in _TUPLE_FIELDS:
        if name in values and values[name] is not None:
            values[name] = tuple(values[name])
    ruleset = values.pop("ruleset", "mordheim")
    try:
        return compile_fighter(FighterBuild(ruleset, **values), kb_root or root)
    except (TypeError, ValueError) as error:
        raise ExportError(f"{case_key}: cannot compile {field}: {error}") from error


def _participant(raw, case_key: str, field: str, root: Path, kb_root: Path | None = None) -> LocalParticipant:
    if isinstance(raw, LocalParticipant):
        return raw
    if not isinstance(raw, Mapping):
        raise ExportError(f"{case_key}: {field} must be a mapping")
    allowed = {"participant_id", "side_id", "fighter", "condition"}
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise ExportError(f"{case_key}: unknown {field} field(s): {unknown}")
    return LocalParticipant(
        participant_id=raw["participant_id"],
        side_id=raw["side_id"],
        fighter=_fighter(raw["fighter"], case_key, f"{field}.fighter", root, kb_root),
        condition=raw.get("condition", "standing"),
    )


def _context(raw, case_key: str, root: Path, kb_root: Path | None = None) -> DuelContext | None:
    if raw is None:
        return None
    if isinstance(raw, DuelContext):
        return raw
    if not isinstance(raw, Mapping):
        raise ExportError(f"{case_key}: context must be a mapping or null")
    allowed = {
        "first_id", "second_id", "nearby", "distances", "contacts", "terrain",
        "charging", "active_participant",
    }
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise ExportError(f"{case_key}: unknown context field(s): {unknown}")
    values = dict(raw)
    values["nearby"] = tuple(
        _participant(entry, case_key, f"context.nearby[{index}]", root, kb_root)
        for index, entry in enumerate(values.get("nearby", ()))
    )
    return DuelContext(**values)


def _rolls(raw: Iterable, case_key: str) -> tuple[dict, ...]:
    result = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, Mapping):
            raise ExportError(f"{case_key}: roll {index} must be a mapping")
        unknown = sorted(set(entry) - {"key", "sides", "value"})
        if unknown:
            raise ExportError(f"{case_key}: roll {index} has unknown field(s): {unknown}")
        result.append({
            "key": entry.get("key"),
            "sides": entry.get("sides", 6),
            "value": entry.get("value"),
        })
    return tuple(result)


def _decisions(raw: Iterable, case_key: str) -> tuple[dict, ...]:
    result = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, Mapping):
            raise ExportError(f"{case_key}: decision {index} must be a mapping")
        unknown = sorted(set(entry) - {"key", "value"})
        if unknown:
            raise ExportError(f"{case_key}: decision {index} has unknown field(s): {unknown}")
        result.append({"key": entry.get("key"), "value": entry.get("value")})
    return tuple(result)


def _expectations(raw: Mapping, case_key: str) -> dict:
    unknown = sorted(set(raw) - set(_EXPECTATION_FIELDS))
    if unknown:
        raise ExportError(f"{case_key}: unknown expectation channel(s): {unknown}")
    return dict(raw)


def _case(raw, root: Path, kb_root: Path | None = None) -> codec.CompiledCase:
    if not isinstance(raw, Mapping):
        raise ExportError("every case must be a mapping")
    prose = sorted(set(raw) & _PROSE_FIELDS)
    if prose:
        raise ExportError(f"prose is not allowed in a case: {prose}")
    unknown = sorted(set(raw) - _CASE_FIELDS)
    if unknown:
        raise ExportError(f"unknown case field(s): {unknown}")
    origin = _origin(raw.get("origin"), str(raw.get("case_key") or raw.get("key") or "<case>"), root)
    case_key = raw.get("case_key") or raw.get("key")
    if not case_key:
        safe = re.sub(r"[^A-Za-z0-9._/-]+", "-", origin.node_id).strip("-")
        case_key = f"{origin.kind}/{safe}"
    if not isinstance(case_key, str) or not case_key.strip():
        raise ExportError("case_key must be a non-empty string")
    fighters = raw.get("fighters")
    if not isinstance(fighters, Mapping) or set(fighters) != {"first", "second"}:
        raise ExportError(f"{case_key}: fighters must declare first and second")
    context = raw.get("context") if "context" in raw else raw.get("duel_context")
    if "context" in raw and "duel_context" in raw:
        raise ExportError(f"{case_key}: declare context or duel_context, not both")
    if raw.get("dice") is not None and raw.get("rolls") is not None:
        raise ExportError(f"{case_key}: declare dice or rolls, not both")
    if raw.get("expectations") is not None and any(name in raw for name in _EXPECTATION_FIELDS):
        raise ExportError(f"{case_key}: expectations cannot be combined with expect_* channels")
    limits = dict(raw.get("limits") or {})
    unknown_limits = sorted(set(limits) - {"simulations", "seed", "batch_size", "maximum_rounds"})
    if unknown_limits:
        raise ExportError(f"{case_key}: unknown limit(s): {unknown_limits}")
    limits.setdefault("maximum_rounds", raw.get("maximum_rounds", 1))
    limits.setdefault("simulations", 1)
    limits.setdefault("seed", 0)
    limits.setdefault("batch_size", 100_000)
    if "maximum_rounds" in raw and "maximum_rounds" in (raw.get("limits") or {}):
        raise ExportError(f"{case_key}: maximum_rounds declared twice")
    if raw.get("expectations") is not None:
        expectations = _expectations(raw["expectations"], case_key)
    else:
        expectations = {
            name: raw[name] for name in _EXPECTATION_FIELDS if name in raw
        } or None
    auxiliary = raw.get("auxiliary_participants", ())
    if not isinstance(auxiliary, (tuple, list)):
        raise ExportError(f"{case_key}: auxiliary_participants must be a sequence")
    rolls = raw.get("dice")
    if rolls is None:
        rolls = raw.get("rolls", ())
    decisions = raw.get("decisions")
    if decisions is None:
        decisions = ()
    return codec.CompiledCase(
        case_key=case_key,
        origin=origin,
        first=_fighter(fighters["first"], case_key, "fighters.first", root, kb_root),
        second=_fighter(fighters["second"], case_key, "fighters.second", root, kb_root),
        context=_context(context, case_key, root, kb_root),
        auxiliary_participants=tuple(
            _participant(entry, case_key, f"auxiliary_participants[{index}]", root, kb_root)
            for index, entry in enumerate(auxiliary)
        ),
        initial_state=raw.get("initial_state") or {"first": {}, "second": {}},
        dice=_rolls(rolls, case_key),
        decisions=_decisions(decisions, case_key),
        limits=codec.CaseLimits(**limits),
        benchmark=raw.get("benchmark"),
        expectations=expectations,
    )


def _source_files(raw, root: Path) -> list[dict]:
    result = []
    for index, entry in enumerate(raw or ()):
        if isinstance(entry, str):
            path, digest = entry, None
        elif isinstance(entry, Mapping):
            unknown = sorted(set(entry) - {"path", "sha256"})
            if unknown:
                raise ExportError(f"source file {index} has unknown field(s): {unknown}")
            path, digest = entry.get("path"), entry.get("sha256")
        else:
            raise ExportError(f"source file {index} must be a path or a mapping")
        if not isinstance(path, str) or not path.strip():
            raise ExportError(f"source file {index} needs a non-empty path")
        if digest is None:
            source = root / path
            if not source.is_file():
                raise ExportError(f"source file does not exist: {path}")
            digest = _sha256_bytes(source.read_bytes())
        result.append({"path": path, "sha256": digest})
    return result


def export_cases(specs, *, kb_root, destination) -> ExportReceipt:
    """Compile explicit case inputs and write the canonical corpus document."""
    root = _repository_root(Path(kb_root))
    if isinstance(specs, Mapping):
        if "cases" not in specs:
            raise ExportError("a case plan mapping must declare 'cases'")
        raw_cases = specs["cases"]
        revision = specs.get("revision") or os.environ.get("MORDHEIM_EXPORT_REVISION")
        files = specs.get("files")
    else:
        raw_cases = specs
        revision = os.environ.get("MORDHEIM_EXPORT_REVISION")
        files = None
    cases = [_case(raw, root, Path(kb_root)) for raw in raw_cases]
    keys = [case.case_key for case in cases]
    if len(keys) != len(set(keys)):
        raise ExportError("duplicate case_key")
    if not revision:
        revision = "unversioned"
    document = codec.encode_document(
        cases,
        source={
            "revision": revision,
            "kb_root": _relative(Path(kb_root), root),
            "files": _source_files(files, root),
        },
        generator=GENERATOR,
    )
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = codec.canonical_json(document).encode("utf-8")
    target.write_bytes(payload)
    encoded = {case["case_key"]: case for case in document["cases"]}
    return ExportReceipt(
        path=str(target),
        case_count=len(cases),
        case_hashes={
            key: encoded[key]["fingerprints"]["case_sha256"] for key in sorted(encoded)
        },
        corpus_sha256=document["fingerprints"]["corpus_sha256"],
    )

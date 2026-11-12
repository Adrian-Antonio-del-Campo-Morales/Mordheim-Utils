"""Parity deliveries: their index, validation and admission.

A parity delivery (``mordheim-parity-delivery/v2``) freezes the combat
configuration of one rules-conformance scenario (``tests/conformance/cases``)
so the engines can be compared on it statistically, with random dice instead
of the scenario's scripted ones.  Its key is ``delivery/<audit_id>/<id>``; its
``case.origin.kind`` is ``conformance``, the corpus it was derived from.

This module indexes ``tests/engines/parity/deliveries``, validates each
delivery's identity and freshness against the current conformance YAML, and
decides whether the parity runner can execute it.  Editing a conformance
scenario therefore makes its delivery ``stale`` until it is re-translated.

It is a catalogue, not an engine: ``tools.verification.parity_catalog``
resolves ``--scenarios`` through it, and the comparison itself belongs to
``mordheim_combat_lab.verification.parity``.  It never compiles fighters,
never replays the conformance dice script and never reads the scenario's
expectations, so a translated delivery is never proof of engine compatibility.

``admit`` returns one of:

``admitted``           the frozen inputs can be executed as they stand.
``blocked`` /
``not-applicable``     the delivery itself declares it is not a scenario;
                       the reason is preserved.
``incompatible``       a frozen input the runner cannot express (an initial
                       state, auxiliary participants, a scripted script), or
                       decision-policy defaults that do not correspond.
``stale`` / ``invalid`` the delivery no longer matches its source, or is
                       malformed.
``policy-unverified``  the decision-policy probe raised, so correspondence is
                       unknown.

Combats run to ``CAMPAIGN_MAXIMUM_ROUNDS`` rounds, independently of the
original scenario's horizon.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Iterable, Mapping, Sequence

#: Statuses a delivery can declare about itself.
ENTRY_OUTCOMES = {"blocked": "blocked", "not-applicable": "not-applicable"}

DELIVERY_SCHEMA = "mordheim-parity-delivery/v2"
#: Every delivery key starts with this prefix: ``delivery/<audit_id>/<id>``.
KEY_PREFIX = "delivery/"
#: ``case.origin.kind`` of a delivery: the corpus its configuration came from.
ORIGIN_KIND = "conformance"
CAMPAIGN_MAXIMUM_ROUNDS = 50
DELIVERY_FIELDS = frozenset({
    "schema", "status", "source", "case_key", "case", "decision_policy",
    "magnitudes", "reason",
})
SOURCE_FIELDS = frozenset({"revision", "path", "sha256", "test_id"})
DELIVERY_STATUSES = ("translated", "blocked", "not-applicable")

#: Magnitudes the shared observed runner can compare, in its own vocabulary.

#: Outcomes that make a run fail (a declared non-scenario does not).
#: Declared non-scenarios: a selection made only of these compares nothing and
#: still succeeds.
#: Runner messages (``_runner._native_engine``) meaning the requested native
#: backend cannot run at all, as opposed to rejecting one duel plan.
#: Admission states whose outcome name is more explicit in the report.


class SelectionError(ValueError):
    """No cases were named, or a named case does not exist."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def deliveries_directory(root: Path | None = None) -> Path:
    return (root or repository_root()) / "tests" / "engines" / "parity" / "deliveries"


def case_filename(case_key: str) -> str:
    return hashlib.sha256(case_key.encode("utf-8")).hexdigest() + ".json"


def head_revision(root: Path | None = None) -> str | None:
    return _source_revision(root or repository_root())["commit"]


def _source_revision(root: Path) -> dict:
    """Commit/branch/dirty state of ``root`` via the shared provenance helper."""
    bootstrap_paths(repository_root())
    from mordheim_combat_lab.provenance import source_revision

    return source_revision(root)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class Delivery:
    """One discovered delivery file (not yet validated)."""

    path: Path
    document: Mapping
    case_key: str
    test_id: str
    status: str
    case: object | None = None
    defects: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    stale: bool = False

    def with_validation(self, validation: "Validation") -> "Delivery":
        return Delivery(
            path=self.path, document=self.document, case_key=self.case_key,
            test_id=self.test_id, status=self.status, case=validation.case,
            defects=validation.defects, warnings=validation.warnings,
            stale=validation.stale,
        )


@dataclass(frozen=True)
class Validation:
    defects: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    stale: bool = False
    case: object | None = None


@dataclass(frozen=True)
class Admission:
    state: str  # admitted | invalid | stale | blocked | not-applicable | incompatible
    detail: str = ""
    case: object | None = None


def discover(directory: Path | None = None) -> tuple[dict[str, Delivery], list[str]]:
    """Index deliveries by ``case_key``; unreadable files become defects."""
    directory = directory or deliveries_directory()
    index: dict[str, Delivery] = {}
    defects: list[str] = []
    for path in sorted(directory.glob("*.json")):
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            defects.append(f"{path.name}: unreadable JSON: {error}")
            continue
        if not isinstance(document, dict):
            defects.append(f"{path.name}: delivery is not an object")
            continue
        key = document.get("case_key")
        source = document.get("source")
        test_id = source.get("test_id") if isinstance(source, dict) else None
        status = document.get("status")
        if not isinstance(key, str) or not key:
            defects.append(f"{path.name}: missing case_key")
            continue
        if key in index:
            defects.append(
                f"{path.name}: duplicate case_key {key!r} also in "
                f"{index[key].path.name}"
            )
            continue
        if not isinstance(test_id, str) or not isinstance(status, str):
            defects.append(f"{path.name}: missing source.test_id or status")
            continue
        index[key] = Delivery(
            path=path, document=document, case_key=key, test_id=test_id,
            status=status,
        )
    return index, defects


def resolve(index: Mapping[str, Delivery], identifier: str) -> Delivery | None:
    """Resolve an explicit ``case_key`` or ``audit_id::id`` identifier."""
    direct = index.get(identifier)
    if direct is not None:
        return direct
    for delivery in index.values():
        if delivery.test_id == identifier:
            return delivery
    return None


def select(index: Mapping[str, Delivery], identifiers: Iterable[str]) -> list[Delivery]:
    """Resolve every explicitly requested identifier; never widen the set."""
    wanted = list(dict.fromkeys(identifiers))
    if not wanted:
        raise SelectionError(
            "no delivery selected: name a delivery/<audit_id>/<id> key or an "
            "<audit_id>::<id> scenario id (--scenarios deliveries selects them "
            "all); select() never sweeps the delivery directory by itself"
        )
    missing = [item for item in wanted if resolve(index, item) is None]
    if missing:
        raise SelectionError(
            "unknown case identifier(s): " + ", ".join(repr(item) for item in missing)
        )
    selected: list[Delivery] = []
    seen: set[str] = set()
    for identifier in wanted:
        delivery = resolve(index, identifier)
        if delivery.case_key in seen:
            continue
        seen.add(delivery.case_key)
        selected.append(delivery)
    return selected


def validate(
    delivery: Delivery, root: Path | None = None, *,
    head: str | None = None, require_head: bool = False,
) -> Validation:
    """Validate one delivery against the contract and the current checkout."""
    root = root or repository_root()
    document = delivery.document
    defects: list[str] = []
    warnings: list[str] = []
    stale = False

    if set(document) != DELIVERY_FIELDS:
        defects.append(f"field set is {sorted(document)}")
    if document.get("schema") != DELIVERY_SCHEMA:
        defects.append(f"schema is {document.get('schema')!r}")

    key = delivery.case_key
    if delivery.path.name != case_filename(key):
        defects.append(f"filename is not sha256(case_key).json: {delivery.path.name}")

    source = document.get("source")
    if not isinstance(source, dict) or set(source) != SOURCE_FIELDS:
        defects.append("source must declare exactly revision/path/sha256/test_id")
        return Validation(tuple(defects), tuple(warnings), stale)
    test_id = source.get("test_id")
    if not isinstance(test_id, str) or "::" not in test_id:
        defects.append("source.test_id is not <audit_id>::<id>")
    elif key != KEY_PREFIX + test_id.replace("::", "/", 1):
        defects.append(f"case_key {key!r} does not match test_id {test_id!r}")

    yaml_path = root / str(source.get("path"))
    if not yaml_path.is_file():
        defects.append(f"source YAML does not exist: {source.get('path')}")
    else:
        current = _sha256(yaml_path)
        if current != source.get("sha256"):
            stale = True
            defects.append(
                f"stale source: YAML sha256 is {current}, delivery records "
                f"{source.get('sha256')}"
            )

    revision = source.get("revision")
    if not isinstance(revision, str) or len(revision) != 40:
        defects.append("source.revision is not a 40-character revision")
    elif head is not None and revision != head:
        message = f"source revision {revision} differs from HEAD {head}"
        if require_head:
            defects.append(message)
        else:
            warnings.append(message)

    status = document.get("status")
    if status not in DELIVERY_STATUSES:
        defects.append(f"unknown status {status!r}")
        return Validation(tuple(defects), tuple(warnings), stale)

    if status != "translated":
        if document.get("case") is not None:
            defects.append("a non-translated delivery must carry case = null")
        if document.get("decision_policy") is not None:
            defects.append("a non-translated delivery must carry decision_policy = null")
        if not isinstance(document.get("reason"), str) or not document["reason"].strip():
            defects.append("a non-translated delivery needs a nonempty reason")
        return Validation(tuple(defects), tuple(warnings), stale)

    if document.get("decision_policy") != {"kind": "engine-default"}:
        defects.append("a translated delivery must use the engine-default policy")
    if document.get("reason") is not None:
        defects.append("a translated delivery must carry reason = null")
    if document.get("magnitudes") != ["winner"]:
        defects.append(
            "the delivery contract declares magnitudes ['winner']; widen a "
            "campaign through execute(magnitudes=...) instead of rewriting deliveries"
        )
    encoded = document.get("case")
    if not isinstance(encoded, dict):
        defects.append("a translated delivery must carry the encoded case")
        return Validation(tuple(defects), tuple(warnings), stale)

    bootstrap_paths(root)
    from tools.verification.compiled_cases import decode_case, encode_case

    try:
        case = decode_case(encoded, key)
    except Exception as error:  # CompiledCaseError and shape errors alike
        defects.append(f"case does not decode: {error}")
        return Validation(tuple(defects), tuple(warnings), stale)
    if encode_case(case) != encoded:
        defects.append("case codec round-trip differs")
    if case.case_key != key:
        defects.append("case.case_key differs from delivery.case_key")
    if (
        case.origin.kind != ORIGIN_KIND
        or case.origin.node_id != test_id
        or case.origin.path != source.get("path")
        or case.origin.sha256 != source.get("sha256")
    ):
        defects.append("case.origin does not match the delivery source")
    if case.dice or case.decisions:
        defects.append("case.determinism must be empty (no prescribed dice/decisions)")
    if case.expectations is not None:
        defects.append("case.expectations must be null")
    if case.benchmark is not None:
        defects.append("case.benchmark must be null")
    if (
        case.limits.simulations is not None
        or case.limits.seed is not None
        or case.limits.batch_size is not None
    ):
        defects.append("case.limits must declare only maximum_rounds")
    return Validation(tuple(defects), tuple(warnings), stale, case)


def expressiveness(case) -> list[str]:
    """Name every frozen input the shared parity runner cannot express."""
    limits: list[str] = []
    state = dict(getattr(case, "initial_state", {}) or {})
    pending = [
        f"initial_state.{side}.{name}={value!r}"
        for side in ("first", "second")
        for name, value in (state.get(side) or {}).items()
    ]
    if pending:
        shown = ", ".join(pending[:3])
        more = "" if len(pending) <= 3 else f" (+{len(pending) - 3} more)"
        limits.append(
            "initial_state overrides are not expressible: the shared parity "
            f"runner has no initial-state channel ({shown}{more})"
        )
    auxiliary = tuple(getattr(case, "auxiliary_participants", ()) or ())
    if auxiliary:
        limits.append(
            f"auxiliary_participants are not expressible ({len(auxiliary)} entries)"
        )
    if getattr(case, "dice", ()):
        limits.append("determinism.dice is not empty; the conformance replay is not used")
    if getattr(case, "decisions", ()):
        limits.append("determinism.decisions is not empty; the conformance script is not used")
    return limits


def decision_policy_evidence() -> dict:
    """Probe both engines' defaults; ``engine-default`` is not assumed equal.

    ``probe_failed`` separates a probe that raised (engine API drift: the
    correspondence is unknown) from a measured disagreement.  ``execute`` fails
    the run in both cases, because no translated case can be compared.
    """
    keys = (
        "round.0.first.vomit-attack",
        "round.0.first.attack.0.lotus-critical",
        "round.0.second.fear.charged.leader.leader",
    )
    try:
        from mordheim_combat.vectorized._driver import _choose
        from mordheim_core.dice import AlwaysAccept

        modular = {key: AlwaysAccept().choose(key) for key in keys}
        candidate = {key: _choose(None, key, None) for key in keys}
    except Exception as error:  # engine API drift: recorded, then fails the run
        return {
            "kind": "engine-default",
            "probes": keys,
            "corresponds": False,
            "probe_failed": True,
            "detail": (
                "decision-policy probe failed: "
                f"{type(error).__name__}: {error}"
            ),
        }
    corresponds = all(value is True for value in modular.values()) and all(
        value is True for value in candidate.values()
    )
    return {
        "kind": "engine-default",
        "modular_default": "AlwaysAccept",
        "candidate_default": "None -> _choose returns True",
        "probes": keys,
        "modular": modular,
        "candidate": candidate,
        "corresponds": corresponds,
        "probe_failed": False,
        "detail": (
            "both defaults accept every probed optional decision"
            if corresponds else
            "default decision policies disagree; frozen scenarios cannot be compared"
        ),
    }


def admit(
    delivery: Delivery, *, policy_corresponds: bool = True,
    policy_probe_failed: bool = False,
) -> Admission:
    """Decide whether the shared runner can execute this delivery.

    ``policy_probe_failed`` marks a decision-policy probe that raised: the
    case is then ``policy-unverified`` (reported as ``execution-failure``), not
    an honest incompatibility.
    """
    if delivery.defects:
        if delivery.stale:
            return Admission("stale", "; ".join(delivery.defects))
        return Admission("invalid", "; ".join(delivery.defects))
    if delivery.status in ENTRY_OUTCOMES:
        detail = str(delivery.document.get("reason") or "")
        return Admission(ENTRY_OUTCOMES[delivery.status], detail)
    if delivery.case is None:
        return Admission("invalid", "translated delivery has no decoded case")
    if policy_probe_failed:
        return Admission(
            "policy-unverified",
            "decision_policy: the engine-default probe failed; correspondence unknown",
        )
    if not policy_corresponds:
        return Admission(
            "incompatible",
            "decision_policy: engine-default defaults do not correspond between engines",
        )
    limits = expressiveness(delivery.case)
    if limits:
        return Admission("incompatible", "; ".join(limits))
    return Admission("admitted", "engine-default", delivery.case)


def build_parity_case(admission: Admission, *, simulations: int, seed: int,
                      magnitudes: Sequence[str]):
    from mordheim_combat_lab.verification.parity import ParityCase

    case = admission.case
    return ParityCase(
        label=case.case_key,
        first=case.first,
        second=case.second,
        maximum_rounds=CAMPAIGN_MAXIMUM_ROUNDS,
        simulations=simulations,
        seed=seed,
        magnitudes=tuple(magnitudes),
        context=case.context,
    )


def bootstrap_paths(root: Path) -> None:
    """Put this checkout's packages first on ``sys.path``.

    Call it before any engine module is imported: a module the process already
    holds keeps its old origin, while process-pool workers re-import from the
    reordered path, so a late call can split the parent and its workers across
    two copies of the engine.
    """
    for relative in (
        ".", "packages/python/core", "packages/python/combat-engine",
        "packages/python/knowledge", "packages/python/roster-construction",
        "apps/combat-lab",
    ):
        entry = str(root / relative)
        if entry not in sys.path:
            sys.path.insert(0, entry)



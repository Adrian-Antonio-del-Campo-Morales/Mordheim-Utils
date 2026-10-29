"""The single E2E precompiled statistical-parity connection.

Selects individual ``mordheim-e2e-statistical-delivery/v1`` deliveries by
explicit identifier, validates their identity and freshness against the current
E2E YAML, and executes the frozen inputs through the existing parity runner.

This module is a connection, not a second engine: it reuses
``mordheim_combat_lab.verification.parity`` for sampling and the six-sigma gate,
``tools.verification.compiled_cases`` for the frozen codec, and the runner's
observed surface so the duel context is preserved.  It never compiles fighters,
never replays the E2E dice script, never reads expectations, and never treats a
translated delivery as proof of engine compatibility.

Observables are an execution decision: deliveries declare ``["winner"]`` (the
delivery contract's minimum), while a campaign may ask the same frozen inputs
for ``wounds`` and ``condition``.  Those names are the runner's own magnitudes;
no new statistical criterion is introduced here.

Outcome vocabulary (per case, after aggregation across candidate backends):

``approved``           the sample passed the six-sigma gate on every compared
                       magnitude and backend; a sample, not a certificate.
``divergence``         a measured statistical difference.
``reference-failure``  the modular oracle could not produce a sample.
``candidate-failure``  the candidate engine raised; the cause is preserved and
                       it is never reported as a measured divergence.
``execution-failure``  the runner could not execute/compare (malformed batch,
                       non-deterministic batch, unmapped outcome code…).
``incompatible``       a frozen input or the engine could not express the case.
``blocked`` / ``not-applicable``  the delivery itself declares no scenario.
``invalid-delivery`` / ``stale-delivery``  the file breaks the contract or its
                       source YAML changed since it was produced.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping, Sequence

SCHEMA = "mordheim-e2e-parity-connection/v1"
DELIVERY_SCHEMA = "mordheim-e2e-statistical-delivery/v1"
DELIVERY_FIELDS = frozenset({
    "schema", "status", "source", "case_key", "case", "decision_policy",
    "magnitudes", "reason",
})
SOURCE_FIELDS = frozenset({"revision", "path", "sha256", "test_id"})
DELIVERY_STATUSES = ("translated", "blocked", "not-applicable")

#: Magnitudes the shared observed runner can compare, in its own vocabulary.
MAGNITUDES = ("winner", "wounds", "condition", "rounds")
#: Campaign default: winner plus both final wounds and both final conditions.
DEFAULT_MAGNITUDES = ("winner", "wounds", "condition")

#: Outcomes that make a run fail (a declared non-scenario does not).
FAILING_OUTCOMES = frozenset({
    "invalid-delivery", "stale-delivery", "reference-failure",
    "candidate-failure", "execution-failure", "divergence",
})
ENTRY_OUTCOMES = {"blocked": "blocked", "not-applicable": "not-applicable"}
#: Admission states whose outcome name is more explicit in the report.
ADMISSION_OUTCOMES = {
    "invalid": "invalid-delivery",
    "stale": "stale-delivery",
    "blocked": "blocked",
    "not-applicable": "not-applicable",
    "incompatible": "incompatible",
}


class SelectionError(ValueError):
    """No cases were named, or a named case does not exist."""


class MagnitudeError(ValueError):
    """A requested magnitude is not one the shared runner compares."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def deliveries_directory(root: Path | None = None) -> Path:
    return (root or repository_root()) / "tests" / "engines" / "fixtures" / "e2e-statistical-deliveries"


def case_filename(case_key: str) -> str:
    return hashlib.sha256(case_key.encode("utf-8")).hexdigest() + ".json"


def head_revision(root: Path | None = None) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, cwd=str(root or repository_root()),
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def branch_name(root: Path | None = None) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True,
            cwd=str(root or repository_root()),
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_magnitudes(value: str | None) -> tuple[str, ...]:
    """Parse a comma-separated magnitude list; ``winner`` is mandatory."""
    if value is None:
        return DEFAULT_MAGNITUDES
    items = tuple(dict.fromkeys(
        part.strip() for part in value.split(",") if part.strip()
    ))
    if not items:
        raise MagnitudeError("no magnitude selected")
    unknown = [item for item in items if item not in MAGNITUDES]
    if unknown:
        raise MagnitudeError(
            "unknown magnitude(s) " + ", ".join(unknown)
            + f"; the shared runner compares {', '.join(MAGNITUDES)}"
        )
    if "winner" not in items:
        raise MagnitudeError(
            "winner is mandatory: the shared observed gate always compares it"
        )
    return items


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


@dataclass
class CaseResult:
    case_key: str
    test_id: str
    outcome: str
    detail: str = ""
    delivery_status: str | None = None
    delivery_file: str | None = None
    stages: dict = field(default_factory=dict)
    engines: tuple[dict, ...] = ()
    limitations: tuple[str, ...] = ()


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
            "no case selected: pass --e2e <case_key|audit_id::id> "
            "(or --e2e-selection-file); this connection never sweeps the "
            "delivery directory"
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
    elif key != "e2e/" + test_id.replace("::", "/", 1):
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
            "the delivery contract declares magnitudes ['winner']; widen the "
            "campaign with --magnitudes instead of rewriting deliveries"
        )
    encoded = document.get("case")
    if not isinstance(encoded, dict):
        defects.append("a translated delivery must carry the encoded case")
        return Validation(tuple(defects), tuple(warnings), stale)

    _bootstrap_paths(root)
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
        case.origin.kind != "e2e"
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
        limits.append("determinism.dice is not empty; the E2E replay is not used")
    if getattr(case, "decisions", ()):
        limits.append("determinism.decisions is not empty; the E2E script is not used")
    return limits


def decision_policy_evidence() -> dict:
    """Probe both engines' defaults; ``engine-default`` is not assumed equal."""
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
    except Exception as error:  # engine API drift is an incompatibility, not a crash
        return {
            "kind": "engine-default",
            "probes": keys,
            "corresponds": False,
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
        "detail": (
            "both defaults accept every probed optional decision"
            if corresponds else
            "default decision policies disagree; frozen scenarios cannot be compared"
        ),
    }


def admit(
    delivery: Delivery, *, policy_corresponds: bool = True,
) -> Admission:
    """Decide whether the shared runner can execute this delivery."""
    if delivery.defects:
        if delivery.stale:
            return Admission("stale", "; ".join(delivery.defects))
        return Admission("invalid", "; ".join(delivery.defects))
    if delivery.status in ENTRY_OUTCOMES:
        detail = str(delivery.document.get("reason") or "")
        return Admission(ENTRY_OUTCOMES[delivery.status], detail)
    if delivery.case is None:
        return Admission("invalid", "translated delivery has no decoded case")
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
        maximum_rounds=case.limits.maximum_rounds,
        simulations=simulations,
        seed=seed,
        magnitudes=tuple(magnitudes),
        context=case.context,
    )


def _engine_name(row) -> str:
    return str(row.backend)


def classify_row(row) -> tuple[str, str]:
    """Map one runner row onto the outcome vocabulary without conflating causes.

    The runner reports a candidate exception as ``DIVERGENCE`` so the row is not
    lost; here it becomes ``candidate-failure`` with the cause preserved.  A
    measured statistical difference stays ``divergence``.
    """
    detail = str(getattr(row, "detail", "") or "")
    status = str(getattr(row, "status", ""))
    if status == "PASS":
        return "approved", ""
    if status == "ERROR":
        return "reference-failure", detail
    if status == "INCOMPATIBLE":
        return "incompatible", detail
    if status == "DIVERGENCE":
        if detail.startswith("DIVERGENCE:exception:"):
            return "candidate-failure", detail
        if (detail.startswith("DIVERGENCE:batch-shape")
                or detail.startswith("DIVERGENCE:batch-nondeterministic")):
            return "execution-failure", detail
        return "divergence", detail
    # NOT_RUN: separate "the engine cannot express this" from "we failed".
    if detail.startswith(("NOT_RUN:native-plan", "NOT_RUN:decision-script")):
        return "incompatible", detail
    return "execution-failure", detail


def aggregate(outcomes: Sequence[str]) -> str:
    """Aggregate per-backend outcomes for one case."""
    for name in ("reference-failure", "candidate-failure", "execution-failure",
                 "divergence"):
        if name in outcomes:
            return name
    if outcomes and all(item == "approved" for item in outcomes):
        return "approved"
    return "incompatible"


def _comparisons(row) -> list[dict]:
    return [{
        "magnitude": item.magnitude,
        "modular_rates": list(item.modular_rates),
        "candidate_rates": list(item.candidate_rates),
        "tolerances": list(item.tolerances),
        "passed": item.passed,
        "detail": item.detail,
    } for item in row.comparisons]


def execute(
    identifiers: Sequence[str], *,
    simulations: int,
    seed: int = 2026,
    backend: str = "numpy",
    workers: int | str | None = 1,
    magnitudes: Sequence[str] = DEFAULT_MAGNITUDES,
    require_head: bool = False,
    deliveries: Path | None = None,
) -> tuple[dict, int]:
    """Validate, admit and sample the explicitly selected deliveries.

    Returns ``(payload, exit_code)``.  Failing outcomes make the exit code 1;
    declared non-scenarios (blocked / not-applicable) and honest
    incompatibilities are counted but do not fail the run.
    """
    root = repository_root()
    _bootstrap_paths(root)
    if simulations < 1:
        raise ValueError("simulations must be at least one")
    if backend not in {"numpy", "native", "all"}:
        raise ValueError(f"unsupported candidate backend {backend!r}")
    requested = ("numpy", "native") if backend == "all" else (backend,)
    magnitudes = tuple(magnitudes)
    if "winner" not in magnitudes:
        raise MagnitudeError("winner is mandatory")

    directory = deliveries or deliveries_directory(root)
    index, discovery_defects = discover(directory)
    selected = select(index, identifiers)
    head = head_revision(root)
    policy = decision_policy_evidence()

    results: list[CaseResult] = []
    prepared = []
    warnings: list[str] = []
    for delivery in selected:
        validation = validate(delivery, root, head=head, require_head=require_head)
        warnings.extend(f"{delivery.path.name}: {note}" for note in validation.warnings)
        delivery = delivery.with_validation(validation)
        admission = admit(delivery, policy_corresponds=policy["corresponds"])
        if admission.state == "admitted":
            parity_case = build_parity_case(
                admission, simulations=simulations, seed=seed, magnitudes=magnitudes,
            )
            prepared.append((delivery, parity_case))
            continue
        results.append(CaseResult(
            case_key=delivery.case_key,
            test_id=delivery.test_id,
            outcome=ADMISSION_OUTCOMES.get(admission.state, admission.state),
            detail=admission.detail,
            delivery_status=delivery.status,
            delivery_file=delivery.path.name,
            stages={"loaded": True, "admitted": False},
            limitations=tuple(expressiveness(delivery.case)) if delivery.case else (),
        ))

    rows_by_case: dict[str, list] = {}
    if prepared:
        from mordheim_combat_lab.verification.parity import run_parity

        run = run_parity(
            [case for _, case in prepared],
            backends=requested,
            candidate="observed",
            workers=workers,
            seed=seed,
        )
        for row in run.rows:
            rows_by_case.setdefault(row.case, []).append(row)

    for delivery, parity_case in prepared:
        rows = rows_by_case.get(parity_case.label, [])
        if not rows:
            results.append(CaseResult(
                case_key=delivery.case_key, test_id=delivery.test_id,
                outcome="execution-failure", detail="the runner produced no row",
                delivery_status=delivery.status, delivery_file=delivery.path.name,
                stages={"loaded": True, "admitted": True},
            ))
            continue
        engine_records = []
        classified = []
        for row in rows:
            outcome, detail = classify_row(row)
            classified.append(outcome)
            engine_records.append({
                "engine": _engine_name(row),
                "status": row.status,
                "outcome": outcome,
                "executed": bool(row.executed),
                "compared": bool(row.compared),
                "approved": bool(row.approved),
                "detail": detail,
                "comparisons": _comparisons(row),
                "modular_seconds": round(row.modular_seconds, 6),
                "candidate_seconds": round(row.candidate_seconds, 6),
            })
        outcome = aggregate(classified)
        detail = "; ".join(
            f"{record['engine']}: {record['detail']}"
            for record in engine_records if record["detail"]
        )
        reference_sampled = any(record["modular_seconds"] > 0.0 for record in engine_records)
        results.append(CaseResult(
            case_key=delivery.case_key,
            test_id=delivery.test_id,
            outcome=outcome,
            detail=detail,
            delivery_status=delivery.status,
            delivery_file=delivery.path.name,
            stages={
                "loaded": True,
                "admitted": True,
                "reference_sampled": reference_sampled,
                "candidate_sampled": any(record["executed"] for record in engine_records),
                "compared": any(record["compared"] for record in engine_records),
                "approved": outcome == "approved",
            },
            engines=tuple(engine_records),
        ))

    summary = _summary(results, len(selected))
    payload = {
        "schema": SCHEMA,
        "connection": "e2e-precompiled",
        "repository": {
            "root": str(root), "revision": head, "branch": branch_name(root),
        },
        "deliveries": str(directory),
        "selection": [delivery.case_key for delivery in selected],
        "options": {
            "simulations": simulations,
            "seed": seed,
            "backend": backend,
            "workers": workers if isinstance(workers, str) else workers,
            "magnitudes": list(magnitudes),
            "require_head": require_head,
        },
        "checks": {
            "decision_policy": policy,
            "discovery_defects": discovery_defects,
            "delivery_warnings": warnings,
        },
        "summary": summary,
        "certifies_parity": False,
        "sample_only": True,
        "results": [_result_payload(item) for item in results],
    }
    exit_code = 1 if any(
        item.outcome in FAILING_OUTCOMES for item in results
    ) else 0
    return payload, exit_code


def report_markdown(payload: dict) -> str:
    """Render the saved E2E result without sampling either engine."""
    from collections import Counter

    def cell(value):
        return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(
            ">", "&gt;").replace("|", "&#124;").replace("\n", "<br>")

    options = payload.get("options", {})
    repository = payload.get("repository", {})
    lines = ["# Paridad estadística E2E", "",
             f"Rama: {cell(repository.get('branch', ''))}. "
             f"Revisión: {cell(repository.get('revision', ''))}.", "",
             f"Candidato: {cell(options.get('backend', ''))}. "
             f"Simulaciones por motor y caso: {cell(options.get('simulations', ''))}. "
             f"Semilla: {cell(options.get('seed', ''))}.", "",
             "Magnitudes: " + cell(", ".join(options.get("magnitudes", []))) + ".", "",
             "Este informe recoge la ejecución; no certifica por sí solo la paridad "
             "del conjunto. Las muestras pequeñas sirven para comprobar la conexión.",
             "", "## Resumen", "", "| Indicador | Cantidad |", "|---|---:|"]
    lines.extend(f"| {cell(key)} | {cell(value)} |"
                 for key, value in payload.get("summary", {}).items())
    results = payload.get("results", [])
    attention = [item for item in results if item["outcome"] not in
                 {"approved", "incompatible", "blocked", "not-applicable"}]
    lines += ["", "## Divergencias y errores", ""]
    if attention:
        lines += ["| Caso | Estado | Motivo |", "|---|---|---|"]
        lines.extend(f"| {cell(item['case_key'])} | {cell(item['outcome'])} | "
                     f"{cell(item.get('detail', ''))} |" for item in attention)
    else:
        lines.append("Sin divergencias ni errores registrados.")
    for outcome in ("incompatible", "blocked", "not-applicable"):
        reasons = Counter(item.get("detail") or "Sin motivo informado"
                          for item in results if item["outcome"] == outcome)
        if reasons:
            lines += ["", f"## {outcome}: motivos", "",
                      "| Cantidad | Motivo |", "|---:|---|"]
            lines.extend(f"| {count} | {cell(reason)} |"
                         for reason, count in reasons.most_common())
    for key in ("discovery_defects", "delivery_warnings"):
        notes = payload.get("checks", {}).get(key, [])
        if notes:
            lines += ["", f"## {key}", ""]
            lines.extend(f"- {cell(note)}" for note in notes)
    return "\n".join(lines) + "\n"


def write_reports(payload: dict, *, output: Path | None = None,
                  output_md: Path | None = None) -> None:
    """Write only explicitly requested report formats, without sampling."""
    if output is not None and output_md is not None and output.resolve() == output_md.resolve():
        raise ValueError("JSON and Markdown outputs must use different paths")
    for path, content in (
        (output, lambda: json.dumps(payload, ensure_ascii=True, indent=2) + "\n"),
        (output_md, lambda: report_markdown(payload)),
    ):
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content(), encoding="utf-8")


def _summary(results: Sequence[CaseResult], selected: int) -> dict:
    def count(*outcomes: str) -> int:
        return sum(1 for item in results if item.outcome in outcomes)

    return {
        "selected": selected,
        "translated": sum(
            1 for item in results if item.delivery_status == "translated"
        ),
        "blocked": count("blocked"),
        "not_applicable": count("not-applicable"),
        "invalid_delivery": count("invalid-delivery"),
        "stale_delivery": count("stale-delivery"),
        "incompatible": count("incompatible"),
        "sampled": sum(1 for item in results if item.stages.get("admitted")),
        "executed": sum(
            1 for item in results if item.stages.get("candidate_sampled")
        ),
        "compared": sum(1 for item in results if item.stages.get("compared")),
        "approved": count("approved"),
        "divergent": count("divergence"),
        "reference_failures": count("reference-failure"),
        "candidate_failures": count("candidate-failure"),
        "execution_failures": count("execution-failure"),
        "failed": count("invalid-delivery", "stale-delivery", "reference-failure",
                        "candidate-failure", "execution-failure"),
    }


def _result_payload(result: CaseResult) -> dict:
    return {
        "case_key": result.case_key,
        "test_id": result.test_id,
        "outcome": result.outcome,
        "detail": result.detail,
        "delivery": {
            "file": result.delivery_file,
            "status": result.delivery_status,
        },
        "stages": result.stages,
        "engines": list(result.engines),
        "limitations": list(result.limitations),
    }


def _bootstrap_paths(root: Path) -> None:
    for relative in (
        ".", "packages/python/core", "packages/python/combat-engine",
        "packages/python/knowledge", "packages/python/roster-construction",
        "apps/combat-lab",
    ):
        entry = str(root / relative)
        if entry not in sys.path:
            sys.path.insert(0, entry)


def read_selection_file(path: Path) -> list[str]:
    """One ``case_key`` or ``audit_id::id`` per line; ``#`` comments allowed."""
    identifiers: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            identifiers.append(stripped)
    return identifiers

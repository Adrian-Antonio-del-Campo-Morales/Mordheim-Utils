"""Parity report dataclasses and JSON/Markdown payload builders."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable

ROOT = Path(__file__).resolve().parents[5]

@dataclass(frozen=True, slots=True)
class ParityObligation:
    kind: str
    id: str
    consumer: str
    evidence: str
    verified: bool

@dataclass(frozen=True, slots=True)
class ParityReport:
    complete: bool
    obligations: tuple[ParityObligation, ...]
    verified: tuple[str, ...]
    pending: tuple[str, ...]
    divergences: tuple[str, ...]
    exact_checks: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class StatisticalParityResult:
    scenario: str
    backend: str
    simulations: int
    modular_rates: tuple[float, float, float]
    vectorized_rates: tuple[float, float, float]
    tolerances: tuple[float, float, float]
    passed: bool
    # Wall time of each engine's sample, at engine level: ``reference`` is the
    # modular oracle for statistical/matrix rows and NumPy for cross rows;
    # ``candidate`` is the backend named in ``backend``. Zero when the sample
    # was supplied by the caller without a measurement.
    reference_seconds: float = 0.0
    candidate_seconds: float = 0.0
    # True when the row's deep pair was re-certified at a larger sample after
    # a suspicious first pass (adaptive escalation; statistical and cross
    # rows never carry the flag).
    escalated: bool = False

@dataclass(frozen=True, slots=True)
class SpecificationParityCase:
    specification: str
    case: str
    operation: str
    status: str
    adapter: str
    detail: str = ""

@dataclass(frozen=True, slots=True)
class SpecificationParityReport:
    complete: bool
    cases: tuple[SpecificationParityCase, ...]
    passed: tuple[str, ...]
    pending: tuple[str, ...]
    divergences: tuple[str, ...]
    out_of_scope: tuple[str, ...]

CERTIFICATION_SIMULATIONS = 100_000

def parity_report_payload(
    report: ParityReport,
    statistical: Iterable[StatisticalParityResult] = (),
    specifications: SpecificationParityReport | None = None,
    deep: Iterable[StatisticalParityResult] = (),
    truncations: Iterable[StatisticalParityResult] = (),
    elapsed_seconds: float | None = None,
    deep_pair_set: str | None = None,
    truncation_pair_set: str | None = None,
) -> dict[str, object]:
    """Return a serializable, self-describing parity certificate.

    ``elapsed_seconds`` is the total wall time of the run that produced the
    certificate (measured by the caller around the whole command); ``None``
    when a payload is assembled from already-computed samples. ``deep_pair_set``
    and ``truncation_pair_set`` identify which maintained scenario collection
    produced each optional section.
    """
    samples = tuple(statistical)
    statistical_passed = all(item.passed for item in samples)
    certification = bool(samples) and all(
        item.simulations >= CERTIFICATION_SIMULATIONS for item in samples
    )
    deep_samples = tuple(deep)
    deep_passed = all(item.passed for item in deep_samples)
    truncation_samples = tuple(truncations)
    truncations_passed = all(item.passed for item in truncation_samples)
    return {
        "schema": "mordheim-combat-parity/v2",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed_seconds,
        "oracle": "combat.modular (read-only)",
        "candidate": "combat.vectorized",
        "complete": report.complete and statistical_passed and deep_passed and (
            specifications is None or specifications.complete
        ) and (not truncation_samples or truncations_passed),
        "certification_sample_complete": certification,
        "certification_minimum_simulations_per_engine": CERTIFICATION_SIMULATIONS,
        "deterministic": {
            "passed": not report.pending and not report.divergences,
            "exact_checks": report.exact_checks,
            "verified": report.verified,
            "pending": report.pending,
            "divergences": report.divergences,
            "obligations": tuple({
                "kind": item.kind, "id": item.id, "consumer": item.consumer,
                "evidence": item.evidence, "verified": item.verified,
            } for item in report.obligations),
        },
        "statistical": tuple({
            "scenario": item.scenario,
            "backend": item.backend,
            "simulations_per_engine": item.simulations,
            "modular_rates": item.modular_rates,
            "vectorized_rates": item.vectorized_rates,
            "tolerances": item.tolerances,
            "passed": item.passed,
            "reference_seconds": item.reference_seconds,
            "candidate_seconds": item.candidate_seconds,
        } for item in samples),
        "deep": None if not deep_samples else {
            "pair_set": deep_pair_set or "full",
            "complete": deep_passed,
            "samples": tuple({
                "scenario": item.scenario,
                "backend": item.backend,
                "simulations_per_engine": item.simulations,
                "reference_rates": item.modular_rates,
                "candidate_rates": item.vectorized_rates,
                "tolerances": item.tolerances,
                "passed": item.passed,
                "reference_seconds": item.reference_seconds,
                "candidate_seconds": item.candidate_seconds,
                "escalated": item.escalated,
            } for item in deep_samples),
        },
        "truncations": None if not truncation_samples else {
            "pair_set": truncation_pair_set or "full",
            "complete": truncations_passed,
            "samples": tuple({
                "scenario": item.scenario,
                "backend": item.backend,
                "simulations_per_engine": item.simulations,
                "modular_rates": item.modular_rates,
                "vectorized_rates": item.vectorized_rates,
                "tolerances": item.tolerances,
                "passed": item.passed,
                "reference_seconds": item.reference_seconds,
                "candidate_seconds": item.candidate_seconds,
            } for item in truncation_samples),
        },
        "specifications": None if specifications is None else {
            "complete": specifications.complete,
            "passed": specifications.passed,
            "pending": specifications.pending,
            "divergences": specifications.divergences,
            "out_of_scope": specifications.out_of_scope,
            "cases": tuple({
                "specification": item.specification,
                "case": item.case,
                "operation": item.operation,
                "status": item.status,
                "adapter": item.adapter,
                "detail": item.detail,
            } for item in specifications.cases),
        },
    }

def parity_report_markdown(payload: dict[str, object]) -> str:
    deterministic = payload["deterministic"]
    assert isinstance(deterministic, dict)
    rows = payload["statistical"]
    assert isinstance(rows, tuple)
    lines = [
        "# Vectorized engine parity report",
        "",
        f"- Generated: `{payload['generated_at']}`",
        *([f"- Elapsed: `{payload['elapsed_seconds']:.1f}s`"]
          if isinstance(payload.get("elapsed_seconds"), (int, float))
          else ["- Elapsed: not recorded"]),
        f"- Oracle: `{payload['oracle']}`",
        f"- Candidate: `{payload['candidate']}`",
        f"- Overall pass: `{payload['complete']}`",
        f"- Certification-sized sample: `{payload['certification_sample_complete']}`",
        f"- Deterministic checks: `{len(deterministic['exact_checks'])}`",
        f"- Verified obligations: `{len(deterministic['verified'])}`",
        f"- Pending obligations: `{len(deterministic['pending'])}`",
        f"- Divergences: `{len(deterministic['divergences'])}`",
        "",
        "## Deterministic checks",
        "",
        *[f"- `{name}`" for name in deterministic["exact_checks"]],
    ]
    specifications = payload.get("specifications")
    if isinstance(specifications, dict):
        lines.extend((
            "", "## Semantic specification parity", "",
            f"- PASS: `{len(specifications['passed'])}`",
            f"- PENDING_ADAPTER: `{len(specifications['pending'])}`",
            f"- DIVERGENCE: `{len(specifications['divergences'])}`",
            f"- OUT_OF_SCOPE: `{len(specifications['out_of_scope'])}`",
        ))
    if rows:
        lines.extend((
            "", "## Statistical comparisons", "",
            "| Scenario | Backend | Duels/engine | Modular W/L/U | Candidate W/L/U | Pass | Time (oracle/cand, s) |",
            "|---|---:|---|---|---|---|---|",
        ))
        for row in rows:
            modular = "/".join(f"{100 * value:.3f}%" for value in row["modular_rates"])
            vector = "/".join(f"{100 * value:.3f}%" for value in row["vectorized_rates"])
            lines.append(
                f"| {row['scenario']} | {row['backend']} | "
                f"{row['simulations_per_engine']:,} | "
                f"{modular} | {vector} | {row['passed']} | "
                f"{row['reference_seconds']:.2f} / {row['candidate_seconds']:.2f} |"
            )
    deep = payload.get("deep")
    if isinstance(deep, dict):
        deep_rows = deep["samples"]
        lines.extend((
            "", "## Deep certification samples", "",
            f"- Pair set: `{deep.get('pair_set', 'full')}`",
            "| Scenario | Candidate | Duels/engine | Reference W/L/U | Candidate W/L/U | Pass | Time (ref/cand, s) |",
            "|---|---:|---|---|---|---|---|",
        ))
        for row in deep_rows:
            reference = "/".join(f"{100 * value:.3f}%" for value in row["reference_rates"])
            candidate = "/".join(f"{100 * value:.3f}%" for value in row["candidate_rates"])
            lines.append(
                f"| {row['scenario']} | {row['backend']} | "
                f"{row['simulations_per_engine']:,} | "
                f"{reference} | {candidate} | {row['passed']} | "
                f"{row['reference_seconds']:.2f} / {row['candidate_seconds']:.2f} |"
            )
    truncations = payload.get("truncations")
    if isinstance(truncations, dict):
        lines.extend((
            "", "## Round-truncation parity samples", "",
            f"- Pair set: `{truncations.get('pair_set', 'full')}`",
            "| Horizon | Candidate | Duels/engine | Modular W/L/U | Candidate W/L/U | Pass | Time (oracle/cand, s) |",
            "|---|---:|---|---|---|---|---|",
        ))
        for row in truncations["samples"]:
            modular = "/".join(f"{100 * value:.3f}%" for value in row["modular_rates"])
            candidate = "/".join(f"{100 * value:.3f}%" for value in row["vectorized_rates"])
            lines.append(
                f"| {row['scenario']} | {row['backend']} | "
                f"{row['simulations_per_engine']:,} | "
                f"{modular} | {candidate} | {row['passed']} | "
                f"{row['reference_seconds']:.2f} / {row['candidate_seconds']:.2f} |"
            )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Renewed battery (P03): statistical outcome parity per case, variant and clause
# ---------------------------------------------------------------------------

BATTERY_SCHEMA = "mordheim-combat-parity-battery/v3"

#: Details that mean the battery itself could not compile the scenario, read its
#: decisions, obtain both samples or compare their distributions.  They are own
#: errors: the command fails even without ``--require-complete``.
BATTERY_ERROR_PREFIXES = (
    "NOT_RUN:compile",
    "NOT_RUN:decision-script",
    "NOT_RUN:case-definition",
    "NOT_RUN:context",
    "NOT_RUN:outcome-codes",
    "DIVERGENCE:exception",
    "DIVERGENCE:batch-shape",
    "DIVERGENCE:batch-nondeterministic",
)


def battery_failure_kind(status: str, detail: str) -> str | None:
    """Classify one result as ``"error"``, ``"dependency"`` or ``None``.

    ``error`` means the run itself failed: the harness could not compile the
    scenario, read its decisions, obtain both samples or compare them, or the
    outcome distributions diverged.  ``dependency`` means a declared capability
    is absent: a real input limit the API cannot express (initial state, per-row
    decisions) or a backend that cannot run the case (``NOT_RUN:native-*``).
    A dependency leaves the run partial, never passed.  This is the one
    classification the CLI exit code and the report buckets both use.
    """
    if status == "DIVERGENCE":
        return "error"
    if detail.startswith(BATTERY_ERROR_PREFIXES):
        return "error"
    if status in {"INCOMPATIBLE", "NOT_RUN"}:
        return "dependency"
    return None


def _battery_owner(detail: str) -> str | None:
    """Return the ``owner=`` label of a case detail, when it declares one."""
    marker = "owner="
    index = detail.find(marker)
    if index < 0:
        return None
    tail = detail[index + len(marker):].strip()
    owner = tail.split()[0].rstrip(".,;") if tail else ""
    return owner or None


def _battery_is_dependency(result) -> bool:
    return battery_failure_kind(
        str(result.status), str(getattr(result, "detail", "") or ""),
    ) == "dependency"


def _battery_is_prepared(result) -> bool:
    """A real input limit is a preparation limit, not a prepared scenario."""
    return not getattr(result, "blocked_by", None)


def _battery_counts(results: Iterable) -> dict[str, int]:
    """Count the stages actually reached, not the final status.

    ``compared`` counts performed comparisons; ``approved`` counts the ones
    that stayed within tolerance.  A divergence is therefore compared+divergent
    and never approved, and a case that never obtained both samples is neither.
    """
    rows = tuple(results)
    statuses = [str(row.status) for row in rows]
    kinds = [
        battery_failure_kind(
            str(row.status), str(getattr(row, "detail", "") or ""),
        )
        for row in rows
    ]
    return {
        "cases": len(rows),
        "executed": sum(1 for row in rows if getattr(row, "executed", False)),
        "compared": sum(1 for row in rows if getattr(row, "compared", False)),
        "approved": sum(1 for row in rows if getattr(row, "approved", False)),
        "divergent": statuses.count("DIVERGENCE"),
        "incompatible": statuses.count("INCOMPATIBLE"),
        "not_run": statuses.count("NOT_RUN"),
        "errors": kinds.count("error"),
        "dependencies": kinds.count("dependency"),
    }


def _battery_comparison_row(item) -> dict[str, object]:
    return {
        "magnitude": str(item.magnitude),
        "modular_rates": list(item.modular_rates),
        "candidate_rates": list(item.candidate_rates),
        "tolerances": list(item.tolerances),
        "passed": bool(item.passed),
        "detail": str(getattr(item, "detail", "") or ""),
    }


def _battery_case_row(result) -> dict[str, object]:
    detail = str(getattr(result, "detail", "") or "")
    comparisons = tuple(getattr(result, "comparisons", ()) or ())
    return {
        "case": str(result.case),
        "level": str(getattr(result, "level", "")),
        "variant": str(getattr(result, "variant", "")),
        "obligation": str(getattr(result, "obligation", "")),
        "backend": str(getattr(result, "backend", "")),
        "status": str(result.status),
        "rows": getattr(result, "rows", None),
        "seed": getattr(result, "seed", None),
        "horizon": getattr(result, "horizon", None),
        "executed": bool(getattr(result, "executed", False)),
        "compared": bool(getattr(result, "compared", False)),
        "approved": bool(getattr(result, "approved", False)),
        "magnitudes": list(getattr(result, "magnitudes", ()) or ()),
        "comparisons": [_battery_comparison_row(item) for item in comparisons],
        "failure": battery_failure_kind(str(result.status), detail),
        "dependency": _battery_is_dependency(result),
        "prepared": _battery_is_prepared(result),
        "blocked_by": getattr(result, "blocked_by", None),
        "owner": _battery_owner(detail),
        # Statistical parity never proves that a rule changes the outcome: that
        # needs the later with/without contrast of a campaign.
        "sensitivity": "pending",
        "modular_seconds": getattr(result, "modular_seconds", 0.0),
        "candidate_seconds": getattr(result, "candidate_seconds", 0.0),
        "detail": detail,
    }


def battery_report_payload(
    report,
    *,
    profile: str | None,
    backend: str,
    catalog_sha256: str,
    inventory_sha256: str,
    elapsed_seconds: float | None = None,
    backends: Iterable[str] | None = None,
    versions: dict[str, object] | None = None,
) -> dict[str, object]:
    """Return the renewed statistical battery certificate.

    The payload describes preparation and, when it happened, execution.  It
    never turns a declared or limited case into a compared one: each row carries
    the stages the runner recorded (``executed``, ``compared``, ``approved``) and
    the magnitudes it compared with their rates and tolerances.  ``complete`` and
    ``accepted`` keep their execution meaning; ``sensitivity`` stays pending
    until a campaign contrasts each scenario with and without its rule.
    """
    results = tuple(getattr(report, "results", ()) or ())
    rows = tuple(_battery_case_row(result) for result in results)
    ran = any(row["executed"] for row in rows)

    variants: dict[str, dict[str, object]] = {}
    clauses: dict[str, dict[str, int]] = {}
    magnitudes: dict[str, dict[str, int]] = {}
    owners: dict[str, set[str]] = {}
    limits: dict[str, str] = {}
    for result, row in zip(results, rows):
        variant = str(row["variant"])
        bucket = variants.setdefault(variant, {
            "cases": 0, "executed": 0, "compared": 0, "approved": 0,
            "divergent": 0, "incompatible": 0, "not_run": 0, "errors": 0,
            "sensitivity_pending": 0, "dependencies": set(),
        })
        bucket["cases"] += 1
        status = str(row["status"])
        for stage in ("executed", "compared", "approved"):
            if row[stage]:
                bucket[stage] += 1
        if row["failure"] == "error":
            bucket["errors"] += 1
        elif status == "DIVERGENCE":
            bucket["divergent"] += 1
        elif status == "INCOMPATIBLE":
            bucket["incompatible"] += 1
        elif status == "NOT_RUN":
            bucket["not_run"] += 1
        # Every case still needs the later with/without contrast.
        bucket["sensitivity_pending"] += 1
        if row["dependency"] and row["owner"]:
            bucket["dependencies"].add(str(row["owner"]))
            owners.setdefault(str(row["owner"]), set()).add(str(row["case"]))
        blocked = str(row.get("blocked_by") or "")
        if blocked:
            limits[str(row["case"])] = blocked
        for item in row["comparisons"]:
            entry = magnitudes.setdefault(
                str(item["magnitude"]), {"cases": 0, "passed": 0},
            )
            entry["cases"] += 1
            if item["passed"]:
                entry["passed"] += 1
        for key in getattr(result, "keys", ()) or ():
            label = str(key)
            clause = clauses.setdefault(label, {
                "cases": 0, "executed": 0, "compared": 0, "approved": 0,
                "divergent": 0, "incompatible": 0,
            })
            clause["cases"] += 1
            for stage in ("executed", "compared", "approved"):
                if row[stage]:
                    clause[stage] += 1
            if status == "INCOMPATIBLE":
                clause["incompatible"] += 1
            elif status == "DIVERGENCE":
                clause["divergent"] += 1

    for bucket in variants.values():
        bucket["dependencies"] = sorted(bucket["dependencies"])

    totals = _battery_counts(results)
    case_ids = len({str(row["case"]) for row in rows})
    coverage = {
        "declared": len(results),
        "case_ids": case_ids,
        "prepared": sum(1 for row in rows if row["prepared"]),
        "executed": totals["executed"],
        "compared": totals["compared"],
        "approved": totals["approved"],
        "divergent": totals["divergent"],
        "incompatible": totals["incompatible"],
        "not_run": totals["not_run"],
        "errors": totals["errors"],
        "dependency": totals["dependencies"],
        "sensitivity_pending": case_ids,
        "dependencies_by_owner": {
            owner: sorted(cases) for owner, cases in sorted(owners.items())
        },
    }

    backend_rows = None
    if backends is not None:
        backend_rows = []
        for name in backends:
            selected = [row for row in rows if row["backend"] == name]
            statuses = [row["status"] for row in selected]
            available = bool(selected) and not all(
                status == "NOT_RUN" and row["dependency"]
                for status, row in zip(statuses, selected)
            )
            backend_rows.append({
                "backend": name,
                "available": available,
                "cases": len(selected),
                "executed": sum(1 for row in selected if row["executed"]),
                "compared": sum(1 for row in selected if row["compared"]),
                "approved": sum(1 for row in selected if row["approved"]),
                "errors": sum(1 for row in selected if row["failure"] == "error"),
                "incompatible": statuses.count("INCOMPATIBLE"),
                "not_run": statuses.count("NOT_RUN"),
            })

    levels = {"quick": 0, "complete": 0, "deep": 0}
    for row in rows:
        if row["level"] in levels:
            levels[str(row["level"])] += 1

    payload: dict[str, object] = {
        "schema": BATTERY_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed_seconds,
        "oracle": "combat.modular (read-only)",
        "candidate": backend,
        "execution": "run" if ran else "not-run",
        "preparation": {
            "profile": profile,
            "catalog_sha256": catalog_sha256,
            "inventory_sha256": inventory_sha256,
            "cases": case_ids,
            "backend_runs": len(results),
            "levels": levels,
            "rows": sorted({int(row["rows"] or 0) for row in rows if row["rows"]}),
            "seeds": sorted({int(row["seed"]) for row in rows
                             if row["seed"] is not None}),
            "horizons": sorted({int(row["horizon"]) for row in rows
                                if row["horizon"] is not None}),
            "magnitudes": sorted(magnitudes),
        },
        "complete": bool(getattr(report, "complete", False)),
        "accepted": bool(getattr(report, "accepted", False)),
        "scope": str(getattr(report, "scope", "provided")),
        "missing_variants": list(getattr(report, "missing_variants", ()) or ()),
        "cases": rows,
        "variants": variants,
        "clauses": clauses,
        "magnitudes": magnitudes,
        "limits": limits,
        "coverage": coverage,
        "sensitivity": {
            "demonstrated": [],
            "pending": sorted({str(row["case"]) for row in rows}),
            "note": (
                "statistical parity compares outcome distributions; it does not "
                "prove that a rule changes them. A with/without contrast needs "
                "the later campaign."
            ),
        },
        "traceability": {
            "candidate": backend,
            "profile": profile,
            "rows": sorted({int(row["rows"] or 0) for row in rows if row["rows"]}),
            "catalog_sha256": catalog_sha256,
            "inventory_sha256": inventory_sha256,
            "battery_module": "mordheim_combat_lab.verification.parity._battery_runner",
            # Real oracle/adaptor/candidate identity: a module and the SHA256
            # of its file, or ``unavailable`` when it is not importable here.
            "versions": dict(versions or {}),
            "elapsed_seconds": elapsed_seconds,
        },
    }
    if backend_rows is not None:
        payload["backends"] = backend_rows
    return payload


def battery_report_markdown(payload: dict[str, object]) -> str:
    """Render the renewed statistical certificate without inventing evidence."""
    preparation = payload["preparation"]
    assert isinstance(preparation, dict)
    coverage = payload["coverage"]
    assert isinstance(coverage, dict)
    variants = payload["variants"]
    assert isinstance(variants, dict)
    magnitudes = payload.get("magnitudes")
    assert isinstance(magnitudes, dict)
    lines = [
        "# Parity battery report",
        "",
        f"- Generated: `{payload['generated_at']}`",
        *([f"- Elapsed: `{payload['elapsed_seconds']:.1f}s`"]
          if isinstance(payload.get("elapsed_seconds"), (int, float))
          else ["- Elapsed: not recorded"]),
        f"- Oracle: `{payload['oracle']}`",
        f"- Candidate: `{payload['candidate']}`",
        f"- Profile: `{preparation.get('profile') or 'provided'}`",
        f"- Execution: `{payload['execution']}`",
        f"- Cases: `{preparation.get('cases')}`",
        f"- Seeds: `{preparation.get('seeds')}`",
        f"- Horizons: `{preparation.get('horizons')}`",
        f"- Catalog: `{preparation.get('catalog_sha256')}`",
        f"- Inventory: `{preparation.get('inventory_sha256')}`",
        "",
        "## Coverage",
        "",
        "| Bucket | Cases |",
        "|---|---:|",
    ]
    for name in ("declared", "case_ids", "prepared", "executed", "compared",
                 "approved", "divergent", "incompatible", "not_run", "errors",
                 "dependency", "sensitivity_pending"):
        lines.append(f"| {name} | {coverage.get(name, 0)} |")
    if magnitudes:
        lines.extend((
            "", "## Magnitudes compared", "",
            "| Magnitude | Comparisons | Within tolerance |",
            "|---|---:|---:|",
        ))
        for name in sorted(magnitudes):
            row = magnitudes[name]
            assert isinstance(row, dict)
            lines.append(f"| {name} | {row['cases']} | {row['passed']} |")
    backend_rows = payload.get("backends")
    if isinstance(backend_rows, list) and backend_rows:
        lines.extend((
            "", "## Backend availability", "",
            "| Backend | Available | Cases | Executed | Compared | Approved "
            "| Incompatible | Not run |",
            "|---|---|---:|---:|---:|---:|---:|---:|",
        ))
        for row in backend_rows:
            lines.append(
                f"| {row['backend']} | {row['available']} | {row['cases']} | "
                f"{row['executed']} | {row['compared']} | {row['approved']} | "
                f"{row['incompatible']} | {row['not_run']} |"
            )
    lines.extend((
        "", "## Variants", "",
        "| Variant | Cases | Executed | Compared | Approved | Incompatible "
        "| Not run | Sensitivity pending | Dependencies |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ))
    for variant in sorted(variants):
        row = variants[variant]
        assert isinstance(row, dict)
        dependencies = ", ".join(row.get("dependencies", ())) or "—"
        lines.append(
            f"| {variant} | {row['cases']} | {row['executed']} | "
            f"{row['compared']} | {row['approved']} | {row['incompatible']} | "
            f"{row['not_run']} | {row['sensitivity_pending']} | {dependencies} |"
        )
    limits = payload.get("limits")
    lines.extend(("", "## Real input limits", ""))
    if isinstance(limits, dict) and limits:
        for case, cause in sorted(limits.items()):
            lines.append(f"- `{case}`: `{cause}`")
    else:
        lines.append("- None recorded by the executed results.")
    owners = coverage.get("dependencies_by_owner")
    lines.extend(("", "## Dependencies by owner", ""))
    if isinstance(owners, dict) and owners:
        for owner, cases in owners.items():
            listed = ", ".join(f"`{case}`" for case in cases)
            lines.append(f"- `{owner}`: {listed}")
    else:
        lines.append("- None recorded by the executed results.")
    lines.extend((
        "", "## Scope of this certificate", "",
        "A case is compared on the terminal outcome distributions of both "
        "engines: `winner` (first win, second win, unresolved) always, plus "
        "`rounds`, `wounds` and `condition` when the case declares them. The "
        "criterion is the six-sigma tolerance of the historical certificate; no "
        "internal counter, flag or hash is required.",
        "",
        "`executed` means both samples were obtained, `compared` that at least "
        "one magnitude was compared and `approved` that all of them stayed "
        "within tolerance. A prepared case with a real input limit (initial "
        "state, per-row decisions) is `INCOMPATIBLE` with its cause and stays in "
        "the denominator; it is never replaced by a weaker scenario.",
        "",
        "`sensitivity` is pending for every case: statistical parity does not "
        "prove that a rule changes the outcome. `complete` and `accepted` are "
        "execution semantics over the required statistical cases of the profile, "
        "not semantic coverage of every internal rule.",
        "",
        "With `--backend all` every case is declared once per backend "
        "(`case_ids` is the catalog size).",
    ))
    return "\n".join(lines) + "\n"

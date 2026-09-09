"""Parity report dataclasses and JSON/Markdown payload builders."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timezone
from typing import Iterable

ROOT = Path(__file__).resolve().parents[4]

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

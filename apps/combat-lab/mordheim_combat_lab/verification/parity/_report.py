"""Parity report dataclasses and the obligation-report payload."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

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
    """One scenario's comparison of a candidate with its reference."""

    scenario: str
    backend: str
    simulations: int
    modular_rates: tuple[float, float, float]
    vectorized_rates: tuple[float, float, float]
    tolerances: tuple[float, float, float]
    passed: bool
    #: Wall time of each engine's sample. Zero when the sample was supplied
    #: by the caller without a measurement.
    reference_seconds: float = 0.0
    candidate_seconds: float = 0.0


#: Final status of a row that passed the six-sigma gate with a sample too
#: small to detect ``MAX_DETECTABLE_DIFFERENCE``: compared, never approved,
#: and it keeps the run incomplete (``--require-complete`` fails), without
#: being an own error.
UNDERPOWERED = "UNDERPOWERED"


def power_verdict(row) -> tuple[str, bool, str]:
    """``(status, approved, detail)`` once the sample's power is accounted for.

    A passing row whose minimum detectable difference exceeds
    ``MAX_DETECTABLE_DIFFERENCE`` proves too little to approve.
    """
    from mordheim_combat_lab.verification.parity._statistical import (
        MAX_DETECTABLE_DIFFERENCE, minimum_detectable_difference, underpowered,
    )

    if row.status != "PASS" or not underpowered(row.simulations):
        return row.status, row.approved, row.detail
    detail = (
        f"UNDERPOWERED: minimum detectable difference "
        f"{minimum_detectable_difference(row.simulations):.4f} > "
        f"{MAX_DETECTABLE_DIFFERENCE} at {row.simulations} rows"
    )
    if row.detail:
        detail += f"; {row.detail}"
    return UNDERPOWERED, False, detail


def parity_report_payload(
    report: ParityReport, elapsed_seconds: float | None = None,
) -> dict[str, object]:
    """The obligation report of the vectorized engine, as a payload.

    These are the exact checks and the source-derived obligation inventory;
    sampling belongs to ``run_parity`` and its own report.
    """
    return {
        "schema": "mordheim-combat-parity/v3",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed_seconds,
        "oracle": "combat.modular (read-only)",
        "candidate": "combat.vectorized",
        "complete": report.complete,
        "exact_checks": report.exact_checks,
        "verified": report.verified,
        "pending": report.pending,
        "divergences": report.divergences,
        "obligations": tuple({
            "kind": item.kind, "id": item.id, "consumer": item.consumer,
            "evidence": item.evidence, "verified": item.verified,
        } for item in report.obligations),
    }


def parity_report_markdown(payload: dict[str, object]) -> str:
    """Render :func:`parity_report_payload` as Markdown."""
    elapsed = payload.get("elapsed_seconds")
    lines = [
        "# Vectorized engine obligations",
        "",
        f"- Generated: `{payload['generated_at']}`",
        f"- Elapsed: `{elapsed:.1f}s`" if isinstance(elapsed, (int, float))
        else "- Elapsed: not recorded",
        f"- Oracle: `{payload['oracle']}`",
        f"- Candidate: `{payload['candidate']}`",
        f"- Complete: `{payload['complete']}`",
        f"- Verified: `{len(payload['verified'])}` of `{len(payload['obligations'])}`;"
        f" pending `{len(payload['pending'])}`; divergences `{len(payload['divergences'])}`",
        "",
        "## Exact checks",
        "",
        *[f"- `{name}`" for name in payload["exact_checks"]],
    ]
    for title, key in (("Divergences", "divergences"), ("Pending", "pending")):
        rows = payload[key]
        if rows:
            lines.extend(("", f"## {title}", "", *[f"- {item}" for item in rows]))
    return "\n".join(lines) + "\n"

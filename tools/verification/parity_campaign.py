"""The report of a parity comparison over stored samples.

``check samples compare`` decides stored pairs with the six-sigma gate and
writes ``parity-campaign.json`` and ``parity-campaign.md`` through
:func:`campaign_payload` and :func:`campaign_markdown`.  A row that was
rejected, could not be compared or was underpowered is recorded as such and
is never counted as approved.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Sequence

from mordheim_combat_lab.verification.parity import MagnitudeComparison
from mordheim_combat_lab.verification.parity import ParityRow
from mordheim_combat_lab.verification.parity._statistical import OUTCOME_LABELS
from mordheim_combat_lab.verification.parity._statistical import MAX_DETECTABLE_DIFFERENCE
from mordheim_combat_lab.verification.parity._statistical import minimum_detectable_difference
from mordheim_combat_lab.verification.parity._statistical import underpowered

SCHEMA = "mordheim-combat-parity-campaign/v1"

#: Sample width of a certification-sized run, as on main.  A narrower campaign
#: is a real comparison, but the report must not present it as certification.
CERTIFICATION_SIMULATIONS = 100_000

#: Outcome rates are reported as percentages; tolerances and differences are
#: differences of rates, hence percentage points.
_PERCENT = 100.0


def _scenario_name(corpus_key: str) -> str:
    """Name of a uniform corpus key (the key itself when unrecognised)."""
    prefix = "scenario/"
    return corpus_key[len(prefix):] if corpus_key.startswith(prefix) else corpus_key


def _verdict(row: ParityRow) -> str:
    """``pass``, ``underpowered``, ``divergent`` or ``not-run``.

    Only an approved row passes, and only when its sample could have detected
    a ``MAX_DETECTABLE_DIFFERENCE`` shift: a narrower sample that stayed within
    tolerance is ``underpowered``, compared but not approved.  A divergence is
    a divergence at any width.
    """
    if row.status == "PASS" and row.approved:
        return "underpowered" if underpowered(row.simulations) else "pass"
    if row.status == "DIVERGENCE":
        return "divergent"
    return "not-run"


def _magnitude(item: MagnitudeComparison) -> dict[str, object]:
    return {
        "magnitude": item.magnitude,
        "modular_rates": list(item.modular_rates),
        "candidate_rates": list(item.candidate_rates),
        "tolerances": list(item.tolerances),
        "differences": [
            abs(left - right)
            for left, right in zip(item.modular_rates, item.candidate_rates)
        ],
        "passed": bool(item.passed),
        "detail": item.detail,
    }


def _row_record(row: ParityRow) -> dict[str, object]:
    return {
        "corpus_key": row.case,
        "scenario": _scenario_name(row.case),
        "backend": row.backend,
        "maximum_rounds": row.maximum_rounds,
        "simulations_per_engine": row.simulations,
        "executed": bool(row.executed),
        "compared": bool(row.compared),
        "approved": _verdict(row) == "pass",
        "status": row.status,
        "verdict": _verdict(row),
        "minimum_detectable_difference": (
            minimum_detectable_difference(row.simulations) if row.simulations else None
        ),
        "magnitudes": [_magnitude(item) for item in row.comparisons],
        "reference_seconds": row.modular_seconds,
        "candidate_seconds": row.candidate_seconds,
        "detail": row.detail,
    }


def campaign_payload(
    rows: Iterable[ParityRow], *,
    config: dict[str, object],
    rejected: Iterable[tuple[str, str]] = (),
    elapsed_seconds: float | None = None,
    generated_at: str | None = None,
) -> dict[str, object]:
    """Return the campaign certificate of one run.

    Every selected scenario appears exactly once: as a sample row, or in
    ``rejected`` when the frozen corpus could not provide it.  ``complete``
    keeps its execution meaning — every selected scenario was compared and
    approved — so a partial or empty run is never complete.
    """
    records = [_row_record(row) for row in rows]
    rejected_records = [
        {
            "corpus_key": key,
            "status": "NOT_RUN",
            "verdict": "not-run",
            "detail": reason,
        }
        for key, reason in rejected
    ]
    statuses = [record["status"] for record in records]
    certification = bool(records) and all(
        record["simulations_per_engine"] >= CERTIFICATION_SIMULATIONS
        for record in records
    )
    coverage = {
        "selected": len(config["scenario_keys"]),
        "rows": len(records),
        "executed": sum(1 for record in records if record["executed"]),
        "compared": sum(1 for record in records if record["compared"]),
        "approved": sum(1 for record in records if record["approved"]),
        "divergent": statuses.count("DIVERGENCE"),
        "underpowered": sum(1 for record in records if record["verdict"] == "underpowered"),
        "incompatible": statuses.count("INCOMPATIBLE"),
        "not_run": statuses.count("NOT_RUN") + len(rejected_records),
        "rejected": len(rejected_records),
    }
    complete = (
        bool(records)
        and not rejected_records
        and len(records) == coverage["selected"]
        and all(record["verdict"] == "pass" for record in records)
    )
    return {
        "schema": SCHEMA,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": elapsed_seconds,
        "oracle": "combat.modular (read-only)",
        "candidate": ("combat.native (compiled)"
                      if config.get("candidate_backend") == "native"
                      else "combat.vectorized (numpy)"),
        "outcome_labels": list(OUTCOME_LABELS),
        "config": dict(config),
        "complete": complete,
        "certification_sample_complete": certification,
        "certification_minimum_simulations_per_engine": CERTIFICATION_SIMULATIONS,
        "maximum_detectable_difference": MAX_DETECTABLE_DIFFERENCE,
        "coverage": coverage,
        "scenarios": records,
        "rejected": rejected_records,
    }


def _percent_values(values: Sequence[float]) -> str:
    return "/".join(f"{_PERCENT * value:.3f}%" for value in values)


def _provenance_lines(payload: dict[str, object]) -> list[str]:
    """Revision and provenance warnings; warnings are shown, never hidden."""
    config = payload["config"]
    assert isinstance(config, dict)
    block = config.get("provenance")
    lines: list[str] = []
    if isinstance(block, dict):
        revision = block.get("revision") or {}
        lines.append(
            f"- Source revision: `{revision.get('commit') or 'unknown'}`"
            f" (dirty: `{revision.get('dirty')}`)"
        )
    warnings = [*(block.get("warnings", ()) if isinstance(block, dict) else ()),
                *payload.get("provenance_warnings", ())]
    if warnings:
        lines.extend(("", "## Provenance warnings", ""))
        lines.extend(f"- **WARNING:** {message}" for message in warnings)
    return lines


def campaign_markdown(payload: dict[str, object]) -> str:
    """Render the campaign certificate without inventing evidence."""
    candidate_name = "Native" if payload["candidate"] == "combat.native (compiled)" else "NumPy"
    config = payload["config"]
    assert isinstance(config, dict)
    coverage = payload["coverage"]
    assert isinstance(coverage, dict)
    rows = payload["scenarios"]
    assert isinstance(rows, list)
    rejected = payload["rejected"]
    assert isinstance(rejected, list)
    lines = [
        f"# Modular-to-{candidate_name} statistical parity campaign",
        "",
        f"- Generated: `{payload['generated_at']}`",
        *([f"- Elapsed: `{payload['elapsed_seconds']:.1f}s`"]
          if isinstance(payload.get("elapsed_seconds"), (int, float))
          else ["- Elapsed: not recorded"]),
        f"- Oracle: `{payload['oracle']}`",
        f"- Candidate: `{payload['candidate']}`",
        f"- Corpus: `{config.get('corpus')}`",
        f"- Corpus SHA256: `{config.get('corpus_sha256')}`",
        f"- Scenarios: `{' '.join(config.get('scenarios') or ())}`",
        f"- Scenarios selected: `{coverage.get('selected')}`",
        f"- Simulations per engine: `{config.get('simulations')}`",
        f"- Seed: `{config.get('seed')}`",
        f"- Maximum rounds: `{config.get('maximum_rounds') or 'per scenario'}`",
        f"- Workers: `{config.get('workers')}`",
        f"- Complete: `{payload['complete']}`",
        f"- Certification-sized sample: "
        f"`{payload['certification_sample_complete']}` "
        f"(minimum `{payload['certification_minimum_simulations_per_engine']:,}` "
        "duels per engine)",
        *_provenance_lines(payload),
        "",
        "## Coverage",
        "",
        "| Bucket | Count |",
        "|---|---:|",
    ]
    for name in ("selected", "rows", "executed", "compared", "approved",
                 "underpowered", "divergent", "incompatible", "not_run", "rejected"):
        lines.append(f"| {name} | {coverage.get(name, 0)} |")
    if rows:
        lines.extend((
            "",
            "## Results",
            "",
            "Rates are first win / second win / unresolved per engine. Tolerance "
            "and difference are percentage points of the same three outcomes, "
            "compared in that order.",
            "",
            "| Corpus key | Duels/engine | Rounds | Modular W/L/U | "
            f"{candidate_name} W/L/U | Tolerance W/L/U | Difference W/L/U | Verdict | "
            f"Oracle s | {candidate_name} s |",
            "|---|---:|---:|---|---|---|---|---|---:|---:|",
        ))
        for row in rows:
            magnitudes = row["magnitudes"]
            assert isinstance(magnitudes, list)
            if magnitudes:
                winner = magnitudes[0]
                assert isinstance(winner, dict)
                modular = winner["modular_rates"]
                candidate = winner["candidate_rates"]
                tolerances = winner["tolerances"]
                differences = winner["differences"]
            else:
                modular = candidate = tolerances = differences = ()
            lines.append(
                f"| {row['corpus_key']} | "
                f"{row['simulations_per_engine']:,} | {row['maximum_rounds']} | "
                f"{_percent_values(modular)} | {_percent_values(candidate)} | "
                f"{_percent_values(tolerances)} | {_percent_values(differences)} | "
                f"{row['verdict']} | {row['reference_seconds']:.2f} | "
                f"{row['candidate_seconds']:.2f} |"
            )
    flagged = [row for row in rows if row["verdict"] != "pass"]
    lines.extend(("", "## Not approved", ""))
    if flagged or rejected:
        for row in flagged:
            lines.append(
                f"- `{row['corpus_key']}`: `{row['status']}` "
                f"executed={row['executed']} compared={row['compared']} — "
                f"{row['detail'] or 'no detail recorded'}"
            )
        for row in rejected:
            lines.append(
                f"- `{row['corpus_key']}`: `{row['status']}` — {row['detail']}"
            )
    elif rows:
        lines.append(
            "- None: every selected scenario was compared and stayed within "
            "the six-sigma tolerance."
        )
    else:
        lines.append("- None: the selection was empty; nothing was compared.")
    lines.extend((
        "",
        "## Scope",
        "",
        "Each row compares the modular oracle's terminal outcome rates with the "
        f"{candidate_name} backend on the compiled fighters frozen in the corpus, using the "
        "six-sigma tolerance with the 0.25% floor. A scenario is `pass` only "
        "when both samples were obtained and every compared magnitude stayed "
        "within tolerance with a sample that could detect a "
        f"{_PERCENT * payload.get('maximum_detectable_difference', 0.05):.0f}-point "
        "shift; `underpowered` means it stayed within a tolerance too wide to "
        "decide anything; `divergent` means a comparison was performed and "
        "failed, and `not-run` means it was never performed.",
        "",
        "This campaign certifies outcome-distribution parity on the maintained "
        "catalogue. It does not establish complete rule coverage. A level only "
        "selects scenarios; every scenario keeps its own frozen round limit.",
    ))
    return "\n".join(lines) + "\n"

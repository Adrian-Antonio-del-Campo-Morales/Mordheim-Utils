"""Independent command: modular-to-NumPy statistical parity over the catalogue.

The five parity tests compare a couple of frozen scenarios; this command walks
the catalogue instead — 43 scenarios with uniform ``scenario/<name>``
keys, selected through the cumulative ``small``, ``normal`` and ``long``
levels (``small`` by default) — and writes a complete JSON and Markdown report.  It owns the
campaign configuration, the report and the CLI; execution belongs to
:func:`mordheim_combat_lab.verification.parity.run_parity`, which is called once for
the whole selection.

A row that was rejected, could not sample the oracle, was incompatible with the
candidate or was never compared is recorded as such and is never counted as
approved.  Parities are decided only
by the six-sigma gate (0.25% floor) of
:func:`mordheim_combat_lab.verification.parity.compare_statistical_parity`.

Usage (from the repository root)::

    python -m tools.verification.parity_campaign --workers 8
    python -m tools.verification.parity_campaign --level long
    python -m tools.verification.parity_campaign --id scenario/basic \
        --id scenario/long --simulations 5000

The report is written to ``<output>/parity-campaign.json`` and
``<output>/parity-campaign.md``; the exit code is 0 only when every selected
scenario was compared and approved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

from tools.verification.compiled_cases import CompiledCaseError
from tools.verification.compiled_cases import load_cases
from tools.verification.parity_catalog import CORPUS
from tools.verification.parity_catalog import LEVELS
from tools.verification.parity_catalog import load
from tools.verification.parity_catalog import select
from mordheim_combat_lab.verification.parity import MagnitudeComparison
from mordheim_combat_lab.verification.parity import ParityCase
from mordheim_combat_lab.verification.parity import ParityRow
from mordheim_combat_lab.verification.parity import run_parity
from mordheim_combat_lab.verification.parity._statistical import OUTCOME_LABELS

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
    """``pass``, ``divergent`` or ``not-run``; only an approved row passes."""
    if row.status == "PASS" and row.approved:
        return "pass"
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
        "approved": bool(row.approved),
        "status": row.status,
        "verdict": _verdict(row),
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
        "coverage": coverage,
        "scenarios": records,
        "rejected": rejected_records,
    }


def _percent_values(values: Sequence[float]) -> str:
    return "/".join(f"{_PERCENT * value:.3f}%" for value in values)


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
        f"- Level: `{config.get('level')}`",
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
        "",
        "## Coverage",
        "",
        "| Bucket | Count |",
        "|---|---:|",
    ]
    for name in ("selected", "rows", "executed", "compared", "approved",
                 "divergent", "incompatible", "not_run", "rejected"):
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
        "within tolerance; `divergent` means a comparison was performed and "
        "failed, and `not-run` means it was never performed.",
        "",
        "This campaign certifies outcome-distribution parity on the maintained "
        "catalogue. It does not establish complete rule coverage. A level only "
        "selects scenarios; every scenario keeps its own frozen round limit.",
    ))
    return "\n".join(lines) + "\n"


def _positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return number


def _workers(value: str) -> int | str:
    if value.casefold() == "auto":
        return "auto"
    return _positive(value)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.verification.parity_campaign",
        description=(
            "Run modular-to-NumPy statistical parity over the frozen catalogue "
            "and write a JSON and Markdown report."
        ),
    )
    selection = parser.add_argument_group("scenario selection")
    selection.add_argument(
        "--level", choices=LEVELS, default="small",
        help="cumulative scenario level: small 8, normal 30, long 43 "
             "(default: small)",
    )
    selection.add_argument(
        "--id", dest="ids", action="append", default=[], metavar="KEY",
        help="uniform corpus key to keep, repeatable (e.g. scenario/basic); "
             "must belong to the selected level",
    )
    samples = parser.add_argument_group("sample configuration")
    samples.add_argument(
        "--simulations", type=_positive, default=1_000, metavar="DUELS",
        help="duels per engine and scenario (default: 1000; sample widths are "
             "execution configuration, not scenario data)",
    )
    samples.add_argument(
        "--seed", type=int, default=2_026,
        help="oracle seed; the NumPy sample uses seed + 1000003 (default: 2026)",
    )
    samples.add_argument(
        "--rounds", type=_positive, default=None, metavar="N",
        help="override every scenario's round budget (default: frozen limits)",
    )
    samples.add_argument(
        "--workers", type=_workers, default="auto", metavar="N|auto",
        help="modular-oracle processes: 1 runs sequentially, auto pools only "
             "samples estimated over ~20s sequentially (default: auto)",
    )
    output = parser.add_argument_group("report")
    output.add_argument(
        "--output", default="reports/parity", metavar="DIR",
        help="directory for parity-campaign.json and parity-campaign.md "
             "(default: reports/parity)",
    )
    return parser


def _corpus_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        chosen = select(level=args.level, keys=args.ids)
    except ValueError as error:
        print(f"parity campaign: {error}", file=sys.stderr)
        return 2
    try:
        cases = load_cases(CORPUS)
    except (CompiledCaseError, OSError) as error:
        print(f"parity campaign: cannot load the frozen corpus: {error}", file=sys.stderr)
        return 2
    scenarios, rejected = load(chosen, cases)
    for key, reason in rejected:
        print(f"NOT_RUN: {key}: {reason}", file=sys.stderr)

    config = {
        "level": args.level,
        "scenario_keys": [key for key, _name in chosen],
        "simulations": args.simulations,
        "seed": args.seed,
        "maximum_rounds": args.rounds,
        "workers": args.workers,
        "corpus": CORPUS.relative_to(CORPUS.parents[3]).as_posix(),
        "corpus_sha256": _corpus_digest(CORPUS),
    }
    cases_to_run = tuple(
        ParityCase(
            label=scenario.key,
            first=scenario.case.first,
            second=scenario.case.second,
            maximum_rounds=(
                scenario.case.limits.maximum_rounds
                if args.rounds is None else args.rounds
            ),
            simulations=args.simulations,
            seed=args.seed,
        )
        for scenario in scenarios
    )
    started = time.perf_counter()
    run = run_parity(
        cases_to_run, backends=("numpy",), candidate="counts",
        workers=args.workers,
    )
    elapsed = time.perf_counter() - started
    payload = campaign_payload(
        run.rows, config=config, rejected=rejected, elapsed_seconds=elapsed,
    )

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    json_path = output / "parity-campaign.json"
    markdown_path = output / "parity-campaign.md"
    json_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n", encoding="utf-8",
    )
    markdown_path.write_text(campaign_markdown(payload), encoding="utf-8")

    coverage = payload["coverage"]
    assert isinstance(coverage, dict)
    print(
        f"parity campaign: {coverage['selected']} selected, "
        f"{coverage['compared']} compared, {coverage['approved']} approved, "
        f"{coverage['divergent']} divergent, "
        f"{coverage['incompatible']} incompatible, "
        f"{coverage['not_run']} not run, {coverage['rejected']} rejected"
    )
    for row in payload["scenarios"]:
        if row["verdict"] != "pass":
            print(f"{row['status']}: {row['corpus_key']}: {row['detail']}")
    print(f"complete={payload['complete']}")
    print(f"report={json_path.as_posix()}")
    print(f"report={markdown_path.as_posix()}")
    return 0 if payload["complete"] else 1


if __name__ == "__main__":  # pragma: no cover - command entry point
    raise SystemExit(main())

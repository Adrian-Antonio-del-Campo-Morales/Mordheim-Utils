#!/usr/bin/env python3
"""Mutation discrimination run for the vectorized engine.

Applies each mutant of the engine-mutation catalogue to a staged copy of the
source tree, runs the deterministic detector suites against the staged copy,
and reports killed vs surviving mutants.  A surviving mutant is a real
verification gap: add the deterministic test that catches it (never a
statistical pair) and rerun.  The live tree is never modified.

Usage::

    python tools/mutate-engine.py [--mutant ID ...] [--suites PATH ...] [--json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mordheim_combat_lab.verification import engine_mutation  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mutant", action="append", metavar="ID",
        help="restrict the run to catalogue ids (repeatable; default: all)")
    parser.add_argument(
        "--suites", nargs="+", metavar="PATH",
        help="detector pytest paths (default: the deterministic detector suites)")
    parser.add_argument("--json", action="store_true",
                        help="print the machine-readable report as JSON")
    parser.add_argument("--timeout", type=int, default=600, metavar="SECONDS",
                        help="per-mutant detector timeout (default: 600)")
    args = parser.parse_args(argv)

    catalogue = engine_mutation.CATALOG
    if args.mutant:
        wanted = set(args.mutant)
        missing = wanted - {mutant.id for mutant in catalogue}
        if missing:
            print(f"unknown mutant ids: {sorted(missing)}", file=sys.stderr)
            return 2
        catalogue = tuple(mutant for mutant in catalogue if mutant.id in wanted)
    suites = tuple(args.suites) if args.suites \
        else engine_mutation.DEFAULT_DETECTOR_SUITES

    def progress(outcome):
        print(
            f"{outcome.mutant.id:<28} {'KILLED' if outcome.killed else 'SURVIVED':<8} "
            f"({outcome.seconds:.1f}s, detector exit {outcome.returncode})",
            flush=True,
        )

    report = engine_mutation.run_catalogue(
        catalogue, suites, timeout=args.timeout, on_progress=progress,
    )
    if args.json:
        print(json.dumps({
            "complete": report.complete,
            "killed": list(report.killed),
            "surviving": list(report.surviving),
            "seconds": report.seconds,
            "outcomes": [{
                "id": item.mutant.id, "killed": item.killed,
                "returncode": item.returncode, "seconds": item.seconds,
            } for item in report.outcomes],
        }, indent=2))
    else:
        for outcome in report.outcomes:
            print(
                f"{outcome.mutant.id:<28} {'KILLED' if outcome.killed else 'SURVIVED':<8} "
                f"({outcome.seconds:.1f}s, detector exit {outcome.returncode})"
            )
        print(f"killed: {len(report.killed)}/{len(report.outcomes)}  "
              f"surviving: {sorted(report.surviving)}")
    return int(not report.complete)


if __name__ == "__main__":
    raise SystemExit(main())

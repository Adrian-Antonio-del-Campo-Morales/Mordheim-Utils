#!/usr/bin/env python3
"""Regenerate the committed deterministic-coverage budget.

Runs the deterministic engine suites under ``coverage`` and writes the
measured covered lines to ``tests/fixtures/coverage/budget.json``.  This must
be a real script (not ``python - <<EOF`` or ``-c``): the measured suites
include multiprocessing tests whose spawned workers re-import the main
module, which only works when the main module lives in a file.

Usage::

    python tools/update-coverage-budget.py [--suites PATH ...]

The gate itself is ``python tools/mordheim-utils.py coverage-gate``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mordheim_combat_lab.verification import coverage_gate  # noqa: E402

try:
    from mordheim_combat_lab.console import HelpFormatter as _HelpFormatter  # noqa: E402
except Exception:  # standalone run without the package importable
    from argparse import HelpFormatter as _HelpFormatter  # type: ignore[assignment]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=_HelpFormatter)
    parser.add_argument(
        "--suites", nargs="+", metavar="PATH",
        help="pytest paths to measure (default: the deterministic suites)",
    )
    parser.add_argument(
        "--output", default="tests/fixtures/coverage/budget.json", metavar="PATH",
        help="budget file to write (default: tests/fixtures/coverage/budget.json)",
    )
    args = parser.parse_args(argv)
    suites = tuple(args.suites) if args.suites else coverage_gate.DEFAULT_SUITES
    report = coverage_gate.measure_coverage(suites)
    output = Path(args.output).resolve()
    coverage_gate.write_budget(output, report)
    for area in coverage_gate.AREA_PATHS:
        covered, statements = report.area_total(area)
        percent = 100.0 * covered / statements if statements else 100.0
        print(f"coverage {area}: {percent:.2f}% ({covered}/{statements} statements)")
    print(f"BUDGET: {output} ({len(report.files)} files, {report.seconds:.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

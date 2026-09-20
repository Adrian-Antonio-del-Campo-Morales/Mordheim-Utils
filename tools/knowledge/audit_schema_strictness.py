#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report how the editorial schemas relate to the committed knowledge base.

Read-only. Two questions, one checklist:

* **Looseness** — a node the schemas leave undescribed, a tautological
  subschema, a key the documents carry and the contract never names, or a
  definition no schema can reach. These are holes and the suite fails on them.
* **Unfinished business** — a declared property, JSON type, enum value or
  ``oneOf``/``anyOf`` branch that no document exercises. Each one is either a
  declaration to tighten or a line in
  ``editorial_schema_audit.JUSTIFIED_FINDINGS`` explaining the contract that
  keeps it alive.

Usage::

    python tools/knowledge/audit_schema_strictness.py
    python tools/knowledge/audit_schema_strictness.py --json
    python tools/knowledge/audit_schema_strictness.py --only hard
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "python" / "knowledge"))

from mordheim_knowledge import editorial_schema_audit as audit  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--only",
        choices=("all", "hard", "soft"),
        default="all",
        help="which findings to report (default: all)",
    )
    parser.add_argument("--json", action="store_true", help="emit the findings as JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    findings = audit.audit_strictness()
    hard = audit.hard_findings(findings)
    unjustified = audit.unjustified_findings(findings)
    justified = [
        finding
        for finding in findings
        if not finding.hard and finding not in unjustified
    ]
    selected = {
        "hard": hard,
        "soft": justified + unjustified,
        "all": findings,
    }[args.only]

    if args.json:
        print(
            json.dumps(
                {
                    "findings": len(findings),
                    "hard": len(hard),
                    "justified": len(justified),
                    "unjustified": len(unjustified),
                    "stale_justifications": audit.stale_justifications(findings),
                    "reported": [
                        {
                            "kind": finding.kind,
                            "schema": finding.schema,
                            "path": finding.path,
                            "detail": finding.detail,
                            "documents": list(finding.documents),
                        }
                        for finding in selected
                    ],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        for finding in selected:
            print(finding)
        print(
            f"\n{len(findings)} findings: {len(hard)} hard, {len(justified)} justified, "
            f"{len(unjustified)} unjustified, "
            f"{len(audit.stale_justifications(findings))} stale justifications"
        )
    return 1 if hard or unjustified or audit.stale_justifications(findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())

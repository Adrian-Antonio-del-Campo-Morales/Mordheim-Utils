"""P00 read-only baseline probe of the existing parity entry points.

Writes ``spec-parity-baseline.txt``: environment, revision, register digest and
the per-case status of ``verify_specification_parity`` (only non-PASS rows) plus
the structural inventory counts.  It executes the existing verification code
against the current working tree; it adds no test, edits no engine and starts
no campaign.

    python -X utf8 TMP_VECTORIAL_ENGINE_2A2B/parity_update/P00-results/baseline_probe.py
"""
from __future__ import annotations

import hashlib
import platform
import subprocess
import sys
import time
from pathlib import Path

RESULTS = Path(__file__).resolve().parent
ROOT = RESULTS.parents[2]
REGISTER = ROOT / "sources/knowledge/verification/clause-contracts.csv"


def git(*args: str) -> str:
    return subprocess.run(
        ("git", *args), cwd=ROOT, capture_output=True, text=True, check=False,
    ).stdout.strip()


def main() -> int:
    import numpy
    from mordheim_combat_lab.verification.parity import (
        verify_specification_parity, verify_vectorized_parity,
    )

    lines = [
        "P00 baseline probe (read-only)",
        f"python={platform.python_version()} numpy={numpy.__version__}",
        f"node={platform.node()} platform={platform.platform()}",
        f"head={git('rev-parse', 'HEAD')}",
        f"branch={git('rev-parse', '--abbrev-ref', 'HEAD')}",
        f"dirty_entries={len(git('status', '--porcelain').splitlines())}",
        f"register_sha256={hashlib.sha256(REGISTER.read_bytes()).hexdigest()}",
        "",
    ]

    started = time.perf_counter()
    inventory = verify_vectorized_parity()
    lines += [
        "verify_vectorized_parity:",
        f"  obligations={len(inventory.obligations)}",
        f"  verified={len(inventory.verified)}",
        f"  pending={len(inventory.pending)}",
        f"  divergences={len(inventory.divergences)}",
        f"  exact_checks={','.join(inventory.exact_checks)}",
        f"  complete={inventory.complete}",
        f"  seconds={time.perf_counter() - started:.1f}",
        "",
    ]
    started = time.perf_counter()
    report = verify_specification_parity()
    lines += [
        "verify_specification_parity:",
        f"  cases={len(report.cases)}",
        f"  pass={len(report.passed)}",
        f"  pending_adapter={len(report.pending)}",
        f"  divergences={len(report.divergences)}",
        f"  out_of_scope={len(report.out_of_scope)}",
        f"  complete={report.complete}",
        f"  seconds={time.perf_counter() - started:.1f}",
        "",
        "non-pass cases (specification/case :: operation :: adapter :: detail):",
    ]
    for case in report.cases:
        if case.status == "PASS":
            continue
        detail = " ".join(str(case.detail).split())
        if len(detail) > 240:
            detail = detail[:240] + " ...[truncated; rerun this probe for the full detail]"
        lines.append(
            f"  {case.status} {case.specification}/{case.case} :: "
            f"{case.operation} :: {case.adapter} :: {detail}"
        )
    text = "\n".join(lines) + "\n"
    (RESULTS / "spec-parity-baseline.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

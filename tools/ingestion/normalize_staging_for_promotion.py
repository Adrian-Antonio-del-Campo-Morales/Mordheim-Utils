#!/usr/bin/env python3
"""Give the staged 2A/2B catalogues the promotion shape of the knowledge base.

The passes of ``mordheim_knowledge.staging_promotion``, in the order they have to
run: ``market`` builds the staged market catalogue (one entry per item, in the
shape of ``catalog/campaign/trading-post.yaml``) *before* ``items`` retires the
field it reads from the item records, and ``hirelings`` builds the staged
campaign side (fees, upkeep, eligibility) *before* it retires ``hire_fee`` and
``available_to`` from the profiles. ``magic`` writes the KB envelope, the
``lore_assignments`` rows and the materialised reprints of the magic documents,
and folds the Magical Failure Table into the band rule that rolls on it. ``shape``
runs last and writes the block-collection keys in the shape the KB keeps: a staged
flow collection (`[a, b]`, `{a: 1}`) is a merge diff that is nothing but shape.
``tools/knowledge/maintenance/format_yaml.py`` then rewrites the folded prose of every document this
tool rebuilds.

Usage::

    python tools/ingestion/normalize_staging_for_promotion.py --check
    python tools/ingestion/normalize_staging_for_promotion.py --write
    python tools/ingestion/normalize_staging_for_promotion.py --check --passes market
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "python" / "knowledge"))

from mordheim_knowledge import staging_promotion as promotion  # noqa: E402


def format_written(paths: list[Path]) -> None:
    """Let the canonical formatter own the shape of every file this tool wrote."""
    yaml_paths = sorted({path for path in paths if path.suffix == ".yaml"})
    if not yaml_paths:
        return
    grouped = [str(path) for path in yaml_paths]
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "knowledge" / "maintenance" / "format_yaml.py"), "--write", *grouped],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise SystemExit((result.stdout or "") + (result.stderr or ""))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report what would change")
    parser.add_argument("--write", action="store_true", help="write the normalisation")
    parser.add_argument(
        "--passes",
        default=",".join(promotion.PASSES),
        help=f"comma-separated passes ({', '.join(promotion.PASSES)})",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    args = parser.parse_args(argv)

    if args.check == args.write:
        parser.error("choose one of --check or --write")

    passes = [name.strip() for name in args.passes.split(",") if name.strip()]
    report = promotion.run(passes)
    if args.json:
        print(
            json.dumps(
                [
                    {"path": edit.path.as_posix(), "changes": len(edit.changes), "detail": edit.changes[:8]}
                    for edit in report.edits
                ],
                indent=2,
                ensure_ascii=False,
            )
        )
    else:
        for edit in report.edits:
            print(f"{edit.path.as_posix()} — {len(edit.changes)} change(s)")
            for change in edit.changes[:6]:
                print(f"    {change}")
    if args.write:
        written = report.write()
        format_written(written)
        print(f"normalized {len(written)} files")
        return 0
    print(f"checked: {len(report.edits)} files would change")
    return 1 if report.edits else 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Close the vocabulary of the open editorial fields (check or write).

The fields the editorial contract leaves open are the ones a gate has to hold:
``sources[].manual`` against ``registry/sources.yaml``, the band ``status`` and
``profiles[].source_path[]`` against the vocabulary the active KB uses. This
tool is that gate's writer.

Usage::

    python tools/knowledge/normalize_open_fields.py --check
    python tools/knowledge/normalize_open_fields.py --write
    python tools/knowledge/normalize_open_fields.py --check --passes manuals,status
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "python" / "knowledge"))

from mordheim_knowledge import open_field_normalization as normalization  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report what would change")
    parser.add_argument("--write", action="store_true", help="write the normalisation")
    parser.add_argument(
        "--passes",
        default=",".join(normalization.PASSES),
        help=f"comma-separated passes ({', '.join(normalization.PASSES)})",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable report")
    args = parser.parse_args(argv)

    if not args.check and not args.write:
        parser.error("choose --check or --write")
    if args.check and args.write:
        parser.error("choose one of --check or --write")

    passes = [name.strip() for name in args.passes.split(",") if name.strip()]
    report = normalization.edits(passes)

    if args.json:
        import json

        payload = [
            {"path": edit.path.as_posix(), "changes": edit.changes} for edit in report.edits
        ]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        for line in report.summary().splitlines():
            print(line)

    if args.write:
        report.write()
        print(f"normalized {len(report.edits)} files")
        return 0

    print(f"checked: {len(report.edits)} files would change")
    return 1 if report.edits else 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Refresh stale ``sources[].digest`` pins in the semantic spec corpus.

The corpus pins every referenced KB rule by content digest so semantic drift
breaks loudly. Data-only KB edits (i18n fills, YAML formatting that preserves
parsed values) also move the fingerprint without changing meaning; this tool
recomputes the fingerprints from the live inventory and rewrites only the
``digest`` fields of the targets that changed.

Usage::

    python tools/refresh_spec_digests.py            # report + rewrite
    python tools/refresh_spec_digests.py --check    # report only

Only ``sources[].digest`` values are touched — interpretations, cases, dice,
expectations and mutations stay untouched.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from mordheim_combat_lab.verification.inventory import inventory  # noqa: E402
from mordheim_knowledge.loader import knowledge_root  # noqa: E402

SPECS_ROOT = Path(__file__).resolve().parent.parent / "tests" / "specs" / "semantic"


def _iter_specifications(doc: object):
    """Yield every specification dict in a spec file (flat or nested)."""
    if isinstance(doc, list):
        for item in doc:
            yield from _iter_specifications(item)
        return
    if not isinstance(doc, dict):
        return
    if "sources" in doc:
        yield doc
    for key in ("specifications",):
        for item in doc.get(key) or []:
            yield from _iter_specifications(item)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report only, do not rewrite")
    args = parser.parse_args()

    indexed = {item.id: item for item in inventory(knowledge_root())}

    spec_files = sorted(SPECS_ROOT.rglob("*.yaml"))
    changed_files = 0
    refreshed = 0
    stale_unknown = []
    for spec_file in spec_files:
        doc = yaml.safe_load(spec_file.read_text(encoding="utf-8")) or {}
        dirty = False
        for spec in _iter_specifications(doc):
            for source in spec.get("sources") or []:
                if not isinstance(source, dict) or "target" not in source:
                    continue
                item = indexed.get(source["target"])
                if item is None:
                    stale_unknown.append(f"{spec_file.name}: {source['target']}")
                    continue
                if item.source_digest != source.get("digest"):
                    if not args.check:
                        source["digest"] = item.source_digest
                        dirty = True
                    refreshed += 1
        if dirty:
            spec_file.write_text(
                yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=100),
                encoding="utf-8",
            )
            changed_files += 1

    mode = "stale (check mode)" if args.check else "refreshed"
    print(f"{mode}: {refreshed} digest pins in {changed_files} files")
    for note in stale_unknown:
        print(f"  unknown target: {note}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

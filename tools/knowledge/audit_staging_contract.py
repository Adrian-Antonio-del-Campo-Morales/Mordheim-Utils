#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Report how the staged warband packages of `sources/2A` and `sources/2B` deviate
from the editorial contract (`contracts/knowledge-editorial-v1/`).

Read-only. The staging trees are deliberately outside the contract coverage of
`tests/knowledge/test_editorial_schemas.py` until they are promoted, so this tool
measures the gap that promotion has to close. It reports the two passes of
`mordheim_knowledge.staging_contract_audit`:

* **schema** — the four documents of every package validated with the same JSON
  Schemas the active knowledge base is validated with, grouped by document, field
  path and error kind so the report names the field rather than listing 4 000
  messages.
* **vocabulary** — the values a staging tree uses in the fields the contract
  deliberately types loosely (`status`, `sources[].manual`, `categories`,
  `grade`, `profiles[].source_path`) that no decision sanctions. A value passes
  either because the KB vocabulary carries it, because it is a registered source
  id (`registry/sources.yaml` is the vocabulary of `manual`), or because
  `ACCEPTED_OPEN_VALUES` names the decision that introduced it.
* **catalogue** — the staged items, Hired Sword and Dramatis profiles, market,
  magic and campaign documents validated against the schema of the KB document
  that will claim them at promotion, plus any catalogue YAML no destination
  claims and the files promotion declares it leaves behind. These are the
  extension classes of `sources/2B/promotion-schema-plan.md`; this pass is what
  says whether the plan still describes the trees.
* **naming** — the files `tools/normalize_names.py --check` would rewrite. The
  title-case policy is a gate for `sources/knowledge` but not for the staging
  trees, so this is one of the two canonical-formatting rules a promotion copy
  can break.
* **shape** — the flow collections of the keys the KB writes in block form
  (`source_path`, `equipment_lists`, `rule_ids`, `skill_access`, `source`,
  `characteristics`, `name_i18n`, `combat_traits`). The other canonical-formatting
  rule: the KB writes those keys as block collections (1 892 sequences and 7 353
  mappings) and a staged `[a, b]` / `{a: 1}` is a merge diff that is nothing but
  shape.

A green schema run is not a promotion certificate: it means the shape is the
promoted shape, not that the values are. Rule/item resolution, `grant` vs
`applies_to` and cross-tree id collisions live in
`tools/knowledge/audit_kb_conformance.py` and the loader.

Usage::

    python tools/knowledge/audit_staging_contract.py
    python tools/knowledge/audit_staging_contract.py --tree 2B
    python tools/knowledge/audit_staging_contract.py --only schema
    python tools/knowledge/audit_staging_contract.py --only naming
    python tools/knowledge/audit_staging_contract.py --only shape
    python tools/knowledge/audit_staging_contract.py --json

Exit code is 0 when the selected scope is clean, and every scope is a gate that
should stay green: `tools/ingestion/normalize_staging_for_promotion.py` closes the
catalogue (the promotion shape of the staged documents) and the shape (its
`shape` pass),
`tools/knowledge/normalize_open_fields.py` the vocabulary and
`tools/normalize_names.py` the naming. A catalogue finding is a promotion-shape
decision of `sources/2B/promotion-schema-plan.md` that has not been applied yet.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "packages" / "python" / "knowledge"))

from mordheim_knowledge import staging_contract_audit as audit  # noqa: E402


def schema_lines(root: Path, limit: int) -> list[str]:
    deviations = audit.schema_deviations(root)
    if not deviations:
        return ["   the four documents of every package match the contract schemas"]
    lines = [f"   {len(deviations)} distinct deviations"]
    for deviation in deviations[:limit]:
        lines.append(f"   {deviation}")
    if len(deviations) > limit:
        lines.append(f"   ... {len(deviations) - limit} more")
    return lines


def catalogue_lines(root: Path) -> list[str]:
    unclaimed, families = audit.catalogue_coverage(root)
    lines = [f"   destination: {', '.join(sorted({family.schema_path for family in families}))}"]
    kept_out = audit.not_promoted_paths(root)
    if kept_out:
        lines.append(f"   {len(kept_out)} file(s) promotion leaves behind (declared):")
        lines.extend(f"      {path.relative_to(root).as_posix()}" for path, _ in kept_out)
    if unclaimed:
        lines.append(f"   {len(unclaimed)} catalogue file(s) no destination claims:")
        lines.extend(f"      {path.relative_to(root).as_posix()}" for path in unclaimed)
    deviations = audit.catalogue_deviations(root)
    if not deviations:
        lines.append("   every catalogue document matches the schema of its promotion destination")
        return lines
    counts: Counter[str] = Counter()
    files: dict[str, set[str]] = {}
    for deviation in deviations:
        key = audit.deviation_class(deviation)
        counts[key] += deviation.count
        files.setdefault(key, set()).update(deviation.packages)
    lines.append(f"   {sum(counts.values())} violations in {len(counts)} classes")
    for key, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        shown = len(files[key])
        lines.append(f"   {count:5d}x {key}" + (f"  [{shown} files]" if shown > 1 else ""))
    return lines


def naming_lines(root: Path) -> list[str]:
    drift = audit.naming_drift(root)
    if not drift:
        return ["   every name satisfies the knowledge base's title-case policy"]
    lines = [f"   {len(drift)} file(s) the knowledge base normalizer would rewrite:"]
    lines.extend(f"   {count:5d} name fields  {path}" for path, count in drift.items())
    return lines


def shape_lines(root: Path) -> list[str]:
    drift = audit.collection_shape_drift(root)
    if not drift:
        return ["   every block-collection key is written in the shape the knowledge base keeps"]
    lines = [f"   {sum(drift.values())} flow collection(s) the KB writes in block form:"]
    lines.extend(f"   {count:5d}x {key}" for key, count in drift.items())
    return lines


def vocabulary_lines(root: Path) -> list[str]:
    findings = audit.open_value_findings(root)
    lines: list[str] = []
    introduced = audit.novel_open_values(root)
    sanctioned = {
        label: {
            value: audit.ACCEPTED_OPEN_VALUES.get(label, {}).get(value, "registered source id")
            for value in values
            if value in audit.ACCEPTED_OPEN_VALUES.get(label, {})
            or (label.endswith("sources[].manual") and value in audit.registered_source_ids())
        }
        for label, values in introduced.items()
    }
    for label, values in sanctioned.items():
        if not values:
            continue
        lines.append(f"   {label} — new names, each with its decision:")
        for value, reason in sorted(values.items()):
            lines.append(f"       {value!r}: {reason}")
    if not findings:
        lines.append(
            "   every other value belongs to the vocabulary of the active knowledge base"
            if lines
            else "   every value belongs to the vocabulary of the active knowledge base"
        )
        return lines
    known = audit.open_field_values(audit.tree_root(audit.REFERENCE_TREE))
    for label, values in findings.items():
        vocabulary = sorted(known[label])
        shown = vocabulary if len(vocabulary) <= 8 else f"{len(vocabulary)} values"
        lines.append(f"   {label} — KB vocabulary: {shown}")
        for value, count in sorted(values.items(), key=lambda item: (-item[1], item[0])):
            lines.append(f"   {count:5d}x {value!r}")
    return lines


def text_report(trees: list[str], scope: str, limit: int) -> str:
    lines: list[str] = []
    for tree in trees:
        root = audit.tree_root(tree)
        lines.append(f"== {tree}: {len(audit.packages(root))} band packages")
        if scope in ("all", "schema"):
            lines.append("-- schema (contract-enforced)")
            lines.extend(schema_lines(root, limit))
        if scope in ("all", "vocabulary"):
            lines.append("-- vocabulary (fields the contract leaves open)")
            lines.extend(vocabulary_lines(root))
        if scope in ("all", "catalogue"):
            lines.append("-- catalogue (staged documents vs their promotion destination)")
            lines.extend(catalogue_lines(root))
        if scope in ("all", "naming"):
            lines.append("-- naming (the title-case gate the staging is not held to)")
            lines.extend(naming_lines(root))
        if scope in ("all", "shape"):
            lines.append("-- shape (the block-collection keys the staging is not held to)")
            lines.extend(shape_lines(root))
        lines.append("")
    return "\n".join(lines)


def json_report(trees: list[str], scope: str) -> str:
    payload: dict = {
        "kb_vocabulary": {
            label: sorted(values)
            for label, values in audit.open_field_values(audit.tree_root(audit.REFERENCE_TREE)).items()
        },
        "accepted_open_values": audit.ACCEPTED_OPEN_VALUES,
        "registered_sources": sorted(audit.registered_source_ids()),
    }
    for tree in trees:
        root = audit.tree_root(tree)
        entry: dict = {"packages": len(audit.packages(root))}
        if scope in ("all", "schema"):
            entry["schema"] = [
                {
                    "document": deviation.document,
                    "path": deviation.path,
                    "kind": deviation.kind,
                    "message": deviation.message,
                    "packages": sorted(deviation.packages),
                    "keys": dict(deviation.keys),
                }
                for deviation in audit.schema_deviations(root)
            ]
        if scope in ("all", "vocabulary"):
            entry["vocabulary"] = {
                "introduced": audit.novel_open_values(root),
                "unsanctioned": audit.open_value_findings(root),
            }
        if scope in ("all", "catalogue"):
            unclaimed, families = audit.catalogue_coverage(root)
            entry["catalogue"] = {
                "destinations": sorted({family.schema_path for family in families}),
                "unclaimed": [path.relative_to(root).as_posix() for path in unclaimed],
                "deviations": [
                    {
                        "family": deviation.document,
                        "path": deviation.path,
                        "kind": deviation.kind,
                        "message": deviation.message,
                        "files": sorted(deviation.packages),
                        "keys": dict(deviation.keys),
                        "count": deviation.count,
                    }
                    for deviation in audit.catalogue_deviations(root)
                ],
            }
        if scope in ("all", "naming"):
            entry["naming"] = audit.naming_drift(root)
        if scope in ("all", "shape"):
            entry["shape"] = audit.collection_shape_drift(root)
        payload[tree] = entry
    return json.dumps(payload, indent=2, ensure_ascii=False)


def findings(trees: list[str], scope: str) -> int:
    total = 0
    for tree in trees:
        root = audit.tree_root(tree)
        if scope in ("all", "schema"):
            total += len(audit.schema_deviations(root))
        if scope in ("all", "vocabulary"):
            total += sum(len(values) for values in audit.open_value_findings(root).values())
        if scope in ("all", "catalogue"):
            unclaimed, _ = audit.catalogue_coverage(root)
            total += len(unclaimed) + sum(deviation.count for deviation in audit.catalogue_deviations(root))
        if scope in ("all", "naming"):
            total += len(audit.naming_drift(root))
        if scope in ("all", "shape"):
            total += sum(audit.collection_shape_drift(root).values())
    return total


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--tree",
        action="append",
        choices=sorted(audit.TREE_DIRECTORIES),
        help=f"tree to audit; repeatable (default: {' '.join(audit.STAGED_TREES)})",
    )
    parser.add_argument(
        "--only",
        choices=("all", "schema", "vocabulary", "catalogue", "naming", "shape"),
        default="all",
        help="which pass to run (default: all)",
    )
    parser.add_argument("--limit", type=int, default=40, help="deviations per tree in the text report")
    parser.add_argument("--json", action="store_true", help="emit the report as JSON")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    trees = args.tree or list(audit.STAGED_TREES)
    print(json_report(trees, args.only) if args.json else text_report(trees, args.only, args.limit), end="")
    return 1 if findings(trees, args.only) else 0


if __name__ == "__main__":
    raise SystemExit(main())

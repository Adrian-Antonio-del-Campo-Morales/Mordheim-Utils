#!/usr/bin/env python3
"""Identity inventory and test coverage of the knowledge base.

The knowledge base is the denominator (``mordheim_knowledge.clauses``): every
core rule, mechanic the runtime keeps, implemented item and ``YES`` rule effect
is one identity, split into clauses only when its printed text has several
observable parts.  Tests declare what they cover: the rules-conformance corpus through
``audit_id``/``covers`` and the deterministic suites through the
``@pytest.mark.covers(identity, *clause_ids)`` marker.  This tool joins the two
sides without importing or running any engine.

Usage::

    python tools/knowledge/clauses.py inventory              # counts by kind and scope
    python tools/knowledge/clauses.py coverage               # coverage summary
    python tools/knowledge/clauses.py coverage --pending     # admitted clauses nobody covers
    python tools/knowledge/clauses.py coverage --identity ID # one identity in detail
    python tools/knowledge/clauses.py check                  # references and consistency; exit 1 on a defect
    python tools/knowledge/clauses.py report --output DIR    # rules-inventory.csv + clause-coverage.csv

Coverage counts declared references, not executed evidence: a scenario or test
that names an identity must still run and pass.  An undivided identity is
covered by any reference; a split identity needs every ``YES`` clause named.
A clause with scope ``YES`` under an effect that is not ``YES`` is reported by
``check`` as an inconsistency to review, never silently dropped.
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages/python/knowledge"))

from mordheim_knowledge.clauses import (  # noqa: E402
    IDENTITY_KINDS, Identity, admitted_clauses, declared_clauses, inventory_digest, load_identities,
)
from mordheim_knowledge.loader import knowledge_root, read_yaml  # noqa: E402

SAFE_YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
CONFORMANCE_CASES = ROOT / "tests/conformance/cases"
TESTS = ROOT / "tests"
#: Identity kinds the conformance corpus may declare (items are covered by deterministic tests only).
CONFORMANCE_KINDS = ("core", "mechanic", "rule")


@dataclass(frozen=True, slots=True)
class Reference:
    """One declared coverage reference: a scenario or a test function naming an identity or one of its clauses."""
    source: str      # ``conformance`` or ``test``
    identity: str
    clause_id: str   # ``""`` when the reference names the identity as a whole
    where: str       # scenario test id or ``path::function``


def conformance_references(cases: Path = CONFORMANCE_CASES) -> list[Reference]:
    references = []
    for path in sorted(cases.rglob("*.yaml")):
        scenarios = yaml.load(path.read_text(encoding="utf-8"), Loader=SAFE_YAML_LOADER) or []
        for scenario in scenarios:
            if not isinstance(scenario, dict) or "audit_id" not in scenario:
                continue
            where = f"{scenario['audit_id']}::{scenario.get('id')}"
            covers = scenario.get("covers") or ()
            if not covers:
                references.append(Reference("conformance", str(scenario["audit_id"]), "", where))
            for clause_id in covers:
                references.append(Reference("conformance", str(scenario["audit_id"]), str(clause_id), where))
    return references


def _marker_calls(decorators) -> list[tuple[str, list[str]]]:
    found = []
    for decorator in decorators:
        if not isinstance(decorator, ast.Call):
            continue
        func = decorator.func
        if not (isinstance(func, ast.Attribute) and func.attr == "covers"):
            continue
        values = [arg.value for arg in decorator.args if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
        if values:
            found.append((values[0], values[1:] or [""]))
    return found


def test_references(tests: Path = TESTS) -> list[Reference]:
    references = []
    for path in sorted(tests.rglob("test_*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        relative = path.relative_to(ROOT).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for identity, clause_ids in _marker_calls(node.decorator_list):
                    for clause_id in clause_ids:
                        references.append(Reference("test", identity, clause_id, f"{relative}::{node.name}"))
    return references


def all_references() -> list[Reference]:
    return [*conformance_references(), *test_references()]


# --------------------------------------------------------------------------- views
def coverage_index(references) -> dict[tuple[str, str], set[str]]:
    """``(identity, clause_id)`` -> references; ``clause_id`` is ``""`` for whole-identity references."""
    index: dict[tuple[str, str], set[str]] = defaultdict(set)
    for reference in references:
        index[(reference.identity, reference.clause_id)].add(f"{reference.source}:{reference.where}")
    return index


def references_of(index, identity: str) -> set[str]:
    return {ref for (name, _), refs in index.items() if name == identity for ref in refs}


def unknown_references(identities, references) -> list[Reference]:
    declared = declared_clauses(identities)
    return [r for r in references
            if r.identity not in declared or (r.clause_id and r.clause_id not in declared[r.identity])]


def inconsistencies(identities) -> list[str]:
    findings = []
    for record in identities:
        for clause in record.clauses:
            if clause.admitted and record.effect_scope not in (None, "YES"):
                findings.append(
                    f"{record.identity}/{clause.clause_id}: clause YES under a {record.effect_scope} effect"
                )
    return findings


def identity_status(record: Identity, index) -> str:
    """``covered`` / ``partial`` / ``uncovered`` for an admitted identity, ``not-admitted`` otherwise."""
    if not record.admitted:
        return "not-admitted"
    if not record.clauses or not record.admitted_clause_ids:
        return "covered" if references_of(index, record.identity) else "uncovered"
    covered = sum(1 for c in record.admitted_clause_ids if index.get((record.identity, c)))
    if covered == len(record.admitted_clause_ids):
        return "covered"
    return "partial" if covered else "uncovered"


def covered_count(record: Identity, index) -> tuple[int, int]:
    """(covered, total) obligations of an admitted identity: its YES clauses, or itself when undivided."""
    if not record.admitted:
        return (0, 0)
    if not record.admitted_clause_ids:
        return (1 if references_of(index, record.identity) else 0, 1)
    return (sum(1 for c in record.admitted_clause_ids if index.get((record.identity, c))), len(record.admitted_clause_ids))


# --------------------------------------------------------------------------- commands
def command_inventory(args) -> int:
    identities = load_identities()
    admitted = [i for i in identities if i.admitted]
    print(f"identities: {len(identities)} ({len(admitted)} admitted); digest {inventory_digest(identities)[:12]}")
    for kind in IDENTITY_KINDS:
        rows = [i for i in admitted if i.kind == kind]
        split = [i for i in rows if i.clauses]
        print(f"  {kind:<9} admitted {len(rows):>5}  split into clauses {len(split):>4}  "
              f"(YES clauses {sum(len(i.admitted_clause_ids) for i in split)}, NO clauses {sum(len(i.clauses) - len(i.admitted_clause_ids) for i in split)})")
    if args.csv:
        write_clause_csv(Path(args.csv), identities, coverage_index(all_references()))
        print(f"wrote {args.csv}")
    return 0


def command_coverage(args) -> int:
    identities = load_identities()
    references = all_references()
    index = coverage_index(references)
    kinds = tuple(args.kind) if args.kind else IDENTITY_KINDS
    if args.identity:
        selected = [i for i in identities if i.identity == args.identity]
        if not selected:
            print(f"unknown identity {args.identity!r}", file=sys.stderr)
            return 2
        record = selected[0]
        print(f"{record.identity} [{'admitted' if record.admitted else 'not admitted'}] -> {identity_status(record, index)}")
        if not record.clauses:
            for ref in sorted(references_of(index, record.identity)):
                print(f"    {ref}")
        for clause in record.clauses:
            refs = sorted(index.get(clause.key, ()))
            print(f"  {clause.clause_id} [{clause.scope}] -> {len(refs)} reference(s)")
            for ref in refs:
                print(f"    {ref}")
        return 0
    admitted = [i for i in identities if i.admitted and i.kind in kinds]
    totals = [covered_count(i, index) for i in admitted]
    covered, total = sum(c for c, _ in totals), sum(t for _, t in totals)
    by_source = Counter(r.source for r in references)
    statuses = Counter(identity_status(i, index) for i in admitted)
    print("Knowledge-base coverage (declared references, not executed evidence)")
    print(f"  obligations: {covered} / {total} covered"
          f"  (conformance references: {by_source['conformance']}, test markers: {by_source['test']})")
    print(f"  admitted identities: {len(admitted)}; covered {statuses['covered']}, "
          f"partial {statuses['partial']}, uncovered {statuses['uncovered']}")
    for kind in kinds:
        rows = [i for i in admitted if i.kind == kind]
        kc = sum(covered_count(i, index)[0] for i in rows); kt = sum(covered_count(i, index)[1] for i in rows)
        print(f"    {kind:<9} {kc:>5} / {kt:<5} obligations in {len(rows)} identities")
    if args.pending:
        print("Pending (no scenario or marker names them):")
        shown = 0
        for record in sorted(admitted, key=lambda i: i.identity):
            pending = ([""] if not record.admitted_clause_ids and not references_of(index, record.identity)
                       else [c for c in sorted(record.admitted_clause_ids) if not index.get((record.identity, c))])
            for clause_id in pending:
                print(f"  {record.identity}" + (f" :: {clause_id}" if clause_id else ""))
                shown += 1
                if args.limit and shown >= args.limit:
                    print("  ... use --limit 0 for the complete list")
                    return 0
    return 0


def command_check(args) -> int:
    identities = load_identities()
    references = all_references()
    unknown = unknown_references(identities, references)
    findings = inconsistencies(identities)
    for reference in unknown:
        print(f"UNKNOWN {reference.source} {reference.where}: {reference.identity}" + (f" :: {reference.clause_id}" if reference.clause_id else ""))
    for finding in findings:
        print(f"REVIEW {finding}")
    print(f"identities {len(identities)}; references {len(references)}; unknown references {len(unknown)}; "
          f"inconsistencies to review {len(findings)}")
    return 1 if unknown else 0


# --------------------------------------------------------------------------- report
def write_clause_csv(path: Path, identities, index) -> None:
    """One row per obligation: a clause of a split identity, or the undivided identity itself."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["identity", "clause_id", "scope", "admitted", "effect_scope", "source_file",
                         "conformance_references", "test_references"])
        for record in identities:
            rows = [(c.clause_id, c.scope, index.get(c.key, set())) for c in record.clauses] or [
                ("", "YES" if record.admitted else "NO", references_of(index, record.identity))]
            for clause_id, scope, refs in rows:
                writer.writerow([
                    record.identity, clause_id, scope, record.admitted, record.effect_scope or "", record.source_file,
                    sum(1 for r in refs if r.startswith("conformance:")), sum(1 for r in refs if r.startswith("test:")),
                ])


def rule_rows(root: Path, by_identity, index):
    """One row per classified effect of the band rules and catalogue skills."""
    rows = []

    def emit(collection, owner, path, rule):
        runtime = rule.get("runtime") or {}
        for effect in runtime.get("effects") or ():
            identity = f"rule/{collection}/{owner}/{rule['id']}/{effect['id']}"
            binding = effect.get("binding") or {}
            record = by_identity[identity]
            covered, total = covered_count(record, index)
            rows.append({
                "identity": identity, "kind": "rule", "collection": collection, "owner": owner,
                "record_id": rule["id"], "name": rule.get("name", ""), "effect_id": effect["id"],
                "scope": effect.get("scope", ""), "implemented": runtime.get("implemented", ""),
                "grant": runtime.get("grant", ""), "binding_kind": binding.get("kind", ""),
                "binding_id": binding.get("id", ""), "reason": effect.get("reason", ""),
                "clauses": len(record.clauses), "obligations": total, "covered": covered,
                "status": identity_status(record, index),
                "source_file": path.relative_to(root).as_posix(),
            })

    for path in sorted((root / "bands").glob("*/*/special-rules.yaml")):
        for rule in read_yaml(path).get("rules") or ():
            emit(path.parent.parent.name, path.parent.name, path, rule)
    for path in sorted((root / "catalog/skills").glob("*.yaml")):
        for skill in read_yaml(path).get("skills") or ():
            emit("catalog", path.stem, path, skill)
    return rows


def record_rows(root: Path, by_identity, index):
    """One row per core rule, mechanic and item."""
    rows = []

    def emit(identity, kind, record, path, **extra):
        entry = by_identity[identity]
        covered, total = covered_count(entry, index)
        rows.append({
            "identity": identity, "kind": kind, "collection": "", "owner": "", "record_id": record["id"],
            "name": record.get("name", ""), "effect_id": "", "scope": extra.pop("scope", "YES"),
            "implemented": extra.pop("implemented", ""), "grant": "", "binding_kind": "",
            "binding_id": extra.pop("binding_id", ""), "reason": "",
            "clauses": len(entry.clauses), "obligations": total, "covered": covered,
            "status": identity_status(entry, index),
            "source_file": path.relative_to(root).as_posix(),
        })

    core = root / "catalog/rules/core-combat.yaml"
    for rule in read_yaml(core).get("rules") or ():
        emit(f"core/{rule['id']}", "core", rule, core)
    mechanics = root / "catalog/mechanics/close-combat.yaml"
    catalogue = read_yaml(mechanics)
    for family in ("weapons", "armours", "defences", "materials", "preparations", "poisons", "skills"):
        for record in catalogue.get(family) or ():
            emit(f"mechanic/{record['id']}", "mechanic", record, mechanics,
                 binding_id=record.get("engine_option", ""))
    for path in sorted((root / "catalog/items").glob("*.yaml")):
        for item in read_yaml(path).get("items") or ():
            emit(f"item/{item['id']}", "item", item, path, implemented=item.get("combat_status", ""),
                 binding_id=item.get("mechanic_id", ""))
    return rows


REPORT_COLUMNS = ["identity", "kind", "collection", "owner", "record_id", "name", "effect_id", "scope",
                  "implemented", "grant", "binding_kind", "binding_id", "reason", "clauses",
                  "obligations", "covered", "status", "source_file"]


def command_report(args) -> int:
    root = knowledge_root()
    identities = load_identities()
    index = coverage_index(all_references())
    by_identity = {i.identity: i for i in identities}
    output = Path(args.output) if args.output else ROOT / "outputs/audit"
    output.mkdir(parents=True, exist_ok=True)
    inventory = output / "rules-inventory.csv"
    with inventory.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        writer.writerows(record_rows(root, by_identity, index) + rule_rows(root, by_identity, index))
    coverage = output / "clause-coverage.csv"
    write_clause_csv(coverage, identities, index)
    summary = output / "summary.json"
    admitted = [i for i in identities if i.admitted]
    totals = [covered_count(i, index) for i in admitted]
    summary.write_text(json.dumps({
        "identities": len(identities), "admitted_identities": len(admitted),
        "obligations": sum(t for _, t in totals), "covered_obligations": sum(c for c, _ in totals),
        "inventory_digest": inventory_digest(identities),
    }, indent=2) + "\n", encoding="utf-8")
    for path in (inventory, coverage, summary):
        print(path.resolve())
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command")
    inventory = commands.add_parser("inventory", help="identity counts by kind, with the clauses that split them")
    inventory.add_argument("--csv", metavar="PATH", help="also write the complete obligation table")
    inventory.set_defaults(handler=command_inventory)
    coverage = commands.add_parser("coverage", help="declared conformance-scenario and test-marker coverage of the admitted identities")
    coverage.add_argument("--pending", action="store_true", help="list admitted obligations nobody covers")
    coverage.add_argument("--identity", metavar="ID", help="show one identity's clauses and references")
    coverage.add_argument("--kind", action="append", choices=IDENTITY_KINDS, help="restrict to identity kinds")
    coverage.add_argument("--limit", type=int, default=50, help="pending rows to print (0 = all)")
    coverage.set_defaults(handler=command_coverage)
    check = commands.add_parser("check", help="unknown references and inconsistencies; exit 1 on an unknown reference")
    check.set_defaults(handler=command_check)
    report = commands.add_parser("report", help="write rules-inventory.csv, clause-coverage.csv and summary.json")
    report.add_argument("--output", metavar="DIR", help="destination directory (default outputs/audit)")
    report.set_defaults(handler=command_report)
    args = parser.parse_args(argv)
    if not args.command:
        args = parser.parse_args(["inventory"])
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())

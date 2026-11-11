"""Generate empty E2E authoring files for admitted identities without importing combat.

Run from any directory: python /path/to/generate_skeletons.py [--dry-run|--check].
Existing files are never overwritten.  The admitted identities and the clauses
they declare come from the knowledge base itself (``mordheim_knowledge.clauses``):
core rules, mechanics the runtime scope keeps and ``YES`` rule effects.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import re
import sys

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "packages/python/knowledge"))

from mordheim_knowledge.clauses import Identity, load_identities  # noqa: E402

KNOWLEDGE_ROOT = ROOT / "sources/knowledge"
CASES = Path(__file__).parent / "cases"
FOLDERS = {"core": "core", "mechanic": "mechanics", "rule": "grants"}
SAFE_YAML_LOADER = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def read_definitions(knowledge_root: Path) -> dict[str, Identity]:
    """Admitted ``core/``, ``mechanic/`` and ``rule/`` identities, by identity."""
    load_identities.cache_clear()
    return {
        record.identity: record for record in load_identities(knowledge_root)
        if record.admitted and record.kind in FOLDERS
    }


def declared_ids(knowledge_root: Path) -> set[str]:
    """Every identity the knowledge base declares, admitted or not."""
    return {record.identity for record in load_identities(knowledge_root)}


def relative_path(identity: str) -> Path:
    """Keep full IDs in headers, with short, collision-checked Windows filenames."""
    kind, tail = identity.split("/", 1)
    stem = re.sub(r"[^a-z0-9._-]+", "--", tail.lower()).strip(".-") or "identity"
    reserved = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)),
                *(f"lpt{i}" for i in range(1, 10))}
    if kind == "rule" or stem != tail or len(stem) > 90 or stem.split(".")[0] in reserved:
        suffix = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:12]
        stem = f"{stem[:72].rstrip('.-')}--{suffix}"
    return Path(FOLDERS[kind]) / f"{stem}.yaml"


def render(record: Identity) -> str:
    lines = [
        "# E2E authoring scaffold; generated comments, manually authored scenarios.",
        f"# audit_id: {record.identity}",
        "# authoring_status: TODO",
        "# execution_status: UNEXECUTED (this scaffold has no behavioral result)",
        "#",
        "# Derive inputs and expectations from rule text and accepted rulings.",
        "# Do not derive them from the engine or execute combat during authoring.",
        "# REVIEWED requires semantic review; covers labels alone are insufficient.",
        "# Preserve audit_id when filling this file.",
        "# Governing rulings: docs/decisions/design-rulings.md",
        f"# Record: sources/knowledge/{record.source_file}",
    ]
    if not record.clauses:
        lines.append("# TODO: Review the rule and author all required scenarios.")
    for clause in sorted(record.clauses, key=lambda clause: (not clause.admitted, clause.clause_id)):
        lines.extend(["#", f"# Clause: {clause.clause_id} (scope: {clause.scope})"])
        if clause.admitted:
            lines.append(f"# TODO[{clause.clause_id}]: Review the rule and author all required scenarios.")
        else:
            lines.append("# Outside the admitted clause scope; retained for context, not a test TODO.")
    lines.extend(["", "[]  # Empty scenario list: this file contributes no test or coverage.", ""])
    return "\n".join(lines)


def header(path: Path) -> dict[str, str]:
    metadata = {}
    with path.open(encoding="utf-8") as handle:
        for _ in range(12):
            line = handle.readline()
            match = re.match(r"# (audit_id): (.+)\s*$", line)
            if match:
                metadata[match[1]] = match[2].strip()
    return metadata


def declared_identities(path: Path) -> set[str]:
    """Identities the scenarios of one corpus file declare (an unreadable file declares none)."""
    try:
        scenarios = yaml.load(path.read_text(encoding="utf-8"), Loader=SAFE_YAML_LOADER)
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return set()
    if not isinstance(scenarios, list):
        return set()
    return {str(s["audit_id"]) for s in scenarios if isinstance(s, dict) and s.get("audit_id")}


def generate(output: Path, knowledge_root: Path, *, check: bool = False, dry_run: bool = False) -> dict:
    definitions = read_definitions(knowledge_root)
    targets = {}
    for identity in definitions:
        key = relative_path(identity).as_posix().casefold()
        if key in targets:
            raise ValueError(f"filename collision: {identity} and {targets[key]}")
        targets[key] = identity
    result = {"identities": len(definitions), "created": 0, "preserved": 0,
              "missing": [], "unexpected": []}
    present: set[str] = set()
    known = declared_ids(knowledge_root)
    for path in sorted(output.rglob("*.yaml")) if output.exists() else []:
        identity = header(path).get("audit_id")
        if identity is not None:
            present.add(identity)
            # A scaffold of a declared identity the runtime does not admit stays
            # (its scenarios document a NO/LATER effect); one the knowledge base
            # no longer declares, or one that moved from its derived path, is retired.
            if identity not in known or path.relative_to(output) != relative_path(identity):
                result["unexpected"].append(path.relative_to(output).as_posix())
        present |= declared_identities(path)
    for identity, record in definitions.items():
        if identity in present:
            result["preserved"] += 1
            continue
        path = output / relative_path(identity)
        if check or dry_run:
            result["missing"].append(path.relative_to(output).as_posix())
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(render(record))
        except FileExistsError:
            result["unexpected"].append(f"{path.relative_to(output).as_posix()} (created concurrently)")
        else:
            result["created"] += 1
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=CASES)
    parser.add_argument("--knowledge-root", type=Path, default=KNOWLEDGE_ROOT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Fail on missing or retired scaffolds; write nothing.")
    mode.add_argument("--dry-run", action="store_true", help="Preview generation; write nothing.")
    args = parser.parse_args(argv)
    try:
        result = generate(args.output_dir, args.knowledge_root, check=args.check, dry_run=args.dry_run)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Admitted IDs: {result['identities']}; created: {result['created']}; "
          f"existing files preserved: {result['preserved']}.")
    for name in ("missing", "unexpected"):
        paths = result[name]
        print(f"{name}: {len(paths)}")
        for path in paths[:10]:
            print(f"  {path}")
        if len(paths) > 10:
            print(f"  ... {len(paths) - 10} more")
    return int(bool(result["unexpected"] or args.check and result["missing"]))


if __name__ == "__main__":
    raise SystemExit(main())

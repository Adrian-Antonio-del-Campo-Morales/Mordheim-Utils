"""Generate source-linked, empty E2E authoring files without importing combat.

Run from any directory: python /path/to/generate_skeletons.py [--dry-run|--check].
Existing files are never overwritten, even when their source snapshot is stale.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
REGISTER = ROOT / "sources/knowledge/verification/clause-contracts.csv"
KNOWLEDGE_ROOT = ROOT / "sources/knowledge"
CASES = Path(__file__).parent / "cases"
FOLDERS = {"core": "core", "mechanic": "mechanics", "rule": "grants"}
REQUIRED_FIELDS = (
    "id", "clause_id", "clause_scope", "clause_text",
    "semantic_contract", "pending", "source_file", "source_fingerprint",
)
CONTEXT_FIELDS = ("effect_id", "relation", "parameters", "conditions", "verification", "notes")


def read_definitions(register: Path) -> dict[str, list[dict[str, str]]]:
    """Use the register's explicit scope decisions; never infer rule semantics."""
    with register.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = set(REQUIRED_FIELDS) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{register}: missing columns {sorted(missing)}")
        rows = []
        for number, raw in enumerate(reader, start=2):
            if any(raw[field] is None for field in REQUIRED_FIELDS):
                raise ValueError(f"{register}:{number}: incomplete row")
            row = {field: raw.get(field) or "" for field in REQUIRED_FIELDS + CONTEXT_FIELDS}
            if not row["id"] or not row["clause_id"]:
                raise ValueError(f"{register}:{number}: empty identity or clause")
            if any("\n" in row[field] or "\r" in row[field]
                   for field in ("id", "clause_id")):
                raise ValueError(f"{register}:{number}: multiline identity or clause")
            rows.append(row)
    admitted = {
        row["id"] for row in rows
        if row["clause_scope"] == "YES" and row["id"].startswith(tuple(f"{kind}/" for kind in FOLDERS))
    }
    definitions = {identity: [] for identity in sorted(admitted)}
    seen = set()
    for row in rows:
        identity = row["id"]
        if identity not in definitions:
            continue
        key = (identity, row["clause_id"])
        if key in seen:
            raise ValueError(f"{register}: duplicate identity/clause {key}")
        seen.add(key)
        definitions[identity].append(row)
    for clauses in definitions.values():
        clauses.sort(key=lambda row: (row["clause_scope"] != "YES", row["clause_id"]))
    return definitions


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


def source_hashes(definitions, knowledge_root: Path) -> dict[str, str]:
    root = knowledge_root.resolve()
    hashes = {}
    for clauses in definitions.values():
        for row in clauses:
            source = row["source_file"]
            if source in hashes:
                continue
            path = (root / source).resolve()
            if not source or not path.is_relative_to(root):
                raise ValueError(f"source_file escapes the knowledge root: {source!r}")
            hashes[source] = (hashlib.sha256(path.read_bytes()).hexdigest()
                              if path.is_file() else "MISSING")
    return hashes


def fingerprint(clauses, hashes) -> str:
    snapshot = {"format": 1, "clauses": clauses,
                "current_sources": {row["source_file"]: hashes[row["source_file"]]
                                    for row in clauses}}
    payload = json.dumps(snapshot, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _comment(lines, label, value):
    lines.append(f"# {label}:")
    lines.extend(f"#   {line}" for line in (value or "(not recorded)").splitlines())


def render(identity, clauses, hashes, register: Path = REGISTER) -> str:
    register = register.resolve()
    register_label = register.relative_to(ROOT).as_posix() if register.is_relative_to(ROOT) else str(register)
    lines = [
        "# E2E authoring scaffold; generated comments, manually authored scenarios.",
        f"# audit_id: {identity}",
        f"# scaffold_fingerprint: {fingerprint(clauses, hashes)}",
        "# authoring_status: TODO",
        "# execution_status: UNEXECUTED (this scaffold has no behavioral result)",
        "#",
        "# Derive inputs and expectations from rule text and accepted rulings.",
        "# Do not derive them from the engine or execute combat during authoring.",
        "# REVIEWED requires semantic review; covers labels alone are insufficient.",
        "# Preserve audit_id and scaffold_fingerprint when filling this file.",
        "# Governing rulings: docs/decisions/design-rulings.md",
        f"# Generated from: {register_label}",
    ]
    for row in clauses:
        lines.extend(["#", f"# Clause: {row['clause_id']} (scope: {row['clause_scope']})"])
        if row["clause_scope"] == "YES":
            lines.append(f"# TODO[{row['clause_id']}]: Review the rule and author all required scenarios.")
        else:
            lines.append("# Outside the admitted clause scope; retained for context, not a test TODO.")
        for field in ("id", "pending", "source_file", "source_fingerprint"):
            _comment(lines, field, row[field])
        current = hashes[row["source_file"]]
        _comment(lines, "source_sha256_at_generation", current)
        if current == "MISSING":
            lines.append("# TODO[source-review]: The registered source file is missing.")
        _comment(lines, "Printed rule text", row["clause_text"])
        _comment(lines, "Semantic contract (check pending.review before treating as accepted)",
                 row["semantic_contract"])
        for field in CONTEXT_FIELDS:
            _comment(lines, "Register notes (context only, not behavioral authority)"
                     if field == "notes" else field, row[field])
    lines.extend(["", "[]  # Empty scenario list: this file contributes no test or coverage.", ""])
    return "\n".join(lines)


def header(path: Path) -> dict[str, str]:
    metadata = {}
    with path.open(encoding="utf-8") as handle:
        for _ in range(12):
            line = handle.readline()
            match = re.match(r"# (audit_id|scaffold_fingerprint): (.+)\s*$", line)
            if match:
                metadata[match[1]] = match[2].strip()
    return metadata


def generate(register: Path, output: Path, knowledge_root: Path,
             *, check: bool = False, dry_run: bool = False) -> dict:
    definitions = read_definitions(register)
    hashes = source_hashes(definitions, knowledge_root)
    targets = {}
    for identity in definitions:
        relative = relative_path(identity)
        key = relative.as_posix().casefold()
        if key in targets:
            raise ValueError(f"filename collision: {identity} and {targets[key]}")
        targets[key] = identity
    result = {"identities": len(definitions), "created": 0, "preserved": 0,
              "missing": [], "stale": [], "unexpected": []}
    for path in sorted(output.rglob("*.yaml")):
        metadata = header(path)
        identity = metadata.get("audit_id")
        if "scaffold_fingerprint" in metadata and (
                identity not in definitions or path.relative_to(output) != relative_path(identity)):
            result["unexpected"].append(path.relative_to(output).as_posix())
    for identity, clauses in definitions.items():
        path = output / relative_path(identity)
        if path.exists():
            result["preserved"] += 1
            metadata = header(path)
            if (metadata.get("audit_id") != identity or
                    metadata.get("scaffold_fingerprint") != fingerprint(clauses, hashes)):
                result["stale"].append(path.relative_to(output).as_posix())
            continue
        if check or dry_run:
            result["missing"].append(path.relative_to(output).as_posix())
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open("x", encoding="utf-8", newline="\n") as handle:
                handle.write(render(identity, clauses, hashes, register))
        except FileExistsError:
            result["stale"].append(f"{path.relative_to(output).as_posix()} (created concurrently)")
        else:
            result["created"] += 1
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", type=Path, default=REGISTER)
    parser.add_argument("--output-dir", type=Path, default=CASES)
    parser.add_argument("--knowledge-root", type=Path, default=KNOWLEDGE_ROOT)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Fail on missing/stale scaffolds; write nothing.")
    mode.add_argument("--dry-run", action="store_true", help="Preview generation; write nothing.")
    args = parser.parse_args(argv)
    try:
        result = generate(args.register, args.output_dir, args.knowledge_root,
                          check=args.check, dry_run=args.dry_run)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(f"Admitted IDs: {result['identities']}; created: {result['created']}; "
          f"existing files preserved: {result['preserved']}.")
    for name in ("missing", "stale", "unexpected"):
        paths = result[name]
        print(f"{name}: {len(paths)}")
        for path in paths[:10]:
            print(f"  {path}")
        if len(paths) > 10:
            print(f"  ... {len(paths) - 10} more")
    return int(bool(result["stale"] or result["unexpected"] or args.check and result["missing"]))


if __name__ == "__main__":
    raise SystemExit(main())

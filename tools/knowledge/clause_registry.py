"""Small, guarded query/prepare/apply interface for the maintained T13 register."""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV = ROOT / "sources/knowledge/verification/clause-contracts.csv"
import clause_registry_validation as validator

PROTECTED = {"id", "clause_id", "source_file", "source_fingerprint", "clause_text"}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(raw):
    errors = validator.check(raw.replace(b"\r\n", b"\n"), {})
    if errors:
        raise ValueError("Invalid CSV:\n" + "\n".join(errors))
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8"), newline="")))
    if len(rows) != 4556:
        raise ValueError(f"Expected 4556 clauses, found {len(rows)}")
    return rows


def key(row):
    return row["id"], row["clause_id"]


def json_cell(field, value):
    if field in validator.OBJ_FIELDS + validator.ARR_FIELDS:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def replace_note_references(notes, replacements):
    if not isinstance(replacements, dict):
        raise ValueError("Note reference replacements must be an object")
    for old, new in replacements.items():
        if not isinstance(old, str) or "completed.md" not in old or old not in notes:
            raise ValueError("Expected existing delivery reference in notes")
        if not isinstance(new, str):
            raise ValueError("Replacement reference must be a string")
        notes = notes.replace(old, new)
    return notes


def prepare(path, requests):
    raw = path.read_bytes()
    rows = {key(row): row for row in read(raw)}
    changes, seen = [], set()
    if not isinstance(requests, list) or not requests:
        raise ValueError("Changes must be a nonempty JSON array")
    for request in requests:
        if set(request) - {"id", "clause_id", "set", "append_notes", "replace_note_references"}:
            raise ValueError("Unknown change properties")
        identity = key(request)
        if identity in seen:
            raise ValueError(f"Duplicate change: {identity}")
        seen.add(identity)
        before = rows[identity]
        after = dict(before)
        note_references = request.get("replace_note_references", {})
        after["notes"] = replace_note_references(before["notes"], note_references)
        for field, value in request.get("set", {}).items():
            if field not in validator.FIELDS or field in PROTECTED or field == "notes":
                raise ValueError(f"Cannot replace field: {field}; use append_notes for notes")
            after[field] = json_cell(field, value)
        note = request.get("append_notes", "")
        if not isinstance(note, str):
            raise ValueError("append_notes must be a string")
        if note:
            after["notes"] += ("\n" if after["notes"] else "") + note
        if after != before:
            change = {"before": before, "after": after}
            if note_references:
                change["replace_note_references"] = note_references
            changes.append(change)
    package = {"csv": str(path.resolve()), "sha256": digest(raw), "changes": changes}
    candidate(raw, package)
    return package


def candidate(raw, package):
    if digest(raw) != package["sha256"]:
        raise ValueError("Concurrent change: CSV differs from prepared snapshot; prepare again")
    rows = read(raw)
    replacements = {}
    index = {key(row): row for row in rows}
    for change in package["changes"]:
        before, after = change["before"], change["after"]
        identity = key(before)
        if identity in replacements or index.get(identity) != before:
            raise ValueError(f"Duplicate or mismatched original: {identity}")
        if set(after) != set(validator.FIELDS):
            raise ValueError("Changed row has unexpected columns")
        if any(before[f] != after[f] for f in PROTECTED):
            raise ValueError("Protected source fields changed")
        expected_notes = replace_note_references(before["notes"], change.get("replace_note_references", {}))
        if after["notes"] != expected_notes and not after["notes"].startswith(
                expected_notes + ("\n" if expected_notes else "")):
            raise ValueError("Existing notes must be preserved; only append notes")
        replacements[identity] = after
    # Preserve untouched records byte-for-byte, including multiline quoted cells.
    lines = io.StringIO(raw.decode("utf-8"), newline="").readlines()
    reader = csv.reader(io.StringIO(raw.decode("utf-8"), newline=""))
    next(reader)
    end = reader.line_num
    chunks = ["".join(lines[:end])]
    for row in rows:
        next(reader)
        span = "".join(lines[end:reader.line_num])
        end = reader.line_num
        if key(row) in replacements:
            out = io.StringIO(newline="")
            csv.writer(out, lineterminator="\r\n" if lines[0].endswith("\r\n") else "\n").writerow(
                [replacements[key(row)][f] for f in validator.FIELDS])
            span = out.getvalue()
        chunks.append(span)
    result = "".join(chunks).encode("utf-8")
    actual = read(result)
    expected = [replacements.get(key(row), row) for row in rows]
    if actual != expected:
        raise ValueError("Conservation check failed")
    errors = validator.check(result.replace(b"\r\n", b"\n"), index)
    if errors:
        raise ValueError("\n".join(errors))
    return result


def show(package):
    changes = []
    for change in package["changes"]:
        before, after = change["before"], change["after"]
        changes.append({"id": before["id"], "clause_id": before["clause_id"],
                        "fields": {f: {"before": before[f], "after": after[f]}
                                   for f in validator.FIELDS if before[f] != after[f]}})
    print(json.dumps(changes, ensure_ascii=False, indent=2))


def apply(path, package, write=False):
    if str(path.resolve()) != package["csv"]:
        raise ValueError("Package belongs to another CSV")
    if not write:
        candidate(path.read_bytes(), package)
        show(package)
        return
    # Cooperative lock: all authorized writers must use this utility.
    lock = path.with_suffix(path.suffix + ".lock")
    handle = lock.open("x")
    try:
        raw = path.read_bytes()
        result = candidate(raw, package)
        if not package["changes"]:
            print("No changes")
            return
        backup = Path(tempfile.mkdtemp(prefix="t13-csv-")) / path.name
        backup.write_bytes(raw)
        print(f"Backup: {backup}", flush=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as out:
                temp_path = Path(out.name)
                out.write(result)
                out.flush()
                os.fsync(out.fileno())
            if path.read_bytes() != raw:
                raise ValueError("Concurrent change: CSV not written")
            os.replace(temp_path, path)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
        print(f"Applied {len(package['changes'])} clause changes")
    finally:
        handle.close()
        lock.unlink()



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    commands = parser.add_subparsers(dest="command", required=True)
    query = commands.add_parser("query")
    for field in ("id", "clause-id", "source", "consumer", "work", "review"):
        query.add_argument("--" + field)
    query.add_argument("--pending", action="store_true")
    query.add_argument("--limit", type=int, default=10)
    query.add_argument("--fields", default="id,clause_id,clause_text,semantic_contract,consumer,pending,notes")
    prep = commands.add_parser("prepare")
    prep.add_argument("changes", type=Path)
    prep.add_argument("--out", type=Path, required=True)
    app = commands.add_parser("apply")
    app.add_argument("package", type=Path)
    app.add_argument("--write", action="store_true", help="Without this flag, only validate and preview")
    args = parser.parse_args()
    try:
        if args.command == "query":
            fields = args.fields.split(",")
            if set(fields) - set(validator.FIELDS) or args.limit < 1:
                raise ValueError("Invalid fields or limit")
            matched = []
            for row in read(args.csv.read_bytes()):
                pending = json.loads(row["pending"])
                if any(value is not None and row[field] != value for field, value in
                       (("id", args.id), ("clause_id", args.clause_id))):
                    continue
                if any(value and value not in row[field] for field, value in
                       (("source_file", args.source), ("consumer", args.consumer))):
                    continue
                if args.work and pending.get("work", "none") != args.work:
                    continue
                if args.review and pending.get("review", "reviewed") != args.review:
                    continue
                if args.pending and not (pending.get("work", "none") != "none" or
                                        pending.get("review", "reviewed") != "reviewed" or
                                        pending.get("requires")):
                    continue
                matched.append({f: row[f] for f in fields})
                if len(matched) == args.limit:
                    break
            print(json.dumps(matched, ensure_ascii=False, indent=2))
        elif args.command == "prepare":
            package = prepare(args.csv, json.loads(args.changes.read_text(encoding="utf-8")))
            with args.out.open("x", encoding="utf-8") as out:
                json.dump(package, out, ensure_ascii=False, indent=2)
            show(package)
            print(f"Prepared: {args.out}")
        else:
            apply(args.csv, json.loads(args.package.read_text(encoding="utf-8")), args.write)
    except (ValueError, KeyError, OSError) as exc:
        parser.exit(1, f"Rejected: {exc}\n")


if __name__ == "__main__":
    main()

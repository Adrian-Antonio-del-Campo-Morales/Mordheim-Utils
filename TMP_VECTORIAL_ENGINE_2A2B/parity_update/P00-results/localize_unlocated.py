"""P00 read-only localization of the admitted keys with an empty ``consumer``.

An empty ``consumer`` list in the register does not prove that a clause has no
implementation: it only proves that the register does not name one.  This probe
looks for the implementation elsewhere, using the register's own evidence
columns first (``verification``, ``notes``, ``pending``) and the repository
second (exact ``id``/``clause_id``/``effect_id`` mentions).

Outputs (P00-results/):
- ``unlocated-localization.csv``: one row per key with the evidence found and a
  proposed disposition for the coordinator.
- ``unlocated-keys.txt``: aggregate counts and the keys with no trace at all.

The proposal is evidence, never a status update: the CSV register is untouched
and no key becomes ``verified``.

Run from the repository root:

    python -X utf8 TMP_VECTORIAL_ENGINE_2A2B/parity_update/P00-results/localize_unlocated.py
"""
from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESULTS = Path(__file__).resolve().parent
REGISTER = ROOT / "sources/knowledge/verification/clause-contracts.csv"

#: Directories scanned for exact mentions.  ``TMP_VECTORIAL_ENGINE_2A2B`` is
#: deliberately excluded: this deliverable must not cite itself as evidence.
SCAN_ROOTS = (
    "packages/python",
    "apps",
    "tools",
    "tests/specs",
    "tests/E2E",
    "tests/python",
    "sources/knowledge",
    "docs/reference",
)
SCAN_SUFFIXES = {".py", ".yaml", ".yml", ".json", ".csv", ".md"}
SKIP_PARTS = {"__pycache__", ".git", "node_modules", ".venv", "build", "dist"}
#: The register contains one row per key, so scanning it would "find" every
#: key in its own definition.  Self-mentions are not implementation evidence.
SKIP_FILES = {"sources/knowledge/verification/clause-contracts.csv"}

CODE_MARKERS = ("packages/python/", "apps/", "tools/")
TEST_MARKERS = ("tests/python/", "tests/E2E/", "tests/specs/")
KB_MARKERS = ("sources/knowledge/",)

#: Phrases the register itself uses to say "not implemented".  The probe keeps
#: them verbatim (first match) so the owner can read the source's own reason.
BLOCKED_MARKERS = (
    "blocked",
    "unimplemented",
    "cannot be wired",
    "cannot be expressed",
    "not representable",
    "no effect carries",
    "gap",
    "needs a new",
    "requires a new",
)


def read_unlocated() -> list[dict]:
    with REGISTER.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [row for row in rows
            if row["clause_scope"] == "YES" and not json.loads(row["consumer"])]


def _references(raw: str) -> list[str]:
    try:
        values = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [str(value) for value in values]


def classify_reference(reference: str) -> str:
    normalized = reference.replace("\\", "/")
    if any(marker in normalized for marker in CODE_MARKERS):
        return "code"
    if any(marker in normalized for marker in TEST_MARKERS):
        return "test"
    if any(marker in normalized for marker in KB_MARKERS):
        return "kb"
    return "other"


def _needle_pattern(keys: list[tuple[str, str, str]]) -> re.Pattern[str]:
    needles: set[str] = set()
    for identifier, clause_id, effect_id in keys:
        needles.add(identifier)
        needles.add(clause_id)
        if effect_id:
            needles.add(effect_id)
    ordered = sorted(needles, key=len, reverse=True)
    return re.compile("|".join(re.escape(needle) for needle in ordered))


def scan_repository(keys: list[tuple[str, str, str]]) -> dict[str, list[str]]:
    """Return {needle: ["relative/path:line", ...]} for exact mentions."""
    pattern = _needle_pattern(keys)
    hits: dict[str, list[str]] = defaultdict(list)
    for relative_root in SCAN_ROOTS:
        base = ROOT / relative_root
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
                continue
            if SKIP_PARTS.intersection(path.parts):
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if not pattern.search(text):
                continue
            relative = path.relative_to(ROOT).as_posix()
            if relative in SKIP_FILES:
                continue
            for line_number, line in enumerate(text.splitlines(), 1):
                for needle in pattern.findall(line):
                    hits[needle].append(f"{relative}:{line_number}")
    return hits


def proposed_class(references: list[str], strong: list[str], weak: list[str]) -> str:
    kinds = {classify_reference(reference) for reference in references}
    if "code" in kinds:
        return "implemented-in-code"
    if "test" in kinds:
        return "implemented-in-tests-only"
    if strong:
        return "mentioned-outside-code"
    if weak:
        return "clause-id-only-mention"
    return "no-trace"


def main() -> int:
    unlocated = read_unlocated()
    keys = [(row["id"], row["clause_id"], row["effect_id"]) for row in unlocated]
    hits = scan_repository(keys)

    rows = []
    for row in unlocated:
        references = _references(row["verification"])
        strong: list[str] = list(hits.get(row["id"], []))
        if row["effect_id"]:
            strong.extend(hits.get(row["effect_id"], []))
        weak = hits.get(row["clause_id"], [])
        notes = row["notes"] or ""
        lower = notes.lower()
        blocked = next((marker for marker in BLOCKED_MARKERS if marker in lower), "")
        rows.append({
            "id": row["id"],
            "clause_id": row["clause_id"],
            "effect_id": row["effect_id"],
            "relation": row["relation"],
            "verification_paths": len(references),
            "verification_code": sum(1 for reference in references
                                     if classify_reference(reference) == "code"),
            "verification_tests": sum(1 for reference in references
                                      if classify_reference(reference) == "test"),
            "verification_kb": sum(1 for reference in references
                                   if classify_reference(reference) == "kb"),
            "strong_mentions": len(strong),
            "clause_id_mentions": len(weak),
            "repository_example": (strong or weak or [""])[0],
            "blocked_marker": blocked,
            "proposed_class": proposed_class(references, strong, weak),
            "note_head": notes.splitlines()[0][:180] if notes else "",
        })

    out = RESULTS / "unlocated-localization.csv"
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    by_class = Counter(row["proposed_class"] for row in rows)
    blocked = sum(1 for row in rows if row["blocked_marker"])
    no_mentions = [row for row in rows if not row["repository_example"]]
    no_evidence = [row for row in rows
                   if not row["verification_paths"] and not row["repository_example"]]

    lines = [
        "admitted_with_empty_consumer=%d" % len(rows),
        "with_code_reference_in_verification=%d" % by_class["implemented-in-code"],
        "with_test_reference_only=%d" % by_class["implemented-in-tests-only"],
        "mentioned_outside_code=%d" % by_class["mentioned-outside-code"],
        "clause_id_only_mention=%d" % by_class["clause-id-only-mention"],
        "no_trace=%d" % by_class["no-trace"],
        "register_note_says_blocked_or_unimplemented=%d" % blocked,
        "with_no_repository_mention=%d" % len(no_mentions),
        "with_no_evidence_at_all=%d" % len(no_evidence),
        "",
        "Disposition proposal: every key stays pending localization.  A code",
        "reference is a lead for the owner, not proof of parity coverage.",
        "",
        "Keys with no code reference and no test reference (first 40):",
    ]
    for row in rows:
        if row["proposed_class"] in {"mentioned-outside-code", "clause-id-only-mention", "no-trace"}:
            example = row["repository_example"] or "-"
            lines.append(f"  {row['id']}::{row['clause_id']}  [{row['proposed_class']}] {example}")
    lines.append("")
    lines.append("Keys with no trace anywhere (id:clause):")
    for row in no_evidence:
        lines.append(f"  {row['id']}::{row['clause_id']}")
    text = "\n".join(lines) + "\n"
    (RESULTS / "unlocated-keys.txt").write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())

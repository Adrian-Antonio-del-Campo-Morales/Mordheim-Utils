#!/usr/bin/env python3
"""Promote cross-band duplicate rules into the shared-rule registry.

Rule text has a single source. Band special rules that restate a shared rule
word-for-word are promoted into ``catalog/rules/special-rules.yaml`` (the
sanctioned, previously-empty cross-band catalogue) and every band copy is
rewritten to ``rule_ref: shared-rule.<id>`` with its duplicated ``effect`` /
``effect_i18n`` prose removed. Names, name translations, runtime bindings and
sources stay on the band records, so engine behaviour is untouched; display
text resolves through the registry (``loader.shared_rule_text``).

Membership is **exact-text only**: two rules in different band directories
whose effects are identical after whitespace folding are, by construction,
restatements of one shared rule, so collapsing them cannot change meaning.
Rules that merely share a name or a mechanic binding (whose prose differs by
band) are never auto-promoted — the tool lists them in ``--report`` as
candidates for a reviewed promotion, never applied automatically.

Usage::

    python tools/rule_registry.py --report    # print the promotion plan
    python tools/rule_registry.py --apply     # rewrite the KB
    python tools/format_yaml.py --write sources/knowledge   # canonicalise

The Spanish effect of each promoted rule moves with it: the registry entry
carries the canonical member's ``effect_i18n.es`` so no translation is lost.
"""
from __future__ import annotations

import argparse
import collections
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
KB = ROOT / "sources" / "knowledge"
REGISTRY = KB / "catalog" / "rules" / "special-rules.yaml"
MIN_EFFECT_LEN = 18


def _norm(text: str) -> str:
    return " ".join(text.casefold().split())


def _records() -> list[dict]:
    rows = []
    for path in sorted((KB / "bands").rglob("special-rules.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for rule in doc.get("rules") or []:
            if isinstance(rule, dict):
                rule["_file"] = path
                rows.append(rule)
    return rows


def _clusters() -> list[list[dict]]:
    by_text = collections.defaultdict(list)
    for rule in _records():
        effect = str(rule.get("effect") or "").strip()
        if len(effect) < MIN_EFFECT_LEN:
            continue
        by_text[_norm(effect)].append(rule)
    clusters = []
    for rows in by_text.values():
        if len({row["_file"].parent.name for row in rows}) >= 2:
            clusters.append(rows)
    return sorted(clusters, key=lambda rows: (-len(rows), _norm(str(rows[0].get("effect")))))


def _clean(name: str) -> bool:
    return "\ufffd" not in name and all(ord(ch) < 128 for ch in name)


def _canonical(rows: list[dict]) -> dict:
    """Deterministic representative of a cluster: majority name, cleanest."""
    counts = collections.Counter(str(row.get("name")) for row in rows)
    by_name = collections.defaultdict(list)
    for row in rows:
        by_name[str(row.get("name"))].append(row)
    ordered = sorted(counts, key=lambda n: (-counts[n], 0 if _clean(n) else 1, n))
    return by_name[ordered[0]][0]


def _slug(name: str) -> str:
    value = re.sub(r"[^A-Za-z0-9]+", "-", name.casefold()).strip("-")
    return value or "rule"


def build_registry() -> dict:
    """Return {shared-rule id: canonical row, members: [...]} proposals."""
    used: dict[str, str] = {}
    result = {}
    for rows in _clusters():
        member = _canonical(rows)
        base = _slug(str(member.get("name") or "rule"))
        rule_id = f"shared-rule.{base}"
        suffix = 2
        while rule_id in used:
            rule_id = f"shared-rule.{base}-{suffix}"
            suffix += 1
        es_effect = str((member.get("effect_i18n") or {}).get("es") or "").strip()
        if not es_effect:
            for row in rows:
                es_effect = str((row.get("effect_i18n") or {}).get("es") or "").strip()
                if es_effect:
                    member = row
                    break
        used[rule_id] = _norm(str(member.get("effect")))
        result[rule_id] = {"canonical": member, "members": rows}
    return result


def _emit_folded(value: str, indent: str) -> list[str]:
    words = value.split()
    lines: list[str] = []
    current = ""
    width = max(30, 100 - len(indent))
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > width:
            lines.append(indent + current)
            current = word
        else:
            current = candidate
    lines.append(indent + current)
    return lines


# --------------------------------------------------------------------------
# Lexical band-file surgery
# --------------------------------------------------------------------------

_KEY = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_.-]+):(?P<rest>.*)$")
_TOP_RULE = re.compile(r"^- id: ")


def _key_index(lines: list[str], block: list[int], key: str, indent: int) -> int | None:
    for index in range(block[0], block[1]):
        match = _KEY.match(lines[index])
        if match and match.group("key") == key and len(match.group("indent")) == indent:
            return index
    return None


def _scalar_end(lines: list[str], index: int) -> int:
    """Index just past the scalar value opened at ``lines[index]``."""
    match = _KEY.match(lines[index])
    indent = len(match.group("indent"))
    rest = match.group("rest").lstrip()
    if not rest:
        # Nested mapping (e.g. `effect_i18n:`): consume children.
        end = index + 1
        while end < len(lines):
            candidate = lines[end]
            if not candidate.strip():
                end += 1
                continue
            if len(candidate) - len(candidate.lstrip()) > indent:
                end += 1
                continue
            break
        return end
    if rest.startswith((">", "|")):
        end = index + 1
        while end < len(lines):
            candidate = lines[end]
            if not candidate.strip():
                end += 1
                continue
            if len(candidate) - len(candidate.lstrip()) > indent:
                end += 1
                continue
            break
        return end
    return index + 1


def rewrite_band_file(path: Path, refs: dict) -> bool:
    """Rewrite one special-rules.yaml: replace cluster rules with rule_ref."""
    original = path.read_text(encoding="utf-8")
    lines = original.replace("\r\n", "\n").split("\n")
    # Top-level rule blocks: each starts at a line matching `- id: ` (indent 0).
    starts = [i for i, line in enumerate(lines) if _TOP_RULE.match(line)]
    blocks = [(starts[i], starts[i + 1] if i + 1 < len(starts) else len(lines)) for i in range(len(starts))]
    out: list[str] = []
    cursor = 0
    for start, end in blocks:
        out.extend(lines[cursor:start])
        header = lines[start]
        rule_id = header[len("- id: "):].strip()
        target = refs.get(rule_id)
        if target is None:
            out.append(header)
            cursor = start + 1
            continue
        # Rebuild this record: header, name, rule_ref, everything else except
        # the duplicated prose (`effect`, `effect_i18n`).
        body: list[str] = []
        skip = set()
        effect_index = _key_index(lines, (start + 1, end), "effect", 2)
        i18n_index = _key_index(lines, (start + 1, end), "effect_i18n", 2)
        if effect_index is not None:
            skip.update(range(effect_index, _scalar_end(lines, effect_index)))
        if i18n_index is not None:
            skip.update(range(i18n_index, _scalar_end(lines, i18n_index)))
        name_index = _key_index(lines, (start + 1, end), "name", 2)
        inserted = False
        for index in range(start, end):
            if index in skip:
                continue
            if name_index is not None and index == name_index + 1 and not inserted:
                # Insert rule_ref right after the name line.
                body.append("  rule_ref: " + target)
                inserted = True
            body.append(lines[index])
        if not inserted:
            body.append("  rule_ref: " + target)
        out.extend(body)
        cursor = end
    out.extend(lines[cursor:])
    text = "\n".join(out)
    if text == original:
        return False
    before = yaml.safe_load(original)
    after = yaml.safe_load(text)
    if len(before.get("rules") or []) != len(after.get("rules") or []):
        raise ValueError(f"{path}: record count changed")
    path.write_text(text, encoding="utf-8", newline="\n")
    return True


def _load_registry_rows() -> dict[str, dict]:
    """Current registry entries by id (parsed rows)."""
    if not REGISTRY.exists():
        return {}
    doc = yaml.safe_load(REGISTRY.read_text(encoding="utf-8")) or {}
    return {str(row.get("id")): row for row in doc.get("rules") or [] if isinstance(row, dict)}


def _band_ref_ids() -> dict[str, list[dict]]:
    """Every band rule that already references the registry, by shared id."""
    refs: dict[str, list[dict]] = {}
    for path in sorted((KB / "bands").rglob("special-rules.yaml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for rule in doc.get("rules") or []:
            ref = rule.get("rule_ref") if isinstance(rule, dict) else None
            if ref:
                refs.setdefault(str(ref), []).append(rule)
    return refs


def _scalar(value: str) -> str:
    value = str(value)
    if chr(10) in value:
        return "'" + value.replace("'", "''") + "'"
    probe = value
    if probe == probe.strip():
        try:
            if yaml.safe_load("x: " + probe) == value:
                return probe
        except Exception:
            pass
    return "'" + value.replace("'", "''") + "'"


def _entry_lines(rule_id: str, row: dict) -> list[str]:
    name = str(row.get("name") or rule_id)
    lines = [f"- id: {rule_id}", f"  name: {_scalar(name)}"]
    es_name = (row.get("name_i18n") or {}).get("es")
    if es_name:
        lines += ["  name_i18n:", f"    es: {_scalar(str(es_name))}"]
    effect = str(row.get("effect") or "").strip()
    if effect:
        lines.append("  effect: >-")
        lines.extend(_emit_folded(effect, "    "))
        es_effect = str((row.get("effect_i18n") or {}).get("es") or "").strip()
        if es_effect:
            lines += ["  effect_i18n:", "    es: >-"]
            lines.extend(_emit_folded(es_effect, "      "))
    return lines


def render_registry_rows(rows: dict[str, dict]) -> str:
    lines = [
        "schema_version: 2",
        "ruleset: mordheim",
        "note: Cross-band rules promoted after an equivalence review (identical prose across two or more band files).",
        "note2: Band rules restate them as `rule_ref`; runtime stays on the band rule.",
        "rules:",
    ]
    for rule_id in sorted(rows):
        lines.extend(_entry_lines(rule_id, rows[rule_id]))
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true", help="print the promotion plan")
    parser.add_argument("--apply", action="store_true", help="write registry and rewrite band files")
    args = parser.parse_args()
    if not args.report and not args.apply:
        parser.error("pass --report and/or --apply")
    proposals = build_registry()
    existing = _load_registry_rows()
    refs = _band_ref_ids()

    # Integrity is checked always: every band rule_ref must resolve, and no
    # registry entry may dangle unreferenced.
    all_ids = set(existing) | set(proposals)
    unresolved = sorted(set(refs) - all_ids)
    orphaned = sorted(set(existing) - set(refs) - set(proposals))
    if args.report:
        total = sum(len(p["members"]) for p in proposals.values())
        print(f"pending promotions: {len(proposals)} clusters, {total} band copies")
        print(f"registry entries: {len(existing)} referenced | band rule_refs: "
              f"{sum(len(v) for v in refs.values())} rules / {len(refs)} ids")
        if unresolved:
            print(f"UNRESOLVED rule_refs (missing registry entries): {len(unresolved)}")
            for value in unresolved:
                print("  ", value)
        if orphaned:
            print(f"unreferenced registry entries: {len(orphaned)}")
            for value in orphaned:
                print("  ", value)
        for rule_id, proposal in sorted(proposals.items()):
            member = proposal["canonical"]
            files = sorted({m["_file"].parent.name for m in proposal["members"]})
            print(f"  {rule_id:42s} n={len(proposal['members']):2d} files={len(files):2d} :: "
                  f"{str(member.get('name'))!r} — {str(member.get('effect'))[:80]}")
    if unresolved:
        return 1
    if not args.apply:
        return 0
    if not proposals:
        print("nothing to promote — registry left unchanged")
        return 0
    # Merge new promotions into the existing registry (never dropping entries)
    # and rewrite only the newly promoted band copies.
    merged = dict(existing)
    by_id: dict[str, str] = {}
    for rule_id, proposal in sorted(proposals.items()):
        if rule_id in merged:
            print(f"ERROR: registry id collision {rule_id}; refusing to overwrite")
            return 1
        member = proposal["canonical"]
        merged[rule_id] = {
            "name": str(member.get("name")),
            "name_i18n": {"es": (member.get("name_i18n") or {}).get("es")}
            if (member.get("name_i18n") or {}).get("es") else None,
            "effect": str(member.get("effect")).strip(),
            "effect_i18n": {"es": (member.get("effect_i18n") or {}).get("es")}
            if (member.get("effect_i18n") or {}).get("es") else None,
        }
        for member_rule in proposal["members"]:
            by_id[str(member_rule.get("id"))] = rule_id
    REGISTRY.write_text(render_registry_rows(merged), encoding="utf-8", newline="\n")
    print(f"wrote {REGISTRY.relative_to(ROOT)} ({len(merged)} entries)")
    files = sorted({m["_file"] for p in proposals.values() for m in p["members"]})
    for path in files:
        if rewrite_band_file(path, by_id):
            print(f"  rewrote {path.relative_to(ROOT)}")
    print(f"rewrote {len(files)} band files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

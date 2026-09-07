import collections
import pathlib
import re
import subprocess
import sys

import yaml

KB = pathlib.Path("sources/knowledge")
BANDS = KB / "bands"
ROOT = KB.parents[1]  # repository root


def git_show(rel: str) -> str:
    out = subprocess.run(
        ["git", "show", "HEAD:" + rel.replace("\\", "/")],
        capture_output=True, cwd=ROOT, check=True)
    return out.stdout.decode("utf-8")


def norm(text: str) -> str:
    return " ".join(text.casefold().split())


# --- collect current refs -------------------------------------------------
refs = collections.defaultdict(list)          # shared id -> member rule records
for path in sorted(BANDS.rglob("special-rules.yaml")):
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for rule in doc.get("rules") or []:
        ref = rule.get("rule_ref")
        if ref:
            rule = dict(rule)
            rule["_file"] = path
            refs[str(ref)].append(rule)

# --- collect leftover translations for identical texts ---------------------
leftover_es = collections.defaultdict(list)   # norm(en) -> es strings
for path in sorted(BANDS.rglob("special-rules.yaml")):
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for rule in doc.get("rules") or []:
        eff = str(rule.get("effect") or "").strip()
        es = (rule.get("effect_i18n") or {}).get("es")
        if eff and isinstance(es, str) and es.strip():
            leftover_es[norm(eff)].append(es.strip())

# --- rebuild registry entries ----------------------------------------------
entries = []
missing_es = []
for shared_id in sorted(refs):
    members = refs[shared_id]
    names = collections.Counter(str(m.get("name")) for m in members)
    en_text = None
    for member in members:
        rel = member["_file"].relative_to(ROOT).as_posix()
        try:
            doc = yaml.safe_load(git_show(rel)) or {}
        except Exception as exc:
            print("  git fail", rel, exc)
            continue
        for rule in doc.get("rules") or []:
            if str(rule.get("id")) == member.get("id") and rule.get("effect"):
                en_text = str(rule["effect"]).strip()
                break
        if en_text:
            break
    if not en_text:
        print("NO-EN", shared_id)
        continue
    es_text = leftover_es.get(norm(en_text), [])
    es = es_text[0] if es_text else ""
    if not es:
        # fall back to the git HEAD translation of any member
        for member in members:
            rel = member["_file"].relative_to(ROOT).as_posix()
            try:
                doc = yaml.safe_load(git_show(rel)) or {}
            except Exception:
                continue
            for rule in doc.get("rules") or []:
                if str(rule.get("id")) == member.get("id"):
                    es = str((rule.get("effect_i18n") or {}).get("es") or "").strip()
                    break
            if es:
                break
    if not es:
        missing_es.append(shared_id)
    canonical_name = names.most_common(1)[0][0]
    es_name = ""
    for member in members:
        if str(member.get("name")) == canonical_name:
            es_name = str((member.get("name_i18n") or {}).get("es") or "").strip()
            break
    entries.append({
        "id": shared_id, "name": canonical_name, "name_es": es_name,
        "effect": en_text, "effect_es": es,
        "n": len(members),
    })

print("rebuilt entries:", len(entries), "of", len(refs), "distinct refs")
print("entries missing Spanish effect:", len(missing_es))


def scalar(value: str) -> str:
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


def emit_folded(value: str, indent: str) -> list:
    words = value.split()
    lines = []
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


out = [
    "schema_version: 2",
    "ruleset: mordheim",
    "note: Cross-band rules promoted after an equivalence review (identical prose across two or more band files).",
    "note2: Band rules restate them as `rule_ref`; runtime stays on the band rule.",
    "rules:",
]
for entry in entries:
    out.append(f"- id: {entry['id']}")
    out.append(f"  name: {scalar(entry['name'])}")
    if entry["name_es"]:
        out.append("  name_i18n:")
        out.append(f"    es: {scalar(entry['name_es'])}")
    out.append("  effect: >-")
    out.extend(emit_folded(entry["effect"], "    "))
    if entry["effect_es"]:
        out.append("  effect_i18n:")
        out.append("    es: >-")
        out.extend(emit_folded(entry["effect_es"], "      "))
out.append("")
path = KB / "catalog" / "rules" / "special-rules.yaml"
path.write_text("\n".join(out), encoding="utf-8", newline="\n")
print("wrote", len(entries), "entries to", path.relative_to(KB.parent))
for sid in missing_es:
    print("  NO-ES", sid)

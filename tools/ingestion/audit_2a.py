# -*- coding: utf-8 -*-
"""Cross-audit of sources/2A staging packages against extracted page texts.

Adapted from audit_2b.py. The 2A sources are mordheimer.net web pages (flat
text extraction with one checkmark line per skill-table cell), so the audit
is structured around that format:

  1. Profile names appear in the extracted text (case/diacritic-insensitive).
  2. Cost: "<N> gold crowns to hire" must appear near the profile name
     (any-agree semantics across occurrences).
  3. Experience: "<name> starts with <N> experience".
  4. Roster: "minimum of N models" / "maximum number of warriors ... N" /
     "500 gold crowns" (any-agree).
  5. Skill table: the skill-access columns are compared cell-by-cell against
     the skill table parsed from the cached source HTML page
     (build/cache/2a-sources/pages/<band>.html), which preserves column
     identity — unlike the flat-text extraction, whose one-checkmark-per-line
     layout makes column attribution ambiguous. Rows whose HTML name cannot
     be matched to a YAML profile are reported as warnings, not problems.
  5b. Statlines: every fighter block (div.fighter with an M/WS header table)
     on the cached page is matched to a YAML profile and its M..Ld values
     compared cell-by-cell. The source sometimes prints "*" for a random
     movement (documented in the profile notes as M: 0) — "*" matches any
     YAML value. Unmatched HTML rows are warnings, not problems.
  6. skill_access token sanity; henchmen have empty access.
  7. Every rule_id referenced by profiles exists in special-rules.yaml.
  8. Every equipment list referenced by profiles exists in equipment-access.yaml.

Outputs a JSON report.  Manual verification is still required for any flag:
text extraction is lossy.
"""
from __future__ import annotations

import html as html_mod
import json
import re
import sys
import unicodedata
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / "sources" / "2A" / "bands" / "mordheim"
TEXTS = ROOT / "build" / "cache" / "2a-sources" / "text"
PAGES = ROOT / "build" / "cache" / "2a-sources" / "pages"
MANIFEST = ROOT / "sources" / "2A" / "manifest.yaml"

# Source pages sometimes name a table row differently from the roster entry
# (e.g. Masters of Horror: roster "Wolfman", skill table "Werewolf").
ROW_ALIASES = {"wolfman": "werewolf", "petty thieves": "petty thief"}

VALID_SKILL_TOKENS = {
    "combat", "shooting", "academic", "strength", "speed", "special",
}

NUM_WORDS = {"three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "two": 2}


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )


STAT_KEYS = ("M", "WS", "BS", "S", "T", "W", "I", "A", "Ld")
COUNT_PREFIX = re.compile(r"^(?:\d+\s*[–-]\s*)?\d+\s+")


def words_match(a: str, b: str) -> bool:
    return a == b or (len(a) >= 3 and len(b) >= 3
                      and (a.startswith(b) or b.startswith(a)))


def pick_statline_key(nm: str, hits: list[str]) -> str | None:
    """Choose among candidate YAML profile names for one HTML row."""
    if not hits:
        return None
    if len(hits) == 1:
        return hits[0]
    # ambiguous: prefer the singularized exact match ("Sheepherders" ->
    # "Sheepherder" beats "Black Sheep")
    for cand in (nm, nm[:-1] if nm.endswith("s") else None):
        if cand and cand in hits:
            return cand
    return None


def html_stat_rows(band_id: str) -> list[tuple[str, list[str]] | None]:
    """Parse the fighter stat blocks out of the cached source HTML page.

    Each ``<div class="fighter">`` carries an <h3> heading with the profile
    name (optionally prefixed by its roster allowance, e.g. "0 – 2 Retainer")
    and an M/WS/... table whose second row holds the values.
    Returns None when the page is missing.
    """
    page_path = PAGES / f"{band_id}.html"
    if not page_path.exists():
        return None
    page = page_path.read_text(encoding="utf-8", errors="replace")
    out: list[tuple[str, list[str]]] = []
    parts = page.split('<div class="fighter">')
    for seg in parts[1:]:
        nxt = seg.find('<div class="fighter">')
        if nxt != -1:
            seg = seg[:nxt]
        h = re.search(r"<h3[^>]*>(.*?)</h3>", seg, re.S)
        if not h:
            continue
        name = re.sub("\u200b", "",
                      html_mod.unescape(re.sub(r"<[^>]+>", "", h.group(1)))).strip()
        for tm in re.finditer(r"<table[^>]*>(.*?)</table>", seg, re.S):
            rows: list[list[str]] = []
            for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", tm.group(1), re.S):
                cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", m.group(1),
                                   re.S)
                rows.append([
                    html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                    for c in cells
                ])
            if len(rows) >= 2 and [c.lower() for c in rows[0][:2]] == \
                    ["m", "ws"]:
                out.append((name, rows[1]))
                break
    return out


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", strip_accents(s).lower()).strip()


def squash(t: str) -> str:
    return re.sub(r"\s+", " ", t)


def load_manifest() -> dict:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    rows = data["bands"] if isinstance(data, dict) and "bands" in data else data
    return {r["id"]: r for r in rows}


def load_text(band_id: str) -> str | None:
    p = TEXTS / f"{band_id}.txt"
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8", errors="replace")


def html_skill_rows(band_id: str) -> dict[str, list[str]] | None:
    """Parse the skill table out of the cached source HTML page.

    Returns {row_name: [skill tokens]} using the header row for column
    identity, or None when the page is missing / has no skill table.
    """
    page_path = PAGES / f"{band_id}.html"
    if not page_path.exists():
        return None
    page = page_path.read_text(encoding="utf-8", errors="replace")
    for tm in re.finditer(r"<table[^>]*>(.*?)</table>", page, re.S):
        rows: list[list[str]] = []
        for m in re.finditer(r"<tr[^>]*>(.*?)</tr>", tm.group(1), re.S):
            cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", m.group(1), re.S)
            rows.append([
                html_mod.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                for c in cells
            ])
        if not rows:
            continue
        header = [c.lower() for c in rows[0]]
        colmap: dict[int, str] = {}
        for i, c in enumerate(header[1:], 1):
            for token in ("combat", "shooting", "academic", "strength",
                          "speed", "special"):
                if token in c:
                    colmap[i] = token
                    break
        if "combat" not in colmap.values():
            continue  # not a skill table
        out: dict[str, list[str]] = {}
        for row in rows[1:]:
            if not row or not row[0]:
                continue
            out[row[0]] = [colmap[i] for i in sorted(colmap)
                           if i < len(row) and "✓" in row[i]]
        if out:
            return out
    return None


def name_in_text(name: str, tn: str) -> bool:
    nm = norm(name)
    if nm and nm in tn:
        return True
    words = [w for w in nm.split() if len(w) >= 4]
    return bool(words) and all(w in tn for w in words)


def check_band(band_id: str, mrow: dict) -> list[dict]:
    issues: list[dict] = []
    pkg = STAGING / band_id

    if not (pkg / "band.yaml").exists():
        return [{"band": band_id, "kind": "package-missing",
                 "detail": "no band.yaml on disk"}]

    band = yaml.safe_load((pkg / "band.yaml").read_text(encoding="utf-8"))
    profiles = yaml.safe_load((pkg / "profiles.yaml").read_text(encoding="utf-8"))
    t = load_text(band_id)
    if t is None:
        issues.append({"band": band_id, "kind": "text-missing",
                       "detail": "no extracted text"})
        return issues
    t2 = squash(t)
    tn = norm(t2)

    # ---- 1. profile names present in text -------------------------------
    for pr in profiles["profiles"]:
        nm = norm(pr["name"])
        if nm and not name_in_text(pr["name"], tn):
            issues.append({"band": band_id, "kind": "profile-name-not-in-text",
                           "profile": pr["name"]})

    # ---- 2. cost for hireable profiles (any-agree) ----------------------
    for pr in profiles["profiles"]:
        nm = norm(pr["name"])
        # "<N> gold crowns to hire" preceded by the profile name within a
        # short window (flat text puts the header and cost on adjacent lines)
        pdf_costs = [int(m.group(1)) for m in re.finditer(
            re.escape(nm) + r".{0,60}?(\d+)\s+gold crowns to hire", t2)]
        if pdf_costs and pr["cost"] not in pdf_costs:
            issues.append({"band": band_id, "kind": "cost-mismatch",
                           "profile": pr["name"], "yaml": pr["cost"],
                           "pdf_candidates": sorted(set(pdf_costs))})

    # ---- 3. experience (any-agree) ---------------------------------------
    for pr in profiles["profiles"]:
        # plural names (Trappers, Apprentices) use "start with" — try both
        # the full name and a singular-ish prefix
        nm_variants = {norm(pr["name"])}
        nm_variants.add(re.sub(r"s$", "", norm(pr["name"])))
        pdf_exps = []
        for nm in nm_variants:
            pdf_exps += [int(m.group(1)) for m in re.finditer(
                re.escape(nm) + r"\s+starts?\s+with\s+(\d+)\s+experience",
                t2, re.I)]
        if pdf_exps and pr["experience"] not in pdf_exps:
            issues.append({"band": band_id, "kind": "experience-mismatch",
                           "profile": pr["name"], "yaml": pr["experience"],
                           "pdf_candidates": sorted(set(pdf_exps))})

    # ---- 4. roster / size lines -----------------------------------------
    roster = band["roster"]

    min_m = re.search(
        r"([A-Za-z' ]{2,50}?)[Ww]arband must include a minimum of "
        r"(three|four|five|\d+) models", t2)
    if min_m:
        raw = min_m.group(2).lower()
        n = int(raw) if raw.isdigit() else NUM_WORDS.get(raw)
        if n and roster["minimum_models"] != n:
            issues.append({"band": band_id, "kind": "min-models-mismatch",
                           "yaml": roster["minimum_models"], "pdf": n})

    max_m = re.search(
        r"maximum number of (?:warriors|models) in (?:the |your )?warband"
        r"(?: may)?(?: never exceed| is)\s*(\d+)", t2)
    if max_m and roster["maximum_models"] != int(max_m.group(1)):
        issues.append({"band": band_id, "kind": "max-models-mismatch",
                       "yaml": roster["maximum_models"],
                       "pdf": int(max_m.group(1))})

    gold_candidates = {int(x) for x in re.findall(
        r"[Yy]ou have (\d{3}) (?:gold crowns|Warp Tokens|warp tokens)", t2)}
    if gold_candidates and roster["starting_gold"] not in gold_candidates:
        issues.append({"band": band_id, "kind": "starting-gold-mismatch",
                       "yaml": roster["starting_gold"],
                       "pdf_candidates": sorted(gold_candidates)})

    # ---- 5. skill table vs cached HTML (column-exact) -------------------
    # Skill access lives per profile (KB pattern, ``skill_access``); the
    # former band-level ``skill_tables`` block was a staging-only duplicate.
    warnings: list[dict] = []
    table = [
        {"id": band_id + "-skill-table", "rows": [
            {"profile_id": p["id"], "access": p.get("skill_access") or []}
            for p in profiles["profiles"] if p.get("skill_access")
        ]},
    ]
    if table:
        html_rows = html_skill_rows(band_id)
        if html_rows is None:
            warnings.append({"band": band_id, "kind": "skill-table-unverified",
                             "detail": "no cached HTML page or no skill table found"})
        else:
            lower_names = {norm(k): v for k, v in html_rows.items()}

            def match_row(pid: str, name: str | None) -> list[str] | None:
                nm = norm(name or pid)
                candidates = [nm, norm(pid), re.sub(r"s$", "", norm(pid)),
                              nm + "s"]
                if candidates[0] in ROW_ALIASES:
                    candidates.append(ROW_ALIASES[candidates[0]])
                for cand in candidates:
                    if cand and cand in lower_names:
                        return lower_names[cand]
                # word-level prefix containment, either direction, must be
                # unambiguous (handles "Halfling Cook" -> "Cook",
                # "Petty Thieves" -> "Petty Thief", "Retainer" ->
                # "Retainers", "Rememberer" -> "Dwarf Rememberer")
                def words_match(a: str, b: str) -> bool:
                    return a == b or (len(a) >= 4 and len(b) >= 4
                                      and (a.startswith(b)
                                           or b.startswith(a)))

                if nm:
                    ywords = nm.split()
                    hits = []
                    for k, v in lower_names.items():
                        kwords = k.split()
                        yaml_subset = all(
                            any(words_match(yw, kw) for kw in kwords)
                            for yw in ywords)
                        row_subset = all(
                            any(words_match(kw, yw) for yw in ywords)
                            for kw in kwords)
                        if yaml_subset or row_subset:
                            hits.append(v)
                    if len(hits) == 1:
                        return hits[0]
                return None

            for tbl in table:
                for row in tbl["rows"]:
                    pid = row["profile_id"]
                    acc = row.get("access") or []
                    pr = next((p for p in profiles["profiles"]
                               if p["id"] == pid), None)
                    hit = match_row(pid, pr["name"] if pr else None)
                    if hit is None:
                        warnings.append({"band": band_id,
                                         "kind": "skill-row-unmatched",
                                         "profile": pr["name"] if pr else pid,
                                         "html_rows": sorted(html_rows)})
                        continue
                    if hit != acc:
                        issues.append({"band": band_id,
                                       "kind": "skill-access-mismatch",
                                       "profile": pr["name"] if pr else pid,
                                       "yaml_access": acc,
                                       "html_access": hit})
    issues.extend(warnings)

    # ---- 5b. statlines vs cached HTML (cell-by-cell) ---------------------
    stat_rows = html_stat_rows(band_id)
    if stat_rows is not None:
        ynames = {norm(p["name"]): p.get("characteristics") or {}
                  for p in profiles["profiles"]}
        for name, stats in stat_rows:
            # strip the roster allowance prefix ("0 – 5 Black sheep" ->
            # "Black sheep") on the raw string, before norm() turns the
            # en-dash into a space
            nm = norm(COUNT_PREFIX.sub("", name))
            key = next((k for k in ynames if k == nm), None)
            if key is None:
                # unambiguous word-level containment in either direction
                # ("Halfling Cook" -> "Cook", "Retainers" -> "Retainer")
                ywords = nm.split()
                hits = []
                for k in ynames:
                    kwords = k.split()
                    yaml_subset = all(
                        any(words_match(yw, kw) for kw in kwords)
                        for yw in ywords)
                    row_subset = all(
                        any(words_match(kw, yw) for yw in ywords)
                        for kw in kwords)
                    if yaml_subset or row_subset:
                        hits.append(k)
                key = pick_statline_key(nm, hits)
            if key is None:
                warnings.append({"band": band_id, "kind": "statline-unmatched",
                                 "html_name": name})
                continue
            yc = ynames[key]
            yvals = [str(yc.get(c, "")) for c in STAT_KEYS]
            diffs = {}
            for k, yv, hv in zip(STAT_KEYS, yvals, stats):
                if hv == "*":
                    continue  # random movement etc., documented in notes
                if yv != hv:
                    diffs[k] = {"yaml": yv, "html": hv}
            if diffs:
                issues.append({"band": band_id, "kind": "statline-mismatch",
                               "profile": key, "diffs": diffs})
    issues.extend(warnings)

    # ---- 6. skill_access sanity -----------------------------------------
    for pr in profiles["profiles"]:
        acc = pr.get("skill_access") or []
        bad = [a for a in acc if a not in VALID_SKILL_TOKENS]
        if bad:
            issues.append({"band": band_id, "kind": "skill-token-invalid",
                           "profile": pr["name"], "tokens": bad})
        if pr["type"] == "henchman" and acc:
            issues.append({"band": band_id, "kind": "henchman-with-skill-access",
                           "profile": pr["name"], "tokens": acc})

    # ---- 7. rule_ids referenced exist in special-rules -------------------
    rules_doc = yaml.safe_load((pkg / "special-rules.yaml").read_text(encoding="utf-8"))
    rule_ids = {r["id"] for r in rules_doc["rules"]}
    for pr in profiles["profiles"]:
        for rid in pr.get("rule_ids") or []:
            if rid not in rule_ids:
                issues.append({"band": band_id, "kind": "rule-id-dangling",
                               "profile": pr["name"], "rule_id": rid})

    # ---- 8. equipment list ids referenced exist --------------------------
    eq_doc = yaml.safe_load((pkg / "equipment-access.yaml").read_text(encoding="utf-8"))
    list_ids = {l["id"] for l in eq_doc["equipment_lists"]}
    for pr in profiles["profiles"]:
        for lid in pr.get("equipment_lists") or []:
            if lid not in list_ids:
                issues.append({"band": band_id, "kind": "equipment-list-dangling",
                               "profile": pr["name"], "list_id": lid})
    return issues


def main() -> int:
    manifest = load_manifest()
    only = sys.argv[1:]
    all_issues: list[dict] = []
    for band_id in sorted(manifest):
        if only and not any(o in band_id for o in only):
            continue
        all_issues.extend(check_band(band_id, manifest[band_id]))

    by_kind: dict[str, int] = {}
    for i in all_issues:
        by_kind[i["kind"]] = by_kind.get(i["kind"], 0) + 1

    print(json.dumps({
        "total_bands": len(manifest),
        "issues_by_kind": by_kind,
        "problem_count": len(all_issues),
        "issues": all_issues,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

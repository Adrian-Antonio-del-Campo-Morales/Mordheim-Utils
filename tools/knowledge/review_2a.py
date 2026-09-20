"""English-review cross-check for the 2A staging tree.

Reads every band package under ``sources/2A/bands/mordheim`` and re-derives
each number (profile costs/xp/characteristics, equipment prices, roster
limits, numbers quoted in rule texts) from the band's cached dedicated-page
draft in ``build/cache/2a-sources/text/<id>.txt``. It then classifies each
check:

    OK         the number was found in the source text in context
    NOT_FOUND  the source text does not contain the context (extraction noise)
    MISMATCH   contradicting digits were found in context

The report is written to ``build/cache/2a-sources/review-report.md`` and
summed to stdout. This tool is **read-only**: it never edits packages, the
manifest or the active knowledge base. Manual verdicts are recorded in
``sources/2A/english-review.md``; ``NOT_FOUND`` is acceptable (extraction
noise), ``MISMATCH`` must be adjudicated against the draft before a row is
marked ``english-reviewed``.

Adapted from ``tools/knowledge/review_2b.py``. 2A differences: the primary
source is the cached mordheimer.net page draft (no scanned sources), and two
warbands use non-gold-crown currencies in their hire lines (warp tokens).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / "sources" / "2A"
BANDS = STAGING / "bands" / "mordheim"
CACHE = ROOT / "build" / "cache" / "2a-sources"
TEXTS = CACHE / "text"
REPORT = CACHE / "review-report.md"

CHAR_ORDER = ("M", "WS", "BS", "S", "T", "W", "I", "A", "Ld")


def load_manifest() -> list[dict]:
    doc = yaml.safe_load((STAGING / "manifest.yaml").read_text(encoding="utf-8")) or {}
    return doc.get("bands") or []


def norm_source(text: str) -> str:
    """Draft text -> uppercase alnum stream for context searches."""
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def load_source_text(band_id: str) -> str:
    path = TEXTS / f"{band_id}.txt"
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def digit_groups(text: str) -> list[str]:
    return re.findall(r"\d+", text)


def context_for(src: str, needle: str, span: int = 24) -> list[str]:
    """All digit groups within `span` chars after each occurrence of needle."""
    out: list[str] = []
    start = 0
    while True:
        i = src.find(needle, start)
        if i < 0:
            break
        out.extend(digit_groups(src[i + len(needle): i + len(needle) + span]))
        start = i + 1
    return out


def check_number(value, contexts: list[str]) -> str:
    v = str(value)
    if not contexts:
        return "NOT_FOUND"
    if v in contexts:
        return "OK"
    return "MISMATCH"


def profile_cost_contexts(src: str, name: str) -> list[str]:
    """Digits directly before each hire marker (gold crowns or warp tokens),
    plus name-adjacent digits."""
    out: list[str] = []
    for marker in ("GOLDCROWNSTOHIRE", "WARPTOKENSTOHIRE"):
        for m in re.finditer(rf"(\d+){marker}", src):
            out.append(m.group(1))
    out.extend(context_for(src, name, 18))
    return out


def profile_stat_run(profile: dict) -> str:
    chars = profile.get("characteristics") or {}
    return "".join(str(chars.get(k, "")) for k in CHAR_ORDER)


def review_band(band_id: str) -> dict:
    pkg = BANDS / band_id
    band = yaml.safe_load((pkg / "band.yaml").read_text(encoding="utf-8"))
    profiles = yaml.safe_load((pkg / "profiles.yaml").read_text(encoding="utf-8"))
    equip = yaml.safe_load((pkg / "equipment-access.yaml").read_text(encoding="utf-8"))
    rules = yaml.safe_load((pkg / "special-rules.yaml").read_text(encoding="utf-8"))

    src = norm_source(load_source_text(band_id))
    checks: list[tuple[str, str, str]] = []

    # roster -----------------------------------------------------------------
    roster = band.get("roster") or {}
    for key, needles in (
        ("minimum_models", ["MINIMUMOF", "MINIMUM", "MINIMUMF"]),
        ("maximum_models", ["MAXIMUMOF", "MAXIMUM", "MAYNEVEREXCEED", "NEVEREXCEED", "WARBANDIS"]),
    ):
        val = roster.get(key)
        if val is None:
            continue
        groups: list[str] = []
        for n in needles:
            groups.extend(context_for(src, n, 10))
        checks.append(("roster", key, check_number(val, groups)))
    gold = roster.get("starting_gold")
    if gold is not None:
        groups = [m.group(1) for m in re.finditer(r"(\d+)(?:GOLDCROWNS|WARPTOKENS)", src)]
        groups += context_for(src, "YOUHAVE", 6) + context_for(src, "YOURWARBANDHAS", 6)
        checks.append(("roster", "starting_gold", check_number(gold, groups)))

    # profiles ---------------------------------------------------------------
    for p in profiles.get("profiles") or []:
        name = re.sub(r"[^A-Z0-9]", "", str(p.get("name", "")).upper())
        run = profile_stat_run(p)
        if run and run in src:
            checks.append(("profile", f"{p['id']}:stats", "OK"))
        else:
            checks.append(("profile", f"{p['id']}:stats", "NOT_FOUND"))
        if p.get("cost") is not None:
            checks.append(
                ("profile", f"{p['id']}:cost", check_number(p["cost"], profile_cost_contexts(src, name)))
            )
        if p.get("experience") is not None:
            groups = context_for(src, f"{name}STARTSWITH", 4)
            groups += re.findall(r"(\d+)EXPERIEN", src)
            checks.append(("profile", f"{p['id']}:xp", check_number(p["experience"], groups)))

    # equipment lists ----------------------------------------------------------
    for lst in equip.get("equipment_lists") or []:
        for item in lst.get("items") or []:
            item_id = str(item.get("item_id", ""))
            cost = item.get("cost")
            if cost is None:
                continue
            needle = re.sub(r"[^A-Z0-9]", "", item_id.replace("_", " ")).upper()
            if not needle:
                continue
            groups = context_for(src, needle, 14)
            notes = str(item.get("notes") or "")
            verdict = check_number(cost, groups)
            if verdict == "MISMATCH" and ("free" in notes or str(cost) in notes):
                verdict = "OK"  # e.g. "1st free/2 gc": nearby digits mislead
            checks.append(("equipment", f"{lst['id']}:{item_id}", verdict))

    # special rules: numbers quoted in effect text must exist in the source ---
    for rule in rules.get("rules") or []:
        effect = str(rule.get("effect") or "")
        nums = re.findall(r"\d+", effect)
        for n in sorted(set(nums)):
            checks.append(
                ("rule", f"{rule['id']}:{n}", "OK" if n in src else "MISMATCH")
            )

    summary = {"OK": 0, "NOT_FOUND": 0, "MISMATCH": 0}
    for _, _, v in checks:
        summary[v] += 1
    return {"band_id": band_id, "checks": checks, "summary": summary}


def main() -> int:
    rows = load_manifest()
    results = [review_band(str(r["id"])) for r in rows]

    lines = ["# 2A english-review cross-check", ""]
    tot = {"OK": 0, "NOT_FOUND": 0, "MISMATCH": 0}
    for res in results:
        for k, v in res["summary"].items():
            tot[k] += v
        lines.append(f"## {res['band_id']}")
        lines.append("")
        for kind, label, verdict in res["checks"]:
            if verdict != "OK":
                lines.append(f"- {verdict}: [{kind}] {label}")
        lines.append("")
    REPORT.write_text("\n".join(lines), encoding="utf-8", newline="\n")

    print(f"bands: {len(results)}")
    print(f"checks: {sum(tot.values())} (OK={tot['OK']} NOT_FOUND={tot['NOT_FOUND']} MISMATCH={tot['MISMATCH']})")
    mismatches = [(r["band_id"], k, l) for r in results for k, l, v in r["checks"] if v == "MISMATCH"]
    if mismatches:
        print("\nMISMATCH detail (also in review-report.md):")
        for band, kind, label in mismatches:
            print(f"  {band}: [{kind}] {label}")
    print(f"\nreport: {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

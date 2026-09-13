"""Import missing item rules from their registered Mordheimer pages.

Matches an item to a page heading, extracts rules/stat lines, translates the
result to Spanish, and patches only missing ``effect`` fields in item YAML.
Ambiguous or absent matches are reported and never guessed.
"""
from __future__ import annotations

import argparse
import difflib
import html
import re
import time
from pathlib import Path

import requests
import yaml
from bs4 import BeautifulSoup, Tag

ROOT = Path(__file__).resolve().parents[2]
ITEMS = ROOT / "sources/knowledge/catalog/items"
CENTRAL = (
    "https://mordheimer.net/docs/weapons-armour/missile",
    "https://mordheimer.net/docs/weapons-armour/blackpowder",
    "https://mordheimer.net/docs/weapons-armour/close-combat",
    "https://mordheimer.net/docs/weapons-armour/armour",
    "https://mordheimer.net/docs/weapons-armour/miscellaneous-equipment",
    "https://mordheimer.net/docs/weapons-armour/animal-bestiary",
)


def key(value: str) -> str:
    value = value.casefold().replace("&", "and")
    value = re.sub(r"\([^)]*\)|\b(one|max|per)\s+\d+\s+per\s+warband\b", " ", value)
    return re.sub(r"[^a-z0-9]+", "", value)


ALIASES = {
    "arcanefamiliar": "familiar",
    "beastmasterwhip": "beastlash",
    "birdofpreyaristocratonly": "birdofprey",
    "blunderbussoneperwarband": "blunderbuss",
    "bronzeaxe": "axe", "bronzedagger": "dagger", "bronzehelmet": "helmet",
    "bronzespear": "spear", "bronzesword": "sword",
    "cathayansilkcloak": "cathayansilkclothes",
    "doublebarrelledhuntingrifle": "ostlanderdoublebarrelledhuntingrifle",
    "elfboots": "elvenboots",
    "flyingcarpet": "magiccarpet",
    "fogwarpstonefragments": "fogenhancingwarpstoneshards",
    "holyrelicpilgrimonly": "holyrelic",
    "horsedamselsquireonly": "horse",
    "magestaff": "quarterstaff",
    "nagarythestandard": "standardofnagarythe",
    "nagarythewarhorn": "warhornofnagarythe",
    "nightmarearistocratonly": "nightmare",
    "pestilensbanner": "clanpestilensbanner",
    "pigeonbombs": "herstenwenklerpigeonbombs",
    "ratfamiliarscroll": "scrolloftheratfamiliar",
    "sigmarshield": "shield",
    "snakewhip": "barbedwhip",
    "throwingaxe": "throwingknivesstars",
    "throwingaxessameasthrowingknives": "throwingaxes",
    "throwingknives": "throwingknivesstars", "throwingstars": "throwingknivesstars",
    "throwingweapons": "throwingknivesstars",
    "travelstaff": "quarterstaff",
    "warhound": "wardogs",
    "warppistol": "warplockpistol",
}


def section_for(name: str, sections: dict[str, list[str]]) -> list[str] | None:
    wanted = ALIASES.get(key(name), key(name))
    exact = sections.get(wanted)
    if exact:
        return exact
    candidates = difflib.get_close_matches(wanted, sections, n=2, cutoff=0.88)
    return sections[candidates[0]] if len(candidates) == 1 else None


def page_sections(url: str, session: requests.Session) -> dict[str, list[str]]:
    response = session.get(url, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    result: dict[str, list[str]] = {}
    for heading in soup.find_all(["h2", "h3", "h4", "h5"]):
        name = heading.get_text(" ", strip=True).removesuffix("​").strip()
        if not name or name.casefold() == "special rules":
            continue
        level = int(heading.name[1])
        nodes: list[Tag] = []
        for node in heading.next_elements:
            if node is heading or not isinstance(node, Tag):
                continue
            if node.name in ("h2", "h3", "h4", "h5") and int(node.name[1]) <= level:
                break
            if node.name in ("p", "li") and not node.find_parent(("p", "li")):
                nodes.append(node)
            elif node.name == "h5" and "special rules" in node.get_text(" ", strip=True).casefold():
                sibling = node.find_next_sibling()
                if sibling and sibling.name not in ("h2", "h3", "h4", "h5"):
                    nodes.append(sibling)
        lines = []
        for node in nodes:
            text = " ".join(node.get_text(" ", strip=True).split())
            if text and text not in lines:
                lines.append(text)
        result.setdefault(key(name), lines)
    return result


def rule_text(lines: list[str]) -> str:
    keep = []
    for line in lines:
        if re.match(r"^(Cost|Availability|Source):", line, re.I):
            continue
        if re.match(r"^(Range|Strength):", line, re.I) or keep or "Special Rules" in line:
            keep.append(line.replace("Special Rules", "").strip())
    if not keep:
        prose = [line for line in lines if not re.match(r"^(Cost|Availability|Source):", line, re.I)]
        keep = prose[-2:]
    keep = [line for line in keep if line]
    return " ".join(keep[:8]).strip()


def translate(text: str, session: requests.Session) -> str:
    response = session.get("https://translate.googleapis.com/translate_a/single", params={
        "client": "gtx", "sl": "en", "tl": "es", "dt": "t", "q": text,
    }, timeout=30)
    response.raise_for_status()
    return "".join(part[0] for part in response.json()[0] if part[0]).strip()


def folded(value: str, indent: int) -> list[str]:
    width, words, rows, current = 100 - indent, value.split(), [], []
    for word in words:
        if current and len(" ".join(current + [word])) > width:
            rows.append(" ".join(current)); current = []
        current.append(word)
    if current: rows.append(" ".join(current))
    return [(" " * indent) + row for row in rows]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    session = requests.Session()
    session.headers["User-Agent"] = "Mordheim-Utils KB maintenance"
    cache: dict[str, dict[str, list[str]]] = {}
    imported = unresolved = 0
    for path in sorted(ITEMS.glob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        additions: dict[str, tuple[str, str]] = {}
        for item in document.get("items") or []:
            if any(item.get(field) for field in ("effect", "description", "text", "note")):
                continue
            urls = [str(ref.get("url")) for ref in item.get("source_refs") or [] if ref.get("url")]
            urls += [url for url in CENTRAL if url not in urls]
            matches: list[list[str]] = []
            for url in urls:
                try:
                    if url not in cache: cache[url] = page_sections(url, session)
                    section = section_for(str(item.get("name") or ""), cache[url])
                    if section: matches.append(section)
                except requests.RequestException:
                    continue
            candidates = [rule_text(lines) for lines in matches if rule_text(lines)]
            if not candidates:
                unresolved += 1
                print(f"UNRESOLVED {item.get('id')} matches={len(candidates)}")
                continue
            english = candidates[0]
            try:
                spanish = translate(english, session)
            except requests.RequestException:
                unresolved += 1; print(f"TRANSLATION_FAILED {item.get('id')}"); continue
            additions[str(item["id"])] = (english, spanish)
            imported += 1
            time.sleep(0.05)
        if args.write and additions:
            lines = path.read_text(encoding="utf-8").splitlines()
            output: list[str] = []
            current = ""
            inserted: set[str] = set()
            for line in lines:
                match = re.match(r"^- id: (.+)$", line)
                if match: current = match.group(1).strip()
                if line.startswith("  source_refs:") and current in additions and current not in inserted:
                    en, es = additions[current]
                    output += ["  effect: >-", *folded(en, 4), "  effect_i18n:", "    es: >-", *folded(es, 6)]
                    inserted.add(current)
                output.append(line)
            path.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(f"imported={imported} unresolved={unresolved} pages={len(cache)} write={args.write}")
    return 0 if unresolved == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

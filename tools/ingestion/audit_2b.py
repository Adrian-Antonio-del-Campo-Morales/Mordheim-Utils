# -*- coding: utf-8 -*-
"""Cross-audit of sources/2B staging packages against extracted PDF texts.

Every check is evaluated against two readings of the source document: the
cached plain text and the geometry reading of the shared reader
(``printed_entries``: words by their coordinates, the gutter between columns,
the reading order, and the cells each line prints). The plain form is complete
but collapses two-column tables; the geometry form keeps every column apart, so
a price list and a table row are read from the row that prints them instead of
from a window of flattened text. A row counts as verified when *either* reading
carries it, and is only reported as a problem when neither can confirm it.

Checks per band:
  1. Profile names appear in the extracted text (case/diacritic-insensitive).
     Names with parenthetical suffixes ("Domnu (Caravan Master)") are matched
     word-wise; OCR-degraded texts (manifest pdf_is_text: false) are only
     reported as info, not problems.
  2. Cost + starting experience: EVERY occurrence of a cost/experience line for
     the profile is collected; the YAML value is accepted if ANY occurrence
     agrees (guards against multi-band anthologies where the same name appears
     in several band sections with different values). Two further reading paths
     cover what no text idiom reaches: the supplements that print the figure on
     a line of its own are read from the page's geometry (the heading nearest
     above on the same left margin), headings set in the decorative display
     face are decoded, and the figures of the three scanned KEP documents - which
     have no text layer at all - are compared with the readings recorded in
     ``READ_OFF_PAGE`` (read off the page image; the readings and their method
     are recorded in ``sources/2B/discrepancy-verdicts.md`` sections 5 and 6).
  3. Roster: min/max models are anchored to the band's own "CHOICE OF WARRIORS"
     section (the match whose leading words overlap the band name; last match
     as fallback) instead of the first match in the document. Both the
     "may never exceed N" and "maximum number of warriors ... is N" phrasings
     are accepted. Starting gold accepts "N gold crowns / warp tokens / GCs /
     tc / wt" phrasings and only flags if no candidate agrees.
  4. skill_access sanity: heroes use only valid tokens; henchmen have empty
     access.
  5. Every rule_id referenced by profiles/band exists in special-rules.yaml.
  6. Every equipment list referenced by profiles exists in equipment-access.yaml.
  7. Equipment rows: printed name + price (the prices read row by row from the
     page's own geometry, every currency the supplements use, formula prices by
     their base figure, and the lists the document delegates to the rulebook
     resolved against the KB copy of the same list).
  8. Rule fidelity: every rule of the package is traceable to its source - its
     name appears in the text, or every significant word of the section it
     cites does. Rules that resolve neither way are reported, except in the two
     documents no search can read (the KEP scans with no text layer, and
     Metal-mongers, whose embedded fonts decode to wrong glyphs - its display
     headings are decoded for the cost lines above, but its rule prose is set in
     a face that cannot be read back).
  9. Skill tables: the source prints each hero's skill lists as a table of X
     marks. The marks are read from the page's own geometry - each row's cells
     aligned with the headings of the table's heading row - and compared with
     the package's ``skill_access``.
 10. Spell / prayer lists: every spell of ``catalog/magic-2b.yaml`` must appear
     in the document its lore cites, with the printed difficulty; the document is
     read by geometry (one of the 60 manifest rows or a cached extra source under
     ``build/cache/2b-pdfs/extra``), never from a flattened layout run.
 11. Hired Sword / Dramatis Personae access: every band-scoped access sentence
     of the source must be reflected by a rule, the hirelings it names must be
     in the package's prose, and every one of them must exist in a hireling
     catalogue (the stat blocks live there, not in the staging packages).

Outputs a JSON report.  Manual verification is still required for any flag:
PDF text extraction is lossy.
"""
from __future__ import annotations

import glob
import json
import re
import sys
import unicodedata
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import unquote

import yaml

# La lectura de la página —geometría, celdas, filas y listas de precio— vive en el
# lector compartido con los cotejos de catálogo (``tools/knowledge``: permanente,
# no propio de esta fase); aquí vive lo que es de este árbol:
# qué documento imprime cada paquete, qué se considera un hallazgo y su adjudicación.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "knowledge"))
from printed_entries import PdfCorpus, cells, price_rows  # noqa: F401

# Las palabras que la fuente imprime para un objeto del catálogo cuando no son las
# suyas —la errata, el nombre del reglamento, la celda que funde la disponibilidad—
# viven en un solo registro compartido con los otros dos cotejos (``printed_wordings``),
# con el sitio donde se leyó cada una y con las listas que el documento delega al
# reglamento en vez de imprimirlas. Aquí se leen por banda.
import printed_wordings as wordings

ROOT = Path(__file__).resolve().parents[2]
STAGING = ROOT / "sources" / "2B" / "bands" / "mordheim"
CACHE = ROOT / "build" / "cache" / "2b-pdfs"
TEXTS = CACHE / "text"
# El documento leído por geometría: las palabras con su coordenada (``word_lines``),
# la página partida en líneas y celdas (``lines``), y las páginas ya leídas en
# memoria durante la corrida (el XML se cachea en disco, página por página).
CORPUS = PdfCorpus(CACHE, CACHE / "words", CACHE / "text-geometry")
MANIFEST = ROOT / "sources" / "2B" / "manifest.yaml"
# Every catalogue a staging package may point at (a 2B band may reuse a 2A or KB item).
CATALOG_GLOBS = (
    "sources/knowledge/catalog/items/*.yaml",
    "sources/2A/catalog/items/*.yaml",
    "sources/2B/catalog/items/*.yaml",
)

VALID_SKILL_TOKENS = {
    "combat", "shooting", "academic", "strength", "speed", "special",
    "pirate", "musicianship",
}

EXTRA = CACHE / "extra"
# Los documentos extra se leen con el mismo lector, con su propia caché de página.
EXTRA_CORPUS = PdfCorpus(EXTRA, CACHE / "words-extra", CACHE / "text-geometry-extra")
MAGIC = ROOT / "sources" / "2B" / "catalog" / "magic-2b.yaml"
# Every catalogue that carries hireling stat blocks (2B has no monopoly: a 2B
# band may reuse a hireling of the active KB, exactly as it may reuse an item).
HIRELING_GLOBS = (
    "sources/knowledge/catalog/hirelings/**/*.yaml",
    "sources/2A/catalog/hirelings/**/*.yaml",
    "sources/2B/catalog/hirelings/**/*.yaml",
)

NUM_WORDS = {"three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "two": 2}


def strip_accents(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", strip_accents(s).lower()).strip()


def squash(t: str) -> str:
    """Single-spaced text for sentence-level regexes."""
    return re.sub(r"\s+", " ", t)


def load_manifest() -> dict:
    data = yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))
    rows = data["bands"] if isinstance(data, dict) and "bands" in data else data
    return {r["id"]: r for r in rows}


def package_rows() -> dict[str, dict]:
    """Band package -> the manifest row that produced it.

    A row describes one source document; ``packages`` declares every band package
    the document yielded (a document may print two warband lists). The row id is
    the key the cache and every scrape artifact use.
    """
    out: dict[str, dict] = {}
    for row in load_manifest().values():
        for package in row.get("packages") or [row["id"]]:
            out[str(package)] = row
    return out


def load_item_names() -> dict[str, str]:
    """item id -> printed name, from the KB plus both provisional catalogues."""
    names: dict[str, str] = {}
    for pattern in CATALOG_GLOBS:
        for path in sorted(glob.glob(pattern)):
            doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
            for item in doc.get("items") or []:
                if isinstance(item, dict) and item.get("id") and item.get("name"):
                    names.setdefault(str(item["id"]), str(item["name"]))
    return names


# ``notes`` that qualify availability or provenance instead of naming the row.
NOTE_IS_NOT_A_NAME = re.compile(
    r"only|price|see |per |free|starting|creation|replaces|not printed|not available|"
    r"may not|cannot|special equipment|same as|bundle|brace|each|discount",
    re.I)


_KB_LISTS: dict[str, dict[str, int]] = {}


def kb_list_prices() -> dict[str, dict[str, int]]:
    """Every KB band list id -> {item id: cost}, the rulebook lists included."""
    if not _KB_LISTS:
        for path in sorted((ROOT / "sources" / "knowledge" / "bands" / "mordheim").glob(
                "*/equipment-access.yaml")):
            doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            for lst in doc.get("equipment_lists") or []:
                rows = _KB_LISTS.setdefault(str(lst.get("id")), {})
                for entry in lst.get("items") or []:
                    cost = entry.get("cost")
                    if entry.get("item_id") and isinstance(cost, int):
                        rows.setdefault(str(entry["item_id"]), cost)
    return _KB_LISTS


# A document that does not price a fighter itself: the Sartosa supplement prints
# the Orc Pirates and the Savage Orcs as "Same as Da Mob" and takes every figure
# from the Orc Mob warband, which the KB transcribes as ``orc-mob`` (the two
# lists agree on all seven figures: 80/40/40, 25, 15, 15, 200). Key: (band id,
# profile name of the package) -> the KB profile the source points at.
DELEGATED_BAND = "orc-mob"
DELEGATED_PROFILES: dict[str, str] = {
    "orc-pirates-sar/Boss": "Orc Boss",
    "orc-pirates-sar/Big Uns": "Orc Big ‘Uns",
    "orc-pirates-sar/Orc Boyz": "Orc Boyz",
    "savage-orcs-sar/Orc Boss": "Orc Boss",
    "savage-orcs-sar/Orc Shaman": "Orc Shaman",
    "savage-orcs-sar/Orc Big ‘Uns": "Orc Big ‘Uns",
    "savage-orcs-sar/Orc Boyz": "Orc Boyz",
    "savage-orcs-sar/Forest Goblins": "Goblin Warriors",
    "savage-orcs-sar/Cave Squigs": "Cave Squigs",
    "savage-orcs-sar/Troll": "Troll",
}


def delegated_target(band_id: str, name: object) -> str | None:
    """The KB profile a package takes this fighter's figures from, if any."""
    return DELEGATED_PROFILES.get(f"{band_id}/{name}")


def kb_band_profiles(band: str) -> dict[str, dict]:
    """KB profile name (presence-normalized) -> the profile, for one warband."""
    path = ROOT / "sources" / "knowledge" / "bands" / "mordheim" / band / "profiles.yaml"
    out: dict[str, dict] = {}
    if path.exists():
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for pr in doc.get("profiles") or []:
            if pr.get("name"):
                out[presence(pr["name"])] = pr
    return out


def source_names_for(entry: dict, item_names: dict[str, str], band_id: str = "") -> list[str]:
    """The possible printed names for an equipment row, best first.

    A name-shaped ``notes`` value is the source's own wording ("Battle axe",
    "Cutlass (Sword)"); an em dash marks the part after it as the printed name
    ("Swivel Gun — Ball Shot" → "Ball Shot"). Notes that only qualify
    availability ("Heroes only") are not names. The catalogue name is always a
    candidate, so a row is only flagged when neither wording carries its price.
    """
    names: list[str] = list(wordings.words_at("2B", band_id, "", str(entry.get("item_id"))))
    raw = str(entry.get("notes") or "").strip().split(";")[0]
    # The source may print a composed label ("Swivel Gun Ammo: Ball Shot",
    # "Weapon — Ball Shot"); every dash/paren segment is a candidate name.
    candidates = [raw]
    for segment in re.split(r"[\u2014\u2013]|\s-\s|:", raw):
        candidates.append(segment)
        candidates.append(segment.split("(")[0])
    for candidate in candidates:
        candidate = candidate.strip().strip("*_").rstrip(".").strip()
        if candidate in names:
            continue
        if (candidate and len(candidate) <= 40 and not re.search(r"\d", candidate)
                and re.search(r"[A-Za-z]{3}", candidate)
                and not NOTE_IS_NOT_A_NAME.search(candidate)):
            names.append(candidate)
    # The catalogue name may itself be a composed label ("Swivel Gun — Ball Shot").
    catalogue = item_names.get(str(entry.get("item_id")), "")
    for part in [catalogue] + re.split(r"[\u2014\u2013]|\s-\s|:", catalogue):
        part = part.strip().strip("*_").rstrip(".").strip()
        if part and part not in names and re.search(r"[A-Za-z]{3}", part):
            names.append(part)
    return names


def document_text(band_id: str) -> str:
    """El documento leído por geometría, con sus marcadores de página.

    Es la segunda lectura de todo el auditor, la que sustituye a la extracción
    con ``pdftotext -layout``: aquélla conservaba el orden de las columnas a costa
    de comprimir sus desplazamientos y perder líneas al intercalarlas, mientras
    que aquí cada columna se lee entera y en su orden.
    """
    return CORPUS.text(band_id)


def raw_plain(band_id: str) -> str:
    """The cached plain extraction with its line structure intact.

    ``load_texts`` squashes the plain form for the sentence-level checks; the
    skill tables are read per line, so they need the file as extracted.
    """
    path = TEXTS / f"{band_id}.txt"
    return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""


def load_texts(band_id: str) -> dict[str, str]:
    """Ambas lecturas del documento fuente: la plana y la de geometría."""
    forms: dict[str, str] = {}
    p = TEXTS / f"{band_id}.txt"
    if p.exists():
        forms["plain"] = squash(p.read_text(encoding="utf-8", errors="replace"))
    if CORPUS.pdf_for(band_id) is not None:
        forms["geometry"] = document_text(band_id)
    return forms


def form_candidates(forms: dict[str, str], pattern: str, flags: int = 0) -> list[int]:
    """Every number captured by ``pattern`` in any extraction form.

    Searched against the squashed text, which is **not** lower-cased: a pattern
    built from a normalized name needs ``re.I`` here, or it silently matches
    nothing (the defect that left the cost and experience checks dead).
    """
    found = {int(m.group(1)) for txt in forms.values()
             for m in re.finditer(pattern, squash(txt), flags)}
    return sorted(found)


def name_in_text(name: str, tn: str) -> bool:
    """Full-name match, else all significant words present.

    Long words carry the signal ("Adventur" matches "Adventurer"); names made
    only of short words ("Orc Big 'Uns") fall back to every word so the check
    does not degenerate into "no word to look for".
    """
    nm = norm(name)
    if nm in tn:
        return True
    words = [w for w in nm.split() if len(w) >= 4] or [w for w in nm.split() if len(w) >= 2]
    return bool(words) and all(w in tn for w in words)


def choose_section_match(t2: str, band_name: str, pattern: str) -> re.Match | None:
    """Pick the match of `pattern` best anchored to the band's own section.

    Anthology PDFs (e.g. KAZ) contain an intro block ("An Adventurer Warband
    must include...") plus one block per band.  We score each match by stem
    overlap between its leading words and the band name (stem = 6-char prefix
    so "Adventurers" matches "Adventurer"); if nothing scores and there are
    several candidate sections, the check is ambiguous and we return None
    instead of guessing.
    """
    def stem(w: str) -> str:
        return w[:6] if len(w) >= 6 else w

    band_stems = {stem(w) for w in norm(band_name).split()}
    band_stems -= {"the", "of", "de"}
    matches = list(re.finditer(pattern, t2, re.I))
    if not matches:
        return None
    if len(matches) == 1:
        return matches[0]
    best, best_score = None, 0
    for m in matches:
        lead_stems = {stem(w) for w in norm(m.group(1) or "").split()}
        score = len(lead_stems & band_stems)
        if score > best_score:
            best, best_score = m, score
    return best


STATS: dict[str, int] = {}


# The three KEP documents are scans with no text layer, and their cost rows are
# set in a face whose figures the OCR drops or misreads ("2UHPPERL<RWNTHIRE" is
# "0-2 SQUIG HOPPERS 30 GOLD CROWNS TO HIRE"). Every one of those figures was
# read off the rendered page — 300/600 dpi crops, per-glyph crops and
# connected-component analysis, corroborated where the same fighter is printed in
# another document — and is recorded in sources/2B/discrepancy-verdicts.md
# sections 5 and 6. Key: (band id, profile name) -> (cost, page of the scan). The
# auditor compares the reading with the package: a match verifies the figure, and
# a difference is a defect of the package, not an unreadable source.
READ_OFF_PAGE: dict[tuple[str, str], tuple[int, str]] = {
    # clan-angrund-kep: Noble read clean at 600 dpi; Engineer and Troll Slayer are
    # the stylized "5" (identical to the "5" of the verified "25") plus "0", the
    # same 50 the KAZ guild veteran is hired for; Ironbreaker is a double "1" + 0.
    ("clan-angrund-kep", "Dwarf Noble"): (85, "3"),
    ("clan-angrund-kep", "Dwarf Engineer"): (50, "4"),
    ("clan-angrund-kep", "Dwarf Troll Slayers"): (50, "4"),
    ("clan-angrund-kep", "Ironbreaker"): (110, "5"),
    # crooked-moon-kep: the Shaman's "5" was eaten by the OCR and is resolved by
    # the source itself (the KEP document declares it is the Night Goblin warband
    # of the Karak Azgal supplement, which prints "0-1 Shaman / 50 gold crowns");
    # the Squig Hopper's two glyphs are the stepped "3" and a closed-counter "0".
    ("crooked-moon-kep", "Big Boss"): (45, "4"),
    ("crooked-moon-kep", "Shaman"): (50, "5"),
    ("crooked-moon-kep", "Bosses"): (25, "5"),
    ("crooked-moon-kep", "Squig Hopper"): (30, "5"),
    # slave-uprising-kep: the Demagogue's "5" (upper bar, left stem, bowl) was
    # mistyped as "3" and corrected on this reading; the three 25s repeat the
    # glyph pattern already verified on the same page.
    ("slave-uprising-kep", "Demagogue"): (50, "2"),
    ("slave-uprising-kep", "Underlings"): (25, "2"),
    ("slave-uprising-kep", "Goblin Leader"): (25, "2"),
    ("slave-uprising-kep", "Human Leader"): (25, "2"),
}


def check_band(band_id: str, mrow: dict) -> list[dict]:
    issues: list[dict] = []
    pkg = STAGING / band_id

    if not (pkg / "band.yaml").exists():
        return [{"band": band_id, "kind": "package-missing",
                 "detail": "no band.yaml on disk"}]

    band = yaml.safe_load((pkg / "band.yaml").read_text(encoding="utf-8"))
    profiles = yaml.safe_load((pkg / "profiles.yaml").read_text(encoding="utf-8"))
    forms = load_texts(str(mrow["id"]))
    if not forms:
        issues.append({"band": band_id, "kind": "text-missing",
                       "detail": "no extracted text"})
        return issues
    ocr_degraded = mrow.get("pdf_is_text") is False

    # ---- 1. profile names present in text -------------------------------
    for pr in profiles["profiles"]:
        nm = norm(pr["name"])
        if nm and not any(name_in_text(pr["name"], norm(txt))
                          for txt in forms.values()):
            kind = ("profile-name-ocr-unverifiable" if ocr_degraded
                    else "profile-name-not-in-text")
            issues.append({"band": band_id, "kind": kind, "profile": pr["name"]})

    # ---- 2. cost / experience for heroes (any-agree semantics) ----------
    for pr in profiles["profiles"]:
        if pr["type"] == "henchman":
            continue
        # cost lines: "1 NOSFERATU .... 125 gc", "1 Big Boss 45 gold crowns to
        # hire", "Scarface 70 gc". The name pattern keeps the printed
        # punctuation out of the way, and every idiom is searched case-
        # insensitively: the sources capitalize, the YAML does not.
        pdf_costs = hero_cost_candidates(
            forms, pr["name"], (pr.get("source") or {}).get("section"),
            shared=len(mrow.get("packages") or [mrow["id"]]) > 1,
            row_id=str(mrow["id"]),
            others=[str(p["name"]) for p in profiles["profiles"]
                    if presence(p["name"]) != presence(pr["name"])])
        # A profile the source never prints a figure for (the promotion-only
        # Captain) carries no cost in the package either: nothing to compare.
        if pdf_costs and pr["cost"]:
            STATS["hero_costs"] = STATS.get("hero_costs", 0) + 1
            if pr["cost"] in pdf_costs:
                STATS["hero_costs_verified"] = STATS.get("hero_costs_verified", 0) + 1
            else:
                issues.append({"band": band_id, "kind": "cost-mismatch",
                               "profile": pr["name"], "yaml": pr["cost"],
                               "pdf_candidates": pdf_costs})
        elif pr["cost"] and delegated_target(band_id, pr["name"]):
            # The document does not price this fighter: it hands the whole list to
            # another warband ("Same as Da Mob"), so the figures are checked
            # against the KB transcription of that warband instead.
            target = delegated_target(band_id, pr["name"])
            kb_prof = kb_band_profiles(DELEGATED_BAND).get(presence(target))
            if kb_prof is None:
                issues.append({"band": band_id, "kind": "cost-delegated",
                               "profile": pr["name"], "yaml": pr["cost"],
                               "detail": f"delegated to {target}, absent from the KB band"})
            elif kb_prof.get("cost") == pr["cost"]:
                STATS["hero_costs_delegated"] = STATS.get("hero_costs_delegated", 0) + 1
                issues.append({"band": band_id, "kind": "cost-delegated",
                               "profile": pr["name"], "yaml": pr["cost"],
                               "detail": f"{kb_prof['name']} of the KB {DELEGATED_BAND} costs the same"})
            else:
                issues.append({"band": band_id, "kind": "cost-mismatch",
                               "profile": pr["name"], "yaml": pr["cost"],
                               "pdf_candidates": [kb_prof.get("cost")],
                               "detail": f"delegated to {target}, KB {DELEGATED_BAND} prices it "
                                         f"{kb_prof.get('cost')}"})
        elif pr["cost"]:
            # No printed figure could be pinned to this profile: the extraction
            # loses the roster table (OCR) or the document prints the cost in a
            # column the text forms drop. Reported, never silently skipped —
            # unless the figure was read off the page image by hand and recorded,
            # which is the only way a scan without a text layer can be verified.
            digit_read = READ_OFF_PAGE.get((band_id, str(pr["name"])))
            if digit_read and digit_read[0] == pr["cost"]:
                STATS["hero_costs_read_off_page"] = STATS.get("hero_costs_read_off_page", 0) + 1
                issues.append({"band": band_id, "kind": "cost-read-off-page",
                               "profile": pr["name"], "yaml": pr["cost"],
                               "detail": f"the figure printed on page {digit_read[1]} of the scan "
                                         f"reads {digit_read[0]}"})
            elif digit_read:
                issues.append({"band": band_id, "kind": "cost-mismatch",
                               "profile": pr["name"], "yaml": pr["cost"],
                               "pdf_candidates": [digit_read[0]],
                               "detail": f"the figure printed on page {digit_read[1]} of the scan "
                                         f"reads {digit_read[0]}"})
            else:
                issues.append({"band": band_id, "kind": "cost-unverifiable",
                               "profile": pr["name"], "yaml": pr["cost"],
                               "detail": "the source's own section prints no cost line "
                                         "for this profile"})
        # experience: "<name> starts with <N> experience [points]"
        pdf_exps = sorted({int(m.group(1))
                           for pattern in hero_name_patterns(pr["name"])
                           for text in forms.values()
                           for m in re.finditer(
                               HERO_EXPERIENCE_IDIOM.format(n=pattern), squash(text), re.I)})
        if pdf_exps:
            STATS["hero_experience"] = STATS.get("hero_experience", 0) + 1
            if pr["experience"] in pdf_exps:
                STATS["hero_experience_verified"] = STATS.get("hero_experience_verified", 0) + 1
            else:
                issues.append({"band": band_id, "kind": "experience-mismatch",
                               "profile": pr["name"], "yaml": pr["experience"],
                               "pdf_candidates": pdf_exps})
        elif delegated_target(band_id, pr["name"]):
            target = delegated_target(band_id, pr["name"])
            kb_prof = kb_band_profiles(DELEGATED_BAND).get(presence(target))
            if kb_prof is not None and kb_prof.get("experience") != pr["experience"]:
                issues.append({"band": band_id, "kind": "experience-mismatch",
                               "profile": pr["name"], "yaml": pr["experience"],
                               "pdf_candidates": [kb_prof.get("experience")],
                               "detail": f"delegated to {target}, KB {DELEGATED_BAND} "
                                         f"starts it at {kb_prof.get('experience')}"})
            elif kb_prof is not None:
                STATS["hero_experience_delegated"] = STATS.get("hero_experience_delegated", 0) + 1

    # ---- 3. roster / size lines -----------------------------------------
    roster = band["roster"]

    min_seen: list[int] = []
    sec_pat = (r"([A-Za-z ]{2,40}?warband) must include a minimum of "
               r"(?:three|four|five|\d+) models"
               r".{0,600}?maximum number of warriors in (?:the |your )?warband"
               r"(?: may)?(?: never exceed| is)\s*(\d+)")
    max_seen: list[int] = []
    for txt in forms.values():
        t2 = squash(txt)
        min_m = choose_section_match(
            t2, band["name"],
            r"([A-Za-z ]{2,40}?warband) must include a minimum of (three|four|five|\d+) models")
        if min_m:
            raw = min_m.group(2).lower()
            n = int(raw) if raw.isdigit() else NUM_WORDS.get(raw)
            if n:
                min_seen.append(n)
        # anchor max-models to the same "X warband must include ..." section
        max_m = choose_section_match(t2, band["name"], sec_pat)
        if max_m:
            max_seen.append(int(max_m.group(2)))
    if min_seen and roster["minimum_models"] not in min_seen:
        issues.append({"band": band_id, "kind": "min-models-mismatch",
                       "yaml": roster["minimum_models"], "pdf": sorted(set(min_seen))})
    if max_seen and roster["maximum_models"] not in max_seen:
        issues.append({"band": band_id, "kind": "max-models-mismatch",
                       "yaml": roster["maximum_models"], "pdf": sorted(set(max_seen))})

    gold_candidates: set[int] = set()
    for txt in forms.values():
        t2 = squash(txt)
        gold_candidates |= {int(x) for x in re.findall(
            r"(?:you have|to spend|available to spend)[^\d]{0,40}(\d{3})", t2, re.I)}
        gold_candidates |= {int(x) for x in re.findall(
            r"(\d{3})\s*(?:gold crowns|warp tokens|gcs?|tc|wt)\b", t2, re.I)}
    if gold_candidates and roster["starting_gold"] not in gold_candidates:
        issues.append({"band": band_id, "kind": "starting-gold-mismatch",
                       "yaml": roster["starting_gold"],
                       "pdf_candidates": sorted(gold_candidates)})

    # ---- 4. skill_access sanity -----------------------------------------
    for pr in profiles["profiles"]:
        acc = pr.get("skill_access") or []
        bad = [a for a in acc if a not in VALID_SKILL_TOKENS]
        if bad:
            issues.append({"band": band_id, "kind": "skill-token-invalid",
                           "profile": pr["name"], "tokens": bad})
        if pr["type"] == "henchman" and acc:
            issues.append({"band": band_id, "kind": "henchman-with-skill-access",
                           "profile": pr["name"], "tokens": acc})

    # ---- 5. rule_ids referenced exist in special-rules -------------------
    rules_doc = yaml.safe_load((pkg / "special-rules.yaml").read_text(encoding="utf-8"))
    rule_ids = {r["id"] for r in rules_doc["rules"]}
    for pr in profiles["profiles"]:
        for rid in pr.get("rule_ids") or []:
            if rid not in rule_ids:
                issues.append({"band": band_id, "kind": "rule-id-dangling",
                               "profile": pr["name"], "rule_id": rid})
    for rid in band.get("rule_ids") or []:
        if rid not in rule_ids:
            issues.append({"band": band_id, "kind": "rule-id-dangling",
                           "profile": "<band>", "rule_id": rid})

    # ---- 6. equipment list ids referenced exist --------------------------
    eq_doc = yaml.safe_load((pkg / "equipment-access.yaml").read_text(encoding="utf-8"))
    list_ids = {l["id"] for l in eq_doc["equipment_lists"]}
    for pr in profiles["profiles"]:
        for lid in pr.get("equipment_lists") or []:
            if lid not in list_ids:
                issues.append({"band": band_id, "kind": "equipment-list-dangling",
                               "profile": pr["name"], "list_id": lid})

    # ---- 7. equipment rows: source name + price --------------------------
    issues.extend(check_equipment_prices(band_id, str(mrow["id"]), eq_doc, forms,
                                         ocr_degraded, STATS))

    # ---- 8. rule fidelity ------------------------------------------------
    flat = " " + " ".join(presence(t) for t in forms.values()) + " "
    degraded = degraded_document(forms, ocr_degraded)
    for rule in rules_doc["rules"]:
        name = presence(rule.get("name") or "")
        if name and f" {name} " in flat:
            STATS["rules_anchored"] = STATS.get("rules_anchored", 0) + 1
            continue
        section = str((rule.get("source") or {}).get("section") or "")
        if section and section_anchored(section, flat):
            STATS["rules_section"] = STATS.get("rules_section", 0) + 1
            continue
        STATS["rules_unanchored"] = STATS.get("rules_unanchored", 0) + 1
        issues.append({
            "band": band_id, "rule": rule.get("id"), "name": rule.get("name"),
            "section": section,
            "kind": ("rule-name-extraction-unverifiable" if degraded
                     else "rule-name-absent"),
        })

    # ---- 9. printed skill tables vs skill_access -------------------------
    issues.extend(check_skill_tables(band_id, str(mrow["id"]), profiles["profiles"],
                                     raw_plain(str(mrow["id"]))))

    # ---- 11. hired swords / dramatis personae access ---------------------
    issues.extend(check_hireling_access(band_id, band, profiles["profiles"],
                                        rules_doc["rules"], forms))
    return issues


# Rows whose price the extraction cannot show next to the name, each adjudicated
# against the PDF by hand and recorded with its verdict (sources/2B/
# discrepancy-verdicts.md). Key: (band, list, item) -> verdict.
KNOWN_EQUIPMENT: dict[tuple[str, str, str], str] = {
    ("dwarf-guildsmen-kaz", "dwarf-warrior-equipment-list", "gromril_armour"):
        "KAZ's dwarf list prints no Gromril Armour price; it mirrors the rulebook list, "
        "whose KB copies (dwarf-rangers, dwarf-treasure-hunters) price it 75 gc. The 100 gc "
        "candidate belongs to the next sentence ('training manual ... sell for 100 gc').",
    ("dwarf-slayers-kaz", "dwarf-warrior-equipment-list", "gromril_armour"):
        "Same shared KAZ dwarf list as dwarf-guildsmen-kaz: 75 gc per the rulebook list; "
        "the 100 gc candidate is a neighbouring sentence.",
}


# How a 2B source prints a hero's recruiting cost. The rulebook's dot-leader
# column is only one of them: the supplements mostly write "<N> <Name> <cost>
# gold crowns to hire", sometimes with the count before the name and sometimes
# with no count at all, and MOU/MIM keep a dot-leader row in one column while
# the other carries the prose. Each idiom is anchored on the printed name and a
# currency word so a number from the surrounding prose cannot stand in for a
# price. {n} is the name pattern, which tolerates printed punctuation.
# Every idiom keeps the printed count in front of the name. A bare "<name> <cost>"
# is deliberately not accepted: the two-column extraction glues a skill table's
# last row or a heading to the neighbouring column's cost line ("... Private Sleuth
# Rookie 25 gold crowns Availability: Rare 12"), which would price a hero with the
# figure of the profile printed beside him.
HERO_COST_IDIOMS = (
    r"(?<![a-z0-9]){n}[^a-z0-9]{{0,4}}[.\u00b7]{{2,}}\s*(\d{{1,4}})",
    r"\b\d{{1,2}}\s*[.)]?\s*{n}\s*[.:\u2013-]?\s*(\d{{1,4}})\s*"
    r"(?:gcs?|gold\s*crowns?|gold\s*coins?)\b",
)
# Every way the 2B sources spell the figure in front of a cost line. Two are the
# supplement's own: KAZ prices the Adventurers in **gold coins**, and the Night
# Haints document prints "cold crowns" (an erratum for gold crowns).
BARE_COST_LINE = re.compile(
    r"^[\s.\u00b7*\u2044]*?(\d{1,4})\s*"
    r"(?:gcs?|gold\s*crowns?|gold\s*coins?|cold\s*crowns?|warp\s*tokens?|tokens?|"
    r"dinars?|coronas?|crowns?)\b"
    r"(?:[^\n]{0,20}?\b(?:to\s*hire|each|per\s*model)\b)?\s*\.?\s*$",
    re.I)
# "<Name> starts with <N> experience [points]", the line every supplement prints.
HERO_EXPERIENCE_IDIOM = r"{n}\s+(?:starts?|begins?)\s+with\s+(\d{{1,3}})\s+experience"


# How far past a profile's own heading its cost line can sit: the supplements
# print "<N> <Name> <cost> gold crowns to hire" under the name in the roster,
# but MOU/MIM print the figure after the profile block and its prose.
HERO_COST_WINDOW = 3500


def hero_name_patterns(name: str) -> list[str]:
    """Printed spellings of a profile's name: the name and its other number.

    A package names a fighter type the way the band list heads it ("Skaven
    Slave Champions", "Apprentices"), while the roster line that prices it is
    often singular ("0-2 Skaven Slave Champion 25 gold crowns to hire").
    """
    variants = {name}
    words = name.split()
    if words:
        last = words[-1]
        if last.endswith("s") and len(last) > 3:
            variants.add(" ".join(words[:-1] + [last[:-1]]))
        else:
            variants.add(" ".join(words[:-1] + [last + "s"]))
    return [name_pattern(v).pattern for v in sorted(variants)]


def section_anchor_pattern(section: object) -> str | None:
    """A regex for a profile's own printed heading, punctuation-tolerant.

    Headings are printed with punctuation the YAML does not carry ("1 Dwarf\n    Master Craftsman", "0-2 Daemon-Fimm"), so the anchor is built from the
    heading's own words and matched against real text - the dot-leader idiom
    needs those dots to still be there.
    """
    words = re.findall(r"[A-Za-z0-9]+", str(section).split("/")[-1])
    if not words:
        return None
    return r"\b" + r"[\W_]{0,4}".join(re.escape(w) for w in words)


# A cost line printed on a line of its own: the MIM and MOU supplements print the
# figure between the profile heading and the stat block, so no name sits beside
# it and the name-anchored idioms above cannot reach it. The page's own geometry
# is what keeps such a figure with its profile: the heading is the nearest line
# above it on the same left margin, which is also what stops a two-column page
# from pricing one warband's fighter with its neighbour's figure.
COST_COLUMN_TOLERANCE = 30   # pt: a heading starts on the cost line's own margin
COST_HEADING_GAP = 240       # pt: how far above a cost line its heading may sit
COST_HEADINGS = 4            # how many lines above a figure are offered as its heading


# Headings a decorative display face prints, recognised by the codes only that
# face produces: no page sets a heading with "$" or ">" in the body font, and
# the face has no lowercase glyphs.
DISPLAY_FONT_HINT = re.compile(r"[\$>@*]|[5-9]")
# The face's own encoding. Each letter is stored as itself minus three when the
# source text was typed in capitals and minus 0x1E when it was not, which is why
# one heading mixes both ranges; the glyphs are the same, so both ranges decode
# to one letter apiece. Derived from the headings the document also prints in
# readable type: "'KDFKBBO>ABMQ" is chosen by the roster as "Engineer Adept" and
# "$I>@H5H>SBK" prices the KB's "Black Skaven" at the same 40 gc.
DISPLAY_FONT_RANGES = ((0x3E, 0x57, 0x03), (0x24, 0x3C, 0x1E))


def symbol_font_text(text: str) -> str:
    """Decode the private-use codes an embedded symbol font leaves behind.

    The MIM profiles head their stat blocks in a symbol font: pdftohtml returns
    ``\uf053\uf068\uf065\uf061\uf072\uf06c\uf073`` where the page shows "Shearls".
    The code point minus 0xF000 is the character the glyph stands for, which is
    what makes the MIM headings readable at all.
    """
    out = []
    for char in text:
        code = ord(char)
        out.append(chr(code - 0xF000) if 0xF000 <= code <= 0xF0FF else char)
    return "".join(out)


def display_font_text(text: str) -> str | None:
    """Read a heading set in the decorative display face, or None if it is not.

    The Skaven supplements set their profile headings in a display face whose
    glyph codes are the letters displaced ("Engineer Adept" is stored as
    ``'KDFKBBO>ABMQ``), so no name-anchored check can recognise them. The face
    is identified by codes no body font prints, then translated; a heading that
    is not in the face returns None and is left exactly as extracted.
    """
    if re.search(r"[a-z]", text) or not DISPLAY_FONT_HINT.search(text):
        return None
    out = []
    for char in text:
        code = ord(char)
        for low, high, shift in DISPLAY_FONT_RANGES:
            if low <= code <= high:
                char = chr(code + shift)
                break
        out.append(char)
    return "".join(out)


def document_pages(row_id: str) -> list[int]:
    """The pages of the cached PDF that belong to this manifest row.

    A campaign PDF carries several warbands (the Karak Azgal anthology carries
    eight): the manifest records where each one starts, so a row's pages are its
    own start up to the next row's start minus one. A row without a recorded
    start is read across the whole document.
    """
    rows = [r for r in load_manifest().values() if r["id"] == row_id]
    if not rows:
        return []
    row = rows[0]
    if not (CACHE / f"{row_id}.pdf").exists():
        return []
    total = int(row.get("pdf_pages") or 0)
    start = row.get("pdf_start_page")
    if not start:
        return list(range(1, total + 1)) if total else list(range(1, 41))
    later = sorted(int(r["pdf_start_page"]) for r in load_manifest().values()
                   if r["pdf_url"] == row["pdf_url"] and r.get("pdf_start_page")
                   and int(r["pdf_start_page"]) > int(start))
    last = (later[0] - 1) if later else (total or int(start))
    return list(range(int(start), max(int(start), last) + 1))


def printed_page_runs(row_id: str, page: int) -> list[dict]:
    """Las columnas impresas de una página, con su tipografía descifrada.

    Una página a dos columnas imprime una línea de la izquierda y otra de la
    derecha a la misma altura (los suplementos MIM y MOU lo hacen), y una tabla
    de equipo, varias listas en la misma línea: la lectura que las separa es la
    del lector compartido, que corta la línea donde el hueco es de columna. Aquí
    sólo se descifra la fuente que esos suplementos usan en sus cifras.
    """
    runs: list[dict] = []
    for line in CORPUS.physical_lines(row_id, page):
        for cell in cells(line):
            text = symbol_font_text(cell.text).strip()
            if not text:
                continue
            runs.append({"top": line["top"], "left": cell.left, "right": cell.right,
                         "text": text, "words": text.split()})
    return runs


# A printed heading: short, and not a sentence (prose lines end in a full stop).
HEADING_LIKE = re.compile(r"^[^.!?]{2,46}$")
# Lines that hand a fighter's own rules to another list ("Orc Boyz – same as Da
# Mob") are not headings and carry no figure: the Sartosan supplement prints the
# whole list that way, and the package's delegated figures are checked against
# the KB's transcription of that list instead of against a neighbour's price.
DELEGATING_HEADING = re.compile(r"\bsame as\b|\bidentical to\b|\bas Da Mob\b", re.I)


def printed_bare_costs(row_id: str) -> list[dict]:
    """Every cost line printed with no name beside it, with its own heading.

    Each figure is paired with the nearest line above it on the same left
    margin, which is the heading a reader's eye pairs it with; a prose line that
    happens to sit in between is stepped over rather than mistaken for it. A
    figure whose heading cannot be found is still returned (heading ``None``),
    so the caller can see it was printed and left unattributed rather than
    assume nothing was there.
    """
    out: list[dict] = []
    for page in document_pages(row_id):
        runs = printed_page_runs(row_id, page)
        for run in runs:
            line = run["text"].strip()
            match = BARE_COST_LINE.match(line)
            if not match:
                continue
            headings: list[str] = []
            for candidate in sorted(runs, key=lambda r: r["top"], reverse=True):
                if candidate is run:
                    continue
                if not run["top"] - COST_HEADING_GAP <= candidate["top"] < run["top"] - 4:
                    continue
                if abs(candidate["left"] - run["left"]) > COST_COLUMN_TOLERANCE:
                    continue
                text = candidate["text"].strip()
                if not HEADING_LIKE.match(text) or DELEGATING_HEADING.search(text):
                    continue
                headings.append(text)
                if len(headings) == COST_HEADINGS:
                    break
            out.append({"page": page, "top": run["top"], "left": run["left"],
                        "cost": int(match.group(1)),
                        "heading": headings[0] if headings else None,
                        "readings": readings_of(headings)})
    return out


_BARE_COST_CACHE: dict[str, list[dict]] = {}


def bare_costs(row_id: str) -> list[dict]:
    """``printed_bare_costs``, read from the page dumps once per document."""
    if row_id not in _BARE_COST_CACHE:
        _BARE_COST_CACHE[row_id] = printed_bare_costs(row_id)
    return _BARE_COST_CACHE[row_id]


HEADING_COUNT = re.compile(r"^\W*(?:\d+\s*[-\u2013/ ]\s*\d+|\d+)?\W*")


def heading_stems(heading: str) -> frozenset[str]:
    """Word stems of a printed heading, without its model-count prefix."""
    stripped = HEADING_COUNT.sub("", heading)
    return frozenset(name_stems(stripped or heading))


def readings_of(headings: list[str]) -> list[str]:
    """Every reading of the lines above a figure: as extracted, and decoded.

    The lines above a cost line are offered as its heading candidates, nearest
    first: a supplement prints an aside between the heading and the figure
    ("0-1* Sea Singer", "*(Replaces Skeleton or Ghost Mate)", "40 gold crowns"),
    so the first line is not always the heading. A heading set in the display
    face is offered both ways as well, so a package named as the extraction
    spells it is recognised either way.
    """
    out: list[str] = []
    for heading in headings:
        out.append(heading)
        decoded = display_font_text(heading)
        if decoded and decoded != heading:
            out.append(decoded)
    return out


def printed_costs_by_profile(row_id: str, name: str,
                             others: Sequence[str] = ()) -> set[int]:
    """Costs the pages print for this profile on a line of its own.

    An exact stem match ("Shearls" for the package's ``Shearl``, "0-2 Fimir
    Warriors" for ``Fimir Warrior``) is the evidence. A heading whose words are
    the profile's own name plus or minus others is accepted as well, because the
    sources qualify both ways ("1 Dwarf Master Craftsman" for ``Master
    Craftsman``, "Machine Ogre" for ``Machine-Ogre``) — but never a heading whose
    extra words are numbers: the stat-block row below a figure reads "Black
    Skaven 6 4 3 4 3 1 5 1 6", and reading that as a heading would price the
    neighbour's fighter.
    """
    wanted = frozenset(name_stems(name))
    other_names = {frozenset(name_stems(other)) for other in others
                   if other and presence(other) != presence(name)}
    exact: set[int] = set()
    contained: set[int] = set()
    for entry in bare_costs(row_id):
        for heading in entry.get("readings") or []:
            stems = heading_stems(heading)
            if stems == wanted:
                exact.add(entry["cost"])
                break
            if stems and (stems < wanted or wanted < stems):
                extra = stems.symmetric_difference(wanted)
                if not any(token.isdigit() for token in extra):
                    contained.add(entry["cost"])
                    break
            if stems in other_names:
                # The line above this figure names another fighter of the same
                # warband ("Cannon Fodder" over the figure of the promotion-only
                # Captain): the figure is that fighter's, so stop reading upwards.
                break
    return exact or contained


def hero_cost_candidates(forms: dict[str, str], name: str, section: object,
                         shared: bool, row_id: str = "",
                         others: Sequence[str] = ()) -> list[int]:
    """Every recruiting cost the source prints for this hero.

    Scoped to the hero's own section: a shared document prints another
    warband's apprentice at 20 gc (the KAZ anthology carries eight warbands), so
    the search starts at the profile's own heading when that heading is printed
    and never reaches across it. A shared document whose heading cannot be
    located is left unverified rather than guessed at; a document that belongs
    to this package alone is searched whole.
    """
    patterns = hero_name_patterns(name)
    anchor = section_anchor_pattern(section)
    found: set[int] = set()
    for text in forms.values():
        flat = squash(text)
        match = re.search(anchor, flat, re.I) if anchor else None
        if match:
            window = flat[match.start():match.start() + HERO_COST_WINDOW]
        elif shared:
            continue
        else:
            window = flat
        for pattern in patterns:
            for idiom in HERO_COST_IDIOMS:
                found |= {int(m.group(1))
                          for m in re.finditer(idiom.format(n=pattern), window, re.I)}
    # The other two shapes the supplements use put the figure on a line of its
    # own: MOU/REL print the heading, then the cost line, then the prose; MIM
    # prints the cost line first and the stat block last. Both are read from the
    # page's own geometry, which is the only form that keeps a column apart from
    # its neighbour.
    if row_id:
        found |= printed_costs_by_profile(row_id, name, others)
    return sorted(found)


# La divisa de una lista de precios («gc», «wt/tc» de los skaven, «dinars» de las
# árabes) y la cifra base de un precio de fórmula («75+5D6 gold crowns», que es el
# que guarda el catálogo) los lee ``printed_entries``, junto con la fila.


def name_pattern(name: str) -> re.Pattern:
    """Match a printed name in raw text, tolerating punctuation and word splits.

    Names are tokenised into alphanumeric words so the printed punctuation does
    not have to match the YAML spelling: a curly apostrophe ("Bramstetter\u2019s")
    matches a straight one, "Scimitar/Sword" matches "Scimitar (Sword)" and a
    line-wrapped name ("Toughened leat hers") still matches.
    """
    parts = [re.escape(part) for part in re.findall(r"[A-Za-z0-9]+", name)]
    if not parts:
        return re.compile(r"(?!)")
    return re.compile(r"(?<![A-Za-z0-9])" + r"[\W_]{0,4}".join(parts), re.I)


_PRICE_ROWS: dict[str, list[dict]] = {}


def printed_price_rows(row_id: str, pages: Sequence[int] | None = None) -> list[dict]:
    """Las filas que tasan un ítem en las páginas leídas, una vez por corrida.

    Cada fila es lo que la página imprime en una columna: el nombre y su precio
    en la misma celda, o el nombre en la celda de arriba que cubre su horizontal
    (las listas a dos columnas y las tablas de equipo parten la celda). El precio
    no puede venir de otra fila, que es lo que una ventana de texto admitía.

    Por defecto se leen las páginas del tramo de la banda, que es donde el lector
    sabe qué lista imprime cada documento; el cotejo de precios pide además el
    documento entero (``document_price_rows``).
    """
    key = (row_id, None if pages is None else tuple(pages))
    if key not in _PRICE_ROWS:
        rows: list[dict] = []
        tail: list[dict] = []
        # La lista de equipo puede cruzar la página: el nombre cierra una (p3 de los
        # corsarios oscuros) y su tarifa abre la siguiente. Las últimas líneas de la
        # página anterior se leen como contexto de la que empieza, y sólo las filas
        # cuya tarifa se imprime en la página se le apuntan.
        for page in (document_pages(row_id) if pages is None else pages):
            lines = CORPUS.physical_lines(row_id, page)
            for row in price_rows(tail + lines, context=len(tail)):
                rows.append({**row, "page": page})
            tail = lines[-2:]
        _PRICE_ROWS[key] = rows
    return _PRICE_ROWS[key]


def document_price_rows(row_id: str) -> list[dict]:
    """Las filas que tasan en **todo** el documento, leídas una vez por corrida.

    El anuario de Karak Azgal imprime las listas de equipo de sus ocho bandas en
    una sección común, fuera del tramo que el manifiesto asigna a cada una: esas
    páginas son de este documento igual que las suyas, y sin ellas la tarifa
    quedaría sin comparar teniéndola la fuente delante.
    """
    return printed_price_rows(row_id, CORPUS.pages(row_id))


# La forma con la que una lista tasa una fila sin cifra: un múltiplo del precio de
# otra cosa («Gromril Weapon 3x the cost», «Ithilmar Weapon .... 2 x Cost*»).
MULTIPLIER = re.compile(r"(\d{1,2})\s*[x\u00d7]\s*(?:the\s*)?cost\b", re.I)


def price_multiplier(row_id: str, patterns: Sequence[re.Pattern]) -> int | None:
    """El múltiplo con el que la fuente tasa la fila, cuando no imprime una cifra.

    Se lee de la línea impresa que nombra al ítem, que es donde la fuente lo
    declara («Gromril Weapon 3x the cost»), y en el documento entero: la lista
    puede estar fuera del tramo de la banda, como sus precios.
    """
    for line in CORPUS.document_lines(row_id):
        text = str(line.get("text") or "")
        hit = MULTIPLIER.search(text)
        if hit and any(pattern.search(text) for pattern in patterns):
            return int(hit.group(1))
    return None


def price_rows_for_name(row_id: str, patterns: Sequence[re.Pattern]) -> tuple[set[int], bool]:
    """Los precios que el documento imprime junto a ese nombre, y si es fórmula.

    Se leen primero las filas del tramo de la banda y, sólo si ahí no hay ninguna
    que nombre al ítem, las del documento entero: la fila se acepta cuando su
    celda —la del precio, la de su izquierda o la de arriba que la cubre— nombra
    al ítem, así que ensanchar las páginas no afloja el cotejo, sólo lo hace
    alcanzar la lista que el documento imprime más allá de su tramo.
    """
    for rows in (printed_price_rows(row_id), document_price_rows(row_id)):
        prices: set[int] = set()
        formula = False
        for price_row in rows:
            # La fila imprime el nombre en su celda o lo deja en la de arriba
            # («Short» / «Bow . . . 10 gc»): las dos formas son la misma fila.
            labels = [price_row["name"], price_row["above"],
                      f"{price_row['above']} {price_row['name']}".strip(),
                      *(price_row.get("names") or [])]
            if not any(pattern.search(label) for pattern in patterns
                       for label in labels if label):
                continue
            prices |= set(price_row["prices"])
            # A formula counts only when it sits in this row's own price cell:
            # a neighbouring row's D6 must not downgrade a plain price into
            # "formula" and hide a wrong figure.
            if price_row["formula"]:
                formula = True
        if prices:
            return prices, formula
    return set(), False


def check_equipment_prices(band_id: str, row_id: str, eq_doc: dict, forms: dict[str, str],
                           ocr_degraded: bool, stats: dict) -> list[dict]:
    """Every priced row must show its price on a source price line.

    Price tables read "<name> . . . . <price>", so a price is what a cell (or the
    cell above it, when the list wraps) prints after the item's own name and a
    currency ("1st free/2 gc" yields the later-purchase price, which is what the
    YAML stores). A row is accepted when any occurrence on any page agrees (the
    same item is printed in several band sections); a row with priced lines but no
    agreement anywhere is a candidate error, and a row whose name the document
    never prints is unverifiable from the extraction.
    """
    issues: list[dict] = []
    item_names = load_item_names()
    # The extractor punctuates leader dots with spaces ("Dagger .. .. .. .. 1st
    # free/2 gc"): collapsing each leader run restores the line structure for the
    # name-presence check without moving any digit.
    texts = {form: re.sub(r"(?:\s*\.\s*){3,}", " ......... ", text)
             for form, text in forms.items()}
    for lst in eq_doc.get("equipment_lists") or []:
        list_id = str(lst.get("id"))
        for entry in lst.get("items") or []:
            cost = entry.get("cost")
            if not isinstance(cost, int):
                continue
            verdict = KNOWN_EQUIPMENT.get((band_id, list_id, str(entry.get("item_id"))))
            if verdict:
                stats["priced_rows"] = stats.get("priced_rows", 0) + 1
                stats["price_adjudicated"] = stats.get("price_adjudicated", 0) + 1
                issues.append({
                    "band": band_id, "list": list_id, "item": entry.get("item_id"),
                    "yaml": cost, "kind": "equipment-price-adjudicated", "detail": verdict,
                })
                continue
            names = source_names_for(entry, item_names, band_id)
            if not names:
                continue
            patterns = [name_pattern(source_name) for source_name in names
                        if len(norm(source_name)) >= 3]
            found = any(pattern.search(text) for pattern in patterns
                        for text in texts.values())
            prices, formula = price_rows_for_name(row_id, patterns)
            agreed = cost in prices
            stats["priced_rows"] = stats.get("priced_rows", 0) + 1
            if agreed or (formula and cost in (0, None)):
                stats["price_verified"] = stats.get("price_verified", 0) + 1
                continue
            delegated = wordings.delegated_reason("2B", band_id, list_id)
            if delegated:
                # The document delegates this list to the rulebook: fall back to the
                # KB transcription of the rulebook list with the same id.
                kb_cost = (kb_list_prices().get(list_id) or {}).get(str(entry.get("item_id")))
                stats["price_rulebook"] = stats.get("price_rulebook", 0) + 1
                if kb_cost == cost:
                    continue
                if kb_cost is None:
                    issues.append({
                        "band": band_id, "list": list_id, "item": entry.get("item_id"),
                        "yaml": cost, "kind": "equipment-price-rulebook-reference",
                        "detail": delegated})
                    continue
                issues.append({
                    "band": band_id, "list": list_id, "item": entry.get("item_id"),
                    "yaml": cost, "pdf_candidates": [kb_cost],
                    "kind": "equipment-price-mismatch",
                    "detail": f"rulebook list (KB {list_id}) prices this row {kb_cost} gc"})
                continue
            issue = {
                "band": band_id, "list": list_id, "item": entry.get("item_id"),
                "source_names": names, "yaml": cost}
            # La fila que la fuente tasa con un múltiplo del precio de otra cosa
            # («Gromril Weapon 3x the cost», «Ithilmar Weapon 2 x Cost*») no tiene
            # cifra propia: el paquete guarda ese múltiplo cuando la fuente lo
            # declara uno a uno —3 por «3x the cost»— o 0 cuando la tarifa es la de
            # otra cosa, que es no guardar cifra ninguna. Las dos formas quedan
            # verificadas por la que la fuente imprime y se cuentan aparte, para
            # que el total de las de cifra no las esconda.
            multiple = None if prices else price_multiplier(row_id, patterns)
            if not found:
                issues.append({**issue, "kind": ("equipment-name-ocr-unverifiable"
                                                 if ocr_degraded
                                                 else "equipment-name-not-in-text")})
            elif multiple is not None and cost in (0, multiple):
                stats["price_verified"] = stats.get("price_verified", 0) + 1
                stats["price_multiplier"] = stats.get("price_multiplier", 0) + 1
            elif multiple is not None:
                issues.append({**issue, "kind": "equipment-price-multiplier-mismatch",
                               "pdf_candidates": [multiple],
                               "detail": f"the source prices it as a multiple, not with a "
                                         f"figure: {multiple}x the cost"})
            elif not prices:
                issues.append({**issue, "kind": ("equipment-price-ocr-unverifiable"
                                                 if ocr_degraded
                                                 else "equipment-price-line-unverifiable")})
            elif formula:
                issues.append({**issue, "kind": "equipment-price-formula",
                               "pdf_candidates": sorted(prices)[:6]})
            else:
                issues.append({**issue, "kind": "equipment-price-mismatch",
                               "pdf_candidates": sorted(prices)[:6]})
    return issues


# --------------------------------------------------------------------------- #
# Fidelity checks (8-11). Each one is evaluated on both extraction forms.
# --------------------------------------------------------------------------- #

def presence(value: object) -> str:
    """Order-preserving alphanumerics, for searching a name inside long prose."""
    return re.sub(r"[^a-z0-9]+", " ", norm(value).replace("-", " ").replace("'", " ")).strip()


# Words that name a document structure rather than identify a section: a
# citation is proven by its distinctive words ("Mobsmen special skills" by
# "Mobsmen"), because the sources print the heading of that section in their own
# words ("MOBSMEN SKILL TABLE").
GENERIC_SECTION_WORDS = {"skills", "skill", "rules", "rule", "special", "equipment",
                         "list", "lists", "table", "tables", "note", "variant", "section",
                         "warband", "henchmen", "heroes"}


def word_present(word: str, flat: str) -> bool:
    """The word is printed, allowing for the source's own inflection.

    A four-letter prefix is enough for the names that matter here and absorbs
    the plural forms the documents switch between ("Sea Elf" / "Sea Elves",
    "Mobsmen" / "Mobsman").
    """
    return bool(re.search(r"(?<![a-z])" + re.escape(word[:4] if len(word) >= 4 else word), flat))


def section_anchored(section: str, flat: str) -> bool:
    """The cited section exists in the text: its words are printed.

    Order and punctuation are not identity (the documents wrap and repeat text
    freely), and neither are the generic nouns of a heading, so a rule named
    editorially ("General Pirate rules", "Strigany Special Skills") still
    proves it was transcribed from the section it cites. A section named only
    with generic words ("Special Skills") is anchored by all of them.
    """
    for segment in section.split("/"):
        words = [w for w in presence(segment).split() if len(w) >= 4]
        if not words:
            continue
        wanted = [w for w in words if w not in GENERIC_SECTION_WORDS] or words
        if all(word_present(w, flat) for w in wanted):
            return True
    return False


def degraded_document(forms: dict[str, str], ocr_degraded: bool) -> bool:
    """True when the extraction cannot be searched for names at all.

    Two cases are known: the KEP scans (manifest ``pdf_is_text: false``) and
    Metal-mongers, whose embedded fonts decode to wrong glyphs, so long words
    come out vowel-less ("5HVOB", "KDFKBBOP"). A name miss there says nothing
    about the package, so it is reported as unverifiable instead.
    """
    if ocr_degraded:
        return True
    words = re.findall(r"[A-Za-z]{5,}", " ".join(forms.values()))
    if not words:
        return True
    odd = sum(1 for w in words if not re.search(r"[aeiouAEIOU]", w))
    return odd / len(words) > 0.05


SKILL_TOKENS = ("combat", "shooting", "academic", "strength", "speed", "special",
                "musicianship", "pirate")
SKILL_LABEL = re.compile(r"\b(" + "|".join(t.capitalize() for t in SKILL_TOKENS) + r")\b", re.I)
SKILL_HEADING = re.compile(r"(?:SPECIAL\s+)?SKILLS?(?:\s+TABLE)?", re.I)
PAGE_MARKER = re.compile(r"=====\s*page\s+(\d+)\s*=====")


def printed_words(line: dict) -> list[tuple[float, float, str]]:
    """Las palabras de una línea física con su tramo: (izquierda, derecha, texto).

    Una tabla de habilidades reparte sus columnas entre *palabras* —cada encabezado
    es una— y no entre celdas: la fuente imprime varios encabezados juntos, con
    menos hueco del que separa dos columnas, y una celda los abarca todos
    («Shooting Academic Strength»). Leerla por palabra es lo que mantiene cada
    marca bajo su propia lista; la página, la fila y sus celdas las lee el lector
    compartido.
    """
    return [(left, right, text) for left, _top, right, text in line.get("spans") or []]


def printed_skill_tables(row_id: str, plain: str) -> list[dict]:
    """Skill tables of a document, with the skill lists each row's X marks tick.

    The document's own page markers say which page a table is on; the marks are
    then attributed to the column heading nearest in coordinates. A mark that
    sits between two headings is left unattributed and the table reported as
    unparsed, never guessed.
    """
    lines = plain.splitlines()
    tables: list[dict] = []
    page = 0
    for index, line in enumerate(lines):
        marker = PAGE_MARKER.search(line)
        if marker:
            page = int(marker.group(1))
            continue
        if index + 2 >= len(lines) or page <= 0:
            continue
        heading = SKILL_HEADING.search(line.strip())
        if not heading or SKILL_LABEL.search(line):
            continue
        # Structure of every printed table: a title, the heading row, then the
        # rows of marks.
        labels = {m.group(1).lower() for m in SKILL_LABEL.finditer(lines[index + 1])}
        if len(labels) < 2 or not re.search(r"\bX\b", lines[index + 2], re.I):
            continue
        page_lines = CORPUS.physical_lines(row_id, page)
        if not page_lines:
            tables.append({"subject": line.strip(), "page": page, "rows": [],
                           "why": "page coordinates unavailable (pdftohtml)"})
            continue
        # The heading row: the line whose cells carry the skill labels. A page can
        # print several tables, so the heading row is taken from *below* the
        # table's own title; without that anchor the marks of one table would be
        # compared against the profile of the next.
        title_key = presence(line.strip())
        title_top = None
        for entry in page_lines:
            joined = presence(" ".join(cell.text for cell in cells(entry)))
            if joined == title_key:
                title_top = entry["top"]
                break
        header_top = None
        for entry in page_lines:
            if title_top is not None and entry["top"] <= title_top:
                continue
            labels_on_line = {m.group(1).lower() for cell in cells(entry)
                              for m in SKILL_LABEL.finditer(cell.text)}
            if len(labels_on_line) >= 2:
                header_top = entry["top"]
                break
        if header_top is None:
            tables.append({"subject": line.strip(), "page": page, "rows": [],
                           "why": ("heading row not found on the page" if title_top is not None
                                   else "table title not found on the page")})
            continue
        columns: list[tuple[str, float]] = []
        seen: set[str] = set()
        header = next(entry for entry in page_lines if entry["top"] == header_top)
        for left, right, text in printed_words(header):
            match = SKILL_LABEL.fullmatch(text)
            if match and match.group(1).lower() not in seen:
                seen.add(match.group(1).lower())
                columns.append((match.group(1).lower(), (left + right) / 2))
        columns.sort(key=lambda entry: entry[1])
        if len(columns) < 2:
            tables.append({"subject": line.strip(), "page": page, "rows": [],
                           "why": "column headings not found on the page"})
            continue
        leftmost = min(centre for _token, centre in columns)
        rows: list[dict] = []
        for entry in page_lines:
            if entry["top"] == header_top or abs(entry["top"] - header_top) > 140:
                continue
            row_words = printed_words(entry)
            marks_on_line = [word for word in row_words
                             if re.fullmatch(r"X+", word[2], re.I)]
            if not marks_on_line:
                continue
            for left, right, text in marks_on_line:
                centre = (left + right) / 2
                ranked = sorted((abs(c - centre), token) for token, c in columns)
                if len(ranked) > 1 and ranked[1][0] - ranked[0][0] < 12:
                    rows.append({"name": "", "marks": [],
                                 "why": "a mark sits between two columns"})
                    continue
                name = ""
                for rleft, _rright, rtext in row_words:
                    if rleft < leftmost - 20 and not SKILL_LABEL.fullmatch(rtext):
                        if presence(rtext) and not re.fullmatch(r"\d+", rtext):
                            name = rtext if not name else f"{name} {rtext}"
                rows.append({"name": name, "marks": [ranked[0][1]], "why": ""})
        # merge the marks of every row printed with the same profile name
        merged: dict[str, dict] = {}
        for row in rows:
            key = presence(row["name"])
            if row["why"]:
                merged.setdefault(key or "<?>", {"name": row["name"], "marks": [],
                                                 "why": row["why"]})
                continue
            entry = merged.setdefault(key, {"name": row["name"], "marks": [], "why": ""})
            entry["marks"] = sorted(set(entry["marks"]) | set(row["marks"]))
        tables.append({"subject": line.strip(), "page": page,
                       "rows": [merged[key] for key in merged], "why": ""})
    return tables


def name_stems(value: object) -> set[str]:
    """Word stems of a name: singular, then a four-letter prefix.

    The sources print the same fighter as "Elder" and "Elders", and the tables
    label rows with the singular ("Squire") where the package profile is plural;
    a prefix absorbs those without collapsing names that differ ("Boss" does not
    become "Big Boss").
    """
    irregular = {"men": "man", "feet": "foot", "dice": "die", "elves": "elf", "dwarves": "dwarf"}
    stems: set[str] = set()
    for word in presence(value).split():
        word = irregular.get(word, word[:-1] if len(word) > 4 and word.endswith("s") else word)
        stems.add(word[:4] if len(word) >= 4 else word)
    return stems


def match_profile(subject: str, profiles: list[dict], containment: bool = False) -> dict | None:
    """The one profile a name matches, or None when it matches none/several.

    Exact matches (on stems) always win. Containment — "Noble" for "Imperial
    Noble" — is only consulted when asked for, because it is what a *package's*
    own tables need and what would otherwise attach another warband's row to a
    similarly named catalogue entry.
    """
    want = name_stems(subject)
    if not want:
        return None
    exact = [p for p in profiles if name_stems(p.get("name") or "") == want]
    if len(exact) == 1:
        return exact[0]
    if not containment:
        return None
    loose = [p for p in profiles
             if want <= name_stems(p.get("name") or "")
             or name_stems(p.get("name") or "") <= want]
    return loose[0] if len(loose) == 1 else None


_CATALOG_PROFILES: list[dict] = []


def catalogue_profiles() -> list[dict]:
    """Every hireling profile of the KB and both staging catalogues."""
    if not _CATALOG_PROFILES:
        for pattern in HIRELING_GLOBS:
            for path in sorted(glob.glob(pattern, recursive=True)):
                doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
                for profile in doc.get("profiles") or []:
                    if isinstance(profile, dict) and profile.get("name"):
                        _CATALOG_PROFILES.append(profile)
    return _CATALOG_PROFILES


PROSE_ROW = re.compile(
    r"^(?P<name>[A-Z][A-Za-z' -]{2,30}):\s*(?P<marks>"
    r"(?:Combat|Shooting|Academic|Strength|Speed|Special|Musicianship|Pirate)"
    r"(?:\s*(?:,|and|&)\s*(?:Combat|Shooting|Academic|Strength|Speed|Special|Musicianship|Pirate))*)$")


def printed_skill_prose(plain: str) -> list[dict]:
    """Skill lists printed as prose rather than as a table, per page.

    Several sources state a hero's lists in one line instead of ticking columns
    ("Boss: Combat, Shooting, Strength, Speed, Special"), which is the same
    evidence in a different shape. The page is kept because an anthology prints
    one such block per warband and they have to be told apart the same way the
    tables are.
    """
    rows: list[dict] = []
    page = 0
    for line in plain.splitlines():
        marker = PAGE_MARKER.search(line)
        if marker:
            page = int(marker.group(1))
            continue
        match = PROSE_ROW.match(line.strip())
        if not match:
            continue
        marks = sorted({piece.group(0).lower()
                        for piece in SKILL_LABEL.finditer(match.group("marks"))})
        if len(marks) >= 2:
            rows.append({"name": match.group("name").strip(), "marks": marks,
                         "page": page})
    return rows


def table_is_this_bands(table: dict, profiles: list[dict]) -> bool:
    """Whether a printed table belongs to the package being audited.

    An anthology prints every warband's table in one document, and a fighter
    type recurs across them (a "Boss" in both the Savage Orc and the Night
    Goblin list). A table belongs to the package when most of its rows name this
    package's own profiles - or the whole table is that one fighter.
    """
    rows = table["rows"]
    if not rows:
        return False
    resolved = sum(1 for row in rows if match_profile(row["name"], profiles, containment=True))
    return (resolved >= 2 and resolved * 2 >= len(rows)) or (len(rows) == 1 and resolved == 1)


def check_skill_tables(band_id: str, row_id: str, profiles: list[dict],
                       plain: str) -> list[dict]:
    """Printed skill lists versus the ``skill_access`` on file.

    A row is resolved by its own label, never by the table title alone: in an
    anthology the title would attach another warband's marks to this package's
    profile of the same name. Rows of tables belonging to another warband, rows
    whose marks could not all be attributed, and rows naming no profile of the
    package are reported as informational findings rather than compared.
    """
    issues: list[dict] = []
    pool = list(profiles) + catalogue_profiles()
    # Resolve every row first: one profile can be printed in more than one table
    # of the same document with different marks, because an anthology carries
    # several warbands' tables and a fighter type recurs across them. Conflicting
    # evidence is not evidence, so those are reported unverifiable, never compared.
    resolved: dict[str, dict] = {}
    rows_to_check: list[dict] = []
    for table in printed_skill_tables(row_id, plain):
        if table["why"]:
            issues.append({"band": band_id, "kind": "skill-table-unparsed",
                           "table": table["subject"], "page": table["page"],
                           "detail": table["why"]})
            continue
        if not table_is_this_bands(table, profiles):
            issues.append({"band": band_id, "kind": "skill-table-other-warband",
                           "table": table["subject"], "page": table["page"],
                           "rows": [row["name"] for row in table["rows"]],
                           "detail": "the document prints this table for another warband"})
            continue
        for row in table["rows"]:
            rows_to_check.append({**row, "table": table["subject"], "page": table["page"]})
    prose_by_page: dict[int, list[dict]] = {}
    for row in printed_skill_prose(plain):
        prose_by_page.setdefault(row["page"], []).append(row)
    for page, block in prose_by_page.items():
        block_table = {"subject": f"prose skill lists (page {page})", "page": page,
                       "rows": block}
        if not table_is_this_bands(block_table, profiles):
            issues.append({"band": band_id, "kind": "skill-table-other-warband",
                           "table": block_table["subject"], "page": page,
                           "rows": [row["name"] for row in block],
                           "detail": "the document prints these lists for another warband"})
            continue
        for row in block:
            rows_to_check.append({**row, "table": block_table["subject"]})

    if rows_to_check:
        for row in rows_to_check:
            if row.get("why") or not row["marks"]:
                issues.append({"band": band_id, "kind": "skill-table-unparsed",
                               "table": row["table"], "page": row["page"],
                               "row": row["name"], "detail": row.get("why") or "no marks"})
                continue
            # A row resolves by its own label: in an anthology one page prints
            # several warbands' tables, and a row's own name is the only thing
            # that says whose marks these are.
            target = match_profile(row["name"], profiles, containment=True)
            if target is None:
                issues.append({"band": band_id, "kind": "skill-table-unmapped",
                               "subject": row["name"],
                               "marks": row["marks"], "page": row["page"],
                               "table": row["table"],
                               "detail": "no profile of that name in the package"})
                continue
            if str(target.get("type") or "") == "henchman":
                # Henchmen carry no skill access in the KB schema, so the marks a
                # row prints for one are not comparable with it.
                issues.append({"band": band_id, "kind": "skill-table-henchman-row",
                               "profile": target.get("name"), "table": row["table"],
                               "marks": row["marks"], "page": row["page"]})
                continue
            key = presence(target.get("name") or target.get("id") or "")
            entry = resolved.setdefault(key, {"profile": target, "rows": []})
            entry["rows"].append({"marks": row["marks"], "table": row["table"],
                                  "page": row["page"]})

    for entry in resolved.values():
        target = entry["profile"]
        access = sorted(str(a) for a in target.get("skill_access") or [])
        variants = {tuple(row["marks"]) for row in entry["rows"]}
        if len(variants) > 1 and tuple(access) not in variants:
            issues.append({"band": band_id, "kind": "skill-table-conflicting",
                           "profile": target.get("name"), "yaml": access,
                           "source": sorted(list(v) for v in variants),
                           "detail": "the document prints this fighter's marks differently"
                                     " in more than one table"})
            continue
        row = next(r for r in entry["rows"] if tuple(r["marks"]) == tuple(access)) \
            if tuple(access) in variants else entry["rows"][0]
        STATS["skill_tables"] = STATS.get("skill_tables", 0) + 1
        if access != row["marks"]:
            issues.append({"band": band_id, "kind": "skill-table-mismatch",
                           "profile": target.get("name"), "profile_id": target.get("id"),
                           "yaml": access, "source": row["marks"],
                           "table": row["table"], "page": row["page"]})
    return issues


def slug_index(rows: list[dict]) -> dict[str, str]:
    """pdf filename slug (undecorated) -> manifest row id."""
    out: dict[str, str] = {}
    for row in rows:
        stem = unquote(str(row.get("pdf_url") or "").rsplit("/", 1)[-1]).rsplit(".", 1)[0]
        if stem:
            out[norm(stem)] = str(row["id"])
    return out


def extra_document(slug: str) -> str | None:
    """Geometry reading of a cached source that is not one of the 60 manifest rows.

    Some material a 2B package cites lives outside the 60 graded documents (the
    Miracle Workers chapter); it is cached under ``2b-pdfs/extra`` and read with
    the same reader, so the evidence that sustains a spell list is the same as
    that of a manifest document.
    """
    want = norm(slug)
    for path in sorted(EXTRA.glob("*.pdf")):
        stem = norm(path.stem)
        if stem and (stem in want or want in stem):
            return EXTRA_CORPUS.text(path.stem)
    return None


def check_magic_prayers(rows: list[dict]) -> list[dict]:
    """Every spell/prayer of catalog/magic-2b.yaml against the document it cites."""
    issues: list[dict] = []
    if not MAGIC.exists():
        return issues
    slugs = slug_index(rows)
    by_id = {str(r["id"]): r for r in rows}
    document = yaml.safe_load(MAGIC.read_text(encoding="utf-8")) or {}
    for lore in document.get("lores") or []:
        ref = (lore.get("source_refs") or [{}])[0]
        slug = unquote(str(ref.get("url") or "").rsplit("/", 1)[-1]).rsplit(".", 1)[0]
        row_id = slugs.get(norm(slug))
        if row_id:
            text = "".join(load_texts(row_id).values())
        else:
            text = extra_document(slug) or ""
        label = row_id or slug
        if not text:
            issues.append({"band": label, "kind": "lore-source-missing",
                           "lore": lore.get("id"), "source": slug})
            continue
        # Anchor the difficulty evidence to the lore's own section when its
        # heading is printed (the section name, else the lore name).
        anchor = presence(str(ref.get("section") or "").split("/")[-1]) or presence(lore.get("name"))
        pos = norm(text).find(anchor) if anchor else -1
        window = text[pos:pos + 6000] if pos >= 0 else text
        printed = {int(m.group(1)) for m in re.finditer(r"[Dd]ifficulty[:.]?\s*(\d+)", window)}
        auto_printed = bool(re.search(r"[Dd]ifficulty[:.]?\s*Auto", window))
        flat = " " + presence(text) + " "
        for spell in lore.get("spells") or []:
            name = presence(spell.get("name") or "")
            if not name:
                continue
            STATS["spells_checked"] = STATS.get("spells_checked", 0) + 1
            if f" {name} " not in flat:
                issues.append({"band": label, "kind": "spell-absent-from-source",
                               "lore": lore.get("id"), "spell": spell.get("name")})
                continue
            STATS["spells_anchored"] = STATS.get("spells_anchored", 0) + 1
            value = spell.get("difficulty")
            if isinstance(value, int) and not isinstance(value, bool) and printed \
                    and value not in printed:
                issues.append({"band": label, "kind": "spell-difficulty",
                               "lore": lore.get("id"), "spell": spell.get("name"),
                               "yaml": value, "source": sorted(printed)})
            elif str(value).lower() == "auto" and printed and not auto_printed:
                issues.append({"band": label, "kind": "spell-difficulty",
                               "lore": lore.get("id"), "spell": spell.get("name"),
                               "yaml": "auto", "source": sorted(printed)})
            if not (spell.get("name_i18n") or {}).get("es"):
                issues.append({"band": label, "kind": "spell-i18n-name",
                               "lore": lore.get("id"), "spell": spell.get("name")})
        if lore.get("id") and not (lore.get("name_i18n") or {}).get("es"):
            issues.append({"band": label, "kind": "spell-i18n-name",
                           "lore": lore.get("id"), "spell": "<lore>"})
    return issues


ACCESS_VERB = re.compile(
    r"\b(?:may (?:only )?(?:hire|employ|recruit)|has access to the following|"
    r"may not (?:hire|employ|recruit))\b", re.I)
HIRELING_WORD = re.compile(r"hired swords?|hirelings?|dramatis personae", re.I)
LEADER_DOTS = re.compile(r"(?:\.\s*){5,}")
# Words that name a race or a practice, which an access sentence mentions
# without offering it as a hireling ("may not hire any Dark Elves").
CATEGORY_WORDS = {
    "human", "humans", "dwarf", "dwarfs", "dwarves", "elf", "elfs", "elves", "skaven",
    "goblin", "goblins", "night", "orc", "orcs", "savage", "undead", "ogre", "ogres",
    "halfling", "halflings", "chaos", "black", "powder", "poison", "poisons", "magic",
    "witch", "witches", "wizard", "wizards", "vampire", "vampires", "strigoi", "sea",
    "dark", "dramatic", "dramatis", "persona", "personae", "ranger", "rangers",
    "mercenary", "mercenaries", "khorne", "evil",
}

# A candidate name is rejected when it ends in one of these, which name the
# game's structures rather than a hireling ("...any Hired Swords", "Choice of
# Warriors", "...equipment list").
NAME_STOPWORDS = {
    "warband", "warbands", "band", "bands", "rules", "rule", "table", "tables", "list",
    "lists", "skills", "skill", "equipment", "models", "model", "warriors", "warrior",
    "heroes", "hero", "henchmen", "henchman", "sword", "swords", "personae", "hire",
    "hired", "following", "them", "any", "all", "the", "and", "or", "additional",
    "experience", "starting", "crowns", "gold", "choice", "best", "page", "weapons",
    "armour", "only", "which", "their", "these", "those", "each", "unless",
}
# Source wording that names the same hireling as a catalogue entry.
HIRELING_SYNONYMS = {
    "black orc": "Black Orc Bodyguard",
    "snerik": "Snerik, Night Goblin Scout",
    "snerik night goblin scout": "Snerik, Night Goblin Scout",
    "dwarf trollslayer": "Dwarf Troll Slayer",
    "pitfighter": "Pit Fighter",
    "imp assassin": "Imperial Assassin",
}


def trim_candidate(name: str) -> str:
    """Drop the structural words a capitalized run swallows from its sentence.

    The regex that finds candidates runs to the next capitalized word, so it
    grabs whatever follows a name: "Black Orc DP" (the document's DP marker),
    "Snerik Choice" ("Choice of Warriors", the next heading). Trailing
    abbreviations, digits and known structures are trimmed, repeatedly, so the
    name itself is judged instead of the words glued to it.
    """
    words = name.split()
    while len(words) > 1:
        last = words[-1]
        if (presence(last) in NAME_STOPWORDS or last.isdigit()
                or (len(last) >= 2 and last.isupper())):
            words.pop()
            continue
        break
    return " ".join(words)


def token_stems(value: object) -> set[str]:
    """Word stems (six-letter prefix) so "Goblins" matches "Goblin"."""
    return {w[:6] for w in presence(value).split() if len(w) >= 3}


def hireling_access_statements(raw: str, band: object) -> list[str]:
    """A band's own sentences that grant or forbid Hired Swords / Dramatis Personae.

    Three qualifications, each of which the sources force:

    * only sentences that speak of hirelings (the same verbs introduce in-game
      skills: "the leader may employ this skill once per game");
    * the table of contents is skipped, its dot leaders being the giveaway; and
    * the sentence has to belong to the band whose package is being audited. An
      anthology carries one document for eight warbands, so the sentence's own
      introducer has to name this band ("the Night Goblin warband may hire...",
      "A Savage Orc warband may hire..."); without that, one warband's access
      line would be reported against every package sharing the document, and the
      document's campaign-wide paragraph ("the warbands may hire any Hired
      Swords ... written specially for Karak Azgal") against all of them.
    """
    stems = token_stems(band)
    out: list[str] = []
    for match in ACCESS_VERB.finditer(raw):
        tail = raw[match.start():match.start() + 260]
        if not HIRELING_WORD.search(tail):
            continue
        before = raw[max(0, match.start() - 400):match.start()]
        if LEADER_DOTS.search(before) or LEADER_DOTS.search(tail):
            continue
        introducer = raw[max(0, match.start() - 150):match.start()]
        if stems and not (token_stems(introducer) & stems):
            continue
        out.append(re.sub(r"\s+", " ", raw[max(0, match.start() - 60):match.start() + 260]))
    return out


_MANIFEST_NAMES: dict[str, str] = {}


def manifest_row_name(band_id: str) -> str:
    """The index name the manifest records for a package ("Night Goblins")."""
    if not _MANIFEST_NAMES:
        for row in load_manifest().values():
            _MANIFEST_NAMES[str(row["id"])] = str(row.get("broheim_name") or "")
            for pkg in row.get("packages") or []:
                _MANIFEST_NAMES[str(pkg)] = str(row.get("broheim_name") or "")
    return _MANIFEST_NAMES.get(band_id, "")


_CATALOG_NAMES: list[str] = []


def catalogue_names() -> list[str]:
    if not _CATALOG_NAMES:
        _CATALOG_NAMES.extend(presence(p["name"]) for p in catalogue_profiles())
    return _CATALOG_NAMES


def check_hireling_access(band_id: str, band: dict, profiles: list[dict],
                          rules: list[dict], forms: dict[str, str]) -> list[dict]:
    """Source access sentences versus the package's rules and the catalogues.

    A sentence the source prints about this band has to be reflected by a rule
    of the package; a hireling it offers has to be named there; and a hireling
    the package does name has to exist in a catalogue, or the warband's access
    points at something the app cannot offer at all. Sentences that *forbid*
    ("may not recruit evil Hired Swords or those who practise magic") name races
    and practices rather than hirelings, so only their rule is required.
    """
    issues: list[dict] = []
    raw = "".join(forms.values())
    scope = " ".join([str(band.get("name") or ""),
                      str(band.get("canonical_family") or ""),
                      manifest_row_name(band_id)])
    statements = hireling_access_statements(raw, scope)
    own_prose = " " + " ".join(presence(r.get("effect") or "") for r in rules) + " "
    covered = "hired sword" in own_prose or "dramatis" in own_prose
    if statements:
        STATS["hireling_statements"] = STATS.get("hireling_statements", 0) + 1
        if not covered:
            issues.append({"band": band_id, "kind": "hireling-access-missing",
                           "statements": len(statements),
                           "example": statements[0][:180]})
    if not statements:
        return issues
    own_names = {presence(band.get("name")), presence(band.get("canonical_family"))}
    own_names |= {presence(p.get("name")) for p in profiles}
    own_names |= {presence(manifest_row_name(band_id))}
    own_names.discard("")
    rule_names = {presence(r.get("name")) for r in rules}
    seen: set[str] = set()
    for statement in statements:
        restricting = bool(re.search(r"may not (?:hire|employ|recruit)|\bexcept\b|\bnor\b",
                                     statement, re.I))
        # Only the sentences that actually offer or forbid: a capitalized run
        # otherwise bridges into the next sentence's prose ("...may hire any
        # Hired Swords or ... worship the Shark God").
        relevant = " ".join(part for part in re.split(r"(?<=[.;])\s+", statement)
                            if ACCESS_VERB.search(part) or HIRELING_WORD.search(part))
        for match in re.finditer(r"\b(?:[A-Z][\w'\u2019-]+ ){1,3}[A-Z][\w'\u2019-]+", relevant):
            raw_match = " ".join(match.group(0).split()).strip(" -\u2013\u2014")
            if HIRELING_WORD.search(raw_match):
                continue          # the phrase itself ("Hired Swords", "Dramatis Personae")
            name = trim_candidate(raw_match)
            if not name:
                continue
            key = presence(name)
            if not key or key in seen:
                continue
            words = key.split()
            if any(w in NAME_STOPWORDS for w in words):
                continue
            if any(len(w) >= 2 and w.isupper() for w in name.split()):
                continue          # a heading or an abbreviation, not a proper name
            if key in own_names or key in rule_names or HIRELING_WORD.fullmatch(key):
                continue
            if set(words) <= CATEGORY_WORDS:
                continue          # a race or a practice, not a hireling
            if token_stems(key) & {s for phrase in own_names for s in token_stems(phrase)}:
                continue          # the band's own fighter type
            seen.add(key)
            if restricting:
                continue          # restrictions are verified by their rule alone
            synonym = presence(HIRELING_SYNONYMS.get(key, ""))
            ingested = f" {key} " in own_prose or (synonym and f" {synonym} " in own_prose)
            if not ingested:
                issues.append({"band": band_id, "kind": "hireling-name-absent",
                               "name": name,
                               "detail": f"offered in {statement[:90]!r}"})
                continue
            if key in catalogue_names() or (synonym and synonym in catalogue_names()):
                continue
            issues.append({"band": band_id, "kind": "hireling-not-in-catalog",
                           "name": name,
                           "detail": "ingested by the package but absent from every catalogue"})
    return issues


# Kinds that mean the package disagrees with its source: they have to be fixed or
# adjudicated. Every other kind is informational (an extraction that cannot be
# read, a table that belongs to another warband of the same document).
PROBLEM_KINDS = {
    "equipment-price-mismatch", "equipment-price-multiplier-mismatch",
    "cost-mismatch", "experience-mismatch",
    "min-models-mismatch", "max-models-mismatch", "starting-gold-mismatch",
    "profile-name-not-in-text", "equipment-name-not-in-text", "rule-id-dangling",
    "equipment-list-dangling", "package-missing", "text-missing",
    "rule-name-absent", "skill-table-mismatch", "spell-absent-from-source",
    "spell-difficulty", "hireling-access-missing", "hireling-name-absent",
    "hireling-not-in-catalog", "lore-source-missing",
}

# Findings verified by hand against the source, with the reason they are not
# defects - the convention audit_2a_sources.py uses, so nothing is dropped
# silently: the entry stays in the report carrying its verdict.
ADJUDICATED: list[tuple[str, str | None, str | None, str]] = [
    ("hireling-name-absent", "khorne-raiders-sar", "Shark God",
     "The access sentence and the adjacent prose about the Sartosan cult are interleaved by "
     "the document's two-column extraction, so the capitalized run bridges into 'worship the "
     "Shark God'. The package does carry the access rule (band--khorne-raider-rules) and "
     "offers nothing that is missing."),
]


def adjudication(issue: dict) -> str | None:
    """The recorded reason this finding is not a defect, or None when it is open."""
    subject = str(issue.get("name") or issue.get("subject") or issue.get("profile") or "")
    detail = str(issue.get("detail") or "")
    for kind, band, prefix, reason in ADJUDICATED:
        if issue.get("kind") != kind:
            continue
        if band is not None and issue.get("band") != band:
            continue
        if prefix is not None and not (subject.startswith(prefix) or detail.startswith(prefix)):
            continue
        return reason
    return None


def main() -> int:
    rows = package_rows()
    only = [arg for arg in sys.argv[1:] if not arg.startswith("--")]
    all_issues: list[dict] = []
    for band_id in sorted(rows):
        if only and not any(o in band_id for o in only):
            continue
        all_issues.extend(check_band(band_id, rows[band_id]))
    if not only:
        all_issues.extend(check_magic_prayers(list(load_manifest().values())))

    by_kind: dict[str, int] = {}
    problems: list[dict] = []
    adjudicated: list[dict] = []
    informational: list[dict] = []
    for issue in all_issues:
        by_kind[issue["kind"]] = by_kind.get(issue["kind"], 0) + 1
        why = adjudication(issue)
        if why:
            adjudicated.append({**issue, "verdict": "known", "why": why})
        elif issue["kind"] in PROBLEM_KINDS:
            problems.append(issue)
        else:
            informational.append(issue)

    print(json.dumps({
        "total_bands": len(rows),
        "equipment_rows_priced": STATS.get("priced_rows", 0),
        "equipment_rows_price_verified": STATS.get("price_verified", 0),
        "equipment_rows_price_multiplier": STATS.get("price_multiplier", 0),
        "equipment_rows_price_adjudicated": STATS.get("price_adjudicated", 0),
        "equipment_rows_price_rulebook": STATS.get("price_rulebook", 0),
        "hero_costs_priced": STATS.get("hero_costs", 0),
        "hero_costs_verified": STATS.get("hero_costs_verified", 0),
        "hero_costs_delegated": STATS.get("hero_costs_delegated", 0),
        "hero_costs_read_off_page": STATS.get("hero_costs_read_off_page", 0),
        "hero_experience_delegated": STATS.get("hero_experience_delegated", 0),
        "hero_experience_comparable": STATS.get("hero_experience", 0),
        "hero_experience_verified": STATS.get("hero_experience_verified", 0),
        "rules_anchored": STATS.get("rules_anchored", 0),
        "rules_anchored_by_section": STATS.get("rules_section", 0),
        "rules_unanchored": STATS.get("rules_unanchored", 0),
        "skill_tables_compared": STATS.get("skill_tables", 0),
        "spells_checked": STATS.get("spells_checked", 0),
        "spells_anchored": STATS.get("spells_anchored", 0),
        "bands_with_hireling_statements": STATS.get("hireling_statements", 0),
        "issues_by_kind": by_kind,
        "problem_count": len(problems),
        "adjudicated_count": len(adjudicated),
        "informational_count": len(informational),
        "problems": problems,
        "adjudicated": adjudicated,
        "informational": informational,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

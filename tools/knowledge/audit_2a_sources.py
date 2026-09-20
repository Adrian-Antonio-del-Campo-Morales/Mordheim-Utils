# -*- coding: utf-8 -*-
"""Source-fidelity audit of sources/2A against the cached mordheimer.net pages.

``audit_2a.py`` checks names, costs, experience, roster, statlines and the skill
table. It does not check whether the *content* of a package matches the page: the
rules, the special skills, the special equipment and the equipment-list tables.
This audit closes that gap using the cached HTML
(``build/cache/2a-sources/pages/<id>.html``), whose headings and tables keep the
source's structure:

* ``<h3>`` under **Special Skills** → a rule with that name must exist.
* ``<h3>`` under **Special Equipment** → the item must exist in a catalog.
* ``<h3>`` *X Equipment List* → a YAML list with that name; every ``Item / Cost``
  row must exist in it with the matching price, and every item in the YAML list
  must appear in the page's table.
* every YAML rule name (or its ``source.section``) must appear on the page.

Item identity uses the same catalog pool the staging validator accepts: the active
KB plus the 2A and 2B provisional catalogs (a 2A band may point at a 2B item
instead of duplicating it). Matching prefers an exact name/id, then an equal word
set, and only falls back to containment when a single candidate qualifies — the
loose bidirectional match of ``audit_2a.py`` is deliberately not reused here,
because "Short bow" would otherwise match "Bow" and produce false price
mismatches.

Findings are adjudicated, not assumed: the source names things a package may
legitimately split (a fighter rule vs a band rule) or reword, and a page may list
an unpriced special item. Verdicts live in ``KNOWN`` below; anything not listed is
reported as an open finding and makes the exit code 1.

Usage::

    python tools/knowledge/audit_2a_sources.py
    python tools/knowledge/audit_2a_sources.py --json
    python tools/knowledge/audit_2a_sources.py --band druchii-mic --show 40
"""
from __future__ import annotations

import argparse
import glob
import html as html_mod
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict

import yaml

PAGES = 'build/cache/2a-sources/pages'
TEXT = 'build/cache/2a-sources/text'
BANDS = 'sources/2A/bands/mordheim'
# Same item pool the staging validator accepts: catalog/items of the active KB plus
# both provisional catalogs. Campaign and hireling catalogs are deliberately out of
# scope (the validator does not resolve band equipment against them either).
CATALOG_DIRS = ('sources/knowledge/catalog/items', 'sources/2A/catalog/items',
                'sources/2B/catalog/items')
# The provisional catalogue of the 2A bands, whose items carry the price the
# Special Equipment sections print (kept separate so a test can point it at a copy).
CATALOG_DIR = 'sources/2A/catalog/items'


def catalog_roots() -> tuple[str, ...]:
    """The item pool, with ``CATALOG_DIR`` looked up at call time.

    The constant can be repointed (the source-fidelity tests run the audit against
    a throwaway copy of the 2A catalogue), and every reader has to follow it.
    """
    return tuple(CATALOG_DIR if base == 'sources/2A/catalog/items' else base
                 for base in CATALOG_DIRS)
# Adjudicated findings. Each row is (kind, band, detail-prefix, why); ``None`` in
# band or prefix acts as a wildcard. Anything else is reported as an open finding.
KNOWN: list[tuple[str, str | None, str | None, str]] = [
    ('rule-name-paraphrased', None, None,
     'display name derived from the prose; the rule cites a source section that exists '
     'on the page (the page has no heading for this rule)'),
    ('rule-name-absent', 'druchii-mic', 'band--naggaroth-prices',
     'named after the source footnote legend it ingests (section: Dark Elf equipment lists)'),
    ('rule-name-absent', 'dwarf-slayer-cult-web', 'band--rememberer-skills',
     'container rule for the Rememberer skill list; the source has skill headings, not '
     'this heading'),
    ('rule-name-absent', 'protectorate-of-sigmar-lotd3', 'band--witch-hunter-hired-swords',
     'derived from the Hired Swords access prose; the source has no such heading'),
    ('special-price-mismatch', 'vampire-hunters-of-sylvania-lotd5', 'silver_tip_stake',
     'the page prints two prices for the same item (10 gc in both equipment lists, 15 gc in '
     'the Special Equipment block): the editorial decision recorded in '
     'discrepancy-verdicts.md #1 keeps the list price operative and the 15 gc as an erratum'),
    ('hireling-not-in-catalog', 'ogre-hunting-party-web', 'Gnoblar Botcher',
     'the source names it among the only three Hired Swords the warband may hire, and no '
     'hireling catalog models it (mordheimer hired-swords grades 1b/1c/2a do not list it '
     'either): a hireling-catalog gap, not a package defect, and the package ingests the '
     'source wording verbatim'),
    ('hireling-not-in-catalog', 'ogre-hunting-party-web', 'Ogre Slaver',
     'the source names it in the same access rule; the catalogs model a different hireling '
     'under a similar name (Ogre Slave Master, 90 gc, hireable by Possessed/Carnival of '
     'Chaos/Beastmen), so this is a hireling-catalog gap rather than a naming variant'),
]

# Printed wording that names an item the catalogue registers under another name,
# adjudicated row by row against the page and recorded in
# sources/2A/discrepancy-verdicts.md. Key: (band, list, item_id) -> the names the
# page prints for that item. A row that matches one of these counts as the same
# row, so its price is compared like any other; the check never infers a synonym
# from a similar spelling.
SOURCE_WORDING: dict[tuple[str, str, str], list[str]] = {
    ('protectorate-of-sigmar-lotd3', 'protectorate-equipment-list', 'blessed_water'):
        ['Holy Water'],
    ('protectorate-of-sigmar-lotd3', 'protectorate-equipment-list', 'sigmarite_hammer'):
        ['Sigmarite Warhammer'],
    ('vampire-hunters-of-sylvania-lotd5', 'vampire-hunters-hero-equipment-list',
     'blessed_water'): ['Holy Water'],
    # The Outlaws page merges the row's availability into its name cell.
    ('outlaws-of-stirwood-forest-redux-fbg', 'outlaws-equipment-list', 'long_bow'):
        ['Long Bow Heroes only'],
}

# Every currency the 2A pages price their lists in: gold crowns written gc / Gold
# Crowns / Crowns, and the warp tokens (wt) of the Clan Moulder Skaven lists.
MONEY = re.compile(
    r'(\d{1,4})\s*(?:gcs?|gold\s*crowns?|gold|coronas?|crowns?|wt|tc|dinars?)\b', re.I)
# A rolled price the page prints in the list itself ("15 + D6 gc", "45+3D6 gold crowns").
ROLLED_PRICE = re.compile(r'(\d{1,4})\s*\+\s*(\d*)\s*D6', re.I)
# A price stated against another item ("3x cost", "3 x price", "2 x base weapon price").
RELATIVE_PRICE = re.compile(
    r'(\d)\s*(?:x|\u00d7)\s*(?:the\s+)?(?:base\s+)?(?:weapon\s+)?(?:price|cost)', re.I)


def cost_cell_value(cell: str) -> tuple[str, object] | None:
    """Normalised price of a source cost cell, or None when it carries no price.

    ('flat', n) is a fixed amount — including the later-purchase figure of "1st
    free/2 gc" and the entry price of "35 wt (70 for a brace)"; ('rolled',
    '15+D6') is a dice price printed in the list; ('relative', 3) is a price
    stated against another item. The currency is not part of the value: Clan
    Moulder prices everything in warp tokens and the lists store the figure the
    page prints.
    """
    text = norm(cell)
    rolled = ROLLED_PRICE.search(text)
    if rolled:
        return ('rolled', f'{rolled.group(1)}+{rolled.group(2)}D6')
    relative = RELATIVE_PRICE.search(text)
    if relative:
        return ('relative', int(relative.group(1)))
    money = MONEY.search(text)
    if money:
        return ('flat', int(money.group(1)))
    if 'free' in text:
        return ('flat', 0)   # the row is printed without a price at all
    return None


def cost_agrees(yaml_cost: object, cell: str) -> bool | None:
    """Does the YAML cost match the source cell? None when the cell has no price.

    A rolled price is stored as the dice expression the schema prescribes
    (``25+1D6``); a relative price as null with its wording in ``notes`` (the KB
    shape of ``gromril_weapon`` and ``ithilmar_weapon``); anything else as the
    printed number.
    """
    parsed = cost_cell_value(cell)
    if parsed is None:
        return None
    kind, value = parsed
    if kind == 'flat':
        return yaml_cost == value
    if kind == 'rolled':
        return str(yaml_cost) == value
    return yaml_cost is None


# A price printed in prose, as the Special Equipment sections write it: "Cost: 15 + D6
# gold crowns", "50 gold crowns" (no Cost label), "1st Free / Second 3gc", "free",
# "3 x base weapon price", "25 Warp Tokens".
PROSE_PRICE = re.compile(
    r'(?:(?P<free>free)\b'
    r'|(?P<multiple>\d)\s*(?:x|\u00d7)\s*(?:the\s+)?(?:base\s+)?(?:weapon\s+)?(?:price|cost)'
    r'|(?P<base>\d{1,4})\s*(?:\+\s*(?P<dice>\d*)\s*D6)?\s*'
    r'(?P<unit>gcs?|gold\s*crowns?|crowns?|warp\s*tokens?|wt|tc|dinars?)\b)', re.I)


def price_shape(expression: object) -> tuple:
    """(amount, dice, currency) of a printed price; the currency alone if relative.

    ``()`` when the text carries no price at all. The dice are kept as the digits
    the page prints (``15 + D6`` → ``(15, '', 'gc')``, ``25 + 3D6`` →
    ``(25, '3', 'gc')``); a price stated against another item keeps its factor
    (``3 x base weapon price`` → ``('x3',)``) and a free row is ``('free',)``.
    """
    match = PROSE_PRICE.search(norm(expression))
    if not match:
        return ()
    if match.group('free'):
        return ('free',)
    if match.group('multiple'):
        return (f"x{match.group('multiple')}",)
    unit = re.sub(r'\s+', ' ', match.group('unit').lower())
    unit = re.sub(r'gold\s*crowns?|crowns?', 'gc', unit)
    unit = re.sub(r'warp\s*tokens?', 'wt', unit)
    unit = re.sub(r'^gcs$', 'gc', unit)
    return (int(match.group('base')), re.sub(r'\s+', '', match.group('dice') or ''), unit)


def same_price(one: tuple, other: tuple) -> bool:
    """Same price, ignoring a currency the catalogue note simply omitted."""
    if not one or not other:
        return False
    if one[0] != other[0]:
        return False
    if len(one) == 1 or len(other) == 1:
        return True
    if one[1] != other[1]:
        return False
    return one[2] == other[2] or not one[2] or not other[2]


def norm(value: object) -> str:
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    text = text.replace('\u200b', ' ').replace('\xa0', ' ')
    text = text.replace('–', '-').replace('—', '-')
    # The pages and the packages apostrophise differently (Wizard's Staff vs
    # Wizard\u2019s Staff): the mark is not identity.
    text = text.replace('\u2019', "'").replace('\u02bc', "'")
    return re.sub(r'\s+', ' ', text).strip().lower()


# Source wording that names the same item as the catalog. Only hyphen/spelling
# variants live here: collapsing words that carry meaning (e.g. "brace") makes
# distinct items collide.
SYNONYMS = {
    'double handed': 'two handed', 'double-handed': 'two handed',
    'doublehanded': 'two handed', 'twohanded': 'two handed', '2 handed': 'two handed',
}


# Connectives carry no identity: the pages write "Hooded Lantern and Rig", "Hammer
# or Mace", "Rope and hook" where a catalog id joins them with '_'.
STOPWORDS = {'and', 'or', 'the', 'of', 'with', 'a', 'an', 'for', 'per'}


def singular(word: str) -> str:
    if len(word) > 3 and word.endswith('s') and not word.endswith('ss'):
        return word[:-1]
    return word


def tokens(value: object) -> list[str]:
    text = norm(value).replace('-', ' ')
    for src, dst in SYNONYMS.items():
        text = text.replace(src, dst)
    words = sorted({singular(w) for w in re.split(r'[^a-z0-9]+', text)
                    if w and w not in STOPWORDS})
    # The KB registers the same weapon under three ids —``great_weapon`` (94 uses),
    # ``two_handed_weapon``, ``great_axe``— all mapped to the single engine option
    # "Double-handed weapon". The pages say "Double-handed weapon", so a plain
    # "Great Weapon" entry names the same item for comparison purposes.
    if set(words) == {'great', 'weapon'}:
        return ['handed', 'two', 'weapon']
    return words


def source_alternatives(name: str) -> list[str]:
    """Source cell -> candidate names, exploding the page's own shorthand.

    The pages write rows such as ``Rapier (Only Andanti)``, ``Mace/Hammer``,
    ``Pistol *``, ``Shovel (Halberd)``, ``Double-handed weapon`` or
    ``Meat Cleaver(Axe) **``.  A parenthetical may be a restriction ("Only
    Andanti") or the underlying base weapon ("Meat Cleaver(Axe)"), so both the
    outer name and the parenthetical are offered as alternatives and the YAML
    list decides which one the transcriber used.
    """
    text = re.sub(r'\*+', ' ', str(name)).replace('\u200b', ' ')
    outer = re.sub(r'\([^)]*\)', ' ', text)
    inner = ' '.join(re.findall(r'\(([^)]*)\)', text))
    parts: list[str] = []
    for candidate in (outer, inner):
        for piece in re.split(r'/', candidate):
            piece = piece.strip(' .')
            if piece and piece not in parts:
                parts.append(piece)
    return parts or [str(name).strip()]


def squash(value: object) -> str:
    """Order-insensitive alphanumerics — for short names only (tokens are sorted)."""
    return ''.join(tokens(value))


def plain(value: object) -> str:
    """Order-preserving alphanumerics, for searching a name inside long prose."""
    text = norm(value).replace('-', ' ').replace("'", ' ').replace('\u2019', ' ')
    return re.sub(r'[^a-z0-9]+', ' ', text).strip()


# Coverage counters, printed by --all / --stats: "0 findings" must never be the
# only evidence, so the run reports how much it actually compared.
STATS: dict[str, int] = {}


def bump(key: str, amount: int = 1) -> None:
    STATS[key] = STATS.get(key, 0) + amount


MANIFEST_NAMES: dict[str, str] = {}


def manifest_names() -> dict[str, str]:
    """band id -> the index name the manifest records for it (authoritative)."""
    global MANIFEST_NAMES
    if not MANIFEST_NAMES:
        document = yaml.safe_load(open('sources/2A/manifest.yaml', encoding='utf-8')) or {}
        MANIFEST_NAMES = {str(row['id']): str(row.get('mordheimer_name') or '')
                          for row in document.get('bands') or []}
    return MANIFEST_NAMES


def docs(path: str) -> list[dict]:
    with open(path, encoding='utf-8') as handle:
        return [d for d in yaml.safe_load_all(handle) if isinstance(d, dict)]


def catalog_items() -> dict[str, str]:
    """item_id -> display name over the active KB and both staging catalogs."""
    out: dict[str, str] = {}
    for base in catalog_roots():
        for path in glob.glob(f'{base}/**/*.yaml', recursive=True):
            for doc in docs(path):
                for item in doc.get('items') or ():
                    if isinstance(item, dict) and item.get('id'):
                        out.setdefault(str(item['id']), str(item.get('name') or item['id']))
    return out


def catalog_item_records() -> dict[str, dict]:
    """item_id -> the catalogue record itself (same pool as ``catalog_items``)."""
    out: dict[str, dict] = {}
    for base in catalog_roots():
        for path in glob.glob(f'{base}/**/*.yaml', recursive=True):
            for doc in docs(path):
                for item in doc.get('items') or ():
                    if isinstance(item, dict) and item.get('id'):
                        out.setdefault(str(item['id']), item)
    return out


def candidate_ids(name: str, candidates: dict[str, str]) -> list[tuple[str, str]]:
    """Every plausible item_id for a source cell, best match first.

    A page cell can name several things at once (``Meat Cleaver(Axe)``,
    ``Yari (Spear)``, ``Mace/Hammer``); the caller decides which one the package
    actually used rather than trusting the first hit.
    """
    ranked: list[tuple[str, str]] = []
    for alternative in source_alternatives(name):
        target = squash(alternative)
        target_words = tokens(alternative)
        for item_id, display in candidates.items():
            if target and target in (squash(item_id), squash(display)):
                ranked.append((item_id, 'exact'))
        joined = target.replace(' ', '')
        for item_id, display in candidates.items():
            if tokens(display) == target_words:
                ranked.append((item_id, 'words'))
            elif joined and joined in (plain(item_id).replace(' ', ''),
                                       plain(display).replace(' ', '')):
                ranked.append((item_id, 'joined'))  # "Longbow" vs "Long Bow"
        contained = [i for i, d in candidates.items()
                     if target_words and set(target_words) <= set(tokens(d))]
        if len(contained) == 1:
            ranked.append((contained[0], 'contained'))
        elif len(contained) > 1:
            longest = max(len(tokens(candidates[i])) for i in contained)
            specific = [i for i in contained if len(tokens(candidates[i])) == longest]
            if len(specific) == 1:
                ranked.append((specific[0], 'longest'))
    seen: list[tuple[str, str]] = []
    order = {'exact': 0, 'words': 1, 'joined': 2, 'contained': 3, 'longest': 4}
    for item_id, how in sorted(ranked, key=lambda r: order.get(r[1], 9)):
        if item_id not in {s[0] for s in seen}:
            seen.append((item_id, how))
    return seen


def match_item(name: str, candidates: dict[str, str]) -> tuple[str | None, str]:
    """Best candidate item_id for a source cell, and how it matched.

    Exact first (name or id), then an equal word set, and containment only when a
    single candidate qualifies. Ties are never resolved silently: they come back as
    ``ambiguous`` so the report can show the options instead of inventing a verdict.
    """
    extra: list[str] = []
    for alternative in source_alternatives(name):
        target = squash(alternative)
        for item_id, display in candidates.items():
            if target and target in (squash(item_id), squash(display)):
                return item_id, 'exact'
        target_words = tokens(alternative)
        equal = [i for i, d in candidates.items() if tokens(d) == target_words]
        if len(equal) == 1:
            return equal[0], 'words'
        contained = [i for i, d in candidates.items()
                     if target_words and set(target_words) <= set(tokens(d))]
        if len(contained) == 1:
            return contained[0], 'contained'
        extra.append(f'{alternative!r}:{len(equal)}eq/{len(contained)}sub')
    return None, 'none(' + ', '.join(extra) + ')'


MAGIC = 'sources/2A/catalog/magic-2a.yaml'
HIRELING_DIRS = ('sources/knowledge/catalog/hirelings/hired-swords',
                 'sources/knowledge/catalog/hirelings/dramatis-personae',
                 # The staging 2B hireling catalogs are read-only cross-reference here,
                 # exactly as ``ingest_2a.py`` pools KB + 2A + 2B item catalogs.
                 'sources/2B/catalog/hirelings')
# A source sentence may name a *category* of hireling rather than a hireling ("any
# kind of Elven Hired Sword", "Snotling Hired Swords", "Dramatis Personae").
CATEGORY_PHRASES = ('hired sword', 'hired swords', 'dramatis persona', 'dramatis personae')
# ... or a *warband* it is being compared to ("as if they were Human Mercenaries").
WARBAND_WORDS = ('warband', 'mercenar', 'witch hunter')
# ... or a game artefact the sentence merely cites ("roll on the Hero's Advancement
# Table"). Matched per word: 'list' is a substring of the hireling "Duellist".
ARTEFACT_WORDS = {'table', 'chart', 'sheet', 'phase', 'skill', 'rule', 'list'}
# Source wording that names a hireling the catalogs model under another name, the
# same way SYNONYMS handles item spelling. Keyed by ``plain()`` text.
HIRELING_SYNONYMS = {
    'high elf mage': 'Elf Mage',   # mordheimer indexes it as Elf Mage; Fey rule = High Elf
    'high elven mage': 'Elf Mage',
}
# Only the hireling concepts: a bare "hire" also matches hiring your own Thralls or
# more Rat Ogres, which is not hireling access at all.
ACCESS_WORDS = ('hired sword', 'hireling', 'dramatis personae',
                # A second sentence can grant access without repeating the noun ("you may
                # hire an Ogre Bodyguard and/or Ogre Slaver"), so the verb counts too --
                # but only with its modal, never a bare "hire" (which also matches hiring
                # your own Thralls or more Rat Ogres).
                'may hire')


def slug_to_band() -> dict[str, str]:
    """mordheimer page slug -> staging band id (the manifest records both)."""
    document = yaml.safe_load(open('sources/2A/manifest.yaml', encoding='utf-8')) or {}
    return {str(row.get('slug')): str(row['id']) for row in document.get('bands') or []
            if row.get('slug')}


def magic_lores() -> list[dict]:
    if not os.path.exists(MAGIC):
        return []
    return (yaml.safe_load(open(MAGIC, encoding='utf-8')) or {}).get('lores') or []


def presence_key(value: object) -> str:
    """Presence key: order-preserving alphanumerics, so "Ogre Slaver-­" matches
    "Ogre Slaver" and "The Mazzalupo" matches "the Mazzalupo"."""
    return plain(value)


def profile_key(value: object) -> str:
    """Identity key for a proper name: squashed, with plural heads folded.

    The pages pluralise freely ("Witch Hunters", "Human Mercenaries"), so an
    exact squash would miss the singular catalog entry of the same hireling.
    """
    return squash(' '.join(singular(word) for word in str(value or '').split()))


def hireling_names() -> dict[str, str]:
    """normalized hireling name -> the catalog name, over every grade."""
    out: dict[str, str] = {}
    for base in HIRELING_DIRS:
        for path in glob.glob(f'{base}/*.yaml'):
            for doc in docs(path):
                for profile in doc.get('profiles') or ():
                    if isinstance(profile, dict) and profile.get('name'):
                        out.setdefault(profile_key(profile['name']), str(profile['name']))
    return out


def band_name_keys() -> set[str]:
    """Identity keys of every warband name the KB knows (plus the staging family)."""
    keys: set[str] = set()
    for path in glob.glob('sources/knowledge/bands/*/*/band.yaml'):
        document = yaml.safe_load(open(path, encoding='utf-8')) or {}
        for field in ('name', 'canonical_family'):
            if document.get(field):
                keys.add(profile_key(document[field]))
    return keys


def magic_heading_matches(lore_name: str, heading: str) -> bool:
    """Does this page heading introduce the lore? (names differ in wording only)"""
    wanted = plain(re.sub(r'\([^)]*\)', ' ', lore_name))
    got = plain(re.sub(r'\([^)]*\)', ' ', heading))
    if not wanted or not got:
        return False
    if wanted == got:
        return True
    a, b = set(wanted.split()), set(got.split())
    return a <= b or b <= a


def spells_match(one: str, other: str) -> bool:
    """Same spell, tolerating the page's punctuation and spacing.

    The pages apostrophise loosely (``Morks' Blessing`` for the catalog's
    ``Mork's Blessing``), so apostrophes are dropped before comparing.
    """
    if squash(one) == squash(other):
        return True
    a = plain(one).replace("'", '')
    b = plain(other).replace("'", '')
    if a and a == b:
        return True
    return a.replace(' ', '') == b.replace(' ', '')



# The pages print numeric difficulties and "Difficulty: Auto" for the always-succeeds
# spells; the KB models the latter as the string 'auto' (never as a number).
DIFFICULTY_RE = re.compile(r'difficulty\s*[:\s]*\s*(\d+|auto)', re.I)


def parse_difficulty(match: re.Match | None) -> int | str | None:
    if not match:
        return None
    value = match.group(1).lower()
    return 'auto' if value == 'auto' else int(value)


def spell_entries(fragment: str, section_name: str = '') -> list[dict]:
    """Spell rows of a magic section, whatever markup the page uses.

    The 2A pages publish spell lists five different ways: numbered ``h3`` headings
    (Necrarchs), a ``D6 | Spell | Difficulty | Description`` table (Druchii), an
    ordered list of ``<strong>Name:</strong>`` items (Snotlings), numbered
    ``<p><strong>N. Name</strong>`` paragraphs (Order of the Mare) and plain
    ``<strong>`` runs. Every strategy is tried and the first that yields names wins,
    so an unparsed list is visible instead of silently passing.
    """
    entries: list[dict] = []

    def add(name: str, difficulty: int | None = None, roll: str | None = None) -> None:
        cleaned = re.sub(r'^\s*(\d+)\s*[.)]?\s*', '', html_mod.unescape(str(name)))
        cleaned = cleaned.replace('\u200b', '').strip(' :.;,\u2013\u2014-')
        if len(cleaned) < 3:
            return
        if any(squash(cleaned) == squash(e['name']) for e in entries):
            return
        entries.append({'name': cleaned, 'difficulty': difficulty, 'roll': roll})

    # A) child headings — numbered ("1 – Soulcage") or not ("Song of Thorns"), with
    #    the difficulty taken from the prose that follows the heading.
    inner = headings(fragment)
    for position, (level, text, _pos) in enumerate(inner):
        if level < 3:
            continue
        if section_name and squash(text) == squash(section_name):
            continue  # the section's own heading (it lives in the slice it opens)
        match = re.match(r'^\s*(\d+)\s*[\u2013\u2014-]\s*(.+)$', text)
        name = match.group(2) if match else text
        body = norm(re.sub(r'<[^>]+>', ' ', slice_of(fragment, inner, position)))
        found_diff = DIFFICULTY_RE.search(body)
        add(name, difficulty=parse_difficulty(found_diff),
            roll=match.group(1) if match else None)
    if entries:
        return entries

    # B) a table whose header names a Spell column
    for table in re.findall(r'<table.*?</table>', fragment, re.S):
        header = [norm(re.sub(r'<[^>]+>', '', cell))
                  for cell in re.findall(r'<th[^>]*>(.*?)</th>', table, re.S)]
        if not any('spell' in cell for cell in header):
            continue
        spell_at = next(i for i, cell in enumerate(header) if 'spell' in cell)
        diff_at = next((i for i, cell in enumerate(header) if 'difficult' in cell), None)
        for row in re.findall(r'<tr.*?</tr>', table, re.S):
            if '<th' in row:
                continue
            cells = [html_mod.unescape(re.sub(r'<[^>]+>', '', cell)).strip()
                     for cell in re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)]
            if len(cells) <= spell_at:
                continue
            difficulty = None
            if diff_at is not None and len(cells) > diff_at:
                match = re.search(r'(\d+)', cells[diff_at])
                difficulty = parse_difficulty(match)
            add(cells[spell_at], difficulty=difficulty, roll=cells[0] if cells else None)
    if entries:
        return entries

    # C) ordered-list items: <li><p><strong>Name:</strong> <em>Difficulty N</em>
    for item in re.findall(r'<li[^>]*>(.*?)</li>', fragment, re.S):
        match = re.search(r'<strong>\s*([^<]{2,90}?)\s*[:.]?\s*</strong>', item)
        if not match:
            continue
        text = norm(re.sub(r'<[^>]+>', ' ', item))
        add(match.group(1), difficulty=parse_difficulty(DIFFICULTY_RE.search(text)))
    if entries:
        return entries

    # D) numbered paragraphs: <p><strong>N. Name</strong> <strong>Difficulty: N</strong>
    for para in re.findall(r'<p[^>]*>(.*?)</p>', fragment, re.S):
        match = re.match(r'\s*<strong>\s*(\d+)[.)]?\s*([^<]{2,90}?)\s*</strong>', para)
        if not match:
            continue
        text = norm(re.sub(r'<[^>]+>', ' ', para))
        add(match.group(2), difficulty=parse_difficulty(DIFFICULTY_RE.search(text)),
            roll=match.group(1))
    return entries


def access_statements(text: str) -> list[str]:
    """Sentences of the page that grant or forbid Hired Swords / Dramatis Personae."""
    out: list[str] = []
    for sentence in re.split(r'(?<=[.!?])\s+', text):
        low = norm(sentence)
        if not any(word in low for word in ACCESS_WORDS):
            continue
        if any(word in low for word in ('may ', 'may not', 'never', 'cannot', "can't",
                                        'no ', 'only', 'same types', 'allowed')):
            out.append(' '.join(sentence.split()))
    return out


def headings(page: str) -> list[tuple[int, str, int]]:
    out = []
    for match in re.finditer(r'<h([1-6])[^>]*>(.*?)</h\1>', page, re.S):
        text = html_mod.unescape(re.sub(r'<[^>]+>', '', match.group(2)))
        # mordheimer appends a zero-width space to every heading (the anchor link)
        text = text.replace('\u200b', '')
        text = re.sub(r'\s+', ' ', text).strip()
        if text:
            out.append((int(match.group(1)), text, match.start()))
    return out


def slice_of(page: str, heads: list[tuple[int, str, int]], index: int) -> str:
    level, _text, start = heads[index]
    end = len(page)
    for lvl, _t, pos in heads[index + 1:]:
        if lvl <= level:
            end = pos
            break
    return page[start:end]


def table_rows(fragment: str) -> list[tuple[str, str]]:
    rows = []
    for table in re.findall(r'<table.*?</table>', fragment, re.S):
        for row in re.findall(r'<tr.*?</tr>', table, re.S):
            if '<th' in row:
                continue
            cells = [html_mod.unescape(re.sub(r'<[^>]+>', '', c)).strip()
                     for c in re.findall(r'<td[^>]*>(.*?)</td>', row, re.S)]
            if len(cells) >= 2 and cells[0]:
                rows.append((cells[0], cells[1]))
    return rows


def find(look: str, haystack: str) -> int:
    return haystack.find(look)


def check_special_equipment_prices(band_id: str, page: str, heads: list[tuple[int, str, int]],
                                   list_prices: dict[str, object], note) -> None:
    """Compare each Special Equipment price the catalogue records with the page's own.

    The equipment lists are not the only place a page prices an item: its Special
    Equipment sections price the band's own objects too, and those prices live in
    the provisional catalogue as prose in ``availability_note`` (or as
    ``cost``/``price_override``). Nothing compared the two, so an item could be
    recorded at the wrong price — or at no price — with no check noticing.

    A price is also accepted from the band's own equipment lists: several items
    (a shared relic, a staff) are priced on the list rather than in their section.
    An item the page never writes a section for, and no list prices, is reported
    as unverifiable rather than assumed correct.
    """
    pages = slug_to_band()
    for path in sorted(glob.glob(f'{CATALOG_DIR}/*.yaml')):
        document = yaml.safe_load(open(path, encoding='utf-8')) or {}
        items = document.get('items') or []
        slug = ''
        for item in items:
            for ref in item.get('source_refs') or ():
                slug = str(ref.get('url') or '').rsplit('/', 1)[-1]
                if slug:
                    break
            if slug:
                break
        if pages.get(slug) != band_id:
            continue
        for item in items:
            item_id = str(item.get('id'))
            name = norm(item.get('name') or item_id)
            section = ''
            for index, (level, head, _pos) in enumerate(heads):
                if level == 3 and norm(head).lower().startswith(name[:12]):
                    section = norm(re.sub(r'<[^>]+>', ' ',
                                          slice_of(page, heads, index)))
                    break
            recorded = item.get('cost')
            if isinstance(recorded, int):
                recorded_shape = (recorded, '', '')
            elif isinstance(recorded, str):
                recorded_shape = price_shape(recorded)
            else:
                recorded_shape = price_shape(item.get('availability_note'))
            page_shape = price_shape(section) if section else ()
            listed = list_prices.get(item_id)
            bump('special_items_checked')
            if section and page_shape:
                bump('special_prices_compared')
                if not same_price(page_shape, recorded_shape):
                    # The catalogue may record no price at all for an item the
                    # band's own list prices: the list is then the operative one
                    # and it has to agree with the section.
                    if (not recorded_shape and listed is not None
                            and same_price(page_shape, (listed, '', ''))):
                        continue
                    note('special-price-mismatch',
                         f'{item_id} ({item.get("name")}): page={page_shape} '
                         f'catalogue={recorded_shape}')
                continue
            if listed is not None:
                continue              # the band's own list carries and verifies the price
            if page_shape and not recorded_shape:
                note('special-price-unrecorded',
                     f'{item_id} ({item.get("name")}): page={page_shape}, no price recorded')
            elif not page_shape:
                note('special-price-unverifiable',
                     f'{item_id} ({item.get("name")}): the page has no section and no list '
                     f'prices it (catalogue={recorded_shape})')


def equipment_list_sections(heads: list[tuple[int, str, int]]) -> list[dict]:
    """Equipment-list headings, with the child lists nested under each one.

    A page publishes its lists either as one heading whose own section holds the
    list tables (Ogre Hunting Party's "Ogre Equipment List", h2, with h4 weapon
    categories inside), as a parent over one child per list (Druchii's "Druchii
    Equipment Lists" over its four "... Equipment List" h3s), or as a list that
    itself contains a sub-list (Protectorate of Sigmar's h2 list with the Hunstman
    list inside). A heading that only opens child lists has no rows of its own and
    is a container; every other heading owns its rows and is a list. Only rows a
    heading owns are matched against a YAML list, so a child's rows can never be
    attributed to its parent.

    Every level is accepted: the pages use h3 for most bands but h2 for Ogre
    Hunting Party, Outlaws, Sorcerous Society, Masters of Horror, Survivors of
    Strigos, Clan Moulder, the LotD bands and Protectorate of Sigmar.
    """
    indexes: list[int] = []
    for index, (level, head, _pos) in enumerate(heads):
        words = norm(head).split()
        if level < 2 or 'equipment' not in words:
            continue
        if words[-1] in ('list', 'lists'):
            indexes.append(index)
    sections: list[dict] = []
    for index in indexes:
        end = next((j for j in range(index + 1, len(heads))
                    if heads[j][0] <= heads[index][0]), len(heads))
        children = [j for j in indexes if index < j < end]
        sections.append({'index': index, 'head': heads[index][1],
                         'children': children})
    return sections


def check_equipment_lists(band_id: str, page: str, heads: list[tuple[int, str, int]],
                          lists: list[dict], items: dict[str, str], raw: str,
                          note) -> None:  # noqa: C901 - one linear pass, kept whole
    """Verify every equipment list against the page, in both directions.

    The check is list-driven: each YAML list has to own a source heading (a list
    the page never publishes is reported instead of skipped, which is the failure
    mode the 2B re-verification closed), and for every matched pair each printed
    row must exist in the list with a matching price while each list entry must be
    printed on the page.

    Prices come from the section's tables — the form that keeps the name/cost
    pairing — and fall back to the flat-text extraction
    (``build/cache/2a-sources/text/``), which prints a name and its price on
    consecutive lines, when the table cannot carry a row. They are compared by
    kind: a fixed amount (including the later-purchase figure of "1st free/
    2 gc"), a dice price the list itself prints ("15 + D6 gc"), or a price stated
    against another item ("3x cost", stored as null with its wording in notes).
    The currency is not part of the value: Clan Moulder prices in warp tokens.
    """
    sections = equipment_list_sections(heads)
    by_index = {s['index']: s for s in sections}
    flat_lines = [norm(line) for line in raw.splitlines()]

    def child_rows(section: dict) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        for child_index in section['children']:
            child = by_index.get(child_index)
            if child is not None:
                out += table_rows(slice_of(page, heads, child['index']))
        return out

    def rows_of(section: dict) -> list[tuple[str, str]]:
        """The rows this heading owns: its tables minus its children's tables."""
        remaining = list(table_rows(slice_of(page, heads, section['index'])))
        for row in child_rows(section):
            if row in remaining:
                remaining.remove(row)
        return remaining

    def yaml_items_of(lst: dict) -> dict[str, dict]:
        return {str(e['item_id']): e for e in lst.get('items') or ()
                if isinstance(e, dict) and e.get('item_id')}

    def named_ids(item_name: str, yaml_items: dict[str, dict], list_id: str) -> list[str]:
        """The list entries this printed row could be, best match first."""
        out = [i for i, _how in candidate_ids(item_name, items) if i in yaml_items]
        printed = norm(item_name)
        for (band, lid, item_id), names in SOURCE_WORDING.items():
            if (band == band_id and lid == list_id and item_id in yaml_items
                    and any(norm(n) == printed for n in names)):
                out.insert(0, item_id)
        return out

    def flat_price(item_id: str, list_id: str) -> str | None:
        """Price cell the flat-text extraction prints for this row, if any."""
        names = [str(items.get(item_id) or item_id).replace('_', ' ')]
        names += SOURCE_WORDING.get((band_id, list_id, item_id), [])
        for name in names:
            key = norm(name)
            if not key:
                continue
            for position, line in enumerate(flat_lines):
                if line != key:
                    continue
                for following in flat_lines[position + 1:position + 3]:
                    if following and cost_cell_value(following):
                        return following
        return None

    def verify_pair(section: dict, lst: dict) -> None:
        head = section['head']
        list_id = str(lst.get('id'))
        bump('lists_verified')
        bump('list_levels_h2' if heads[section['index']][0] == 2 else 'list_levels_other')
        yaml_items = yaml_items_of(lst)
        # (a) every printed row is in the list, with a matching price. The list
        # itself decides which candidate row is the ingested one, so a naming
        # variant is reported as a missing row rather than silently accepted.
        source_ids: set[str] = set()
        for item_name, cost_cell in rows_of(section):
            candidates = named_ids(item_name, yaml_items, list_id)
            if not candidates:
                matches = candidate_ids(item_name, items)
                if matches:
                    note('list-item-missing',
                         f'{head}: {item_name} \u2192 best={matches[0][0]} not in list')
                else:
                    note('source-row-unmatched', f'{head}: {item_name} ({cost_cell})')
                continue
            source_ids |= set(candidates)
            bump('rows_priced')
            verdict = cost_agrees(yaml_items[candidates[0]].get('cost'), cost_cell)
            if verdict is None:
                bump('rows_without_a_price_cell')
            elif verdict:
                bump('rows_price_verified')
            if verdict is False:
                note('item-cost', f'{head}: {item_name} source={cost_cell} '
                     f'yaml={yaml_items[candidates[0]].get("cost")}')
        # (b) every list entry is printed on the page, in the table or in the flat
        # extraction
        for item_id, entry in yaml_items.items():
            if item_id in source_ids:
                continue
            bump('rows_checked_against_page')
            cell = flat_price(item_id, list_id)
            if cell is not None and cost_agrees(entry.get('cost'), cell) is not False:
                bump('rows_verified_from_flat_text')
                continue
            note('item-not-in-source',
                 f'{head}: {item_id} ({items.get(item_id)}) cost={entry.get("cost")}')

    matched: dict[int, dict] = {}
    for section in sections:
        if not rows_of(section):
            continue  # a container heading, its rows belong to the child lists
        head_words = set(tokens(section['head']))
        exact = [lst for lst in lists if set(tokens(lst.get('name'))) == head_words]
        # The YAML name usually carries the band prefix the page heading omits
        # ("Hero Equipment List" vs "Necrarch Hero Equipment List"), so containment
        # is allowed in both directions; several candidates are reported, not guessed.
        candidates = exact or [lst for lst in lists
                               if head_words and (head_words <= set(tokens(lst.get('name')))
                                                  or set(tokens(lst.get('name'))) <= head_words)]
        if not candidates:
            note('list-not-ingested', section['head'])
            continue
        if len(candidates) > 1:
            longest = max(len(tokens(c.get('name'))) for c in candidates)
            specific = [c for c in candidates if len(tokens(c.get('name'))) == longest]
            if len(specific) > 1:
                note('list-ambiguous',
                     f"{section['head']}: {[c.get('id') for c in specific]}")
                continue
            target = specific[0]
        else:
            target = candidates[0]
        matched[section['index']] = target
        verify_pair(section, target)

    # A list the page never publishes cannot be checked at all.
    seen = {str(lst.get('id')) for lst in matched.values()}
    for lst in lists:
        if str(lst.get('id')) not in seen:
            note('list-without-source', f"{lst.get('id')} ({lst.get('name')})")

    # Rows printed under a heading whose child lists are the only lists ingested
    # would be source rows no list ingests.
    for section in sections:
        if not section['children'] or rows_of(section):
            continue
        remaining = child_rows(section)
        for child_index in section['children']:
            child = by_index.get(child_index)
            if child is None or child_index not in matched:
                continue
            for row in table_rows(slice_of(page, heads, child['index'])):
                if row in remaining:
                    remaining.remove(row)
        for item_name, cost_cell in remaining:
            note('source-row-unmatched', f"{section['head']}: {item_name} ({cost_cell})")


# A stat header the page prints *inside* a Special Equipment section: the mounts and
# the familiars carry their own profile row there, and the profile is the only part
# of such an item the app cannot derive from the prose.
STAT_HEADER = re.compile(r'\bm ws bs s t w i a ld\b')   # norm() lowercases the section
STAT_CELL = re.compile(r'\d+|-')   # norm() folds en/em dashes to '-'


def item_prose(item: dict) -> str:
    parts = [str(item.get('effect') or '')]
    for special in item.get('special_rules') or ():
        parts.append(f"{special.get('name') or ''} {special.get('effect') or ''}")
    return ' '.join(parts)


def carries_in_order(needle: list[str], haystack: list[str]) -> bool:
    index = 0
    for value in haystack:
        if index < len(needle) and value == needle[index]:
            index += 1
    return index == len(needle)


def check_item_profiles(band_id: str, page: str, heads: list[tuple[int, str, int]],
                        items: dict[str, str], records: dict[str, dict], note) -> None:
    """A profile row printed in a Special Equipment section must be transcribed.

    These sections are prose, so ``audit_2a.py`` — which reads the page's
    ``div.fighter`` blocks — never sees them: the Pigback Mount's M..Ld row was
    missing from the catalogue until the 2A re-verification compared digits against
    the source. The row is compared as an ordered subsequence of the numbers in the
    item's own text, so the wording wrapped around it is free.
    """
    for index, (level, head, _pos) in enumerate(heads):
        if level != 2 or norm(head) != 'special equipment':
            continue
        for child_index in range(index + 1, len(heads)):
            lvl, item_heading, _p = heads[child_index]
            if lvl <= level:
                break
            if lvl != 3:
                continue
            fragment = html_mod.unescape(re.sub(r'<[^>]+>', ' ',
                                               slice_of(page, heads, child_index)))
            section = re.sub(r'\s+', ' ', norm(fragment))
            match = STAT_HEADER.search(section)
            if not match:
                continue
            cells = STAT_CELL.findall(section[match.end():])[:9]
            printed = [cell for cell in cells if cell.isdigit()]
            if not printed:
                continue
            # Every plausible catalogue item is accepted: the display names collide
            # across catalogs (the KB's Trollheim ``familiar`` vs the 2A
            # ``society_familiar``), and the check is about the row being written
            # down, not about which of the candidates the packager picked.
            candidates = [item_id for item_id, _how in candidate_ids(item_heading, items)]
            if not candidates:
                continue   # an item that does not exist is already reported
            bump('item_profiles_checked')
            if not any(carries_in_order(printed, re.findall(
                    r'\d+', item_prose(records.get(item_id) or {})))
                       for item_id in candidates):
                note('item-profile-absent', f'{candidates[0]}: {" ".join(printed)}')


# A parenthetical clarification inside rule prose — "(i.e. …)", "(thus, …)",
# "(no save allowed)" — as opposed to a worked example, which the KB drops (no file
# of the KB, 2A or 2B carries an "(Example: …)").
CLARIFICATION = re.compile(r'\(([^()]{12,})\)')
EXAMPLE_LEAD = re.compile(r'^(?:\d+\s*)?(?:example|ex\.|ex |e\.g\.|eg\.)', re.I)
# Headings whose prose is a *list* (every row of it is compared by
# ``check_equipment_lists``), not rule text: their parenthesised restrictions must not
# be read as rule clarifications.
LIST_HEADING = re.compile(r'equipment list|skill table|characteristic increase')


def rule_prose_section(heads: list[tuple[int, str, int]],
                       rule: dict) -> int | None:
    """Index of the heading a rule says it transcribes, if the page has it.

    Only the rule's own section is checked, and only when the last segment of
    ``source.section`` names an ``h3``: the section is then the prose of *that* rule,
    so a clarification it prints belongs in that rule's effect. A rule citing a
    container heading (``Special Skills``) owns no prose of its own and is skipped.
    """
    section = str((rule.get('source') or {}).get('section') or '')
    tail = norm(section.split('/')[-1]).strip()
    if not tail:
        return None
    for index, (level, head, _pos) in enumerate(heads):
        if level != 3 or LIST_HEADING.search(norm(head)):
            continue
        if norm(head) == tail:
            return index
    return None


# The pages write small numbers both ways ("you cannot have 1 snotling runt" vs the
# transcription's "one Snotling runt"): the figure is the same number.
NUMBER_WORDS = {'1': 'one', '2': 'two', '3': 'three', '4': 'four', '5': 'five',
                '6': 'six', '7': 'seven', '8': 'eight', '9': 'nine', '10': 'ten'}


def number_words(text: str) -> str:
    return re.sub(r'\b(\d{1,2})\b',
                  lambda m: NUMBER_WORDS.get(m.group(1), m.group(0)), text)


def check_rule_clarifications(band_id: str, page: str, heads: list[tuple[int, str, int]],
                              rules: list[dict], note) -> None:
    """A clarification the page writes inside rule prose must survive transcription.

    Three of them had been condensed away (the Stampede bonus, the Rememberer's
    Back-up Records and the Monster Slayer modifier wording) with no check noticing:
    the sections are prose and only the rule *names* were traced to the page. The
    magic sections are covered too, because their prose is ingested into the lore
    catalog rather than into a rule.
    """
    written = [str(rule.get('effect') or '') for rule in rules]
    written += [str(s.get('effect') or '') for rule in rules
                for s in rule.get('special_rules') or []]
    for lore in magic_lores():
        ref = (lore.get('source_refs') or [{}])[0]
        slug = str(ref.get('url') or '').rsplit('/', 1)[-1]
        if slug_to_band().get(slug) == band_id:
            written += [str(spell.get('effect') or '') for spell in lore.get('spells') or []]
    # Band-wide: one section may feed several rules (the Slayer rules block carries
    # the Rememberer's own rule), and what matters is that the clarification is written
    # down in the package, not which rule of it holds it.
    haystack = re.sub(r'\s+', ' ', number_words(norm(' '.join(written))))
    for rule in rules:
        index = rule_prose_section(heads, rule)
        if index is None:
            continue
        fragment = html_mod.unescape(re.sub(r'<[^>]+>', ' ', slice_of(page, heads, index)))
        section = re.sub(r'\s+', ' ', norm(fragment))
        for match in CLARIFICATION.finditer(section):
            text = number_words(re.sub(r'\s+', ' ', match.group(1)).strip())
            if EXAMPLE_LEAD.match(text):
                continue     # a worked example: dropped by convention
            bump('clarifications_checked')
            if text not in haystack:
                note('clarification-absent',
                     f'{rule.get("id")} [{heads[index][1]}]: ({text[:80]})')


def check_band(band_id: str, items: dict[str, str]) -> list[dict]:
    findings: list[dict] = []

    def note(kind: str, detail: str) -> None:
        for k, b, prefix, reason in KNOWN:
            if k != kind or (b is not None and b != band_id):
                continue
            if prefix is not None and not detail.startswith(prefix):
                continue
            findings.append({'band': band_id, 'kind': kind, 'detail': detail,
                             'verdict': 'known', 'why': reason})
            return
        findings.append({'band': band_id, 'kind': kind, 'detail': detail})

    page_path = os.path.join(PAGES, f'{band_id}.html')
    if not os.path.exists(page_path):
        note('missing-page', page_path)
        return findings
    page = open(page_path, encoding='utf-8').read()
    raw = open(os.path.join(TEXT, f'{band_id}.txt'), encoding='utf-8').read()
    flat = norm(raw)
    heads = headings(page)

    band_doc = docs(f'{BANDS}/{band_id}/band.yaml')[0]
    rules: list[dict] = []
    for doc in docs(f'{BANDS}/{band_id}/special-rules.yaml'):
        rules += doc.get('rules') or []
    lists: list[dict] = []
    for doc in docs(f'{BANDS}/{band_id}/equipment-access.yaml'):
        lists += doc.get('equipment_lists') or []

    # --- 1. band identity ----------------------------------------------------
    # The band name comes from the mordheimer index, not from the band page's own
    # prose, so it is checked against the manifest entry (the authoritative source
    # for the name) rather than searched for verbatim in the extracted text.
    name = str(band_doc.get('name') or '')
    manifest_name = str(manifest_names().get(band_id) or '')
    if name and manifest_name and set(tokens(name)) != set(tokens(manifest_name)):
        note('band-name', f'{name!r} vs manifest {manifest_name!r}')
    for member in (band_doc.get('roster') or {}).get('members') or []:
        pid = str(member.get('profile_id'))
        profile = next((p for doc in docs(f'{BANDS}/{band_id}/profiles.yaml')
                        for p in doc.get('profiles') or []
                        if str(p.get('id')) == pid), {})
        pname = str(profile.get('name') or pid)
        if norm(pname) not in flat:
            note('roster-name', pname)

    # --- 2. special skills (h3s between the "Special Skills" h2 and the next h2) --
    # A skill list may be ingested as one rule per skill or as a single band rule
    # that enumerates the list in its prose (e.g. band--slayer-special-skills), so a
    # heading counts as ingested when it appears in any rule name *or* rule effect.
    rule_names = [str(r.get('name') or '') for r in rules]
    rule_prose_plain = f" {'  '.join(plain(r.get('effect')) for r in rules)} "
    for index, (level, head, _pos) in enumerate(heads):
        if level != 2 or norm(head) != 'special skills':
            continue
        end = next((j for j in range(index + 1, len(heads)) if heads[j][0] <= 2), len(heads))
        for lvl, skill, _p in heads[index + 1:end]:
            if lvl != 3:
                continue
            if norm(skill).endswith('only'):
                # "Strigoi Vampire Only" is a heading for a restricted skill list,
                # not a skill: nothing to ingest under that name.
                continue
            if any(squash(skill) == squash(rn) or set(tokens(skill)) == set(tokens(rn))
                   for rn in rule_names):
                continue
            if plain(skill) and f' {plain(skill)} ' in rule_prose_plain:
                continue
            note('skill-not-ingested', skill)

    # --- 3. special equipment ------------------------------------------------
    for index, (level, head, _pos) in enumerate(heads):
        if level != 2 or norm(head) != 'special equipment':
            continue
        for lvl, item, pos in heads[index + 1:]:
            if lvl <= level:
                break
            if lvl != 3:
                continue
            if match_item(item, items)[0] is None:
                note('equipment-not-ingested', item)

    # --- 3b. profile rows printed inside a Special Equipment section ----------
    check_item_profiles(band_id, page, heads, items, catalog_item_records(), note)

    # --- 4. equipment lists, both directions ---------------------------------
    check_equipment_lists(band_id, page, heads, lists, items, raw, note)

    # --- 4b. special-equipment prices (the sections' own printed prices) ------
    list_prices: dict[str, object] = {}
    for lst in lists:
        for entry in lst.get('items') or ():
            if isinstance(entry, dict) and entry.get('item_id') is not None:
                list_prices.setdefault(str(entry['item_id']), entry.get('cost'))
    check_special_equipment_prices(band_id, page, heads, list_prices, note)

    # --- 5. rule names traceable to the page ---------------------------------
    # Compared on alphanumerics only: the pages punctuate freely ("Achilles'
    # Heel", "'Eadache!", "That (Git)'s Got Talent!") and those marks are not
    # identity. A name absent even then is only accepted when the rule cites a
    # source section that does exist on the page.
    flat_plain = f' {plain(flat)} '
    for rule in rules:
        rname = str(rule.get('name') or '')
        if rname and f' {plain(rname)} ' in flat_plain:
            continue
        section = str((rule.get('source') or {}).get('section') or '')
        if section and f' {plain(section.split("/")[-1])} ' in flat_plain:
            note('rule-name-paraphrased', f'{rule.get("id")}: {rname} [source section present]')
            continue
        if rname:
            note('rule-name-absent', f'{rule.get("id")}: {rname}')

    # --- 5b. parenthetical clarifications inside rule prose -------------------
    check_rule_clarifications(band_id, page, heads, rules, note)

    # --- 6. spell lists (one lore per magic section) --------------------------
    for lore in magic_lores():
        ref = (lore.get('source_refs') or [{}])[0]
        slug = str(ref.get('url') or '').rsplit('/', 1)[-1]
        if slug_to_band().get(slug) != band_id:
            continue
        lname = str(lore.get('name') or '')
        # The heading may be the lore's own h2 (most bands) or an h3 under a generic
        # "Magic" h2 (Survivors of Strigos); the deepest matching heading wins so the
        # section slice starts at the lore, not at its parent.
        candidates = [i for i, (lvl, h, _p) in enumerate(heads)
                      if lvl >= 2 and magic_heading_matches(lname, h)]
        index = max(candidates, key=lambda i: heads[i][0]) if candidates else None
        if index is None:
            note('lore-section-absent', f'{lore.get("id")}: no heading for {lname!r}')
            continue
        fragment = slice_of(page, heads, index)
        found = spell_entries(fragment, heads[index][1])
        if not found:
            note('magic-section-unparsed', f'{lore.get("id")}: {heads[index][1]}')
            continue
        for spell in lore.get('spells') or []:
            sname = str(spell.get('name') or '')
            hit = next((e for e in found if spells_match(sname, e['name'])), None)
            if hit is None:
                note('spell-absent-from-source', f'{lore.get("id")}: {sname}')
                continue
            source_diff, yaml_diff = hit.get('difficulty'), spell.get('difficulty')
            if source_diff is not None and yaml_diff is not None:
                if str(source_diff) != str(yaml_diff):
                    note('spell-difficulty', f'{lore.get("id")}/{sname}: '
                         f'source={source_diff} yaml={yaml_diff}')
            if not (spell.get('name_i18n') or {}).get('es'):
                note('spell-i18n', f'{lore.get("id")}/{sname}: no name_i18n.es')
        for entry in found:
            if not any(spells_match(str(s.get('name') or ''), entry['name'])
                       for s in lore.get('spells') or []):
                note('spell-not-ingested',
                     f'{lore.get("id")}: {entry["name"]} '
                     f'(difficulty {entry.get("difficulty")})')

    # --- 7. Hired Sword / Dramatis Personae access ---------------------------
    # The pages carry access rules, not stat blocks: the stat blocks live in the KB
    # hireling catalogs. What must be ingested here is the band's access, so every
    # sentence that grants or forbids hirelings has to be reflected by a rule, and
    # every hireling the sentence names must exist in a hireling catalog.
    # Statements come from the *raw* text: normalising first would lowercase every
    # proper name, and the hireling names are exactly what has to be checked.
    own_prose = f' {plain("  ".join(str(r.get("effect") or "") for r in rules))} '
    statements = access_statements(raw)
    if statements and 'hired sword' not in own_prose and 'dramatis' not in own_prose:
        note('hireling-access-missing', f'{len(statements)} source statement(s), no rule')
    catalog = hireling_names()
    warbands = band_name_keys()
    own_names = {profile_key(band_doc.get('name')), profile_key(band_doc.get('canonical_family')),
                 profile_key(manifest_names().get(band_id))}
    own_tokens: set[str] = set()
    for field in ('name', 'canonical_family'):
        own_tokens |= set(tokens(band_doc.get(field) or ''))
    own_tokens |= set(tokens(manifest_names().get(band_id) or ''))
    for doc in docs(f'{BANDS}/{band_id}/profiles.yaml'):
        for profile in doc.get('profiles') or []:
            if isinstance(profile, dict):
                own_tokens |= set(tokens(profile.get('name') or ''))
    rule_names = {plain(r.get('name') or '') for r in rules}
    page_headings = {plain(head) for _level, head, _pos in heads}
    NAME_RE = re.compile(r'\b(?:[A-Z][\w\'\u2019-]+ ){1,3}[A-Z][\w\'\u2019-]+')
    for statement in statements:
        # Hirelings are offered from the access phrase onwards ("may only hire the
        # following Hired Swords: … you may hire an Ogre Bodyguard and/or Ogre Slaver").
        # A name *before* it is context, not an offer: the snotlings' "roll on the Hero's
        # Advancement Table (… very much like Hired Swords)" only cites a table.
        low = norm(statement)
        starts = [low.find(word) for word in ACCESS_WORDS]
        matches = list(NAME_RE.finditer(statement))
        if any(start >= 0 for start in starts):
            in_list_from = min(start for start in starts if start >= 0)
        elif len(matches) >= 2:
            in_list_from = 0   # an enumeration without an introducer still offers hirelings
        else:
            continue            # a lone name in a comparison sentence is not an offer
        for match in matches:
            name = match.group(0)
            if match.start() < in_list_from:
                continue
            cleaned = ' '.join(name.split()).strip(' -\u2013\u2014')
            if not plain(cleaned):
                continue
            # The sentence regex bridges into neighbouring headings and rule names
            # ("Special Rules", "Shady Reputation"); those are not hirelings.
            if plain(cleaned) in rule_names or plain(cleaned) in page_headings:
                continue
            text = plain(cleaned)
            key = profile_key(cleaned)
            if key in own_names or key in warbands:
                continue  # the band itself, or another warband it is compared to
            if own_tokens and set(tokens(cleaned)) <= own_tokens:
                continue  # the band's own fighter type ("Ogre Hunter warbands…")
            if any(phrase in text for phrase in CATEGORY_PHRASES):
                continue
            if any(word in text for word in WARBAND_WORDS):
                continue
            if set(text.split()) & ARTEFACT_WORDS:
                continue
            # Ingestion requirement, catalog or not: a hireling the source offers has to
            # appear in the band's own access prose.
            if text in HIRELING_SYNONYMS:
                synonym = plain(HIRELING_SYNONYMS[text])
                if synonym not in own_prose and text not in own_prose:
                    note('hireling-name-absent',
                         f'{cleaned} [= catalog {HIRELING_SYNONYMS[text]!r}]')
            elif presence_key(cleaned) not in own_prose:
                note('hireling-name-absent', f'{cleaned} (in {statement[:60]!r}…)')
            # ... and when the package did ingest it, the catalogs have to resolve it, or
            # the warband's access points at a hireling the app cannot offer at all.
            ingested = text in own_prose or presence_key(cleaned) in own_prose
            if ingested and key not in catalog and text not in HIRELING_SYNONYMS:
                note('hireling-not-in-catalog', f'{cleaned} (in {statement[:60]!r}…)')
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--band', help='audit a single band id')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--show', type=int, default=12)
    parser.add_argument('--all', action='store_true', help='include adjudicated findings')
    args = parser.parse_args()

    items = catalog_items()
    band_ids = ([args.band] if args.band
                else sorted(os.path.basename(os.path.dirname(p))
                            for p in glob.glob(f'{BANDS}/*/band.yaml')))
    report: list[dict] = []
    for band_id in band_ids:
        report += check_band(band_id, items)

    known = [row for row in report if row.get('verdict') == 'known']
    open_rows = [row for row in report if row.get('verdict') != 'known']

    if args.json:
        print(json.dumps({'open': open_rows, 'adjudicated': known}, indent=2, ensure_ascii=False))
        return 1 if open_rows else 0

    print(f'sources/2A vs cached pages: {len(open_rows)} open finding(s),'
          f' {len(known)} adjudicated')
    stats = defaultdict(int, STATS)
    print('equipment coverage: {lists} list(s) matched ({h2} published under an h2);'
          ' {priced} printed row(s) compared ({matching} matching, {no_cell} without a'
          ' price cell); {absent} list entr(y/ies) absent from the tables ({flat} of'
          ' them confirmed by the flat-text extraction)'.format(
              lists=stats['lists_verified'], h2=stats['list_levels_h2'],
              priced=stats['rows_priced'], matching=stats['rows_price_verified'],
              no_cell=stats['rows_without_a_price_cell'],
              absent=stats['rows_checked_against_page'],
              flat=stats['rows_verified_from_flat_text']))
    print('rule prose: {clar} parenthetical clarification(s) of the rule sections compared'
          ' with the rule and lore texts'.format(clar=stats['clarifications_checked']))
    print('special-equipment coverage: {items} catalogue item(s) of the 19 bands, {priced}'
          ' with a price on the page compared against the recorded one; {rows} profile'
          ' row(s) printed inside those sections compared with the item text'.format(
              items=stats['special_items_checked'], priced=stats['special_prices_compared'],
              rows=stats['item_profiles_checked']))
    by_kind: dict[str, list[dict]] = {}
    for row in (report if args.all else open_rows):
        by_kind.setdefault(row['kind'], []).append(row)
    for kind, rows in sorted(by_kind.items()):
        print(f'\n## {kind} ({len(rows)})')
        for row in rows[:args.show]:
            suffix = f'  — known: {row["why"]}' if row.get('verdict') == 'known' else ''
            print(f"  {row['band']}: {row['detail']}{suffix}")
        if len(rows) > args.show:
            print(f'  … {len(rows) - args.show} more')
    return 1 if open_rows else 0


if __name__ == '__main__':
    sys.exit(main())

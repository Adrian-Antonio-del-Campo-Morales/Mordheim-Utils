"""Give the staged catalogues the promotion shape of the knowledge base.

The staging trees transcribe sources faithfully; the knowledge base keeps the
same facts in *its* places. This module is the transformation between the two,
and every step follows a decision the KB already carries:

- **Market facts live in the campaign market catalogue.** ``catalog/items/*``
  carries identity, printed text and the mechanic; price, availability, rarity
  and buying restrictions live in ``catalog/campaign/trading-post.yaml``, which
  is where the rarity test reads them from (``campaign/trading-and-rarity.yaml``
  names ``availability.rarity`` of that document as its target). The staged item
  catalogues therefore gain a *staged market document* with one entry per item —
  the same one-entry-per-item coverage the KB keeps, 335 of 335 — and lose
  ``rarity``, ``availability_note``, ``availability_note_i18n`` and ``unique``.
- **An item's printed rules are its printed text.** ``special_rules`` is a
  staging-side structure of the same prose ``effect`` already carries, and
  ``rules`` is printed text too, so both fold into ``effect`` (and, for the
  Spanish the source also prints, into ``effect_i18n.es``: the rule names and
  their text, joined into the one prose field the item contract has). Nothing is
  dropped: every rule name and its text survives inside the field.
- **The item ``kind`` is the contract's enum.** ``miscellaneous``, ``mount`` and
  ``ammunition`` are staging names the KB splits across ``combat-equipment``,
  ``material-or-upgrade`` and ``out-of-scope``; the reclassification is a table
  here, item by item, not a guess in code.
- **The catalogue envelope is the KB envelope.** Item and hireling catalogues
  carry no ``status`` (the KB files have none), and a staged document that *is*
  a new KB document — the market catalogue, the magic catalogue — carries the
  status of unconfirmed content (``draft``), not ``published``: the merge into
  the published document is what promotes it.
- **A collection of the KB is a block collection.** The keys the KB writes as a
  block sequence (``source_path``, ``equipment_lists``, ``rule_ids``,
  ``skill_access``) or as a block mapping (``source``, ``characteristics``,
  ``name_i18n``, ``combat_traits``) are never a non-empty flow collection there,
  so the staged ``[a, b]`` and ``{a: 1}`` are rewritten to the shape the KB
  keeps. An *empty* collection stays: ``[]`` and ``{}`` are the KB's own shape.

- **A band package is promoted whole.** The KB keeps one directory per band and
  the staging tree already writes that shape, so the band step is a copy: the
  four documents keep their prose, their ``runtime`` marks, their band-side
  prices, notes and provenance, and only the declared transforms touch them —
  every ``item_id`` follows the identity decisions of T04 and an annotation that
  named a staging tree names the KB document the same facts live in. A package
  the KB carries with different content is a collision, and the promotion
  refuses it instead of overwriting a published record.

Editing is lexical: the staged files carry comments, so the passes edit the
lines they own instead of re-dumping the document, and ``tools/knowledge/maintenance/format_yaml.py``
still owns the canonical shape of everything written. Each pass re-parses what
it wrote and compares it with a pure transform of what it read.
"""
from __future__ import annotations

import re
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml

from mordheim_knowledge import open_field_normalization as lexical
from mordheim_knowledge.editorial_schemas import validate_document

CHECKOUT = lexical.CHECKOUT
STAGING_TREES = lexical.STAGING_TREES
KB_ROOT = lexical.KB_ROOT

#: Indent of the keys of a catalogue record: the ``- id:`` of a record sits at
#: column zero, so its own keys sit one level in. Distinguishes a record's
#: ``effect`` from the ``effect`` of an item rule nested under it.
RECORD_INDENT = 2

#: The editorial status of a staged document that will merge into a published
#: KB document. ``draft`` is the contract's own word for content a curator has
#: not confirmed yet, so the staged catalogue never claims to be published.
STAGED_STATUS = "draft"


# --------------------------------------------------------------------------- #
# Item kinds: the KB enum, item by item
# --------------------------------------------------------------------------- #

#: Staging kind -> KB kind, per item. The KB distinguishes usable gear
#: (``combat-equipment``), something applied to another item
#: (``material-or-upgrade``) and a record carried for the campaign runtime only
#: (``out-of-scope``, which is how the KB keeps its wardogs, war boars and other
#: creatures). ``miscellaneous`` and ``mount`` are staging names for all three.
ITEM_KINDS: dict[str, str] = {
    # 2A — creatures and mounts are carried for the campaign runtime, as the KB
    # does with `warhound`, `war_boar`, `giant_wolf` and `giant_spider`.
    "wolf_rat_mount": "out-of-scope",
    "pigback_mount": "out-of-scope",
    "power_squig": "out-of-scope",
    "society_familiar": "out-of-scope",
    # 2A — gear a warband carries.
    "hooded_lantern_rig": "combat-equipment",
    "surgeons_journal": "combat-equipment",
    "finger_pendant": "combat-equipment",
    "bearcloak": "combat-equipment",
    "unholy_relic": "combat-equipment",
    "damned_book": "combat-equipment",
    "sashimono": "combat-equipment",
    "black_gold_wristbands": "combat-equipment",
    "ring_of_strigos": "combat-equipment",
    "cursed_book": "combat-equipment",
    # 2A — ammunition is an upgrade of the missile weapon, as the KB keeps
    # `hunting_arrows` and the other ammunition entries.
    "blessed_bolts": "material-or-upgrade",
    # 2B — the harpoon is printed in the Missile Weapons sections and its own
    # text calls it a thrown javelin, so the staged `close-combat-weapon` is
    # wrong; the reclassification is the declared correction of T04 (§A.8).
    "harpoon": "ranged-weapon",
}

#: Item keys the KB item record does not have; their facts move to the staged
#: market document (``rarity``, ``availability_note``, ``availability_note_i18n``,
#: ``unique``) or into ``effect`` (``special_rules``, ``rules``).
MARKET_KEYS: tuple[str, ...] = ("rarity", "availability_note", "availability_note_i18n", "unique")
PROSE_KEYS: tuple[str, ...] = ("special_rules", "rules")

#: Root keys the staged catalogue does not carry. ``status`` is the one the KB
#: item and hireling files never had.
DROP_ROOT_KEYS: tuple[str, ...] = ("status",)

#: The catalog id each staged document adopts: the id its KB family uses.
CATALOG_IDS: dict[str, str] = {
    "catalog/magic-2a.yaml": "campaign-magic",
    "catalog/magic-2b.yaml": "campaign-magic",
    "catalog/trading-post-2a.yaml": "campaign-trading-post",
    "catalog/trading-post-2b.yaml": "campaign-trading-post",
    "catalog/hired-swords-and-dramatis-2b.yaml": "campaign-hired-swords-and-dramatis",
}

MARKET_DOCUMENTS: dict[str, str] = {
    "2A": "catalog/trading-post-2a.yaml",
    "2B": "catalog/trading-post-2b.yaml",
}

#: The staged documents that are a new KB document rather than a package file.
STAGED_DOCUMENTS = tuple(MARKET_DOCUMENTS.values()) + (
    "catalog/magic-2a.yaml",
    "catalog/magic-2b.yaml",
    "catalog/hired-swords-and-dramatis-2b.yaml",
)

#: The printed rules of an item are prose in the KB, so the market entry of a
#: unique item cannot live on price: it is found, not bought, and the note says
#: so in the field the KB uses for exactly that (``restriction.note``).
UNIQUE_NOTE = (
    "Unique: the source prints a single specimen per campaign, found through the "
    "exploration chart rather than bought at the trading post."
)
#: An item no source of the pack prices: the entry records that the pack prints
#: no market price for it, the way the KB notes a `not_sold` item of its own.
UNPRICED_NOTE = "No source of the pack prints a market price for it; the item is carried for the campaign record."


@dataclass
class Report:
    """The edits of a full run, one entry per file."""

    edits: list[lexical.Edit] = field(default_factory=list)

    @property
    def changed(self) -> bool:
        return bool(self.edits)

    def write(self) -> list[Path]:
        for edit in self.edits:
            edit.write()
        return [edit.path for edit in self.edits]


def _tree_root(tree: str) -> Path:
    return Path("sources") / tree


def _document_path(tree: str, relative: str) -> Path:
    return _tree_root(tree) / relative


def _item_catalogues(tree: str) -> list[Path]:
    return sorted(path for path in (_tree_root(tree) / "catalog" / "items").glob("*.yaml"))


def _catalogue_files(tree: str) -> list[Path]:
    """Every catalogue YAML of a tree: the items, the hirelings and the documents."""
    root = _tree_root(tree) / "catalog"
    return sorted(path for path in root.rglob("*.yaml") if path.is_file())


def _items(path: Path) -> list[dict]:
    document = yaml.safe_load(lexical.read_text(path))
    return list((document or {}).get("items") or [])


# --------------------------------------------------------------------------- #
# Lexical edits of a record: the block of one catalogue record
# --------------------------------------------------------------------------- #

_KEY = lexical.KEY
_LIST_ITEM = re.compile(r"^\s*-\s")


def _key_of(line: str) -> tuple[str, int, bool] | None:
    """``(key, indent, is_list_item)`` of a mapping key line, or ``None``."""
    match = _KEY.match(line)
    if match is None:
        return None
    return match.group("key"), len(match.group("indent")), bool(match.group("dash"))


def _own_key(line: str, key: str, indent: int) -> bool:
    """Whether the line declares ``key`` at exactly ``indent``, not as a list item."""
    found = _key_of(line)
    return found is not None and found[0] == key and found[1] == indent and not found[2]


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip())


def _block_end(lines: list[str], start: int, indent: int) -> int:
    """Index after the last line of the block a key at ``indent`` owns."""
    index = start + 1
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            lookahead = index
            while lookahead < len(lines) and not lines[lookahead].strip():
                lookahead += 1
            if lookahead >= len(lines):
                break
            following = lines[lookahead]
            if _indent_of(following) > indent or (
                _indent_of(following) == indent and _LIST_ITEM.match(following)
            ):
                index = lookahead
                continue
            break
        if _indent_of(line) > indent or (_indent_of(line) == indent and _LIST_ITEM.match(line)):
            index += 1
            continue
        break
    return index


def _drop_keys(lines: list[str], key: str, indent: int) -> int:
    """Remove every ``key`` block at ``indent``; returns how many were dropped."""
    dropped = 0
    index = len(lines) - 1
    while index >= 0:
        if _own_key(lines[index], key, indent):
            end = _block_end(lines, index, indent)
            del lines[index:end]
            dropped += 1
        index -= 1
    return dropped


def _folded(lines: list[str], index: int, text: str) -> list[str]:
    """The ``key: >-`` block that carries ``text``, replacing the block at ``index``."""
    line = lines[index]
    indent = _indent_of(line)
    found = _key_of(line)
    assert found is not None
    ending = lexical.line_ending(line)
    # One physical line per value: wrapping prose is ``tools/knowledge/maintenance/format_yaml.py``'s
    # job, and it folds only where folding cannot change the text (`To-Hit` is
    # never split across the break). A hand-rolled wrap would silently turn a
    # hyphenated word into two.
    block = [f"{' ' * indent}{found[0]}: >-{ending}", f"{' ' * (indent + 2)}{text}{ending}"]
    end = _block_end(lines, index, indent)
    lines[index:end] = block
    return lines


def _parent_at(lines: list[str], index: int, parent: str) -> bool:
    """Whether the key at ``index`` sits inside a ``parent:`` block."""
    indent = _indent_of(lines[index])
    for earlier in range(index - 1, -1, -1):
        line = lines[earlier]
        if not line.strip():
            continue
        if _indent_of(line) < indent:
            return _own_key(line, parent, _indent_of(line))
    return False


def _set_scalar(lines: list[str], key: str, text: str, *, parent: str | None = None) -> bool:
    """Rewrite the folded scalar of ``key``; ``parent`` scopes it to a nested block."""
    indent = RECORD_INDENT + 2 if parent else RECORD_INDENT
    for index, line in enumerate(lines):
        if not _own_key(line, key, indent):
            continue
        if parent is not None and not _parent_at(lines, index, parent):
            continue
        _folded(lines, index, text)
        return True
    return False


def _insert_scalar(
    lines: list[str], anchor: str, key: str, text: str, *, parent: str | None = None
) -> bool:
    """Write ``key: >-`` after the block of ``anchor``, when the key has no block yet."""
    for index, line in enumerate(lines):
        if not _own_key(line, anchor, RECORD_INDENT):
            continue
        block = [line for line in _folded_lines(line, key, text, parent=parent)]
        lines[_block_end(lines, index, RECORD_INDENT) : _block_end(lines, index, RECORD_INDENT)] = block
        return True
    return False


def _folded_lines(line: str, key: str, text: str, *, parent: str | None = None) -> list[str]:
    """The lines of a ``key: >-`` (or ``parent:`` + ``key: >-``) block."""
    ending = lexical.line_ending(line)
    indent = RECORD_INDENT if parent is None else RECORD_INDENT + 2
    child = indent + 2
    block: list[str] = []
    if parent is not None:
        block.append(f"{' ' * RECORD_INDENT}{parent}:{ending}")
    block.append(f"{' ' * indent}{key}: >-{ending}")
    block.append(f"{' ' * child}{text}{ending}")
    return block


def _record_id(line: str) -> str | None:
    """The ``id`` a catalogue record opens with: a ``- id: x`` at column zero.

    The indent matters: an item rule nested under ``special_rules`` is written
    as ``  - id: critical-damage``, and reading that as a record boundary would
    split the record that owns it.
    """
    match = _KEY.match(line)
    if match is None or not match.group("dash") or match.group("key") != "id":
        return None
    if match.group("indent"):
        return None
    value = match.group("rest").strip()
    return value or None


def _records(lines: list[str]) -> list[tuple[int, int]]:
    """``(start, end)`` of every record block of a catalogue document."""
    starts = [index for index, line in enumerate(lines) if _record_id(line) is not None]
    return [
        (start, starts[position + 1] if position + 1 < len(starts) else len(lines))
        for position, start in enumerate(starts)
    ]


# --------------------------------------------------------------------------- #
# The market document
# --------------------------------------------------------------------------- #


def _walk_item_ids(node: Any) -> Iterator[dict]:
    """Every mapping of a document that references an item by id."""
    if isinstance(node, dict):
        if isinstance(node.get("item_id"), str):
            yield node
        for value in node.values():
            yield from _walk_item_ids(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_item_ids(value)


def _listed_items(tree: str) -> dict[str, tuple[str, dict]]:
    """``{item_id: (band id, entry)}`` of every item a staged list buys."""
    found: dict[str, tuple[str, dict]] = {}
    for path in sorted((_tree_root(tree) / "bands").glob("*/*/equipment-access.yaml")):
        document = yaml.safe_load(lexical.read_text(path)) or {}
        for entry in _walk_item_ids(document):
            found.setdefault(entry["item_id"], (path.parent.name, entry))
    return found


def _carried_items(tree: str) -> set[str]:
    """``item_ids`` a staged profile carries as starting equipment."""
    found: set[str] = set()
    for path in sorted((_tree_root(tree) / "bands").glob("*/*/profiles.yaml")):
        document = yaml.safe_load(lexical.read_text(path)) or {}
        found |= {entry["item_id"] for entry in _walk_item_ids(document)}
    return found


_DICE_COST = re.compile(r"^(\d+)\s*\+\s*(\d*)D(\d+)$")
_RARE = re.compile(r"^Rare\s+(\d+)$", re.IGNORECASE)
_MULTIPLIER = re.compile(r"(\d+)\s*x\s*base\b", re.IGNORECASE)
_PRICE_IN_NOTE = re.compile(r"(\d+)\s*\+\s*(\d*)D(\d+)")
_NOT_FOR_SALE = re.compile(r"starting equipment only|not purchasable|no purchase|innate", re.IGNORECASE)
_HEROES_ONLY = re.compile(r"heroes only", re.IGNORECASE)


def price_of(cost: Any, note: str | None) -> dict | None:
    """The market price of an item, as the KB types it.

    ``base_gc`` for a flat price, ``base_gc`` plus ``optional_variable_cost`` for
    a rolled one (``15 + D6 gc``), ``multiplier`` for something priced against
    the item it upgrades (``3 x base weapon price``) and ``null`` when the source
    prints no market price at all — never a zero standing in for "unknown".
    """
    if isinstance(cost, bool):
        cost = None
    if isinstance(cost, int):
        return {"base_gc": cost}
    if isinstance(cost, str):
        match = _DICE_COST.match(cost.strip())
        if match:
            return {
                "base_gc": int(match.group(1)),
                "optional_variable_cost": {
                    "dice": {"count": int(match.group(2) or 1), "sides": int(match.group(3))}
                },
            }
        if cost.strip().isdigit():
            return {"base_gc": int(cost.strip())}
    if note:
        match = _MULTIPLIER.search(note)
        if match:
            return {"multiplier": int(match.group(1))}
    return None


def availability_of(rarity: Any, note: str | None) -> dict:
    """How the item is obtained: ``common``, ``rare`` with its ``Rare N``, ``not_sold``."""
    if isinstance(rarity, bool):
        rarity = None
    if isinstance(rarity, int):
        return {"kind": "rare", "rarity": rarity}
    if isinstance(rarity, str):
        match = _RARE.match(rarity.strip())
        if match:
            return {"kind": "rare", "rarity": int(match.group(1))}
        if rarity.strip().isdigit():
            return {"kind": "rare", "rarity": int(rarity.strip())}
    if note and _NOT_FOR_SALE.search(note):
        return {"kind": "not_sold"}
    return {"kind": "common"}


def _has_prose(note: str | None) -> bool:
    """Whether an availability note says more than a price and a rarity."""
    if not note:
        return False
    stripped = _PRICE_IN_NOTE.sub("", note)
    stripped = re.sub(r"\b\d+\s*(?:x\b)?", "", stripped)
    stripped = re.sub(
        r"\b(?:cost|gold crowns?|gc|per pair|common|rare\s*\d+|heroes only|only|and|the|a|of|to|be|is|it)\b",
        "",
        stripped,
        flags=re.IGNORECASE,
    )
    return bool(re.search(r"[A-Za-z]{4,}", stripped))


#: A price printed in a currency the KB does not model. ``price.base_gc`` is
#: gold crowns by contract, so a warp-token price is not expressible: the entry
#: records no amount and the source wording — which the entry keeps verbatim —
#: carries it. A free item is the same problem from the other side: the contract
#: has no `free`, and zero gold crowns is what a price of nothing means.
_WARP_TOKENS = re.compile(r"warp\s*tokens?|\bwt\b", re.IGNORECASE)
_FREE = re.compile(r"\bfree\b", re.IGNORECASE)


def printed_price(note: str | None) -> dict | None:
    """The structured price of a printed buying note, when the KB can hold it."""
    if not note:
        return None
    if _WARP_TOKENS.search(note):
        return None
    match = _PRICE_IN_NOTE.search(note)
    if match:
        return price_of(f"{match.group(1)}+{match.group(2) or 1}D{match.group(3)}", None)
    price = price_of(None, note)
    if price is None and _FREE.search(note):
        return {"base_gc": 0}
    return price


def market_entry(item: dict, listed: tuple[str, dict] | None) -> dict:
    """One market entry for an item of a staged catalogue, in the KB entry shape.

    The lists of the bands are the second copy of the market facts a pack keeps:
    a printed price there is the price of the entry, and the rest of the note is
    the buying rule the lists do not keep, so it travels verbatim as a
    ``condition`` restriction.
    """
    item_id = str(item["id"])
    entry = listed[1] if listed is not None else None
    note = item.get("availability_note")
    list_notes = (entry.get("notes") if entry else None) or ""
    # The Special Equipment section of the pack prints the operative price of the
    # item; the band list is the second copy, and it is what prices an item whose
    # own note prints no amount at all.
    price = printed_price(note)
    if price is None and not (note and _WARP_TOKENS.search(note)):
        price = price_of(entry.get("cost") if entry else None, note)
    facts = any(key in item for key in MARKET_KEYS) or listed is not None
    if item.get("unique"):
        availability = {"kind": "not_sold"}
    elif facts:
        availability = availability_of(item.get("rarity"), note)
    else:
        availability = {"kind": "not_sold"}
        price = None
    restrictions: list[dict] = []
    if listed is not None:
        restrictions.append({"type": "warband_only", "band_ids": [listed[0]]})
    # The buying rule of the entry is the item's own note, verbatim: the band
    # list keeps its notes (a list price, the reason for a discrepancy) in the
    # band file, which is where promotion merges them.
    if _HEROES_ONLY.search(f"{note or ''} {list_notes}"):
        restrictions.append({"type": "heroes_only"})
    if item.get("unique"):
        restrictions.append({"type": "condition", "note": UNIQUE_NOTE})
    elif not facts:
        restrictions.append({"type": "condition", "note": UNPRICED_NOTE})
    elif note and _has_prose(note):
        restrictions.append({"type": "condition", "note": note})
    return {
        "id": f"campaign.trading-post.{item_id.replace('_', '-')}",
        "item_id": item_id,
        "price": price,
        "availability": availability,
        "restrictions": restrictions,
        "source_refs": item.get("source_refs") or [],
    }


@dataclass
class MarketDocument:
    path: Path
    text: str
    entries: int


def _kb_document(relative: str) -> dict:
    return yaml.safe_load(lexical.read_text(CHECKOUT / KB_ROOT / "catalog" / relative)) or {}


def _existing_entries(path: Path) -> dict[str, dict]:
    """``item_id -> entry`` of the market catalogue already on disk, if any."""
    if not path.is_file():
        return {}
    document = yaml.safe_load(lexical.read_text(path)) or {}
    return {str(entry["item_id"]): entry for entry in document.get("items") or () if entry.get("item_id")}


def market_document(tree: str) -> MarketDocument:
    """The staged market catalogue of a tree: one entry per staged item.

    The KB keeps an entry for every item it has (335 of 335), so the coverage
    here is the same: an item the pack never prices still gets its entry, with
    ``not_sold`` and the note that says why.

    An entry already written is kept as it is. The market pass reads the market
    facts out of the item records, so a second run — by which time the item pass
    has retired them — would otherwise rebuild every entry from what is left.
    """
    relative = MARKET_DOCUMENTS[tree]
    path = _document_path(tree, relative)
    target = _kb_document("campaign/trading-post.yaml")
    listed = _listed_items(tree)
    existing = _existing_entries(path)
    entries: list[dict] = []
    for catalogue in _item_catalogues(tree):
        for item in _items(catalogue):
            item_id = str(item["id"])
            entries.append(existing.get(item_id) or market_entry(item, listed.get(item_id)))
    entries.sort(key=lambda entry: entry["item_id"])
    manuals = _tree_manuals(tree)
    manual = "broheim.net" if "broheim.net" in manuals else sorted(manuals)[0]
    document = {
        "schema_version": target["schema_version"],
        "ruleset": target["ruleset"],
        "catalog": target["catalog"],
        "status": STAGED_STATUS,
        "source": {
            "manual": manual,
            "printed_page": 0,
            "section": "Band equipment lists and item catalogues of the pack (market availability)",
        },
        "items": entries,
        "effect_ids": target["effect_ids"],
    }
    text = yaml.safe_dump(
        document, allow_unicode=True, sort_keys=False, default_flow_style=False, width=100
    )
    return MarketDocument(path, text, len(entries))


def _tree_manuals(tree: str) -> set[str]:
    values: set[str] = set()
    for path in sorted(_tree_root(tree).rglob("*.yaml")):
        for _, value in lexical.source_reference_values(lexical.read_text(path)):
            values.add(value)
    return values


# --------------------------------------------------------------------------- #
# The item record
# --------------------------------------------------------------------------- #


def folded_effect(item: dict) -> str:
    """The item's printed text with the rules it names folded into it.

    ``special_rules`` names each rule and prints its text; ``rules`` is a prose
    block of its own. The KB item has one prose field, so the rule names and
    their text join it in the order the item declares them, English first and
    Spanish (when the source prints it) in ``effect_i18n.es``.
    """
    parts = [str(item.get("effect") or "").strip()]
    for rule in item.get("special_rules") or []:
        name = rule.get("name") or rule.get("id") or ""
        text = str(rule.get("effect") or "").strip()
        parts.append(f"{name}: {text}" if text else str(name))
    rules = item.get("rules")
    if isinstance(rules, str) and rules.strip():
        parts.append(rules.strip())
    return " ".join(part for part in parts if part)


def folded_effect_es(item: dict) -> str:
    """The Spanish printed text with the Spanish rule names and texts folded in."""
    printed = item.get("effect_i18n") or {}
    parts = [str(printed.get("es") or "").strip()]
    for rule in item.get("special_rules") or []:
        name = (rule.get("name_i18n") or {}).get("es") or ""
        text = str((rule.get("effect_i18n") or {}).get("es") or "").strip()
        if name or text:
            parts.append(f"{name}: {text}" if text else str(name))
    return " ".join(part for part in parts if part)


def promoted_item(item: dict) -> dict:
    """The item record the KB keeps: identity, printed text, kind and provenance."""
    promoted = {
        key: value
        for key, value in item.items()
        if key not in (*MARKET_KEYS, *PROSE_KEYS)
    }
    if promoted["id"] in ITEM_KINDS:
        promoted["kind"] = ITEM_KINDS[promoted["id"]]
    effect = folded_effect(item)
    if effect:
        promoted["effect"] = effect
    spanish = folded_effect_es(item)
    if spanish:
        promoted["effect_i18n"] = {**(item.get("effect_i18n") or {}), "es": spanish}
    return promoted


def promoted_document(document: dict) -> dict:
    """The catalogue document the KB keeps, from the staged one."""
    promoted = {key: value for key, value in document.items() if key not in DROP_ROOT_KEYS}
    promoted["items"] = [promoted_item(item) for item in document.get("items") or []]
    return promoted


def _catalogue_pass(tree: str) -> list[lexical.Edit]:
    """Item catalogues in the item shape the KB keeps, one block per record."""
    edits: list[lexical.Edit] = []
    for path in _item_catalogues(tree):
        original = lexical.read_text(path)
        document = yaml.safe_load(original) or {}
        items = {str(item["id"]): item for item in document.get("items") or []}
        text, dropped = _drop_root_scalar(original, "status")
        changes: list[str] = []
        if dropped:
            changes.append("root status: dropped (the KB item files carry no envelope status)")
        lines = lexical.lines(text)
        for start, end in reversed(_records(lines)):
            item_id = _record_id(lines[start])
            item = items.get(item_id or "")
            if item is None:
                continue
            record = lines[start:end]
            found = _record(record, item, item_id or "")
            lines[start:end] = record
            changes += found
        if not changes:
            continue
        after = "".join(lines)
        _verify_catalogue(path, original, after)
        lexical.publish(path, after)
        edits.append(lexical.Edit(path, changes, after, original))
    return edits


def _drop_root_scalar(text: str, key: str) -> tuple[str, int]:
    """Remove a root-level ``key: value`` written on one line."""
    lines = lexical.lines(text)
    for index, line in enumerate(lines):
        found = _key_of(line)
        if found is not None and found[1] == 0 and found[0] == key:
            del lines[index]
            return "".join(lines), 1
    return text, 0


def _value_of(line: str) -> str:
    """The scalar a key line carries, unquoted."""
    match = _KEY.match(line)
    if match is None:
        return ""
    return (match.group("rest") or "").strip().strip("'\"")


def _record(record: list[str], item: dict, item_id: str) -> list[str]:
    """Put one item record in the KB shape; returns what changed in it."""
    changes: list[str] = []
    kind = ITEM_KINDS.get(str(item["id"]))
    if kind is not None:
        for index, line in enumerate(record):
            if _own_key(line, "kind", RECORD_INDENT):
                # A record already in the target shape is left alone: the pass has
                # to be idempotent, or every run reports work it does not do.
                if _value_of(line) != kind:
                    record[index] = lexical.replace_scalar(line, "kind", kind)
                    changes.append(f"{item_id}.kind -> {kind}")
                break
    for key in MARKET_KEYS:
        if _drop_keys(record, key, RECORD_INDENT):
            changes.append(f"{item_id}.{key}: dropped")
    folded = 0
    for key in PROSE_KEYS:
        folded += _drop_keys(record, key, RECORD_INDENT)
    if folded:
        changes.append(f"{item_id}.{', '.join(PROSE_KEYS)}: folded into effect")
    if changes:
        effect = folded_effect(item)
        if effect:
            _set_scalar(record, "effect", effect)
        spanish = folded_effect_es(item)
        if spanish:
            if not _set_scalar(record, "es", spanish, parent="effect_i18n"):
                _insert_scalar(record, "effect", "es", spanish, parent="effect_i18n")
    return changes


def _verify_catalogue(path: Path, before: str, after: str) -> None:
    """After the pass the document is the pure promotion of the staged one."""
    original = yaml.safe_load(before) or {}
    updated = yaml.safe_load(after) or {}
    expected = promoted_document(original)
    if expected != updated:
        raise ValueError(f"{path}: the item pass changed more than the promotion shape")


# --------------------------------------------------------------------------- #
# The collection shape: the keys the KB writes in block form
# --------------------------------------------------------------------------- #

#: Keys the knowledge base writes as a *block* sequence. Measured over the three
#: trees, the KB keeps these four in block form and never writes a non-empty flow
#: sequence — ``source_path`` 534, ``equipment_lists`` 529, ``rule_ids`` 475,
#: ``skill_access`` 344 — while an empty list is ``[]``, which the KB also writes
#: (``equipment_lists`` 86, ``rule_ids`` 159, ``skill_access`` 287).
BLOCK_SEQUENCE_KEYS: tuple[str, ...] = ("source_path", "equipment_lists", "rule_ids", "skill_access")

#: Keys the knowledge base writes as a *block* mapping: ``name_i18n`` 3 742,
#: ``source`` 2 290, ``characteristics`` 666 and ``combat_traits`` (``{}`` 437
#: times, the rest anchored block mappings). A staged ``{...}`` is the one shape
#: of these keys the KB does not have.
BLOCK_MAPPING_KEYS: tuple[str, ...] = ("source", "characteristics", "name_i18n", "combat_traits")

#: Every key a promotion copy has to write in block form before it merges.
BLOCK_COLLECTION_KEYS: tuple[str, ...] = BLOCK_SEQUENCE_KEYS + BLOCK_MAPPING_KEYS

_FLOW_VALUE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z0-9_.-]+):\s*(?P<value>[\[\{].*)$")


@dataclass(frozen=True)
class FlowCollection:
    """A non-empty flow collection under a key the KB writes in block form."""

    line: int
    end: int
    key: str
    sequence: bool
    body: str


def _value_position(text: str, position: int) -> bool:
    """Whether the quote at ``position`` opens a scalar rather than sits inside one."""
    for earlier in range(position - 1, -1, -1):
        character = text[earlier]
        if character.isspace():
            continue
        return character in ":,{["
    return True


def _flow_span(lines: list[str], start: int, column: int) -> tuple[int, int] | None:
    """``(line, column)`` of the bracket that closes the collection opened here.

    Quotes are tracked because the staged flows carry single-quoted URLs: a `]`
    inside one is text, not the end of the collection.
    """
    depth = 0
    quote: str | None = None
    for index in range(start, len(lines)):
        line = lines[index]
        position = column if index == start else 0
        while position < len(line):
            character = line[position]
            if quote is not None:
                if character == quote:
                    quote = None
            elif character in "'\"" and _value_position(line, position):
                quote = character
            elif character in "[{":
                depth += 1
            elif character in "]}":
                depth -= 1
                if depth == 0:
                    return index, position
            position += 1
    return None


def _one_line(text: str) -> str:
    """A flow body that spans lines, on one line, with quoted text left as it is.

    A line break inside a quoted scalar folds to a space in YAML, so collapsing
    the run of whitespace a break introduces — and nothing else — keeps the
    value; a quoted URL keeps its interior spacing byte for byte.
    """
    out: list[str] = []
    quote: str | None = None
    pending = False
    for position, character in enumerate(text):
        if quote is not None:
            if character == "\n":
                out.append(" ")
                pending = True
            elif pending and character.isspace():
                continue
            else:
                pending = False
                out.append(character)
                if character == quote:
                    quote = None
            continue
        if character.isspace():
            pending = True
            continue
        if pending:
            out.append(" ")
            pending = False
        if character in "'\"" and _value_position(text, position):
            quote = character
        out.append(character)
    return "".join(out).strip()


def _split_flow(body: str) -> list[str]:
    """The top-level entries of a flow collection body, verbatim.

    A comma inside a quoted scalar or a nested collection is part of the entry.
    """
    entries: list[str] = []
    current: list[str] = []
    depth = 0
    quote: str | None = None
    for position, character in enumerate(body):
        if quote is not None:
            current.append(character)
            if character == quote:
                quote = None
            continue
        if character in "'\"" and _value_position(body, position):
            quote = character
        elif character in "[{":
            depth += 1
        elif character in "]}":
            depth -= 1
        elif character == "," and depth == 0:
            entries.append("".join(current))
            current = []
            continue
        current.append(character)
    entries.append("".join(current))
    return [entry.strip() for entry in entries if entry.strip()]


def _flow_entry(entry: str) -> tuple[str, str]:
    """``(key, value)`` of a flow mapping entry, the value verbatim."""
    depth = 0
    quote: str | None = None
    for position, character in enumerate(entry):
        if quote is not None:
            if character == quote:
                quote = None
            continue
        if character in "'\"" and _value_position(entry, position):
            quote = character
        elif character in "[{":
            depth += 1
        elif character in "]}":
            depth -= 1
        elif character == ":" and depth == 0:
            return entry[:position].strip(), entry[position + 1 :].strip()
    return entry.strip(), ""


def _block_collection(line: str, collection: FlowCollection) -> list[str]:
    """The block collection carrying the same entries, in the KB's shape.

    A block sequence puts its dashes at the indent of its key — measured over
    every block sequence of the three trees, that delta is always zero — and a
    block mapping puts its children two columns in.
    """
    indent = line[: len(line) - len(line.lstrip())]
    ending = lexical.line_ending(line)
    block = [f"{indent}{collection.key}:{ending}"]
    if collection.sequence:
        return block + [f"{indent}- {entry}{ending}" for entry in _split_flow(collection.body)]
    for entry in _split_flow(collection.body):
        name, value = _flow_entry(entry)
        block.append(f"{indent}  {name}:{' ' + value if value else ''}{ending}")
    return block


def flow_collections(text: str) -> list[FlowCollection]:
    """Every non-empty flow collection under a key the KB writes in block form.

    An *empty* collection is not returned: ``[]`` and ``{}`` are the shape the KB
    itself uses for "nothing", so they are already canonical.
    """
    found: list[FlowCollection] = []
    lines = lexical.lines(text)
    for index, line in enumerate(lines):
        match = _FLOW_VALUE.match(line)
        if match is None or match.group("key") not in BLOCK_COLLECTION_KEYS:
            continue
        span = _flow_span(lines, index, match.start("value"))
        if span is None:
            raise ValueError(f"unterminated flow collection at line {index + 1}: {line.strip()!r}")
        end, column = span
        opening = match.start("value")
        if end == index:
            body = lines[index][opening + 1 : column]
        else:
            body = "\n".join([lines[index][opening + 1 :], *lines[index + 1 : end], lines[end][:column]])
        flat = _one_line(body)
        if not flat or flat.startswith("#"):
            continue
        found.append(
            FlowCollection(index, end, match.group("key"), match.group("value").lstrip()[0] == "[", flat)
        )
    return found


def block_shape(text: str) -> str:
    """The document text with every block-collection key in the KB's shape."""
    found = flow_collections(text)
    if not found:
        return text
    lines = lexical.lines(text)
    for collection in reversed(found):
        lines[collection.line : collection.end + 1] = _block_collection(lines[collection.line], collection)
    return "".join(lines)


def shape_pass(tree: str) -> list[lexical.Edit]:
    """Write every block-collection key of a tree in the shape the KB keeps.

    Nothing is dropped: the entries are the ones the flow collection carried,
    verbatim and in the same order, and the pass re-parses the whole document and
    compares it with what it read, so a rewrite that changed anything else fails
    instead of landing.
    """
    edits: list[lexical.Edit] = []
    for path in sorted(_tree_root(tree).rglob("*.yaml")):
        if not path.is_file():
            continue
        original = lexical.read_text(path)
        if not flow_collections(original):
            continue
        after = block_shape(original)
        if yaml.safe_load(original) != yaml.safe_load(after):
            raise ValueError(f"{path}: the shape pass changed more than the collection shape")
        counts: Counter[str] = Counter(
            collection.key for collection in flow_collections(original)
        )
        changes = [
            f"{key}: {count} flow collection(s) -> block (the shape the KB keeps)"
            for key, count in sorted(counts.items())
        ]
        lexical.publish(path, after)
        edits.append(lexical.Edit(path, changes, after, original))
    return edits


# --------------------------------------------------------------------------- #
# Passes
# --------------------------------------------------------------------------- #


def status_pass(tree: str) -> list[lexical.Edit]:
    """The root ``status`` of the staged catalogues, as the KB keeps it.

    A staged *document* (the market catalogue, the magic catalogue) carries
    ``draft``: it is content a curator has not confirmed, and merging it into the
    published KB document is what publishes it. A staged *package* file carries
    what its KB family carries, which for items and hirelings is nothing at all.
    """
    edits: list[lexical.Edit] = []
    for path in _catalogue_files(tree):
        relative = path.relative_to(_tree_root(tree)).as_posix()
        original = lexical.read_text(path)
        document = yaml.safe_load(original) or {}
        if "status" not in document:
            continue
        is_document = relative in STAGED_DOCUMENTS
        if is_document and document["status"] == STAGED_STATUS:
            continue
        if not is_document:
            text, dropped = _drop_root_scalar(original, "status")
            if not dropped:
                continue
            change = "root status: dropped (the KB keeps no status on this family)"
        else:
            faces = [line for line in lexical.lines(original) if _own_key(line, "status", 0)]
            if not faces:
                continue
            text = original.replace(faces[0], lexical.replace_scalar(faces[0], "status", STAGED_STATUS), 1)
            change = f"root status: {document['status']!r} -> {STAGED_STATUS!r} (unconfirmed content)"
        after = text
        updated = yaml.safe_load(after) or {}
        expected = {**document, "status": STAGED_STATUS} if is_document else {
            key: value for key, value in document.items() if key != "status"
        }
        if updated != expected:
            raise ValueError(f"{path}: the status pass changed more than the envelope")
        lexical.publish(path, after)
        edits.append(lexical.Edit(path, [change], after, original))
    return edits


def _merge(report: Report, edits: Iterable[lexical.Edit]) -> None:
    """Add edits to a report, chaining the ones that touch the same file."""
    for edit in edits:
        previous = next((item for item in report.edits if item.path == edit.path), None)
        if previous is None:
            report.edits.append(edit)
            continue
        position = report.edits.index(previous)
        report.edits[position] = lexical.Edit(
            edit.path, previous.changes + edit.changes, edit.text, previous.original
        )


PASSES: tuple[str, ...] = ("status", "market", "items", "hirelings", "magic", "shape")


def market_edits(tree: str) -> list[lexical.Edit]:
    """The staged market catalogue of a tree, as one edit."""
    document = market_document(tree)
    current = lexical.read_text(document.path) if document.path.is_file() else ""
    if current == document.text or (current and yaml.safe_load(current) == yaml.safe_load(document.text)):
        return []
    lexical.publish(document.path, document.text)
    return [
        lexical.Edit(
            document.path,
            [f"{document.entries} market entries"],
            document.text,
            current,
        )
    ]


def run(passes: Iterable[str] | None = None) -> Report:
    """Run the passes in order: the market reads the facts the item pass retires."""
    wanted = list(passes) if passes else list(PASSES)
    for name in wanted:
        if name not in PASSES:
            raise ValueError(f"Unknown pass: {name!r}")
    report = Report()
    for name in PASSES:
        if name not in wanted:
            continue
        for tree in STAGING_TREES:
            if name == "status":
                _merge(report, status_pass(tree))
            elif name == "market":
                _merge(report, market_edits(tree))
            elif name == "items":
                _merge(report, _catalogue_pass(tree))
            elif name == "hirelings":
                from mordheim_knowledge import hireling_promotion

                _merge(report, hireling_promotion.hireling_edits(tree))
            elif name == "magic":
                from mordheim_knowledge import magic_promotion

                _merge(report, magic_promotion.magic_edits(tree))
            elif name == "shape":
                _merge(report, shape_pass(tree))
    return report


# --------------------------------------------------------------------------- #
# Promotion: the staged catalogues merged into the knowledge base
# --------------------------------------------------------------------------- #
#
# The passes above give the staged trees the *shape* of the knowledge base. The
# promotion is the second half: it reads that shape, decides what each record
# does when it meets the KB (the decisions of T04, as tables here) and merges it
# into a destination root. A destination is any directory that mirrors
# ``sources/knowledge``; its first run reads the KB as the base of every document
# it merges into, so a temporary root is a faithful "KB after the promotion",
# and the second run reads what the first wrote and therefore changes nothing.
#
# Two rules keep it honest:
#
# * **Nothing is written without being asked.** A preview computes the whole
#   promotion and writes nothing; writing needs an explicit destination, and
#   then each document is validated against the schema of its KB family and
#   formatted by the canonical formatter.
# * **A collision nobody declared stops the promotion.** The tables below are
#   the *only* reasons a staged id may meet an existing KB id; anything else
#   would overwrite a published record, so the promotion refuses it instead.

#: The knowledge base document a promoted record of each item kind joins. The KB
#: keeps one file per kind, which is what makes the destination of a new record
#: mechanical rather than another editorial decision (``miscellaneous.yaml`` is
#: the KB's own legacy bucket and is never a promotion target).
ITEM_FILES: dict[str, str] = {
    "armour": "catalog/items/armour.yaml",
    "close-combat-weapon": "catalog/items/weapons-close-combat.yaml",
    "ranged-weapon": "catalog/items/weapons-ranged.yaml",
    "shield-or-defence": "catalog/items/shields-and-defences.yaml",
    "combat-equipment": "catalog/items/combat-equipment.yaml",
    "material-or-upgrade": "catalog/items/materials-and-upgrades.yaml",
    "out-of-scope": "catalog/items/out-of-scope.yaml",
    "trollheim-equipment": "catalog/items/trollheim.yaml",
}

#: Staged item id -> KB item id. The KB entry survives, the staged row is not
#: published, its provenance joins the KB record and the band lists re-point to
#: the KB id (T04 §A.7 and the at-promotion table of the merge notes).
ITEM_REDIRECTS: dict[str, str] = {
    "dueling_pistol": "duelling_pistol",
    "dragon_cloak": "sea_dragon_cloak",
    "elven_bow": "elf_bow",
    "rope_and_hook": "rope_hook",
    "throwing_axe_sar": "throwing_axe",
    "throwing_knife": "throwing_knives",
    "wardog": "warhound",
}

#: Staged item id -> KB item id: one printed item the KB already holds, so the KB
#: record survives and the staged definition is dropped with its provenance
#: folded in. Kept apart from the redirects because both spell the same item,
#: while a redirect resolves a *name* difference.
ITEM_MERGES: dict[str, str] = {
    "horsemans_hammer": "horsemans_hammer",
    "hunting_arrows": "hunting_arrows",
}

#: Staged items the KB keeps under a related but different printed record: same
#: broad concept, different rules, so both are published (T04 §3.1).
ITEM_VARIANTS: tuple[str, ...] = (
    "repeater_pistol_moh",  # 8" + Too Much Tinkering against the KB 6" pistol
    "shield_of_sigmar",  # 6+ save against the KB trading-post shield
    "society_familiar",  # companion bestiary against the KB ritual familiar
    "warplock_pistol",  # MiM Range 6"/S4 against the KB Warp Pistol Range 8"/S5
    "wolf_cloak",  # no printed effect against the KB Middenheim hunt cloak
)

#: A staged market entry whose KB-convention id (`campaign.trading-post.<item
#: id>`) is already claimed by the entry of a *different* item. The variant
#: entry qualifies its id with the source, which is the shape the KB itself uses
#: for a second entry of one item (`campaign.trading-post.pike.tileans`,
#: `campaign.trading-post.ostlander-double-barrelled-pistol`); no published
#: record is renamed and no price moves.
MARKET_ENTRY_QUALIFIERS: dict[str, str] = {
    # The KB entry `campaign.trading-post.warplock-pistol` belongs to `warp_pistol`
    # ("Warp Pistol", Range 8", S5, rare 11), while the staged `warplock_pistol`
    # is the Mutiny in Marienburg printing (Range 6", S4, 35 gc, common to the
    # Metal Mongers list). T05 finding: 26 KB entry ids already break the
    # convention, so the qualifier — not a rename of the KB record — is the
    # smaller change.
    "warplock_pistol": "mim",
}

#: ``staged item id -> (action, KB item id)``: every declared collision, in one
#: table, so the refusal list and the preview read the same decision.
ITEM_DECISIONS: dict[str, tuple[str, str]] = {
    **{key: ("redirect", value) for key, value in ITEM_REDIRECTS.items()},
    **{key: ("merge", value) for key, value in ITEM_MERGES.items()},
}

# --------------------------------------------------------------------------- #
# Band packages: the same facts in the KB's own tree
# --------------------------------------------------------------------------- #

#: Where a band package lives, on both sides of the promotion.
BAND_ROOT = "bands/mordheim"

#: The four documents of a band package, in the order the contract reads them.
BAND_DOCUMENTS: tuple[str, ...] = (
    "band.yaml",
    "profiles.yaml",
    "equipment-access.yaml",
    "special-rules.yaml",
)

#: Staged prose that names a staging tree. Nothing but ``sources/knowledge`` is
#: read in production, so a promoted annotation that pointed at ``sources/2A`` or
#: ``sources/2B`` would leave a reference into staging on the KB side — exactly
#: what the isolation tests exist to catch, and ``promote`` refuses a document
#: that would carry one. Every string here is an editorial annotation the
#: ingestion wrote (never printed source text) and its replacement names the KB
#: document the same facts live in after promotion. The staged trees keep their
#: own wording verbatim; only the promoted copy is reworded.
STAGING_NOTE_REWRITES: dict[str, str] = {
    "sources/2A/catalog/magic-2a.yaml": "catalog/campaign/magic.yaml",
    "sources/2B/catalog/magic-2b.yaml": "catalog/campaign/magic.yaml",
    "sources/2B/catalog/items/savage-orc-and-skryre-gear.yaml": "catalog/items/weapons-ranged.yaml",
    "sources/2B/catalog/items/corpse-liquor.yaml": "catalog/items/combat-equipment.yaml",
    "sources/2A/discrepancy-verdicts.md": "the 2A discrepancy verdicts of the staging tree",
}

#: ``(band, rule id) -> scope``: the rule-level scope the promoted copy carries
#: where the staged mark disagrees with the rule's own effects. The KB loader
#: *derives* a rule's scope from its effects (``YES`` if any effect is ``YES``,
#: otherwise ``LATER`` if any is ``LATER``, otherwise ``NO``) and refuses a
#: document where the two disagree, so the corrected value is not an editorial
#: choice: it is the one the effects already spell out, and the affected rule has
#: a legal copy in another band carrying exactly that value (for
#: ``band--hard-to-kill``: ``black-dwarfs`` at ``YES``, ``fen-guard-mim`` at
#: ``LATER``). Everything else of the rule — its text, its ``implemented`` mark,
#: its grant, its effects, their bindings, their scopes and their reasons — is
#: copied verbatim, and the staged tree keeps the staged mark.
BAND_SCOPE_REPAIRS: dict[tuple[str, str], str] = {
    ("dwarf-slayer-cult-web", "band--hard-to-kill"): "LATER",
    ("dwarf-slayer-cult-web", "band--hard-head"): "LATER",
    ("house-guard-sc", "band--dueling-pride"): "LATER",
    ("house-guard-sc", "pikemen--pikewall"): "LATER",
    ("lords-of-the-marsh-mim", "young-nobles--spiked-tail"): "LATER",
    ("lords-of-the-marsh-mim", "fimir-warriors--spiked-tail"): "LATER",
    ("underworld-alliance-mim", "goblin-bully--one-upmanship"): "LATER",
    ("watchmen-mim", "private-sleuth--scryer"): "LATER",
}

MARKET_DOCUMENT = "catalog/campaign/trading-post.yaml"
MAGIC_DOCUMENT = "catalog/campaign/magic.yaml"
CAMPAIGN_DOCUMENT = "catalog/campaign/hired-swords-and-dramatis.yaml"

#: ``KB family -> the grade-2b document the promoted profiles join``.
HIRELING_DOCUMENTS: dict[str, str] = {
    "hired-swords": "catalog/hirelings/hired-swords/grade-2b.yaml",
    "dramatis-personae": "catalog/hirelings/dramatis-personae/grade-2b.yaml",
}
HIRELING_CATALOGUES: dict[str, str] = {
    "hired-swords": "hirelings-hired-swords",
    "dramatis-personae": "hirelings-dramatis-personae",
}

#: The schema every document a promotion writes answers to.
PROMOTED_SCHEMAS: dict[str, str] = {
    MARKET_DOCUMENT: "campaign-trading-post.yaml.schema.json",
    MAGIC_DOCUMENT: "campaign-magic.yaml.schema.json",
    CAMPAIGN_DOCUMENT: "campaign-hired-swords-and-dramatis.yaml.schema.json",
    **{value: "catalog-items.yaml.schema.json" for value in ITEM_FILES.values()},
    **{value: "hireling-profile-hired-sword.yaml.schema.json" for value in (HIRELING_DOCUMENTS["hired-swords"],)},
    **{value: "hireling-profile-dramatis-personae.yaml.schema.json" for value in (HIRELING_DOCUMENTS["dramatis-personae"],)},
}

#: Staged documents the promotion never publishes, with the reason. The band
#: packages are not here: each one is promoted whole, and its item references
#: follow ``ITEM_DECISIONS``.
PROMOTED_EXCLUSIONS: dict[str, str] = {
    "catalog/items/missing-item-stubs.yaml": (
        "an empty helper of the ingestion flow; its stubs are already resolved in their "
        "definitive catalogues (staging_contract_audit.NOT_PROMOTED)"
    ),
}

#: The staged families of the promotion preview, in reporting order.
PROMOTION_FAMILIES: tuple[str, ...] = ("items", "market", "magic", "hirelings", "bands")

ACTION_NEW = "new"
ACTION_MERGE = "merge"
ACTION_VARIANT = "variant"
ACTION_REDIRECT = "redirect"
ACTION_EXCLUDE = "exclude"
ACTION_CONFLICT = "conflict"
ACTION_PRESENT = "already-promoted"

STAGED_KEYS: tuple[str, ...] = (
    "items",
    "market",
    "lores",
    "assignments",
    "hired_swords",
    "dramatis",
    "campaign_hired",
    "campaign_dramatis",
)


class PromotionRefused(Exception):
    """The promotion met a collision the editorial tables do not declare."""


@dataclass(frozen=True)
class Action:
    """What the promotion does with one staged record."""

    family: str
    source_id: str
    action: str
    destination: str
    detail: str = ""

    def as_dict(self) -> dict[str, str]:
        return {
            "family": self.family,
            "source_id": self.source_id,
            "action": self.action,
            "destination": self.destination,
            "detail": self.detail,
        }


@dataclass
class Promotion:
    """A promotion: what every record does, and the documents it would write."""

    actions: list[Action] = field(default_factory=list)
    edits: list[lexical.Edit] = field(default_factory=list)
    destination: str = "sources/knowledge"

    @property
    def conflicts(self) -> list[Action]:
        return [action for action in self.actions if action.action == ACTION_CONFLICT]

    def counts(self) -> dict[str, int]:
        counted = Counter(action.action for action in self.actions)
        return {name: counted[name] for name in sorted(counted)}

    def families(self) -> dict[str, dict[str, int]]:
        """How each staged family fares, which is what a review reads first."""
        found: dict[str, dict[str, int]] = {}
        for action in self.actions:
            found.setdefault(action.family, Counter())[action.action] += 1
        return {family: dict(found[family]) for family in sorted(found)}

    def as_dict(self) -> dict:
        return {
            "destination": self.destination,
            "counts": self.counts(),
            "families": self.families(),
            "files": [edit.path.as_posix() for edit in self.edits],
            "actions": [action.as_dict() for action in self.actions],
        }

    def summarise(self) -> str:
        lines = [f"destination: {self.destination}"]
        for family, counted in self.families().items():
            detail = ", ".join(f"{name} {count}" for name, count in sorted(counted.items()))
            lines.append(f"{family}: {detail}")
        for action in self.actions:
            lines.append(f"    [{action.action}] {action.family}/{action.source_id} -> {action.destination} {action.detail}")
        for edit in self.edits:
            lines.append(f"would write {edit.path.as_posix()} ({len(edit.changes)} change(s))")
        return "\n".join(lines)

    def write(self) -> list[Path]:
        """Write the destination documents, refusing an undeclared collision."""
        if self.conflicts:
            raise PromotionRefused(_refusal(self.conflicts))
        for edit in self.edits:
            edit.write()
        return [edit.path for edit in self.edits]


def _refusal(conflicts: list[Action]) -> str:
    detail = "; ".join(f"{action.family}/{action.source_id} ({action.detail})" for action in conflicts)
    return (
        "the promotion refuses undeclared collisions with the knowledge base: "
        f"{detail}. Declare the decision in the tables of staging_promotion "
        "(ITEM_REDIRECTS, ITEM_MERGES, ITEM_VARIANTS, HIRELING_REDIRECTS) instead."
    )


_STAGED: dict[str, dict[str, list[dict]]] = {}


def staged_catalogues(tree: str) -> dict[str, list[dict]]:
    """The staged records of a tree, already read in their promotion shape.

    Read through the lexical overlay, so a promotion preview sees the staged
    trees as their normalisation leaves them without writing that normalisation
    first. The band packages are not read: they keep their own promotion step.
    """
    if tree in _STAGED:
        return _STAGED[tree]
    from mordheim_knowledge import hireling_promotion
    from mordheim_knowledge import magic_promotion

    found: dict[str, list[dict]] = {key: [] for key in STAGED_KEYS}
    for path in _item_catalogues(tree):
        found["items"].extend(_items(path))
    market = yaml.safe_load(lexical.read_text(_document_path(tree, MARKET_DOCUMENTS[tree]))) or {}
    found["market"].extend(market.get("items") or [])
    relative = magic_promotion.MAGIC_DOCUMENTS.get(tree)
    if relative is not None:
        magic = yaml.safe_load(lexical.read_text(_document_path(tree, relative))) or {}
        found["lores"].extend(magic.get("lores") or [])
        found["assignments"].extend((magic.get("lore_assignments") or {}).get("rows") or [])
    if tree in hireling_promotion.CAMPAIGN_DOCUMENTS:
        for profile in hireling_promotion._staged_profiles(tree):
            found["hired_swords"].append(hireling_promotion.promoted_hireling_profile(profile))
        dramatis = yaml.safe_load(
            lexical.read_text(_document_path(tree, hireling_promotion.DRAMATIS_DOCUMENTS[tree]))
        ) or {}
        found["dramatis"].extend(dramatis.get("profiles") or [])
        campaign = yaml.safe_load(
            lexical.read_text(_document_path(tree, hireling_promotion.CAMPAIGN_DOCUMENTS[tree]))
        ) or {}
        found["campaign_hired"].extend(campaign.get("hired_swords") or [])
        found["campaign_dramatis"].extend(campaign.get("dramatis_personae") or [])
    # One choke point for the editorial annotations that name a staging tree:
    # every family reads through here, so a promoted record can never carry one.
    found = {key: [promoted_record(record) for record in records] for key, records in found.items()}
    _STAGED[tree] = found
    return found


def clear_staged_cache() -> None:
    """Forget the staged view, so a changed tree is read again."""
    _STAGED.clear()


@contextmanager
def promotion_view() -> Iterator[None]:
    """The staged trees as their normalisation leaves them, written nowhere.

    The passes publish their result to the lexical overlay rather than the disk,
    so running them is what makes the staged documents readable in their
    promotion shape. The overlay is restored afterwards: a preview never changes
    what the rest of the process reads, and never touches a file.
    """
    saved = dict(lexical._OVERLAY)
    try:
        run()
        yield
    finally:
        lexical._OVERLAY.clear()
        lexical._OVERLAY.update(saved)


# --------------------------------------------------------------------------- #
# Destination documents
# --------------------------------------------------------------------------- #


def _dump(document: Any) -> str:
    return yaml.safe_dump(
        document, allow_unicode=True, sort_keys=False, default_flow_style=False, width=100
    )


def _base_text(root: Path, relative: str) -> str:
    """The text to merge into: the destination's copy, or the knowledge base's.

    A destination starts empty, so its first promotion reads the KB as the base
    of every document; its second reads what the first wrote, which is what
    makes the second pass empty.
    """
    path = Path(root) / relative
    if path.is_file():
        return lexical.read_text(path)
    kb = CHECKOUT / KB_ROOT / relative
    if kb.is_file():
        return lexical.read_text(kb)
    return ""


def _promoted_schema(relative: str) -> str | None:
    """The contract document a promoted document answers to, or ``None``.

    A band document is named by its own file, and the band contract carries one
    schema per document name; the item catalogues share one shape, whether the
    record joins an existing KB file or the KB's own surviving bucket.
    """
    if relative.startswith(f"{BAND_ROOT}/"):
        return f"{Path(relative).name}.schema.json"
    if relative.startswith("catalog/items/"):
        return "catalog-items.yaml.schema.json"
    return PROMOTED_SCHEMAS.get(relative)


def _record_lines(record: dict, ending: str, indent: int = 0) -> list[str]:
    """One record as a block list item, at the indent of its list key."""
    body = _dump(record).splitlines()
    pad = " " * indent
    child = " " * (indent + 2)
    block = [f"{pad}- {body[0]}"]
    block += [f"{child}{line}" if line.strip() else "" for line in body[1:]]
    return [line + ending for line in block]


def _source_ref_lines(ref: dict, ending: str) -> list[str]:
    """One provenance entry as the KB writes it, two columns under the record."""
    pad = " " * RECORD_INDENT
    body = _dump(ref).splitlines()
    block = [f"{pad}- {body[0]}"]
    block += [f"{pad}  {line}" if line.strip() else "" for line in body[1:]]
    return [line + ending for line in block]


def _append_records(text: str, key: str, records: list[dict], indent: int = 0) -> str:
    """Add records at the end of the list a document keeps under ``key``."""
    lines = lexical.lines(text)
    ending = lexical.line_ending(lines[0]) if lines else "\n"
    for index, line in enumerate(lines):
        if _own_key(line, key, indent):
            end = _block_end(lines, index, indent)
            lines[end:end] = [
                line for record in records for line in _record_lines(record, ending, indent)
            ]
            return "".join(lines)
    raise ValueError(f"the document keeps no {key!r} list at indent {indent}")


def _fold_source_refs(text: str, record_id: str, refs: list[dict]) -> str:
    """Add provenance entries to one record, after the ones it already carries."""
    lines = lexical.lines(text)
    ending = lexical.line_ending(lines[0]) if lines else "\n"
    for start, end in _records(lines):
        if _record_id(lines[start]) != record_id:
            continue
        record = lines[start:end]
        for index, line in enumerate(record):
            if _own_key(line, "source_refs", RECORD_INDENT):
                stop = _block_end(record, index, RECORD_INDENT)
                record[stop:stop] = [line for ref in refs for line in _source_ref_lines(ref, ending)]
                lines[start:end] = record
                return "".join(lines)
        # The record keeps no provenance yet: the key joins it, before the
        # `combat_status`/`mechanic_id` envelope the item contract ends with.
        insert = next(
            (
                index
                for index, line in enumerate(record)
                if _own_key(line, "combat_status", RECORD_INDENT)
            ),
            len(record),
        )
        block = [f"{' ' * RECORD_INDENT}source_refs:{ending}"]
        block += [line for ref in refs for line in _source_ref_lines(ref, ending)]
        record[insert:insert] = block
        lines[start:end] = record
        return "".join(lines)
    raise ValueError(f"no record {record_id!r} to fold provenance into")


@dataclass
class _Target:
    """One destination document: its base text and what the promotion adds."""

    root: Path
    relative: str
    text: str
    appended: dict[str, list[dict]] = field(default_factory=dict)
    folded: dict[str, list[dict]] = field(default_factory=dict)

    def append(self, key: str, records: Iterable[dict], indent: int = 0) -> None:
        self.appended.setdefault(f"{indent}:{key}", []).extend(records)

    def fold(self, record_id: str, refs: Iterable[dict]) -> None:
        self.folded.setdefault(record_id, []).extend(refs)

    def result(self) -> str:
        text = self.text
        for record_id, refs in self.folded.items():
            text = _fold_source_refs(text, record_id, refs)
        for pointer, records in self.appended.items():
            indent, _, key = pointer.partition(":")
            text = _append_records(text, key, records, int(indent))
        return text


def _target(targets: dict[str, _Target], root: Path, relative: str) -> _Target:
    if relative not in targets:
        targets[relative] = _Target(root, relative, _base_text(root, relative))
    return targets[relative]


def _refs_of(record: dict) -> list[dict]:
    return [ref for ref in record.get("source_refs") or [] if isinstance(ref, dict)]


def _new_refs(existing: list[dict], candidates: list[dict]) -> list[dict]:
    """The provenance entries a record does not already carry (idempotence)."""
    known = {_dump(ref) for ref in existing}
    return [ref for ref in candidates if _dump(ref) not in known]


# --------------------------------------------------------------------------- #
# The staged families, one by one
# --------------------------------------------------------------------------- #


def _item_documents(root: Path) -> list[str]:
    """Every item document the destination and the KB keep, by relative path."""
    relatives = {
        path.relative_to(CHECKOUT / KB_ROOT).as_posix()
        for path in sorted((CHECKOUT / KB_ROOT / "catalog" / "items").glob("*.yaml"))
    }
    root_items = Path(root) / "catalog" / "items"
    if root_items.is_dir():
        relatives |= {f"catalog/items/{path.name}" for path in sorted(root_items.glob("*.yaml"))}
    return sorted(relatives)


def _item_index(root: Path) -> dict[str, tuple[str, dict]]:
    """``item id -> (document, record)`` of every item already published."""
    found: dict[str, tuple[str, dict]] = {}
    for relative in _item_documents(root):
        document = yaml.safe_load(_base_text(root, relative)) or {}
        for item in document.get("items") or []:
            found.setdefault(str(item["id"]), (relative, item))
    return found


def _evaluate(
    record: dict, index: dict[str, tuple[str, dict]], decisions: dict[str, tuple[str, str]]
) -> tuple[str, str, str, list[dict]]:
    """``(action, KB id, document, refs to fold)`` of one staged record.

    The declared tables decide; everything else is either a new record or a
    collision no table declares, and the caller refuses the latter.
    """
    source_id = str(record["id"])
    decision = decisions.get(source_id)
    if decision is not None:
        action, target_id = decision
        existing = index.get(target_id)
        if existing is None:
            return ACTION_CONFLICT, target_id, "", []
        relative, target = existing
        return action, target_id, relative, _new_refs(_refs_of(target), _refs_of(record))
    existing = index.get(source_id)
    if existing is None:
        return ACTION_NEW, source_id, "", []
    relative, published = existing
    if published == record:
        return ACTION_PRESENT, source_id, relative, []
    return ACTION_CONFLICT, source_id, relative, []


def _promote_items(
    root: Path,
    staged: dict[str, list[dict]],
    actions: list[Action],
    targets: dict[str, _Target],
    index: dict[str, tuple[str, dict]],
) -> None:
    for item in staged["items"]:
        record = promoted_item(item)
        source_id = str(record["id"])
        action, target_id, relative, refs = _evaluate(record, index, ITEM_DECISIONS)
        if action == ACTION_CONFLICT:
            if relative:
                detail = f"the KB already keeps {target_id!r} with different content"
            else:
                detail = f"the KB keeps no item {target_id!r} to fold into"
            actions.append(Action("items", source_id, action, relative or target_id, detail))
            continue
        if action in (ACTION_MERGE, ACTION_REDIRECT):
            if refs:
                _target(targets, root, relative).fold(target_id, refs)
            actions.append(
                Action(
                    "items",
                    source_id,
                    action,
                    relative,
                    f"KB {target_id} survives; {len(refs)} source_ref(s) folded",
                )
            )
            continue
        if action == ACTION_PRESENT:
            actions.append(Action("items", source_id, action, relative))
            continue
        kind = str(record.get("kind") or "")
        destination = ITEM_FILES.get(kind)
        if destination is None:
            actions.append(Action("items", source_id, ACTION_CONFLICT, kind, "no KB file for the kind"))
            continue
        if source_id in ITEM_VARIANTS:
            action = ACTION_VARIANT
        _target(targets, root, destination).append("items", [record])
        index[source_id] = (destination, record)
        actions.append(Action("items", source_id, action, destination, f"kind {kind}"))


def _market_index(root: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    """``(by entry id, by item id)`` of the market catalogue already published."""
    document = yaml.safe_load(_base_text(root, MARKET_DOCUMENT)) or {}
    entries = list(document.get("items") or [])
    return (
        {str(entry["id"]): entry for entry in entries},
        {str(entry["item_id"]): entry for entry in entries if entry.get("item_id")},
    )


def _promote_market(
    root: Path, staged: dict[str, list[dict]], actions: list[Action], targets: dict[str, _Target]
) -> None:
    by_id, by_item = _market_index(root)
    for entry in staged["market"]:
        entry_id = str(entry["id"])
        item_id = str(entry["item_id"])
        sourced = ""
        qualifier = MARKET_ENTRY_QUALIFIERS.get(item_id)
        if qualifier is not None and entry_id in by_id:
            entry = {**entry, "id": f"{entry_id}-{qualifier}"}
            entry_id = str(entry["id"])
            sourced = f" (variant entry, the id of the KB record is taken)"
        decision = ITEM_DECISIONS.get(item_id)
        if decision is not None:
            action, target_item = decision
            target = by_item.get(target_item)
            if target is None:
                actions.append(
                    Action(
                        "market",
                        entry_id,
                        action,
                        MARKET_DOCUMENT,
                        f"the KB keeps no market entry for {target_item}; the band-side price stays band-side",
                    )
                )
                continue
            refs = _new_refs(_refs_of(target), _refs_of(entry))
            if refs:
                _target(targets, root, MARKET_DOCUMENT).fold(str(target["id"]), refs)
            actions.append(
                Action(
                    "market",
                    entry_id,
                    action,
                    MARKET_DOCUMENT,
                    f"KB entry {target['id']} survives; {len(refs)} source_ref(s) folded",
                )
            )
            continue
        published = by_id.get(entry_id)
        if published is not None:
            if published == entry:
                actions.append(Action("market", entry_id, ACTION_PRESENT, MARKET_DOCUMENT))
            else:
                actions.append(
                    Action(
                        "market",
                        entry_id,
                        ACTION_CONFLICT,
                        MARKET_DOCUMENT,
                        "the KB already publishes this entry with different content",
                    )
                )
            continue
        _target(targets, root, MARKET_DOCUMENT).append("items", [entry])
        by_id[entry_id] = entry
        by_item[item_id] = entry
        actions.append(Action("market", entry_id, ACTION_NEW, MARKET_DOCUMENT, f"item {item_id}{sourced}"))


def _magic_index(root: Path) -> tuple[dict[str, dict], set[tuple]]:
    """``(lores by id, assignment rows)`` of the magic document already published."""
    document = yaml.safe_load(_base_text(root, MAGIC_DOCUMENT)) or {}
    lores = {str(lore["id"]): lore for lore in document.get("lores") or []}
    rows = {
        (row.get("wizard"), row.get("profile_id"), row.get("band"), row.get("lore"))
        for row in (document.get("lore_assignments") or {}).get("rows") or []
    }
    return lores, rows


def _promote_magic(
    root: Path, staged: dict[str, list[dict]], actions: list[Action], targets: dict[str, _Target]
) -> None:
    lores, rows = _magic_index(root)
    for lore in staged["lores"]:
        lore_id = str(lore["id"])
        published = lores.get(lore_id)
        if published is not None:
            if published == lore:
                actions.append(Action("magic", lore_id, ACTION_PRESENT, MAGIC_DOCUMENT))
            else:
                actions.append(
                    Action(
                        "magic",
                        lore_id,
                        ACTION_CONFLICT,
                        MAGIC_DOCUMENT,
                        "the KB already keeps this lore id with different text",
                    )
                )
            continue
        _target(targets, root, MAGIC_DOCUMENT).append("lores", [lore])
        lores[lore_id] = lore
        action = ACTION_NEW
        actions.append(Action("magic", lore_id, action, MAGIC_DOCUMENT, f"{len(lore.get('spells') or [])} spell(s)"))
    changes: list[dict] = []
    for row in staged["assignments"]:
        key = (row.get("wizard"), row.get("profile_id"), row.get("band"), row.get("lore"))
        if key in rows:
            actions.append(Action("magic", str(row.get("wizard")), ACTION_PRESENT, MAGIC_DOCUMENT, f"row {row.get('lore')}"))
            continue
        changes.append(row)
        rows.add(key)
        actions.append(Action("magic", str(row.get("wizard")), ACTION_NEW, MAGIC_DOCUMENT, f"row {row.get('lore')}"))
    if changes:
        _target(targets, root, MAGIC_DOCUMENT).append("rows", changes, 2)


def _hireling_index(root: Path) -> tuple[dict[str, dict], dict[str, dict]]:
    """``(profiles by id, campaign entries by profile id)`` already published."""
    profiles: dict[str, dict] = {}
    for family, relative in HIRELING_DOCUMENTS.items():
        document = yaml.safe_load(_base_text(root, relative)) or {}
        for profile in document.get("profiles") or []:
            profiles.setdefault(str(profile["id"]), profile)
    campaign = yaml.safe_load(_base_text(root, CAMPAIGN_DOCUMENT)) or {}
    entries = list(campaign.get("hired_swords") or []) + list(campaign.get("dramatis_personae") or [])
    return profiles, {str(entry["profile_id"]): entry for entry in entries if entry.get("profile_id")}


def _hireling_family(profile_id: str) -> str:
    return "dramatis-personae" if ".dramatis." in profile_id else "hired-swords"


def _redirected_entry(entry: dict, rename: dict[str, str]) -> tuple[str, dict]:
    """A campaign entry with the id its redirected profile carries."""
    profile_id = str(entry["profile_id"])
    target = rename.get(profile_id)
    if target is None:
        return str(entry["id"]), entry
    from mordheim_knowledge import hireling_promotion

    renamed = hireling_promotion._renamed(entry, profile_id, target)
    slug = target.split(".", 2)[2]
    family = "dramatis" if _hireling_family(target) == "dramatis-personae" else "hired-sword"
    renamed["id"] = f"campaign.hireling.{family}.{slug}"
    return str(renamed["id"]), renamed


def _promote_hirelings(
    root: Path, staged: dict[str, list[dict]], actions: list[Action], targets: dict[str, _Target]
) -> None:
    from mordheim_knowledge import hireling_promotion

    rename = hireling_promotion.HIRELING_REDIRECTS
    profiles, _ = _hireling_index(root)
    for record in staged["hired_swords"] + staged["dramatis"]:
        profile_id = str(record["id"])
        published = profiles.get(profile_id)
        if published is not None:
            action = ACTION_PRESENT if published == record else ACTION_CONFLICT
            detail = "" if action == ACTION_PRESENT else "the KB already keeps this profile id"
            actions.append(Action("hirelings", profile_id, action, HIRELING_DOCUMENTS[_hireling_family(profile_id)], detail))
            continue
        action = ACTION_REDIRECT if profile_id in set(rename.values()) else ACTION_NEW
        destination = HIRELING_DOCUMENTS[_hireling_family(profile_id)]
        target = _target(targets, root, destination)
        if target.text:
            target.append("profiles", [record])
        else:
            target.text = _dump(
                {
                    "schema_version": 1,
                    "ruleset": "mordheim",
                    "catalog": HIRELING_CATALOGUES[_hireling_family(profile_id)],
                    "grade": record.get("grade") or "2b",
                    "profiles": [record],
                }
            )
        profiles[profile_id] = record
        detail = "-miracle-workers redirect" if action == ACTION_REDIRECT else ""
        actions.append(Action("hirelings", profile_id, action, destination, detail))
    campaign = yaml.safe_load(_base_text(root, CAMPAIGN_DOCUMENT)) or {}
    published_ids = {
        str(entry["id"])
        for entry in (campaign.get("hired_swords") or []) + (campaign.get("dramatis_personae") or [])
    }
    for entry in staged["campaign_hired"] + staged["campaign_dramatis"]:
        entry_id, record = _redirected_entry(entry, rename)
        if entry_id in published_ids:
            actions.append(Action("hirelings", entry_id, ACTION_PRESENT, CAMPAIGN_DOCUMENT, "campaign entry"))
            continue
        key = "hired_swords" if ".hired-sword." in entry_id else "dramatis_personae"
        _target(targets, root, CAMPAIGN_DOCUMENT).append(key, [record])
        published_ids.add(entry_id)
        action = ACTION_REDIRECT if entry_id != str(entry["id"]) else ACTION_NEW
        actions.append(Action("hirelings", entry_id, action, CAMPAIGN_DOCUMENT, f"campaign entry into {key}"))


# --------------------------------------------------------------------------- #
# Band packages: promotion is a copy with its references resolved
# --------------------------------------------------------------------------- #

_ITEM_REFERENCE = re.compile(r"(item_id:\s*)([A-Za-z0-9_.\-]+)")
_STAGING_REFERENCE = re.compile(r"sources/2[AB]")
#: The ``scope`` of a rule's own ``runtime`` block: four spaces in, never a
#: list item (an effect's scope sits two spaces deeper, under ``effects:``).
_RULE_SCOPE = re.compile(r"^(?P<pad> {4})scope:(?P<gap>\s+)(?P<quote>['\"]?)(?P<scope>YES|NO|LATER)(?P=quote)\s*$")


def _completed_trait_bindings(text: str) -> str:
    """Write the value of a trait binding the staged rule left implicit.

    Every one of the KB's trait bindings carries ``parameters.value`` explicitly
    (170 of 170 before this promotion), the value the trait registry types, and
    the compiler reads it with no default: a grant that omits it hands the
    compiler ``None`` and the structural verification stops with a ``TypeError``
    instead of reporting. Six staged bindings omit it (``trait.concussion-immune``
    three times, ``trait.poison-immune`` twice, ``trait.frenzy`` once), and every
    other occurrence of those traits in the KB carries ``true``, which is also
    the only reading of a rule that *grants* the trait. The staged rule keeps its
    own shape.
    """
    lines = lexical.lines(text)
    inserts: list[tuple[int, int]] = []
    index = 0
    while index < len(lines):
        head = _key_of(lines[index])
        # A `binding:` that carries a nested mapping; `binding: null` is skipped.
        if head is None or head[0] != "binding" or head[2] or lines[index].partition(":")[2].strip():
            index += 1
            continue
        indent = head[1]
        end = index + 1
        while end < len(lines) and (not lines[end].strip() or _indent_of(lines[end]) > indent):
            end += 1
        children: dict[str, int] = {}
        for position, line in enumerate(lines[index + 1 : end]):
            found = _key_of(line)
            if found is not None and found[1] == indent + 2 and not found[2]:
                children.setdefault(found[0], position)
        kind = children.get("kind")
        if kind is None or "parameters" in children:
            index = end
            continue
        if lines[index + 1 + kind].partition(":")[2].strip().strip("'\"") != "trait":
            index = end
            continue
        inserts.append((index + 1 + children.get("id", kind) + 1, indent + 2))
        index = end
    if not inserts:
        return text
    ending = lexical.line_ending(lines[0]) if lines else "\n"
    for position, child in sorted(inserts, reverse=True):
        lines[position:position] = [
            f"{' ' * child}parameters:{ending}",
            f"{' ' * (child + 2)}value: true{ending}",
        ]
    return "".join(lines)


def _repaired_runtime_scopes(text: str, band: str) -> str:
    """The declared rule-level scope corrections of one band document."""
    if not BAND_SCOPE_REPAIRS:
        return text
    lines = lexical.lines(text)
    rule = ""
    for index, line in enumerate(lines):
        head = _key_of(line)
        if head is not None and head[0] == "id" and head[1] == 0 and head[2]:
            rule = line.partition(":")[2].strip()
            continue
        match = _RULE_SCOPE.match(line)
        if match is None:
            continue
        wanted = BAND_SCOPE_REPAIRS.get((band, rule))
        if wanted is None or match.group("scope") == wanted:
            continue
        lines[index] = f"{match.group('pad')}scope:{match.group('gap')}{wanted}{lexical.line_ending(line)}"
    return "".join(lines)


def _staging_path_pattern(path: str) -> re.Pattern[str]:
    """The path, tolerating the line wrap a folded scalar may put inside it."""
    return re.compile(r"/\s*".join(re.escape(part) for part in path.split("/")))


def promoted_annotation(text: str) -> str:
    """One editorial annotation with its staging path named as the KB document."""
    for staging, published in STAGING_NOTE_REWRITES.items():
        text = _staging_path_pattern(staging).sub(published, text)
    return text


def promoted_record(node: Any) -> Any:
    """A staged record with the declared annotations re-pointed; keys untouched."""
    if isinstance(node, str):
        return promoted_annotation(node)
    if isinstance(node, dict):
        return {key: promoted_record(value) for key, value in node.items()}
    if isinstance(node, list):
        return [promoted_record(value) for value in node]
    return node


def promoted_band_document(text: str, band: str) -> str:
    """A staged band document as the knowledge base reads it.

    Three declared transforms and nothing else: every ``item_id`` follows the
    identity decisions of T04, an annotation that named a staging tree names the
    KB document holding the same facts instead, and a rule-level scope the
    loader derives differently from its effects is corrected to the value those
    effects spell out. The band's own prose, its other ``runtime`` marks, its
    band-side prices, notes and provenance are copied verbatim.
    """

    def resolve(match: re.Match[str]) -> str:
        key = match.group(2)
        decision = ITEM_DECISIONS.get(key)
        return match.group(1) + (decision[1] if decision is not None else key)

    text = promoted_annotation(_ITEM_REFERENCE.sub(resolve, text))
    text = _repaired_runtime_scopes(text, band)
    return _completed_trait_bindings(text)


def _same_document(left: str, right: str) -> bool:
    """Whether two texts carry the same document; the shape of either is not content."""
    return yaml.safe_load(left) == yaml.safe_load(right)


def _promote_bands(
    root: Path, tree: str, actions: list[Action], targets: dict[str, _Target]
) -> None:
    """Copy a staged band package into the KB with its item references resolved.

    A package is promoted whole — the four documents keep their prose, their
    ``runtime`` marks, their band-side prices and their provenance, and only the
    declared transforms of :func:`promoted_band_document` touch them. A document
    the destination already carries is compared, never overwritten: the same
    document is already promoted, and a different one is a collision the caller
    refuses.
    """
    staged_root = _tree_root(tree) / BAND_ROOT
    if not staged_root.is_dir():
        return
    for package in sorted(path for path in staged_root.iterdir() if path.is_dir()):
        band_id = package.name
        band = yaml.safe_load(lexical.read_text(package / "band.yaml")) or {}
        declared = str(band.get("id") or "")
        if declared != band_id:
            actions.append(
                Action(
                    "bands",
                    band_id,
                    ACTION_CONFLICT,
                    "",
                    f"band.yaml declares id {declared!r}, the package directory is {band_id!r}",
                )
            )
            continue
        for name in BAND_DOCUMENTS:
            path = package / name
            relative = f"{BAND_ROOT}/{band_id}/{name}"
            if not path.is_file():
                actions.append(
                    Action(
                        "bands",
                        f"{band_id}/{name}",
                        ACTION_CONFLICT,
                        relative,
                        "the staged package does not carry this document",
                    )
                )
                continue
            wanted = promoted_band_document(lexical.read_text(path), band_id)
            target = _target(targets, root, relative)
            if target.text:
                if _same_document(target.text, wanted):
                    actions.append(Action("bands", f"{band_id}/{name}", ACTION_PRESENT, relative))
                else:
                    actions.append(
                        Action(
                            "bands",
                            f"{band_id}/{name}",
                            ACTION_CONFLICT,
                            relative,
                            "the KB already keeps this band document with different content",
                        )
                    )
                continue
            target.text = wanted
            actions.append(Action("bands", f"{band_id}/{name}", ACTION_NEW, relative, f"{tree} package"))


def _promote_exclusions(actions: list[Action]) -> None:
    for relative, reason in sorted(PROMOTED_EXCLUSIONS.items()):
        actions.append(Action("bands" if relative.startswith("bands") else "items", relative, ACTION_EXCLUDE, "", reason))


# --------------------------------------------------------------------------- #
# Entry point
# --------------------------------------------------------------------------- #


def promote(
    root: str | Path | None = None, trees: Iterable[str] = STAGING_TREES
) -> Promotion:
    """Plan the promotion of the staged catalogues into a destination root.

    Without ``root`` the destination is the knowledge base itself; a temporary
    directory participates the same way, which is how a promotion is proved
    before it is applied. Nothing is written and nothing is refused: the
    returned :class:`Promotion` carries the actions — conflicts included, so a
    preview can show them — and the documents, and ``write`` is what lands them
    (and refuses an undeclared collision).
    """
    from mordheim_knowledge import editorial_schemas

    destination = Path(root) if root is not None else CHECKOUT / KB_ROOT
    promotion = Promotion(destination=destination.as_posix())
    targets: dict[str, _Target] = {}
    index = _item_index(destination)
    with promotion_view():
        for tree in trees:
            staged = staged_catalogues(tree)
            _promote_items(destination, staged, promotion.actions, targets, index)
            _promote_market(destination, staged, promotion.actions, targets)
            _promote_magic(destination, staged, promotion.actions, targets)
            _promote_hirelings(destination, staged, promotion.actions, targets)
        # Bands last: a package that is promoted needs the item documents, the
        # market entry and the hireling profile its references name to be in the
        # destination already, so the shared records go first (T07 step 7-8).
        for tree in trees:
            _promote_bands(destination, tree, promotion.actions, targets)
    _promote_exclusions(promotion.actions)
    for relative, target in sorted(targets.items()):
        text = target.result()
        # The knowledge base is the only tree a reader loads: a promoted document
        # that named a staging tree would break that isolation, so the promotion
        # stops instead of publishing it.
        if _STAGING_REFERENCE.search(text):
            raise ValueError(
                f"{relative}: the promoted document would name a staging tree, and the "
                "knowledge base reads sources/knowledge only; declare the rewrite in "
                "STAGING_NOTE_REWRITES"
            )
        document = yaml.safe_load(text)
        schema = _promoted_schema(relative)
        if schema is None:
            raise ValueError(f"{relative}: no KB schema is declared for this document")
        problems = editorial_schemas.validate_document(schema, document)
        if problems:
            raise ValueError(f"{relative}: the promoted document does not match the contract: {problems[:3]}")
        path = destination / relative
        current = lexical.read_text(path) if path.is_file() else ""
        if current == text:
            continue
        # Not published to the lexical overlay: a promotion is a separate
        # operation from the normalisation passes, and a plan that were visible
        # to the next reader would make a document on disk and in memory
        # disagree. The edit carries the text, and ``write`` lands it.
        promotion.edits.append(
            lexical.Edit(
                path,
                [
                    f"{len(target.appended)} list(s) extended, "
                    f"{len(target.folded)} record(s) folded"
                ],
                text,
                current,
            )
        )
    return promotion

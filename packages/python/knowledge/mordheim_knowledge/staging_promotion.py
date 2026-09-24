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

Editing is lexical: the staged files carry comments, so the passes edit the
lines they own instead of re-dumping the document, and ``tools/format_yaml.py``
still owns the canonical shape of everything written. Each pass re-parses what
it wrote and compares it with a pure transform of what it read.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Iterator

import yaml

from mordheim_knowledge import open_field_normalization as lexical

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
    # One physical line per value: wrapping prose is ``tools/format_yaml.py``'s
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

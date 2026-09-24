"""Give the staged magic catalogues the promotion shape of the knowledge base.

The KB keeps one magic document (``catalog/campaign/magic.yaml``): the casting
rules, one row per wizard saying which lore he uses, the lores themselves and
the effect ids of the magic subsystem. The staged documents are ``draft``
fragments of it, and this pass finishes them:

* **The envelope the contract requires.** ``casting_rules`` is the canonical
  casting rule of the KB document (the staged note says no source of the packs
  introduces new casting mechanics), ``pending_lores`` and ``effect_ids`` are the
  KB's, and ``lore_assignments`` becomes the KB block: ``rows`` with
  ``wizard``/``profile_id``/``band``/``lore`` and its ``source_refs``. The rows
  are editorial knowledge, so they are a table here, per tree — including the
  wizards that cast from a lore the KB already holds.
* **Reprints and variants, in the KB's own form.** A lore the source reprints in
  full is stated in full again, with its own ids: that is how the KB keeps
  ``lore.necromancy-restless-dead`` beside ``lore.necromancy`` and
  ``lore.onogal-rituals`` beside ``lore.nurgle-rituals``. A variant that only
  renumbers spells keeps its place with the relationship in ``note``. A mirror
  whose six prayers are the KB list is not duplicated: the wizard is routed to
  the existing lore, exactly as the staged note asks. A lore the KB already has
  under the same id but with different printed text becomes its own id, so the
  merge never collides.
* **A printed chart lives with the rule that rolls on it.** The Magical Failure
  Table is the text of ``band--vagaries-of-magic`` (the band contract has no
  table slot, and the KB keeps its band charts in the rule's own prose), so the
  rows travel there and the magic document keeps no band-specific table.
"""
from __future__ import annotations

import textwrap
from pathlib import Path

import yaml

from mordheim_knowledge import open_field_normalization as lexical
from mordheim_knowledge import staging_promotion as promotion
from mordheim_knowledge.editorial_schemas import validate_document

SCHEMA = "campaign-magic.yaml.schema.json"
KB_DOCUMENT = "campaign/magic.yaml"
MAGIC_DOCUMENTS: dict[str, str] = {
    "2A": "catalog/magic-2a.yaml",
    "2B": "catalog/magic-2b.yaml",
}
CATALOGUE_ID = "campaign-magic"

#: Root keys the staged document carries and the KB document does not.
DROP_ROOT_KEYS: tuple[str, ...] = (
    "casting_rules_note",
    "magical_failure_table",
    "magical_failure_table_note",
    "magical_failure_table_source",
)

#: The KB order of the document: the merge keeps the same shape it reads.
ROOT_ORDER: tuple[str, ...] = (
    "schema_version",
    "ruleset",
    "catalog",
    "status",
    "casting_rules",
    "lore_assignments",
    "lores",
    "pending_lores",
    "effect_ids",
)

#: ``(band, profile, lore)`` of every wizard of a staged tree. A band wizard is
#: named by his pair; ``None`` marks a hireling wizard, whom the profile alone
#: identifies. Editorial knowledge, not inferred from a profile name.
MAGIC_ASSIGNMENTS: dict[str, tuple[tuple[str | None, str, str], ...]] = {
    "2A": (
        ("dreamwalkers-cult-of-morr-fbg", "priest-of-morr", "lore.funerary-rites"),
        ("druchii-mic", "sorceress", "lore.dark-elf-magic"),
        ("mazzalupo-web", "wandering-knight", "lore.commands"),
        ("necrarchs-the-soul-stealers-lotd1", "necrarch-vampire", "lore.dreaded-scrolls-of-nagash"),
        ("nipponese-expedition-web", "vim-to-mage", "lore.arabian-elemental-magic"),
        ("order-of-the-mare-web", "dame-of-the-mare", "lore.blessings-of-the-mare"),
        ("outlaws-of-stirwood-forest-redux-fbg", "cleric", "lore.prayers-of-sigmar"),
        ("protectorate-of-sigmar-lotd3", "warrior-priest", "lore.prayers-of-sigmar"),
        ("snotlings-web", "shaman", "lore.snotling-waaagh-magic"),
        ("sorcerous-society-lotd4", "magus", "lore.elemental-air"),
        ("sorcerous-society-lotd4", "magus", "lore.elemental-earth"),
        ("sorcerous-society-lotd4", "magus", "lore.elemental-fire"),
        ("sorcerous-society-lotd4", "magus", "lore.elemental-water"),
        ("sorcerous-society-lotd4", "magus", "lore.lesser-magic"),
        ("sorcerous-society-lotd4", "mage", "lore.elemental-air"),
        ("sorcerous-society-lotd4", "mage", "lore.elemental-earth"),
        ("sorcerous-society-lotd4", "mage", "lore.elemental-fire"),
        ("sorcerous-society-lotd4", "mage", "lore.elemental-water"),
        ("sorcerous-society-lotd4", "mage", "lore.lesser-magic"),
        ("survivors-of-strigos-sylv", "seer", "lore.charms-and-hexes-strigos"),
        ("survivors-of-strigos-sylv", "strigoi-vampire", "lore.dark-arts-strigos"),
        ("vampire-hunters-of-sylvania-lotd5", "priest-of-morr", "lore.funerary-rites-lotd5"),
        ("wood-elves-of-athel-loren-web", "forest-mage", "lore.woodland-incantations"),
    ),
    "2B": (
        ("call-of-the-night-haint-mim", "cairn-wraith", "lore.necromancy"),
        ("channel-rats-mim", "petru", "lore.charms-and-hexes"),
        ("forest-goblins-lus", "shaman", "lore.forest-goblin-magic"),
        ("ghost-pirates-sar", "sea-singer", "lore.songs-of-sorrow"),
        ("high-elves-lus", "loremaster", "lore.spells-of-the-djedhi"),
        ("lothern-sea-patrol-sar", "mist-mage", "lore.lothern-sea-spells"),
        ("necrarchs-mou", "nosferatu", "lore.necromancy"),
        ("shallows-beasts-mim", "mutant-priest", "lore.chaos-rituals"),
        ("shallows-beasts-mim", "mutant-priest", "lore.prayers-of-manann"),
        ("wood-elves-of-arden-mou", "forest-mage", "lore.wood-elven-spells"),
        # The Miracle Workers priests are Hired Swords of their chapter: their
        # starting experience and their prayers stay with the profile, and the
        # assignment is a row of this document.
        (None, "druid-priest-of-taal", "lore.prayers-of-taal"),
        (None, "mariner-priest-of-manann", "lore.prayers-of-manann"),
        (None, "priest-of-morr", "lore.prayers-of-morr"),
        (None, "priest-of-verena", "lore.prayers-of-verena-and-solkan"),
        (None, "priestess-of-shallya", "lore.prayers-of-shallya"),
        (None, "trickster-priest-of-ranald", "lore.prayers-of-ranald-and-handrich"),
        (None, "war-priestess-of-myrmidia", "lore.prayers-of-myrmidia"),
        (None, "warrior-priest-of-sigmar", "lore.prayers-of-sigmar"),
        (None, "wolf-priest-of-ulric", "lore.prayers-of-ulric-miracle-workers"),
    ),
}

#: A lore the KB already holds under the same id with different printed text gets
#: its own id, so the merge never collides: the Sylvania page prints the Seer's
#: Charms & Hexes list, the KB keeps the Witch's.
LORE_RENAMES: dict[str, str] = {"lore.charms-and-hexes": "lore.charms-and-hexes-strigos"}
CHARMS_NOTE_SUFFIX = (
    " VARIANT of the KB lore.charms-and-hexes (used by the Witch): the Sylvania page prints the "
    "six-spell list with different difficulties (Scry 8 vs 6, Curse 8 vs 6, Dust of the Blind 9) "
    "and expanded wording, and its sixth spell is Cure of Thorns (D9) where the KB keeps Cure (D6). "
    "Kept apart so a source change stays auditable."
)

#: The 2B mirror is the KB list with one spelling difference in a spell name, so
#: the wizard is routed to the existing lore and the duplicate is not published.
MIRROR_LORES: tuple[str, ...] = ("lore.prayers-of-taal-and-rhya",)

#: The Djedhi lore the Lothern list is reprinted from: the source reprints five
#: of its spells and its own fourth spell replaces *Fleeting Shadows*, so the
#: lore is stated in full here, with its own ids.
LOTHERN_LORE = "lore.lothern-sea-spells"
LOTHERN_SOURCE = "lore.spells-of-the-djedhi"
LOTHERN_INHERITED_ROLLS: tuple[str, ...] = ("1", "2", "3", "5", "6")
LOTHERN_NOTE = (
    "VARIANT of the KB Djedhi lore (lore.spells-of-the-djedhi), stated in full the way the KB keeps "
    "its own reprints (lore.necromancy-restless-dead, lore.onogal-rituals): the source reprints five "
    "of the Djedhi spells and the fourth spell, Mistress of the Deep (D8), replaces Fleeting Shadows. "
    'Source note: "Most of the following spells are taken from the \'Djed-Hi Spell List\' from the '
    '\'Elven Mage Hired Sword\' by Jake Thornton. The exception is the 4th spell, \'Mistress of the '
    'Deep\', which replaces the spell \'Fleeting Shadows\'."'
)

#: The failure table of the Sorcerous Society: its site is the rule that rolls on
#: it. The band contract has no table field and the KB keeps its band charts in
#: the rule's own prose, so the rows travel there.
FAILURE_TABLE_RULE = "band--vagaries-of-magic"
FAILURE_TABLE_DOCUMENT = "bands/mordheim/sorcerous-society-lotd4/special-rules.yaml"
FAILURE_TABLE_LEAD = (
    "Magical Failure Table (used with permission from the Border Town Burning supplement). "
    "2D6 result: "
)
FAILURE_TABLE_REASON = (
    "Out of scope: miscast resolution is a magic-subsystem interaction. The Magical Failure Table "
    "the rule invokes (Border Town Burning, used with permission) is printed with the rule: the band "
    "contract has no table slot, so the rows travel as the rule's own text, the way the KB keeps its "
    "other printed charts inside the rule that rolls on them."
)

LAST_KEYS: tuple[str, ...] = (
    "id",
    "name",
    "name_i18n",
    "note",
    "spells",
    "source_refs",
)


def _dump(document: dict) -> str:
    return yaml.safe_dump(
        document, allow_unicode=True, sort_keys=False, default_flow_style=False, width=100
    )


def _kb() -> dict:
    return promotion._kb_document(KB_DOCUMENT)


def magic_rows(tree: str) -> list[dict]:
    """The ``lore_assignments.rows`` of a tree, in the KB row shape."""
    rows = []
    for band, profile, lore in MAGIC_ASSIGNMENTS[tree]:
        profile_id = profile if band is not None else f"hireling.hired-sword.{profile}"
        wizard = f"{band}-{profile}" if band is not None else profile
        rows.append({"wizard": wizard, "profile_id": profile_id, "band": band, "lore": lore})
    rows.sort(key=lambda row: (row["band"] or "", row["profile_id"], row["lore"]))
    return rows


def _preferred_manual(tree: str) -> str:
    manuals = promotion._tree_manuals(tree)
    if "broheim.net" in manuals:
        return "broheim.net"
    return sorted(manuals)[0]


def _assignment_refs(tree: str) -> list[dict]:
    return [
        {
            "manual": _preferred_manual(tree),
            "printed_page": 0,
            "section": f"Band and hired-sword wizards and their lores of the {tree} packs "
            "(allocated spells)",
        }
    ]


def _lothern(lore: dict, kb_lores: dict[str, dict]) -> dict:
    """The Lothern list stated in full, the way the KB keeps its own reprints."""
    inherited = [
        spell
        for spell in kb_lores[LOTHERN_SOURCE]["spells"]
        if spell["roll"] in LOTHERN_INHERITED_ROLLS
    ]
    spells = []
    for spell in inherited:
        copy = dict(spell)
        copy["id"] = f"spell.{LOTHERN_LORE.split('.', 1)[1]}.{spell['id'].rsplit('.', 1)[-1]}"
        spells.append(copy)
    # A second run finds the inherited spells already stated: they come from the
    # KB text, so only the lore's own rows are added.
    spells.extend(
        dict(spell) for spell in lore["spells"] if spell["roll"] not in LOTHERN_INHERITED_ROLLS
    )
    spells.sort(key=lambda spell: int(spell["roll"]))
    return {**lore, "spells": spells, "note": LOTHERN_NOTE}


def promoted_lore(lore: dict, kb_lores: dict[str, dict]) -> dict:
    """One staged lore in the KB lore shape; idempotent by construction."""
    promoted = {
        key: value
        for key, value in lore.items()
        if key not in ("variant_of", "variant_of_lore", "mirror_of_lore", "marks", "replaces_lore", "inherited_spell_ids")
    }
    promoted["spells"] = [
        {key: value for key, value in spell.items() if key != "replaces"}
        for spell in lore.get("spells") or []
    ]
    if promoted["id"] == LOTHERN_LORE and LOTHERN_SOURCE in kb_lores:
        promoted = _lothern(promoted, kb_lores)
    rename = LORE_RENAMES.get(str(lore["id"]))
    if rename is not None:
        slug = rename.split(".", 1)[1]
        promoted["id"] = rename
        for spell in promoted["spells"]:
            spell["id"] = f"spell.{slug}.{spell['id'].rsplit('.', 1)[-1]}"
        promoted["note"] = str(lore.get("note") or "").strip() + CHARMS_NOTE_SUFFIX
    return {key: promoted[key] for key in LAST_KEYS if key in promoted}


def promoted_magic_document(document: dict, tree: str) -> dict:
    """The staged magic document as the KB document it will merge into."""
    kb = _kb()
    kb_lores = {lore["id"]: lore for lore in kb["lores"]}
    lores = []
    for lore in document.get("lores") or []:
        if str(lore["id"]) in MIRROR_LORES:
            continue
        lores.append(promoted_lore(lore, kb_lores))
    values = {
        "schema_version": document["schema_version"],
        "ruleset": document["ruleset"],
        "catalog": CATALOGUE_ID,
        "status": document["status"],
        "casting_rules": kb["casting_rules"],
        "lore_assignments": {"source_refs": _assignment_refs(tree), "rows": magic_rows(tree)},
        "lores": lores,
        "pending_lores": list(kb.get("pending_lores") or []),
        "effect_ids": list(kb.get("effect_ids") or []),
    }
    return {key: values[key] for key in ROOT_ORDER}


def _magic_schema_problems(text: str) -> list[str]:
    return validate_document(SCHEMA, yaml.safe_load(text))


def magic_edits(tree: str) -> list[lexical.Edit]:
    """The magic document of a tree, and the band rule its table belongs to."""
    if tree not in MAGIC_DOCUMENTS:
        return []
    path = promotion._document_path(tree, MAGIC_DOCUMENTS[tree])
    original = lexical.read_text(path)
    document = yaml.safe_load(original) or {}
    text = _dump(promoted_magic_document(document, tree))
    problems = _magic_schema_problems(text)
    if problems:
        raise ValueError(f"{path}: the promoted document does not match the contract: {problems[:3]}")
    edits: list[lexical.Edit] = []
    if yaml.safe_load(original) != yaml.safe_load(text):
        lexical.publish(path, text)
        edits.append(
            lexical.Edit(
                path,
                [
                    "envelope: casting rules, lore assignments, pending lores and effect ids of the KB",
                    f"{len(promoted_magic_document(document, tree)['lores'])} lores in the KB shape",
                ],
                text,
                original,
            )
        )
    edits += _failure_table_edits(tree, document)
    return edits


def _failure_table_edits(tree: str, magic: dict) -> list[lexical.Edit]:
    """Fold the printed table into the band rule that rolls on it."""
    rows = magic.get("magical_failure_table")
    path = promotion._document_path(tree, FAILURE_TABLE_DOCUMENT)
    if not path.is_file():
        if rows:
            raise ValueError(f"{path}: the document that keeps the rule is missing")
        return []
    original = lexical.read_text(path)
    document = yaml.safe_load(original) or {}
    rule = next(
        (item for item in document.get("rules") or [] if item.get("id") == FAILURE_TABLE_RULE), None
    )
    if rule is None:
        if rows:
            raise ValueError(f"{path}: rule {FAILURE_TABLE_RULE} is missing")
        return []
    carried = FAILURE_TABLE_LEAD in str(rule.get("effect") or "")
    if rows is None and not carried:
        raise ValueError(f"{path}: the failure table left the magic document without reaching the rule")
    expected = _promoted_rules(document, rows, carried)
    folded = bool(rows) and not carried
    text = _rewrite_rule(original, expected)
    if yaml.safe_load(text) != expected:
        raise ValueError(f"{path}: the failure-table fold changed more than the rule text")
    if text == original:
        return []
    change = (
        f"{FAILURE_TABLE_RULE}: the Magical Failure Table ({len(rows)} rows) printed with its rule"
        if folded
        else f"{FAILURE_TABLE_RULE}: the rule prose rewrapped to the maintained width"
    )
    lexical.publish(path, text)
    return [lexical.Edit(path, [change], text, original)]


def _table_prose(rows: list[dict]) -> str:
    return FAILURE_TABLE_LEAD + " ".join(f"{row['roll']} - {row['result']}" for row in rows)


def _promoted_rules(document: dict, rows: list[dict] | None, carried: bool) -> dict:
    """The special-rules document with the table folded into the rule."""
    promoted = yaml.safe_load(yaml.safe_dump(document))
    for rule in promoted["rules"]:
        if rule.get("id") != FAILURE_TABLE_RULE:
            continue
        if rows is not None and not carried:
            text = str(rule.get("effect") or "").rstrip()
            rule["effect"] = f"{text} {_table_prose(rows)}"
        for effect in (rule.get("runtime") or {}).get("effects") or []:
            effect["reason"] = FAILURE_TABLE_REASON
    return promoted


#: Ancho de la prosa mantenida del repositorio: el mismo al que envuelve
#: ``tools/knowledge/maintenance/format_yaml.py``.
PROSE_WIDTH = 100


def _wrapped_block(key: str, text: str, indent: int, ending: str) -> list[str]:
    """A folded ``key: >-`` block, one wrapped physical line per prose line."""
    body = textwrap.wrap(text, width=PROSE_WIDTH, break_long_words=False, break_on_hyphens=False)
    return [f"{' ' * indent}{key}: >-{ending}"] + [
        f"{' ' * (indent + 2)}{line}{ending}" for line in body
    ]


def _rewrite_rule(original: str, expected: dict) -> str:
    """The same document, rewritten line by line: the rule's effect and its reason."""
    lines = lexical.lines(original)
    ending = lexical.line_ending(lines[0]) if lines else "\n"
    target = next(
        start
        for start, _ in promotion._records(lines)
        if promotion._record_id(lines[start]) == FAILURE_TABLE_RULE
    )
    end = promotion._block_end(lines, target, 0)
    block = lines[target:end]
    rule = next(item for item in expected["rules"] if item.get("id") == FAILURE_TABLE_RULE)
    effect = next(index for index, line in enumerate(block) if promotion._own_key(line, "effect", 2))
    block[effect : promotion._block_end(block, effect, 2)] = _wrapped_block(
        "effect", str(rule["effect"]), 2, ending
    )
    reason = next(index for index, line in enumerate(block) if promotion._own_key(line, "reason", 6))
    reason_text = (rule.get("runtime") or {}).get("effects", [{}])[0].get("reason") or ""
    block[reason : promotion._block_end(block, reason, 6)] = _wrapped_block(
        "reason", str(reason_text), 6, ending
    )
    lines[target:end] = block
    return "".join(lines)

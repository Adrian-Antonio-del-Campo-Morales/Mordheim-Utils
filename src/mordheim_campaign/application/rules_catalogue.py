"""application.rules_catalogue: read model for the RULES browser.

Follows the read-only DTO pattern of ``post_battle_catalogue.py``: the Tk
screens ask this catalogue for the browsable KB content and receive frozen
rows already resolved to the active locale (``MORDHEIM_LOCALE``). It never
edits state and never reaches YAML from the UI.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from unicodedata import normalize

from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_knowledge.i18n import display_effect, display_name
from mordheim_knowledge.loader import load_items, load_skills
from mordheim_knowledge.rules_catalog import load_rules_catalog


@dataclass(frozen=True, slots=True)
class RuleEntry:
    """One browsable KB row, already resolved to the active locale."""

    category_id: str
    entry_id: str
    name: str
    effect: str
    #: Free detail chips (e.g. "difficulty 7", "henchman table").
    tags: tuple[str, ...] = ()
    source_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RulesCategory:
    category_id: str
    label: str


def _unaccent_lower(text: str) -> str:
    decomposed = normalize("NFD", text.casefold())
    return "".join(char for char in decomposed if char.isascii())


def _source_labels(refs) -> tuple[str, ...]:
    labels = []
    for ref in refs or ():
        if not isinstance(ref, dict):
            continue
        section = str(ref.get("section") or "").strip()
        manual = str(ref.get("manual") or "").strip()
        label = section or manual
        if label:
            labels.append(label)
    return tuple(labels)


def _entry(category_id: str, row: dict, *, tags=()) -> RuleEntry:
    return RuleEntry(
        category_id=category_id,
        entry_id=str(row.get("id") or ""),
        name=display_name(row, str(row.get("id") or "")),
        effect=display_effect(row),
        tags=tuple(tags),
        source_refs=_source_labels(row.get("source_refs")),
    )


def _lore_name(lore_id: str) -> str:
    return lore_id.rsplit(".", 1)[-1].replace("-", " ").title()


class RulesCatalogue:
    """KB categories, entries and search for the RULES browser."""

    def __init__(self, port: KnowledgePort) -> None:
        self.port = port
        # KB files are immutable during a session: load once.
        self._catalog = load_rules_catalog(self.port.ruleset)
        self._skill_rows = load_skills(self.port.ruleset)
        self._item_rows = load_items(self.port.ruleset)
        self._entries_cache: dict[str, tuple[RuleEntry, ...]] = {}

    # ------------------------------------------------------------- sources

    def _rules_document(self, stem: str) -> dict:
        return self._catalog.document(stem)

    # ---------------------------------------------------------- categories

    def categories(self) -> tuple[RulesCategory, ...]:
        """The browsable categories, in display order, with row counts."""
        counts = {
            "special-rules": len(self._rules_document("special-rules").get("rules") or ()),
            "conditions": len(self._rules_document("conditions").get("conditions") or ()),
            "core-rules": len(self._rules_document("core-combat").get("rules") or ()),
            "skills": len(self._skills()),
            "equipment": len(self._items()),
            "spells": len(self._spells()),
            "scenarios": len(self._scenarios()),
            "injuries": len(self._injury_tables()),
        }
        labels = {
            "special-rules": "Special Rules",
            "conditions": "Conditions",
            "core-rules": "Core Rules",
            "skills": "Skills",
            "equipment": "Equipment",
            "spells": "Spells",
            "scenarios": "Scenarios",
            "injuries": "Serious Injuries",
        }
        return tuple(
            RulesCategory(category_id, label)
            for category_id, label in labels.items()
            if counts.get(category_id)
        )

    # ------------------------------------------------------------- entries

    def _skills(self) -> tuple[RuleEntry, ...]:
        rows = []
        for row in self._skill_rows:
            table = str(row.get("category") or "").replace("-", " ").title()
            rows.append(_entry("skills", row, tags=(table,) if table and table != "None" else ()))
        return tuple(sorted(rows, key=lambda entry: ((entry.tags or ("",))[0], entry.name.casefold())))

    def _items(self) -> tuple[RuleEntry, ...]:
        rows = []
        for row in self._item_rows:
            kind = str(row.get("kind") or "").replace("-", " ").title()
            rows.append(_entry("equipment", row, tags=(kind,) if kind else ()))
        return tuple(sorted(rows, key=lambda entry: (entry.tags[0] if entry.tags else "", entry.name.casefold())))

    def _spells(self) -> tuple[RuleEntry, ...]:
        rows = []
        for lore in self.port.campaign_catalog().catalogue("magic.yaml").get("lores") or ():
            lore_name = _lore_name(str(lore.get("id") or ""))
            for spell in lore.get("spells") or ():
                difficulty = spell.get("difficulty")
                tag = f"{lore_name} · difficulty {difficulty}" if difficulty is not None else lore_name
                rows.append(_entry("spells", spell, tags=(tag,)))
        return tuple(sorted(rows, key=lambda entry: entry.name.casefold()))

    def _scenarios(self) -> tuple[RuleEntry, ...]:
        rows = []
        for row in self.port.campaign_catalog().catalogue("scenarios.yaml").get("scenarios") or ():
            mode = str(row.get("player_mode") or "")
            rows.append(_entry("scenarios", row, tags=(mode,) if mode else ()))
        return tuple(rows)

    def _injury_tables(self) -> tuple[RuleEntry, ...]:
        rows = []
        for table in self.port.campaign_catalog().catalogue("serious-injuries.yaml").get("tables") or ():
            applies = str(table.get("applies_to") or "").title()
            dice = table.get("dice") or {}
            count = int(dice.get("count") or 2)
            rows.append(RuleEntry(
                category_id="injuries",
                entry_id=str(table.get("id") or ""),
                name=display_name(table, str(table.get("id") or "")),
                effect=f"{len(table.get('results') or ())} results on {count}D{int(dice.get('sides') or 6)}",
                tags=(applies,) if applies else (),
                source_refs=_source_labels(table.get("source_refs")),
            ))
        return tuple(rows)

    def entries(self, category_id: str) -> tuple[RuleEntry, ...]:
        """All rows of one category."""
        builders = {
            "special-rules": lambda: tuple(
                _entry("special-rules", row)
                for row in self._rules_document("special-rules").get("rules") or ()
            ),
            "conditions": lambda: tuple(
                _entry("conditions", row)
                for row in self._rules_document("conditions").get("conditions") or ()
            ),
            "core-rules": lambda: tuple(
                _entry("core-rules", row)
                for row in self._rules_document("core-combat").get("rules") or ()
            ),
            "skills": self._skills,
            "equipment": self._items,
            "spells": self._spells,
            "scenarios": self._scenarios,
            "injuries": self._injury_tables,
        }
        builder = builders.get(category_id)
        if builder is None:
            return ()
        if category_id not in self._entries_cache:
            self._entries_cache[category_id] = builder()
        return self._entries_cache[category_id]

    def entry(self, category_id: str, entry_id: str) -> RuleEntry | None:
        return next((row for row in self.entries(category_id) if row.entry_id == entry_id), None)

    # -------------------------------------------------------------- search

    def search(self, text: str, category_id: str | None = None) -> tuple[RuleEntry, ...]:
        """Case/accent-insensitive substring over localized name + effect."""
        needle = _unaccent_lower(text.strip())
        if not needle:
            return ()
        categories = (category_id,) if category_id else tuple(row.category_id for row in self.categories())
        hits: list[RuleEntry] = []
        for current in categories:
            for row in self.entries(current):
                haystack = _unaccent_lower(f"{row.name} {row.effect} {' '.join(row.tags)}")
                if needle in haystack:
                    hits.append(row)
        return tuple(hits)

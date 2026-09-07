"""RULES browser: validated loader, application catalogue and search."""
from __future__ import annotations

from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.rules_catalogue import RulesCatalogue
from mordheim_knowledge.rules_catalog import load_rules_catalog
from mordheim_knowledge import i18n as kb_i18n


def test_rules_catalog_loads_all_prose_documents():
    catalog = load_rules_catalog()
    assert "special-rules" in catalog.stems()
    assert "conditions" in catalog.stems()
    assert "core-combat" in catalog.stems()
    assert len(catalog.document("special-rules").get("rules") or ()) >= 90


def test_rules_catalog_rejects_a_wrong_ruleset():
    import pytest

    with pytest.raises(ValueError):
        load_rules_catalog(ruleset="not-mordheim")


def _catalogue() -> RulesCatalogue:
    return KnowledgePort().rules_catalogue()


def test_categories_expose_only_non_empty_ones_in_order():
    categories = _catalogue().categories()
    ids = [category.category_id for category in categories]
    assert ids[0] == "special-rules"  # display order starts with special rules
    for category_id in ("conditions", "skills", "equipment", "spells", "scenarios", "injuries"):
        assert category_id in ids


def test_entries_carry_localized_names_and_effects():
    catalogue = _catalogue()
    entry = next(
        row for row in catalogue.entries("special-rules")
        if row.entry_id == "shared-rule.always-hungry"
    )
    assert entry.name == "Always Hungry"
    assert entry.effect.startswith("A Troll requires")
    spell = next(
        row for row in catalogue.entries("spells")
        if row.entry_id == "spell.lesser-magic.fires-of-uzhul"
    )
    assert spell.name == "Fires of U'Zhul"
    assert any("difficulty 7" in tag for tag in spell.tags)


def test_spanish_locale_resolves_i18n_fields():
    catalogue = _catalogue()
    original = kb_i18n.current_locale()
    try:
        kb_i18n.set_locale("es")
        entry = next(
            row for row in catalogue.entries("special-rules")
            if row.entry_id == "shared-rule.always-hungry"
        )
        assert entry.name == "Siempre Hambriento"
    finally:
        kb_i18n.set_locale(original)


def test_search_matches_names_effects_and_ignores_accents():
    catalogue = _catalogue()
    hits = catalogue.search("always hungry")
    assert any(row.entry_id == "shared-rule.always-hungry" for row in hits)
    scoped = catalogue.search("frenzy", category_id="conditions")
    assert scoped and all(row.category_id == "conditions" for row in scoped)
    assert catalogue.search("") == ()
    assert catalogue.search("zzzz-no-such-entry") == ()


def test_port_accessor_returns_a_working_catalogue():
    port = KnowledgePort()
    catalogue = port.rules_catalogue()
    entry = catalogue.entry("core-rules", "combat-order")
    assert entry is not None and entry.effect
    assert catalogue.entry("core-rules", "no-such-id") is None


def test_cross_links_from_skills_to_warband_profiles():
    catalogue = _catalogue()
    entry = catalogue.entry("skills", "skill.acrobat")
    links = catalogue.profile_links("skills", entry)
    assert links, "Speed skills should reach profiles through the Speed table"
    assert all(link.relation in ("skill table", "starting skill") for link in links)
    assert all(link.band and link.profile for link in links)


def test_cross_links_from_shared_rule_to_band_profiles():
    catalogue = _catalogue()
    entry = catalogue.entry("special-rules", "shared-rule.always-hungry")
    links = catalogue.profile_links("special-rules", entry)
    assert links and all(link.relation == "special rule" for link in links)
    assert any("Troll" in link.profile or link.profile for link in links)  # some profile carries it


def test_cross_links_from_equipment_and_spells():
    catalogue = _catalogue()
    item_links = catalogue.profile_links("equipment", catalogue.entry("equipment", "blessed_water"))
    assert item_links and all(link.relation == "equipment" for link in item_links)
    spell = catalogue.entry("spells", "spell.prayers-of-sigmar.armour-of-righteousness")
    spell_links = catalogue.profile_links("spells", spell)
    assert spell_links and all(link.relation == "lore" for link in spell_links)
    assert any("Matriarch" in link.profile for link in spell_links)
    # Categories without roster semantics have no links.
    assert catalogue.profile_links("conditions", catalogue.entries("conditions")[0]) == ()

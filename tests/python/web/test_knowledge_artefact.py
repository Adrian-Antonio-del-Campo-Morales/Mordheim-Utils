"""web.knowledge-artefact: the P4.2 generator is deterministic and complete.

Tests the YAML → JSON web generator (`tools/knowledge/generate_knowledge_web.py`)
against the Knowledge Base inventory:

1. the artefact builds and contains every required top section;
2. output is byte-identical across runs (no timestamps, stable order);
3. every band/profile/item/skill id is unique in its declared scope;
4. every stable id resolves (profiles→bands, trading-post item ids→KB items);
5. excluded Combat Lab data never leaks into the artefact.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "tools" / "knowledge"
sys.path.insert(0, str(TOOLS))
PACKAGE_ROOTS = (
    ROOT / "packages" / "python" / "combat-engine",
    ROOT / "packages" / "python" / "roster-construction",
    ROOT / "packages" / "python" / "core",
    ROOT / "packages" / "python" / "knowledge",
    ROOT / "packages" / "python" / "campaign",
)
for package_root in reversed(PACKAGE_ROOTS):
    sys.path.insert(0, str(package_root))

import generate_knowledge_web as generator  # noqa: E402


def _artefact() -> dict:
    return generator.generate()


def test_artefact_has_every_required_top_section() -> None:
    artefact = _artefact()
    for key in ("schema_version", "ruleset", "collections", "bands", "profiles",
                "items", "skills", "display_names", "display_effects", "weapon_hands", "campaign", "indexes"):
        assert key in artefact, f"missing top section {key!r}"
    assert artefact["schema_version"] == 1
    assert artefact["ruleset"] == "mordheim"
    for stem in generator.CAMPAIGN_CATALOGUE_STEMS:
        assert stem in artefact["campaign"], f"campaign catalogue {stem!r} missing from the artefact"


def test_output_is_byte_identical_across_runs() -> None:
    first = json.dumps(_artefact(), ensure_ascii=False, indent=1, sort_keys=False)
    second = json.dumps(_artefact(), ensure_ascii=False, indent=1, sort_keys=False)
    assert first == second


def test_ids_are_unique_in_their_declared_scope() -> None:
    artefact = _artefact()
    assert len({str(band["id"]) for band in artefact["bands"]}) == len(artefact["bands"])
    assert len({str(item["item_id"]) for item in artefact["items"]}) == len(artefact["items"])
    assert len({str(skill["id"]) for skill in artefact["skills"]}) == len(artefact["skills"])
    scoped = {(str(profile["collection"]), str(profile["band_id"]), str(profile["id"]))
              for profile in artefact["profiles"]}
    assert len(scoped) == len(artefact["profiles"])


def test_stable_references_resolve() -> None:
    artefact = _artefact()
    band_keys = {(str(band["collection"]), str(band["id"])) for band in artefact["bands"]}
    for profile in artefact["profiles"]:
        assert (str(profile["collection"]), str(profile["band_id"])) in band_keys
    all_item_ids = {str(row["id"]) for row in __import__("mordheim_knowledge.loader", fromlist=["load_items"]).load_items(artefact["ruleset"])}
    artefact_item_ids = {str(item["item_id"]) for item in artefact["items"]}
    assert artefact_item_ids <= all_item_ids
    # indexes stay coherent
    assert set(artefact["indexes"]["items_by_id"]) == artefact_item_ids


def test_profiles_materialize_shared_special_rule_references() -> None:
    artefact = _artefact()
    profile = next(row for row in artefact["profiles"] if row["id"] == "serpent-priestess")
    assert "shared-rule.leader" in profile["rule_ids"]


def test_profiles_materialize_equipment_forbids_from_special_rules() -> None:
    profile = next(row for row in _artefact()["profiles"] if row["id"] == "augur")
    assert profile["equipment_forbids"] == ["armour"]


def test_band_specific_special_rules_include_localized_prose() -> None:
    artefact = _artefact()
    rule = next(
        row for row in artefact["rules_prose"]["special-rules"]
        if row["id"] == "bergjaeger--set-traps"
    )
    assert rule["names"]["es"] == "Colocar Trampas"
    assert "Bergjäger" in rule["effects"]["es"]


def test_every_translated_band_rule_publishes_a_legacy_name_label() -> None:
    artefact = _artefact()
    labels = {row["names"]["en"]: row["names"]["es"]
              for row in artefact["rules_prose"]["localized-labels"]}
    assert labels["No Armour"] == "Sin Armadura"
    assert labels["No Missile Weapons"] == "Sin Armas de Proyectil"
    assert labels["Slayer Skills"] == "Habilidades de Matatrolles"
    assert len(labels) >= 700

    labels_by_id = {row["id"]: row["names"]["es"]
                    for row in artefact["rules_prose"]["localized-labels"]}
    assert labels_by_id["dwarf-troll-slayers--no-armour"] == "Sin Armadura"
    assert labels_by_id["dwarf-troll-slayers--no-missile-weapons"] == "Sin Armas de Proyectil"
    assert labels_by_id["dwarf-troll-slayers--slayer-skills"] == "Habilidades de Matatrolles"
    contextual = [row for row in artefact["rules_prose"]["profile-special-rules"]
                  if row["id"] == "dwarf-troll-slayers--no-armour"]
    assert any("Matatrolles Enanos" in row["effects"]["es"] for row in contextual)


def test_campaign_items_include_entries_outside_combat_lab_scope() -> None:
    artefact = _artefact()
    items = {item["item_id"]: item for item in artefact["items"]}
    assert items["rope_hook"]["names"]["es"] == "Gancho de Cuerda"
    assert items["healing_herbs"]["names"]["es"] == "Hierbas Curativas"
    assert items["long_bow"]["effects"]["es"] == 'Alcance: 30". Fuerza: 3.'
    assert items["elf_bow"]["effects"]["es"].startswith('Alcance: 36". Fuerza: 3.')
    assert "-1 a la tirada para impactar" in items["elven_cloak"]["effects"]["es"]
    assert all(item.get("effects", {}).get("en") and item.get("effects", {}).get("es")
               for item in items.values())


def test_excluded_combat_lab_surfaces_do_not_leak() -> None:
    artefact = _artefact()
    text = json.dumps(artefact)
    for forbidden in ("simulation-mappings", "execution-contract", "runtime-scope"):
        assert forbidden not in text


def test_display_names_travel_per_locale_with_canonical_english() -> None:
    artefact = _artefact()
    sample = artefact["bands"][0]
    assert "names" in sample and sample["names"].get("en"), "canonical English name missing"
    translated = [item for item in artefact["items"] if "es" in item.get("names", {})]
    assert translated, "expected at least some Spanish translations in the KB"


def test_every_profile_ability_with_a_canonical_id_has_a_display_name() -> None:
    artefact = _artefact()
    labels = artefact["display_names"]
    canonical_ids = {str(row["id"]) for row in artefact["skills"]}
    canonical_ids.update(
        str(row["id"])
        for rows in artefact["rules_prose"].values()
        for row in rows
    )
    canonical_ids.update(
        str(row["id"])
        for rows in generator.load_mechanics(artefact["ruleset"]).values()
        if isinstance(rows, list)
        for row in rows
        if isinstance(row, dict) and row.get("id")
    )
    for profile in artefact["profiles"]:
        traits = profile.get("combat_traits") or {}
        ability_ids = [*profile.get("inherent_rules", ()), *profile.get("rule_ids", ()), *traits.get("starting_skills", ())]
        for ability_id in ability_ids:
            identifier = str(ability_id)
            if identifier not in canonical_ids:
                continue
            assert identifier in labels or f"{profile['id']}:{identifier}" in labels or f"{profile['band_id']}:{profile['id']}:{identifier}" in labels, f"missing display name for {ability_id!r} on {profile['id']!r}"
    assert labels["skill.blessed-sight"]["es"] == "Vista Bendecida"
    assert artefact["display_effects"]["skill.blessed-sight"]["es"].startswith("La Augur puede repetir")


def test_serious_injury_tables_publish_reader_facing_names() -> None:
    tables = {row["id"]: row for row in _artefact()["campaign"]["serious-injuries"]["tables"]}
    assert tables["campaign.serious-injuries.hero"]["name"] == "Heroes' Serious Injuries Chart"
    assert tables["campaign.serious-injuries.hero"]["name_i18n"]["es"] == "Tabla de Heridas Graves de Héroes"
    assert tables["campaign.serious-injuries.henchman"]["name"] == "Henchmen's Serious Injuries Chart"
    assert tables["campaign.serious-injuries.henchman"]["name_i18n"]["es"] == "Tabla de Heridas Graves de Secuaces"


def test_unsupported_ruleset_fails_with_actionable_error() -> None:
    """A ruleset whose KB catalogues do not exist stops the build with a clear
    GenerationError naming the ruleset — never a raw loader traceback."""
    import pytest

    with pytest.raises(generator.GenerationError, match="trollheim"):
        generator.generate("trollheim")


def test_collections_of_the_artefact_match_the_ruleset() -> None:
    artefact = _artefact()
    for collection in artefact["collections"]:
        assert artefact["ruleset"] in collection["rulesets"]
    indexed = artefact["indexes"]["bands_by_collection"]
    assert set(indexed) == {str(collection["id"]) for collection in artefact["collections"]}

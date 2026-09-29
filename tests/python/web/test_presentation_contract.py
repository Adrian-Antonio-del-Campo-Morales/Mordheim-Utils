import pytest

from tools.knowledge.presentation_contract import build_presentation_entries, presentation_issues


def sources_of(artefact):
    return {entry["ref"]["id"]: entry["source"] for entry in build_presentation_entries(artefact)}


def test_pending_translations_are_explicit_and_never_count_as_complete():
    entries = build_presentation_entries({"items": [{"item_id": "test", "name": "Name"}]})
    assert entries[0]["fields"]["name"]["es"] == "TODO-TRANSLATE"
    assert presentation_issues(entries) == ["items/[item_id=test]:name.es"]


def test_empty_declared_translation_overrides_canonical_text():
    entries = build_presentation_entries({"items": [{"item_id": "test", "name": "Old", "names": {"en": "", "es": "Nombre"}}]})
    assert entries[0]["fields"]["name"]["en"] == "TODO-TRANSLATE"
    assert presentation_issues(entries) == ["items/[item_id=test]:name.en"]


def test_missing_required_name_is_inventoried_instead_of_skipped():
    entries = build_presentation_entries({"items": [{"item_id": "unnamed"}]})
    assert entries[0]["fields"]["name"] == {"en": "TODO-TRANSLATE", "es": "TODO-TRANSLATE"}
    assert presentation_issues(entries) == ["items/[item_id=unnamed]:name.en", "items/[item_id=unnamed]:name.es"]


def test_runtime_references_do_not_become_duplicate_skill_definitions():
    entries = build_presentation_entries({
        "skills": [{"id": "skill.example", "names": {"en": "Example", "es": "Ejemplo"}}],
        "rules_prose": {"profile-special-rules": [{"id": "local-rule", "band_id": "band", "runtime": {
            "effects": [{"id": "skill.example", "type": "skill.grant"}],
        }}]},
    })
    assert len([entry for entry in entries if entry["ref"]["id"] == "skill.example"]) == 1


def test_identity_includes_kind_and_owner_and_conflicts_fail():
    data = {"items": [{"item_id": "same", "name": "Item"}], "profiles": [
        {"id": "same", "band_id": "a", "name": "A"},
        {"id": "same", "band_id": "b", "name": "B"},
    ]}
    assert len(build_presentation_entries(data)) == 3
    data["profiles"].append({"id": "same", "band_id": "a", "name": "Wrong"})
    with pytest.raises(ValueError, match="Duplicate presentation identity"):
        build_presentation_entries(data)


def test_nested_labels_are_inventoried_and_source_metadata_is_not_a_label():
    entries = build_presentation_entries({"campaign": {"x": {"options": [
        {"id": "choice", "label": "Choice", "label_i18n": {"es": "Opción"}, "source_refs": [{"note": "Editorial"}]}
    ]}}})
    assert len(entries) == 1
    assert entries[0]["source"] == "campaign/x/options/[id=choice]"
    assert presentation_issues(entries) == []


def test_scenario_metadata_and_notes_have_explicit_translation_slots():
    entries = build_presentation_entries({"campaign": {"scenarios": {"scenarios": [{
        "id": "scenario.test", "names": {"en": "Scenario", "es": "Escenario"}, "author": "Author", "progression": {
            "wyrdstone": "One shard", "notes": ["First note", "Second note"],
            "loot": {"contents": [{"reward": "A sword"}]},
        },
    }]}}})
    fields = {entry["source"]: entry["fields"] for entry in entries}
    scenario = "campaign/scenarios/scenarios/[id=scenario.test]"
    # A personal or editorial credit keeps the published text in both locales by
    # itself: lacking a translation is never a pending translation for a name.
    assert fields[scenario]["author"] == {"en": "Author", "es": "Author"}
    progression = fields[f"{scenario}/progression"]
    assert progression["notes"] == {"en": "First note\nSecond note", "es": "TODO-TRANSLATE"}
    assert progression["wyrdstone"]["es"] == "TODO-TRANSLATE"
    assert len(presentation_issues(entries)) == 3


def test_personal_credit_is_published_in_both_locales_and_a_declared_translation_wins():
    entries = build_presentation_entries({"campaign": {"scenarios": {"scenarios": [
        {"id": "scenario.anonymous", "author": "Anonymous", "author_i18n": {"es": "Anónimo"}},
        {"id": "scenario.named", "author": "Tuomas Pirinen"},
    ]}}})
    fields = {entry["source"]: entry["fields"] for entry in entries}
    # Translatable prose is honoured: the declared canonical translation wins.
    assert fields["campaign/scenarios/scenarios/[id=scenario.anonymous]"]["author"] == {"en": "Anonymous", "es": "Anónimo"}
    # A proper name is preserved in both locales, never a missing translation.
    assert fields["campaign/scenarios/scenarios/[id=scenario.named]"]["author"] == {"en": "Tuomas Pirinen", "es": "Tuomas Pirinen"}


# ---------------------------------------------------------------------------
# Stable locators: an entry addresses the row it describes, never the position
# the row happens to occupy in an array.
# ---------------------------------------------------------------------------


def test_locator_addresses_a_row_by_its_canonical_identifier():
    assert sources_of({"items": [{"item_id": "sword", "name": "Sword"}]}) == {"sword": "items/[item_id=sword]"}
    assert sources_of({"rules_prose": {"special-rules": [
        {"id": "shared-rule.fear", "names": {"en": "Fear"}}]}}) == {"shared-rule.fear": "rules_prose/special-rules/[id=shared-rule.fear]"}


def test_locator_adds_the_published_scope_when_an_identifier_is_not_unique():
    entries = build_presentation_entries({"profiles": [
        {"id": "chief", "band_id": "barbarian", "name": "Chief"},
        {"id": "chief", "band_id": "reiklander", "name": "Chief"},
    ]})
    assert sorted(entry["source"] for entry in entries) == [
        "profiles/[id=chief,band_id=barbarian]",
        "profiles/[id=chief,band_id=reiklander]",
    ]


def test_locator_inserting_a_row_never_moves_an_identity():
    first = {"items": [{"item_id": "a", "name": "A"}, {"item_id": "b", "name": "B"}]}
    second = {"items": [{"item_id": "z", "name": "Z"}, {"item_id": "a", "name": "A"}, {"item_id": "b", "name": "B"}]}
    without = sources_of(first)
    with_extra = sources_of(second)
    assert without == {"a": "items/[item_id=a]", "b": "items/[item_id=b]"}
    assert {key: with_extra[key] for key in without} == without


def test_locator_keeps_a_slash_inside_a_selector_value():
    sources = sources_of({"rules_prose": {"localized-labels": [
        {"id": "localized-label.Animal Handler – Horse/Warhorse", "names": {"en": "Animal Handler"}}]}})
    assert sources == {"localized-label.Animal Handler – Horse/Warhorse":
                       "rules_prose/localized-labels/[id=localized-label.Animal Handler – Horse/Warhorse]"}


def test_locator_falls_back_to_an_index_only_when_no_published_field_identifies_the_row():
    sources = sources_of({"campaign": {"x": {"options": [
        {"type": "step", "note": "Same"}, {"type": "step", "note": "Same"}]}}})
    assert sorted(sources.values()) == ["campaign/x/options/[#0]", "campaign/x/options/[#1]"]


def test_locator_never_emits_a_value_carrying_a_reserved_separator():
    # The identifier cannot be written in the grammar, so it is not used: the
    # row keeps a hint the consumer verifies against the text of the entry,
    # instead of an escaped key that two rows could collide under.
    assert sources_of({"items": [{"item_id": "bro[ken"}]}) == {"bro[ken": "items/[#0]"}

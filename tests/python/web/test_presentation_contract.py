import pytest

from tools.knowledge.presentation_contract import build_presentation_entries, presentation_issues


def test_pending_translations_are_explicit_and_never_count_as_complete():
    entries = build_presentation_entries({"items": [{"item_id": "test", "name": "Name"}]})
    assert entries[0]["fields"]["name"]["es"] == "TODO-TRANSLATE"
    assert presentation_issues(entries) == ["items/0:name.es"]


def test_empty_declared_translation_overrides_canonical_text():
    entries = build_presentation_entries({"items": [{"item_id": "test", "name": "Old", "names": {"en": "", "es": "Nombre"}}]})
    assert entries[0]["fields"]["name"]["en"] == "TODO-TRANSLATE"
    assert presentation_issues(entries) == ["items/0:name.en"]


def test_missing_required_name_is_inventoried_instead_of_skipped():
    entries = build_presentation_entries({"items": [{"item_id": "unnamed"}]})
    assert entries[0]["fields"]["name"] == {"en": "TODO-TRANSLATE", "es": "TODO-TRANSLATE"}
    assert presentation_issues(entries) == ["items/0:name.en", "items/0:name.es"]


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
    with pytest.raises(ValueError, match="Ambiguous presentation identity"):
        build_presentation_entries(data)


def test_nested_labels_are_inventoried_and_source_metadata_is_not_a_label():
    entries = build_presentation_entries({"campaign": {"x": {"options": [
        {"id": "choice", "label": "Choice", "label_i18n": {"es": "Opción"}, "source_refs": [{"note": "Editorial"}]}
    ]}}})
    assert len(entries) == 1
    assert entries[0]["source"] == "campaign/x/options/0"
    assert presentation_issues(entries) == []


def test_scenario_metadata_and_notes_have_explicit_translation_slots():
    entries = build_presentation_entries({"campaign": {"scenarios": {"scenarios": [{
        "id": "scenario.test", "names": {"en": "Scenario", "es": "Escenario"}, "author": "Author", "progression": {
            "wyrdstone": "One shard", "notes": ["First note", "Second note"],
            "loot": {"contents": [{"reward": "A sword"}]},
        },
    }]}}})
    fields = {entry["source"]: entry["fields"] for entry in entries}
    assert fields["campaign/scenarios/scenarios/0"]["author"]["es"] == "TODO-TRANSLATE"
    progression = fields["campaign/scenarios/scenarios/0/progression"]
    assert progression["notes"] == {"en": "First note\nSecond note", "es": "TODO-TRANSLATE"}
    assert progression["wyrdstone"]["es"] == "TODO-TRANSLATE"
    assert len(presentation_issues(entries)) == 4

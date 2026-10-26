import pytest

from tools.knowledge.presentation_contract import build_presentation_entries

# The whole file proves the stable presentation locators that address a
# published row independently of its array position.


def sources_of(artefact):
    return {entry["ref"]["id"]: entry["source"] for entry in build_presentation_entries(artefact)}


# Stable locators: an entry addresses the row it describes, never the position
# the row happens to occupy in an array.


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

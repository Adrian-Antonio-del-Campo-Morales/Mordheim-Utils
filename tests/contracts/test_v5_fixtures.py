"""Validate every v5 contract fixture against the shared JSON Schema.

Runs as part of the contract tests: the fixtures are the executable
documentation of the format and must never drift from the schema.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "contracts" / "campaign-file-v5"
SCHEMA_PATH = CONTRACT / "campaign-file-v5.schema.json"
FIXTURES = sorted((CONTRACT / "fixtures").glob("*.json"))


def test_contract_files_exist():
    assert SCHEMA_PATH.is_file()
    assert {path.name for path in FIXTURES} == {
        "draft.json",
        "active-campaign.json",
        "pending-post-battle.json",
        "full-inventory.json",
    }


def test_schema_is_valid_draft_2020_12():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)


@pytest.mark.parametrize("fixture_path", FIXTURES, ids=lambda path: path.name)
def test_fixture_validates_against_schema(fixture_path):
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    document = json.loads(fixture_path.read_text(encoding="utf-8"))
    errors = list(Draft202012Validator(schema).iter_errors(document))
    assert not errors, "\n".join(
        f"{'/'.join(map(str, error.absolute_path)) or '(root)'}: {error.message}" for error in errors
    )


def test_fixtures_cover_the_four_campaign_shapes():
    documents = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in FIXTURES
    }
    draft = documents["draft.json"]
    assert draft["campaign"]["configuration"]["is_draft"] is True
    assert draft["view"]["selected_moment"] == "draft:0"

    active = documents["active-campaign.json"]
    assert active["campaign"]["configuration"]["is_draft"] is False
    assert active["campaign"]["states"] and active["campaign"]["battles"]

    pending = documents["pending-post-battle.json"]
    pending_post = next(post for post in pending["campaign"]["post_battles"] if not post["complete"])
    assert pending_post["event_log"], "the pending sequence must carry applied work"

    full = documents["full-inventory.json"]
    item = next(item for item in full["campaign"]["inventory"] if item["id"] == "holy_relic")
    assert item["equipped"] == 0 and item["stash"] == 1 and item["rarity"] == "Rare"
    assert item["special_rules"] == ["Scenario effect"]
    daggers = next(item for item in full["campaign"]["inventory"] if item["id"] == "dagger")
    assert daggers["owned"] == daggers["equipped"] + daggers["stash"]
    assert any(
        entry["item_id"] for warrior in full["campaign"]["warriors"] for entry in warrior["equipment"]
    )


def test_fixtures_carry_stable_kb_ids_only():
    """The KB is never serialised: references travel as ids."""
    for path in FIXTURES:
        document = json.loads(path.read_text(encoding="utf-8"))
        identity = document["campaign"]["identity"]
        assert identity["band_id"], path.name
        for warrior in document["campaign"]["warriors"]:
            assert warrior["profile_id"], f"{path.name}: warrior {warrior['id']} without profile_id"
        for item in document["campaign"]["inventory"]:
            assert item["id"], f"{path.name}: inventory row without item id"

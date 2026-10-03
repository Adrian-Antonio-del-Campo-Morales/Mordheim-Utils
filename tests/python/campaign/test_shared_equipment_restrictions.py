"""Parity of the migrated confirmation gates with their retained entry results."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.post_battle_engine import PostBattleEngine
from mordheim_construction.eligibility import call

CASES = json.loads((Path(__file__).resolve().parents[3]
                   / "tests/fixtures/eligibility/warrior-equipment.json").read_text(encoding="utf-8"))


class FixturePort(KnowledgePort):
    """Lookup-only fixture port; exercise the maintained projection method."""

    def __init__(self, args):
        self.args = args

    def item_kind(self, item_id):
        return self.args["category"]

    def profile(self, *args):
        if self.args["profile"] is None:
            raise KeyError("No canonical profile")
        return self.args["profile"]

    def items_for_profile(self, profile):
        return [SimpleNamespace(item_id=row["item_id"]) for row in profile["equipment_access"]]

    def skill_by_name(self, name):
        ids = dict(zip(self.args["warrior"]["skills"], self.args["warrior"]["skill_ids"]))
        return {"id": ids.get(name)}

    def weapon_hands(self, item_id):
        return self.args["weapon_hands"].get(item_id)

    def item_name(self, item_id):
        return self.args["item_name"]

    def trading_post_restriction(self, item_id):
        note = self.args.get("profile_restriction_note")
        return {"notes": [note] if note else []}


def engine_and_warrior(row):
    args = row["args"]
    warrior = SimpleNamespace(**copy.deepcopy(args["warrior"]))
    warrior.equipment = [SimpleNamespace(**entry) for entry in warrior.equipment]
    campaign = SimpleNamespace(collection="fixture", band_id="fixture")
    return PostBattleEngine(FixturePort(args), campaign, None), warrior


@pytest.mark.parametrize("row", CASES, ids=lambda row: row["name"])
def test_campaign_confirmation_preserves_entry_decision(row):
    engine, warrior = engine_and_warrior(row)
    args = row["args"]
    if args["stage"] == "profile":
        result = engine._profile_assignment_violation(args["item_id"], warrior)
    else:
        result = engine.loadout_violation(warrior, args["item_id"], amount=args["amount"])
    assert result == row["expected"]


@pytest.mark.parametrize("row", CASES, ids=lambda row: row["name"])
def test_actual_embedded_shared_decision_preserves_entry_result(row):
    assert call("warriorEquipmentRestriction", row["args"]) == row["expected"]


@pytest.mark.parametrize("stage", ["profile", "loadout"])
def test_confirmation_delegates_and_propagates_transport_failure(monkeypatch, stage):
    import mordheim_construction.eligibility as transport
    row = next(row for row in CASES if row["args"]["stage"] == stage)
    engine, warrior = engine_and_warrior(row)
    invoked = []

    def shared(operation, facts):
        invoked.append((operation, facts["stage"]))
        return "shared verdict"

    monkeypatch.setattr(transport, "call", shared)
    check = (lambda: engine._profile_assignment_violation(row["args"]["item_id"], warrior)) if stage == "profile" else (
        lambda: engine.loadout_violation(warrior, row["args"]["item_id"]))
    assert check() == "shared verdict"
    assert invoked == [("warriorEquipmentRestriction", stage)]

    def failed(*args):
        raise ValueError("transport unavailable")

    monkeypatch.setattr(transport, "call", failed)
    with pytest.raises(ValueError, match="transport unavailable"):
        check()

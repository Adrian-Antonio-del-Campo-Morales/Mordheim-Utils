"""Shared construction context parity through the real embedded runtime.

The direct TypeScript suite (`tests/typescript/domain/shared-construction-context.test.ts`)
runs the same fixtures against the maintained module; this file runs them through
MiniRacer, so an equivalent context and proposal set must produce equivalent
decisions on both entry points.
"""
import json
from pathlib import Path

import pytest

from mordheim_construction.eligibility import call

ROOT = Path(__file__).resolve().parents[3]
CASES = json.loads((ROOT / "tests/fixtures/eligibility/construction-context.json").read_text())


def _allowed(decisions):
    return [bool(decision["allowed"]) for decision in decisions]


def _codes(decisions):
    return [[issue["code"] for issue in decision["issues"]] for decision in decisions]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_selection_decisions_match_the_fixture(case):
    decisions = call("selectionDecisions", case["context"], case["proposals"])
    assert _allowed(decisions) == case["allowed"]
    assert _codes(decisions) == case["issue_codes"]
    assert [[issue["code"] for issue in decision["reports"]] for decision in decisions] == case["report_codes"]


@pytest.mark.parametrize("case", CASES, ids=lambda case: case["name"])
def test_complete_validation_matches_the_fixture(case):
    issues = call("validateConstruction", case["context"], {"draft": True})
    assert [issue["code"] for issue in issues] == case["validation_codes"]


@pytest.fixture(scope="module")
def canonical_transport_context():
    from mordheim_combat_lab.application.catalogue import CombatCatalogue
    catalogue = CombatCatalogue()
    choice = next(row for row in catalogue.profiles("mordheim", "mercenaries")
                  if row.profile_id == "mercenary-captain")
    package, profile, build = catalogue._selection_context(choice)
    return build, {
        "profile": catalogue._profile_facts(package, profile, build),
        "items": {}, "skills": {}, "selections": [],
        "slots": {"main_weapon_id": "weapon.fist", "off_hand_id": None},
        "operation": {"product": "combat-lab"},
    }


def test_installed_catalogue_is_lookup_not_carried_equipment(canonical_transport_context):
    from mordheim_construction.eligibility import construction_call
    build, facts = canonical_transport_context
    assert call("validateConstruction", facts) == []
    assert construction_call("validateConstruction", build, facts) == []


@pytest.mark.parametrize("source", ["selections", "possession"])
def test_transport_checks_actual_selected_and_owned_items(canonical_transport_context, source):
    from mordheim_construction.eligibility import construction_call
    build, facts = canonical_transport_context
    assert "weapon.blowpipe" not in {row["item_id"] for row in facts["profile"]["equipment_access"]}
    entries = [{"id": "weapon.blowpipe", "kind": "equipment"}] if source == "selections" else ["weapon.blowpipe"]
    issues = construction_call("validateConstruction", build, {**facts, source: entries})
    assert [(issue["code"], issue["subject_ids"][-1]) for issue in issues] == [
        ("equipment_not_permitted", "weapon.blowpipe")]


def test_transport_preserves_final_and_draft_requirement_checks(canonical_transport_context):
    from mordheim_construction.eligibility import construction_call
    build, facts = canonical_transport_context
    missing = {**facts, "limits": {"required_tag": "bow"}}
    assert [issue["code"] for issue in construction_call("validateConstruction", build, missing)] == [
        "equipment_required_missing"]
    assert construction_call("validateConstruction", build, missing, draft=True) == []

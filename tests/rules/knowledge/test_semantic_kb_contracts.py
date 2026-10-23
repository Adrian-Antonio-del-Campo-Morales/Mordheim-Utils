"""KB contracts formerly embedded in the semantic integration runner."""
from __future__ import annotations

from mordheim_knowledge.loader import knowledge_root
from mordheim_combat_lab.verification.scenarios import check_case
import pytest


@pytest.mark.parametrize("operation, choices", [
    ("selection_choices", {"bad": {"armour_id": "armour.light-armour"}}),
    ("selection_choices", {"bad": {"arbitrary_code": "pass"}}),
    ("equipment_choices", {"bad": {"special_rule_ids": []}}),
])
@pytest.mark.phase1_kb_contracts
def test_construction_choices_reject_fields_outside_their_contract(operation, choices):
    with pytest.raises(ValueError, match="unsupported construction fields"):
        check_case({"operation": operation, "context": {"choices": choices},
                    "expect": {"result.accepted": []}}, knowledge_root())


@pytest.mark.phase1_kb_contracts
def test_selection_choices_cannot_ignore_decisions():
    with pytest.raises(ValueError, match="construction cases cannot request combat decisions"):
        check_case({"operation": "selection_choices", "context": {"choices": {}},
                    "decisions": [{"key": "unrelated", "value": True}],
                    "expect": {"result.accepted": []}}, knowledge_root())


@pytest.mark.phase1_kb_contracts
def test_interaction_concepts_are_normalized_and_unknown_concepts_rejected():
    from mordheim_combat_lab.verification.interactions import normalize_interaction_contract
    assert normalize_interaction_contract({"reads": ["strength.base", "fighter.strength"],
                                           "writes": ["attacks.count"]}) == {
        "reads": ["fighter.strength"], "writes": ["attack.count"],
    }
    with pytest.raises(ValueError, match="unknown interaction concepts"):
        normalize_interaction_contract({"reads": [], "writes": ["attaks.count"]})

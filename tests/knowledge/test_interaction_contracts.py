"""Contracts for the KB interaction vocabulary."""
import pytest


def test_interaction_concepts_are_normalized_and_unknown_concepts_rejected():
    from mordheim_combat_lab.verification.interactions import normalize_interaction_contract
    assert normalize_interaction_contract({"reads": ["strength.base", "fighter.strength"],
                                           "writes": ["attacks.count"]}) == {
        "reads": ["fighter.strength"], "writes": ["attack.count"],
    }
    with pytest.raises(ValueError, match="unknown interaction concepts"):
        normalize_interaction_contract({"reads": [], "writes": ["attaks.count"]})


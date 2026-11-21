"""The rule-removal probe tells discriminating evidence from evidence that passes anyway.

Each case is a self-contained scenario, so the checks do not depend on the corpus.
The probe's binding filter is a pass-through whenever no removal is active, so
installing it in a test process leaves every other test unaffected.
"""
from __future__ import annotations

import copy

import pytest

from mordheim_conformance.integrity.removal_probe import probe_identity, probe_scenario, verdict

HARD_HEAD = "rule/mordheim/sons-of-hashut/band--hard-head/trait.concussion-immune"
HARD_TO_KILL = "mechanic/skill.hard-to-kill"

# The printed Hard Head: a mace's Concussion does not turn an injury of 2 into Stunned.
MACE_INJURY_TWO = {
    "fighters": {
        "first": {"main_weapon_id": "weapon.mace",
                  "characteristics": {"weapon_skill": 10, "strength": 8, "toughness": 3,
                                      "wounds": 3, "initiative": 10, "attacks": 1}},
        "second": {"collection": "mordheim", "band_id": "sons-of-hashut", "profile_id": "chaos-dwarf-warriors"},
    },
    "initial_state": {"second": {"wounds": 1, "attacks": 0}},
    "duel_context": {"charging": [], "active_participant": "first"},
    "maximum_rounds": 1,
    "rolls": [{"key": "round.0.first.attack.0.hit", "value": 4},
              {"key": "round.0.first.attack.0.wound", "value": 4},
              {"key": "round.0.first.attack.0.injury.0", "value": 2}],
    "expect_rounds": {0: {"state.second.wounds": 0, "state.second.condition": "KNOCKED_DOWN"}},
    "expect_final": {"rounds_executed": 1, "termination_reason": "horizon"},
}


def _missing_attack(case):
    """The same bearer, but the attack misses: the rule can never matter."""
    case = copy.deepcopy(case)
    case["rolls"] = [{"key": "round.0.first.attack.0.hit", "value": 1}]
    case["expect_rounds"] = {0: {"state.second.wounds": 1, "state.second.condition": "STANDING"}}
    return case


def test_a_scenario_that_reaches_the_rule_boundary_discriminates():
    assert probe_scenario(HARD_HEAD, MACE_INJURY_TWO) == "fails"


def test_a_scenario_that_passes_without_the_rule_is_reported():
    result = probe_identity(HARD_HEAD, [("missing-attack", _missing_attack(MACE_INJURY_TWO))])
    assert result == {"verdict": "non-discriminating", "scenarios": {"missing-attack": "survives"}}


def test_a_scenario_that_never_builds_the_recipient_is_inert():
    hand_built = copy.deepcopy(_missing_attack(MACE_INJURY_TWO))
    hand_built["fighters"]["second"] = {"main_weapon_id": "weapon.mace",
                                        "characteristics": {"weapon_skill": 3, "strength": 3, "toughness": 3,
                                                            "wounds": 1, "initiative": 2, "attacks": 1}}
    assert probe_scenario(HARD_HEAD, hand_built) == "inert"


def test_a_scenario_that_already_fails_is_not_counted():
    wrong = copy.deepcopy(MACE_INJURY_TWO)
    wrong["expect_rounds"] = {0: {"state.second.condition": "STUNNED"}}
    result = probe_identity(HARD_HEAD, [("wrong", wrong)])
    assert result == {"verdict": "untested", "scenarios": {"wrong": "baseline-fails"}}


def test_a_mechanic_is_removed_from_the_build_id_lists():
    # Hard to Kill: an injury of 5 Stuns instead of taking the fighter out.
    case = {
        "fighters": {
            "first": {"main_weapon_id": "weapon.sword",
                      "characteristics": {"weapon_skill": 10, "strength": 8, "toughness": 3,
                                          "wounds": 3, "initiative": 10, "attacks": 1}},
            "second": {"main_weapon_id": "weapon.sword", "skill_ids": ["skill.hard-to-kill"],
                       "characteristics": {"weapon_skill": 3, "strength": 3, "toughness": 3,
                                           "wounds": 1, "initiative": 2, "attacks": 1}},
        },
        "initial_state": {"second": {"attacks": 0}},
        "duel_context": {"charging": [], "active_participant": "first"},
        "maximum_rounds": 1,
        "rolls": [{"key": "round.0.first.attack.0.hit", "value": 4},
                  {"key": "round.0.first.attack.0.wound", "value": 4},
                  {"key": "round.0.first.attack.0.injury.0", "value": 5}],
        "expect_rounds": {0: {"state.second.condition": "STUNNED"}},
        "expect_final": {"rounds_executed": 1, "termination_reason": "horizon"},
    }
    assert probe_scenario(HARD_TO_KILL, case) == "fails"


BROADSWORD = "mechanic/weapon.broadsword"

# The printed Broadsword's +1 Strength moves the wound target against Toughness 3
# to 3+, so a wound die of 3 wounds only with the bonus.  The weapon sits in the
# scalar main_weapon_id slot, which no id list holds.
BROADSWORD_WOUNDS_ON_THREE = {
    "fighters": {
        "first": {"main_weapon_id": "weapon.broadsword",
                  "characteristics": {"weapon_skill": 3, "strength": 3, "toughness": 3,
                                      "wounds": 2, "initiative": 5, "attacks": 1}},
        "second": {"main_weapon_id": "weapon.mace",
                   "characteristics": {"weapon_skill": 3, "strength": 3, "toughness": 3,
                                       "wounds": 2, "initiative": 2, "attacks": 1}},
    },
    "duel_context": {"charging": ["first"], "active_participant": "first"},
    "maximum_rounds": 1,
    "rolls": [{"key": "round.0.first.attack.0.hit", "value": 4},
              {"key": "round.0.first.attack.0.wound", "value": 3},
              {"key": "round.0.second.attack.0.hit", "value": 1}],
    "expect_rounds": {0: {"attacks.0.damage": 1, "attacks.1.damage": 0, "state.second.wounds": 1}},
    "expect_final": {"rounds_executed": 1, "termination_reason": "horizon"},
}


def test_an_equipment_slot_is_removed_by_neutralising_its_execution_entry():
    assert probe_scenario(BROADSWORD, BROADSWORD_WOUNDS_ON_THREE) == "fails"


def test_an_equipment_scenario_that_passes_without_the_entry_survives():
    # A wound die of 4 wounds at Strength 3 as well: the bonus never matters.
    case = copy.deepcopy(BROADSWORD_WOUNDS_ON_THREE)
    case["rolls"][1]["value"] = 4
    assert probe_scenario(BROADSWORD, case) == "survives"


def test_a_tag_only_entry_whose_effect_lives_in_the_item_catalogue_is_inert():
    # Light Armour's execution entry carries only its tag; the save itself comes
    # from the item record, so neutralising the entry never touches the effect.
    case = copy.deepcopy(BROADSWORD_WOUNDS_ON_THREE)
    case["fighters"]["first"]["main_weapon_id"] = "weapon.mace"
    case["fighters"]["second"]["armour_id"] = "armour.light-armour"
    case["rolls"] = [{"key": "round.0.first.attack.0.hit", "value": 1},
                     {"key": "round.0.second.attack.0.hit", "value": 1}]
    case["expect_rounds"] = {0: {"state.second.wounds": 2, "state.first.wounds": 2}}
    assert probe_scenario("mechanic/armour.light-armour", case) == "inert"


@pytest.mark.parametrize("outcomes,expected", [
    ({"a": "fails", "b": "survives"}, "discriminating"),
    ({"a": "refused", "b": "survives"}, "construction-only"),
    ({"a": "inert", "b": "inert"}, "inert"),
    ({"a": "survives", "b": "inert"}, "non-discriminating"),
    ({"a": "baseline-fails"}, "untested"),
    ({"a": "baseline-fails", "b": "fails"}, "discriminating"),
])
def test_the_identity_verdict_follows_its_scenarios(outcomes, expected):
    assert verdict(outcomes) == expected

"""Copied support checks and real-pipeline runner proofs; not full ID coverage."""
from fractions import Fraction
import os
from pathlib import Path
import subprocess
import sys

import pytest

from mordheim_core.dice import RollRequest
from mordheim_knowledge.loader import knowledge_root
from mordheim_modular_e2e.corpus import CorpusError, lookup_observation
from mordheim_modular_e2e.dice import EvidenceMismatch, StrictDecisions, StrictDice, enumerate_exact
from mordheim_modular_e2e.runner import _build, _lookup, _plain, _state, check_case


@pytest.mark.phase0_preflight
@pytest.mark.parametrize("values", [[], [{"key": "wrong", "value": 3}],
                                    [{"key": "hit", "sides": 3, "value": 3}]])
def test_strict_dice_rejects_unexpected_requests(values):
    with pytest.raises(EvidenceMismatch):
        StrictDice(values).roll(RollRequest("hit"))


@pytest.mark.phase0_preflight
def test_strict_dice_checks_unused_rolls_and_repeated_keys():
    tape = StrictDice([{"key": "hit", "value": 2}, {"key": "hit", "value": 6}])
    assert tape.roll(RollRequest("hit")) == 2
    with pytest.raises(EvidenceMismatch, match="unused"):
        tape.finish()
    assert tape.roll(RollRequest("hit")) == 6
    tape.finish()


@pytest.mark.phase0_preflight
def test_strict_decisions_rejects_unused_and_unexpected_choices():
    policy = StrictDecisions([{"key": "hug", "value": False}])
    with pytest.raises(EvidenceMismatch, match="unused"):
        policy.finish()
    assert policy.choose("hug") is False
    policy.finish()
    with pytest.raises(EvidenceMismatch):
        policy.choose("hug")


@pytest.mark.phase0_preflight
def test_adaptive_enumeration_weights_short_circuit_and_mixed_dice_exactly():
    def trial(dice):
        if dice.roll(RollRequest("first")) >= 5:
            return "early"
        return "late" if dice.roll(RollRequest("second", 3)) == 3 else "failed"
    assert enumerate_exact(trial) == {
        "early": Fraction(1, 3), "late": Fraction(2, 9), "failed": Fraction(4, 9),
    }


@pytest.mark.phase0_preflight
def test_enumeration_refuses_to_truncate_unbounded_sequences():
    def forever(dice):
        while True:
            dice.roll(RollRequest("again"))
    with pytest.raises(ValueError, match="roll bound"):
        enumerate_exact(forever, max_rolls=2)


@pytest.mark.phase4_modular
def test_copied_helpers_build_initialize_and_observe_without_mutating_inputs():
    build = {"main_weapon_id": "weapon.mace", "defence_ids": ["defence.lucky-charm"]}
    overrides = {"condition": "STUNNED", "resources_spent": ["example"], "wounds": 1}
    dice = StrictDice([])
    fighter = _build(build, knowledge_root())
    state = _state(fighter, overrides, dice, "first")
    observed = _plain({"state": state})
    assert _lookup(observed, "state.condition") == "STUNNED"
    assert _lookup(observed, "state.resources_spent.0") == "example"
    assert _lookup(observed, "state.wounds") == 1
    assert _lookup(observed, "state.lucky_charm") is True
    assert build["defence_ids"] == ["defence.lucky-charm"]
    assert overrides["condition"] == "STUNNED"
    assert overrides["resources_spent"] == ["example"]
    dice.finish()


@pytest.mark.phase0_preflight
def test_copied_lookup_does_not_ignore_invalid_expectation_paths():
    """The harness name is the shared pure lookup, and invalid paths still fail.

    The failure is the documented corpus mismatch, which keeps the original
    ``KeyError``/``IndexError`` as its cause rather than swallowing it, so an
    unknown segment or an index outside the observed list is never read as an
    absent-but-acceptable observation.
    """
    with pytest.raises(CorpusError, match="observation does not exist") as missing:
        _lookup({"state": {"wounds": 1}}, "state.wondss")
    assert isinstance(missing.value.__cause__, KeyError)
    with pytest.raises(CorpusError, match="observation does not exist") as out_of_face:
        _lookup({"rounds": []}, "rounds.0")
    assert isinstance(out_of_face.value.__cause__, IndexError)
    assert _lookup is lookup_observation


def _duel_case():
    return {
        "id": "runner-state-continuation",
        "fighters": {
            side: {"main_weapon_id": "weapon.mace", "characteristics": {
                "weapon_skill": 3, "strength": 3, "toughness": 3,
                "wounds": 2, "initiative": initiative, "attacks": 1,
            }} for side, initiative in (("first", 5), ("second", 2))
        },
        "duel_context": {"charging": ["first"], "active_participant": "first"},
        "initial_state": {"first": {"resources_spent": ["spent.before-combat"]}},
        "maximum_rounds": 2,
        "rolls": [
            {"key": "round.0.first.attack.0.hit", "value": 4},
            {"key": "round.0.first.attack.0.wound", "value": 4},
            {"key": "round.0.second.attack.0.hit", "value": 1},
            {"key": "round.1.first.attack.0.hit", "value": 1},
            {"key": "round.1.second.attack.0.hit", "value": 1},
        ],
        "expect_initial": {"second.wounds": 2, "active_participant": "first"},
        "expect_rounds": {
            0: {"state.second.wounds": 1, "state.round_index": 1,
                "active_participant": "first", "state.active_participant": "second"},
            1: {"state.second.wounds": 1, "state.round_index": 2, "active_participant": "second"},
        },
        "expect_final": {"rounds_executed": 2, "termination_reason": "horizon",
                         "state.first.resources_spent": ["spent.before-combat"],
                         "state.second.wounds": 1, "state.second.condition": "STANDING"},
    }


@pytest.mark.phase4_modular
def test_real_rounds_preserve_wounds_resources_and_alternate_turns():
    check_case(_duel_case(), knowledge_root())


@pytest.mark.phase4_modular
def test_recovery_occurs_only_on_the_combatants_own_turn():
    case = _duel_case()
    case["initial_state"]["first"]["condition"] = "STUNNED"
    case["initial_state"]["second"] = {"condition": "STUNNED"}
    case["rolls"] = []
    case["expect_initial"] = {"first.condition": "STUNNED", "second.condition": "STUNNED"}
    case["expect_rounds"] = {
        0: {"state.first.condition": "KNOCKED_DOWN", "state.second.condition": "STUNNED"},
        1: {"state.first.condition": "KNOCKED_DOWN", "state.second.condition": "KNOCKED_DOWN"},
    }
    case["expect_final"] = {"rounds_executed": 2, "termination_reason": "horizon"}
    check_case(case, knowledge_root())


@pytest.mark.phase4_modular
def test_initialization_dice_are_not_repeated_between_rounds():
    case = _duel_case()
    case["fighters"]["first"]["preparation_ids"] = ["preparation.crimson-shade"]
    case["rolls"].insert(0, {"key": "first.crimson-shade", "sides": 3, "value": 2})
    case["expect_initial"]["first.initiative"] = 7
    for expected in case["expect_rounds"].values():
        expected["state.first.initiative"] = 7
    check_case(case, knowledge_root())


def _terminal_case():
    case = _duel_case()
    case["maximum_rounds"] = 3
    case["fighters"]["second"]["characteristics"]["wounds"] = 1
    case["rolls"] = [
        {"key": "round.0.first.attack.0.hit", "value": 4},
        {"key": "round.0.first.attack.0.wound", "value": 4},
        {"key": "round.0.first.attack.0.injury.0", "value": 5},
    ]
    case["expect_initial"] = {"second.wounds": 1}
    case["expect_rounds"] = {0: {"state.second.condition": "OUT", "state.round_index": 1}}
    case["expect_final"] = {"rounds_executed": 1, "termination_reason": "second_out",
                            "state.second.wounds": 0}
    return case


@pytest.mark.phase4_modular
def test_real_injury_terminates_before_the_requested_horizon():
    check_case(_terminal_case(), knowledge_root())


@pytest.mark.phase4_modular
def test_unexecuted_round_checkpoint_cannot_be_ignored():
    case = _terminal_case()
    case["expect_rounds"][1] = {"state.round_index": 2}
    with pytest.raises(EvidenceMismatch, match="checkpoint 1 was not executed"):
        check_case(case, knowledge_root())


@pytest.mark.phase4_modular
def test_local_context_preserves_nearby_provider_and_independent_turn_owner():
    case = _duel_case()
    case["duel_context"] = {
        "first_id": "owner", "second_id": "opponent",
        "charging": [], "active_participant": "opponent",
        "nearby": [{"participant_id": "helper", "side_id": "first", "fighter": {
            "band_id": "mercenaries", "profile_id": "mercenary-captain",
        }}],
        "distances": [["owner", "helper", 2]],
        "contacts": [["owner", "opponent"]],
    }
    case["expect_initial"] = {"initial_charge_flags": [False, False], "active_participant": "opponent"}
    case["expect_rounds"][0].update({"active_participant": "opponent", "state.active_participant": "owner"})
    case["expect_rounds"][1]["active_participant"] = "owner"
    case["expect_final"]["state.context.facts.nearby.0.participant_id"] = "helper"
    check_case(case, knowledge_root())


@pytest.mark.phase4_modular
def test_real_weapon_allocation_decision_precedes_attack_dice():
    case = _duel_case()
    case["fighters"]["first"]["characteristics"]["attacks"] = 2
    case["fighters"]["first"]["off_hand_id"] = "weapon.axe"
    case["maximum_rounds"] = 1
    case["rolls"] = [
        {"key": f"round.0.first.attack.{index}.hit", "value": 1} for index in range(3)
    ] + [{"key": "round.0.second.attack.0.hit", "value": 1}]
    case["decisions"] = [{"key": "round.0.first.main-weapon-majority", "value": True}]
    case["expect_rounds"] = {0: {"state.second.wounds": 2, "state.round_index": 1}}
    case["expect_final"] = {"rounds_executed": 1, "termination_reason": "horizon"}
    case["expect_events"] = [
        {"kind": "decision", "key": "round.0.first.main-weapon-majority", "value": True},
        *({"kind": "roll", "sides": 6, **roll} for roll in case["rolls"]),
    ]
    check_case(case, knowledge_root())


@pytest.mark.phase4_modular
@pytest.mark.parametrize("checkpoint", ["initial", "round", "final"])
def test_incorrect_expectations_fail_at_each_checkpoint(checkpoint):
    case = _duel_case()
    if checkpoint == "initial":
        case["expect_initial"]["second.wounds"] = 99
    elif checkpoint == "round":
        case["expect_rounds"][0]["state.second.wounds"] = 99
    else:
        case["expect_final"]["state.second.wounds"] = 99
    with pytest.raises(EvidenceMismatch, match="expected 99"):
        check_case(case, knowledge_root())


@pytest.mark.phase4_modular
@pytest.mark.parametrize("extra", ["roll", "decision"])
def test_full_loop_rejects_unconsumed_scripts(extra):
    case = _duel_case()
    if extra == "roll":
        case["rolls"].append({"key": "unused", "value": 1})
    else:
        case["decisions"] = [{"key": "unused", "value": True}]
    with pytest.raises(EvidenceMismatch, match="unused"):
        check_case(case, knowledge_root())


@pytest.mark.phase0_preflight
@pytest.mark.parametrize("maximum", [0, -1, True, 1.5])
def test_full_loop_rejects_invalid_horizons(maximum):
    case = _duel_case()
    case["maximum_rounds"] = maximum
    with pytest.raises(ValueError, match="positive integer"):
        check_case(case, knowledge_root())


@pytest.mark.phase0_preflight
def test_full_loop_rejects_misspelled_scenario_fields():
    case = _duel_case()
    case["maximum_rounnds"] = 2
    with pytest.raises(ValueError, match="unknown E2E case fields"):
        check_case(case, knowledge_root())


@pytest.mark.phase0_preflight
def test_runner_imports_without_loading_the_old_verifier(pytestconfig):
    environment = {**os.environ, "PYTHONPATH": os.pathsep.join(
        str(path) for path in pytestconfig.getini("pythonpath"))}
    command = (
        "import runpy, sys; runpy.run_path(sys.argv[1]); "
        "import mordheim_modular_e2e.runner; "
        "assert not any(name.startswith('mordheim_combat_lab.verification') for name in sys.modules)"
    )
    subprocess.run([sys.executable, "-c", command, str(Path(__file__).with_name("conftest.py"))],
                   env=environment, check=True)

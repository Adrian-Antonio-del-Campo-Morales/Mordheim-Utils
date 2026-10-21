"""The admitted duel consequences of the Clockworkers constructs.

The band's ``Construct`` rule admits four lasting individual states (No Pain,
immunity to poison, immunity to drugs and immunity to Psychology) and its
``In-built Equipment`` clause is a construction fact, never a duel immunity.
Every expectation here drives the real consumer of each clause: the injury
context, the poison transport, the preparation filter, the Fear test and the
whip's disarm.
"""
from __future__ import annotations

import pytest

from mordheim_combat import phases
from mordheim_combat.modular import attacks, psychology
from mordheim_combat.modular.contexts import _injury_context, weapon_against_opponent
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_construction.compiler import compile_fighter
from mordheim_core.dice import AlwaysAccept, ScriptedDice
from mordheim_core.models import Characteristics, DuelContext, EffectSet, FighterBuild

BAND = "clockworkers-sc"
CONSTRUCTS = ("clockwork-soldiers", "clockwork-fiend")


def construct(profile_id: str, **options):
    return compile_fighter(FighterBuild("mordheim", band_id=BAND, profile_id=profile_id,
                                        main_weapon_id="weapon.mace", **options))


def mortal(**options):
    """A living member of the same band: the control for every immunity."""
    return compile_fighter(FighterBuild("mordheim", band_id=BAND, profile_id="master-of-clocks",
                                        main_weapon_id="weapon.mace", **options))


@pytest.mark.compilation
def test_both_constructs_carry_their_admitted_immunities():
    for profile_id in CONSTRUCTS:
        fighter = construct(profile_id)
        tags = set(fighter.global_effects.tags)
        assert {"mechanic.psychology-immunity", "skill.ignore-pain", "poison_immune"} <= tags
        assert "mechanic.drug-immunity" in tags
        assert fighter.global_effects.poison_immunity


@pytest.mark.rule_behavior
def test_no_pain_downgrades_a_stunned_result_through_the_injury_consumer():
    # 1-2 knocked down, 3-4 stunned, 5+ out of action on the printed chart.
    stunned_total = 3
    construct_context = _injury_context(construct("clockwork-soldiers"), EffectSet(), "k")
    mortal_context = _injury_context(mortal(), EffectSet(), "k")
    assert phases.injury_condition(stunned_total, construct_context) == phases.Condition.KNOCKED_DOWN
    assert phases.injury_condition(stunned_total, mortal_context) == phases.Condition.STUNNED


@pytest.mark.rule_behavior
def test_a_poisoned_weapon_leaves_the_construct_unpoisoned():
    poisoner = mortal(main_poison_id="poison.black-lotus")
    assert "poison.black-lotus" in poisoner.main_weapon.tags
    blocked = weapon_against_opponent(poisoner, construct("clockwork-soldiers"), poisoner.main_weapon)
    kept = weapon_against_opponent(poisoner, mortal(), poisoner.main_weapon)
    assert "poison.black-lotus" not in blocked.tags
    assert "poison.black-lotus" in kept.tags


@pytest.mark.compilation
def test_a_drug_does_not_reach_the_construct_and_still_reaches_the_hero():
    drug = "preparation.mad-cap-mushrooms"
    assert drug not in construct("clockwork-soldiers", preparation_ids=(drug,)).global_effects.tags
    assert drug in mortal(preparation_ids=(drug,)).global_effects.tags


@pytest.mark.rule_behavior
def test_the_construct_takes_no_fear_test_when_charged_by_a_fear_causer():
    fear_causer = construct("clockwork-fiend")
    assert psychology.causes_fear(fear_causer, mortal())
    charged = DuelContext(charging=("first",), active_participant="first")
    defender = construct("clockwork-soldiers")
    state = initialize_duel(fear_causer, defender, ScriptedDice({}), context=charged)
    # An empty tape proves that no Leadership roll was demanded from the immune
    # defender; the charge stays.
    after = psychology.resolve_fear(fear_causer, defender, state, ScriptedDice({}), AlwaysAccept())
    assert after.failed_charges == frozenset() and after.initial_charge_flags == (True, False)
    # The same charge against the band's living member demands exactly that test.
    mortal_state = initialize_duel(fear_causer, mortal(), ScriptedDice({}), context=charged)
    with pytest.raises(KeyError):
        psychology.resolve_fear(fear_causer, mortal(), mortal_state, ScriptedDice({}), AlwaysAccept())


@pytest.mark.rule_behavior
def test_the_construct_is_not_immune_to_being_disarmed():
    """The in-built clause bars a roster removal, not a disarm in the duel."""
    attacker = compile_fighter(FighterBuild("mordheim", Characteristics(4, 3, 3, 1, 4, 1),
                                            main_weapon_id="weapon.whip-tc14"))
    defender = construct("clockwork-soldiers")
    outcome = attacks.resolve_reference_attack(
        attacker, defender, initialize_fighter(attacker, ScriptedDice({}), "init"),
        initialize_fighter(defender, ScriptedDice({}), "init"), attacker.main_weapon,
        ScriptedDice({"k.hit": 6, "k.disarm-hold": 1}), key="k", decisions=AlwaysAccept())
    assert outcome.disarm_slot == defender.main_hand_slot == "main"
    assert outcome.defender.broken_hands == frozenset({"main"})

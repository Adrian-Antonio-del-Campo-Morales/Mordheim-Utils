"""The admitted duel consequences of the Clockworkers constructs.

The band's ``Construct`` rule admits four lasting individual states (No Pain,
immunity to poison, immunity to drugs and immunity to Psychology) and its
``In-built Equipment`` clause is a construction fact, never a duel immunity.
Every expectation here drives the real consumer of each clause: the injury
context, the poison transport, the preparation filter, the Fear test and the
whip's disarm.
"""
from __future__ import annotations

import sys
import pytest

from mordheim_combat import phases
from mordheim_combat.modular import attacks, psychology
from mordheim_combat.modular.contexts import _injury_context, weapon_against_opponent
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_core.dice import AlwaysAccept, ScriptedDice
from mordheim_core.models import Characteristics, DuelContext, EffectSet, FighterBuild


# The frozen-build loader is the only compilation route in this module: the
# fixture below replaces this name with ``load_builds(...).fighter``, so every
# builder keeps its complete FighterBuild and the local ``replace`` calls stay
# untouched, while nothing compiles here.
compile_fighter = None


@pytest.fixture(autouse=True)
def _frozen_compiles(compiled_builds, monkeypatch):
    """Inject the common loader callable; ``compiled_builds`` is wired by conftest."""
    monkeypatch.setattr(
        sys.modules[__name__], "compile_fighter", compiled_builds.fighter)


BAND = "clockworkers-sc"


def mortal(**options):
    """A living member of the same band: the control for every immunity."""
    return compile_fighter(FighterBuild("mordheim", band_id=BAND, profile_id="master-of-clocks",
                                        main_weapon_id="weapon.mace", **options))


@pytest.mark.phase3_rules
def test_no_pain_downgrades_a_stunned_result_through_the_injury_consumer(precompiled):
    compiled = precompiled()
    construct_effects, mortal_effects = compiled.first, compiled.second
    # 1-2 knocked down, 3-4 stunned, 5+ out of action on the printed chart.
    stunned_total = 3
    construct_context = _injury_context(construct_effects, EffectSet(), "k")
    mortal_context = _injury_context(mortal_effects, EffectSet(), "k")
    assert phases.injury_condition(stunned_total, construct_context) == phases.Condition.KNOCKED_DOWN
    assert phases.injury_condition(stunned_total, mortal_context) == phases.Condition.STUNNED


@pytest.mark.phase3_rules
def test_a_poisoned_weapon_leaves_the_construct_unpoisoned(precompiled):
    # ``first`` is the recorded poisoned hero of the band, ``second`` the
    # clockwork soldier that receives the attack.
    compiled = precompiled()
    poisoner, construct_fighter = compiled.first, compiled.second
    assert "poison.black-lotus" in poisoner.main_weapon.tags
    blocked = weapon_against_opponent(poisoner, construct_fighter, poisoner.main_weapon)
    kept = weapon_against_opponent(poisoner, mortal(), poisoner.main_weapon)
    assert "poison.black-lotus" not in blocked.tags
    assert "poison.black-lotus" in kept.tags


@pytest.mark.phase2_construction
def test_a_drug_does_not_reach_the_construct_and_still_reaches_the_hero(precompiled):
    compiled = precompiled()
    drug = "preparation.mad-cap-mushrooms"
    assert drug not in compiled.first.global_effects.tags
    assert drug in compiled.second.global_effects.tags


@pytest.mark.phase3_rules
def test_the_construct_takes_no_fear_test_when_charged_by_a_fear_causer(precompiled):
    first, second = precompiled(0), precompiled(2)
    fear_causer = first.first
    defender = first.second
    mortal = second.second
    assert psychology.causes_fear(fear_causer, mortal)
    charged = DuelContext(charging=("first",), active_participant="first")
    state = initialize_duel(fear_causer, defender, ScriptedDice({}), context=charged)
    # An empty tape proves that no Leadership roll was demanded from the immune
    # defender; the charge stays.
    after = psychology.resolve_fear(fear_causer, defender, state, ScriptedDice({}), AlwaysAccept())
    assert after.failed_charges == frozenset() and after.initial_charge_flags == (True, False)
    # The same charge against the band's living member demands exactly that test.
    mortal_state = initialize_duel(fear_causer, mortal, ScriptedDice({}), context=charged)
    with pytest.raises(KeyError):
        psychology.resolve_fear(fear_causer, mortal, mortal_state, ScriptedDice({}), AlwaysAccept())


@pytest.mark.phase3_rules
def test_the_construct_is_not_immune_to_being_disarmed(precompiled):
    """The in-built clause bars a roster removal, not a disarm in the duel."""
    compiled = precompiled()
    attacker, defender = compiled.first, compiled.second
    outcome = attacks.resolve_reference_attack(
        attacker, defender, initialize_fighter(attacker, ScriptedDice({}), "init"),
        initialize_fighter(defender, ScriptedDice({}), "init"), attacker.main_weapon,
        ScriptedDice({"k.hit": 6, "k.disarm-hold": 1}), key="k", decisions=AlwaysAccept())
    assert outcome.disarm_slot == defender.main_hand_slot == "main"
    assert outcome.defender.broken_hands == frozenset({"main"})

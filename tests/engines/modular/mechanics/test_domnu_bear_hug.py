"""The Domnu's printed Bear Hug and its narrower precondition.

Sources:

* ``sources/knowledge/bands/mordheim/channel-rats-mim/special-rules.yaml`` /
  ``domnu--bear-hug``: *"If the Domnu hits the same enemy warrior with both of his
  unarmed attacks in the same round of combat, the player may choose to make a
  single Bear Hug attack instead of resolving the attacks normally.  Each player
  rolls a D6 and adds his warrior's Strength to the roll.  If the Domnu's total is
  higher or the totals are equal, the opposing warrior takes a single automatic
  wound with no armour save allowed.  If the enemy warrior's total is higher, the
  warrior has broken the Domnu's hold and suffers no damage from the attack."*
* ``sources/knowledge/bands/mordheim/kislevites/special-rules.yaml`` /
  ``trained-bear--bear-hug``: the same opposed-roll replacement, but its printed
  precondition is only *"both of his attacks"*.

The two origins share one engine operator (the ``bear_hug`` effect, the pool
branch and ``phases.resolve_bear_hug``); the Domnu adds the printed *unarmed*
precondition through the ``rule.bear-hug-unarmed`` marker the pool gate reads.
This file witnesses the marker and the precondition boundary; the shared
opposed-roll sequence and its tie/decline cases stay in
The standalone semantic corpus was retired; the local rule witnesses remain.
"""
from __future__ import annotations

import sys
from mordheim_combat.modular import pools
from mordheim_combat.modular import state as st
from tests.engines.shared.dice import StrictDecisions, StrictDice
from mordheim_core.models import Characteristics, FighterBuild
import pytest


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


def domnu(main_weapon_id="weapon.fist", band_id="channel-rats-mim", profile_id="domnu"):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band_id, profile_id=profile_id,
        main_weapon_id=main_weapon_id))


def opponent():
    # Strength 3 beside the Domnu's Strength 4, so a 3/3 opposed roll wins.
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 3, 3, 1, leadership=7),
        main_weapon_id="weapon.mace"))


def pool(attacker, count, rolls, decisions, key="domnu", *, defender=None):
    if defender is None:
        defender = opponent()
    attacker_state = st.initialize_fighter(attacker, StrictDice([]), "a")
    defender_state = st.initialize_fighter(defender, StrictDice([]), "d")
    dice = StrictDice([{"key": roll_key, "value": value} for roll_key, value in rolls])
    result = pools._resolve_attack_pool(
        attacker, defender, attacker_state, defender_state, count, dice,
        key=key, first_round=False, charging=False, decisions=decisions)
    return result, dice, result[1]


def test_the_domnu_compiles_the_bear_hug_with_its_unarmed_marker(precompiled):
    fighter = precompiled().first
    assert fighter.global_effects.bear_hug is True
    assert "rule.bear-hug-unarmed" in fighter.global_effects.tags
    # The printed Prize-fighter clause of the same profile is what lets an
    # unarmed Domnu make the two attacks this rule needs.
    assert "skill.unarmed-fighting" in fighter.global_effects.tags


def test_the_marker_stays_absent_from_a_non_recipient(precompiled):
    tinker = precompiled().first
    assert tinker.global_effects.bear_hug is False
    assert "rule.bear-hug-unarmed" not in tinker.global_effects.tags


def test_two_unarmed_hits_replace_into_one_unsaveable_wound(precompiled):
    compiled = precompiled()
    fighter, defender = compiled.first, compiled.second
    result, dice, defender_state = pool(
        fighter, 2,
        (("domnu.attack.0.hit", 5), ("domnu.attack.1.hit", 5),
         ("domnu.bear-hug.attacker", 3), ("domnu.bear-hug.defender", 3)),
        StrictDecisions([{"key": "domnu.bear-hug", "value": True}]), defender=defender)
    # One replacement attack, not three: the two qualifying hits are consumed.
    assert [(outcome.hit, outcome.wounded, outcome.damage) for outcome in result[2]] == [
        (True, True, 1)]
    # The opposed roll is exhaustive: no wound, armour or injury die was asked
    # for, which is the printed "single automatic wound with no armour save".
    assert [request.key for request in dice.requests] == [
        "domnu.attack.0.hit", "domnu.attack.1.hit",
        "domnu.bear-hug.attacker", "domnu.bear-hug.defender"]
    dice.finish()
    assert defender_state.wounds == 2  # one automatic wound against Wounds 3
    assert defender_state.condition.name == "STANDING"  # no injury roll was needed


def test_losing_the_opposed_roll_deals_no_damage(precompiled):
    compiled = precompiled()
    fighter, defender = compiled.first, compiled.second
    result, dice, defender_state = pool(
        fighter, 2,
        (("domnu.attack.0.hit", 5), ("domnu.attack.1.hit", 5),
         ("domnu.bear-hug.attacker", 1), ("domnu.bear-hug.defender", 5)),
        StrictDecisions([{"key": "domnu.bear-hug", "value": True}]), defender=defender)
    assert result[2] == ()
    dice.finish()
    assert defender_state.wounds == 3


def test_an_armed_domnu_is_never_offered_the_hug():
    # Printed precondition: both hits must be *unarmed*.  An axe-armed Domnu has
    # two attacks and both hit, yet no Bear Hug decision is ever requested, so
    # ``StrictDecisions`` with no scripted answer is the discriminating control.
    fighter = domnu(main_weapon_id="weapon.axe")
    assert fighter.global_effects.bear_hug is True
    result, dice, defender_state = pool(
        fighter, 2,
        (("domnu.attack.0.hit", 5), ("domnu.attack.1.hit", 5),
         ("domnu.attack.0.wound", 3), ("domnu.attack.1.wound", 3)),
        StrictDecisions([]))
    assert len(result[2]) == 2
    assert all(outcome.wounded and outcome.damage == 1 for outcome in result[2])
    assert defender_state.wounds == 1  # both ordinary hits resolve
    dice.finish()


def test_the_trained_bear_keeps_its_unqualified_attacks_clause(precompiled):
    # The same operator without the marker: the Bear's natural attacks still
    # offer the replacement, which is what the shared operator and its
    # specification already witness.
    bear = precompiled().first
    assert bear.global_effects.bear_hug is True
    assert "rule.bear-hug-unarmed" not in bear.global_effects.tags


def test_hug_replaces_two_hits_and_preserves_a_third_independent_attack(precompiled):
    compiled = precompiled()
    result, dice, defender_state = pool(compiled.first, 3,
        (("domnu.attack.0.hit", 5), ("domnu.attack.1.hit", 5), ("domnu.attack.2.hit", 5),
         ("domnu.bear-hug.attacker", 3), ("domnu.bear-hug.defender", 3),
         ("domnu.attack.2.wound", 3)),
        StrictDecisions([{"key": "domnu.bear-hug", "value": True}]), defender=compiled.second)
    assert len(result[2]) == 2 and [outcome.damage for outcome in result[2]] == [1, 1]
    assert defender_state.wounds == 1
    dice.finish()

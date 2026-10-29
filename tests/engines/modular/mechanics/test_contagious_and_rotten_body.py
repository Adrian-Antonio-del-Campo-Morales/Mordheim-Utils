"""Contagious and Rotten Body on both Clan Pestilens origins.

The reaction itself is the shared ``trait.contagious`` branch of
``aftermath._react_to_wound``; it is reused unchanged, together with the
Toughness-test helper and the shared Rotten Body selection gate.  What these
discriminators cover is the Mordheim origin's missing binding, the prerequisite
both origins share, and the trigger limits the printed rule states: only a
close-combat injury that definitively leaves the bearer Out of Action — after
a rescue — and only once per resolved injury.
"""
from __future__ import annotations

import sys
from dataclasses import replace

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from tests.engines.shared.dice import StrictDice
from mordheim_core.models import Characteristics, DuelContext, FighterBuild


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


HIT = "round.0.first.attack.0.hit"
WOUND = "round.0.first.attack.0.wound"
INJURY = "round.0.first.attack.0.injury.0"
RESCUE = "round.0.first.attack.0.force-of-will.rescue"
REACTION = "round.0.first.attack.0.contagious"


def tape(*values):
    return StrictDice([{"key": key, "value": value} for key, value in values])


def attacker(toughness=3, attacks=1):
    """A supplied local fighter: the injury, not the profile, is what is under test."""
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(6, 6, toughness, 2, 4, attacks),
        main_weapon_id="weapon.mace",
    ))


def duel(owner, foe, *values):
    """One charged round with a strict tape.

    Every reaction die must be scripted here, so an extra reaction overruns the
    tape and fails instead of passing unnoticed.
    """
    opening, dice = tape(), tape(*values)
    start = initialize_duel(owner, foe, opening, context=DuelContext(
        charging=("first",), active_participant="first"))
    result = resolve_round(owner, foe, start, dice)
    opening.finish()
    dice.finish()
    return result


@pytest.mark.parametrize("collection", ("mordheim", "trollheim"))
def test_only_a_definitive_out_of_action_forces_the_test_and_a_rescue_removes_it(precompiled, collection):
    compiled = precompiled()
    # ``builders`` provenance: the bearer was compiled before the attacker.
    bearer, strike_owner = compiled.first, compiled.second
    # A Knocked Down result leaves the bearer in the fight: no reaction die exists.
    stopped = duel(strike_owner, bearer, (HIT, 5), (WOUND, 4), (INJURY, 1))
    assert stopped.state.second.condition is phases.Condition.KNOCKED_DOWN
    assert stopped.state.first.wounds == 2
    # The established Out result is definitive: the attacker tests Toughness once.
    struck = duel(strike_owner, bearer, (HIT, 5), (WOUND, 4), (INJURY, 6), (REACTION, 6))
    assert struck.state.second.condition is phases.Condition.OUT
    assert struck.state.first.wounds == 1
    # A rescue is resolved first, so the trigger never happens at all.
    rescued = replace(bearer, global_effects=replace(
        bearer.global_effects, tags=(*bearer.global_effects.tags, "mechanic.force-of-will")))
    saved = duel(strike_owner, rescued, (HIT, 5), (WOUND, 4), (INJURY, 6), (RESCUE, 4),
                 ("round.0.second.attack.0.hit", 1))
    assert saved.state.second.condition is phases.Condition.STANDING
    assert saved.state.second.wounds == 1 and saved.state.first.wounds == 2


def test_the_reacting_fighter_tests_once_per_resolved_injury(precompiled):
    compiled = precompiled()
    # Two attacks, the first already lethal: the second is abandoned, and the tape
    # carries a single reaction die because a repeated reaction would overrun it.
    struck = duel(compiled.first, compiled.second, (HIT, 5),
                  ("round.0.first.attack.1.hit", 1), (WOUND, 4), (INJURY, 6), (REACTION, 6))
    assert struck.state.second.condition is phases.Condition.OUT
    assert struck.state.first.wounds == 1


@pytest.mark.parametrize("toughness,face,wounds", [(3, 6, 1), (3, 1, 2), (6, 6, 1)])
def test_the_toughness_test_limits_including_the_natural_six(precompiled, toughness, face, wounds):
    compiled = precompiled()
    struck = duel(compiled.first, compiled.second, (HIT, 5), (WOUND, 4), (INJURY, 6),
                  (REACTION, face))
    assert struck.state.second.condition is phases.Condition.OUT
    assert struck.state.first.wounds == wounds


def test_undead_and_possessed_attackers_are_exempt(precompiled):
    compiled = precompiled()
    guardian, bearer = compiled.first, compiled.second
    assert "undead_or_possessed" in guardian.global_effects.tags
    exempt = duel(guardian, bearer, ("round.0.second.fear.charged.0", 1),
                  ("round.0.second.fear.charged.1", 1), (HIT, 5), (WOUND, 4), (INJURY, 6))
    assert exempt.state.second.condition is phases.Condition.OUT
    assert exempt.state.first.wounds == 1


def test_contagious_requires_new_melee_damage_not_an_already_out_bearer(precompiled):
    from mordheim_combat.modular.aftermath import _react_to_wound
    from mordheim_combat.modular.state import AttackOutcome

    compiled = precompiled()
    owner, bearer = compiled.first, compiled.second
    state = initialize_duel(owner, bearer, tape(), context=DuelContext(
        charging=("first",), active_participant="first"))
    for melee, damage in ((False, 1), (True, 0)):
        # Non-melee reactive damage, or merely seeing an existing OUT state,
        # does not satisfy the printed close-combat injury trigger.
        outcome = AttackOutcome(state.first,
                                replace(state.second, condition=phases.Condition.OUT, wounds=0),
                                damage=damage, melee_attack=melee)
        dice = tape()
        result = _react_to_wound(owner, bearer, outcome, dice, "not-a-melee-injury")
        dice.finish()
        assert result.attacker.wounds == state.first.wounds

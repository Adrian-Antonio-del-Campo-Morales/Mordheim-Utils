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

from dataclasses import replace

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild

ORIGINS = (("mordheim", "skaven-clan-pestilens"), ("trollheim", "lustria-clan-pestilens"))
ROTTEN_BODY = "band--clan-pestilens-special-skills-rotten-body"
CONTAGIOUS = "band--clan-pestilens-special-skills-contagious"

HIT = "round.0.first.attack.0.hit"
WOUND = "round.0.first.attack.0.wound"
INJURY = "round.0.first.attack.0.injury.0"
RESCUE = "round.0.first.attack.0.force-of-will.rescue"
REACTION = "round.0.first.attack.0.contagious"


def tape(*values):
    return StrictDice([{"key": key, "value": value} for key, value in values])


def priest(collection="mordheim", rules=(ROTTEN_BODY, CONTAGIOUS)):
    band = dict(ORIGINS)[collection]
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id="plague-priest", collection=collection,
        main_weapon_id="weapon.club", special_rule_ids=rules,
    ))


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


@pytest.mark.parametrize("collection,band", ORIGINS)
@pytest.mark.rule_behavior
def test_each_origin_executes_contagious_under_its_rotten_body_prerequisite(collection, band):
    tagged = priest(collection)
    assert "contagious" in tagged.global_effects.tags
    assert "poison_immune" in tagged.global_effects.tags
    with pytest.raises(ValueError, match="Contagious requires Rotten Body"):
        priest(collection, rules=(CONTAGIOUS,))
    lonely = priest(collection, rules=(ROTTEN_BODY,))
    assert "contagious" not in lonely.global_effects.tags
    # The recipients are untouched: a profile outside the printed list is refused.
    with pytest.raises(ValueError, match="special rule is not available"):
        compile_fighter(FighterBuild(
            "mordheim", band_id=band, profile_id="plague-novices", collection=collection,
            main_weapon_id="weapon.club", special_rule_ids=(ROTTEN_BODY, CONTAGIOUS),
        ))


@pytest.mark.parametrize("collection", ("mordheim", "trollheim"))
@pytest.mark.rule_behavior
def test_only_a_definitive_out_of_action_forces_the_test_and_a_rescue_removes_it(collection):
    bearer = priest(collection)
    # A Knocked Down result leaves the bearer in the fight: no reaction die exists.
    stopped = duel(attacker(), bearer, (HIT, 5), (WOUND, 4), (INJURY, 1))
    assert stopped.state.second.condition is phases.Condition.KNOCKED_DOWN
    assert stopped.state.first.wounds == 2
    # The established Out result is definitive: the attacker tests Toughness once.
    struck = duel(attacker(), bearer, (HIT, 5), (WOUND, 4), (INJURY, 6), (REACTION, 6))
    assert struck.state.second.condition is phases.Condition.OUT
    assert struck.state.first.wounds == 1
    # A rescue is resolved first, so the trigger never happens at all.
    rescued = replace(bearer, global_effects=replace(
        bearer.global_effects, tags=(*bearer.global_effects.tags, "mechanic.force-of-will")))
    saved = duel(attacker(), rescued, (HIT, 5), (WOUND, 4), (INJURY, 6), (RESCUE, 4),
                 ("round.0.second.attack.0.hit", 1))
    assert saved.state.second.condition is phases.Condition.STANDING
    assert saved.state.second.wounds == 1 and saved.state.first.wounds == 2


@pytest.mark.rule_behavior
def test_the_reacting_fighter_tests_once_per_resolved_injury():
    # Two attacks, the first already lethal: the second is abandoned, and the tape
    # carries a single reaction die because a repeated reaction would overrun it.
    struck = duel(attacker(attacks=2), priest(), (HIT, 5),
                  ("round.0.first.attack.1.hit", 1), (WOUND, 4), (INJURY, 6), (REACTION, 6))
    assert struck.state.second.condition is phases.Condition.OUT
    assert struck.state.first.wounds == 1


@pytest.mark.parametrize("toughness,face,wounds", [(3, 6, 1), (3, 1, 2), (6, 6, 1)])
@pytest.mark.rule_behavior
def test_the_toughness_test_limits_including_the_natural_six(toughness, face, wounds):
    struck = duel(attacker(toughness), priest(), (HIT, 5), (WOUND, 4), (INJURY, 6),
                  (REACTION, face))
    assert struck.state.second.condition is phases.Condition.OUT
    assert struck.state.first.wounds == wounds


@pytest.mark.rule_behavior
def test_undead_and_possessed_attackers_are_exempt():
    guardian = compile_fighter(FighterBuild(
        "mordheim", band_id="tomb-guardians", profile_id="tomb-guardians",
        main_weapon_id="weapon.mace",
    ))
    assert "undead_or_possessed" in guardian.global_effects.tags
    exempt = duel(guardian, priest(), ("round.0.second.fear.charged.0", 1),
                  ("round.0.second.fear.charged.1", 1), (HIT, 5), (WOUND, 4), (INJURY, 6))
    assert exempt.state.second.condition is phases.Condition.OUT
    assert exempt.state.first.wounds == 1


@pytest.mark.rule_behavior
def test_contagious_requires_new_melee_damage_not_an_already_out_bearer():
    from mordheim_combat.modular.aftermath import _react_to_wound
    from mordheim_combat.modular.state import AttackOutcome

    owner, bearer = attacker(), priest()
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

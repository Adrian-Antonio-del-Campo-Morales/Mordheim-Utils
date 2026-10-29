"""Combat: the printed additional attacks join the bearer's pool.

Companion of ``tests/python/construction/test_spiked_tail_and_sword_gnoblar.py``.
Every attack misses on a natural one, so the assertions read the pool the round
built, not a wound outcome.
"""
from __future__ import annotations

from dataclasses import replace

from mordheim_combat.modular.contexts import _attack_strength
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from tests.engines.shared.dice import StrictDecisions, StrictDice
from mordheim_core.models import DuelContext
import pytest




def run(fighter, opponent):
    dice = StrictDice([{"key": key, "value": 1} for key in rolls(fighter)])
    decisions = StrictDecisions([])
    context = DuelContext(charging=("first",), active_participant="first")
    state = initialize_duel(fighter, opponent, dice, context=context)
    result = resolve_round(fighter, opponent, state, dice, decisions)
    dice.finish()
    decisions.finish()
    return result


def rolls(fighter):
    keys = []
    if any("stupidity" in str(effect.tags) or "mechanic.stupidity" in effect.tags
           for effect in (fighter.global_effects,)):
        keys += [f"round.0.first.stupidity.{index}" for index in range(3)]
    keys += ["round.0.second.fear.charged.0", "round.0.second.fear.charged.1"]
    count = fighter.characteristics.attacks + len(fighter.extra_attacks)
    keys += [f"round.0.first.attack.{index}.hit" for index in range(count)]
    keys.append("round.0.second.attack.0.hit")
    return keys


def tail_profile(fighter):
    return next(effect for effect in fighter.extra_attacks if "rule.spiked-tail" in effect.tags)


def gnoblar_profile(fighter):
    return next(effect for effect in fighter.extra_attacks if "rule.sword-gnoblar" in effect.tags)


def test_spiked_tail_adds_exactly_one_attack_to_every_rounds_pool(precompiled):
    compiled = precompiled()
    with_tail = run(compiled.first, compiled.second)
    without = run(replace(compiled.first, extra_attacks=()), compiled.second)
    assert len(with_tail.attacks) == len(without.attacks) + 1


def test_sword_gnoblar_adds_exactly_one_attack_to_the_bearers_pool(precompiled):
    compiled = precompiled()
    carried = run(compiled.first, compiled.second)
    plain = run(replace(compiled.first, extra_attacks=()), compiled.second)
    assert len(carried.attacks) == len(plain.attacks) + 1


def test_spiked_tail_resolves_at_the_bearers_strength_plus_one(precompiled):
    compiled = precompiled()
    fighter, foe = compiled.first, compiled.second
    state = initialize_fighter(fighter, StrictDice([]), "probe")
    strength, _ = _attack_strength(fighter, foe, state, tail_profile(fighter),
                                   tail_profile(fighter), first_round=True, charging=False)
    assert strength == fighter.characteristics.strength + 1


def test_sword_gnoblar_resolves_at_fixed_strength_two(precompiled):
    compiled = precompiled()
    fighter, foe = compiled.first, compiled.second
    state = initialize_fighter(fighter, StrictDice([]), "probe")
    strength, _ = _attack_strength(fighter, foe, state, gnoblar_profile(fighter),
                                   gnoblar_profile(fighter), first_round=True, charging=False)
    assert strength == 2
    assert strength != fighter.characteristics.strength + 1

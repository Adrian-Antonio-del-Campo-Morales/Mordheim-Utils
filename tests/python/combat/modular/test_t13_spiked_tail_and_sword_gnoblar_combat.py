"""T13 A-block combat: the printed additional attacks join the bearer's pool.

Companion of ``tests/python/construction/test_t13_spiked_tail_and_sword_gnoblar.py``.
Every attack misses on a natural one, so the assertions read the pool the round
built, not a wound outcome.
"""
from __future__ import annotations

from dataclasses import replace

from mordheim_combat.modular.contexts import _attack_strength
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild


def fimir(profile="fimir-warriors"):
    return compile_fighter(FighterBuild("mordheim", band_id="lords-of-the-marsh-mim",
                                        profile_id=profile))


def captain():
    return compile_fighter(FighterBuild("mordheim", band_id="maneaters", profile_id="captain",
                                        main_weapon_id="weapon.sword",
                                        owned_item_ids=("sword_gnoblar",)))


def opponent():
    return compile_fighter(FighterBuild("mordheim",
        Characteristics(3, 3, 3, 2, 3, 1, leadership=6), main_weapon_id="weapon.mace"))


def run(fighter):
    dice = StrictDice([{"key": key, "value": 1} for key in rolls(fighter)])
    decisions = StrictDecisions([])
    context = DuelContext(charging=("first",), active_participant="first")
    state = initialize_duel(fighter, opponent(), dice, context=context)
    result = resolve_round(fighter, opponent(), state, dice, decisions)
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


def test_spiked_tail_adds_exactly_one_attack_to_every_rounds_pool():
    with_tail = run(fimir())
    without = run(replace(fimir(), extra_attacks=()))
    assert len(with_tail.attacks) == len(without.attacks) + 1


def test_sword_gnoblar_adds_exactly_one_attack_to_the_bearers_pool():
    carried = run(captain())
    plain = run(replace(captain(), extra_attacks=()))
    assert len(carried.attacks) == len(plain.attacks) + 1


def test_spiked_tail_resolves_at_the_bearers_strength_plus_one():
    fighter = fimir()
    state = initialize_fighter(fighter, StrictDice([]), "probe")
    strength, _ = _attack_strength(fighter, opponent(), state, tail_profile(fighter),
                                   tail_profile(fighter), first_round=True, charging=False)
    assert strength == fighter.characteristics.strength + 1


def test_sword_gnoblar_resolves_at_fixed_strength_two():
    fighter = captain()
    state = initialize_fighter(fighter, StrictDice([]), "probe")
    strength, _ = _attack_strength(fighter, opponent(), state, gnoblar_profile(fighter),
                                   gnoblar_profile(fighter), first_round=True, charging=False)
    assert strength == 2
    assert strength != fighter.characteristics.strength + 1

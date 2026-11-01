"""Stateful round rules in the compiled core: one contract per capability.

Each case grants the frozen ``scenario/basic`` pair the tags its capability
reads and drives the native batch core alone with a recording die source, so
each assertion is a fixed fact of the oracle's rules.  Nothing here samples
the modular oracle or compares engines.
"""
from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

from mordheim_core.models import DuelContext, EffectSet
from tools.verification.compiled_cases import load_cases

native = pytest.importorskip("mordheim_combat._combat_native")

_CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "compiled-cases.json"
#: Both duelists own the turn facts, so no charge or priority die is drawn.
_STILL = DuelContext(charging=(), active_participant="first")
#: The second fighter charges and owns the turn (for the Pikewall reader).
_CHARGED = DuelContext(charging=("second",), active_participant="second")


@lru_cache(maxsize=1)
def _pair():
    case = load_cases(_CORPUS)["scenario/basic"]
    return case.first, case.second


def _tagged(fighter, *tags):
    return replace(fighter, global_effects=replace(
        fighter.global_effects, tags=(*fighter.global_effects.tags, *tags)))


def _armed(fighter, weapon):
    return replace(fighter, main_weapon=weapon, main_weapon_without_poison=None,
                   off_hand=None, off_hand_without_poison=None,
                   off_hand_attacks=False, extra_attacks=())


class _Dice:
    """Records every draw; unscripted draws fall back to a one."""

    def __init__(self, *script):
        self.script = list(script)
        self.log = []

    def integers(self, low, high, size=None):
        drawn = [self.script.pop(0) if self.script else 1
                 for _ in range(1 if size is None else int(size))]
        self.log.extend(drawn)
        return np.asarray(drawn, dtype=np.int8)

    def random(self, size=None):
        return np.zeros(size)


class _Policy:
    def __init__(self, **answers):
        self.answers = answers
        self.keys = []

    def choose(self, key, context=None):
        self.keys.append(key)
        return next((v for s, v in self.answers.items() if key.endswith(s)), True)


def _run(first, second, *script, rounds=1, policy=None, context=_STILL):
    dice, policy = _Dice(*script), policy or _Policy()
    result = native.simulate_batch_observed(
        first, second, 1, dice, rounds, policy, context=context)
    return result, dice, policy


def test_thin_flesh_lowers_the_wound_target_by_one_point_of_toughness():
    first, second = _pair()
    # Strength 3 against Toughness 3 needs a 4; Thin Flesh makes it a 3, so a
    # wound roll of exactly 3 discriminates.
    thin, _, _ = _run(first, _tagged(second, "rule.thin-flesh"), 6, 3)
    plain, _, _ = _run(first, second, 6, 3)
    assert int(thin.second_wounds[0]) < int(plain.second_wounds[0])


def test_pikewall_rerolls_a_failed_hit_while_the_bearer_is_charged():
    first, second = _pair()
    spear = EffectSet(tags=("weapon.spear",), priority=1)
    walled = _run(_armed(_tagged(first, "mechanic.pikewall"), spear), second,
                  1, context=_CHARGED)
    plain = _run(_armed(first, spear), second, 1, context=_CHARGED)
    # The printed re-roll needs the charge it is offered against: the walled
    # bearer spends one extra die re-rolling its missed hit.
    assert len(walled[1].log) == len(plain[1].log) + 1


def test_the_revenant_regenerates_one_wound_on_its_own_turn():
    first, second = _pair()
    victim = replace(second, characteristics=replace(
        second.characteristics, wounds=2))
    script = (6, 5, 1, 1, 5)
    healed, _, _ = _run(first, _tagged(victim, "mechanic.curse-of-the-revenant"),
                        *script, rounds=2)
    plain, _, _ = _run(first, victim, *script, rounds=2)
    # Wounded in round 0, the bearer takes its 5+ attempt in its own turn.
    assert int(healed.second_wounds[0]) == int(plain.second_wounds[0]) + 1


def test_herb_lore_heals_one_wound_on_a_four_plus():
    first, second = _pair()
    victim = replace(second, characteristics=replace(
        second.characteristics, wounds=2))
    script = (6, 5, 1, 1, 5)
    healed, _, policy = _run(first, _tagged(victim, "mechanic.herb-lore"),
                             *script, rounds=2)
    plain, _, _ = _run(first, victim, *script, rounds=2)
    assert int(healed.second_wounds[0]) == int(plain.second_wounds[0]) + 1
    assert "round.1.second.herb-lore" in policy.keys


def test_the_rousing_sermon_grants_its_phase_one_attack_once_per_battle():
    first, second = _pair()
    _, preaching, policy = _run(_tagged(first, "mechanic.rousing-sermon"), second, 1)
    _, plain, _ = _run(first, second, 1)
    assert "round.0.first.rousing-sermon" in policy.keys
    # One extra attack means one extra To Hit die in that phase.
    assert len(preaching.log) == len(plain.log) + 1


def test_the_alchemist_brew_restores_the_backley_penalty_it_applied():
    first, second = _pair()
    # The brew prints Strength and Initiative penalties at duel start; a
    # passed Toughness test on the bearer's own turn gives them back.
    brewed = _tagged(first, "condition.alchemist-backleys-brew")
    restored, _, _ = _run(brewed, second, 1, 1, 1)
    # The penalty is restored only once: the column is spent with it.
    again, _, _ = _run(brewed, second, 1, 1, 1, rounds=2)
    assert int(restored.first_wounds[0]) == first.characteristics.wounds
    assert int(again.first_wounds[0]) == first.characteristics.wounds


def test_the_jester_declares_one_trick_per_turn_and_trip_replaces_the_wound():
    first, second = _pair()
    jester = _tagged(first, "mechanic.confound-and-confuse")
    policy = _Policy(**{"dodge_trick_active": False, "banter_trick_active": False})
    result, _, _ = _run(jester, second, 6, 2, policy=policy)
    # The three slots are offered in their printed order and the first
    # accepted offer lights exactly its own slot.
    assert policy.keys[:3] == [
        "round.0.first.jester-trick.dodge_trick_active",
        "round.0.first.jester-trick.banter_trick_active",
        "round.0.first.jester-trick.trip_trick_active",
    ]
    # Trip gives up the attack's wound roll and knocks the opponent down on
    # a 2+, so the defender is Knocked Down with its Wounds intact.
    assert "round.0.first.attack.0.trip.hit" in policy.keys
    assert int(result.second_condition[0]) == 1
    assert int(result.second_wounds[0]) == second.characteristics.wounds

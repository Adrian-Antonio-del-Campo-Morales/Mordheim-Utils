"""Per-turn declarations and their consumers in the compiled core.

One contract per capability, driven through the native batch core alone with
a recording die source.  Nothing here samples the modular oracle or compares
engines.
"""
from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

from mordheim_core.models import DuelContext, EffectSet, MutationOption
from tools.verification.compiled_cases import load_cases

native = pytest.importorskip("mordheim_combat._combat_native")

_CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "compiled-cases.json"
_STILL = DuelContext(charging=(), active_participant="first")
#: The second fighter charges and owns the turn, so the first is "charged".
_CHARGED = DuelContext(charging=("second",), active_participant="second")


@lru_cache(maxsize=1)
def _pair():
    case = load_cases(_CORPUS)["scenario/basic"]
    return case.first, case.second


def _tagged(fighter, *tags):
    return replace(fighter, global_effects=replace(
        fighter.global_effects, tags=(*fighter.global_effects.tags, *tags)))


class _Dice:
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


def test_shifty_strikes_one_extra_blow_when_its_bearer_is_charged():
    first, second = _pair()
    shifty = _run(_tagged(first, "skill.shifty"), second, context=_CHARGED)
    plain = _run(first, second, context=_CHARGED)
    # The charged bearer strikes its bonus blow before its ordinary pool, so
    # the phase spends one extra To Hit die.
    assert len(shifty[1].log) == len(plain[1].log) + 1


def test_the_djinns_curse_turns_blows_against_its_bearer_aside():
    first, second = _pair()
    # The bearer declares on its own turn (round zero belongs to "first")
    # and the enemy strikes it in that very phase: a hit of exactly 4 lands
    # without the curse and misses with it.
    cursed, _, policy = _run(_tagged(first, "mechanic.djinns-curse"), second, 1, 4, 6)
    plain, _, _ = _run(first, second, 1, 4, 6)
    assert "round.0.first.djinn-power.curse" in policy.keys
    assert int(cursed.first_condition[0]) == 0
    assert int(plain.first_condition[0]) != 0


def test_the_storm_of_blades_grants_one_attack_and_woven_mist_spends_one():
    first, second = _pair()
    storm = _run(_tagged(first, "dance.storm-of-blades"), second)
    plain = _run(first, second)
    assert "round.0.first.dance.storm-of-blades" in storm[2].keys
    assert len(storm[1].log) == len(plain[1].log) + 1
    # Woven Mist trades the dancer's attack for its priority, so a
    # one-attack profile strikes nothing at all.
    mist = _run(_tagged(first, "dance.woven-mist"), second)
    assert len(mist[1].log) == len(plain[1].log) - 1


def test_the_main_gauche_dagger_mode_adds_its_off_hand_attack():
    first, second = _pair()
    bearer = _tagged(replace(
        first, off_hand=EffectSet(tags=("weapon.main-gauche",), parry=True),
        off_hand_attacks=False), "mechanic.main-gauche-modes")
    parrying = _run(bearer, second)
    assert "round.0.first.main-gauche-parry" in parrying[2].keys
    # Kept back it parries and strikes nothing; used as a dagger it strikes.
    dagger = _run(bearer, second, policy=_Policy(**{"main-gauche-parry": False}))
    assert len(parrying[1].log) + 1 == len(dagger[1].log)


def test_the_rememberer_offers_one_repeat_of_a_missed_blow():
    first, second = _pair()
    slayer = _tagged(first, "condition.rememberer-support", "identity.slayer",
                     "fighter-kind.hero", "mechanic.rememberer-large-only")
    large = _tagged(second, "size.large")
    _, remembering, policy = _run(slayer, large, 1)
    _, plain, _ = _run(first, large, 1)
    assert "round.0.first.attack.0.rememberer" in policy.keys
    assert len(remembering.log) == len(plain.log) + 1


def test_the_inquisitor_brands_its_enemy_on_a_judgement_of_six():
    first, second = _pair()
    chart = tuple(MutationOption(roll=10 * tens + units,
                                 effect=EffectSet(tags=("mutation.test",)),
                                 stat_ops=(("strength", "add", 2),))
                  for tens in range(1, 7) for units in range(1, 7))
    inquisitor = replace(_tagged(first, "mechanic.solkan-inquisitor"),
                         mutation_options=chart)
    branded = _run(inquisitor, second, 6)
    quiet = _run(inquisitor, second, 1)
    # A six spends the two chart dice (tens and units) a failure does not.
    assert len(branded[1].log) == len(quiet[1].log) + 2

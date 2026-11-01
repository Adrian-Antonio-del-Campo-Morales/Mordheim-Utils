"""Attack-resolution capabilities of the compiled core: one per capability.

Each case grants the frozen ``scenario/basic`` pair the tags its capability
reads and drives the native batch core alone with a recording die source, so
the assertion is a fixed fact of the oracle's rules -- which dice were drawn,
which decision keys were asked and what the warriors ended up as.  Nothing
here samples the modular oracle or compares engines.
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


@lru_cache(maxsize=1)
def _pair():
    case = load_cases(_CORPUS)["scenario/basic"]
    return case.first, case.second


def _tagged(fighter, *tags, **fields):
    return replace(fighter, global_effects=replace(
        fighter.global_effects, tags=(*fighter.global_effects.tags, *tags), **fields))


def _armed(fighter, weapon):
    """The fighter reduced to one named weapon, so one pool means one attack."""
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


def _run(first, second, *script, rounds=1, policy=None):
    dice, policy = _Dice(*script), policy or _Policy()
    result = native.simulate_batch_observed(
        first, second, 1, dice, rounds, policy, context=_STILL)
    return result, dice, policy


def test_hatred_rerolls_a_failed_first_round_hit():
    """The oracle's whole ``_hit_reroll`` list, folded through its predicate."""
    first, second = _pair()
    undead = _tagged(second, "nature.undead")
    _, hating, _ = _run(_tagged(first, "mechanic.hatred-undead"), undead, 1, 1, 1)
    _, plain, _ = _run(first, undead, 1, 1)
    # Hatred spends one extra die re-rolling the missed first-round hit.
    assert len(hating.log) == len(plain.log) + 1


def test_killing_blow_wounds_automatically_on_a_natural_six():
    first, second = _pair()
    blade = EffectSet(tags=("weapon.sword",))
    killer, _, _ = _run(_armed(first, replace(
        blade, tags=(*blade.tags, "mechanic.killing-blow"))), second, 6)
    ordinary, plain, _ = _run(_armed(first, blade), second, 6)
    # No To Wound die is rolled, so the natural six goes straight to injury
    # and takes the one-Wound defender down; the ordinary blade rolls to
    # wound instead and its failure leaves the defender standing.
    assert int(killer.second_wounds[0]) == 0
    assert int(ordinary.second_wounds[0]) == second.characteristics.wounds


def test_spectral_touch_adds_one_extra_wound_on_a_natural_six():
    first, second = _pair()
    tough = replace(second, characteristics=replace(
        second.characteristics, wounds=3, toughness=3))
    fist = EffectSet(tags=("weapon.fist",))
    ghost, _, _ = _run(_armed(first, replace(
        fist, tags=(*fist.tags, "trait.spectral-touch"))), tough, 6)
    plain, _, _ = _run(_armed(first, fist), tough, 6)
    # One extra wound of this same attack, not a fresh hit: the ordinary
    # wound roll fails for both, so only the trait costs the defender a Wound.
    assert int(ghost.second_wounds[0]) == int(plain.second_wounds[0]) - 1


def test_a_helpless_defender_is_taken_out_without_losing_wounds():
    """The oracle returns ``damage=1`` and leaves the Wound total untouched."""
    first, second = _pair()
    netted = _tagged(replace(second, characteristics=replace(
        second.characteristics, wounds=3)), "condition.netted")
    result, _, _ = _run(first, netted, 6, 6)
    assert int(result.second_condition[0]) == 4
    assert int(result.second_wounds[0]) == 3


def test_the_shock_rod_stuns_on_a_low_injury_roll():
    first, second = _pair()
    result, _, _ = _run(_armed(first, EffectSet(tags=("weapon.shock-rod",))),
                        second, 6, 6, 1, 1)
    # The printed band stuns where the ordinary table would knock down.
    assert int(result.second_condition[0]) == 2


def test_the_ethereal_save_turns_a_hit_aside_on_its_supplied_face():
    first, second = _pair()
    ghost = _tagged(second, "mechanic.ethereal-hit-save", ethereal_hit_save=2)
    saved, _, _ = _run(first, ghost, 6, 2)
    missed, _, _ = _run(first, ghost, 6, 1)
    # The supplied face decides it: a 2 saves, a 1 lets the wound roll run.
    assert int(saved.second_wounds[0]) == ghost.characteristics.wounds
    assert len(_run(first, ghost, 6, 1)[1].log) > len(_run(first, ghost, 6, 2)[1].log)


def test_the_vomit_attack_replaces_the_whole_pool_when_accepted():
    first, second = _pair()
    belcher = replace(first, vomit_attack=EffectSet(
        tags=("weapon.vomit-attack",), fixed_strength=5, automatic_hit=True))
    accepted, _, policy = _run(belcher, second, 6)
    declined, _, _ = _run(belcher, second, 6,
                          policy=_Policy(**{".vomit-attack": False}))
    assert "round.0.first.vomit-attack" in policy.keys
    # Accepting swaps the whole pool for the Strength 5 automatic hit, which
    # wounds; declining keeps the printed weapon, whose wound roll fails.
    assert int(accepted.second_wounds[0]) < int(declined.second_wounds[0])
    assert int(declined.second_wounds[0]) == second.characteristics.wounds


def test_the_lotus_critical_is_offered_under_the_round_attack_key():
    first, second = _pair()
    poisoner = _armed(first, EffectSet(tags=("weapon.dagger", "poison.black-lotus")))
    _, dice, policy = _run(poisoner, second, 6,
                           policy=_Policy(**{".lotus-critical": False}))
    assert "round.0.first.attack.0.lotus-critical" in policy.keys


def test_ranalds_luck_adjusts_one_owned_attack_die_once_per_battle():
    first, second = _pair()
    _, dice, policy = _run(_tagged(first, "mechanic.ranalds-luck"), second, 3,
                           policy=_Policy(**{".ranalds-luck.minus": False}))
    # The owned hit die is offered the printed adjustment under its own key.
    assert "round.0.first.attack.0.hit.ranalds-luck.plus" in policy.keys
    assert policy.keys.count("round.0.first.attack.0.hit.ranalds-luck.plus") == 1

"""The last modular rules ported to the compiled core.

One contract per distinct mechanism (a compile-time fold, a new attack step,
a new per-turn producer), driven through the native batch core alone with a
recording die source.  Nothing here samples the modular oracle or compares
engines.
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
_STILL = DuelContext(charging=(), active_participant="first")


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


def test_a_folded_hit_modifier_reaches_the_to_hit_roll():
    """Unholy Stink stands for every constant clause of the oracle's
    ``prepare_hit_context`` that the compile layer folds."""
    first, second = _pair()
    stinking, _, _ = _run(first, _tagged(second, "mechanic.unholy-stink"), 4, 6)
    plain, _, _ = _run(first, second, 4, 6)
    # A blow of exactly 4 lands without the stench and misses through it.
    assert int(stinking.second_wounds[0]) == second.characteristics.wounds
    assert int(plain.second_wounds[0]) < second.characteristics.wounds


def test_a_folded_strength_clause_reaches_the_wound_target():
    """The Seaguard's spear stands for the oracle's ``_attack_strength``
    clauses the compile layer folds."""
    first, second = _pair()
    spear = EffectSet(tags=("weapon.spear", "mechanic.seaguard-spear-master"))
    master = _armed(_tagged(first, "mechanic.seaguard-spear-master"), spear)
    plain = _armed(first, EffectSet(tags=("weapon.spear",)))
    sharp, _, _ = _run(master, second, 6, 3)
    blunt, _, _ = _run(plain, second, 6, 3)
    # Strength 4 wounds Toughness 3 on a 3; Strength 3 needs a 4.
    assert int(sharp.second_wounds[0]) < int(blunt.second_wounds[0])


def test_darting_steel_caps_the_parry_at_the_blow_it_answers():
    first, second = _pair()
    fencer = replace(second, main_weapon=EffectSet(tags=("weapon.sword",), parry=True))
    fencer = _tagged(fencer, "defence.buckler")
    darting = _run(_pair()[0], _tagged(fencer, "mechanic.darting-steel"), 4, 6)
    plain = _run(_pair()[0], fencer, 4, 6)
    # A parry of 6 blocks a hit of 4 normally; Darting Steel refuses it, so
    # the defender spends its printed re-roll instead.
    assert len(darting[1].log) == len(plain[1].log) + 1


def test_marks_of_ranald_ducks_a_landed_hit_on_an_unmodifiable_six():
    first, second = _pair()
    priest = _tagged(second, "mechanic.marks-of-ranald")
    ducked, _, _ = _run(first, priest, 6, 6)
    assert int(ducked.second_wounds[0]) == second.characteristics.wounds


def test_titanic_strength_throws_a_standing_foe_down_on_a_failed_wound():
    first, second = _pair()
    titan = _tagged(first, "mechanic.titanic-strength")
    result, _, _ = _run(titan, second, 6, 1, 6)
    # The blow fails to wound, and the Strength test of 6 fails with it.
    assert int(result.second_condition[0]) == 1
    assert int(result.second_wounds[0]) == second.characteristics.wounds


def test_the_honourable_strike_nothing_at_a_foe_already_down():
    first, second = _pair()
    netted = _tagged(second, "condition.netted")
    honourable, dice, _ = _run(_tagged(first, "mechanic.honorable"), netted)
    # No die is drawn at all: the pool declines the helpless target and the
    # netted victim cannot strike back.
    assert dice.log == []
    assert int(honourable.second_condition[0]) == 1


def test_the_mantle_of_crows_opens_the_phase_with_its_own_hit():
    first, second = _pair()
    crows = _run(_tagged(first, "mechanic.mantle-of-crows"), second)
    plain = _run(first, second)
    assert len(crows[1].log) == len(plain[1].log) + 1


def test_ravening_onslaught_turns_a_natural_six_into_another_blow():
    first, second = _pair()
    ravening = _run(_tagged(first, "mechanic.ravening-onslaught"), second, 6)
    plain = _run(first, second, 6)
    assert len(ravening[1].log) == len(plain[1].log) + 1


def test_a_failed_animosity_test_silences_the_squabbler_entirely():
    first, second = _pair()
    squabbler = _tagged(first, "mechanic.goblin-squabble")
    failed, _, _ = _run(squabbler, second, 1, 6, 6)
    passed, _, _ = _run(first, second, 6, 6)
    # Rolling a one costs the whole pool, so the enemy takes no blow and
    # answers freely; without the squabble the exchange runs the other way.
    assert int(failed.second_wounds[0]) == second.characteristics.wounds
    assert int(passed.second_wounds[0]) < second.characteristics.wounds


def test_the_torturers_hold_replaces_both_pools():
    first, second = _pair()
    held, dice, policy = _run(_tagged(first, "mechanic.gaoler-grapple"), second)
    assert "round.0.first.torturer-grapple" in policy.keys
    # A declared hold is the warrior's whole pool and pins its victim, so
    # neither side strikes an independent blow.
    assert dice.log == []


def test_the_sea_shanty_costs_its_listener_one_attack():
    first, second = _pair()
    singer = _tagged(first, "mechanic.sea-shanty")
    sung, _, policy = _run(singer, replace(second, characteristics=replace(
        second.characteristics, attacks=2)), 6, 6)
    assert "round.0.first.sea-shanty" in policy.keys


def test_the_electrical_touch_forfeits_a_blow_for_its_jolt():
    first, second = _pair()
    jolting = _run(_tagged(first, "mechanic.electrical-touch"), second)
    plain = _run(first, second)
    assert "round.0.first.electrical-touch.forfeit.0" in jolting[2].keys
    assert len(jolting[1].log) == len(plain[1].log) + 1


def test_the_giggle_juice_spray_replaces_one_allocated_blow():
    first, second = _pair()
    sprayed = _run(_tagged(first, "mechanic.giggle-juice-spray"), second)
    plain = _run(first, second)
    assert "round.0.first.giggle-juice-attack.0" in sprayed[2].keys
    assert len(sprayed[1].log) == len(plain[1].log) + 1


def test_the_wheelo_collision_lands_before_any_weapon_blow():
    first, second = _pair()
    charging = DuelContext(charging=("first",), active_participant="first")
    dice, policy = _Dice(), _Policy()
    native.simulate_batch_observed(
        _tagged(first, "mechanic.wheelo-impact"), second, 1, dice, 1, policy,
        context=charging)
    plain_dice = _Dice()
    native.simulate_batch_observed(first, second, 1, plain_dice, 1, _Policy(),
                                   context=charging)
    assert len(dice.log) == len(plain_dice.log) + 1


def test_the_slayer_deathblow_is_offered_once_he_is_taken_out():
    """The captured allocation outlives its owner, so the offer must reach a
    Slayer who went down during the very phase that allocated it."""
    from mordheim_core.models import DuelRequest
    from mordheim_combat.vectorized import simulate_duel

    first, second = _pair()
    slayer = _tagged(replace(first, characteristics=replace(
        first.characteristics, attacks=2, wounds=1)), "mechanic.deathblow")

    class _Recorder:
        def __init__(self):
            self.suffixes = set()

        def choose(self, key, context=None):
            self.suffixes.add(key.rsplit(".", 1)[-1])
            return True

    policy = _Recorder()
    simulate_duel(DuelRequest(slayer, second, 3000, seed=11, batch_size=3000,
                              decision_policy=policy), backend="native")
    assert "deathblow" in policy.suffixes


def test_the_impetuous_charge_offers_its_release():
    first, second = _pair()
    charging = DuelContext(charging=("first",), active_participant="first")
    dice, policy = _Dice(), _Policy()
    native.simulate_batch_observed(
        _tagged(first, "condition.impetuous-charge"), second, 1, dice, 1, policy,
        context=charging)
    assert "round.0.first.impetuous-avoid-compulsion" in policy.keys
    # Accepting the offer runs a Leadership test, which costs two dice the
    # uncompelled warrior never spends.
    declined = _Dice()
    native.simulate_batch_observed(
        _tagged(first, "condition.impetuous-charge"), second, 1, declined, 1,
        _Policy(**{"impetuous-avoid-compulsion": False}), context=charging)
    assert len(dice.log) == len(declined.log) + 2


def test_an_inconsistency_profile_redraws_its_value_every_round():
    first, second = _pair()
    variable = replace(first, random_characteristics=(("S", 1, 6, 0),))
    lazy = _run(_tagged(variable, "mechanic.inconsistency"), second, rounds=2)
    eager = _run(variable, second, rounds=2)
    # The lazy profile draws its Strength once per round; the eager one rolls
    # it at duel start and keeps it.
    assert len(lazy[1].log) == len(eager[1].log) + 1


def test_a_variable_characteristic_is_drawn_only_when_something_reads_it():
    """``require_characteristics`` draws at the operation that reads the
    value, so a characteristic no operation reads costs no die at all."""
    first, second = _pair()
    unread = _tagged(replace(first, random_characteristics=(("I", 1, 6, 0),)),
                     "mechanic.inconsistency")
    read = _tagged(replace(first, random_characteristics=(("S", 1, 6, 0),)),
                   "mechanic.inconsistency")
    plain = _run(first, second)
    # A plain exchange reads Strength at the wound step and never reads the
    # variable Initiative, so only the Strength profile pays for a draw.
    assert len(_run(unread, second)[1].log) == len(plain[1].log)
    assert len(_run(read, second)[1].log) == len(plain[1].log) + 1


def test_the_electrical_forfeit_offers_each_allocated_attack_in_turn():
    first, second = _pair()
    bearer = _tagged(replace(first, characteristics=replace(
        first.characteristics, attacks=3)), "mechanic.electrical-touch")
    prefix = "round.0.first.electrical-touch.forfeit."
    # The first accepted index is the blow the jolt replaces, so the search
    # stops there.
    accepted = _run(bearer, second)[2].keys
    assert [k for k in accepted if "electrical" in k] == [prefix + "0"]
    # Declining walks on to the next allocated attack.
    declined = _run(bearer, second,
                    policy=_Policy(**{"forfeit.0": False}))[2].keys
    assert [k for k in declined if "electrical" in k] == [prefix + "0", prefix + "1"]


def test_an_accepted_forfeit_leaves_the_pool_and_the_jolt_recharges():
    first, second = _pair()
    bearer = _tagged(replace(first, characteristics=replace(
        first.characteristics, attacks=3)), "mechanic.electrical-touch")
    refused = _Policy(**{"forfeit.0": False, "forfeit.1": False, "forfeit.2": False})
    whole = _run(bearer, second, policy=refused)
    jolting = _run(bearer, second)
    # Three blows and a reply when every offer is refused; accepting costs
    # the pool one blow and spends the jolt's own recharge die instead.
    assert len(whole[1].log) == 4
    assert len(jolting[1].log) == 5

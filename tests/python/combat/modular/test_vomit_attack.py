"""L02: canonical optional Vomit Attack and whole-pool replacement witnesses.

The Warpstone Troll source (Underworld Alliance, p. 5) specifies one automatic
S5 hit instead of normal attacks, ignoring armour. The maintained mechanic
also makes the automatic hit unparryable. Synthetic loadout compositions below
test the operator, and do not assert canonical access to those weapons/skills.
"""
from dataclasses import replace

import numpy as np
import pytest

from mordheim_combat.kernel import compile_duel_plan
from mordheim_combat.modular.pools import _resolve_attack_pool
from mordheim_combat.modular.rounds import resolve_round, select_attack_replacement
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat.native._combat_compile import compile_duel
from mordheim_combat.vectorized import simulate_batch, simulate_duel, simulate_duel_parallel
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, DuelRequest, EffectSet, FighterBuild


RULE = "warpstone-troll--vomit-attack"


def troll(selected=True):
    return compile_fighter(FighterBuild(
        "mordheim", band_id="underworld-alliance-mim", profile_id="warpstone-troll",
        special_rule_ids=(RULE,) if selected else (),
    ))


def opponent(**options):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 4, 1, 1),
        main_weapon_id="weapon.sword", off_hand_id="defence.buckler",
        armour_id="armour.gromril-armour", **options,
    ))


def roll(key, value=1):
    return {"key": key, "value": value}


def choice(key, value=True):
    return {"key": key, "value": value}


def run(first, second, rolls, choices, state=None):
    # Vomit witnesses assume the active Troll passed its mandatory Psychology
    # test. Keep that canonical prerequisite explicit in the strict request tape.
    if state is None and "mechanic.stupidity" in first.global_effects.tags and not first.global_effects.frenzy:
        rolls[:0] = [roll("round.0.first.stupidity.0"), roll("round.0.first.stupidity.1")]
    dice, decisions = StrictDice(rolls), StrictDecisions(choices)
    if state is None:
        state = initialize_duel(first, second, dice, context=DuelContext(
            charging=(), active_participant="first",
        ))
    result = resolve_round(first, second, state, dice, decisions)
    dice.finish()
    decisions.finish()
    return result, [request.key for request in dice.requests]


def test_canonical_selection_retains_normal_weapon_and_compiles_separate_option():
    selected, absent = troll(), troll(False)
    assert selected.main_weapon == absent.main_weapon
    assert selected.global_effects == absent.global_effects
    assert absent.vomit_attack is None
    assert selected.vomit_attack == EffectSet(
        tags=("weapon.vomit-attack",), cannot_be_parried=True, ignore_armour=True,
        fixed_strength=5, automatic_hit=True,
    )


@pytest.mark.parametrize("selected,accept,count", [(True, True, 1), (True, False, 4), (False, False, 4)])
def test_real_round_replacement_and_ordinary_controls(selected, accept, count):
    first, second = troll(selected), opponent()
    rolls = ([roll("round.0.first.attack.0.wound", 2)] if accept else
             [roll(f"round.0.first.attack.{i}.hit") for i in range(4)])
    rolls += [roll("round.0.second.attack.0.hit")]
    choices = [choice("round.0.first.vomit-attack", accept)] if selected else []
    result, requests = run(first, second, rolls, choices)
    assert len(result.attacks) == count + 1
    assert result.state.second.wounds == (3 if accept else 4)
    assert requests == [entry["key"] for entry in rolls]
    if accept:
        hit = result.attacks[0]
        assert hit.hit and hit.wounded and not hit.parried and not hit.saved
        assert not hit.natural_hit_six


def test_replacement_is_a_fresh_choice_each_round_not_a_permanent_weapon_change():
    first, second = troll(), opponent()
    initial, _ = run(first, second,
        [roll("round.0.first.attack.0.wound"), roll("round.0.second.attack.0.hit")],
        [choice("round.0.first.vomit-attack")])
    later, _ = run(first, second,
        [*[roll(f"round.1.first.attack.{i}.hit") for i in range(4)],
         roll("round.1.second.attack.0.hit")],
        [choice("round.1.first.vomit-attack", False)], initial.state)
    assert len(initial.attacks) == 2 and len(later.attacks) == 5


def test_second_participant_has_its_own_decision_and_dice_keys():
    result, requests = run(opponent(), troll(),
        [roll("round.0.second.attack.0.wound"), roll("round.0.first.attack.0.hit")],
        [choice("round.0.second.vomit-attack")])
    assert requests[0] == "round.0.second.attack.0.wound"
    assert len(result.attacks) == 2


@pytest.mark.parametrize("save,face,saved", [("ward_save", 6, True), ("ward_save", 5, False),
                                            ("regeneration_save", 4, True), ("regeneration_save", 3, False)])
def test_armour_denial_keeps_independent_special_saves(save, face, saved):
    first, second = troll(), opponent(trait_overrides={save: 6 if save == "ward_save" else 4})
    result, _ = run(first, second,
        [roll("round.0.first.attack.0.wound", 2),
         roll(f"round.0.first.attack.0.special.{save.removesuffix('_save')}", face),
         roll("round.0.second.attack.0.hit")],
        [choice("round.0.first.vomit-attack")])
    assert result.attacks[0].saved is saved
    assert result.state.second.wounds == (4 if saved else 3)


@pytest.mark.parametrize("direct", [False, True])
def test_vomit_suppresses_other_hands_natural_attacks_and_charge_replacements(direct):
    # Deliberately synthetic composition: no claim that a Warpstone Troll can
    # buy these skills/items. Both the new option and legacy explicit weapon
    # must replace the whole normal pool without asking competing decisions.
    first, second = troll(), opponent()
    poison_weapon = EffectSet(tags=("weapon.whip", "poison.black-lotus"), fixed_strength=9)
    first = replace(first, off_hand=poison_weapon, off_hand_attacks=True,
                    extra_attacks=(poison_weapon,), global_effects=replace(first.global_effects,
                    frenzy=True, tags=(*first.global_effects.tags, "mechanic.bull-charge", "mechanic.body-slam")))
    decisions = StrictDecisions([] if direct else [choice("select.vomit-attack")])
    if direct:
        first = replace(first, main_weapon=first.vomit_attack, vomit_attack=None)
    else:
        first = select_attack_replacement(first, first_round=True, charging=True,
                                         decisions=decisions, key="select")
    dice = StrictDice([roll("pool.attack.0.wound", 2)])
    _, defender, outcomes = _resolve_attack_pool(first, second,
        initialize_fighter(first, dice, key="first"), initialize_fighter(second, dice, key="second"),
        1, dice, key="pool", first_round=True, charging=True, decisions=decisions)
    dice.finish()
    decisions.finish()
    assert len(outcomes) == 1 and defender.wounds == 3


@pytest.mark.parametrize("backend", ["auto", "numpy", "native"])
def test_unported_option_is_refused_before_optimized_execution(backend):
    with pytest.raises(ValueError, match="optional Vomit Attack.*modular"):
        simulate_duel(DuelRequest(troll(), opponent(), simulations=1), backend=backend)


def test_low_level_optimized_entries_do_not_silently_drop_the_option():
    first, second = troll(), opponent()
    for call in (lambda: compile_duel_plan(first, second), lambda: compile_duel(first, second),
                 lambda: simulate_batch(first, second, 1, np.random.default_rng(0), 1),
                 lambda: simulate_duel_parallel(DuelRequest(first, second, simulations=1))):
        with pytest.raises(ValueError, match="optional Vomit Attack.*modular"):
            call()

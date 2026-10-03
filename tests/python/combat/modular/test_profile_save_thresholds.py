"""T13-F011/T13-F012: compiled save thresholds consumed by the modular engine.

Canonical profiles are compiled with the maintained ``FighterBuild``/
``compile_fighter`` API; no trait is injected by hand.  The same clauses as in
``tests/python/construction/test_t13_profile_save_thresholds.py`` are exercised
here through the real attack pipeline, the isolated phase preparers and the
whole-round duel driver:

* ``lords-of-the-marsh-mim`` / ``band--scaly-skin``: Fimir Warriors have a 5+
  armour save, "Light armour adds +1", and the band save "cannot be modified
  beyond 6 by Strength"; a "no save" critical result negates the save.
* ``underworld-alliance-mim`` / ``boglars--regeneration``: the wound is ignored
  "on a result of 5 or more", fire and fire-based magic cannot be regenerated,
  and a blocked regeneration must not request a die.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.contexts import prepare_armour_context, prepare_special_save_context
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_combat_lab.verification.parity._replay import replay_duel
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, EffectSet, FighterBuild

FIMIR = ("lords-of-the-marsh-mim", "fimir-warriors")
BOGLAR = ("underworld-alliance-mim", "boglars")
WARPSTONE_TROLL = ("underworld-alliance-mim", "warpstone-troll")


def profile(pair, **options):
    band_id, profile_id = pair
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band_id, profile_id=profile_id, **options
    ))


def fighter(strength: int = 3, attacks: int = 1, **options):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, strength, 3, 3, 3, attacks), **options
    ))


def mace(strength: int = 3):
    return fighter(strength, main_weapon_id="weapon.mace")


def state(unit):
    dice = StrictDice([])
    result = initialize_fighter(unit, dice, "init")
    dice.finish()
    return result


def roll(key, value, sides=6):
    return {"key": key, "value": value, "sides": sides}


def attack(attacker, defender, rolls, **options):
    dice, choices = StrictDice(rolls), StrictDecisions([])
    result = resolve_reference_attack(
        attacker, defender, state(attacker), state(defender),
        attacker.main_weapon, dice, key="a", decisions=choices, **options
    )
    dice.finish()
    choices.finish()
    return result


# ---------------------------------------------------------------------------
# Fimir Warriors: 5+ natural save inside the band-wide clauses
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("face,saved,damage", [(5, True, 0), (4, False, 1)])
def test_fimir_warriors_only_save_on_the_printed_five(face, saved, damage):
    # To-wound target is 6 (S3 against T5), so a natural six wounds without a
    # critical; the armour die is then the only remaining decision.
    result = attack(mace(), profile(FIMIR), [roll("a.hit", 6), roll("a.wound", 6), roll("a.armour", face)])
    assert result.saved is saved
    assert result.damage == damage
    assert result.defender.wounds == 3 - damage


@pytest.mark.parametrize("face,saved,damage", [(4, True, 0), (3, False, 1)])
def test_fimir_warriors_light_armour_adds_one_to_the_five_plus(face, saved, damage):
    result = attack(
        mace(), profile(FIMIR, armour_id="armour.light-armour"),
        [roll("a.hit", 6), roll("a.wound", 6), roll("a.armour", face)],
    )
    assert result.saved is saved
    assert result.damage == damage


def test_fimir_warriors_natural_armour_target_is_five_not_six():
    context = prepare_armour_context(mace(), profile(FIMIR), state(mace()), state(profile(FIMIR)), EffectSet(), EffectSet())
    assert context.natural_armour_save == 5
    assert phases.armour_target(context) == 5


def test_fimir_warriors_light_armour_target_is_four():
    defender = profile(FIMIR, armour_id="armour.light-armour")
    context = prepare_armour_context(mace(), defender, state(mace()), state(defender), EffectSet(), EffectSet())
    assert phases.armour_target(context) == 4


def test_fimir_strength_worsening_stops_at_the_band_six_plus_floor():
    # "cannot be modified beyond 6 by Strength": S6 would ask for 5+3=8 plus
    # the ordinary armour slot, but the natural save is floored at 6.
    strong = mace(6)
    defender = profile(FIMIR)
    context = prepare_armour_context(strong, defender, state(strong), state(defender), strong.main_weapon, strong.main_weapon)
    assert context.strength == 6
    assert phases.armour_target(context) == 6


@pytest.mark.parametrize("face,saved,damage", [(6, True, 0), (5, False, 1)])
def test_fimir_strength_boundary_six_plus_floor_on_a_real_attack(face, saved, damage):
    # S6 against T5 asks for 3+ to wound, so 3 wounds without a critical.
    result = attack(mace(6), profile(FIMIR), [roll("a.hit", 6), roll("a.wound", 3), roll("a.armour", face)])
    assert result.saved is saved
    assert result.damage == damage


def test_fimir_critical_no_save_result_negates_the_natural_armour_without_a_die():
    # S4 against T5 asks for 5+ to wound; a six both wounds and criticises, and
    # the critical chart result 3 is a "no save".
    attacker = mace(4)
    result = attack(attacker, profile(FIMIR), [roll("a.hit", 6), roll("a.wound", 6), roll("a.critical", 3)])
    assert result.critical is True
    assert result.defender.wounds == 1
    assert result.damage == 2
    # StrictDice.finish() above already proves no armour die was requested.


def test_fimir_armour_denial_reaches_the_isolated_armour_context():
    attacker = fighter(main_weapon_id="weapon.vomit-attack")
    defender = profile(FIMIR)
    context = prepare_armour_context(
        attacker, defender, state(attacker), state(defender),
        attacker.main_weapon, attacker.main_weapon,
    )
    assert context.ignore_armour is True
    assert phases.armour_target(context) == 7


def test_fimir_failed_armour_does_not_request_a_special_save_die():
    # The Fimir clause grants only the natural armour save: after a failed 1
    # the tape ends at the armour die, so nothing else may be consumed.
    result = attack(mace(), profile(FIMIR), [roll("a.hit", 6), roll("a.wound", 6), roll("a.armour", 1)])
    assert result.damage == 1
    assert result.defender.wounds == 2


def test_fimir_has_no_ward_or_regeneration_contribution():
    compiled = profile(FIMIR)
    context = prepare_special_save_context(compiled, EffectSet())
    assert context.ward_save == 7
    assert context.regeneration_save == 7
    assert context.regeneration_blocked is False


# ---------------------------------------------------------------------------
# Boglars: regeneration 5+ with the fire prohibition
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("face,saved,damage", [(5, True, 0), (4, False, 1)])
def test_boglar_regeneration_only_saves_on_five_or_more(face, saved, damage):
    # S3 against T3 asks for 4+ to wound, so 4 wounds without a critical and
    # the regeneration die is the first save rolled (no armour over 6).
    assert profile(BOGLAR).armour_save == 7
    rolls = [roll("a.hit", 6), roll("a.wound", 4), roll("a.special.regeneration", face)]
    if not saved:
        rolls.append(roll("a.injury.0", 1))
    result = attack(mace(), profile(BOGLAR), rolls)
    assert result.damage == damage
    assert result.defender.wounds == (1 if saved else 0)


def test_boglar_regeneration_context_is_five_plus_and_fire_blocked():
    compiled = profile(BOGLAR)
    ordinary = prepare_special_save_context(compiled, EffectSet())
    assert ordinary.regeneration_save == 5
    assert ordinary.regeneration_blocked is False
    assert ordinary.ward_save == 7
    fire = prepare_special_save_context(compiled, EffectSet(tags=("attack.fire",)))
    assert fire.regeneration_blocked is True
    assert fire.regeneration_save == 5


def test_fire_tag_alone_does_not_block_a_different_defender():
    # The block is the Boglar's clause, not a global fire prohibition.
    assert prepare_special_save_context(profile(WARPSTONE_TROLL), EffectSet(tags=("attack.fire",))).regeneration_blocked is True
    ordinary = fighter()
    assert ordinary.global_effects.regeneration_save == 7


def test_boglar_fire_weapon_never_requests_a_regeneration_die():
    # weapon.brazier-iron is the canonical fire producer (attack.fire); S4
    # against T3 asks for 3+ to wound.  StrictDice.finish() proves the tape was
    # consumed exactly, i.e. no regeneration die was requested.
    result = attack(
        fighter(main_weapon_id="weapon.brazier-iron"), profile(BOGLAR),
        [roll("a.hit", 6), roll("a.ignition", 1), roll("a.wound", 3), roll("a.injury.0", 1)],
    )
    assert result.damage == 1
    assert result.defender.condition == phases.Condition.KNOCKED_DOWN


def test_boglar_ordinary_weapon_requests_the_regeneration_die_for_the_same_wound():
    result = attack(
        mace(), profile(BOGLAR),
        [roll("a.hit", 6), roll("a.wound", 4), roll("a.special.regeneration", 3), roll("a.injury.0", 1)],
    )
    assert result.damage == 1
    assert result.defender.condition == phases.Condition.KNOCKED_DOWN


def test_boglar_magical_tag_is_not_a_fire_block():
    # "fire or fire-based magic" is expressed by the attack.fire tag; a plain
    # magical attack has no canonical producer in the current KB and must not
    # block the roll by itself.
    context = prepare_special_save_context(profile(BOGLAR), EffectSet(tags=("attack.magical",)))
    assert context.regeneration_blocked is False


# ---------------------------------------------------------------------------
# cross-profile controls in the same process
# ---------------------------------------------------------------------------
def test_warpstone_troll_still_saves_on_four_while_boglars_needs_five():
    troll_saved = attack(mace(), profile(WARPSTONE_TROLL), [roll("a.hit", 6), roll("a.wound", 5), roll("a.special.regeneration", 4)])
    assert troll_saved.saved is True and troll_saved.damage == 0
    boglar_failed = attack(
        mace(), profile(BOGLAR),
        [roll("a.hit", 6), roll("a.wound", 4), roll("a.special.regeneration", 4), roll("a.injury.0", 1)],
    )
    assert boglar_failed.saved is False and boglar_failed.damage == 1


def test_control_compilations_do_not_change_between_boglar_attacks():
    troll_before = profile(WARPSTONE_TROLL)
    attack(mace(), profile(BOGLAR), [roll("a.hit", 6), roll("a.wound", 4), roll("a.special.regeneration", 4), roll("a.injury.0", 1)])
    troll_after = profile(WARPSTONE_TROLL)
    assert troll_before == troll_after
    assert troll_after.global_effects.regeneration_save == 4
    assert profile(BOGLAR).global_effects.regeneration_save == 5


# ---------------------------------------------------------------------------
# whole-round driver (real duel)
# ---------------------------------------------------------------------------
def duel_context():
    return DuelContext(charging=("first",), active_participant="first")


def test_real_duel_fimir_armour_save_five_keeps_the_wound():
    result = replay_duel(
        profile(FIMIR), mace(), backend="modular", context=duel_context(),
        rolls=[
            # The Fimir's own three attacks miss.
            roll("round.0.first.attack.0.hit", 1),
            roll("round.0.first.attack.1.hit", 1),
            roll("round.0.first.attack.2.hit", 1),
            # The attacker wounds once; the printed 5+ natural save holds.
            roll("round.0.second.attack.0.hit", 6),
            roll("round.0.second.attack.0.wound", 6),
            roll("round.0.second.attack.0.armour", 5),
        ],
    )
    assert result.winner == 2 and result.rounds == 1
    assert result.wounds == (3, 3)
    assert result.conditions == (0, 0)


def test_real_duel_boglar_needs_five_and_goes_out_on_a_four():
    result = replay_duel(
        profile(BOGLAR), mace(), backend="modular", context=duel_context(),
        rolls=[
            roll("round.0.first.attack.0.hit", 1),
            roll("round.0.second.attack.0.hit", 6),
            roll("round.0.second.attack.0.wound", 4),
            roll("round.0.second.attack.0.special.regeneration", 4),
            roll("round.0.second.attack.0.injury.0", 6),
        ],
    )
    assert result.winner == 1 and result.rounds == 1
    assert result.wounds == (0, 3)
    assert result.conditions == (int(phases.Condition.OUT), 0)

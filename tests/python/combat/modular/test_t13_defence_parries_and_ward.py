"""T13 M3 (defences): parry skills, the Ranald duck and natural-armour provenance.

The two parry skills are selectable members of the Karak Azgal special skill
tables (``adventurers-kaz``); the Trickster-Priest's Marks of Ranald is a
grade-2b hired-sword rule.  Every fighter is compiled through the maintained
``FighterBuild`` API, and each assertion reads a real attack or the shared phase
preparers.  The cases discriminate the wrong interpretation (a parry granted to
any weapon, a re-roll granted without a sword or buckler, a Strength cap that
also swallows the printed Cutting Edge exception, a fire attack that negates
more than the hide save, or a duck that resolves after the critical) instead of
a compiled metadata field.
"""
from __future__ import annotations

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.contexts import (
    _combined_effect, _injury_context, _parry_context, prepare_armour_context,
    prepare_special_save_context,
)
from mordheim_combat.modular.state import _parry_capacity, initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, EffectSet, FighterBuild

MARKS = "hireling.hired-sword.trickster-priest-of-ranald.rule.marks-of-ranald"
WHITE_TOWER = ("skill.chosen-of-the-white-tower",)
DOUBLE_HANDED = ("skill.instinctive-warrior",)
TRICKSTER = "hireling.hired-sword.trickster-priest-of-ranald"


def canonical(band, profile, weapon, **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=profile, main_weapon_id=weapon, **options))


def bare(band, profile, **options):
    """A profile the equipment lists leave unequippable, compiled with its own kit."""
    return compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile, **options))


def attacker(strength=3, weapon="weapon.mace"):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, strength, 3, 2, 3, 1, leadership=7),
        main_weapon_id=weapon))


def trickster(**options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id="hirelings.hired-sword.2b", profile_id=TRICKSTER, **options))


def state(unit):
    dice = StrictDice([])
    result = initialize_fighter(unit, dice, "init")
    dice.finish()
    return result


def strike(atk, dfn, rolls):
    init = StrictDice([])
    first, second = initialize_fighter(atk, init, "a"), initialize_fighter(dfn, init, "d")
    init.finish()
    dice = StrictDice([{"key": "x." + key, "value": value} for key, value in rolls])
    result = resolve_reference_attack(atk, dfn, first, second, atk.main_weapon, dice, key="x")
    dice.finish()
    return result


# ---------------------------------------------------------------------------
# Chosen of the White Tower: parry without a buckler or a sword, and re-roll
# that parry once the Elf is armed with a parrying weapon.
# ---------------------------------------------------------------------------
def test_chosen_of_the_white_tower_parries_without_a_parrying_weapon():
    elf = canonical("adventurers-kaz", "elf", "weapon.dagger", skill_ids=WHITE_TOWER)
    assert _parry_capacity(elf) == 1
    assert strike(attacker(), elf, [("hit", 4), ("parry", 5)]).parried


def test_an_unchosen_elf_gets_no_parry_from_the_shared_skill_table():
    plain = canonical("adventurers-kaz", "elf", "weapon.dagger")
    assert _parry_capacity(plain) == 0


def test_chosen_of_the_white_tower_rerolls_only_a_sword_or_buckler_parry():
    unarmed = canonical("adventurers-kaz", "elf", "weapon.dagger", skill_ids=WHITE_TOWER)
    armed = canonical("adventurers-kaz", "elf", "weapon.sword", skill_ids=WHITE_TOWER)
    assert _parry_context(unarmed, state(unarmed), unarmed.main_weapon, 3, 4, "p").reroll is False
    assert _parry_context(armed, state(armed), armed.main_weapon, 3, 4, "p").reroll is True
    # A buckler is the other printed arming; it parries from the off hand even
    # though the main hand does not.
    buckler = canonical("adventurers-kaz", "elf", "weapon.dagger",
                        off_hand_id="defence.buckler", skill_ids=WHITE_TOWER)
    assert _parry_capacity(buckler) == 1
    assert _parry_context(buckler, state(buckler), buckler.main_weapon, 3, 4, "p").reroll is True


def test_chosen_of_the_white_tower_grants_no_reroll_to_another_parrying_weapon():
    # The skill still grants the parry itself, but its own re-roll is printed
    # only "if he is already armed in that way": a trident is a parrying weapon
    # that is neither a sword nor a buckler, so it parries without the Chosen
    # re-roll.  An independent motive (e.g. fighting-claws) is a different
    # reason and is deliberately not exercised as the same thing here.
    trident = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 3, 3, 1, leadership=7),
        main_weapon_id="weapon.trident", skill_ids=WHITE_TOWER))
    assert trident.main_weapon.parry and _parry_capacity(trident) == 1
    assert _parry_context(trident, state(trident), trident.main_weapon, 3, 4, "p").reroll is False


def test_miniath_reroll_is_independent_of_the_chosen_skill():
    # Miniath (the canonical Lustria/High Elf band rule) keeps its own motive (a
    # native parrying weapon) and is not disturbed by separating the Chosen
    # re-roll out of the shared expression: the sword re-rolls, the non-parrying
    # dagger does not, while both still get the parry itself.
    sword = canonical("high-elves-lus", "loremaster", "weapon.sword",
                      special_rule_ids=("band--skill-miniath",))
    assert _parry_context(sword, state(sword), sword.main_weapon, 3, 4, "p").reroll is True
    dagger = canonical("high-elves-lus", "loremaster", "weapon.dagger",
                       special_rule_ids=("band--skill-miniath",))
    assert _parry_capacity(dagger) == 1
    assert _parry_context(dagger, state(dagger), dagger.main_weapon, 3, 4, "p").reroll is False


# ---------------------------------------------------------------------------
# Instinctive Warrior: the double-handed weapon parries as an ordinary sword
# rather than becoming a parry with any weapon.
# ---------------------------------------------------------------------------
def test_instinctive_warrior_parries_with_the_double_handed_weapon():
    barbarian = canonical(
        "adventurers-kaz", "barbarian", "weapon.double-handed-weapon", skill_ids=DOUBLE_HANDED)
    assert _parry_capacity(barbarian) == 1
    assert strike(attacker(), barbarian, [("hit", 4), ("parry", 5)]).parried


def test_instinctive_warrior_grants_nothing_to_a_one_handed_weapon():
    dagger = canonical("adventurers-kaz", "barbarian", "weapon.dagger", skill_ids=DOUBLE_HANDED)
    assert _parry_capacity(dagger) == 0


def test_a_double_handed_weapon_alone_does_not_parry():
    plain = canonical("adventurers-kaz", "barbarian", "weapon.double-handed-weapon")
    assert _parry_capacity(plain) == 0


def test_instinctive_warrior_keeps_the_ordinary_sword_parry_without_a_reroll():
    barbarian = canonical(
        "adventurers-kaz", "barbarian", "weapon.double-handed-weapon", skill_ids=DOUBLE_HANDED)
    context = _parry_context(barbarian, state(barbarian), barbarian.main_weapon, 3, 4, "p")
    assert context.reroll is False


# ---------------------------------------------------------------------------
# Marks of Ranald: an unmodifiable 6+ duck past any hit, magic included, rolled
# before critical hit effects are determined and never repeated as a ward save.
# ---------------------------------------------------------------------------
def test_trickster_priest_ducks_hits_on_six():
    assert strike(attacker(), trickster(special_rule_ids=(MARKS,)),
                  [("hit", 6), ("marks-of-ranald", 6)]).saved


def test_trickster_priest_without_the_mark_has_no_save():
    assert prepare_special_save_context(trickster(), EffectSet()).ward_save == 7


def test_trickster_priest_duck_precedes_the_wound_and_the_critical():
    # The duck intercepts a landed hit before the To Wound roll, so no wound die
    # (and therefore no critical) is ever requested.  ``strike`` calls
    # StrictDice.finish(), so any stray wound/critical digit would fail here.
    result = strike(attacker(), trickster(special_rule_ids=(MARKS,)),
                    [("hit", 6), ("marks-of-ranald", 6)])
    assert result.saved is True
    assert result.wounded is False and result.damage == 0
    assert result.attacker.critical_available is True


def test_trickster_priest_duck_consumes_no_resource_and_leaves_no_second_save():
    priest = trickster(special_rule_ids=(MARKS,))
    result = strike(attacker(), priest, [("hit", 6), ("marks-of-ranald", 6)])
    assert result.defender.resources_spent == state(priest).resources_spent
    # The ability resolves exactly once, at the hit stage; it must not also
    # remain live as a ward save rolled after the critical (the defect this
    # case pins): the shared special-save context exposes no 6+ save.
    assert prepare_special_save_context(priest, EffectSet()).ward_save == 7


def test_trickster_priest_failing_duck_falls_through_to_the_wound_chain():
    result = strike(attacker(), trickster(special_rule_ids=(MARKS,)),
                    [("hit", 4), ("marks-of-ranald", 5), ("wound", 4), ("injury.0", 1)])
    assert result.saved is False and result.damage == 1
    assert result.defender.wounds == 0


def test_trickster_priest_duck_is_unmodified_by_magical_attacks():
    # The printed clause covers every source "including magical attacks"; the
    # hellblade is the canonical magical producer and ducks exactly as usual.
    result = strike(attacker(weapon="weapon.hellblade"),
                    trickster(special_rule_ids=(MARKS,)),
                    [("hit", 6), ("marks-of-ranald", 6)])
    assert result.saved is True and result.damage == 0


# ---------------------------------------------------------------------------
# Natural-armour provenance rules: an inherent save that Strength cannot
# worsen, one that ignores Strength entirely, and one a magical blow skips.
# ---------------------------------------------------------------------------
def armour(attacker_strength, defender, weapon="weapon.mace", incoming=None):
    atk = attacker(attacker_strength, weapon)
    # The combined effect carries the weapon's own armour penetration and target
    # bonus, exactly as the real attack pipeline computes them.
    effect = incoming or _combined_effect(atk, atk.main_weapon)
    context = prepare_armour_context(
        atk, defender, state(atk), state(defender), atk.main_weapon, effect)
    return phases.armour_target(context), context


def test_fen_guard_bark_skin_caps_the_strength_penalty_at_six():
    dryads = canonical("fen-guard-mim", "dryads", "weapon.mace")
    assert armour(3, dryads)[0] == 6
    # The printed cap: a Strength 6 blow would otherwise ask for 7 (no save).
    assert armour(6, dryads)[0] == 6


def test_fen_guard_bark_skin_cutting_edge_is_exempt_from_the_strength_cap():
    dryads = canonical("fen-guard-mim", "dryads", "weapon.mace")
    # The printed exception ("except by weapons with the Cutting Edge rule"):
    # an armour-penetrating weapon still worsens the hide save past 6, so the
    # worst-save cap swallows only the Strength penalty, not the penetration.
    assert armour(3, dryads, "weapon.axe")[0] == 7
    assert armour(6, dryads, "weapon.axe")[0] == 7


def test_fen_guard_bark_skin_cutting_edge_denies_the_die_on_a_real_attack():
    dryads = canonical("fen-guard-mim", "dryads", "weapon.mace")
    # The same Strength 6 attack: the capped mace still asks for a 6+ hide die
    # and holds on a six...
    mace = strike(attacker(6), dryads, [("hit", 6), ("wound", 3), ("armour", 6)])
    assert mace.saved is True and mace.damage == 0
    # ...while the Cutting Edge exception denies the save outright, so no armour
    # die appears in the tape (StrictDice.finish() would fail otherwise).
    axe = strike(attacker(6, "weapon.axe"), dryads,
                 [("hit", 6), ("wound", 3), ("injury.0", 1)])
    assert axe.saved is False and axe.damage == 1


def test_fen_guard_bark_skin_fire_ignores_only_the_hide_save():
    dryads = canonical("fen-guard-mim", "dryads", "weapon.mace")
    assert armour(3, dryads)[0] == 6
    assert armour(3, dryads, incoming=EffectSet(tags=("attack.fire",)))[0] == 7
    # The clause denies the inherent hide save, not armour globally: another
    # band's natural armour is untouched by the same fire attack.
    fimir = canonical("lords-of-the-marsh-mim", "fimir-warriors", "weapon.mace")
    assert armour(3, fimir, incoming=EffectSet(tags=("attack.fire",)))[0] == 5


def test_fen_guard_bark_skin_fire_weapon_denies_the_die_on_a_real_attack():
    dryads = canonical("fen-guard-mim", "dryads", "weapon.mace")
    # brazier-iron is the canonical fire producer; the 6+ hide die is skipped
    # entirely, so the tape runs hit -> ignition -> wound -> injury.
    result = strike(attacker(4, "weapon.brazier-iron"), dryads,
                    [("hit", 6), ("ignition", 1), ("wound", 3), ("injury.0", 1)])
    assert result.saved is False and result.damage == 1


def test_halfling_layers_of_fat_ignores_enemy_strength():
    elder = canonical("halflings-mic", "halfling-elder", "weapon.mace")
    target, context = armour(6, elder)
    assert context.natural_armour_unmodified is True
    assert target == 6


def test_companion_filly_odd_covering_is_a_five_plus_save_negated_by_magic():
    filly = bare("order-of-the-mare-web", "companion-filly")
    mundane, context = armour(6, filly)
    assert (context.natural_armour_save, context.natural_armour_unmodified) == (5, True)
    assert context.natural_armour_negated_by_magic is True
    assert mundane == 5
    assert armour(6, filly, incoming=EffectSet(tags=("attack.magical",)))[0] == 7


def test_companion_filly_covering_matches_the_dame_precedent():
    dame = bare("order-of-the-mare-web", "dame-of-the-mare")
    target, context = armour(6, dame)
    assert (context.natural_armour_save, target) == (5, 5)


# ---------------------------------------------------------------------------
# Connections to existing defence operators: the pending step was the
# construction data that routes the printed item/note, not new behaviour.
# ---------------------------------------------------------------------------
def test_silent_brotherhood_cloak_is_the_buckler_item_it_names():
    master = bare("silent-brotherhood-sc", "silent-master", off_hand_id="defence.buckler")
    assert _parry_capacity(master) == 1
    assert _parry_capacity(bare("silent-brotherhood-sc", "silent-master")) == 0
    # A profile the equipment list does not give the cloak to stays refused.
    with pytest.raises(ValueError, match="not available"):
        bare("silent-brotherhood-sc", "thugs", off_hand_id="defence.buckler")


def test_snerik_short_sword_is_the_kb_sword_item():
    snerik = bare("hirelings.dramatis-personae.2b", "hireling.dramatis.snerik-night-goblin-scout")
    assert _parry_capacity(snerik) == 0
    sword = bare("hirelings.dramatis-personae.2b", "hireling.dramatis.snerik-night-goblin-scout",
                 main_weapon_id="weapon.sword")
    assert sword.main_weapon.parry and _parry_capacity(sword) == 1


def test_trident_parry_payload_is_consumed():
    trident = attacker(weapon="weapon.trident")
    assert trident.main_weapon.parry and _parry_capacity(trident) == 1


def test_white_wolf_pelt_resolves_to_the_six_plus_saving_throw():
    priest = bare("hirelings.hired-sword.2b",
                  "hireling.hired-sword.wolf-priest-of-ulric-miracle-workers")
    assert priest.armour_save == 6
    assert "defence.wolf-pelt-cloak" in priest.global_effects.tags


def test_pristekk_shock_rod_is_consumed_as_a_shock_weapon():
    chieftain = bare("skaven-of-clan-pristekk-sc", "chieftain", main_weapon_id="weapon.shock-rod")
    assert _injury_context(chieftain, chieftain.main_weapon, "i").shock is True

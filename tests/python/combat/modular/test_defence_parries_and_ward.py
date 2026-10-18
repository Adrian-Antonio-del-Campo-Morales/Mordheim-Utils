"""Defence parries and ward: parry skills, the Ranald duck and natural-armour provenance.

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
from dataclasses import replace

from mordheim_combat import phases
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.contexts import (
    _combined_effect, _injury_context, _parry_context, prepare_armour_context,
    prepare_special_save_context, _hit_reroll,
)
from mordheim_combat.modular.state import _parry_capacity, initialize_fighter
from mordheim_combat.modular.pools import _resolve_attack_pool, _resolve_prepared_defences
from mordheim_combat.modular.contexts import OwnedRollDice, prepare_hit_context
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_core.dice import RollRequest
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


# Chosen of the White Tower: parry without a buckler or a sword, and re-roll
# that parry once the Elf is armed with a parrying weapon.
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


# Instinctive Warrior: the double-handed weapon parries as an ordinary sword
# rather than becoming a parry with any weapon.
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


# Marks of Ranald: an unmodifiable 6+ duck past any hit, magic included, rolled
# before critical hit effects are determined and never repeated as a ward save.
# Dwarfs printed Parry: two Dwarf axes, or a Dwarf axe with a sword in either
# hand order, give up the second parry and gain a single failed-parry reroll.
# Two ordinary swords keep no reroll, and the parry limit stays at one.
def test_two_dwarf_axes_re_roll_a_failed_parry():
    axes = bare("dwarf-slayers-kaz", "slayers", main_weapon_id="weapon.dwarf-axe",
                off_hand_id="weapon.dwarf-axe")
    assert _parry_capacity(axes) == 1
    assert _parry_context(axes, state(axes), axes.main_weapon, 3, 4, "p").reroll is True


def test_a_dwarf_axe_and_a_sword_re_roll_the_parry_in_both_hand_orders():
    main_axe = bare("dwarf-slayers-kaz", "slayers", main_weapon_id="weapon.dwarf-axe",
                    off_hand_id="weapon.sword")
    main_sword = bare("dwarf-slayers-kaz", "slayers", main_weapon_id="weapon.sword",
                      off_hand_id="weapon.dwarf-axe")
    assert _parry_capacity(main_axe) == 1
    assert _parry_context(main_axe, state(main_axe), main_axe.main_weapon, 3, 4, "p").reroll is True
    assert _parry_context(main_sword, state(main_sword), main_sword.main_weapon, 3, 4, "p").reroll is True


def test_two_ordinary_swords_gain_no_failed_parry_reroll():
    swords = bare("dwarf-slayers-kaz", "slayers", main_weapon_id="weapon.sword",
                  off_hand_id="weapon.sword")
    assert _parry_capacity(swords) == 1
    assert _parry_context(swords, state(swords), swords.main_weapon, 3, 4, "p").reroll is False


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


# Natural-armour provenance rules: an inherent save that Strength cannot
# worsen, one that ignores Strength entirely, and one a magical blow skips.
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


# Connections to existing defence operators: the pending step was the
# construction data that routes the printed item/note, not new behaviour.
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


def test_mourngul_three_plus_ethereal_save_has_the_printed_threshold_and_magic_exception():
    unit = bare("call-of-the-night-haint-mim", "mourngul")
    assert unit.global_effects.ethereal_hit_save == 3
    assert strike(attacker(), unit, [("hit", 4), ("ethereal", 3)]).saved
    # A failed Ethereal roll needs the ordinary wound roll, with no second save.
    assert not strike(attacker(), unit,
        [("hit", 4), ("ethereal", 2), ("wound", 1)]).saved
    magic = strike(attacker(weapon="weapon.hellblade"), unit,
        [("hit", 4), ("wound", 1)])
    assert not magic.saved


@pytest.mark.parametrize("curse", [False, True])
def test_pooled_ranald_ducks_every_hit_and_skips_a_hit_already_saved_by_ethereal(curse):
    # Composition witness: it does not establish a canonical Ethereal Priest.
    atk = attacker()
    if curse:
        atk = replace(atk, global_effects=replace(atk.global_effects,
            tags=(*atk.global_effects.tags, "condition.djinns-curse-active")))
    priest = trickster(special_rule_ids=(MARKS,))
    priest = replace(priest, global_effects=replace(priest.global_effects,
        tags=(*priest.global_effects.tags, "mechanic.ethereal-hit-save")))
    first, second = state(atk), state(priest)
    prepared = resolve_reference_attack(atk, priest, first, second, atk.main_weapon,
        StrictDice([{"key": "x.hit", "value": 4}]), key="x", hit_only=True)
    dice = StrictDice([{"key": "x.ethereal", "value": 4}])
    _, _, defended = _resolve_prepared_defences(atk, priest, first, second,
        ((atk.main_weapon, prepared),), dice, keys=("x",),
        first_round=False, charging=False, helpless=False)
    assert defended[0].saved
    dice.finish()
    priest = trickster(special_rule_ids=(MARKS,))
    dice = StrictDice([{"key": "x.marks-of-ranald", "value": 6}])
    _, _, defended = _resolve_prepared_defences(atk, priest, first, state(priest),
        ((atk.main_weapon, prepared),), dice, keys=("x",),
        first_round=False, charging=False, helpless=False)
    assert defended[0].saved
    dice.finish()


def test_ranald_plus_changes_one_own_hit_and_preserves_natural_face():
    unit = trickster(special_rule_ids=(MARKS,))
    target = attacker()
    dice = StrictDice([{"key": "x.hit", "value": 3}])
    decisions = StrictDecisions([{"key": "x.hit.ranalds-luck.plus", "value": True}])
    result = resolve_reference_attack(unit, target, state(unit), state(target), unit.main_weapon,
        dice, key="x", hit_only=True, decisions=decisions)
    assert result.hit and "ranalds-luck" in result.attacker.resources_spent
    dice.finish()
    decisions.finish()
    # A modified five is a successful six, but carries no natural-six trigger.
    dice = StrictDice([{"key": "y.hit", "value": 5}])
    decisions = StrictDecisions([{"key": "y.hit.ranalds-luck.plus", "value": True}])
    result = resolve_reference_attack(unit, target, state(unit), state(target), unit.main_weapon,
        dice, key="y", hit_only=True, decisions=decisions)
    assert result.hit_roll == 6 and not result.natural_hit_six
    dice.finish()
    decisions.finish()


def test_ranald_minus_is_optional_and_the_resource_follows_the_owner_across_sites():
    unit = trickster(special_rule_ids=(MARKS,))
    dice = StrictDice([{"key": "own.test", "value": 5}, {"key": "own.hit", "value": 2}])
    decisions = StrictDecisions([
        {"key": "own.test.ranalds-luck.plus", "value": False},
        {"key": "own.test.ranalds-luck.minus", "value": True}])
    owned = OwnedRollDice(dice, unit, state(unit), decisions)
    assert owned.roll(RollRequest("own.test")) == 4
    assert owned.roll(RollRequest("own.hit")) == 2
    assert owned.state.resources_spent == {"ranalds-luck"}
    dice.finish()
    decisions.finish()


def test_oracle_reroll_is_shared_across_hit_and_wound_and_never_rerolls_a_reroll():
    # Local resource witness; the canonical selected Oracle is separately compiled.
    unit = attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "mechanic.oracle"), reroll_hits=True))
    target = attacker()
    dice = StrictDice([
        {"key": "x.hit", "value": 1}, {"key": "x.hit.reroll", "value": 1}])
    decisions = StrictDecisions([{"key": "x.hit.one-roll-reroll", "value": True}])
    result = resolve_reference_attack(unit, target, state(unit), state(target), unit.main_weapon,
        dice, key="x", decisions=decisions)
    assert not result.hit and result.attacker.resources_spent == {"one-roll-reroll"}
    dice.finish()
    decisions.finish()
    unit = replace(unit, global_effects=replace(unit.global_effects, reroll_hits=False))
    dice = StrictDice([
        {"key": "y.hit", "value": 4}, {"key": "y.wound", "value": 1},
        {"key": "y.wound.reroll", "value": 4}])
    decisions = StrictDecisions([
        {"key": "y.hit.one-roll-reroll", "value": False},
        {"key": "y.wound.one-roll-reroll", "value": True}])
    result = resolve_reference_attack(unit, target, state(unit), state(target), unit.main_weapon,
        dice, key="y", decisions=decisions)
    assert result.wounded and result.attacker.resources_spent == {"one-roll-reroll"}
    dice.finish()
    decisions.finish()


def test_aenur_fixed_hit_threshold_retains_modifiers_and_automatic_hit_provenance():
    unit = bare("hirelings.dramatis-personae.core", "hireling.dramatis.aenur",
                main_weapon_id="weapon.ienh-khain")
    target = attacker()
    context = prepare_hit_context(unit, target, state(unit), state(target), unit.main_weapon,
        _combined_effect(unit, unit.main_weapon))
    assert context.fixed_target == 2
    dice = StrictDice([{"key": "hit", "value": 2}])
    assert phases.resolve_hit(context, dice).success
    dice.finish()
    dice = StrictDice([{"key": "hit", "value": 2}])
    assert not phases.resolve_hit(replace(context, modifier=-1), dice).success
    dice.finish()
    hit = phases.resolve_hit(replace(context, automatic=True), StrictDice([]))
    assert hit.success and hit.roll == 0
    dice = StrictDice([{"key": "x.hit", "value": 2}, {"key": "x.wound", "value": 5},
                      {"key": "x.critical", "value": 1}])
    result = resolve_reference_attack(unit, target, state(unit), replace(state(target), wounds=4),
        unit.main_weapon, dice, key="x")
    assert result.critical and result.damage == 2
    dice.finish()


@pytest.mark.parametrize("mark,profile", [
    ("hireling.hired-sword.war-priestess-of-myrmidia.rule.marks-of-myrmidia",
     "hireling.hired-sword.war-priestess-of-myrmidia"),
    ("hireling.hired-sword.priest-of-morr-miracle-workers.skill.augur",
     "hireling.hired-sword.priest-of-morr-miracle-workers"),
])
def test_selected_oracle_and_augur_own_one_reroll_then_keep_it_spent_when_defending(mark, profile):
    unit = bare("hirelings.hired-sword.2b", profile, special_rule_ids=(mark,))
    target = attacker()
    dice = StrictDice([{"key": "x.hit", "value": 1}, {"key": "x.hit.reroll", "value": 1}])
    decisions = StrictDecisions([{"key": "x.hit.one-roll-reroll", "value": True}])
    first = resolve_reference_attack(unit, target, state(unit), state(target), unit.main_weapon,
        dice, key="x", decisions=decisions, hit_only=True)
    assert not first.hit and "one-roll-reroll" in first.attacker.resources_spent
    dice.finish()
    decisions.finish()
    # A later real opposing attack may not offer another own-roll resource.
    dice = StrictDice([{"key": "y.hit", "value": 4}, {"key": "y.wound", "value": 1}])
    second = resolve_reference_attack(target, unit, state(target), first.attacker, target.main_weapon,
        dice, key="y", decisions=StrictDecisions([]))
    assert "one-roll-reroll" in second.defender.resources_spent
    dice.finish()


def test_andanti_roll_under_ws_parry_has_strict_boundary_and_retains_strength_limit():
    unit = bare("dreamwalkers-cult-of-morr-fbg", "andanti",
                main_weapon_id="weapon.rapier", off_hand_id="weapon.main-gauche")
    context = _parry_context(unit, state(unit), EffectSet(), 3, 6, "p")
    assert context.roll_under == unit.characteristics.weapon_skill
    dice = StrictDice([{"key": "p.parry", "value": unit.characteristics.weapon_skill - 1}])
    assert phases.resolve_parry(context, dice).blocked
    dice.finish()
    dice = StrictDice([{"key": "p.parry", "value": unit.characteristics.weapon_skill}])
    assert not phases.resolve_parry(context, dice).blocked
    dice.finish()
    assert not phases.resolve_parry(replace(context,
        attacker_strength=2 * context.defender_strength), StrictDice([])).attempted


def test_greenskin_traitor_grants_hatred_to_the_enemy_only_with_psychology_and_first_round_limits():
    scout = bare("hirelings.hired-sword.1c", "hireling.hired-sword.hobgoblin-scout")
    greenskin = attacker()
    greenskin = replace(greenskin, global_effects=replace(greenskin.global_effects,
        tags=(*greenskin.global_effects.tags, "species.orc")))
    def reroll(unit, target, first=True, frenzy=False):
        return _hit_reroll(unit, target, unit.main_weapon, _combined_effect(unit, unit.main_weapon),
                           first, False, frenzy=frenzy)
    assert reroll(greenskin, scout)
    assert not reroll(scout, greenskin)
    assert not reroll(greenskin, scout, first=False)
    assert not reroll(greenskin, scout, frenzy=True)
    assert not reroll(attacker(), scout)
    immune = replace(greenskin, global_effects=replace(greenskin.global_effects,
        tags=(*greenskin.global_effects.tags, "mechanic.psychology-immunity")))
    assert not reroll(immune, scout)


def test_djinn_curse_modifies_enemy_melee_hits_and_each_ordinary_save_once():
    # Only the selected, still active power contributes penalties.
    unit, target = attacker(), attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "condition.djinns-curse-active")))
    effect = _combined_effect(target, target.main_weapon)
    context = prepare_hit_context(target, unit, state(target), state(unit), target.main_weapon, effect)
    assert context.modifier == -1
    assert prepare_hit_context(target, unit, state(target), state(unit), target.main_weapon,
                               effect, melee_attack=False).modifier == 0
    target = replace(target, armour_save=5, global_effects=replace(target.global_effects,
        ward_save=5, regeneration_save=4))
    incoming = _combined_effect(unit, unit.main_weapon)
    context = prepare_armour_context(unit, target, state(unit), state(target), unit.main_weapon, incoming)
    assert phases.armour_target(context) == 6
    special = prepare_special_save_context(target, incoming)
    assert (special.ward_save, special.regeneration_save) == (6, 5)


def test_corruption_can_force_one_eligible_successful_hit_to_reroll_without_rerolling_a_reroll():
    unit, target = attacker(), attacker()
    target = replace(target, global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, "mechanic.corruption")))
    dice = StrictDice([{"key": "x.hit", "value": 4}, {"key": "x.hit.reroll", "value": 1}])
    decisions = StrictDecisions([{"key": "x.corruption", "value": True}])
    result = resolve_reference_attack(unit, target, state(unit), state(target), unit.main_weapon,
        dice, key="x", hit_only=True, decisions=decisions)
    assert not result.hit and "corruption" in result.defender.resources_spent
    dice.finish()
    decisions.finish()
    immune = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "mechanic.psychology-immunity")))
    dice = StrictDice([{"key": "y.hit", "value": 4}])
    result = resolve_reference_attack(immune, target, state(immune), state(target), unit.main_weapon,
        dice, key="y", hit_only=True, decisions=StrictDecisions([]))
    assert result.hit and "corruption" not in result.defender.resources_spent
    dice.finish()


def test_rememberer_uses_one_selected_pool_with_variant_recipient_and_expiry_limits():
    unit = canonical("dwarf-slayers-kaz", "giant-slayer", "weapon.mace",
        condition_ids=("condition.rememberer-kaz-support",))
    target = attacker()
    target = replace(target, global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, "size.large")))
    dice = StrictDice([
        {"key": "x.attack.0.hit", "value": 1}, {"key": "x.attack.0.hit.reroll", "value": 4},
        {"key": "x.attack.1.hit", "value": 1}, {"key": "x.attack.1.hit.reroll", "value": 4},
        {"key": "x.attack.0.wound", "value": 1}, {"key": "x.attack.1.wound", "value": 1}])
    decisions = StrictDecisions([{"key": "x.attack.0.rememberer", "value": True}])
    first, second, outcomes = _resolve_attack_pool(unit, target, state(unit), state(target), 2, dice,
        key="x", first_round=False, charging=False, decisions=decisions)
    assert len(outcomes) == 2 and first.resources_spent == {"rememberer"}
    dice.finish()
    decisions.finish()
    # The same key cannot revive the phase-local activation after it expires.
    dice = StrictDice([{"key": "x.attack.0.hit", "value": 1}])
    later = _resolve_attack_pool(unit, target, first, second, 1, dice,
        key="x", first_round=False, charging=False, decisions=StrictDecisions([]))
    assert not later[2][0].hit
    dice.finish()
    tough = replace(target, global_effects=replace(target.global_effects,
        tags=tuple(tag for tag in target.global_effects.tags if tag != "size.large")))
    tough_state = replace(state(tough), toughness=5)
    dice = StrictDice([{"key": "z.hit", "value": 1}])
    assert not resolve_reference_attack(unit, tough, state(unit), tough_state, unit.main_weapon,
        dice, key="z", hit_only=True, decisions=StrictDecisions([])).hit
    dice.finish()
    unit = canonical("dwarf-slayer-cult-web", "giant-slayer", "weapon.mace",
        condition_ids=("condition.rememberer-web-support",))
    dice = StrictDice([{"key": "z.hit", "value": 1}, {"key": "z.hit.reroll", "value": 4}])
    decisions = StrictDecisions([{"key": "z.rememberer", "value": True}])
    assert resolve_reference_attack(unit, tough, state(unit), tough_state, unit.main_weapon,
        dice, key="z", hit_only=True, decisions=decisions).hit
    dice.finish()
    decisions.finish()


def test_shaggy_hide_combines_normal_armour_but_respects_the_specific_leather_exception():
    unit = canonical("beastmen-raiders", "beastmen-chieftain", "weapon.mace",
        armour_id="armour.light-armour", off_hand_id="defence.shield",
        special_rule_ids=("band--beastmen-special-skills-shaggy-hide",))
    assert armour(3, unit)[0] == 4  # ordinary light armour 6+, shield, hide
    # Leathers are not on that warband's printed list. A free build exercises
    # the same innate save/stack operators and the item's explicit exception.
    free = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        armour_id="armour.toughened-leathers",
        trait_overrides={"natural_armour_save": 6, "natural_armour_stacks": True}))
    assert armour(3, free)[0] == 6


def test_achilles_heel_criticals_when_needing_six_and_stampede_denies_only_charge_armour():
    unit, target = attacker(), attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "mechanic.achilles-heel")))
    dice = StrictDice([{"key": "x.hit", "value": 4}, {"key": "x.wound", "value": 6},
                      {"key": "x.critical", "value": 1}])
    result = resolve_reference_attack(unit, target, state(unit), replace(state(target), toughness=5, wounds=5),
        unit.main_weapon, dice, key="x")
    assert result.critical and result.damage == 2
    dice.finish()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "condition.stampede-active")))
    target = replace(target, armour_save=2)
    dice = StrictDice([{"key": "y.hit", "value": 4}, {"key": "y.wound", "value": 5}])
    result = resolve_reference_attack(unit, target, state(unit), state(target), unit.main_weapon,
        dice, key="y", first_round=True, charging=True)
    assert result.damage == 1 and not result.saved
    dice.finish()
    dice = StrictDice([{"key": "z.hit", "value": 4}, {"key": "z.wound", "value": 5},
                      {"key": "z.armour", "value": 2}])
    result = resolve_reference_attack(unit, target, state(unit), state(target), unit.main_weapon,
        dice, key="z", first_round=False, charging=False)
    assert result.saved
    dice.finish()


def test_darting_steel_requires_both_under_ws_and_no_more_than_the_highest_hit_roll():
    unit = compile_fighter(FighterBuild("mordheim", Characteristics(4, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.sword", off_hand_id="defence.buckler"))
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "mechanic.darting-steel")))
    context = _parry_context(unit, state(unit), EffectSet(), 3, 2, "p")
    assert (context.roll_under, context.maximum_roll) == (4, 2)
    # Disable the independent sword+buckler reroll to isolate the two bounds.
    context = replace(context, reroll=False)
    dice = StrictDice([{"key": "p.parry", "value": 3}])
    assert not phases.resolve_parry(context, dice).blocked
    dice.finish()
    dice = StrictDice([{"key": "p.parry", "value": 2}])
    assert phases.resolve_parry(context, dice).blocked
    dice.finish()


def test_persistent_frenzy_survives_the_immediate_stunned_injury_transition():
    unit, target = attacker(), attacker()
    target = replace(target, global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, "mechanic.persistent-frenzy")))
    dice = StrictDice([{"key": "x.hit", "value": 4}, {"key": "x.wound", "value": 4},
                      {"key": "x.injury.0", "value": 3}])
    result = resolve_reference_attack(unit, target, state(unit),
        replace(state(target), wounds=1, frenzy=True), unit.main_weapon, dice, key="x")
    assert result.defender.condition == phases.Condition.STUNNED and result.defender.frenzy
    dice.finish()


def test_self_backlash_has_one_roll_resource_owner_across_wound_and_save():
    unit = attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "mechanic.oracle"), ward_save=5))
    initial = state(unit)
    effect = EffectSet(tags=("mechanic.black-hunger-backlash", "effect.no-critical"),
        fixed_strength=3, automatic_hit=True, cannot_be_parried=True, ignore_armour=True)
    dice = StrictDice([{"key": "x.wound", "value": 1}, {"key": "x.wound.reroll", "value": 4},
                      {"key": "x.special.ward", "value": 1}])
    decisions = StrictDecisions([{"key": "x.wound.one-roll-reroll", "value": True}])
    result = resolve_reference_attack(unit, unit, initial, initial, effect, dice,
        key="x", melee_attack=False, decisions=decisions)
    assert result.attacker.resources_spent == result.defender.resources_spent == {"one-roll-reroll"}
    dice.finish()
    decisions.finish()


def test_inconsistency_rolls_only_the_characteristics_needed_after_a_hit_and_caches_them():
    unit, target = attacker(), attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "mechanic.inconsistency")),
        random_characteristics=(("WS", 1, 6, 0), ("S", 1, 6, 0)))
    initial = state(unit)
    assert not initial.random_rolled
    dice = StrictDice([{"key": "x.attacker.characteristic.WS.0", "value": 3},
                      {"key": "x.hit", "value": 1}])
    first = resolve_reference_attack(unit, target, initial, state(target), unit.main_weapon, dice, key="x")
    assert first.attacker.random_rolled == {"WS"}
    dice.finish()
    dice = StrictDice([{"key": "y.hit", "value": 4},
                      {"key": "y.attacker.characteristic.S.0", "value": 4},
                      {"key": "y.wound", "value": 1}])
    second = resolve_reference_attack(unit, target, first.attacker, first.defender,
        unit.main_weapon, dice, key="y")
    assert second.attacker.random_rolled == {"WS", "S"}
    assert second.attacker.strength == 4
    dice.finish()


def test_an_indestructible_weapon_can_be_parried_without_a_trap_blade_break_roll():
    unit, target = attacker(weapon="weapon.sword"), attacker(weapon="weapon.sword-breaker")
    unit = replace(unit, main_weapon=replace(unit.main_weapon,
        tags=(*unit.main_weapon.tags, "weapon.indestructible")))
    result = strike(unit, target, [("hit", 4), ("parry", 5)])
    assert result.parried and not result.attacker.broken_hands


def test_ranald_modified_six_keeps_its_physical_five_for_pooled_equal_parry():
    unit = trickster(special_rule_ids=(MARKS,))
    target = attacker(weapon="weapon.sword")
    target = replace(target, global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, "skill.sword-master")))
    dice = StrictDice([{"key": "x.attack.0.hit", "value": 5},
                      {"key": "x.attack.0.parry", "value": 6}])
    decisions = StrictDecisions([{"key": "x.attack.0.hit.ranalds-luck.plus", "value": True}])
    _, _, outcomes = _resolve_attack_pool(unit, target, state(unit), state(target), 1, dice,
        key="x", first_round=False, charging=False, decisions=decisions)
    assert outcomes[0].parried
    dice.finish()
    decisions.finish()


def test_ethereal_and_step_aside_do_not_combine_but_magical_attacks_can_use_step_aside():
    target = attacker()
    target = replace(target, global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, "mechanic.ethereal-hit-save"), step_aside=True))
    assert prepare_special_save_context(target, EffectSet()).ward_save == 7
    assert prepare_special_save_context(target, EffectSet(tags=("attack.magical",))).ward_save == 5
    result = strike(attacker(weapon="weapon.hellblade"), target,
        [("hit", 4), ("wound", 4), ("special.ward", 5)])
    assert result.saved


@pytest.mark.parametrize("persistent", [False, True])
def test_direct_titanic_knockdown_ends_ordinary_frenzy_only(persistent):
    unit, target = attacker(), attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "mechanic.titanic-strength")))
    if persistent:
        target = replace(target, global_effects=replace(target.global_effects,
            tags=(*target.global_effects.tags, "mechanic.persistent-frenzy")))
    dice = StrictDice([{"key": "x.hit", "value": 4}, {"key": "x.wound", "value": 1},
                      {"key": "x.titanic-strength", "value": 6}])
    result = resolve_reference_attack(unit, target, state(unit), replace(state(target), frenzy=True),
        unit.main_weapon, dice, key="x")
    assert result.defender.condition == phases.Condition.KNOCKED_DOWN
    assert result.defender.frenzy == persistent


def test_djinn_passive_capability_has_no_curse_and_active_luck_respects_missing_intrinsic_save():
    unit = attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "mechanic.djinns-curse"),
        ward_save=5, ward_save_mundane_only=True))
    target = attacker()
    assert prepare_hit_context(target, unit, state(target), state(unit),
        target.main_weapon, _combined_effect(target, target.main_weapon)).modifier == 0
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "condition.djinns-luck-active")))
    assert prepare_special_save_context(unit, EffectSet()).ward_save == 4
    magic = prepare_special_save_context(unit, EffectSet(tags=("attack.magical",)))
    assert magic.ward_save == 6 and not magic.ward_blocked


@pytest.mark.parametrize("injury,damage,condition", [(1, 0, phases.Condition.STANDING),
    (2, 1, phases.Condition.KNOCKED_DOWN), (4, 1, phases.Condition.STUNNED)])
def test_inured_to_pain_ignores_zero_injury_damage_and_keeps_other_boundaries(injury, damage, condition):
    target = attacker()
    target = replace(target, characteristics=replace(target.characteristics, wounds=1),
        global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, "mechanic.inured-to-pain")))
    result = strike(attacker(), target, [("hit", 4), ("wound", 4), ("injury.0", injury)])
    assert result.damage == damage and result.defender.condition == condition
    assert result.defender.wounds == (1 if damage == 0 else 0)


@pytest.mark.parametrize("strength_roll,held", [(1, False), (2, True)])
def test_gaoler_grapple_replaces_all_attacks_and_uses_strict_under_strength_minus_one(strength_roll, held):
    unit = canonical("hirelings.hired-sword.1b", "hireling.hired-sword.gaoler", "weapon.flail",
        owned_item_ids=("flail",))
    target = attacker()
    dice = StrictDice([{"key": "x.grapple.hit", "value": 4},
        {"key": "x.grapple.strength", "value": strength_roll}])
    decisions = StrictDecisions([{"key": "x.torturer-grapple", "value": True}])
    first, second, results = _resolve_attack_pool(unit, target, state(unit), state(target),
        3, dice, key="x", first_round=False, charging=False, decisions=decisions)
    assert first.grappling == second.grappled == held
    assert len(results) == 1 and results[0].damage == 0 and second.wounds == 2
    dice.finish(); decisions.finish()


def test_giggle_juice_replaces_one_attack_with_strength_two_and_consumes_one_battle_resource():
    unit = bare("hirelings.dramatis-personae.2a", "hireling.dramatis.the-foole")
    target = attacker()
    target = replace(target, characteristics=replace(target.characteristics, wounds=1))
    unit = replace(unit, global_effects=replace(unit.global_effects,
        strength_bonus=3, damage=3))
    dice = StrictDice([{"key": "x.attack.1.hit", "value": 4},
        {"key": "x.attack.0.wound", "value": 5},
        {"key": "x.attack.0.injury.0", "value": 2},
        {"key": "x.attack.1.wound", "value": 1}])
    decisions = StrictDecisions([{"key": "x.giggle-juice-attack.0", "value": True}])
    first, second, results = _resolve_attack_pool(unit, target, state(unit), state(target),
        2, dice, key="x", first_round=False, charging=False, decisions=decisions)
    assert "giggle-juice" in first.resources_spent
    assert len(results) == 2 and results[0].damage == 1 and not results[1].wounded
    assert second.condition == phases.Condition.STUNNED
    dice.finish(); decisions.finish()


def test_electrical_forfeit_removes_only_nominated_offhand_and_no_sole_stunned_finisher():
    unit = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1),
        main_weapon_id="weapon.mace", off_hand_id="weapon.dagger"))
    target = attacker()
    dice = StrictDice([{"key": "x.attack.0.hit", "value": 4},
        {"key": "x.attack.0.wound", "value": 1}])
    decisions = StrictDecisions([])
    _, _, results = _resolve_attack_pool(unit, target, state(unit), state(target),
        2, dice, key="x", first_round=False, charging=False, decisions=decisions, forfeit_index=1)
    assert len(results) == 1
    dice.finish(); decisions.finish()
    dice = StrictDice([])
    _, _, results = _resolve_attack_pool(unit, target, state(unit),
        replace(state(target), condition=phases.Condition.STUNNED),
        1, dice, key="x", first_round=False, charging=False,
        decisions=StrictDecisions([]), forfeit_index=0)
    assert not results
    dice.finish()


@pytest.mark.parametrize("last,damage,remaining,condition", [
    (1, 0, 1, phases.Condition.STANDING), (4, 1, 0, phases.Condition.STUNNED)])
def test_inured_zero_cancels_each_multiwound_injury_and_its_nightshade_penalty(last, damage, remaining, condition):
    unit, target = attacker(), attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        damage=2, tags=(*unit.global_effects.tags, "poison.nightshade")))
    target = replace(target, characteristics=replace(target.characteristics, wounds=1),
        global_effects=replace(target.global_effects,
            tags=(*target.global_effects.tags, "mechanic.inured-to-pain")))
    result = strike(unit, target, [("hit", 4), ("wound", 4),
        ("injury.0", 1), ("injury.1", last)])
    assert result.damage == result.defender.initiative_penalty == damage
    assert result.defender.wounds == remaining and result.defender.condition == condition


@pytest.mark.parametrize("tag", ["nature.undead", "nature.daemon", "nature.dead",
    "mechanic.pain-immunity", "size.large"])
def test_gaoler_does_not_offer_grapple_to_an_excluded_recipient(tag):
    unit, target = attacker(), attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "mechanic.gaoler-grapple")))
    target = replace(target, global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, tag)))
    dice, decisions = StrictDice([{"key": "x.attack.0.hit", "value": 1}]), StrictDecisions([])
    _resolve_attack_pool(unit, target, state(unit), state(target), 1, dice,
        key="x", first_round=False, charging=False, decisions=decisions)
    dice.finish(); decisions.finish()


def test_giggle_poison_immunity_cancels_the_whole_spray_and_the_once_battle_resource_stays_spent():
    unit = bare("hirelings.dramatis-personae.2a", "hireling.dramatis.the-foole")
    target = attacker()
    target = replace(target, global_effects=replace(target.global_effects, poison_immunity=True))
    dice = StrictDice([])
    decisions = StrictDecisions([{"key": "x.giggle-juice-attack.0", "value": True}])
    first, second, results = _resolve_attack_pool(unit, target, state(unit), state(target),
        1, dice, key="x", first_round=False, charging=False, decisions=decisions)
    assert "giggle-juice" in first.resources_spent and not results[0].wounded
    dice.finish(); decisions.finish()
    dice = StrictDice([{"key": "y.attack.0.hit", "value": 1}])
    decisions = StrictDecisions([])
    _resolve_attack_pool(unit, target, first, second, 1, dice,
        key="y", first_round=False, charging=False, decisions=decisions)
    dice.finish(); decisions.finish()


@pytest.mark.parametrize("condition", [phases.Condition.KNOCKED_DOWN, phases.Condition.STUNNED])
def test_electrical_fixed_strength_hit_still_rolls_to_wound_a_helpless_target(condition):
    from mordheim_combat.modular.pools import electrical_touch_weapon
    unit, target = attacker(), attacker()
    unit = replace(unit, main_weapon=electrical_touch_weapon(target))
    dice = StrictDice([{"key": "x.attack.0.wound", "value": 1}])
    _, second, results = _resolve_attack_pool(unit, target, state(unit),
        replace(state(target), condition=condition), 1, dice,
        key="x", first_round=False, charging=False, single_bonus=True,
        decisions=StrictDecisions([]))
    assert len(results) == 1 and not results[0].wounded and second.condition == condition
    dice.finish()


def test_trip_roll_belongs_to_the_jester_and_uses_no_wound_die():
    unit, target = attacker(), attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "mechanic.confound-and-confuse", "mechanic.ranalds-luck")))
    dice = StrictDice([{"key": "x.hit", "value": 4}, {"key": "x.trip-roll", "value": 1}])
    decisions = StrictDecisions([
        {"key": "x.hit.ranalds-luck.plus", "value": False},
        {"key": "x.hit.ranalds-luck.minus", "value": False},
        {"key": "x.trip.hit", "value": True},
        {"key": "x.trip-roll.ranalds-luck.plus", "value": True}])
    result = resolve_reference_attack(unit, target,
        replace(state(unit), trip_trick_active=True), state(target), unit.main_weapon,
        dice, key="x", decisions=decisions)
    assert result.defender.condition == phases.Condition.KNOCKED_DOWN
    assert "ranalds-luck" in result.attacker.resources_spent
    assert "ranalds-luck" not in result.defender.resources_spent and not result.wounded
    dice.finish(); decisions.finish()


def test_excellent_reflexes_has_one_special_save_with_a_source_bound_dodge_upgrade():
    unit = canonical('hirelings.hired-sword.1b','hireling.hired-sword.tomb-robber','weapon.sword')
    incoming = EffectSet(tags=("attack.magical",))
    assert prepare_special_save_context(unit, incoming).ward_save == 5
    upgraded = canonical('hirelings.hired-sword.1b','hireling.hired-sword.tomb-robber','weapon.sword',
        condition_ids=('condition.tomb-robber-dodge-known',))
    assert prepare_special_save_context(upgraded, incoming).ward_save == 4
    other = attacker()
    other = replace(other, global_effects=replace(other.global_effects,
        tags=(*other.global_effects.tags, "condition.tomb-robber-dodge-known")))
    assert prepare_special_save_context(other, incoming).ward_save == 7


@pytest.mark.parametrize('upgraded,roll',[(False,5),(True,4)])
def test_native_tomb_robber_special_save_resolves_actual_magical_wound(upgraded,roll):
    target = canonical('hirelings.hired-sword.1b','hireling.hired-sword.tomb-robber','weapon.sword',
        condition_ids=('condition.tomb-robber-dodge-known',) if upgraded else ())
    unit = attacker(strength=6)
    unit = replace(unit,global_effects=replace(unit.global_effects,tags=(*unit.global_effects.tags,'attack.magical')))
    result = strike(unit,target,[('hit',6),('wound',3),('special.ward',roll)])
    assert result.saved and result.defender.wounds == target.characteristics.wounds


@pytest.mark.parametrize('incoming_tag',[None,'attack.magical','attack.blessed'])
def test_native_chaos_fury_natural_armour_and_printed_denials(incoming_tag):
    target = canonical('hirelings.hired-sword.2a','hireling.hired-sword.chaos-fury','weapon.natural-attacks')
    assert phases.has_tag(target.global_effects,'attack.magical')
    unit = attacker(strength=6)
    if incoming_tag:
        unit = replace(unit,global_effects=replace(unit.global_effects,tags=(*unit.global_effects.tags,incoming_tag)))
    rolls = [('hit',6),('wound',3)]
    rolls += [('armour',5)] if incoming_tag is None else [('injury.0',1)]
    result = strike(unit,target,rolls)
    assert result.saved == (incoming_tag is None)


def test_native_magic_acorn_automatically_replaces_only_one_actual_first_round_miss():
    unit = compile_fighter(FighterBuild('mordheim',Characteristics(3,3,3,2,3,2),
        main_weapon_id='weapon.mace',defence_ids=('defence.magic-acorn',),
        trait_overrides={'fighter_kind':'hero'}))
    target = attacker()
    dice = StrictDice([{'key':'x.attack.0.hit','value':1}, {'key':'x.attack.1.hit','value':1},
        {'key':'x.attack.0.wound','value':1}])
    first,_,results = _resolve_attack_pool(unit,target,state(unit),state(target),2,dice,
        key='x',first_round=True,charging=False,decisions=None)
    assert [result.hit for result in results] == [True,False]
    assert results[0].hit_roll == 1 and not results[0].critical
    assert 'magic-acorn' in first.resources_spent
    dice.finish()


def test_magic_acorn_is_hero_only_and_does_not_replace_later_round_misses():
    with pytest.raises(ValueError,match='Hero|hero'):
        compile_fighter(FighterBuild('mordheim',Characteristics(3,3,3,2,3,1),
            defence_ids=('defence.magic-acorn',)))
    unit = compile_fighter(FighterBuild('mordheim',Characteristics(3,3,3,2,3,1),
        defence_ids=('defence.magic-acorn',),trait_overrides={'fighter_kind':'hero'}))
    dice = StrictDice([{'key':'x.hit','value':1}])
    result = resolve_reference_attack(unit,attacker(),state(unit),state(attacker()),unit.main_weapon,
        dice,key='x',first_round=False)
    assert not result.hit and 'magic-acorn' not in result.attacker.resources_spent
    dice.finish()


def veskit():
    return canonical('hirelings.dramatis-personae.core','hireling.dramatis.veskit','weapon.veskit-claws')


@pytest.mark.parametrize('injury,condition',[(1,phases.Condition.STANDING),
    (3,phases.Condition.STANDING),(5,phases.Condition.OUT)])
def test_native_veskit_ignores_injury_states_without_healing_or_skipping_out(injury,condition):
    unit,target = attacker(strength=6),veskit()
    dice = StrictDice([{'key':'x.hit','value':6},{'key':'x.wound','value':3},
        {'key':'x.armour','value':1},{'key':'x.injury.0','value':injury}])
    result = resolve_reference_attack(unit,target,state(unit),replace(state(target),wounds=1),
        unit.main_weapon,dice,key='x')
    assert result.defender.wounds == 0 and result.defender.condition == condition
    assert result.damage == 1 and result.wounded and not result.saved
    dice.finish()


def test_native_veskit_keeps_four_attacks_and_uses_fixed_strength_five_total_penetration_three():
    from mordheim_combat.modular.contexts import _attack_strength
    unit,target = veskit(),attacker()
    strength,armour_strength = _attack_strength(unit,target,state(unit),unit.main_weapon,
        _combined_effect(unit,unit.main_weapon),False,False)
    assert unit.characteristics.attacks == 4 and not unit.main_weapon.paired
    assert strength == 5 and armour_strength-3+unit.main_weapon.armour_penetration == 3
    assert unit.natural_armour_save == 3 and not unit.natural_armour_unmodified


def test_native_veskit_claws_follow_the_adopted_one_parry_and_failed_reroll():
    target = veskit()
    assert _parry_capacity(target) == 1
    assert strike(attacker(),target,[('hit',4),('parry',4),('parry.reroll',5)]).parried


def lucky_ranger():
    return canonical('hirelings.hired-sword.core','hireling.hired-sword.elf-ranger','weapon.sword',
        special_rule_ids=('hireling.hired-sword.elf-ranger.skill.luck',))


def test_native_ranger_luck_can_spend_the_shared_resource_on_own_leadership_then_not_a_hit():
    from mordheim_combat.modular.leadership import resolve_local_leadership
    from mordheim_combat.modular.state import DuelState
    unit,target = lucky_ranger(),attacker()
    current = DuelState(state(unit),state(target))
    dice = StrictDice([{'key':'ld.0','value':6},{'key':'ld.0.reroll','value':1},{'key':'ld.1','value':6}])
    choices = StrictDecisions([{'key':'ld.0.luck','value':True}])
    passed,own = resolve_local_leadership(unit,current,dice,choices,'ld',first=True,return_state=True)
    assert passed and 'luck' in own.resources_spent
    dice.finish(); choices.finish()
    dice = StrictDice([{'key':'hit.hit','value':1}])
    result = resolve_reference_attack(unit,target,own,current.second,unit.main_weapon,dice,
        key='hit',decisions=StrictDecisions([]))
    assert not result.hit
    dice.finish()


def test_native_ranger_may_reroll_a_successful_own_wound_and_must_keep_the_worse_second_roll():
    unit,target = lucky_ranger(),attacker()
    dice = StrictDice([{'key':'x.hit','value':6},{'key':'x.wound','value':4},{'key':'x.wound.reroll','value':1}])
    choices = StrictDecisions([{'key':'x.hit.luck','value':False},{'key':'x.wound.luck','value':True}])
    result = resolve_reference_attack(unit,target,state(unit),state(target),unit.main_weapon,dice,key='x',decisions=choices)
    assert not result.wounded and 'luck' in result.attacker.resources_spent
    dice.finish(); choices.finish()


@pytest.mark.parametrize('profile,band,weapon',[
    ('hireling.dramatis.countess-marianna-chevaux-vampire-assassin','hirelings.dramatis-personae.1a','weapon.rapier'),
    ('hireling.dramatis.sigmund-spindle-the-harvester-of-flesh','hirelings.dramatis-personae.2a','weapon.scythe')])
@pytest.mark.parametrize('injury,condition',[(1,phases.Condition.STANDING),(3,phases.Condition.STANDING),(5,phases.Condition.OUT)])
def test_native_marianna_and_sigmund_source_distinct_no_pain_compositions(profile,band,weapon,injury,condition):
    unit,target = attacker(strength=6),canonical(band,profile,weapon)
    dice = StrictDice([{'key':'x.hit','value':6},{'key':'x.wound','value':3},
        {'key':'x.special.ward','value':1},{'key':'x.injury.0','value':injury}])
    result = resolve_reference_attack(unit,target,state(unit),replace(state(target),wounds=1),unit.main_weapon,dice,key='x')
    assert result.defender.condition == condition and result.defender.wounds == 0
    assert result.damage == 1 and result.wounded
    dice.finish()


@pytest.mark.parametrize('magic,save,condition',[(False,4,phases.Condition.STANDING),
    (False,3,phases.Condition.KNOCKED_DOWN),(True,None,phases.Condition.KNOCKED_DOWN)])
def test_native_bone_goliath_ignores_injury_only_on_four_and_magic_denies_it(magic,save,condition):
    unit = attacker(strength=6)
    if magic: unit = replace(unit,global_effects=replace(unit.global_effects,tags=(*unit.global_effects.tags,'attack.magical')))
    target = canonical('hirelings.hired-sword.1c','hireling.hired-sword.bone-goliath','weapon.natural-attacks')
    rolls = [{'key':'x.hit','value':6},{'key':'x.wound','value':3},{'key':'x.injury.0','value':3}]
    if save is not None: rolls.append({'key':'x.injury.0.undead-construct','value':save})
    dice = StrictDice(rolls)
    result = resolve_reference_attack(unit,target,state(unit),replace(state(target),wounds=1),unit.main_weapon,dice,key='x')
    assert result.defender.condition == condition and result.defender.wounds == 0
    assert result.wounded and result.damage == 1 and not result.saved
    dice.finish()


def test_the_highest_of_several_injury_results_applies():
    unit, target = attacker(), attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects, damage=2))
    target = replace(target, characteristics=replace(target.characteristics, wounds=1))
    # A multi-wound hit forcing one knocked-down and one out-of-action injury
    # ends out of action; the same roll set without the 6 stays knocked down.
    result = strike(unit, target, [("hit", 4), ("wound", 4), ("injury.0", 2), ("injury.1", 6)])
    assert result.defender.condition == phases.Condition.OUT
    assert result.defender.wounds == -1
    survived = strike(unit, target, [("hit", 4), ("wound", 4), ("injury.0", 2), ("injury.1", 3)])
    assert survived.defender.condition == phases.Condition.STUNNED


def test_bone_goliath_checks_each_injury_and_keeps_the_unignored_result():
    unit,target = attacker(strength=6),canonical('hirelings.hired-sword.1c','hireling.hired-sword.bone-goliath','weapon.natural-attacks')
    unit = replace(unit,main_weapon=replace(unit.main_weapon,damage=2))
    dice = StrictDice([{'key':'x.hit','value':6},{'key':'x.wound','value':3},
        {'key':'x.injury.0','value':5},{'key':'x.injury.0.undead-construct','value':4},
        {'key':'x.injury.1','value':3},{'key':'x.injury.1.undead-construct','value':3}])
    result = resolve_reference_attack(unit,target,state(unit),replace(state(target),wounds=1),unit.main_weapon,dice,key='x')
    assert result.defender.condition == phases.Condition.KNOCKED_DOWN
    assert result.defender.wounds == -1 and result.damage == 2 and not result.saved
    dice.finish()


@pytest.mark.parametrize("luck", [False, True])
def test_intrinsic_djinn_save_is_unmodifiable_but_luck_replacement_is_an_ordinary_ward(luck):
    unit, target = attacker(), attacker()
    tags = ("mechanic.djinn-ethereal", "mechanic.ranalds-luck")
    if luck:
        tags += ("condition.djinns-luck-active",)
    target = replace(target, global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, *tags), ward_save=5, ward_save_mundane_only=True))
    dice = StrictDice([{"key": "x.hit", "value": 4}, {"key": "x.wound", "value": 4},
        {"key": "x.special.ward", "value": 3 if luck else 4}])
    decisions = StrictDecisions([{"key": "x.special.ward.ranalds-luck.plus", "value": True}] if luck else [])
    result = resolve_reference_attack(unit, target, state(unit), state(target),
        unit.main_weapon, dice, key="x", decisions=decisions)
    assert result.saved == luck
    assert ("ranalds-luck" in result.defender.resources_spent) == luck
    dice.finish(); decisions.finish()


@pytest.mark.parametrize("source,key,face", [
    ("mechanic.ethereal-hit-save", "x.ethereal", 4),
    ("mechanic.marks-of-ranald", "x.marks-of-ranald", 6),
    ("mechanic.djinn-ethereal", "x.special.ward", 5),
])
@pytest.mark.parametrize("passes", [False, True])
def test_active_curse_preserves_the_printed_unmodifiable_save(source, key, face, passes):
    unit, target = attacker(), attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "condition.djinns-curse-active")))
    target = replace(target, global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, source, "mechanic.ranalds-luck"),
        ward_save=5 if source == "mechanic.djinn-ethereal" else 7))
    rolls = [{"key": "x.hit", "value": 4}]
    if source == "mechanic.djinn-ethereal":
        rolls.append({"key": "x.wound", "value": 4})
    rolls.append({"key": key, "value": face if passes else face-1})
    if not passes and source != "mechanic.djinn-ethereal":
        rolls.append({"key": "x.wound", "value": 1})
    dice = StrictDice(rolls)
    result = resolve_reference_attack(unit, target, state(unit), state(target), unit.main_weapon,
        dice, key="x", decisions=StrictDecisions([]))
    dice.finish()
    assert result.saved == passes
    assert "ranalds-luck" not in result.defender.resources_spent


@pytest.mark.parametrize("face,saved", [(4, False), (5, True)])
def test_curse_preserves_daemonic_flesh_face_and_its_roll_is_unmodifiable(face, saved):
    unit = attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "condition.djinns-curse-active")))
    target = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 3, 1),
        trait_overrides={"natural_armour_save": 5, "natural_armour_unmodified": True,
                         "natural_armour_negated_by_magic": True}))
    target = replace(target, global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, "mechanic.daemonic-flesh", "mechanic.ranalds-luck")))
    dice = StrictDice([{"key": "x.hit", "value": 4}, {"key": "x.wound", "value": 4},
                       {"key": "x.armour", "value": face}])
    result = resolve_reference_attack(unit, target, state(unit), state(target), unit.main_weapon,
        dice, key="x", decisions=StrictDecisions([]))
    dice.finish()
    assert result.saved == saved
    assert "ranalds-luck" not in result.defender.resources_spent


@pytest.mark.parametrize("luck,ordinary_face", [(True, 5), (False, 4)])
def test_curse_keeps_a_stronger_ordinary_djinn_ward_modifiable(luck, ordinary_face):
    unit, target = attacker(), attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "condition.djinns-curse-active")))
    tags = ("mechanic.djinn-ethereal", "mechanic.ranalds-luck")
    if luck:
        tags += ("condition.djinns-luck-active",)
    target = replace(target, global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, *tags), ward_save=ordinary_face))
    incoming = _combined_effect(unit, unit.main_weapon)
    prepared = prepare_special_save_context(target, incoming)
    assert prepared.ward_save == 5 and not prepared.ward_unmodifiable
    dice = StrictDice([{"key": "x.hit", "value": 4}, {"key": "x.wound", "value": 4},
                       {"key": "x.special.ward", "value": 4}])
    decisions = StrictDecisions([{"key": "x.special.ward.ranalds-luck.plus", "value": True}])
    result = resolve_reference_attack(unit, target, state(unit), state(target), unit.main_weapon,
        dice, key="x", decisions=decisions)
    dice.finish(); decisions.finish()
    assert result.saved and "ranalds-luck" in result.defender.resources_spent


@pytest.mark.parametrize("incoming_tag", [None, "attack.magical", "attack.blessed"])
def test_daemonic_flesh_is_unmodifiable_natural_armour_with_both_printed_denials(incoming_tag):
    unit = attacker(strength=6)
    if incoming_tag:
        unit = replace(unit, global_effects=replace(unit.global_effects,
            tags=(*unit.global_effects.tags, incoming_tag)))
    target = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 3, 1),
        trait_overrides={"natural_armour_save": 5, "natural_armour_unmodified": True,
            "natural_armour_negated_by_magic": True}))
    target = replace(target, global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, "mechanic.daemonic-flesh", "mechanic.ranalds-luck")))
    rolls = [{"key": "x.hit", "value": 4}, {"key": "x.wound", "value": 3}]
    if incoming_tag is None:
        rolls += [{"key": "x.armour", "value": 4}]
    dice, decisions = StrictDice(rolls), StrictDecisions([])
    result = resolve_reference_attack(unit, target, state(unit), state(target), unit.main_weapon,
        dice, key="x", decisions=decisions)
    assert not result.saved and result.damage == 1
    assert "ranalds-luck" not in result.defender.resources_spent
    dice.finish(); decisions.finish()


def test_native_gaoler_zero_injury_preserves_its_current_last_wound():
    unit = attacker(strength=4)
    target = canonical("hirelings.hired-sword.1b", "hireling.hired-sword.gaoler", "weapon.flail",
        owned_item_ids=("flail",))
    dice = StrictDice([{"key": "x.hit", "value": 4}, {"key": "x.wound", "value": 4},
        {"key": "x.injury.0", "value": 1}])
    result = resolve_reference_attack(unit, target, state(unit), replace(state(target), wounds=1),
        unit.main_weapon, dice, key="x", decisions=StrictDecisions([]))
    assert result.damage == 0 and result.defender.wounds == 1
    assert result.defender.condition == phases.Condition.STANDING
    dice.finish()


def test_native_centaur_adds_one_trample_without_its_spear_charge_bonus():
    unit = canonical("hirelings.hired-sword.1c", "hireling.hired-sword.chaos-centaur", "weapon.spear",
        off_hand_id="defence.shield", owned_item_ids=("throwing_axe", "shield", "spear"))
    target = attacker()
    target = replace(target, characteristics=replace(target.characteristics, toughness=4))
    dice = StrictDice([{"key": "x.attack.0.hit", "value": 4}, {"key": "x.attack.1.hit", "value": 4},
        {"key": "x.attack.0.wound", "value": 3}, {"key": "x.attack.1.wound", "value": 3}])
    _, _, results = _resolve_attack_pool(unit, target, state(unit), state(target), 1, dice,
        key="x", first_round=True, charging=True, decisions=StrictDecisions([]))
    assert len(results) == 2 and results[0].wounded and not results[1].wounded
    dice.finish()


@pytest.mark.parametrize("tag,eligible", [(None, True), ("attack.magical", True), ("attack.fire", False)])
def test_native_belandysh_uses_four_plus_wound_regeneration_except_fire(tag, eligible):
    target = bare("hirelings.dramatis-personae.1c", "hireling.dramatis.belandysh-condemned-champion-of-chen",
        main_weapon_id="weapon.broadsword-of-damnation", armour_id="armour.chaos-armour",
        defence_ids=("defence.helmet",))
    incoming = EffectSet(tags=(tag,) if tag else ())
    context = prepare_special_save_context(target, incoming, defender_state=state(target))
    dice = StrictDice([{"key": "special.regeneration", "value": 4}] if eligible else [])
    result = phases.resolve_special_save(context, dice)
    assert result.saved == eligible
    dice.finish()


def test_plague_carrier_retries_after_resistance_then_infects_that_enemy_only_once():
    unit, target = attacker(), attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "mechanic.plague-carrier")))
    first, second = state(unit), state(target)
    for label, test, penalty in (("a", 3, 0), ("b", 4, 1), ("c", None, 1)):
        rolls = [{"key": f"{label}.hit", "value": 4}]
        if test is not None:
            rolls.append({"key": f"{label}.plague-carrier", "value": test})
        rolls.append({"key": f"{label}.wound", "value": 1})
        dice = StrictDice(rolls)
        result = resolve_reference_attack(unit, target, first, second, unit.main_weapon,
            dice, key=label, decisions=StrictDecisions([]))
        first, second = result.attacker, result.defender
        assert second.initiative_penalty == penalty
        assert ("plague-carrier-infected" in first.resources_spent) == bool(penalty)
        dice.finish()


@pytest.mark.parametrize("nature", ["nature.undead", "nature.daemon", "nature.possessed"])
def test_plague_carrier_has_no_borrowed_rot_immunity_and_infects_before_an_armour_save(nature):
    unit, target = attacker(), attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "mechanic.plague-carrier")))
    target = replace(target, armour_save=5, global_effects=replace(target.global_effects,
        poison_immunity=True, tags=(*target.global_effects.tags, nature)))
    dice = StrictDice([{"key": "x.hit", "value": 4},
        {"key": "x.plague-carrier", "value": 4},
        {"key": "x.wound", "value": 4}, {"key": "x.armour", "value": 5}])
    result = resolve_reference_attack(unit, target, state(unit), state(target), unit.main_weapon,
        dice, key="x", decisions=StrictDecisions([]))
    assert result.saved and result.defender.initiative_penalty == 1
    dice.finish()


def test_plague_carrier_does_not_test_on_a_miss_or_parried_hit():
    unit = attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "mechanic.plague-carrier")))
    target = attacker(weapon="weapon.sword")
    dice = StrictDice([{"key": "x.hit", "value": 4}, {"key": "x.parry", "value": 5}])
    result = resolve_reference_attack(unit, target, state(unit), state(target), unit.main_weapon,
        dice, key="x", decisions=StrictDecisions([]))
    assert result.parried and not result.defender.initiative_penalty
    dice.finish()
    result = strike(unit, target, [("hit", 1)])
    assert not result.hit and not result.defender.initiative_penalty


def test_mim_regeneration_heals_full_ordinary_maximum_and_preserves_real_multiwound_reactions():
    unit, target = attacker(), attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects, damage_die_sides=3))
    target = replace(target, global_effects=replace(target.global_effects,
        tags=(*target.global_effects.tags, "mechanic.mim-regeneration", "skill.monstrous",
            "condition.petru-fortitude", "acid_blood")))
    dice = StrictDice([{"key": "x.attack.0.hit", "value": 4},
        {"key": "x.attack.0.wound", "value": 4},
        {"key": "x.attack.0.damage", "value": 2, "sides": 3},
        {"key": "x.attack.0.mim-regeneration", "value": 4},
        {"key": "x.attack.0.acid-blood.0.wound", "value": 1},
        {"key": "x.attack.0.acid-blood.1.wound", "value": 1}])
    decisions = StrictDecisions([{"key": "x.attack.0.mim-regeneration", "value": True}])
    _, second, results = _resolve_attack_pool(unit, target, state(unit),
        replace(state(target), wounds=1), 1, dice, key="x", first_round=False,
        charging=False, decisions=decisions)
    assert second.wounds == 3  # base2 + Monstrous; spent extra Petru W is not restored
    assert second.condition == phases.Condition.STANDING
    assert results[0].damage == 2 and not results[0].saved and results[0].wounded
    dice.finish(); decisions.finish()


def test_mim_regeneration_decline_does_not_exhaust_but_first_failure_prevents_later_attempts():
    unit, target = attacker(), attacker()
    target = replace(target, characteristics=replace(target.characteristics, wounds=5),
        global_effects=replace(target.global_effects,
            tags=(*target.global_effects.tags, "mechanic.mim-regeneration")))
    first, second = state(unit), state(target)
    for label, attempt, failure, expected in (("a", False, None, 4), ("b", True, 3, 3), ("c", None, None, 2)):
        rolls = [{"key": f"{label}.hit", "value": 4}, {"key": f"{label}.wound", "value": 4}]
        if failure is not None:
            rolls += [{"key": f"{label}.mim-regeneration", "value": failure}]
        dice = StrictDice(rolls)
        decisions = StrictDecisions([{"key": f"{label}.mim-regeneration", "value": attempt}]
            if attempt is not None else [])
        result = resolve_reference_attack(unit, target, first, second, unit.main_weapon,
            dice, key=label, decisions=decisions)
        first, second = result.attacker, result.defender
        assert second.wounds == expected
        assert ("mim-regeneration-exhausted" in second.resources_spent) == (label != "a")
        dice.finish(); decisions.finish()


@pytest.mark.parametrize("helpless", [False, True])
def test_mim_regeneration_precedes_automatic_out_from_an_established_wound_and_allows_fire(helpless):
    unit, target = attacker(), attacker()
    unit = replace(unit, global_effects=replace(unit.global_effects,
        tags=(*unit.global_effects.tags, "attack.fire")))
    target = replace(target, injury_profile=0 if helpless else 2,
        global_effects=replace(target.global_effects,
            tags=(*target.global_effects.tags, "mechanic.mim-regeneration")))
    current = replace(state(target), wounds=1,
        condition=phases.Condition.KNOCKED_DOWN if helpless else phases.Condition.STANDING)
    rolls = [] if helpless else [{"key": "x.hit", "value": 4}]
    rolls += [{"key": "x.wound", "value": 4}, {"key": "x.mim-regeneration", "value": 4}]
    dice = StrictDice(rolls)
    decisions = StrictDecisions([{"key": "x.mim-regeneration", "value": True}])
    result = resolve_reference_attack(unit, target, state(unit), current, unit.main_weapon,
        dice, key="x", decisions=decisions, helpless_at_start=helpless)
    assert result.defender.wounds == 2 and result.defender.condition == current.condition
    assert result.damage == 1 and not result.saved
    dice.finish(); decisions.finish()


# The printed Dwarf-slayer-cult Parry clause binds the single failed-parry
# reroll to two Dwarf axes or to a Dwarf axe and a sword in either hand order,
# while it keeps the one-parry limit and grants no reroll to two swords.
def dwarf_combatant(main_weapon, off_hand):
    # Both arming orders sit inside the printed slayer equipment list, where the
    # clause belongs, so each compiled side runs the real eligibility route.
    return canonical("dwarf-slayer-cult-web", "giant-slayer", main_weapon,
                     off_hand_id=off_hand)


def test_dwarf_axe_with_sword_gains_the_printed_failed_parry_reroll():
    for combo in (("weapon.dwarf-axe", "weapon.sword"), ("weapon.sword", "weapon.dwarf-axe")):
        fighter = dwarf_combatant(*combo)
        assert fighter.main_weapon.parry or fighter.off_hand.parry
        context = _parry_context(fighter, state(fighter), fighter.main_weapon, 3, 4, "p")
        assert context.reroll is True, combo


def test_dwarf_axe_pair_keeps_the_reroll_and_two_swords_get_none():
    pair = dwarf_combatant("weapon.dwarf-axe", "weapon.dwarf-axe")
    assert _parry_context(pair, state(pair), pair.main_weapon, 3, 4, "p").reroll is True
    # The one-parry-per-phase limit stays: the printed pair gives up the second
    # parry in exchange for the reroll, and never parries twice.
    assert _parry_capacity(pair) == 1
    swords = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 3, 3, 1, leadership=7),
        main_weapon_id="weapon.sword", off_hand_id="weapon.sword"))
    assert swords.main_weapon.parry and swords.off_hand.parry
    context = _parry_context(swords, state(swords), swords.main_weapon, 3, 4, "p")
    assert context.reroll is False

"""T13 A-block: the printed weapon variants inside a resolved round.

The Ladle denies the armour the defender wears while the saving throws from a
shield or a skill still resolve; the pool modifiers keep the Barbed Whip's
single whipcrack bonus; the Cleaver keeps the bearer's Strength and its printed
armour modifier.
"""
from __future__ import annotations

from mordheim_combat.modular.contexts import prepare_armour_context
from mordheim_combat.modular.contexts import prepare_special_save_context
from mordheim_combat.modular.contexts import prepare_wound_context
from mordheim_combat.modular.rounds import apply_round_weapon_attack_modifiers
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat.phases import armour_target, resolve_armour
from mordheim_combat.phases import resolve_special_save, resolve_wound
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.contracts import effect_index
from mordheim_core.models import Characteristics, FighterBuild


def build(main_weapon_id, armour_id="armour.no-armour", off_hand_id=None, **options):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(4, 3, 3, 3, 3, 1, leadership=7),
        main_weapon_id=main_weapon_id, armour_id=armour_id, off_hand_id=off_hand_id,
        **options))


def wound_stage(attacker_weapon, defender):
    attacker = build(attacker_weapon)
    me = initialize_fighter(attacker, StrictDice([]), "probe")
    enemy = initialize_fighter(defender, StrictDice([]), "probe")
    return prepare_wound_context(attacker, defender, me, enemy,
                                 attacker.main_weapon, attacker.main_weapon, key="wound")


def armour_stage(attacker_weapon, defender):
    attacker = build(attacker_weapon)
    me = initialize_fighter(attacker, StrictDice([]), "probe")
    enemy = initialize_fighter(defender, StrictDice([]), "probe")
    return prepare_armour_context(attacker, defender, me, enemy,
                                  attacker.main_weapon, attacker.main_weapon, key="armour")


def test_the_ladle_denies_a_defender_wearing_heavy_armour_any_save():
    stage = armour_stage("weapon.ladle", build("weapon.mace", armour_id="armour.heavy-armour"))
    assert armour_target(stage) > 6
    assert resolve_armour(stage, StrictDice([])).eligible is False


def test_the_ladle_denies_the_worn_armour_but_keeps_the_shield_save():
    stage = armour_stage("weapon.ladle", build("weapon.mace", armour_id="armour.heavy-armour",
                                               off_hand_id="defence.shield"))
    assert armour_target(stage) == 6
    assert resolve_armour(stage, StrictDice([{"key": "armour", "value": 6}])).saved is True
    assert resolve_armour(stage, StrictDice([{"key": "armour", "value": 5}])).saved is False


def test_the_ladle_leaves_an_unarmoured_defender_with_only_its_shield():
    stage = armour_stage("weapon.ladle", build("weapon.mace", off_hand_id="defence.shield"))
    assert armour_target(stage) == 6


def test_an_ordinary_mace_still_lets_the_worn_armour_save():
    armoured = build("weapon.mace", armour_id="armour.heavy-armour")
    assert armour_target(armour_stage("weapon.mace", armoured)) == 5
    assert armour_target(armour_stage("weapon.ladle", armoured)) > 6


def test_the_cleaver_attack_costs_the_defender_one_point_of_armour_save():
    armoured = build("weapon.mace", armour_id="armour.heavy-armour")
    # The printed -1 to the save is the axe modifier and the bearer keeps its
    # own Strength, so the attack carries no Strength term either.
    assert armour_target(armour_stage("weapon.mace", armoured)) == 5
    assert armour_target(armour_stage("weapon.cleaver", armoured)) == 6


def test_the_cleaver_wounds_at_the_bearer_strength():
    """"Strength: As user": the printed -1 is the save modifier, not Strength."""
    context = wound_stage("weapon.cleaver", build("weapon.mace"))
    assert context.strength == 3                      # the bearer's own Strength
    assert context.toughness == 3
    # Strength 3 against Toughness 3 wounds on 4+; a Strength penalty would
    # move the target to 5+ and this roll would fail.
    result = resolve_wound(context, StrictDice([{"key": "wound", "value": 4}]))
    assert result.target == 4
    assert result.success is True


def test_the_ladle_denies_an_equipment_ward_and_keeps_a_skill_save():
    """The printed clause keeps saves "from shields or skills" only."""
    ladle = effect_index("mordheim")["weapon.ladle"].effect
    skins = build("weapon.mace", defence_ids=("defence.enchanted-skins",))
    assert skins.global_effects.ward_save == 6        # the equipment ward
    denied = prepare_special_save_context(skins, ladle, key="special")
    assert denied.ward_save > 6
    assert resolve_special_save(denied, StrictDice([])).saved is False
    step = build("weapon.mace", skill_ids=("skill.step-aside",))
    kept = prepare_special_save_context(step, ladle, key="special")
    assert kept.ward_save == 5
    assert resolve_special_save(
        kept, StrictDice([{"key": "special.ward", "value": 5}])).saved is True


def test_the_barbed_whip_adds_one_whipcrack_attack_when_it_charges():
    whip = build("weapon.barbed-whip")
    foe = build("weapon.mace")
    assert apply_round_weapon_attack_modifiers(
        whip, foe, 2, first_round=True, charging=True, charged=False) == 3
    assert apply_round_weapon_attack_modifiers(
        whip, foe, 2, first_round=True, charging=False, charged=True) == 3
    # A plain mace never gains the whipcrack attack.
    assert apply_round_weapon_attack_modifiers(
        foe, whip, 2, first_round=True, charging=True, charged=False) == 2

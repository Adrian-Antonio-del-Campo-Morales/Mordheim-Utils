"""C14b discriminators: physical kits and intrinsic defences.

Each case names the printed provenance it discriminates: the instrument hand
that limits the Piper's legal combinations, the House Guard plate armour whose
printed 4+ composes through the ordinary armour path only for its printed
recipient, the Gromril suit that follows its physical piece, the intrinsic
Gibbet cage that is not carried equipment, and the Witch Elf's drugs and
martial-arts save.  Cases reuse the existing compile -> initialize -> resolve
path; no new harness.
"""
from __future__ import annotations

import pytest

from mordheim_combat.modular.equipment import equipment_for_state
from mordheim_combat.modular.state import FighterState
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import desktop_call
from mordheim_core.models import Characteristics, FighterBuild
from mordheim_knowledge.loader import knowledge_root, load_bands, load_simulation_mappings

ROOT = knowledge_root()
BANDS = {str(pack.band["id"]): pack for collection in ("mordheim", "trollheim")
         for pack in load_bands(collection, ROOT)}


def fighter(band_id, profile_id, **options):
    return FighterBuild("mordheim", Characteristics(3, 3, 3, 3, 3, 1, leadership=7),
                        band_id=band_id, profile_id=profile_id,
                        main_weapon_id=options.pop("main_weapon_id", "weapon.mace"), **options)


def profile_row(band_id, profile_id):
    return next(row for row in BANDS[band_id].profiles if str(row["id"]) == profile_id)


def offers(band_id, profile_id, **options):
    build = fighter(band_id, profile_id, **options)
    facts = desktop_call("profileFacts", build, ROOT, package=BANDS[band_id],
                         profile=profile_row(band_id, profile_id))
    return {str(offer["item_id"]) for offer in facts["equipment_access"] or ()}


# --- the instrument hand (Cursed Piper) -------------------------------------
def test_the_instrument_hand_forbids_the_double_handed_weapon_only_for_the_piper():
    two_handed = "weapon.double-handed-weapon"
    # The same printed weapon and the same equipment list stay legal for the
    # Piper's fellow Heroes: the restriction's recipient is the Piper alone.
    assert compile_fighter(fighter("cursed-cavalcade", "companions", main_weapon_id=two_handed))
    with pytest.raises(ValueError, match="may not be used by cursed-cavalcade/cursed-piper"):
        compile_fighter(fighter("cursed-cavalcade", "cursed-piper", main_weapon_id=two_handed))


def test_the_instrument_hand_leaves_one_one_handed_weapon_available():
    armed = compile_fighter(fighter("cursed-cavalcade", "cursed-piper", main_weapon_id="weapon.sword"))
    assert armed.main_weapon is not None
    with pytest.raises(ValueError, match="at most 1 one-handed weapon"):
        compile_fighter(fighter("cursed-cavalcade", "cursed-piper",
                                main_weapon_id="weapon.sword", off_hand_id="weapon.dagger"))


# --- House Guard plate armour ------------------------------------------------
def test_the_printed_four_plus_plate_armour_composes_through_the_ordinary_path():
    mappings = {row["item_id"]: row for row in load_simulation_mappings("mordheim")["item_mappings"]}
    assert mappings["house_guard_plate_armour"]["mechanic_id"] == "armour.plate-armour"
    assert "armour.plate-armour" in offers("house-guard-sc", "commander", variant_ids=("house.baluardo",))
    wearer = compile_fighter(fighter("house-guard-sc", "commander", variant_ids=("house.baluardo",),
                                     armour_id="armour.plate-armour", main_weapon_id="weapon.sword"))
    assert wearer.armour_save == 4
    # The ordinary path keeps every other armour on its own printed profile.
    heavy = compile_fighter(fighter("house-guard-sc", "commander", variant_ids=("house.baluardo",),
                                    armour_id="armour.heavy-armour", main_weapon_id="weapon.sword"))
    assert heavy.armour_save == 5


def test_the_plate_armour_recipient_stays_a_printed_variant_and_keeps_the_special_list():
    # House Baluardo prints it in the Heroes list; the ungated special list
    # carries the same item with the same printed 4+.
    assert "armour.plate-armour" not in offers("house-guard-sc", "commander")
    special = next(row for row in BANDS["house-guard-sc"].equipment_lists
                   if str(row["id"]) == "special-house-guard-equipment")
    assert [str(item["item_id"]) for item in special["items"]][0] == "house_guard_plate_armour"


# --- Att'la's Plate Mail and the transformation front ------------------------
def artefact(**options):
    """The artefact is found by exploration, so no band list gates it."""
    return FighterBuild("mordheim", Characteristics(3, 3, 3, 3, 3, 1, leadership=7),
                        main_weapon_id="weapon.sword", **options)


def test_attlas_gromril_save_and_fortitude_wound_follow_the_physical_piece():
    worn = compile_fighter(artefact(armour_id="armour.attlas-plate-mail"))
    assert (worn.armour_save, worn.characteristics.wounds) == (4, 4)
    plate = next(item for item in worn.mutation_equipment if item.slot == "armour")
    assert "material.gromril" in plate.effect.tags
    # Removing the piece withdraws both the Gromril 4+ and the Fortitude Wound.
    removed = compile_fighter(artefact())
    assert (removed.armour_save, removed.characteristics.wounds) == (7, 3)


def test_a_transformation_casts_off_the_worn_piece_and_keeps_the_innate_rules():
    worn = compile_fighter(artefact(skill_ids=("skill.ignore-pain",),
                                    armour_id="armour.attlas-plate-mail"))
    cast = equipment_for_state(worn, FighterState(wounds=worn.characteristics.wounds, transformed=True),
                               first_round=False)
    assert (cast.armour_save, cast.characteristics.wounds) == (7, 3)
    assert "skill.ignore-pain" in cast.global_effects.tags


def test_the_intrinsic_gibbet_cage_is_not_carried_equipment():
    gibbets = compile_fighter(fighter("ghost-pirates-sar", "gibbets", main_weapon_id="weapon.fist"))
    assert gibbets.armour_save == 5
    # The cage is a quality of the Gibbets, not a piece: casting equipment off
    # keeps its 5+ while the worn Gromril suit above lost its 4+.
    cast = equipment_for_state(gibbets, FighterState(wounds=gibbets.characteristics.wounds, transformed=True),
                              first_round=False)
    assert cast.armour_save == 5
    with pytest.raises(ValueError, match='"armour-suit" is forbidden'):
        compile_fighter(fighter("ghost-pirates-sar", "gibbets", armour_id="armour.heavy-armour",
                                main_weapon_id="weapon.fist"))


# --- Witch Elf: drugs and martial arts ---------------------------------------
def canonical_witch(**options):
    """The Witch Elf as the band configures her: no weapon is selected, so her
    own printed kit is the loadout."""
    return compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 3, 3, 1, leadership=7),
                                        band_id="dark-elf-corsairs-mou", profile_id="witch-elf", **options))


@pytest.mark.parametrize("selection", [{}, {"main_weapon_id": "weapon.sword"}])
def test_the_printed_kit_arms_both_hands_with_a_coated_dark_elven_blade(selection):
    witch = canonical_witch(**selection)
    for weapon in (witch.main_weapon, witch.off_hand):
        assert {"weapon.sword", "material.dark-elf-blade", "poison.black-venom"} <= set(weapon.tags)
        assert (weapon.strength_bonus, weapon.critical_injury_bonus, weapon.concussion) == (1, 1, True)
    assert witch.off_hand_attacks
    # Each blade is its own carried piece; the kit's own items are what she
    # carries, and the qualification and coating are consumed by those copies.
    assert [item.item_id for item in witch.mutation_equipment if item.slot in {"main", "off"}] == ["sword", "sword"]
    assert not [item for item in witch.mutation_equipment if item.slot is None]
    # The drugs and the martial-arts defence connected earlier stay untouched.
    assert witch.global_effects.frenzy and witch.natural_armour_save == 5


def test_the_printed_kit_concedes_no_generic_access():
    row = profile_row("dark-elf-corsairs-mou", "witch-elf")
    assert row["equipment_lists"] == []
    # Her own printed pieces and their operators are the whole offer, so the
    # shared engine answers every caller without conceding a generic list.
    assert offers("dark-elf-corsairs-mou", "witch-elf") == {
        "sword", "dark_elf_blade_weapon_upgrade", "dark_venom",
        "weapon.sword", "material.dark-elf-blade", "poison.black-venom"}


def test_the_dark_venom_raises_the_strength_of_her_attacks():
    from mordheim_combat import phases
    from mordheim_combat.modular.contexts import prepare_armour_context
    from mordheim_combat.modular.state import initialize_fighter
    from mordheim_core.dice import ScriptedDice

    plain = compile_fighter(fighter("dark-elf-corsairs-mou", "corsairs", main_weapon_id="weapon.sword"))

    def armour_target(attacker):
        defender = compile_fighter(FighterBuild(
            "mordheim", Characteristics(3, 3, 3, 3, 3, 1, leadership=7),
            main_weapon_id="weapon.sword", armour_id="armour.light-armour"))
        context = prepare_armour_context(
            attacker, defender, initialize_fighter(attacker, ScriptedDice({}), "a"),
            initialize_fighter(defender, ScriptedDice({}), "d"),
            attacker.main_weapon, attacker.main_weapon, key="wound")
        return phases.armour_target(context)

    # One Strength higher when wounding and when the armour save is modified:
    # the coated blade leaves a 6+ light armour no save at all.
    assert (armour_target(plain), armour_target(canonical_witch())) == (6, 7)


def test_the_second_blade_adds_the_one_attack_the_engine_already_grants():
    from mordheim_combat.phases import AttackPoolContext, build_attacks

    witch = canonical_witch()
    plain = compile_fighter(fighter("dark-elf-corsairs-mou", "corsairs", main_weapon_id="weapon.sword"))
    assert witch.characteristics.attacks == 1
    # Attack 1 doubled by the drugs, plus the single attack of a second weapon,
    # which frenzy must not duplicate.
    assert (build_attacks(AttackPoolContext(plain)).attacks,
            build_attacks(AttackPoolContext(witch)).attacks) == (1, 3)


def test_the_witch_elf_drugs_grant_frenzy_without_touching_her_fellows():
    witch = compile_fighter(fighter("dark-elf-corsairs-mou", "witch-elf", main_weapon_id="weapon.fist"))
    assert witch.global_effects.frenzy
    sorceress = compile_fighter(fighter("dark-elf-corsairs-mou", "sorceress", main_weapon_id="weapon.fist"))
    assert not sorceress.global_effects.frenzy


def test_the_martial_arts_save_is_an_intrinsic_five_plus_against_a_wound():
    from mordheim_combat import phases
    from mordheim_combat.modular.contexts import prepare_armour_context
    from mordheim_combat.modular.state import initialize_fighter
    from mordheim_core.dice import ScriptedDice

    witch = compile_fighter(fighter("dark-elf-corsairs-mou", "witch-elf", main_weapon_id="weapon.fist"))
    assert witch.natural_armour_save == 5
    def save_of(attacker):
        return prepare_armour_context(
            attacker, witch, initialize_fighter(attacker, ScriptedDice({}), "a"),
            initialize_fighter(witch, ScriptedDice({}), "d"),
            attacker.main_weapon, attacker.main_weapon, key="wound")

    context = save_of(compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 3, 2, 1, leadership=7), main_weapon_id="weapon.sword")))
    assert phases.armour_target(context) == 5
    assert not phases.resolve_armour(context, ScriptedDice({"wound": 4})).saved
    assert phases.resolve_armour(context, ScriptedDice({"wound": 5})).saved
    # The printed save is modified by the attacker's Strength, as an armour save.
    stronger = save_of(compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 4, 3, 3, 2, 1, leadership=7), main_weapon_id="weapon.sword")))
    assert phases.armour_target(stronger) == 6

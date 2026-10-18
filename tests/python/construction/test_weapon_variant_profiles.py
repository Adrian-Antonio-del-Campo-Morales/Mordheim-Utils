"""Printed weapon variants get their own catalogue operator.

Source (``sources/knowledge``):

* ``catalog/items/weapons-close-combat.yaml`` / ``cleaver``: *"Strength: As user
  -1 Save : Target gets -1 to armour save"* — the printed Strength column is "As
  user" and the ``-1`` belongs to the Save column — and
  ``cleaver_counts_as_axe``: the Cleaver counts as an Axe.
* ``catalog/items/weapons-close-combat.yaml`` / ``barbed_whip``: *"Strength: As
  user Whipcrack"* — no Strength penalty and no *cannot be parried* property.
* ``catalog/items/weapons-close-combat.yaml`` / ``ladle``: *"No save except
  shields … The only saving throws allowed are from shields or skills."*

Each printed variant now resolves to its own ``weapon.*`` operator through the
item record, so the shared ``weapon.axe`` / ``weapon.beastlash`` / ``weapon.mace``
profiles keep their own printed text.
"""
from __future__ import annotations

import pytest

from mordheim_combat import phases
from mordheim_combat.modular.equipment import whipcrack_weapon
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.contracts import effect_index
from mordheim_core.models import Characteristics, FighterBuild
from mordheim_knowledge.loader import load_items, load_simulation_mappings

VARIANTS = {
    "cleaver": "weapon.cleaver",
    "cleaver_counts_as_axe": "weapon.cleaver",
    "barbed_whip": "weapon.barbed-whip",
    "ladle": "weapon.ladle",
}


def build(main_weapon_id, **options):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(4, 3, 3, 3, 3, 1, leadership=7),
        main_weapon_id=main_weapon_id, **options))


def test_each_printed_variant_resolves_to_its_own_operator():
    mappings = {row["item_id"]: row
                for row in load_simulation_mappings("mordheim", None)["item_mappings"]}
    for item_id, mechanic_id in VARIANTS.items():
        assert mappings[item_id]["status"] == "implemented", item_id
        assert mappings[item_id]["mechanic_id"] == mechanic_id, item_id


def test_the_cleaver_keeps_the_bearer_strength_and_counts_as_an_axe():
    cleaver = build("weapon.cleaver").main_weapon
    # "Strength: As user": the printed -1 belongs to the Save column, so the
    # weapon carries the armour modifier and no Strength penalty.
    assert cleaver.strength_bonus == 0
    assert cleaver.armour_penetration == 1
    # The identity the printed clause names, while the Cleaver profile governs.
    assert "weapon.axe" in cleaver.tags
    assert build("weapon.axe").main_weapon.strength_bonus == 0


def test_the_barbed_whip_prints_no_strength_penalty_and_no_cannot_be_parried():
    whip = build("weapon.barbed-whip").main_weapon
    assert whip.strength_bonus == 0
    assert whip.cannot_be_parried is False
    # The Beastlash keeps its own printed -1 and unparryable property.
    beastlash = build("weapon.beastlash").main_weapon
    assert beastlash.strength_bonus == -1 and beastlash.cannot_be_parried is True


def test_the_barbed_whip_still_carries_the_whipcrack_bonus():
    assert whipcrack_weapon(build("weapon.barbed-whip")) is not None
    assert whipcrack_weapon(build("weapon.mace")) is None


def test_the_ladle_operator_publishes_the_shield_and_skill_exception():
    ladle = effect_index("mordheim")["weapon.ladle"].effect
    assert ladle.ignore_armour_except_shield_and_skills is True
    assert ladle.concussion is True
    # It is a mace profile for every other purpose.
    ladle_weapon = build("weapon.ladle").main_weapon
    assert "weapon.mace" in ladle_weapon.tags and "weapon.ladle" in ladle_weapon.tags


@pytest.mark.parametrize("off_hand,armour,expected", [
    (None, "armour.no-armour", 7),
    (None, "armour.heavy-armour", 7),
    ("defence.shield", "armour.no-armour", 6),
    ("defence.shield", "armour.heavy-armour", 6),
])
def test_only_shield_and_skill_saves_survive_the_ladle(off_hand, armour, expected):
    fighter = build("weapon.ladle", off_hand_id=off_hand, armour_id=armour)
    allowed = max(1, 7 - fighter.shield_and_skill_effects.armour_save_bonus)
    assert allowed == expected


def test_a_save_from_another_provenance_does_not_join_the_ladle_exception():
    """The printed clause keeps shields and skills, not every other source."""
    cloaked = build("weapon.ladle", defence_ids=("defence.wolf-pelt-cloak",))
    # The pelt cloak does improve the composite save ...
    assert cloaked.armour_save == 6
    # ... but it is neither a shield nor a skill, so the clause denies it.
    assert max(1, 7 - cloaked.shield_and_skill_effects.armour_save_bonus) == 7


def test_a_skill_ward_is_the_only_special_save_the_ladle_keeps():
    skins = build("weapon.mace", defence_ids=("defence.enchanted-skins",))
    assert skins.global_effects.ward_save == 6
    assert skins.shield_and_skill_effects.ward_save == 7
    step = build("weapon.mace", skill_ids=("skill.step-aside",))
    assert step.global_effects.step_aside is True
    assert step.shield_and_skill_effects.step_aside is True
# --- C07a: each item reaches the operator its own source prints --------------
# The R13 coordinator withdrew this block's earlier closure: a binding, and a
# test that built the bound operator directly, did not establish that the
# printed entry carries that operator's clause.  The discriminators below read
# the canonical record and its item->mechanic mapping, then reach the consumer.


def items():
    return {row["id"]: row for row in load_items("mordheim", None)}


def mappings():
    return {row["item_id"]: row
            for row in load_simulation_mappings("mordheim", None)["item_mappings"]}


def test_the_belaying_pin_is_the_thrown_weapon_its_source_lists():
    """The Pirate and Swabbie lists print it under *Missile Weapons*.

    Everything the record prints is the thrown Range 6" profile with its
    awkward-thrown range and move modifiers, which is the excluded shooting
    subsystem.  The withdrawn `weapon.mace` binding implied an unprinted
    Concussion, so the pin carries no close-combat operator at all, and the
    Channel Rats wording stays recorded as separate provenance instead of
    being collapsed into the Town Crier text.
    """
    pin = items()["belaying_pin"]
    assert pin["kind"] == "ranged-weapon"
    assert pin["combat_status"] == "out_of_scope"
    assert "mechanic_id" not in pin
    assert [ref["printed_page"] for ref in pin["source_refs"]] == [0, 0, 178]
    assert mappings()["belaying_pin"] == {"item_id": "belaying_pin",
                                          "status": "out_of_scope"}
    # The Concussion the old binding asserted belongs to the Mace record only.
    assert items()["mace"]["mechanic_id"] == "weapon.mace"
    assert build("weapon.mace").main_weapon.concussion is True


def test_the_sunstaff_is_the_missile_weapon_its_source_lists():
    """The Heroines list prints it under *Missile Weapons*, at Range 24.

    Nothing in the printed entry is a two-handed, Strength +1 or ignition
    clause, so the `weapon.brazier-iron` equivalence is withdrawn.  The other
    source's Lustria copy keeps its own record: this decision is not extended
    to it.
    """
    staff = items()["sunstaff"]
    assert staff["kind"] == "ranged-weapon"
    assert staff["combat_status"] == "out_of_scope"
    assert "mechanic_id" not in staff
    assert 'Range: 24"' in staff["effect"] and "Accurate" in staff["effect"]
    assert mappings()["sunstaff"] == {"item_id": "sunstaff",
                                      "status": "out_of_scope"}
    lustria = items()["sunstaff_lustria"]
    assert lustria["combat_status"] == "implemented"
    assert lustria["mechanic_id"] == "weapon.brazier-iron"
    assert mappings()["sunstaff_lustria"]["engine_option"] == "Brazier iron"


def test_the_sun_gauntlet_melee_half_is_the_off_hand_strength_four_attack():
    assert items()["sun_gauntlet"]["mechanic_id"] == "weapon.sun-gauntlet"
    with pytest.raises(ValueError, match="illegal main-hand selection"):
        build("weapon.sun-gauntlet", armour_id="armour.no-armour")
    fighter = build("weapon.sword", off_hand_id="weapon.sun-gauntlet",
                    armour_id="armour.no-armour")
    gauntlet = fighter.off_hand
    assert gauntlet.fixed_strength == 4
    assert gauntlet.ignore_armour is True


# --- R13: the Yari's two printed grips, offered from its own canonical line ---
# What a bearer buys is the object: one item record (``yari``), one list line
# (15 gc, Silent Hunter only) and one carried weapon. Its two printed modes are
# declared by that record (``alternate_mechanic_ids``), so the offer, the
# acceptance and the compiled attack all follow the item instead of a second,
# invented object with its own line.

YARI_GRIPS = ("weapon.yari-one-handed", "weapon.yari-two-handed")


def silent_hunter(profile_id="silent-hunter"):
    from mordheim_combat_lab.application.catalogue import CombatCatalogue
    catalogue = CombatCatalogue()
    choice = next(row for row in catalogue.profiles("trollheim", "chaos-streets-deathbringers")
                  if row.profile_id == profile_id)
    return catalogue, choice


def grip_build(main_weapon_id, **options):
    """Compile a grip through its printed recipient, not through a bare id."""
    return compile_fighter(FighterBuild(
        "mordheim", collection="trollheim", band_id="chaos-streets-deathbringers",
        profile_id="silent-hunter", main_weapon_id=main_weapon_id, **options))


def test_the_yari_record_declares_both_printed_grips_of_one_object():
    yari = items()["yari"]
    assert yari["combat_status"] == "implemented"
    assert yari["mechanic_id"] == "weapon.yari-one-handed"
    assert yari["alternate_mechanic_ids"] == ["weapon.yari-two-handed"]
    # One object and one bridge: the register keeps a single row whose default
    # profile is unchanged, and no item record is invented for the second grip.
    assert mappings()["yari"]["mechanic_id"] == "weapon.yari-one-handed"
    assert mappings()["yari"]["alternate_mechanic_ids"] == ["weapon.yari-two-handed"]
    assert [row["id"] for row in load_items("mordheim", None)
            if row.get("mechanic_id") in YARI_GRIPS] == ["yari"]


def test_both_printed_grips_are_offered_and_accepted_from_the_same_line():
    catalogue, choice = silent_hunter()
    offered = dict(catalogue.weapons(choice))
    assert [grip for grip in YARI_GRIPS if grip in offered] == list(YARI_GRIPS)
    # A single line prices the object, not the mode: its own 15 gc either way.
    assert {catalogue.cost(grip, choice) for grip in YARI_GRIPS} == {15.0}
    # Each grip is selectable in the editor's own decision, not merely listable.
    assert catalogue.equipment_decisions(choice, YARI_GRIPS, slot="main") == dict.fromkeys(YARI_GRIPS)
    # The same one carried object covers either grip in the complete kit.
    for grip in YARI_GRIPS:
        assert not catalogue.validate_configuration(
            choice, possession=("yari",), slots={"main_weapon_id": grip})


def test_each_grip_transports_to_the_modular_attack_with_its_printed_properties():
    opponent = build("weapon.dagger", armour_id="armour.no-armour")
    one_handed = grip_build("weapon.yari-one-handed", owned_item_ids=("yari",))
    assert one_handed.main_weapon.parry is True and one_handed.main_weapon.two_handed is False
    two_handed = grip_build("weapon.yari-two-handed", owned_item_ids=("yari",))
    assert two_handed.main_weapon.parry is True and two_handed.main_weapon.two_handed is True
    # The modular duel's own priority resolver reads the compiled weapon, so the
    # two-handed grip reaches the round with its printed Strike First.
    assert phases.resolve_priority(
        phases.PriorityContext(one_handed, opponent, first_round=True)).priority == 0
    assert phases.resolve_priority(
        phases.PriorityContext(two_handed, opponent, first_round=True)).priority == 1


def test_the_two_handed_grip_rejects_an_incompatible_secondary_hand():
    catalogue, choice = silent_hunter()
    # The one-handed grip keeps the legal secondary hand the printed profile allows.
    assert catalogue.equipment_decisions(
        choice, ("weapon.dagger",), slot="off",
        main_weapon_id="weapon.yari-one-handed") == {"weapon.dagger": None}
    assert grip_build("weapon.yari-one-handed", off_hand_id="weapon.dagger",
                      owned_item_ids=("yari", "dagger")).off_hand is not None
    # The two-handed grip occupies both hands, in the selection decision itself
    # and at compilation.
    blocked = catalogue.equipment_decisions(
        choice, ("weapon.dagger",), slot="off",
        main_weapon_id="weapon.yari-two-handed")
    assert "occupies both hands" in blocked["weapon.dagger"]
    with pytest.raises(ValueError, match="occupies both hands"):
        grip_build("weapon.yari-two-handed", off_hand_id="weapon.dagger",
                   owned_item_ids=("yari", "dagger"))


def test_neither_grip_reaches_a_recipient_whose_list_omits_the_object():
    catalogue, choice = silent_hunter("shadow-blade")
    assert not [grip for grip in YARI_GRIPS if grip in dict(catalogue.weapons(choice))]
    for grip in YARI_GRIPS:
        assert catalogue.validate_configuration(
            choice, possession=("yari",), slots={"main_weapon_id": grip})
    assert "not on any equipment list" in catalogue.equipment_decisions(
        choice, ("yari",), slot="main")["yari"]

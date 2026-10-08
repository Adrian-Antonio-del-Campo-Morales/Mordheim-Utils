"""T13 A-block: printed weapon variants get their own catalogue operator.

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

from mordheim_combat.modular.equipment import whipcrack_weapon
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.contracts import effect_index
from mordheim_core.models import Characteristics, FighterBuild
from mordheim_knowledge.loader import load_simulation_mappings

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

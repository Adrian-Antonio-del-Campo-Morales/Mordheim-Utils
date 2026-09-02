"""Restricciones de Savage: toda armadura, pero no las armas cuerpo a cuerpo."""
import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild


def build(profile="orc-nuttaz", **equipment):
    return FighterBuild("mordheim", band_id="black-orcs", profile_id=profile, **equipment)


@pytest.mark.parametrize("equipment", [
    {"armour_id": "armour.light-armour"},
    {"off_hand_id": "defence.shield"},
    {"defence_ids": ("defence.helmet",)},
    {"main_weapon_id": "weapon.pistol"},
    {"off_hand_id": "weapon.pistol"},
    {"main_weapon_id": "weapon.duelling-pistol"},
])
def test_savage_rejects_forbidden_equipment_by_rule(equipment):
    with pytest.raises(ValueError, match="armour is forbidden|missile weapons are forbidden"):
        compile_fighter(build(**equipment))


@pytest.mark.parametrize("weapon", ["weapon.dagger", "weapon.axe", "weapon.sword"])
def test_savage_preserves_melee_access(weapon):
    fighter = compile_fighter(build(main_weapon_id=weapon))
    assert weapon in fighter.main_weapon.tags
    assert fighter.global_effects.attacks_bonus == 1


@pytest.mark.parametrize("equipment", [
    {"armour_id": "armour.light-armour"},
    {"off_hand_id": "defence.shield"},
    {"defence_ids": ("defence.helmet",)},
])
def test_savage_does_not_restrict_ordinary_boyz(equipment):
    compile_fighter(build("orc-boyz", **equipment))

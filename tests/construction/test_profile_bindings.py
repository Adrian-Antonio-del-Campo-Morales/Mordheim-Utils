"""Bindings automáticos de perfil."""
from __future__ import annotations

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
import pytest as pytest


def test_profile_characteristics_projects_selected_bonuses():
    ordinary = compile_fighter(FighterBuild(
        "mordheim", band_id="mercenaries", profile_id="mercenary-captain",
    ))
    middenheimer = compile_fighter(FighterBuild(
        "mordheim", band_id="mercenaries", profile_id="mercenary-captain",
        special_rule_ids=("band--middenheim-physical-prowess",),
    ))
    assert middenheimer.characteristics.strength == ordinary.characteristics.strength + 1


def test_profile_fist_overrides_the_unarmed_profile_fallback():
    peasant = compile_fighter(FighterBuild(
        "mordheim", band_id="battle-monks-of-cathay", profile_id="raging-peasants",
    ))
    assert "weapon.fist" in peasant.main_weapon.tags
    assert peasant.main_weapon.strength_bonus == -1
    assert peasant.main_weapon.target_armour_bonus == 1


def test_profile_natural_attacks_selects_the_natural_weapon():
    warhound = compile_fighter(FighterBuild(
        "mordheim", band_id="beastmen-raiders", profile_id="warhounds-of-chaos",
    ))
    assert "weapon.natural-attacks" in warhound.main_weapon.tags
    assert "weapon.fist" not in warhound.main_weapon.tags


def test_profile_random_characteristics_preserves_the_exact_dice_contract():
    condemned = compile_fighter(FighterBuild(
        "mordheim", band_id="marauders-of-chaos", profile_id="condemned",
    ))
    assert condemned.random_characteristics == (
        ("WS", 1, 6, 0),
        ("S", 1, 6, 0),
        ("T", 1, 6, 0),
        ("A", 1, 3, 0),
    )


def test_profile_equipment_restrictions_have_a_legal_and_an_illegal_case():
    compile_fighter(FighterBuild(
        "mordheim", band_id="horned-hunters", profile_id="priest-of-taal",
    ))
    with pytest.raises(ValueError, match="equipment is not available|heavy armour is forbidden"):
        compile_fighter(FighterBuild(
            "mordheim", band_id="horned-hunters", profile_id="priest-of-taal",
            armour_id="armour.heavy-armour",
        ))


def test_profile_skill_access_has_a_rejected_and_granted_strength_skill():
    with pytest.raises(ValueError, match="skills are not available"):
        compile_fighter(FighterBuild(
            "mordheim", band_id="dark-elves", profile_id="high-born",
            skill_ids=("skill.mighty-blow",),
        ))
    granted = compile_fighter(FighterBuild(
        "mordheim", band_id="dark-elves", profile_id="high-born",
        skill_ids=("skill.mighty-blow",),
        special_rule_ids=("band--dark-elf-special-skills-powerful-build",),
    ))
    assert granted.global_effects.strength_bonus == 1

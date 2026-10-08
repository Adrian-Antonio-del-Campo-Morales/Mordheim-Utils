"""T13 A-block: the Dragon Monk's printed unarmed mastery.

Source (``sources/knowledge``): ``bands/mordheim/pirates-of-the-cathayan-sea-sar/
profiles.yaml`` / ``dragon-monk`` / ``equipment_restrictions``: *"May never wear
armour. Suffers no penalties for fighting unarmed and receives +1 Attack when
doing so."*

The profile rule ``dragon-monk--unarmed-mastery`` publishes that clause as the
shared ``skill.unarmed-fighting`` operator, which the attack pool and the
strength and armour stages all read: the bearer resolves one attack more than its
profile Attacks value and its unarmed attacks carry neither the fist's Strength
penalty nor its armour bonus.  The armour ban keeps its own executed consequence
in the shared qualification stage.
"""
from __future__ import annotations

import pytest

from mordheim_combat.modular.contexts import _attack_strength, _combined_effect
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat.phases import AttackPoolContext, build_attacks
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild


def build(profile_id="dragon-monk", weapon="weapon.fist", **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id="pirates-of-the-cathayan-sea-sar", profile_id=profile_id,
        main_weapon_id=weapon, **options))


def plain(strength=3):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(4, strength, 3, 3, 3, 1, leadership=7),
        main_weapon_id="weapon.fist"))


def test_the_profile_rule_publishes_the_shared_operator():
    from mordheim_construction.combat_packages import combat_packages

    rule = next(rule for pack in combat_packages("mordheim", None)
                for rule in pack.special_rules
                if rule["id"] == "dragon-monk--unarmed-mastery")
    assert rule["runtime"]["implemented"] == "YES"
    assert rule["applies_to"]["profile_ids"] == ["dragon-monk"]
    assert [effect["binding"] for effect in rule["runtime"]["effects"]] == [
        {"kind": "mechanic", "id": "skill.unarmed-fighting"}]
    # Only the dragon-monk carries the operator's tag.
    assert "skill.unarmed-fighting" in build().global_effects.tags
    assert "skill.unarmed-fighting" not in plain().global_effects.tags


def test_the_unarmed_monk_resolves_one_attack_more_than_its_profile_value():
    monk = build()
    assert monk.characteristics.attacks == 1
    assert build_attacks(AttackPoolContext(monk)).attacks == 2
    # The bonus belongs to the printed "when doing so": armed, the monk keeps A1.
    assert build_attacks(AttackPoolContext(build(weapon="weapon.dagger"))).attacks == 1


def test_another_unarmed_fighter_keeps_the_single_attack_clamp():
    assert build_attacks(AttackPoolContext(build("shanghaires"))).attacks == 1


def test_the_unarmed_monk_suffers_neither_the_fist_strength_penalty_nor_its_armour_bonus():
    monk, foe = build(), plain()
    control = build("shanghaires")
    states = {fighter: initialize_fighter(fighter, StrictDice([]), "probe")
              for fighter in (monk, control, foe)}
    effect = _combined_effect(monk, monk.main_weapon)
    assert _attack_strength(monk, foe, states[monk], monk.main_weapon, effect,
                            False, False)[0] == monk.characteristics.strength
    control_effect = _combined_effect(control, control.main_weapon)
    assert _attack_strength(control, foe, states[control], control.main_weapon,
                            control_effect, False, False)[0] == control.characteristics.strength - 1


def test_the_printed_armour_ban_keeps_its_executed_consequence():
    with pytest.raises(ValueError, match="armour"):
        build(armour_id="armour.light-armour")
    assert build(armour_id="armour.no-armour") is not None

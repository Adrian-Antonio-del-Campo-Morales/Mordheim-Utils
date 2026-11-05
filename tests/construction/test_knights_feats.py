"""Knights Feats selection keeps its printed recipients and local effects."""
from dataclasses import replace

import pytest

from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild


@pytest.mark.parametrize("band,recipient", [
    ("bretonnian-knights-errant-mou", "knights-errant"),
    ("bretonnian-brigands-mou", "fallen-noble"),
    ("disciples-of-maldred-mou", "questing-knights"),
])
def test_combat_charge_is_offered_and_compiles_without_permanent_bonuses(band, recipient):
    catalogue = CombatCatalogue()
    choice = next(profile for profile in catalogue.profiles(
        "mordheim", band) if profile.profile_id == recipient)
    offered = {skill.id: skill for skill in catalogue.skills(choice)}
    assert offered["skill.combat-charge"].runtime_available
    assert ("skill.sword-master" in offered) is (band == "bretonnian-knights-errant-mou")
    assert "skill.lancer" not in offered
    assert offered["skill.armour-specialist"].runtime_available
    assert catalogue.skill_rule_ids(("skill.combat-charge",)) == (("skill.combat-charge",), ())
    build = FighterBuild("mordheim", band_id=band,
                         profile_id=recipient, main_weapon_id="weapon.sword")
    absent = compile_fighter(build)
    selected = compile_fighter(replace(build, skill_ids=("skill.combat-charge",)))
    assert "skill.combat-charge" not in absent.global_effects.tags
    assert selected.global_effects.tags.count("skill.combat-charge") == 1
    assert selected.characteristics == absent.characteristics
    assert selected.global_effects.attacks_bonus == absent.global_effects.attacks_bonus == 0


@pytest.mark.parametrize("band,recipient", [
    ("bretonnian-knights-errant-mou", "knights-errant"),
    ("bretonnian-brigands-mou", "fallen-noble"),
    ("disciples-of-maldred-mou", "questing-knights"),
])
def test_armour_specialist_is_offered_without_permanent_save_or_movement_bonuses(band, recipient):
    catalogue = CombatCatalogue()
    choice = next(profile for profile in catalogue.profiles(
        "mordheim", band) if profile.profile_id == recipient)
    offered = {skill.id: skill for skill in catalogue.skills(choice)}
    assert offered["skill.armour-specialist"].runtime_available
    assert "skill.lancer" not in offered
    assert catalogue.skill_rule_ids(("skill.armour-specialist",)) == (("skill.armour-specialist",), ())
    build = FighterBuild("mordheim", band_id=band, profile_id=recipient,
                         main_weapon_id="weapon.sword", armour_id="armour.heavy-armour",
                         off_hand_id="defence.shield")
    absent = compile_fighter(build)
    selected = compile_fighter(replace(build, skill_ids=("skill.armour-specialist",)))
    assert "skill.armour-specialist" not in absent.global_effects.tags
    assert selected.global_effects.tags.count("skill.armour-specialist") == 1
    assert selected.characteristics == absent.characteristics
    assert selected.armour_save == absent.armour_save
    assert selected.global_effects.armour_save_floor == absent.global_effects.armour_save_floor == 7


@pytest.mark.parametrize("skill", ["skill.combat-charge", "skill.armour-specialist"])
@pytest.mark.parametrize("band,profile,variants", [
    ("bretonnian-knights-errant-mou", "squires", ()),
    ("bretonnian-knights-errant-mou", "squires", ("promotion.hero",)),
    ("bretonnian-brigands-mou", "scarface", ()),
    ("disciples-of-maldred-mou", "prophet", ()),
    ("disciples-of-maldred-mou", "squires", ()),
    ("mercenaries", "mercenary-captain", ()),
])
def test_knights_feat_is_refused_outside_its_printed_recipients(band, profile, variants, skill):
    with pytest.raises(ValueError, match="skill"):
        compile_fighter(FighterBuild("mordheim", band_id=band, profile_id=profile,
            main_weapon_id="weapon.sword", variant_ids=variants,
            skill_ids=(skill,)))

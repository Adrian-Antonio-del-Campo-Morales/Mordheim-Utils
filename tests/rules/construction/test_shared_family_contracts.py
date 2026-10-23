"""Construction contracts shared by the vectorized rule families.

Moved from ``tests/engines/vectorized/test_shared_families.py`` by T08: the
subject is warband construction (rejections and skill access), not the
vectorized engine.
"""
from __future__ import annotations

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
from pathlib import Path
import pytest as pytest


ROOT = Path(__file__).resolve().parents[3] / "sources/knowledge"


def build(band, profile, *, collection="mordheim", **kwargs):
    return FighterBuild("mordheim", band_id=band, profile_id=profile, collection=collection, **kwargs)


@pytest.mark.phase5_vectorized
def test_shared_compiler_contracts_enforce_construction_rules():
    with pytest.raises(ValueError, match="poisons are forbidden"):
        compile_fighter(build(
            "battle-monks-of-cathay", "dragon-monks", main_poison_id="poison.black-lotus",
        ), ROOT)
    with pytest.raises(ValueError, match="drugs are forbidden"):
        compile_fighter(build(
            "lustria-high-elves", "sword-guardians", collection="trollheim",
            preparation_ids=("preparation.crimson-shade",),
        ), ROOT)
    antidote = compile_fighter(build(
        "lustria-high-elves", "sword-guardians", collection="trollheim",
        preparation_ids=("preparation.tears-of-shallaya",),
    ), ROOT)
    assert antidote.global_effects.poison_immunity

    with pytest.raises(ValueError, match="at least one mutation"):
        compile_fighter(build("cult-of-the-possessed", "mutants"), ROOT)
    mutant = compile_fighter(build(
        "cult-of-the-possessed", "mutants",
        special_rule_ids=("band--mutations-tentacle",),
    ), ROOT)
    assert mutant.global_effects.incoming_attacks_modifier == -1


@pytest.mark.phase5_vectorized
def test_arms_master_censer_bearer_skill_access_and_pit_fighter_trait():
    with pytest.raises(ValueError, match="occupies both hands"):
        compile_fighter(build(
            "pit-fighters", "pit-king", main_weapon_id="weapon.flail", off_hand_id="weapon.dagger",
        ), ROOT)
    arms_master = compile_fighter(build(
        "pit-fighters", "pit-king", main_weapon_id="weapon.flail", off_hand_id="weapon.dagger",
        special_rule_ids=("band--pit-fighter-skill-arms-master",),
    ), ROOT)
    assert arms_master.off_hand_attacks

    with pytest.raises(ValueError, match="requires Black Hunger"):
        compile_fighter(build(
            "skaven-clan-pestilens", "plague-priest", main_weapon_id="weapon.censer",
            special_rule_ids=("band--clan-pestilens-special-skills-censer-bearer",),
        ), ROOT)
    bearer = compile_fighter(build(
        "skaven-clan-pestilens", "plague-priest", main_weapon_id="weapon.censer",
        special_rule_ids=(
            "band--clan-pestilens-special-skills-black-hunger",
            "band--clan-pestilens-special-skills-censer-bearer",
        ),
    ), ROOT)
    assert bearer.global_effects.frenzy

    ogre = compile_fighter(build(
        "pit-fighters", "ogre-pit-fighter", skill_ids=("skill.mighty-blow",),
    ), ROOT)
    assert ogre.global_effects.strength_bonus == 1
    assert "pit_fighter" in arms_master.global_effects.tags

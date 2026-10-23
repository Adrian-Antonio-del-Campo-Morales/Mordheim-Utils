"""Selectable construction bindings."""
from __future__ import annotations

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
import pytest as pytest


def build(band_id, profile_id, *, collection="mordheim", **kwargs):
    return FighterBuild(
        "mordheim", band_id=band_id, profile_id=profile_id,
        collection=collection, **kwargs,
    )


@pytest.mark.phase2_construction
def test_berserker_accepts_alone_and_rejects_ferocious_charge():
    berserker = "band--troll-slayer-special-skills-berserker"
    ferocious = "band--troll-slayer-special-skills-ferocious-charge"
    accepted = compile_fighter(build(
        "pit-fighters", "dwarf-troll-slayer", special_rule_ids=(berserker,),
    ))
    assert "compiler.berserker-incompatible-with-ferocious-charge" in accepted.construction_tags
    with pytest.raises(ValueError, match="may not be combined"):
        compile_fighter(build(
            "pit-fighters", "dwarf-troll-slayer",
            special_rule_ids=(berserker, ferocious),
        ))


@pytest.mark.phase2_construction
def test_censer_bearer_rejects_missing_prerequisite_and_accepts_exact_loadout():
    censer_bearer = "band--clan-pestilens-special-skills-censer-bearer"
    with pytest.raises(ValueError, match="requires Black Hunger"):
        compile_fighter(build(
            "skaven-clan-pestilens", "plague-priest",
            main_weapon_id="weapon.censer", special_rule_ids=(censer_bearer,),
        ))
    accepted = compile_fighter(build(
        "skaven-clan-pestilens", "plague-priest", main_weapon_id="weapon.censer",
        special_rule_ids=(
            "band--clan-pestilens-special-skills-black-hunger", censer_bearer,
        ),
    ))
    assert accepted.global_effects.frenzy
    assert "compiler.censer-bearer-loadout" in accepted.construction_tags


@pytest.mark.phase2_construction
def test_chaos_engineer_is_an_explicit_positive_only_duel_contract():
    # Chaos Armour and rarity rolls are outside the 1v1 catalogue.  Selection
    # is still observable, but there is no legal in-scope forbidden item from
    # which to manufacture a meaningful negative duel fixture.
    engineer = compile_fighter(build(
        "black-dwarfs", "sorcerer",
        special_rule_ids=("band--chaos-dwarf-special-skills-chaos-engineer",),
    ))
    assert "compiler.chaos-engineer" in engineer.construction_tags


@pytest.mark.phase2_construction
def test_arms_master_lifts_the_two_handed_offhand_restriction():
    kwargs = dict(main_weapon_id="weapon.flail", off_hand_id="weapon.dagger")
    with pytest.raises(ValueError, match="occupies both hands"):
        compile_fighter(build("pit-fighters", "pit-king", **kwargs))
    accepted = compile_fighter(build(
        "pit-fighters", "pit-king", **kwargs,
        special_rule_ids=("band--pit-fighter-skill-arms-master",),
    ))
    assert accepted.off_hand_attacks
    assert "compiler.ignore-difficult-to-use-restrictions" in accepted.construction_tags


@pytest.mark.phase2_construction
def test_master_of_arms_lifts_the_same_restriction_for_maneaters():
    kwargs = dict(
        main_weapon_id="weapon.double-handed-weapon", off_hand_id="weapon.sword",
    )
    with pytest.raises(ValueError, match="occupies both hands"):
        compile_fighter(build("maneaters", "captain", **kwargs))
    accepted = compile_fighter(build(
        "maneaters", "captain", **kwargs,
        special_rule_ids=("band--ogres-special-skills-master-of-arms",),
    ))
    assert accepted.off_hand_attacks
    assert "compiler.master-of-arms" in accepted.construction_tags


@pytest.mark.phase2_construction
def test_master_of_throwing_weapons_changes_the_compiled_limit():
    ordinary = compile_fighter(build(
        "lustria-savage-goblins", "trackers", collection="trollheim",
    ))
    master = compile_fighter(build(
        "lustria-savage-goblins", "trackers", collection="trollheim",
        special_rule_ids=("band--savage-goblin-special-skills-master-of-throwing-weapons",),
    ))
    assert ordinary.missile_weapon_limit == 2
    assert master.missile_weapon_limit == 5


@pytest.mark.phase2_construction
def test_proven_warrior_accepts_younguns_and_rejects_other_profiles():
    rule = "band--black-orc-special-skills-proven-warrior"
    accepted = compile_fighter(build(
        "black-orcs", "younguns", main_weapon_id="weapon.double-handed-weapon",
        special_rule_ids=(rule,),
    ))
    assert "compiler.proven-warrior" in accepted.construction_tags
    with pytest.raises(ValueError, match="Young'un"):
        compile_fighter(build(
            "black-orcs", "black-orc-boss", special_rule_ids=(rule,),
        ))


@pytest.mark.phase2_construction
def test_renowned_virtue_requires_exactly_one_foreign_virtue():
    renowned = "band--renowned-virtue"
    with pytest.raises(ValueError, match="exactly one"):
        compile_fighter(build(
            "bretonnian-chapel-guard", "questing-knight",
            special_rule_ids=(renowned,),
        ))
    accepted = compile_fighter(build(
        "bretonnian-chapel-guard", "questing-knight",
        special_rule_ids=(renowned, "band--virtue-of-valour"),
    ))
    assert "compiler.renowned-virtue" in accepted.construction_tags
    assert "skill.virtue-of-valour" in accepted.global_effects.tags


@pytest.mark.phase2_construction
def test_trollheim_grizzled_veteran_is_a_chosen_hero_skill():
    """The printed Hero skill is selected, never granted to the whole band."""
    rule = "band--pit-fighter-skill-grizzled-veteran"
    plain = compile_fighter(build(
        "chaos-streets-pit-fighters", "pit-veterans", collection="trollheim",
    ))
    assert "mechanic.psychology-immunity" not in plain.global_effects.tags
    accepted = compile_fighter(build(
        "chaos-streets-pit-fighters", "pit-veterans", collection="trollheim",
        special_rule_ids=(rule,),
    ))
    assert "mechanic.psychology-immunity" in accepted.global_effects.tags
    # A henchman profile outside the printed eligibility list cannot take it.
    with pytest.raises(ValueError, match=rule):
        compile_fighter(build(
            "chaos-streets-pit-fighters", "pit-fighters", collection="trollheim",
            special_rule_ids=(rule,),
        ))

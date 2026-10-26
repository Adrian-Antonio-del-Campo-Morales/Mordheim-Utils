"""Construction contracts formerly grouped with the vectorized rule families.

Moved from the vectorized engine suite by T08: the subject is warband
construction (rejections, tags and access limits), not the vectorized engine.
"""
from __future__ import annotations

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
from pathlib import Path
import pytest as pytest


ROOT = Path(__file__).resolve().parents[2] / "sources/knowledge"


def build(band, profile, *, collection="mordheim", **kwargs):
    return FighterBuild("mordheim", band_id=band, profile_id=profile, collection=collection, **kwargs)


def test_animal_friendship_and_contagious_traits_are_selectable_and_enforce_prerequisites():
    friend = compile_fighter(build(
        "horned-hunters", "horned-hunter",
        special_rule_ids=("band--horned-hunter-special-skills-animal-friendship",),
    ), ROOT)
    assert "animal_friendship" in friend.global_effects.tags

    with pytest.raises(ValueError, match="requires Rotten Body"):
        compile_fighter(build(
            "lustria-clan-pestilens", "plague-priest", collection="trollheim",
            special_rule_ids=("band--clan-pestilens-special-skills-contagious",),
        ), ROOT)
    contagious = compile_fighter(build(
        "lustria-clan-pestilens", "plague-priest", collection="trollheim",
        special_rule_ids=(
            "band--clan-pestilens-special-skills-rotten-body",
            "band--clan-pestilens-special-skills-contagious",
        ),
    ), ROOT)
    assert "contagious" in contagious.global_effects.tags


def test_construction_contracts_enforce_access_restrictions_and_limits():
    outlaw = compile_fighter(build("outlaws-of-stirwood-forest", "bandit-leader"), ROOT)
    tracker = compile_fighter(build(
        "lustria-savage-goblins", "trackers", collection="trollheim",
        special_rule_ids=("band--savage-goblin-special-skills-master-of-throwing-weapons",),
    ), ROOT)
    assert outlaw.missile_weapon_limit == 1
    assert tracker.missile_weapon_limit == 5

    with pytest.raises(ValueError, match="poisons are forbidden for Knights"):
        compile_fighter(build(
            "bretonnian-chapel-guard", "questing-knight",
            main_poison_id="poison.black-lotus",
        ), ROOT)
    # Tribe choice belongs to warband construction and to the campaign
    # (including mounted options), not to the 1v1 duel builder.
    with pytest.raises(ValueError, match="choose exactly one Foreign or Native background"):
        compile_fighter(build(
            "khemri-lahmian-brotherhood", "lahmian-vampire", collection="trollheim",
            variant_ids=("background.foreign", "background.native"),
        ), ROOT)


def test_pirate_mercenary_access_master_of_arms_and_mutation_contracts():
    pirate = compile_fighter(build(
        "lustria-pirates", "pirate-captain", collection="trollheim",
        armour_id="armour.heavy-armour",
    ), ROOT)
    assert pirate.armour_save <= 5

    ogre = compile_fighter(build(
        "maneaters", "captain", main_weapon_id="weapon.double-handed-weapon", off_hand_id="weapon.sword",
        special_rule_ids=("band--ogres-special-skills-master-of-arms",),
    ), ROOT)
    assert ogre.off_hand_attacks

    with pytest.raises(ValueError, match="at least one mutation"):
        compile_fighter(build("cult-of-the-possessed", "mutants"), ROOT)
    possessed = compile_fighter(build(
        "cult-of-the-possessed", "mutants",
        special_rule_ids=("band--mutations-tentacle",),
    ), ROOT)
    assert possessed.global_effects.incoming_attacks_modifier == -1


def test_remaining_meta_contracts_compile_for_their_legal_profiles():
    builds = (
        build("carnival-of-chaos", "tainted-ones", special_rule_ids=("band--blessings-of-nurgle-bloated-foulness",)),
        build("black-dwarfs", "sorcerer", special_rule_ids=("band--chaos-dwarf-special-skills-chaos-engineer",)),
        build("chaos-streets-undead-bloodlines", "von-carstein-vampire", collection="trollheim"),
        build("outlaws-of-stirwood-forest", "cleric"),
        build("lustria-high-elves", "sword-guardians", collection="trollheim"),
        build("bretonnian-chapel-guard", "squires"),
    )
    assert all(compile_fighter(candidate, ROOT) for candidate in builds)

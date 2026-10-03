"""T13.2b -- Bloated Foulness compiles its Movement reduction.

Source: Carnival of Chaos / Blessings of Nurgle / Bloated Foulness, 40 gc.
"The Tainted One is a huge, disgusting mass of diseased, flabby folds. It gains
+1 Wound and +1 Toughness but has its Movement reduced by -1."

The expectations below are derived from the canonical ``tainted-ones`` profile
plus the rule's own text, not from the compiler contract that is under test.
Blessings of Nurgle are mandatory for a Tainted One, so the control is a
blessing that grants no characteristic (Nurgle's Rot, which only grants poison
immunity).
"""
from __future__ import annotations

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands


BLESSING = "band--blessings-of-nurgle-bloated-foulness"
MARK_OF_NURGLE = "band--blessings-of-nurgle-mark-of-nurgle"
NURGLES_ROT = "band--blessings-of-nurgle-nurgles-rot"


def _canonical_tainted_one():
    """The printed profile, read from the canonical knowledge base."""
    package = next(band for band in load_bands("mordheim") if band.band["id"] == "carnival-of-chaos")
    return next(profile for profile in package.profiles if profile["id"] == "tainted-ones")


def _compile(*special_rule_ids):
    return compile_fighter(FighterBuild(
        "mordheim", band_id="carnival-of-chaos", profile_id="tainted-ones",
        special_rule_ids=special_rule_ids,
    ))


def test_control_blessing_matches_the_printed_profile():
    printed = _canonical_tainted_one()["characteristics"]
    control = _compile(NURGLES_ROT)
    assert control.characteristics.movement == printed["M"]
    assert control.characteristics.toughness == printed["T"]
    assert control.characteristics.wounds == printed["W"]
    assert control.characteristics.leadership == printed["Ld"]


def test_bloated_foulness_moves_movement_down_one_and_toughness_and_wounds_up_one():
    printed = _canonical_tainted_one()["characteristics"]
    bloated = _compile(BLESSING)
    assert bloated.characteristics.movement == printed["M"] - 1
    assert bloated.characteristics.toughness == printed["T"] + 1
    assert bloated.characteristics.wounds == printed["W"] + 1


def test_bloated_foulness_leaves_weapon_skill_strength_initiative_attacks_and_leadership_alone():
    control = _compile(NURGLES_ROT)
    bloated = _compile(BLESSING)
    for field in ("weapon_skill", "strength", "initiative", "attacks", "leadership"):
        assert getattr(bloated.characteristics, field) == getattr(control.characteristics, field)


def test_mark_of_nurgle_keeps_its_wound_bonus_without_the_movement_reduction():
    control = _compile(NURGLES_ROT)
    marked = _compile(MARK_OF_NURGLE)
    assert marked.characteristics.wounds == control.characteristics.wounds + 1
    assert marked.characteristics.toughness == control.characteristics.toughness
    assert marked.characteristics.movement == control.characteristics.movement


def test_both_blessings_accumulate_each_contribution_exactly_once():
    control = _compile(NURGLES_ROT)
    both = _compile(BLESSING, MARK_OF_NURGLE)
    assert both.characteristics.wounds == control.characteristics.wounds + 2
    assert both.characteristics.toughness == control.characteristics.toughness + 1
    assert both.characteristics.movement == control.characteristics.movement - 1
    assert both.characteristics.leadership == control.characteristics.leadership


def test_bloated_foulness_keeps_movement_a_known_integer():
    bloated = _compile(BLESSING)
    assert isinstance(bloated.characteristics.movement, int)
    assert bloated.characteristics.movement != 0

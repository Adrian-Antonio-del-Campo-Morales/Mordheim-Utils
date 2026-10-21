"""The shared preparations and characteristic bonuses.

Each clause is proved at its printed recipient: the canonical compiler applies
the bonus or supplied result to that model, a non-recipient is refused or stays
unchanged, and the printed limit (the Brewers' "never greater than 10") holds.
The Brewers' fear and frenzy results are exercised by the sibling suite;
this file covers the third result of the same table and the remaining
selections.
"""
from __future__ import annotations

import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild

BREWER = "dwarf-guildsmen-kaz"
REMASSEN = "band--remasen-officer-leadership"
REMAS = "band--remas-officer-leadership"
PALADIN = "band--necromantic-modification-paladin-of-horror"
MIDDENHEIM = "band--middenheim-physical-prowess"


def canonical(band, profile, *, collection="mordheim", **options):
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band, profile_id=profile, collection=collection, **options))


# --- Brewers: the fifth and sixth result of the same supplied table ---------

@pytest.mark.rule_behavior
def test_the_special_brew_raises_both_characteristics_and_stops_at_ten():
    plain = canonical(BREWER, "master-craftsman")
    drinker = canonical(BREWER, "master-craftsman",
                        condition_ids=("condition.troll-brew-special-brew",))
    assert drinker.characteristics.weapon_skill == plain.characteristics.weapon_skill + 1
    assert drinker.characteristics.strength == plain.characteristics.strength + 1
    # Only the two printed characteristics move.
    assert drinker.characteristics.initiative == plain.characteristics.initiative
    # "This may temporarily take the statistics above the normal racial
    # maximum but never greater than 10."
    advanced = canonical(BREWER, "master-craftsman",
                         characteristics=Characteristics(10, 10, 3, 1, 4, 1,
                                                        movement=3, leadership=9),
                         condition_ids=("condition.troll-brew-special-brew",))
    assert (advanced.characteristics.weapon_skill, advanced.characteristics.strength) == (10, 10)


@pytest.mark.eligibility
def test_one_brew_is_drawn_per_battle_and_only_a_guildsmen_dwarf_drinks_it():
    with pytest.raises(ValueError, match="only one"):
        canonical(BREWER, "master-craftsman", condition_ids=(
            "condition.troll-brew-frenzy", "condition.troll-brew-special-brew"))
    with pytest.raises(ValueError, match="Dwarf of the Guildsmen"):
        canonical("tileans", "captain", condition_ids=("condition.troll-brew-frenzy",))
    with pytest.raises(ValueError, match="Hero"):
        canonical(BREWER, "artisans", condition_ids=("condition.troll-brew-special-brew",))
    with pytest.raises(ValueError, match="Dwarf of the Guildsmen"):
        canonical(BREWER, "master-craftsman", trait_overrides={"species": "human"},
                  condition_ids=("condition.troll-brew-special-brew",))


# --- Remas and Remasen officers --------------------------------------------

@pytest.mark.eligibility
def test_remas_and_remasen_officers_keep_their_printed_recipients():
    remasen = canonical("tileans", "captain")
    assert canonical("tileans", "captain",
                     special_rule_ids=(REMASSEN,)).characteristics.leadership == \
        remasen.characteristics.leadership + 1
    remas = canonical("lustria-tileans", "mercenary-captain", collection="trollheim")
    assert canonical("lustria-tileans", "mercenary-captain", collection="trollheim",
                     special_rule_ids=(REMAS,)).characteristics.leadership == \
        remas.characteristics.leadership + 1
    # A henchman of either warband is not a printed recipient of the rule.
    for band, collection in (("tileans", "mordheim"), ("lustria-tileans", "trollheim")):
        with pytest.raises(ValueError, match="not available"):
            canonical(band, "warriors", collection=collection,
                      special_rule_ids=((REMASSEN if collection == "mordheim" else REMAS),))


# --- The Necromantic Abomination's Paladin of Horror ------------------------

@pytest.mark.eligibility
def test_paladin_of_horror_reaches_the_abomination_only():
    plain = canonical("khemri-necromancers", "necromantic-abomination", collection="trollheim")
    modified = canonical("khemri-necromancers", "necromantic-abomination", collection="trollheim",
                         special_rule_ids=(PALADIN,))
    assert modified.characteristics.leadership == plain.characteristics.leadership + 1
    with pytest.raises(ValueError, match="not available"):
        canonical("khemri-necromancers", "necromancer", collection="trollheim",
                  special_rule_ids=(PALADIN,))


# --- Power Grab: the supplied race-majority state ---------------------------

@pytest.mark.rule_behavior
def test_power_grab_adjusts_the_supplied_race_once():
    plain = canonical("underworld-alliance-mim", "goblin-bully")
    majority = canonical("underworld-alliance-mim", "goblin-bully",
                         condition_ids=("condition.power-grab-majority",))
    minority = canonical("underworld-alliance-mim", "goblin-bully",
                         condition_ids=("condition.power-grab-minority",))
    assert majority.characteristics.leadership == plain.characteristics.leadership + 1
    assert minority.characteristics.leadership == plain.characteristics.leadership - 1
    # A race is one or the other at match start, never both.
    with pytest.raises(ValueError, match="only one"):
        canonical("underworld-alliance-mim", "goblin-bully", condition_ids=(
            "condition.power-grab-majority", "condition.power-grab-minority"))
    with pytest.raises(ValueError, match="Underworld Alliance"):
        canonical("tileans", "captain", condition_ids=("condition.power-grab-majority",))


# --- One selected bonus, however the caller names it -----------------------

@pytest.mark.compilation
def test_a_repeated_selection_applies_its_bonus_once():
    once = canonical("tileans", "captain", special_rule_ids=(REMASSEN,))
    assert canonical("tileans", "captain",
                     special_rule_ids=(REMASSEN, REMASSEN)).characteristics.leadership == \
        once.characteristics.leadership
    middenheim = canonical("mercenaries", "mercenary-captain", special_rule_ids=(MIDDENHEIM,))
    assert canonical("mercenaries", "mercenary-captain",
                     special_rule_ids=(MIDDENHEIM, MIDDENHEIM)).characteristics.strength == \
        middenheim.characteristics.strength == 4
    # The supplied condition route already resolves a repeated id once; the
    # printed ceiling of the Special Brew is not doubled either.
    brew = canonical(BREWER, "master-craftsman",
                     condition_ids=("condition.troll-brew-special-brew",))
    assert canonical(BREWER, "master-craftsman", condition_ids=(
        "condition.troll-brew-special-brew", "condition.troll-brew-special-brew",
    )).characteristics == brew.characteristics


# --- The shared Middenheim origin -------------------------------------------

@pytest.mark.eligibility
def test_the_middenheim_variant_raises_only_its_two_printed_profiles():
    # The printed clause is the absolute "Strength 4 instead of Strength 3"; the
    # KB prints 3 for both profiles of both bands, so the shared +1 bonus and the
    # printed sentence are the same value.
    for band, collection, variant in (("mercenaries", "mordheim", MIDDENHEIM),
                                      ("trollheim-mercenaries", "trollheim", MIDDENHEIM)):
        for profile in ("mercenary-captain", "champions"):
            plain = canonical(band, profile, collection=collection)
            chosen = canonical(band, profile, collection=collection, special_rule_ids=(variant,))
            assert plain.characteristics.strength == 3
            assert chosen.characteristics.strength == 4
        with pytest.raises(ValueError, match="not available"):
            canonical(band, "warriors", collection=collection, special_rule_ids=(variant,))


# --- The supplied Human Rememberer -----------------------------------------

# Primary: the supplied override compiles the printed Human line and switches
# the equipment list. The paired refusals are the secondary guarantee.
@pytest.mark.compilation
def test_the_human_rememberer_uses_its_printed_line_and_the_mercenary_list():
    human = {"trait_overrides": {"species": "human"}}
    dwarf = canonical("dwarf-slayers-kaz", "rememberer")
    supplied = canonical("dwarf-slayers-kaz", "rememberer", **human)
    # The printed Human line: M4 WS4 BS2 S3 T3 W1 I4 A1 Ld7.
    assert (supplied.characteristics.movement, supplied.characteristics.weapon_skill,
            supplied.characteristics.strength, supplied.characteristics.toughness,
            supplied.characteristics.wounds, supplied.characteristics.initiative,
            supplied.characteristics.attacks, supplied.characteristics.leadership) == (4, 4, 3, 3, 1, 4, 1, 7)
    assert "species.human" in supplied.global_effects.tags
    # "instead equipped from the Mercenary equipment list": the rulebook list
    # opens the Mercenary items and no longer the Dwarf Warrior list.
    assert canonical("dwarf-slayers-kaz", "rememberer",
                     main_weapon_id="weapon.dwarf-axe").main_weapon.tags == ("weapon.dwarf-axe", "material.normal")
    assert canonical("dwarf-slayers-kaz", "rememberer", main_weapon_id="weapon.morning-star",
                     **human).main_weapon.tags == ("weapon.morning-star", "material.normal")
    for options, weapon in ((human, "weapon.dwarf-axe"), ({}, "weapon.morning-star")):
        with pytest.raises(ValueError, match="not available"):
            canonical("dwarf-slayers-kaz", "rememberer", main_weapon_id=weapon, **options)

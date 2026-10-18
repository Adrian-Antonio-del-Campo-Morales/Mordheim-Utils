"""Warpaint and Elven Wine as executable battle preparations.

Both printed clauses leave the same question open: what "one use only" means,
and who may take the object.  The answer reuses the existing preparation
operator instead of a new consumable subsystem: the build declares the object
once, the item's printed market clause names the bands that may take it, and the
band's own equipment list is the other printed route to it.  The effect is
applied at ``duel_start`` and covers that battle, so a saving throw or a Fear
test never spends it and no general psychology immunity is granted.

Warpaint: 6+ invulnerable save, also useable by the Savage Goblin Boyz.
Elven Wine: immune to Fear for the whole battle, for the bearer that drinks it.
"""
from __future__ import annotations

from dataclasses import replace

import pytest

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.contexts import prepare_special_save_context
from mordheim_combat.modular.psychology import causes_fear, resolve_fear
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice
from mordheim_construction.combat_packages import combat_packages
from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import desktop_call
from mordheim_core.models import DuelContext, FighterBuild

WARPAINT = "preparation.warpaint"
WINE = "preparation.elven-wine"
PACKAGES = {(collection, str(package.band["id"])): package
            for collection in ("mordheim", "trollheim") for package in combat_packages(collection)}


def build(collection, band, profile, *preparations):
    return FighterBuild("mordheim", collection=collection, band_id=band, profile_id=profile,
                        preparation_ids=tuple(preparations))


def offers(collection, band, profile):
    package = PACKAGES[(collection, band)]
    row = next(entry for entry in package.profiles if str(entry["id"]) == profile)
    return set(desktop_call("preparationOptions", build(collection, band, profile),
                            package=package, profile=row))


def refused(collection, band, profile, preparation):
    with pytest.raises(ValueError, match="printed recipients"):
        compile_fighter(build(collection, band, profile, preparation))


def tape(*pairs):
    return StrictDice([{"key": key, "value": value} for key, value in pairs])


def enemy():
    """A Strength 5 strike that wounds the Toughness 4 bearer on 2+."""
    base = compile_fighter(FighterBuild("mordheim", band_id="mercenaries",
                                        profile_id="mercenary-captain", main_weapon_id="weapon.mace"))
    return replace(base, characteristics=replace(base.characteristics, strength=5))


def attack(key="a", face=6):
    """One unsaved wound turned away by the printed 6+ save."""
    owner, foe = compile_fighter(build("mordheim", "savage-orcs-kaz", "boyz", WARPAINT)), enemy()
    dice = tape((f"{key}.hit", 4), (f"{key}.wound", 4), (f"{key}.special.ward", face))
    result = resolve_reference_attack(foe, owner, initialize_fighter(foe, tape(), f"{key}.a"),
                                     initialize_fighter(owner, tape(), f"{key}.d"),
                                     foe.main_weapon, dice, key=key, decisions=StrictDecisions([]))
    dice.finish()
    return owner, result


# --- Warpaint: recipients ---------------------------------------------------

def test_warpaint_reaches_the_printed_orc_bearers_and_the_gobbo_boyz():
    for profile in ("boyz", "gobbo-boyz"):
        assert WARPAINT in offers("mordheim", "savage-orcs-kaz", profile)
        fighter = compile_fighter(build("mordheim", "savage-orcs-kaz", profile, WARPAINT))
        assert WARPAINT in fighter.global_effects.tags


def test_warpaint_is_not_a_generic_market_consumable():
    """The Savage Orc clause is the recipient: another warband cannot take it."""
    assert WARPAINT not in offers("mordheim", "mercenaries", "mercenary-captain")
    refused("mordheim", "mercenaries", "mercenary-captain", WARPAINT)


# --- Warpaint: printed effect and single use --------------------------------

def test_warpaint_delivers_the_six_plus_invulnerable_save():
    owner, first = attack("a")
    assert owner.global_effects.ward_save == 6
    assert first.saved is True and first.defender.wounds == owner.characteristics.wounds
    assert prepare_special_save_context(owner, enemy().main_weapon, key="probe").ward_save == 6


def test_one_use_is_one_battle_application_and_never_one_saving_throw():
    """A second strike of the same duel still meets the same 6+ save."""
    _, first = attack("a")
    _, second = attack("b")
    assert first.saved is True and second.saved is True
    assert second.defender.wounds == 1
    # One supply, one application: declaring the paint twice adds nothing.
    once = compile_fighter(build("mordheim", "savage-orcs-kaz", "boyz", WARPAINT))
    twice = compile_fighter(build("mordheim", "savage-orcs-kaz", "boyz", WARPAINT, WARPAINT))
    assert twice.global_effects == once.global_effects


# --- Elven Wine: recipients -------------------------------------------------

def test_elven_wine_reaches_the_printing_lists_and_the_shadow_warrior_market():
    assert WINE in offers("trollheim", "lustria-high-elves", "sword-guardians")
    assert WINE in offers("trollheim", "chaos-streets-sons-of-nagarythe", "shadow-warrior")
    assert WINE in compile_fighter(
        build("trollheim", "lustria-high-elves", "sword-guardians", WINE)).global_effects.tags


def test_elven_wine_is_not_offered_where_no_printed_clause_reaches_it():
    # The Cadet list of the same band never prints the wine, and a mercenary is
    # not a printed recipient at all.
    assert WINE not in offers("trollheim", "lustria-high-elves", "cadets")
    refused("trollheim", "lustria-high-elves", "cadets", WINE)
    assert WINE not in offers("mordheim", "mercenaries", "mercenary-captain")
    refused("mordheim", "mercenaries", "mercenary-captain", WINE)


# --- Elven Wine: effect, recipient and single use ---------------------------

def fear_setup(wine):
    foe = compile_fighter(FighterBuild("mordheim", band_id="mercenaries",
        profile_id="mercenary-captain", trait_overrides={"causes_fear": True}))
    bearer = compile_fighter(build("trollheim", "lustria-high-elves", "sword-guardians", *wine))
    assert causes_fear(foe, bearer)
    return foe, bearer


def test_elven_wine_is_fear_immunity_for_the_bearer_and_not_psychology_immunity():
    foe, bearer = fear_setup((WINE,))
    assert "mechanic.fear-immunity" in bearer.global_effects.tags
    assert "mechanic.psychology-immunity" not in bearer.global_effects.tags
    assert "mechanic.fear-immunity" not in foe.global_effects.tags
    # The charge is met with no Fear roll at all: an empty tape is enough, and
    # StrictDice refuses an unqueued request.
    dice = StrictDice([])
    state = initialize_duel(foe, bearer, dice, context=DuelContext(
        charging=("first",), active_participant="first"))
    after = resolve_fear(foe, bearer, state, dice, StrictDecisions([]))
    assert after.second.fear_hit_sixes is False
    assert after.second.condition is state.second.condition
    assert after.engaged is True
    dice.finish()


def test_without_the_wine_the_same_fear_test_still_happens():
    foe, bearer = fear_setup(())
    assert "mechanic.fear-immunity" not in bearer.global_effects.tags
    dice = tape(("round.0.second.fear.charged.0", 6), ("round.0.second.fear.charged.1", 6))
    state = initialize_duel(foe, bearer, dice, context=DuelContext(
        charging=("first",), active_participant="first"))
    after = resolve_fear(foe, bearer, state, dice, StrictDecisions([]))
    assert after.second.fear_hit_sixes is True
    dice.finish()


def test_one_use_is_the_battle_and_a_second_declaration_changes_nothing():
    once = compile_fighter(build("trollheim", "lustria-high-elves", "sword-guardians", WINE))
    twice = compile_fighter(build("trollheim", "lustria-high-elves", "sword-guardians", WINE, WINE))
    assert twice.global_effects == once.global_effects
    assert once.global_effects.tags.count("mechanic.fear-immunity") == 1

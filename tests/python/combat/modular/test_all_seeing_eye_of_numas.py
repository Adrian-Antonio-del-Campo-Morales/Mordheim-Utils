"""Campaign artefact: the Eye of Numas supplies its printed additional 6+ save.

The Magical Artefacts Table entry is an exploration result, so its acquisition is
excluded and the bearer is *supplied*: the physical piece enters the kit and its
mechanic is selected, the same possession/selection pair the equipment catalogue
already uses for a carried defence.  The clause this file pins is the printed
additional 6+ save against strikes in close combat, which is not modified by
Strength or by weapon modifiers and resolves after the armour save.
"""
from __future__ import annotations

import pytest

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.contexts import prepare_armour_context
from mordheim_combat.modular.contexts import prepare_special_save_context
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import initialize_duel, initialize_fighter
from mordheim_combat.phases import armour_target
from mordheim_combat_lab.verification.dice import StrictDice, StrictDecisions
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, DuelContext, FighterBuild

ITEM = "all_seeing_eye_of_numas"
MECHANIC = "defence.all-seeing-eye-of-numas"


def tape(*values):
    return StrictDice([{"key": key, "value": value} for key, value in values])


def bearer(armour_id="armour.no-armour"):
    """The supplied bearer: the physical artefact is carried and selected once."""
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
        main_weapon_id="weapon.mace", armour_id=armour_id,
        defence_ids=(MECHANIC,), owned_item_ids=(ITEM,)))


def enemy(strength=3, weapon="weapon.mace"):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, strength, 3, 3, 3, 1, leadership=7),
        main_weapon_id=weapon))


def state(fighter):
    return initialize_fighter(fighter, tape(), "init")


@pytest.mark.parametrize("ward,saved", [(5, False), (6, True)])
@pytest.mark.phase3_rules
def test_the_carried_artefact_saves_on_its_printed_six_after_the_armour_save(ward, saved):
    owner, foe = bearer("armour.light-armour"), enemy()
    # Carrying the piece and selecting its mechanic deliver the one 6+ save; the
    # physical item the bearer passes around is the artefact itself.
    assert owner.global_effects.ward_save == 6
    assert [piece.item_id for piece in owner.mutation_equipment if piece.item_id == ITEM] == [ITEM]
    start = initialize_duel(foe, owner, tape(), context=DuelContext(
        charging=("first",), active_participant="first"))
    dice = tape(("round.0.first.attack.0.hit", 4), ("round.0.first.attack.0.wound", 4),
                ("round.0.first.attack.0.armour", 1),
                ("round.0.first.attack.0.special.ward", ward),
                ("round.0.second.attack.0.hit", 1))
    result = resolve_round(foe, owner, start, dice, StrictDecisions([]))
    dice.finish()
    # The worn armour is rolled first (the 1 loses the 5+) and the artefact adds
    # its own save afterwards: the wound lands unless the printed face comes up.
    assert result.state.second.wounds == (2 if saved else 1)


@pytest.mark.phase3_rules
def test_strength_and_weapon_modifiers_move_the_armour_save_but_never_the_artefact_save():
    owner = bearer("armour.heavy-armour")
    mundane, strong = enemy(), enemy(strength=5, weapon="weapon.cleaver")
    # The printed heavy armour is 5+ and it does react: Strength 5 and the
    # Cleaver's printed -1 take that save away entirely, which is exactly the
    # modifier the artefact's clause excludes from its own save.
    assert armour_target(prepare_armour_context(
        mundane, owner, state(mundane), state(owner),
        mundane.main_weapon, mundane.main_weapon, key="armour")) == 5
    assert armour_target(prepare_armour_context(
        strong, owner, state(strong), state(owner),
        strong.main_weapon, strong.main_weapon, key="armour")) > 6
    assert prepare_special_save_context(owner, mundane.main_weapon, key="special").ward_save == 6
    assert prepare_special_save_context(owner, strong.main_weapon, key="special").ward_save == 6
    # And the resolved attack keeps the printed boundary: with the armour save
    # denied, a 5 on the artefact's own die still wounds the bearer.
    dice = tape(("a.hit", 4), ("a.wound", 3), ("a.special.ward", 5))
    result = resolve_reference_attack(strong, owner, state(strong), state(owner),
                                      strong.main_weapon, dice, key="a",
                                      decisions=StrictDecisions([]))
    dice.finish()
    assert result.saved is False and result.damage == 1

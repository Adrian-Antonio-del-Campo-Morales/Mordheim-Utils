"""Entrada de todo el catálogo al motor modular."""
from __future__ import annotations

from dataclasses import replace
from mordheim_combat_lab.combat.modular.rounds import resolve_round
from mordheim_combat_lab.combat.modular.state import initialize_duel
from mordheim_combat_lab.construction.compiler import compile_fighter
from mordheim_combat_lab.domain.dice import KeyedDice
from mordheim_combat_lab.domain.models import Characteristics
from mordheim_combat_lab.domain.models import FighterBuild
from mordheim_combat_lab.knowledge.loader import load_bands
from mordheim_combat_lab.knowledge.loader import load_mechanics
from mordheim_combat_lab.knowledge.loader import load_runtime_scope
import pytest


def profile_build(collection, band_id, profile_id):
    mandatory = (
        ("band--mutations-tentacle",)
        if band_id in {"cult-of-the-possessed", "trollheim-cult-of-the-possessed"}
        and profile_id == "mutants"
        else ("band--blessings-of-nurgle-bloated-foulness",)
        if band_id == "carnival-of-chaos" and profile_id == "tainted-ones"
        else ()
    )
    return FighterBuild(
        "mordheim", band_id=band_id, profile_id=profile_id,
        collection=collection, special_rule_ids=mandatory,
    )


def test_modular_runtime_rejects_a_manually_injected_lance():
    fighter = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1)))
    lance = replace(fighter, main_weapon=replace(fighter.main_weapon, tags=("weapon.lance",)))
    with pytest.raises(ValueError, match="mounted combat is not supported"):
        initialize_duel(lance, fighter, KeyedDice(1))


def test_every_legal_profile_can_execute_a_complete_scalar_round():
    opponent = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
    ))
    executed = 0
    for collection in ("mordheim", "trollheim"):
        for band in load_bands(collection):
            for profile in band.profiles:
                fighter = compile_fighter(profile_build(
                    collection, band.band["id"], profile["id"],
                ))
                dice = KeyedDice(executed + 1)
                state = initialize_duel(fighter, opponent, dice)
                result = resolve_round(fighter, opponent, state, dice)
                assert result.state.round_index == 1
                executed += 1
    assert executed == 534


def test_every_execution_mechanism_can_enter_the_scalar_round_pipeline():
    characteristics = Characteristics(3, 3, 3, 2, 3, 1)
    opponent = compile_fighter(FighterBuild("mordheim", characteristics))
    excluded = {
        row["id"] for row in load_runtime_scope("mordheim").get("mechanic_exclusions") or ()
    }
    executed = 0
    for family in ("weapons", "armours", "defences", "materials", "preparations", "poisons", "skills"):
        for row in load_mechanics("mordheim")[family]:
            mechanic_id = row["id"]
            if mechanic_id in excluded:
                continue
            if family == "weapons":
                options = ({"main_weapon_id": mechanic_id} if row.get("main_hand")
                           else {"off_hand_id": mechanic_id})
            elif family == "armours":
                options = ({"defence_ids": (mechanic_id,)}
                           if mechanic_id == "armour.cathayan-quilted-silk"
                           else {"armour_id": mechanic_id})
            elif family == "defences":
                options = ({"off_hand_id": mechanic_id}
                           if mechanic_id in {"defence.shield", "defence.buckler", "defence.kite-shield"}
                           else {"defence_ids": (mechanic_id,)})
            elif family == "materials":
                options = {"main_material_id": mechanic_id}
            elif family == "preparations":
                options = {"preparation_ids": (mechanic_id,)}
            elif family == "poisons":
                options = {"main_poison_id": mechanic_id}
            else:
                options = {"skill_ids": (mechanic_id,)}
            fighter = compile_fighter(FighterBuild("mordheim", characteristics, **options))
            dice = KeyedDice(10_000 + executed)
            state = initialize_duel(fighter, opponent, dice)
            assert resolve_round(fighter, opponent, state, dice).state.round_index == 1
            executed += 1
    assert executed == 190

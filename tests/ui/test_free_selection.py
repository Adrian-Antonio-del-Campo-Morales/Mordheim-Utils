"""external.test_free_selection: responsibility extracted without altering the rules."""
from __future__ import annotations

from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import FighterBuild


def test_free_selection_build_compiles_with_runtime_equipment():
    catalogue = CombatCatalogue()
    sword = next(item_id for item_id, name in catalogue.weapons(None) if name == "Sword")
    shield = next(item_id for item_id, name in catalogue.off_hand_options(None) if name == "Shield")

    fighter = compile_fighter(
        FighterBuild(
            "mordheim",
            Characteristics(4, 3, 3, 1, 4, 1),
            main_weapon_id=sword,
            off_hand_id=shield,
        )
    )

    assert fighter.fighter_id == "custom:custom"


def test_free_selection_build_compiles_with_an_implemented_warband_skill():
    fighter = compile_fighter(FighterBuild(
        "mordheim",
        Characteristics(4, 3, 3, 1, 4, 1),
        special_rule_ids=("band--pit-fighter-skill-arms-master",),
    ))

    assert fighter.fighter_id == "custom:custom"

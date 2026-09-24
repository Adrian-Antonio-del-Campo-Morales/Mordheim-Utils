"""The summoned creature keeps its wounds before disappearing."""
from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat.phases import Condition
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics, FighterBuild
from mordheim_combat_lab.verification.dice import StrictDice


def test_bat_survives_first_wound_then_disappears_without_injury_roll():
    attacker = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1), main_weapon_id="weapon.mace",
    ))
    bat = compile_fighter(FighterBuild(
        "mordheim", collection="trollheim", band_id="chaos-streets-undead-bloodlines",
        profile_id="vampire-bat",
    ))
    initialization = StrictDice([])
    attacker_state = initialize_fighter(attacker, initialization, "a")
    bat_state = initialize_fighter(bat, initialization, "d")
    initialization.finish()
    for remaining, condition in ((1, Condition.STANDING), (0, Condition.OUT)):
        dice = StrictDice([
            {"key": "test.hit", "value": 5},
            {"key": "test.wound", "value": 5},
        ])
        outcome = resolve_reference_attack(
            attacker, bat, attacker_state, bat_state, attacker.main_weapon, dice, key="test",
        )
        dice.finish()
        assert outcome.defender.wounds == remaining
        assert outcome.defender.condition == condition
        attacker_state, bat_state = outcome.attacker, outcome.defender

"""Engine contracts separated from the corresponding rule witnesses."""


from __future__ import annotations


from dataclasses import replace


import pytest


from mordheim_combat import phases


from mordheim_combat.modular.attacks import resolve_reference_attack


from mordheim_combat.modular.contexts import prepare_armour_context, prepare_special_save_context


from mordheim_combat.modular.state import initialize_fighter


from tests.engines.shared.dice import StrictDecisions, StrictDice


from tests.engines.modular.replay import replay_duel


import sys


from mordheim_core.models import Characteristics, DuelContext, EffectSet, FighterBuild


compile_fighter = None


@pytest.fixture(autouse=True)
def _frozen_compiles(compiled_builds, monkeypatch):
    """Inject the common loader callable; ``compiled_builds`` is wired by conftest."""
    monkeypatch.setattr(
        sys.modules[__name__], "compile_fighter", compiled_builds.fighter)


BOGLAR = ("underworld-alliance-mim", "boglars")


WARPSTONE_TROLL = ("underworld-alliance-mim", "warpstone-troll")




def profile(pair, **options):
    band_id, profile_id = pair
    return compile_fighter(FighterBuild(
        "mordheim", band_id=band_id, profile_id=profile_id, **options
    ))


def fighter(strength: int = 3, attacks: int = 1, **options):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, strength, 3, 3, 3, attacks, leadership=7), **options
    ))


def mace(strength: int = 3):
    return fighter(strength, main_weapon_id="weapon.mace")


def state(unit):
    dice = StrictDice([])
    result = initialize_fighter(unit, dice, "init")
    dice.finish()
    return result


def roll(key, value, sides=6):
    return {"key": key, "value": value, "sides": sides}


def attack(attacker, defender, rolls, **options):
    dice, choices = StrictDice(rolls), StrictDecisions([])
    result = resolve_reference_attack(
        attacker, defender, state(attacker), state(defender),
        attacker.main_weapon, dice, key="a", decisions=choices, **options
    )
    dice.finish()
    choices.finish()
    return result


def test_control_compilations_do_not_change_between_boglar_attacks():
    troll_before = profile(WARPSTONE_TROLL)
    attack(mace(), profile(BOGLAR), [roll("a.hit", 6), roll("a.wound", 4), roll("a.special.regeneration", 4), roll("a.injury.0", 1)])
    troll_after = profile(WARPSTONE_TROLL)
    assert troll_before == troll_after
    assert troll_after.global_effects.regeneration_save == 4
    assert profile(BOGLAR).global_effects.regeneration_save == 5

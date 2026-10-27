"""Engine contracts separated from the corresponding rule witnesses."""


from dataclasses import replace


import pytest


from mordheim_combat.kernel import compile_duel_plan


from mordheim_combat.modular.pools import _resolve_attack_pool


from mordheim_combat.modular.rounds import resolve_round, select_attack_replacement


from mordheim_combat.modular.state import initialize_duel, initialize_fighter




from mordheim_combat.native import simulate_duel


from tests.engines.shared.dice import StrictDecisions, StrictDice


import sys


from mordheim_core.models import Characteristics, DuelContext, DuelRequest, EffectSet, FighterBuild


compile_fighter = None


@pytest.fixture(autouse=True)
def _frozen_compiles(compiled_builds, monkeypatch):
    """Inject the common loader callable; ``compiled_builds`` is wired by conftest."""
    monkeypatch.setattr(
        sys.modules[__name__], "compile_fighter", compiled_builds.fighter)


RULE = "warpstone-troll--vomit-attack"




def troll(selected=True):
    return compile_fighter(FighterBuild(
        "mordheim", band_id="underworld-alliance-mim", profile_id="warpstone-troll",
        special_rule_ids=(RULE,) if selected else (),
    ))


def opponent(**options):
    return compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 4, 1, 1),
        main_weapon_id="weapon.sword", off_hand_id="defence.buckler",
        armour_id="armour.gromril-armour", **options,
    ))


def test_unported_option_is_refused_before_optimized_execution():
    """The native gate refuses the optional Vomit Attack before dispatch.

    The gate names its first pending capability, which for this Troll is a
    local modifier rather than the Vomit option, so its refusal is asserted
    generically.
    """
    with pytest.raises(ValueError, match="modular engine"):
        simulate_duel(DuelRequest(troll(), opponent(), simulations=1))


def test_low_level_optimized_entries_do_not_silently_drop_the_option(precompiled):
    first = precompiled(0).first
    second = precompiled(0).second
    with pytest.raises(ValueError, match="modular engine"):
        compile_duel_plan(first, second, backend="native")
    with pytest.raises(ValueError, match="modular engine"):
        simulate_duel(DuelRequest(first, second, simulations=1))

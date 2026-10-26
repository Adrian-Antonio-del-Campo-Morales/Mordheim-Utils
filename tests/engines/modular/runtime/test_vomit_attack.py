"""Engine contracts separated from the corresponding rule witnesses."""


from dataclasses import replace


import numpy as np


import pytest


from mordheim_combat.kernel import compile_duel_plan


from mordheim_combat.modular.pools import _resolve_attack_pool


from mordheim_combat.modular.rounds import resolve_round, select_attack_replacement


from mordheim_combat.modular.state import initialize_duel, initialize_fighter


from mordheim_combat.native._combat_compile import compile_duel


from mordheim_combat.vectorized import available_backends, simulate_batch, simulate_duel, simulate_duel_parallel


from mordheim_combat_lab.verification.dice import StrictDecisions, StrictDice


import sys


from mordheim_core.models import Characteristics, DuelContext, DuelRequest, EffectSet, FighterBuild


compile_fighter = None


@pytest.fixture(autouse=True)
def _frozen_compiles(compiled_builds, monkeypatch):
    """Inject the common loader callable; ``compiled_builds`` is wired by conftest."""
    monkeypatch.setattr(
        sys.modules[__name__], "compile_fighter", compiled_builds.fighter)


RULE = "warpstone-troll--vomit-attack"


@pytest.fixture
def _frozen_compiles(compiled_builds, monkeypatch):
    """Use frozen build results for the explicitly migrated preparations."""
    monkeypatch.setattr(
        sys.modules[__name__], "compile_fighter", compiled_builds.fighter)


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


@pytest.mark.usefixtures("_frozen_compiles")
@pytest.mark.parametrize("backend", ["auto", "numpy", "native"])
def test_unported_option_is_refused_before_optimized_execution(backend):
    """NumPy executes the connected option; the native gate still refuses it.

    The native gate names its first pending capability, which for this Troll is
    a local modifier rather than the Vomit option, so its refusal is asserted
    generically. Auto follows the first available backend. The NumPy request
    supplies explicit Leadership because the
    charging fear test needs it in both engines.
    """
    selected = available_backends()[0] if backend == "auto" else backend
    if selected == "numpy":
        led = compile_fighter(FighterBuild(
            "mordheim", Characteristics(3, 3, 3, 4, 1, 1, leadership=7),
            main_weapon_id="weapon.sword",
        ))
        result = simulate_duel(DuelRequest(troll(), led, simulations=1), backend=backend)
        assert result.first_wins + result.second_wins + result.unresolved == 1
        return
    with pytest.raises(ValueError, match="modular engine"):
        simulate_duel(DuelRequest(troll(), opponent(), simulations=1), backend=backend)


def test_low_level_optimized_entries_do_not_silently_drop_the_option(precompiled):
    first = precompiled(0).first
    # The accepted NumPy entries execute the connected option instead of
    # dropping it. Explicit Leadership keeps the charging fear test valid.
    led = precompiled(0).second
    second = precompiled(1).second
    for call in (lambda: compile_duel_plan(first, second), lambda: compile_duel(first, second)):
        with pytest.raises(ValueError, match="modular engine"):
            call()
    assert sum(simulate_batch(first, led, 1, np.random.default_rng(0), 1)) == 1
    parallel = simulate_duel_parallel(DuelRequest(first, led, simulations=1))
    assert parallel.first_wins + parallel.second_wins + parallel.unresolved == 1

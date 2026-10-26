"""The observed oracle leg must reproduce the counting oracle exactly."""
import sys
from mordheim_combat.modular.duel import simulate_duel_observed
from mordheim_combat.modular.duel import simulate_duel_reference
from tests.engines.fixtures.precompiled_catalog import benchmark_scenarios
import numpy as np
import pytest


# The frozen-build loader is the only compilation route in this module: the
# fixture below replaces this name with ``load_builds(...).fighter``, so every
# builder keeps its complete FighterBuild and the local ``replace`` calls stay
# untouched, while nothing compiles here.
compile_fighter = None


@pytest.fixture(autouse=True)
def _frozen_compiles(compiled_builds, monkeypatch):
    """Inject the common loader callable; ``compiled_builds`` is wired by conftest."""
    monkeypatch.setattr(
        sys.modules[__name__], "compile_fighter", compiled_builds.fighter)




def _pair(scenario_id: str = "basic"):
    scenario = next(
        item for item in benchmark_scenarios() if item.id == scenario_id
    )
    return compile_fighter(scenario.first), compile_fighter(scenario.second), scenario


def test_observed_totals_reproduce_the_reference_sample():
    first, second, scenario = _pair()
    simulations, seed = 400, 2026
    observed = simulate_duel_observed(
        first, second, simulations, seed=seed,
        maximum_rounds=scenario.maximum_rounds,
    )
    reference = simulate_duel_reference(
        first, second, simulations, seed=seed,
        maximum_rounds=scenario.maximum_rounds,
    )
    assert (observed.first_wins, observed.second_wins, observed.unresolved) == (
        reference.first_wins, reference.second_wins, reference.unresolved,
    )
    assert observed.as_result() == reference


def test_observed_arrays_are_replayable_and_in_range():
    first, second, scenario = _pair("stateful")
    simulations = 300
    left = simulate_duel_observed(
        first, second, simulations, seed=7,
        maximum_rounds=scenario.maximum_rounds,
    )
    right = simulate_duel_observed(
        first, second, simulations, seed=7,
        maximum_rounds=scenario.maximum_rounds,
    )
    assert np.array_equal(left.winner, right.winner)
    assert np.array_equal(left.resolution_rounds, right.resolution_rounds)
    rounds = left.resolution_rounds
    assert int(rounds.min()) >= 1
    assert int(rounds.max()) <= scenario.maximum_rounds
    for value in ("first_wounds", "second_wounds", "first_condition", "second_condition"):
        assert getattr(left, value).shape == (simulations,)


def test_unresolved_duels_report_the_full_round_budget():
    # The 75-round long scenario is the most likely to leave duels open; the
    # invariant is structural: a duel that never resolved ran out of its round
    # budget (both fighters still active), so it must have executed every
    # round.  A simultaneous mutual KO also counts as unresolved but ends
    # mid-budget with both conditions OUT.
    first, second, scenario = _pair("long")
    observed = simulate_duel_observed(
        first, second, 200, seed=11, maximum_rounds=scenario.maximum_rounds,
    )
    unresolved = observed.winner == 2
    if not unresolved.any():
        return
    out_of_budget = (observed.first_condition == 4) | (observed.second_condition == 4)
    assert int(observed.resolution_rounds[unresolved & ~out_of_budget].min()) \
        == scenario.maximum_rounds


def test_observed_validates_its_bounds():
    first, second, scenario = _pair()
    import pytest
    with pytest.raises(ValueError):
        simulate_duel_observed(first, second, 0, maximum_rounds=scenario.maximum_rounds)

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from mordheim_combat.vectorized import simulate_batch_observed
from mordheim_core.models import DuelContext
from mordheim_core.models import MutationOption


def fighter(vector_case, test):
    """Return the frozen fighter primed by ``test``'s own case."""
    return vector_case(f"test_observations/{test}-0-0").first


@pytest.mark.phase5_vectorized
def test_observed_batch_preserves_per_row_terminal_state(vector_case):
    case = vector_case("test_observations/test_observed_batch_preserves_per_row_terminal_state-0-0")
    result = simulate_batch_observed(
        case.first, case.second, 64, np.random.default_rng(9), maximum_rounds=10,
    )

    assert result.winner.shape == result.rounds.shape == (64,)
    assert result.first_wounds.shape == result.second_wounds.shape == (64,)
    assert result.first_condition.shape == result.second_condition.shape == (64,)
    assert set(np.unique(result.winner)) <= {-1, 0, 1}
    assert np.all((result.rounds >= 1) & (result.rounds <= 10))
    assert {name for name, _values in result.first_resources} == {
        "lucky-charm", "force-of-will", "mark-of-the-old-ones", "luck",
    }


def _tagged(fighter, *tags):
    return replace(
        fighter,
        global_effects=replace(
            fighter.global_effects,
            tags=tuple(dict.fromkeys((*fighter.global_effects.tags, *tags))),
        ),
    )


@pytest.mark.phase5_vectorized
def test_initialised_rows_keep_independent_state_and_lazy_characteristics(vector_case):
    from mordheim_combat.vectorized._state import initialize_fighter
    from mordheim_combat.vectorized._state import refresh_random_characteristics
    from mordheim_combat.vectorized._state import require_characteristics

    variable = replace(
        _tagged(
            fighter(vector_case, "test_initialised_rows_keep_independent_state_and_lazy_characteristics"),
            "mechanic.inconsistency",
        ),
        random_characteristics=(("WS", 1, 6, 0), ("A", 1, 3, 0)),
    )
    state = initialize_fighter(
        variable, 3, np.random.default_rng(4), lazy_inconsistency=True,
    )

    # A variable profile keeps its printed values; nothing is rolled at start.
    assert state.random_rolled.tolist() == [0, 0, 0]
    assert state.weapon_skill.tolist() == [3, 3, 3]
    assert state.attacks.tolist() == [1, 1, 1]

    # Every column belongs to its own row: writing one never reaches another.
    state.wounds[0] = 0
    state.attacks[0] = 9
    state.random_rolled[0] = 1
    assert state.wounds.tolist() == [0, 1, 1]
    assert state.attacks.tolist() == [9, 1, 1]
    assert state.starting_wounds.tolist() == [1, 1, 1]

    # Only the requested characteristic of the requested rows is drawn, and a
    # second request in the same round reuses the value.
    rows = np.array([1, 2])
    require_characteristics(variable, state, rows, np.random.default_rng(5), {"A"})
    assert state.random_rolled.tolist() == [1, 16, 16]
    rolled = state.attacks[rows].copy()
    require_characteristics(variable, state, rows, np.random.default_rng(6), {"A"})
    assert state.random_rolled.tolist() == [1, 16, 16]
    assert state.attacks[rows].tolist() == rolled.tolist()

    # The next round clears the mask for its own rows only.
    refresh_random_characteristics(variable, state, np.array([2]), np.random.default_rng(7))
    assert state.random_rolled.tolist() == [1, 16, 0]
    require_characteristics(
        variable, state, np.array([2]), np.random.default_rng(8), {"WS", "A"},
    )
    assert state.random_rolled.tolist() == [1, 16, 17]


@pytest.mark.phase5_vectorized
def test_brand_projection_stays_on_its_own_simulation_row(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized._mutations import apply_brand_row
    from mordheim_combat.vectorized._mutations import fighter_for_row

    printed = fighter(vector_case, "test_brand_projection_stays_on_its_own_simulation_row")
    state = _new_state(printed, 2, np.random.default_rng(1))
    brand = MutationOption(roll=63, stat_ops=(("toughness", "add", 1),))
    projected = apply_brand_row(printed, state, 1, brand, np.random.default_rng(2))

    # Only the branded row changes, and its projection is cached for the
    # attack layers; the unbranded row keeps the printed fighter.
    assert state.toughness.tolist() == [3, 4]
    assert state.mutations[0] == ()
    assert len(state.mutations[1]) == 1
    assert projected.characteristics.toughness == 4
    assert state.effective_fighter[1] is projected
    assert fighter_for_row(printed, state, 0) is printed


@pytest.mark.phase5_vectorized
def test_supplied_duel_start_facts_follow_the_modular_charge_contract(vector_case):
    from mordheim_combat.vectorized._state import validate_duel_start

    case = vector_case("test_observations/test_supplied_duel_start_facts_follow_the_modular_charge_contract-0-0")
    strict = _tagged(case.first, "mechanic.shallya-strictures")
    charging = DuelContext(charging=("first",), active_participant="first")
    with pytest.raises(ValueError, match="Shallyan Strictures"):
        validate_duel_start(strict, case.second, charging)
    assert validate_duel_start(
        strict, _tagged(case.second, "band.carnival-of-chaos"), charging,
    ) == (True, False)

    nuttaz = _tagged(case.first, "condition.nuttaz-charge")
    with pytest.raises(ValueError, match="compulsory charge"):
        validate_duel_start(
            nuttaz, case.second,
            DuelContext(charging=(), active_participant="first"),
        )

    witch_finder = _tagged(
        case.first, "condition.witch-finder-charge", "mechanic.solkan-witch-finder",
    )
    with pytest.raises(ValueError, match="Witch-finder"):
        validate_duel_start(witch_finder, case.second, charging)

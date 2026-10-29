"""Vectorized rule contracts for supplied duel-start facts."""
from __future__ import annotations

from dataclasses import replace

import pytest

from mordheim_core.models import DuelContext

def _tagged(fighter, *tags):
    return replace(
        fighter,
        global_effects=replace(
            fighter.global_effects,
            tags=tuple(dict.fromkeys((*fighter.global_effects.tags, *tags))),
        ),
    )

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

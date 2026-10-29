"""Contracts: canonical facts, local identity and real charge consumers."""
from dataclasses import replace
import pickle
import pytest
from mordheim_core.models import Characteristics, DuelContext, DuelRequest, FighterBuild, LocalParticipant
from mordheim_core.context import prepare_duel_context
from mordheim_core.dice import ScriptedDice
from mordheim_combat.kernel import compile_duel_plan
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat.modular.rounds import resolve_round


@pytest.fixture
def precompiled(shared_precompiled):
    """Resolve this module's historical ``unit/shared`` case."""
    return shared_precompiled


@pytest.mark.parametrize("charging,counts", [((), (1, 1)), (("first",), (2, 1)),
    (("second",), (1, 2)), (("first", "second"), (2, 2))])
def test_real_round_consumes_charge_facts_and_independent_clock(charging, counts, precompiled):
    unit = precompiled().first
    context = DuelContext(charging=charging, active_participant="second")
    state = initialize_duel(unit, unit, ScriptedDice([]), context=context)
    assert state.initial_charge_flags == ("first" in charging, "second" in charging)
    assert not state.first_player_turn
    # All attacks miss; a priority tie may consume one extra draw.
    result = resolve_round(unit, unit, state, ScriptedDice([1] * 10))
    assert len(result.attacks) == sum(counts)
    assert result.state.first_player_turn
    assert result.state.context is state.context

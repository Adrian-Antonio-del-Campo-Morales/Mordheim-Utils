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


def test_real_parallel_cancellation_is_propagated(precompiled):
    from threading import Event
    from mordheim_combat.vectorized import simulate_duel_parallel
    from mordheim_core.models import SimulationCancelled
    unit = precompiled().first
    cancel = Event()
    cancel.set()
    request = DuelRequest(unit, unit, 2, batch_size=1, maximum_rounds=1, cancel_event=cancel)
    with pytest.raises(SimulationCancelled, match="parallel simulation cancelled"):
        simulate_duel_parallel(request, workers=1)

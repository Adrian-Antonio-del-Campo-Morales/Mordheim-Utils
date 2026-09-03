"""external.test_execution: responsibility extracted without altering the rules."""
from __future__ import annotations

from mordheim_combat_lab.application.settings import DuelExecutionSettings
from mordheim_combat.vectorized import simulate_duel
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import FighterBuild
from mordheim_core.models import SimulationCancelled
import pytest as pytest
from threading import Event


def test_execution_settings_build_a_runtime_request():
    fighter = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1)))
    cancel_event = Event()
    settings = DuelExecutionSettings(1_000, 42, 100, 25)

    request = settings.request(fighter, fighter, cancel_event)

    assert (request.simulations, request.seed, request.batch_size, request.maximum_rounds) == (1_000, 42, 100, 25)
    assert request.cancel_event is cancel_event


def test_execution_settings_reject_non_positive_runtime_limits():
    with pytest.raises(ValueError):
        DuelExecutionSettings(0, 0, 100, 25)


def test_execution_settings_passes_cancellation_to_the_runtime():
    fighter = compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1)))
    cancel_event = Event()
    cancel_event.set()

    with pytest.raises(SimulationCancelled):
        simulate_duel(DuelExecutionSettings(1_000, 0, 100, 25).request(fighter, fighter, cancel_event))

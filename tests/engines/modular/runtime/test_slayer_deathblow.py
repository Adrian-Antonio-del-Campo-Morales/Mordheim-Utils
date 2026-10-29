"""Engine contracts separated from the corresponding rule witnesses."""


import sys


from dataclasses import replace


import pytest


from mordheim_combat import phases


from mordheim_combat.kernel import require_optimized_support


from mordheim_combat.modular.contexts import _injury_context


from mordheim_combat.modular.rounds import resolve_round


from mordheim_combat.modular.state import initialize_duel


from tests.engines.shared.dice import StrictDecisions, StrictDice


from mordheim_core.models import DuelContext, EffectSet, FighterBuild




compile_fighter = None


@pytest.fixture(autouse=True)
def _frozen_compiles(compiled_builds, monkeypatch):
    """Inject the common loader callable; ``compiled_builds`` is wired by conftest."""
    monkeypatch.setattr(
        sys.modules[__name__], "compile_fighter", compiled_builds.fighter)


def test_deathblow_declares_itself_a_modular_only_operator(precompiled):
    slayer, killer = precompiled().first, precompiled().second
    with pytest.raises(ValueError, match="modular"):
        require_optimized_support(slayer, killer)

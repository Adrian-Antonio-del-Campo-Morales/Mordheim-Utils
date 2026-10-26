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


def test_kernel_and_native_lowering_keep_named_optional_stats(precompiled):
    from mordheim_combat.native._combat_compile import compile_duel
    compiled = precompiled()
    known = compiled.first
    unit = compiled.second
    plan = compile_duel_plan(known, unit)
    assert (plan.first.movement, plan.first.leadership) == (5, 9)
    assert plan.second.movement is plan.second.leadership is None
    lowered = compile_duel(known, unit)
    assert (lowered["first"]["movement"], lowered["first"]["leadership"]) == (5, 9)
    assert lowered["second"]["movement"] is lowered["second"]["leadership"] is None
    prepared = prepare_duel_context(known, unit, DuelContext())
    assert prepared.characteristic("first", "leadership") == 9


def test_native_unavailable_is_an_explicit_error(monkeypatch, precompiled):
    import builtins
    from mordheim_combat.vectorized import simulate_duel
    unit = precompiled().first
    original = builtins.__import__
    def unavailable(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "mordheim_combat" and "_combat_native" in fromlist:
            raise ImportError("isolated unavailable extension")
        return original(name, globals, locals, fromlist, level)
    monkeypatch.setattr(builtins, "__import__", unavailable)
    with pytest.raises(RuntimeError, match="not available"):
        simulate_duel(DuelRequest(unit, unit, 1), backend="native")

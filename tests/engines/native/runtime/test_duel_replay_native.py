"""Native replay-driver contracts: callbacks, cleanup and context version.

The compiled extension consumes binary/integer callbacks and owns global
callback state. These cases exercise that driver directly; they do not compare
modular and native outcomes.
"""
import pytest
from mordheim_combat.native import available_backends
from mordheim_core.models import DuelContext
from tests.engines.native.replay import replay_duel

SYMMETRIC = (
    "unit/parity/test_duel_replay/"
    "test_native_callback_rejects_invalid_binary_draw-0-0"
)
NATIVE_EXCEPTION = (
    "unit/parity/test_duel_replay/"
    "test_native_exception_cleanup_and_reentry_are_strict-0-0"
)
NATIVE_CALLBACK = (
    "unit/parity/test_duel_replay/"
    "test_native_callback_rejects_invalid_integer_and_cleans_up-0-0"
)
ROUND_COUNTER = (
    "unit/parity/test_duel_replay/"
    "test_native_observation_round_counter_does_not_wrap-0-0"
)


def load(cases, key):
    """The frozen pair and its resolved context; never compiles anything."""
    case = cases[key]
    return case.first, case.second, case.context


def tape(values):
    return [{"key": f"draw.{i}.{kind}", "sides": sides, "value": value}
            for i, (kind, sides, value) in enumerate(values)]


def _native_extension():
    """Return the compiled module, failing with the rebuild instructions."""
    if "native" not in available_backends():
        pytest.fail(
            "native combat extension is not available or was built for stale "
            "layouts; install it with `python -m pip install -e \".[dev]\"` "
            "(a working C compiler is required) and reinstall after an update"
        )
    from mordheim_combat import _combat_native
    return _combat_native


def execute(first, second, optimized, **kwargs):
    return replay_duel(first, second, rolls=tape(optimized), **kwargs)


def test_native_exception_cleanup_and_reentry_are_strict(cases):
    native = _native_extension()
    from mordheim_core.models import DuelRequest
    from mordheim_combat.kernel import compile_duel_plan
    first, second, context = load(cases, NATIVE_EXCEPTION)
    request = DuelRequest(first, second, 1, maximum_rounds=1)
    class Nested:
        def integers(self, *args):
            native.simulate_duel(request, compile_duel_plan(first, second))
    with pytest.raises(RuntimeError, match="nested native"):
        native.simulate_batch_observed(first, second, 1, Nested(), 1, context=context)
    # A failure never leaves the global callback or batch ownership behind.
    result = execute(first, second, [("integer", 6, 1)] * 2, context=context)
    assert result.winner == 2
    native.simulate_duel(request, compile_duel_plan(first, second))


def test_explicit_native_context_and_replay_never_fall_back(cases, monkeypatch):
    native = _native_extension()
    from mordheim_combat.native import simulate_duel
    from mordheim_core.models import DuelRequest
    unit = load(cases, SYMMETRIC)[0]
    context = DuelContext(charging=(), active_participant="first")
    request = DuelRequest(unit, unit, 1, context=context)
    monkeypatch.setattr(native, "supports_plan", lambda plan: False)
    with pytest.raises(RuntimeError, match="does not support"):
        simulate_duel(request)
    with pytest.raises(RuntimeError, match="does not support"):
        replay_duel(unit, unit, rolls=[], context=context)
    monkeypatch.setattr(native, "CONTEXT_VERSION", 0)
    with pytest.raises(RuntimeError, match="stale"):
        simulate_duel(request)


@pytest.mark.parametrize("value", [0, 7, 1.5, True])
def test_native_callback_rejects_invalid_integer_and_cleans_up(cases, value):
    import numpy as np
    native = _native_extension()
    first, second, context = load(cases, NATIVE_CALLBACK)
    class Bad:
        def integers(self, *args):return np.array([value])
    with pytest.raises((ValueError, TypeError)):
        native.simulate_batch_observed(first, second, 1, Bad(), 1, context=context)
    assert execute(first, second, [("integer", 6, 1)] * 2, context=context).winner == 2


@pytest.mark.parametrize("value", [-0.1, 1, float("nan"), True])
def test_native_callback_rejects_invalid_binary_draw(cases, value):
    import numpy as np
    native = _native_extension()
    first, second, _ = load(cases, SYMMETRIC)
    class Bad:
        def random(self, *args):return np.array([value])
    with pytest.raises(ValueError):
        native.simulate_batch_observed(first, second, 1, Bad(), 1)


def test_native_observation_round_counter_does_not_wrap(cases):
    import numpy as np
    native = _native_extension()
    first, second, _ = load(cases, ROUND_COUNTER)
    class Misses:
        def integers(self, low, high, size=None):return np.ones(size, dtype=np.int8)
    result = native.simulate_batch_observed(first, second, 1, Misses(), 32768,
        context=DuelContext(charging=(), active_participant="first"))
    assert int(result.rounds[0]) == 32768
    assert result.rounds.dtype == np.int64

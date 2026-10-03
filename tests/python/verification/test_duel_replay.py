"""Small independently authored, real-driver T13.1 replay proofs."""
from dataclasses import replace
import pytest
from mordheim_combat_lab.verification.parity._replay import ReplayRng, replay_duel
from mordheim_combat_lab.verification.reports import EvidenceMismatch
from mordheim_core.models import Characteristics, DuelContext, FighterBuild
from mordheim_construction.compiler import compile_fighter

BACKENDS = ("modular", "numpy", "native")


def fighter(initiative=3, **build):
    return compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 1, initiative, 1), main_weapon_id="weapon.mace", **build))


def tape(values):
    return [{"key": f"draw.{i}.{kind}", "sides": sides, "value": value}
            for i, (kind, sides, value) in enumerate(values)]


def execute(first, second, backend, scalar, optimized, **kwargs):
    if backend == "native":
        from mordheim_combat.vectorized import available_backends
        if "native" not in available_backends():
            pytest.skip("native extension unavailable")
    return replay_duel(first, second, backend=backend,
        rolls=scalar if backend == "modular" else tape(optimized), **kwargs)


def roll(key, value, sides=6):
    return {"key": key, "sides": sides, "value": value}


@pytest.mark.parametrize("backend", BACKENDS)
def test_real_attack_wound_injury_and_terminal_state(backend):
    first, second = fighter(), fighter(initiative=2)
    result = execute(first, second, backend,
        [roll("round.0.first.attack.0.hit", 4), roll("round.0.first.attack.0.wound", 4),
         roll("round.0.first.attack.0.injury.0", 5)],
        [("integer", 6, v) for v in (4, 4, 5)],
        context=DuelContext(charging=("first",), active_participant="second"))
    assert result.terminal == (0, 1, (1, 0), (0, 4), (frozenset(), frozenset()))
    assert len(result.rolls) == 3 and result.decisions == ()


@pytest.mark.parametrize("backend", BACKENDS)
def test_absence_misses_and_priority_tie(backend):
    unit = fighter()
    result = execute(unit, unit, backend,
        [roll("round.0.priority-tie", 6), roll("round.0.first.attack.0.hit", 1), roll("round.0.second.attack.0.hit", 1)],
        [("binary", 2, 1), ("integer", 6, 1), ("integer", 6, 1)],
        context=DuelContext(charging=(), active_participant="second"))
    assert result.terminal == (2, 1, (1, 1), (0, 0), (frozenset(), frozenset()))


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("first_charges", [True, False])
def test_injected_charge_and_d3_initialization_preserve_backend_order(backend, first_charges):
    first = fighter(preparation_ids=("preparation.crimson-shade",))
    second = fighter(initiative=2)
    order = ("first", "second") if first_charges else ("second", "first")
    scalar = [roll("duel.charge", 6 if first_charges else 1), roll("first.crimson-shade", 2, 3)]
    scalar += [roll(f"round.0.{side}.attack.0.hit", 1) for side in order]
    optimized = [("integer", 3, 2), ("binary", 2, 1 if first_charges else 2), ("integer", 6, 1), ("integer", 6, 1)]
    result = execute(first, second, backend, scalar, optimized)
    assert result.terminal == (2, 1, (1, 1), (0, 0), (frozenset(), frozenset()))
    assert len(result.rolls) == 4


@pytest.mark.parametrize("backend", BACKENDS)
def test_lucky_charm_consumption_and_continuation(backend):
    first, second = fighter(), fighter(initiative=2, defence_ids=("defence.lucky-charm",))
    result = execute(first, second, backend,
        [roll("round.0.first.attack.0.hit", 4), roll("round.0.first.attack.0.lucky-charm", 6), roll("round.0.second.attack.0.hit", 1)],
        [("integer", 6, v) for v in (4, 6, 1)],
        context=DuelContext(charging=("first",), active_participant="first"))
    assert result.terminal == (2, 1, (1, 1), (0, 0), (frozenset(), frozenset({"lucky-charm"})))


@pytest.mark.parametrize("backend", BACKENDS)
def test_missing_or_extra_draws_fail(backend):
    first, second = fighter(), fighter(initiative=2)
    context = DuelContext(charging=("first",), active_participant="first")
    with pytest.raises(EvidenceMismatch, match="unexpected roll"):
        execute(first, second, backend, [], [], context=context)
    scalar = [roll("round.0.first.attack.0.hit", 1), roll("round.0.second.attack.0.hit", 1), roll("unused", 1)]
    with pytest.raises(EvidenceMismatch, match="unused rolls"):
        execute(first, second, backend, scalar, [("integer", 6, 1)] * 3, context=context)


def test_replay_validates_sides_values_binary_draws_and_cleanup():
    rng = ReplayRng(tape([("integer", 3, 3), ("binary", 2, 2)]))
    assert rng.integers(1, 4, 1).tolist() == [3]
    assert rng.random(1).tolist() == [0.75]
    rng.finish()
    with pytest.raises(EvidenceMismatch):
        ReplayRng(tape([("integer", 3, 2)])).integers(1, 7, 1)
    with pytest.raises(ValueError):
        ReplayRng(tape([("integer", 3, 4)])).integers(1, 4, 1)


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("accept", [False, True])
def test_supported_bull_charge_decision_is_consumed_once(backend, accept):
    first, second = fighter(), fighter(initiative=2)
    first = replace(first, global_effects=replace(first.global_effects, tags=("mechanic.bull-charge",)))
    action = "bull-charge" if accept else "attack.0"
    result = execute(first, second, backend,
        [roll(f"round.0.first.{action}.hit", 1), roll("round.0.second.attack.0.hit", 1)],
        [("integer", 6, 1), ("integer", 6, 1)],
        choices=[{"key": "round.0.first.bull-charge" if backend == "modular" else "bull-charge", "value": accept}],
        context=DuelContext(charging=("first",), active_participant="second"))
    assert result.terminal == (2, 1, (1, 1), (0, 0), (frozenset(), frozenset()))
    assert result.decisions == (("round.0.first.bull-charge" if backend == "modular" else "bull-charge"),)


@pytest.mark.parametrize("backend", BACKENDS)
@pytest.mark.parametrize("active", ["first", "second"])
def test_real_turn_sensitive_operator_uses_clock_without_charge(backend, active):
    first, second = fighter(), fighter(initiative=2)
    first = replace(first, global_effects=replace(first.global_effects, tags=("skill.inspiring-sermon",)))
    first_count = 2 if active == "first" else 1
    scalar = [roll(f"round.0.first.attack.{i}.hit", 1) for i in range(first_count)]
    scalar += [roll("round.0.second.attack.0.hit", 1)]
    result = execute(first, second, backend, scalar,
        [("integer", 6, 1)] * (first_count + 1),
        context=DuelContext(charging=(), active_participant=active))
    assert result.terminal == (2, 1, (1, 1), (0, 0), (frozenset(), frozenset()))
    assert len(result.rolls) == first_count + 1


def test_decision_exhaustion_and_unused_choice_fail():
    first, second = fighter(), fighter(initiative=2)
    context = DuelContext(charging=("first",), active_participant="first")
    first = replace(first, global_effects=replace(first.global_effects, tags=("mechanic.bull-charge",)))
    for backend in BACKENDS:
        with pytest.raises(EvidenceMismatch, match="unexpected decision"):
            execute(first, second, backend, [], [], context=context)
        with pytest.raises(EvidenceMismatch, match="unused scripted decisions"):
            execute(fighter(), second, backend,
                [roll("round.0.first.attack.0.hit", 1), roll("round.0.second.attack.0.hit", 1)],
                [("integer", 6, 1)] * 2, context=context,
                choices=[{"key": "unused", "value": True}])


def test_native_exception_cleanup_and_reentry_are_strict():
    native = pytest.importorskip("mordheim_combat._combat_native")
    from mordheim_core.models import DuelRequest
    from mordheim_combat.kernel import compile_duel_plan
    first, second = fighter(), fighter(initiative=2)
    context = DuelContext(charging=("first",), active_participant="first")
    request = DuelRequest(first, second, 1, maximum_rounds=1)
    class Nested:
        def integers(self, *args):
            native.simulate_duel(request, compile_duel_plan(first, second))
    with pytest.raises(RuntimeError, match="nested native"):
        native.simulate_batch_observed(first, second, 1, Nested(), 1, context=context)
    # A failure never leaves the global callback or batch ownership behind.
    result = execute(first, second, "native",
        [], [("integer", 6, 1)] * 2, context=context)
    assert result.winner == 2
    native.simulate_duel(request, compile_duel_plan(first, second))


@pytest.mark.parametrize("backend", BACKENDS)
def test_disability_initialization_marker_is_not_a_spent_resource(backend):
    first, second = fighter(), fighter(initiative=2)
    first = replace(first, global_effects=replace(first.global_effects, tags=("mechanic.disability",)))
    scalar = [roll("first.disability", 3), roll("round.0.first.attack.0.hit", 1), roll("round.0.second.attack.0.hit", 1)]
    result = execute(first, second, backend, scalar, [("integer", 6, v) for v in (3, 1, 1)],
        context=DuelContext(charging=("first",), active_participant="first"))
    assert result.terminal == (2, 1, (1, 1), (0, 0), (frozenset(), frozenset()))


def test_explicit_native_context_and_replay_never_fall_back(monkeypatch):
    native = pytest.importorskip("mordheim_combat._combat_native")
    from mordheim_combat.vectorized import simulate_duel
    from mordheim_core.models import DuelRequest
    unit = fighter()
    context = DuelContext(charging=(), active_participant="first")
    request = DuelRequest(unit, unit, 1, context=context)
    monkeypatch.setattr(native, "supports_plan", lambda plan: False)
    with pytest.raises(RuntimeError, match="does not support"):
        simulate_duel(request, backend="native")
    with pytest.raises(RuntimeError, match="does not support"):
        replay_duel(unit, unit, backend="native", rolls=[], context=context)
    monkeypatch.setattr(native, "CONTEXT_VERSION", 0)
    with pytest.raises(RuntimeError, match="stale"):
        simulate_duel(request, backend="native")


@pytest.mark.parametrize("value", [0, 7, 1.5, True])
def test_native_callback_rejects_invalid_integer_and_cleans_up(value):
    import numpy as np
    native = pytest.importorskip("mordheim_combat._combat_native")
    first, second = fighter(), fighter(initiative=2)
    context = DuelContext(charging=("first",), active_participant="first")
    class Bad:
        def integers(self, *args):return np.array([value])
    with pytest.raises((ValueError, TypeError)):
        native.simulate_batch_observed(first, second, 1, Bad(), 1, context=context)
    assert execute(first, second, "native", [], [("integer", 6, 1)] * 2, context=context).winner == 2


@pytest.mark.parametrize("value", [-0.1, 1, float("nan"), True])
def test_native_callback_rejects_invalid_binary_draw(value):
    import numpy as np
    native = pytest.importorskip("mordheim_combat._combat_native")
    class Bad:
        def random(self, *args):return np.array([value])
    with pytest.raises(ValueError):
        native.simulate_batch_observed(fighter(), fighter(), 1, Bad(), 1)



def test_native_observation_round_counter_does_not_wrap():
    import numpy as np
    native = pytest.importorskip("mordheim_combat._combat_native")
    class Misses:
        def integers(self, low, high, size=None):return np.ones(size, dtype=np.int8)
    result = native.simulate_batch_observed(fighter(), fighter(initiative=2), 1, Misses(), 32768,
        context=DuelContext(charging=(), active_participant="first"))
    assert int(result.rounds[0]) == 32768
    assert result.rounds.dtype == np.int64

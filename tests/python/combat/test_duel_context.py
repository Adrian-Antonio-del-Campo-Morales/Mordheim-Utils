"""T13.1 contracts: canonical facts, local identity and real charge consumers."""
from dataclasses import replace
import pickle
import pytest
from mordheim_core.models import Characteristics, DuelContext, DuelRequest, FighterBuild, LocalParticipant
from mordheim_core.context import prepare_duel_context
from mordheim_core.dice import ScriptedDice
from mordheim_construction.compiler import compile_fighter
from mordheim_combat.kernel import compile_duel_plan
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat.modular.rounds import resolve_round


def fighter():
    return compile_fighter(FighterBuild("mordheim", Characteristics(3, 3, 3, 2, 3, 1)))


def test_six_positional_stats_remain_valid_and_unknown_is_explicit():
    stats = Characteristics(3, 3, 3, 1, 3, 1)
    assert stats.movement is stats.leadership is None
    with pytest.raises(TypeError):
        Characteristics(3, 3, 3, 1, 3, 1, 4, 7)
    prepared = prepare_duel_context(fighter(), fighter(), DuelContext())
    with pytest.raises(ValueError, match="requires explicit leadership"):
        prepared.characteristic("first", "leadership")
    with pytest.raises(ValueError, match="missing distance"):
        prepared.distance("first", "second")


@pytest.mark.parametrize("value", [-1, True, 1.5])
@pytest.mark.parametrize("name", ["movement", "leadership"])
def test_invalid_contextual_stat_is_rejected(name, value):
    with pytest.raises(ValueError):
        Characteristics(3, 3, 3, 1, 3, 1, **{name: value})


def test_canonical_stats_survive_player_advances_and_explicit_overrides():
    build = FighterBuild("mordheim", band_id="mercenaries", profile_id="mercenary-captain")
    canonical = compile_fighter(build)
    advanced = compile_fighter(replace(build, characteristics=Characteristics(5, 4, 4, 2, 4, 2)))
    assert (canonical.characteristics.movement, canonical.characteristics.leadership) == (4, 8)
    assert (advanced.characteristics.movement, advanced.characteristics.leadership) == (4, 8)
    custom = compile_fighter(replace(build, characteristics=replace(advanced.characteristics, movement=5, leadership=9)))
    assert (custom.characteristics.movement, custom.characteristics.leadership) == (5, 9)
    from mordheim_combat_lab.application.analyses import improve_attributes
    improved = improve_attributes(replace(build, characteristics=custom.characteristics), {"S": 1})
    assert (improved.characteristics.movement, improved.characteristics.leadership) == (5, 9)


def test_local_identity_does_not_replace_canonical_identity():
    unit = fighter()
    context = DuelContext(first_id="a", second_id="b", nearby=(LocalParticipant("helper", "first", unit),),
        distances=(("a", "helper", 2),), contacts=(("a", "b"),), terrain=(("a", "difficult"),))
    prepared = prepare_duel_context(unit, unit, context)
    assert [p.participant_id for p in prepared.participants] == ["a", "b", "helper"]
    assert prepared.participant("a").fighter.fighter_id == prepared.participant("b").fighter.fighter_id
    assert prepared.distance("helper", "a") == 2
    assert pickle.loads(pickle.dumps(context)) == context
    plan = compile_duel_plan(unit, unit, context=context)
    assert plan.context == prepared
    assert len(plan.first.characteristics) == 6
    with pytest.raises(ValueError, match="unique"):
        DuelContext(nearby=(LocalParticipant("first", "first", unit),))


@pytest.mark.parametrize("changes", [
    {"first_id": "second"}, {"distances": (("first", "unknown", 2),)},
    {"distances": (("first", "second", float("nan")),)},
    {"distances": (("first", "second", -1),)},
    {"distances": (("first", "second", True),)},
    {"distances": (("first", "second", 1), ("second", "first", 2))},
    {"distances": (("first", "second", 1),), "contacts": (("second", "first"),)},
    {"charging": ()}, {"active_participant": "unknown"},
    {"terrain": (("unknown", "difficult"),)},
])
def test_invalid_or_contradictory_facts_fail(changes):
    with pytest.raises(ValueError):
        DuelContext(**changes)


@pytest.mark.parametrize("charging,counts", [((), (1, 1)), (("first",), (2, 1)),
    (("second",), (1, 2)), (("first", "second"), (2, 2))])
def test_real_round_consumes_charge_facts_and_independent_clock(charging, counts):
    unit = fighter()
    unit = replace(unit, global_effects=replace(unit.global_effects, charge_attacks_bonus=1))
    context = DuelContext(charging=charging, active_participant="second")
    state = initialize_duel(unit, unit, ScriptedDice([]), context=context)
    assert state.initial_charge_flags == ("first" in charging, "second" in charging)
    assert not state.first_player_turn
    # All attacks miss; a priority tie may consume one extra draw.
    result = resolve_round(unit, unit, state, ScriptedDice([1] * 10))
    assert len(result.attacks) == sum(counts)
    assert result.state.first_player_turn
    assert result.state.context is state.context


def test_context_free_and_empty_context_retain_rng_order_and_results():
    unit = fighter()
    from mordheim_combat.modular.duel import simulate_duel_reference
    from mordheim_combat.vectorized import simulate_duel
    assert simulate_duel_reference(unit, unit, 30, seed=9) == simulate_duel_reference(unit, unit, 30, seed=9, context=DuelContext())
    request = DuelRequest(unit, unit, 100, seed=11, batch_size=31)
    assert simulate_duel(request, backend="numpy") == simulate_duel(replace(request, context=DuelContext()), backend="numpy")


@pytest.mark.parametrize("backend", ["numpy", "native"])
def test_real_pool_preserves_context(backend):
    from mordheim_combat.vectorized import available_backends, simulate_duel, simulate_duel_parallel
    from mordheim_combat_lab.application.settings import DuelExecutionSettings, simulate_battery
    if backend == "native" and "native" not in available_backends():
        pytest.skip("native extension unavailable")
    unit = fighter()
    unit = replace(unit, global_effects=replace(unit.global_effects, charge_attacks_bonus=1))
    context = DuelContext(charging=("second",), active_participant="first")
    request = DuelRequest(unit, unit, 80, seed=13, batch_size=21, maximum_rounds=3, context=context)
    sequential = simulate_duel(request, backend=backend)
    settings = DuelExecutionSettings(80, 13, 21, 3)
    assert settings.request(unit, unit, context=context).context == context
    assert simulate_battery(unit, unit, settings, workers=2, backend=backend, context=context) == sequential
    if backend == "numpy":
        assert simulate_duel_parallel(request, workers=2) == sequential
    from mordheim_combat.modular.duel import simulate_duel_reference
    from mordheim_combat.modular.parallel import simulate_duel_reference_parallel
    assert simulate_duel_reference_parallel(unit, unit, 20, seed=13, maximum_rounds=3, workers=2, context=context) == simulate_duel_reference(unit, unit, 20, seed=13, maximum_rounds=3, context=context)


def test_kernel_and_native_lowering_keep_named_optional_stats():
    from mordheim_combat.native._combat_compile import compile_duel
    unit = fighter()
    known = replace(unit, characteristics=replace(unit.characteristics, movement=5, leadership=9))
    plan = compile_duel_plan(known, unit)
    assert (plan.first.movement, plan.first.leadership) == (5, 9)
    assert plan.second.movement is plan.second.leadership is None
    lowered = compile_duel(known, unit)
    assert (lowered["first"]["movement"], lowered["first"]["leadership"]) == (5, 9)
    assert lowered["second"]["movement"] is lowered["second"]["leadership"] is None
    prepared = prepare_duel_context(known, unit, DuelContext())
    assert prepared.characteristic("first", "leadership") == 9



def test_native_unavailable_is_an_explicit_error(monkeypatch):
    import builtins
    from mordheim_combat.vectorized import simulate_duel
    unit = fighter()
    original = builtins.__import__
    def unavailable(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "mordheim_combat" and "_combat_native" in fromlist:
            raise ImportError("isolated unavailable extension")
        return original(name, globals, locals, fromlist, level)
    monkeypatch.setattr(builtins, "__import__", unavailable)
    with pytest.raises(RuntimeError, match="not available"):
        simulate_duel(DuelRequest(unit, unit, 1), backend="native")


def test_real_parallel_cancellation_is_propagated():
    from threading import Event
    from mordheim_combat.vectorized import simulate_duel_parallel
    from mordheim_core.models import SimulationCancelled
    unit = fighter()
    cancel = Event()
    cancel.set()
    request = DuelRequest(unit, unit, 2, batch_size=1, maximum_rounds=1, cancel_event=cancel)
    with pytest.raises(SimulationCancelled, match="parallel simulation cancelled"):
        simulate_duel_parallel(request, workers=1)

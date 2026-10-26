"""Contracts: canonical facts, local identity and real charge consumers."""
from dataclasses import replace
import pickle
import pytest
from mordheim_core.models import Characteristics, DuelContext, DuelRequest, LocalParticipant
from mordheim_core.context import prepare_duel_context
from mordheim_core.dice import ScriptedDice
from mordheim_combat.kernel import compile_duel_plan
from mordheim_combat.modular.state import initialize_duel
from mordheim_combat.modular.rounds import resolve_round


def test_six_positional_stats_remain_valid_and_unknown_is_explicit(precompiled):
    stats = Characteristics(3, 3, 3, 1, 3, 1)
    assert stats.movement is stats.leadership is None
    with pytest.raises(TypeError):
        Characteristics(3, 3, 3, 1, 3, 1, 4, 7)
    unit = precompiled().first
    prepared = prepare_duel_context(unit, unit, DuelContext())
    with pytest.raises(ValueError, match="requires explicit leadership"):
        prepared.characteristic("first", "leadership")
    with pytest.raises(ValueError, match="missing distance"):
        prepared.distance("first", "second")


@pytest.mark.parametrize("value", [-1, True, 1.5])
@pytest.mark.parametrize("name", ["movement", "leadership"])
def test_invalid_contextual_stat_is_rejected(name, value):
    with pytest.raises(ValueError):
        Characteristics(3, 3, 3, 1, 3, 1, **{name: value})


def test_canonical_stats_survive_player_advances_and_explicit_overrides(precompiled):
    compiled = precompiled()
    canonical = compiled.first
    advanced = compiled.second
    assert (canonical.characteristics.movement, canonical.characteristics.leadership) == (4, 8)
    assert (advanced.characteristics.movement, advanced.characteristics.leadership) == (4, 8)
    custom = replace(
        advanced,
        characteristics=replace(advanced.characteristics, movement=5, leadership=9),
    )
    assert (custom.characteristics.movement, custom.characteristics.leadership) == (5, 9)


def test_local_identity_does_not_replace_canonical_identity(precompiled):
    unit = precompiled().first
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


def test_context_free_and_empty_context_retain_rng_order_and_results(precompiled):
    unit = precompiled().first
    from mordheim_combat.modular.duel import simulate_duel_reference
    from mordheim_combat.vectorized import simulate_duel
    assert simulate_duel_reference(unit, unit, 30, seed=9) == simulate_duel_reference(unit, unit, 30, seed=9, context=DuelContext())
    request = DuelRequest(unit, unit, 100, seed=11, batch_size=31)
    assert simulate_duel(request, backend="numpy") == simulate_duel(replace(request, context=DuelContext()), backend="numpy")

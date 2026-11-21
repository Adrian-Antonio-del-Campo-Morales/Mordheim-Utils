"""Foundations of the Cython port: state schema, per-row projections, the
phase pipeline, decision keys and contextual facts.

One contract per capability.  Every case comes from the frozen corpus and is
run through the native batch core alone (``simulate_batch_observed`` with a
scripted source); nothing here samples the modular oracle or compares
engines.
"""
from __future__ import annotations

from dataclasses import fields, replace
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

from mordheim_core.models import DuelContext, LocalParticipant
from tools.verification.compiled_cases import load_cases

native = pytest.importorskip("mordheim_combat._combat_native")

_CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "compiled-cases.json"
#: Both duelists own the turn facts; no charge or priority die is drawn.
_STILL = DuelContext(charging=(), active_participant="first")


@lru_cache(maxsize=1)
def _cases():
    return load_cases(_CORPUS)


class _Misses:
    """Every die shows a one: no hit lands, so the duel outlives the round."""

    def integers(self, low, high, size=None):
        return np.ones(size, dtype=np.int8)

    def random(self, size=None):
        # A symmetric pair ties on priority and Initiative; the coin picks first.
        return np.zeros(size)


class _Recorder:
    def __init__(self):
        self.keys = []

    def choose(self, key, context=None):
        self.keys.append(key)
        return True


def test_state_schema_covers_every_combat_state_column():
    from mordheim_combat.vectorized._driver import _resource_observation
    from mordheim_combat.vectorized._state import initialize_fighter
    from mordheim_combat.vectorized._types import CombatState

    covered = set(native.STATE_COLUMNS)
    for alias, columns in native.STATE_COLUMN_ALIASES.items():
        assert set(columns) <= covered
        covered.add(alias)
    assert {field.name for field in fields(CombatState)} <= covered

    case = _cases()["scenario/basic"]
    result = native.simulate_batch_observed(case.first, case.second, 1, _Misses(), 1, context=_STILL)
    vector = initialize_fighter(case.first, 1, np.random.default_rng(0))
    assert [name for name, _ in result.first_resources] == [
        name for name, _ in _resource_observation(vector)]


def test_row_projection_simulates_the_projected_fighter():
    case = _cases()["scenario/durable-vs-elite"]
    printed = case.first.characteristics.wounds
    assert printed > 1
    thinner = replace(case.first, characteristics=replace(case.first.characteristics, wounds=1))
    trace = {}
    result = native.simulate_batch_observed(
        case.first, case.second, 2, _Misses(), 1, context=_STILL,
        row_projections={"first": {1: thinner}}, trace=trace)
    # Row 0 keeps the printed fighter; row 1 is folded through its own
    # projection, whose smaller maximum clamps the Wounds (the oracle's
    # post-projection clamp), with the opponent's rows untouched.
    assert list(trace["projection"][0]) == [0, 1]
    assert list(trace["projection"][1]) == [0, 0]
    assert list(result.first_wounds) == [printed, 1]


def test_round_phases_run_in_the_oracle_order():
    case = _cases()["scenario/basic"]
    trace = {}
    native.simulate_batch_observed(case.first, case.second, 1, _Misses(), 2, context=_STILL, trace=trace)
    assert trace["phases"] == list(native.ROUND_PHASES) * 2
    assert native.ROUND_PHASES[:2] == ("round-start", "own-turn-recovery")
    assert native.ROUND_PHASES[-3:] == ("pools", "attacks", "aftermath")


def test_decisions_are_asked_under_the_oracle_round_keys():
    case = _cases()["conformance/mechanic/mechanic.bull-charge/a-declared-bull-charge-knocks-the-enemy-down"]
    policy = _Recorder()
    trace = {}
    native.simulate_batch_observed(
        case.first, case.second, 1, _Misses(), 1, policy,
        context=DuelContext(charging=("first",), active_participant="first"), trace=trace)
    assert "round.0.first.bull-charge" in policy.keys
    assert trace["decisions"] == policy.keys
    assert all(key.startswith("round.0.") for key in policy.keys)


def test_context_folds_participants_and_engagement():
    from mordheim_combat.native._combat_compile import compile_context
    from mordheim_core.context import prepare_duel_context

    case = _cases()["scenario/basic"]
    first = replace(case.first, global_effects=replace(
        case.first.global_effects, tags=(*case.first.global_effects.tags, "band.test")))
    leader = replace(case.second, fighter_id="leader", global_effects=replace(
        case.second.global_effects,
        tags=(*case.second.global_effects.tags, "band.test", "mechanic.leader-six")))
    context = DuelContext(
        nearby=(LocalParticipant("boss", "first", leader, "knocked-down"),),
        distances=(("first", "boss", 5.0),),
    )
    folded = compile_context(prepare_duel_context(first, case.second, context))
    me, foe, boss = folded["participants"]
    assert (me["side"], boss["side"], foe["side"]) == (0, 0, 1)
    assert boss["condition"] == 1 and boss["flags"]["mechanic.leader-six"]
    assert me["bands"] == boss["bands"] == 1 and foe["bands"] == 0
    assert folded["distances"][0][2] == 5.0 and folded["distances"][1][2] == -1.0
    # Supplied contacts that do not join the duelists leave them unengaged:
    # the duel ends unresolved without a round, as the oracle's loop does.
    apart = DuelContext(contacts=(), charging=(), active_participant="first")
    result = native.simulate_batch_observed(case.first, case.second, 1, _Misses(), 3, context=apart)
    assert int(result.rounds[0]) == 0 and int(result.winner[0]) == 0

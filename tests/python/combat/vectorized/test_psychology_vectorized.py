"""Focused proof of the vectorized Psychology and local Leadership helpers.

These are the new owning layers for ``modular/psychology.py`` and
``modular/leadership.py``; each case exercises one consequence the batch loop
must consume, with deterministic dice so a single row set shows the pass and
fail sides of the same mask.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from mordheim_combat.vectorized._leadership import (
    leadership_resources,
    resolve_local_leadership,
)
from mordheim_combat.vectorized._psychology import (
    causes_fear,
    psychology_resources,
    resolve_fear,
    resolve_stupidity,
)
from mordheim_combat.vectorized._state import initialize_fighter
from mordheim_construction.compiler import compile_fighter
from mordheim_core.context import prepare_duel_context
from mordheim_core.models import (
    Characteristics,
    DuelContext,
    FighterBuild,
    LocalParticipant,
)


class FixedRng:
    """Return one value for every die of the row set."""

    def __init__(self, value: int):
        self.value = value

    def integers(self, low, high=None, size=None, dtype=None):
        return np.full(size if size is not None else (), self.value, dtype=dtype or np.int64)

    def random(self, size=None):
        return np.zeros(size if size is not None else ())


def fighter(*tags, leadership=7):
    base = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 2, 3, 1, leadership=leadership)))
    if not tags:
        return base
    return replace(base, global_effects=replace(
        base.global_effects,
        tags=tuple(dict.fromkeys((*base.global_effects.tags, *tags))),
    ))


@pytest.mark.phase5_vectorized
def test_stupidity_failure_stays_on_its_row_and_cancels_that_rows_charge():
    stupid = fighter("mechanic.stupidity")
    other = fighter()
    state = initialize_fighter(stupid, 6, FixedRng(1))
    opponent_state = initialize_fighter(other, 6, FixedRng(1))
    # The frenzied row skips the test; every other row rolls two sixes.
    state.frenzy[0] = True
    rows = np.arange(6)
    outcome = resolve_stupidity(
        stupid, other, state, opponent_state, rows,
        first_player_turn=True, round_index=0,
        charges=np.ones(6, dtype=bool), rng=FixedRng(6),
        leadership=leadership_resources(6),
    )

    assert list(outcome.failed) == [False, True, True, True, True, True]
    assert list(state.stupidity_failed) == [False, True, True, True, True, True]
    # A failed initial charge cannot establish contact that round.
    assert list(outcome.charges) == [True, False, False, False, False, False]

    # Only the named rows change: a later call for one row leaves the rest.
    state.stupidity_failed[:] = False
    resolve_stupidity(
        stupid, other, state, opponent_state, np.array([2]),
        first_player_turn=True, round_index=0,
        charges=np.ones(6, dtype=bool), rng=FixedRng(1),
        leadership=leadership_resources(6),
    )
    assert list(state.stupidity_failed) == [False, False, False, False, False, False]


@pytest.mark.phase5_vectorized
def test_a_failed_fear_test_after_being_charged_marks_only_the_charged_rows():
    terrifying = fighter("mechanic.causes-fear")
    victim = fighter(leadership=3)
    first_state = initialize_fighter(terrifying, 4, FixedRng(1))
    second_state = initialize_fighter(victim, 4, FixedRng(1))
    resources = (psychology_resources(4), psychology_resources(4))
    outcome = resolve_fear(
        terrifying, victim, first_state, second_state, np.arange(4),
        round_index=0, engaged=np.ones(4, dtype=bool),
        first_charges=np.ones(4, dtype=bool),
        second_charges=np.zeros(4, dtype=bool),
        rng=FixedRng(6), resources=resources,
    )

    assert outcome.first_charges.all()
    assert not outcome.second_charges.any()
    assert outcome.engaged.all()
    # The charged victim is hit on natural sixes only; the charger is untouched.
    assert resources[1].fear_hit_sixes.all()
    assert not resources[0].fear_hit_sixes.any()
    assert not outcome.first_failed.any()
    assert not outcome.second_failed.any()


@pytest.mark.phase5_vectorized
def test_a_failed_fear_test_cancels_the_chargers_contact_on_its_own_rows():
    pyromaniac = fighter("mechanic.fears-fire", leadership=3)
    flame = fighter("condition.open-flame")
    first_state = initialize_fighter(pyromaniac, 3, FixedRng(1))
    second_state = initialize_fighter(flame, 3, FixedRng(1))
    resources = (psychology_resources(3), psychology_resources(3))
    outcome = resolve_fear(
        pyromaniac, flame, first_state, second_state, np.arange(3),
        round_index=0, engaged=np.ones(3, dtype=bool),
        first_charges=np.ones(3, dtype=bool),
        second_charges=np.zeros(3, dtype=bool),
        rng=FixedRng(6), resources=resources,
    )

    assert outcome.first_failed.all()
    assert not outcome.first_charges.any()
    assert not outcome.engaged.any()
    assert not resources[0].fear_hit_sixes.any()


@pytest.mark.phase5_vectorized
def test_local_leadership_borrows_the_supplied_providers_value_within_its_radius():
    band = "band.test-warband"
    recruit = fighter(band, leadership=3)
    leader = fighter("mechanic.leader-six", band, leadership=9)
    state = initialize_fighter(recruit, 4, FixedRng(1))
    rows = np.arange(4)

    def context(distance):
        return prepare_duel_context(recruit, fighter(), DuelContext(
            nearby=(LocalParticipant("leader", "first", leader),),
            distances=(("first", "leader", distance),),
        ))

    # Two fours total 8: above the recruit's own 3, within the borrowed 9.
    borrowed = resolve_local_leadership(
        recruit, state, rows, first=True, key="round.0.first.leader",
        rng=FixedRng(4), context=context(6), decisions=None,
    )
    assert borrowed.all()
    out_of_range = resolve_local_leadership(
        recruit, state, rows, first=True, key="round.0.first.leader",
        rng=FixedRng(4), context=context(7), decisions=None,
    )
    assert not out_of_range.any()


@pytest.mark.phase5_vectorized
def test_the_holy_relic_passes_once_and_the_next_test_rolls_normally():
    bearer = fighter("defence.holy-relic", leadership=3)
    state = initialize_fighter(bearer, 2, FixedRng(1))
    resources = leadership_resources(2)
    args = dict(first=True, key="round.0.first.relic", context=None, decisions=None)
    first = resolve_local_leadership(
        bearer, state, np.arange(2), rng=FixedRng(6), resources=resources, **args)
    assert first.all()
    assert resources.holy_relic.all()
    second = resolve_local_leadership(
        bearer, state, np.arange(2), rng=FixedRng(6), resources=resources, **args)
    assert not second.any()


@pytest.mark.phase5_vectorized
def test_causes_fear_matches_the_scalar_operator_on_the_supplied_facts():
    from mordheim_combat.modular.psychology import causes_fear as scalar

    cases = (
        (fighter("mechanic.causes-fear"), fighter()),
        (fighter("mechanic.fear-human"), fighter("species.human")),
        (fighter("species.snake"), fighter("mechanic.fear-of-snakes")),
        (fighter("mechanic.fear-beastmen"), fighter("species.beastman")),
        (fighter("mechanic.fears-fire"), fighter("condition.open-flame")),
        (fighter("mechanic.morrs-servant"), fighter("nature.undead")),
    )
    for carrier, enemy in cases:
        assert causes_fear(carrier, enemy) is scalar(carrier, enemy)

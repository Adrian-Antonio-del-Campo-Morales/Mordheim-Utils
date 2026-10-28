"""A failed Stupidity test cancels the charge and ends the engagement.

Phase 0 regression guard (plan decision D1).  The oracle
(``modular.psychology.resolve_stupidity``) leaves a round-0 charger that fails
Stupidity with no charge and ``engaged=False``: the duel ends unresolved after
its one attempted round, both fighters untouched.  The NumPy driver used to
clear the charge but keep the row engaged, so the Stupid fighter fought on
without attacking.  The defect was invisible to every other test and showed up
only as three divergent parity-campaign rows (regen-vs-fire,
trained-bear-vs-scarecrow, silent-walker-vs-cold-one).
"""
from __future__ import annotations

import numpy as np

from mordheim_combat.vectorized import simulate_batch_observed
from mordheim_core.models import Characteristics, CompiledFighter, DuelContext, EffectSet


def _fighter(fighter_id: str, leadership: int, *tags: str) -> CompiledFighter:
    return CompiledFighter(
        fighter_id, Characteristics(3, 3, 3, 2, 3, 1, leadership=leadership),
        main_weapon=EffectSet(tags=("weapon.dagger",)), off_hand=None,
        global_effects=EffectSet(tags=tags), armour_save=7, helmet_save=7,
        natural_armour_save=7,
    )


def test_failed_stupidity_charge_ends_the_engagement_unresolved():
    stupid = _fighter("stupid", 4, "mechanic.stupidity")
    # Psychology immunity keeps Fear out: Stupidity is the only failing gate.
    steady = _fighter("steady", 7, "mechanic.psychology-immunity")
    count = 400

    forced = DuelContext(charging=("first",), active_participant="first")
    batch = simulate_batch_observed(
        stupid, steady, count, np.random.default_rng(11), 50, None, context=forced)
    unresolved = batch.winner == 0
    # P(2d6 > 4) = 30/36: the charge fails about 83% of the time.
    assert 0.72 <= unresolved.mean() <= 0.94
    assert (batch.rounds[unresolved] == 1).all()
    assert (batch.first_wounds[unresolved] == 2).all()
    assert (batch.second_wounds[unresolved] == 2).all()

    # When the steady fighter charges, no charge can be cancelled by Stupidity.
    other = DuelContext(charging=("second",), active_participant="second")
    batch = simulate_batch_observed(
        stupid, steady, count, np.random.default_rng(11), 50, None, context=other)
    assert not (batch.winner == 0).any()

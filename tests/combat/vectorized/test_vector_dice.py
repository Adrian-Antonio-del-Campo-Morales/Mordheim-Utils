from __future__ import annotations

import numpy as np

from mordheim_combat_lab.combat.vector_dice import FastVectorDice
from mordheim_combat_lab.combat.vector_dice import KeyedVectorDice
from mordheim_combat_lab.combat.vector_dice import VectorRollRequest


def test_keyed_vector_dice_are_stable_under_row_reordering_and_chunking():
    dice = KeyedVectorDice(91)
    rows = np.array([8, 2, 12, 1], dtype=np.int64)
    complete = dice.roll(VectorRollRequest("round.0.first.hit", rows))
    reordered = dice.roll(VectorRollRequest("round.0.first.hit", rows[::-1]))[::-1]
    chunked = np.concatenate((
        dice.roll(VectorRollRequest("round.0.first.hit", rows[:2])),
        dice.roll(VectorRollRequest("round.0.first.hit", rows[2:])),
    ))

    assert complete.tolist() == reordered.tolist() == chunked.tolist()
    assert np.all((complete >= 1) & (complete <= 6))


def test_semantic_keys_and_seeds_define_independent_rolls():
    rows = np.arange(32, dtype=np.int64)
    first = KeyedVectorDice(4).roll(VectorRollRequest("hit", rows))
    repeated = KeyedVectorDice(4).roll(VectorRollRequest("hit", rows))
    another_key = KeyedVectorDice(4).roll(VectorRollRequest("wound", rows))
    another_seed = KeyedVectorDice(5).roll(VectorRollRequest("hit", rows))

    assert first.tolist() == repeated.tolist()
    assert first.tolist() != another_key.tolist()
    assert first.tolist() != another_seed.tolist()


def test_fast_vector_dice_return_bulk_rolls_and_uniforms():
    rows = np.arange(100, dtype=np.int64)
    dice = FastVectorDice(7)
    rolls = dice.roll(VectorRollRequest("ignored-in-production", rows, sides=3))
    uniforms = dice.random("ignored-in-production", rows)

    assert rolls.shape == uniforms.shape == (100,)
    assert np.all((rolls >= 1) & (rolls <= 3))
    assert np.all((uniforms >= 0) & (uniforms < 1))

"""Vectorized engine: per-row mutation and shape projections.

The acquisition rules already exist, validated, in ``modular.mutations``.
This module keeps that one implementation and moves only its storage: the
projection is evaluated for the rows that actually carry a brand, and the
result is cached in ``CombatState.effective_fighter`` for the attack layers.

A batch may roll a different brand on different rows, so mutations are
per-row objects (a tuple per simulation), never a ``CompiledFighter`` shared
by the batch.  Nothing here runs a duel; the transition that acquires a
brand belongs to the round integration.
"""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace

import numpy as np

from mordheim_combat.modular.mutations import apply_brand
from mordheim_combat.modular.mutations import fighter_for_mutations
from mordheim_combat.vectorized._types import CombatState
from mordheim_core.dice import RollRequest
from mordheim_core.models import CarriedEquipment
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet
from mordheim_core.models import MutationOption


@dataclass(frozen=True, slots=True)
class MutationState:
    """The slice of one fighter's row that ``modular.mutations`` reads.

    It is a view, not a second engine: ``read_mutation_state`` fills it from
    the row's columns and ``write_mutation_state`` stores it back.
    """

    mutations: tuple[MutationOption, ...] = ()
    mutation_equipment: tuple[CarriedEquipment, ...] | None = None
    mutation_weapon_limbs: tuple[EffectSet, ...] = ()
    mutated_hands: tuple[str, ...] = ()
    atrophied_arms: int = 0
    atrophied_legs: int = 0
    transformed: bool = False
    equipment_cast_off: bool = False
    hillman_wolf: bool = False
    resources_spent: frozenset[str] = frozenset()
    parries_remaining: int = 0
    wounds: int = 0
    weapon_skill: int = 0
    strength: int = 0
    toughness: int = 0
    initiative: int = 0
    attacks: int = 0

    def spend(self, resource: str) -> "MutationState":
        return replace(self, resources_spent=self.resources_spent | {resource})


class _RowDice:
    """One row's generator exposed through the modular ``DiceSource`` protocol."""

    def __init__(self, rng: np.random.Generator) -> None:
        self.rng = rng

    def roll(self, request: RollRequest) -> int:
        return int(self.rng.integers(1, request.sides + 1))


def _tail_index(resources: frozenset[str]) -> int:
    for value in resources:
        if value.startswith("mutation-tail."):
            return int(value.rsplit(".", 1)[1])
    return -1


def read_mutation_state(state: CombatState, row: int) -> MutationState:
    """Read one simulation row as the modular mutation state."""
    tail = int(state.mutation_tail[row])
    return MutationState(
        mutations=state.mutations[row],
        mutation_equipment=state.mutation_equipment[row],
        mutation_weapon_limbs=state.mutation_weapon_limbs[row],
        mutated_hands=state.mutated_hands[row],
        atrophied_arms=int(state.atrophied_arms[row]),
        atrophied_legs=int(state.atrophied_legs[row]),
        transformed=bool(state.transformed[row]),
        equipment_cast_off=bool(state.equipment_cast_off[row]),
        hillman_wolf=bool(state.hillman_wolf[row]),
        resources_spent=(
            frozenset({f"mutation-tail.{tail}"}) if tail >= 0 else frozenset()
        ),
        parries_remaining=int(state.parry_remaining[row]),
        wounds=int(state.wounds[row]),
        weapon_skill=int(state.weapon_skill[row]),
        strength=int(state.strength[row]),
        toughness=int(state.toughness[row]),
        initiative=int(state.initiative[row]),
        attacks=int(state.attacks[row]),
    )


def write_mutation_state(
    state: CombatState, row: int, current: MutationState,
) -> None:
    """Store a modular mutation state back into its own row."""
    state.mutations[row] = current.mutations
    state.mutation_equipment[row] = current.mutation_equipment
    state.mutation_weapon_limbs[row] = current.mutation_weapon_limbs
    state.mutated_hands[row] = current.mutated_hands
    state.atrophied_arms[row] = current.atrophied_arms
    state.atrophied_legs[row] = current.atrophied_legs
    state.transformed[row] = current.transformed
    state.equipment_cast_off[row] = current.equipment_cast_off
    state.hillman_wolf[row] = current.hillman_wolf
    state.mutation_tail[row] = _tail_index(current.resources_spent)
    state.parry_remaining[row] = current.parries_remaining
    state.wounds[row] = current.wounds
    state.weapon_skill[row] = current.weapon_skill
    state.strength[row] = current.strength
    state.toughness[row] = current.toughness
    state.initiative[row] = current.initiative
    state.attacks[row] = current.attacks
    # The cached projection described the previous brand set.
    state.effective_fighter[row] = None


def fighter_for_row(
    fighter: CompiledFighter, state: CombatState, row: int,
) -> CompiledFighter:
    """Return the effective fighter of one row, projecting it once."""
    cached = state.effective_fighter[row]
    if cached is not None:
        return cached
    if not state.mutations[row]:
        return fighter
    projected = fighter_for_mutations(fighter, read_mutation_state(state, row))
    state.effective_fighter[row] = projected
    return projected


def apply_brand_row(
    fighter: CompiledFighter, state: CombatState, row: int,
    option: MutationOption, rng: np.random.Generator,
    decisions=None, key: str = "mutation",
) -> CompiledFighter:
    """Acquire one brand on one row and return its projected fighter.

    The transition timing (when a row rolls its brand) belongs to the round
    integration; this helper only keeps the existing acquisition rule.
    """
    current = read_mutation_state(state, row)
    result = apply_brand(fighter, current, option, _RowDice(rng), decisions, key)
    write_mutation_state(state, row, result)
    return fighter_for_row(fighter, state, row)


def refresh_effective_fighter(state: CombatState, row: int) -> None:
    """Drop a row's cached projection after an out-of-band state change."""
    state.effective_fighter[row] = None

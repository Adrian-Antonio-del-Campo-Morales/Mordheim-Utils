"""Vectorized engine: the equipment a combat phase actually uses.

The rules already exist, validated, in ``modular.equipment.equipment_for_state``
(loss of a broken hand's items, transformations that cast the kit off, the
Cursed Hillman's wolf form, the Festooned with Pistols club, carried backup
weapons and the extra attacks a lost slot takes with it).  This module keeps
that one implementation and moves only its storage:

* :func:`phase_equipment` is the batch-wide projection the round driver uses.
* :func:`equipment_for_rows` projects the rows that carry their own state
  (broken hands, a mutation projection, a transformation), so a change on one
  simulation never rewrites the equipment of the whole batch.
"""
from __future__ import annotations

from dataclasses import replace

import numpy as np

from mordheim_combat.modular.equipment import equipment_for_state
from mordheim_combat.modular.state import FighterState
from mordheim_core.models import CompiledFighter, EffectSet
from ._types import CombatState, has


def _broken_slots(fighter: CompiledFighter, broken: int) -> frozenset[str]:
    """Translate the per-row hand bit mask into the modular slot set.

    Bit 1 is the main hand and bit 2 the off hand, the two slots the vectorized
    engine damages today.  The modular state also names ``extra``, ``tail`` and
    ``backup.N`` slots; those are carried by G02's ``mutation_equipment``
    columns and are not expressible in this mask yet (see the G04 deliverable).
    """
    slots = set()
    if broken & 1:
        slots.add(fighter.main_hand_slot)
    if broken & 2:
        slots.add(fighter.off_hand_slot)
    # Bits 4, 8, ... name the mutated hands (``mutation.hand.<slot>`` extra
    # attacks) in the projected fighter's order, so a whip's disarm can break
    # them as the modular ``_choose_whip_disarm`` candidates allow.
    for index, slot in enumerate(mutation_hand_slots(fighter)):
        if broken & (4 << index):
            slots.add(slot)
    return frozenset(slots)


def mutation_hand_slots(fighter: CompiledFighter) -> tuple[str, ...]:
    """The ``mutation.hand.<slot>`` slots of the fighter's extra attacks, in order."""
    return tuple(
        tag.removeprefix("mutation.hand.")
        for attack in fighter.extra_attacks for tag in attack.tags
        if tag.startswith("mutation.hand."))


def _row_state(
    fighter: CompiledFighter, broken: int, *,
    transformed: bool = False, equipment_cast_off: bool = False,
    hillman_wolf: bool = False,
) -> FighterState:
    """The four state facts ``equipment_for_state`` reads, for one row."""
    return FighterState(
        wounds=1,
        broken_hands=_broken_slots(fighter, broken),
        transformed=transformed,
        equipment_cast_off=equipment_cast_off,
        hillman_wolf=hillman_wolf,
    )


def phase_equipment(fighter: CompiledFighter, *, first_round: bool,
                    broken_hands: int = 0,
                    transformed: bool = False, equipment_cast_off: bool = False,
                    hillman_wolf: bool = False) -> CompiledFighter:
    """Return the fighter whose equipment this phase uses.

    The defaults keep the historical driver call unchanged; the extra keyword
    arguments let the round integration hand one simulation's state in without
    touching the other rows.
    """
    return equipment_for_state(
        fighter,
        _row_state(
            fighter, broken_hands, transformed=transformed,
            equipment_cast_off=equipment_cast_off, hillman_wolf=hillman_wolf,
        ),
        first_round=first_round,
    )


def equipment_for_rows(
    fighter: CompiledFighter, state: CombatState, rows: np.ndarray, *,
    first_round: bool,
) -> dict[int, CompiledFighter]:
    """Project the effective equipment of ``rows``, one simulation at a time.

    A row without broken hands, without a mutation projection and without a
    transformation keeps the batch-wide projection, so the common case costs
    one projection for the whole batch.  Only a row that owns the change pays
    for its own one.
    """
    base = phase_equipment(fighter, first_round=first_round)
    projected: dict[int, CompiledFighter] = {}
    for value in np.asarray(rows).ravel():
        row = int(value)
        row_fighter = _fighter_for_row(fighter, state, row)
        broken = int(state.broken_hands[row])
        transformed = bool(state.transformed[row])
        cast_off = bool(state.equipment_cast_off[row])
        wolf = bool(state.hillman_wolf[row])
        if (row_fighter is fighter and not broken and not transformed
                and not cast_off and not wolf):
            projected[row] = base
            continue
        projected[row] = equipment_for_state(
            row_fighter,
            _row_state(
                row_fighter, broken, transformed=transformed,
                equipment_cast_off=cast_off, hillman_wolf=wolf,
            ),
            first_round=first_round,
        )
    return projected


def _fighter_for_row(fighter: CompiledFighter, state: CombatState, row: int) -> CompiledFighter:
    # Imported lazily: ``_mutations`` builds on the same state schema and the
    # equipment layer only needs the projection when a row actually has marks.
    from mordheim_combat.vectorized._mutations import fighter_for_row
    return fighter_for_row(fighter, state, row)


def staff_power(fighter: CompiledFighter, decisions, key: str) -> CompiledFighter:
    if has(fighter.main_weapon, 'weapon.serpent-staff') and (
        decisions is None or decisions.choose(f'{key}.serpent-staff', fighter)
    ):
        return replace(fighter, main_weapon=EffectSet(
            tags=('effect.serpent-staff-power',), fixed_strength=4, priority=1),
            off_hand=None, off_hand_attacks=False, extra_attacks=())
    return fighter

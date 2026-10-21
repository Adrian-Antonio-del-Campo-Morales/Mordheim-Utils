"""Vectorized engine: per-simulation fighter state initialisation.

This module ports ``modular.state.initialize_fighter``,
``modular.state.require_characteristics``,
``modular.state._refresh_random_characteristics`` and the duel-start charge
validation of ``modular.state.initialize_duel`` to array columns.

Every field of :class:`~mordheim_combat.vectorized._types.CombatState` is
indexed by simulation row and belongs to exactly one fighter: the two
combatants of a batch never share an array, and a value written on one row
never reaches another.  The modular contract stays the single source of the
rules; only the storage is per row.
"""
from __future__ import annotations

import numpy as np

from mordheim_combat.vectorized._types import (
    CombatState,
    KNOCKED_DOWN,
    STANDING,
    _parry_capacity,
    has,
)
from mordheim_combat.modular.state import maximum_wounds
from mordheim_core.context import prepare_duel_context
from mordheim_core.models import CompiledFighter
from mordheim_core.models import DuelContext


#: Order of ``CombatState.random_modifiers`` and the bit each characteristic
#: owns in ``CombatState.random_rolled``.
STATS = ("WS", "S", "T", "I", "A")
STAT_BITS = {stat: 1 << index for index, stat in enumerate(STATS)}
STAT_ATTRIBUTES = {
    "WS": "weapon_skill", "S": "strength", "T": "toughness",
    "I": "initiative", "A": "attacks",
}

#: The condition bonuses ``initialize_fighter`` folds into the live profile.
#: Each tuple is ``(tag, characteristic, bonus)``; only the Alchemist's
#: Backley's Brew entries are kept to be restored later (``alchemy.py``).
_CONDITION_BONUSES = (
    ("condition.petru-debilitating", "T", -1),
    ("condition.petru-strength", "S", 1),
    ("condition.petru-resilience", "T", 1),
    ("condition.alchemist-resilience", "T", 1),
    ("condition.alchemist-strength", "S", 1),
    ("condition.alchemist-aberrantius-vigortia", "S", 1),
    ("condition.alchemist-aberrantius-vigortia", "T", 1),
    ("condition.alchemist-backleys-brew", "S", -1),
    ("condition.alchemist-backleys-brew", "I", -1),
)

_CHARGE_TARGETS = (
    "band.carnival-of-chaos",
    "identity.onogal-follower",
)
_WITCH_FINDER_TARGETS = (
    "identity.chaos-follower", "warband-group.chaotic", "identity.warlock",
    "identity.necromancer", "identity.sorcerer", "identity.warp-tainted",
)


def _objects(value, count: int) -> np.ndarray:
    """One object column where every row owns the given immutable value."""
    column = np.empty(count, dtype=object)
    column[:] = [value] * count
    return column


# ``maximum_wounds`` is re-exported from the validated modular contract: the
# extra Wound of the shared monstrous operator and the Petru Fortitude
# exception must stay one definition, not a second copy.
__all__ = [
    "STATS",
    "charge_allowed",
    "initialize_fighter",
    "maximum_wounds",
    "refresh_random_characteristics",
    "require_characteristics",
    "validate_duel_start",
]


def initialize_fighter(
    fighter: CompiledFighter, count: int, rng: np.random.Generator, *,
    lazy_inconsistency: bool = False,
) -> CombatState:
    """Port of ``modular.state.initialize_fighter`` for ``count`` rows.

    ``lazy_inconsistency`` selects the modular cadence: a variable WS/S/T/A
    profile is left unrolled until an operation calls
    :func:`require_characteristics`.  The historical ``_new_state`` entry
    point keeps the engine's previous eager draw for the same profile (see the
    G02 deliverable); the round integration switches it once the operators
    call the lazy helper.
    """
    effects = fighter.global_effects
    characteristics = fighter.characteristics
    inconsistency = has(effects, "mechanic.inconsistency")
    values: dict[str, int] = {
        "WS": characteristics.weapon_skill,
        "S": characteristics.strength,
        "T": characteristics.toughness + effects.toughness_bonus,
        "I": characteristics.initiative,
        "A": characteristics.attacks,
    }
    crimson = (
        rng.integers(1, 4, count, dtype=np.int8)
        if has(effects, "preparation.crimson-shade")
        else np.zeros(count, dtype=np.int8)
    )
    # In the modular cadence a supplied permanently variable profile is *not*
    # rolled at duel start: each characteristic is drawn when its operation
    # needs it.  The eager branch keeps the historical ``_new_state`` behaviour
    # until the operators call the lazy helper (see the G02 deliverable).
    lazy = inconsistency and lazy_inconsistency
    random_characteristics = () if lazy else fighter.random_characteristics
    for characteristic, dice, sides, bonus in random_characteristics:
        rolls = np.zeros(count, dtype=np.int16)
        for _ in range(dice):
            rolls += rng.integers(1, sides + 1, count, dtype=np.int16)
        values[characteristic] = rolls + bonus
    backley: dict[str, int] = {}
    for tag, stat, bonus in _CONDITION_BONUSES:
        if not has(effects, tag):
            continue
        base = values[stat]
        if base is None:
            # An absent characteristic has no base to modify.
            continue
        before = base
        values[stat] = base + bonus if inconsistency else max(1, base + bonus)
        if tag == "condition.alchemist-backleys-brew":
            backley[stat] = before - values[stat]
    poetry = has(effects, "condition.poetry-inspired")
    if poetry:
        values["WS"] += 1
    supplied_disability = next(
        (result for result in range(1, 7)
         if has(effects, f"condition.disability-{result}")),
        0,
    )
    if has(effects, "mechanic.disability") and not supplied_disability:
        # The permanent table result is supplied at construction and priced in
        # there; the duel never rolls it (same contract as ``initialize_fighter``).
        raise ValueError(
            "Disability requires a permanent supplied result, not a duel-time table roll"
        )
    disability = np.full(count, supplied_disability, dtype=np.int8)
    guiding_dream = (
        rng.integers(1, 7, count, dtype=np.int8)
        if has(effects, "mechanic.guiding-dream")
        else np.zeros(count, dtype=np.int8)
    )
    nominated = has(effects, "condition.guiding-dream-target")
    # An absent Initiative (``None``) keeps its flag in ``initiative_missing``
    # and uses the ordering placeholder zero in the numeric column.
    columns = {
        stat: np.full(count, 0 if value is None else value, dtype=np.int16)
        for stat, value in values.items()
    }
    if nominated:
        columns["S"] += np.isin(guiding_dream, (4, 5)).astype(np.int16)
    netted = has(effects, "condition.netted")
    netted_rows = np.full(count, netted, dtype=bool)
    frenzy = np.full(count, has(effects, "mechanic.persistent-frenzy"), dtype=bool)
    initial_frenzy = np.full(count, bool(effects.frenzy), dtype=bool)
    if nominated:
        initial_frenzy |= guiding_dream == 6
    # Psychology immunity suppresses the initial frenzy; the two explicit
    # exceptions are persistent frenzy (above) and Snorri's supplied frenzy.
    frenzy_permitted = np.full(
        count,
        not has(effects, "mechanic.psychology-immunity")
        or has(effects, "condition.snorri-frenzy"),
        dtype=bool,
    )
    frenzy |= initial_frenzy & ~netted_rows & frenzy_permitted
    wounds = maximum_wounds(fighter)
    random_modifiers = np.zeros((len(STATS), count), dtype=np.int16)
    random_rolled = np.zeros(count, dtype=np.uint8)
    if inconsistency:
        for stat, *_ in fighter.random_characteristics:
            printed = getattr(characteristics, STAT_ATTRIBUTES[stat])
            random_modifiers[STATS.index(stat), :] = columns[stat] - printed
            if not lazy:
                # Legacy eager draw: it already stands for this round's value.
                random_rolled[:] |= STAT_BITS[stat]
    state = CombatState(
        wounds=np.full(count, wounds, dtype=np.int16),
        condition=np.full(count, KNOCKED_DOWN if netted else STANDING, dtype=np.int8),
        initiative_penalty=np.zeros(count, dtype=np.int8),
        initiative_floor=np.ones(count, dtype=np.int8),
        frenzy=frenzy,
        lucky_charm=np.full(count, has(effects, "defence.lucky-charm"), dtype=bool),
        crimson_initiative=crimson,
        attack_penalty=np.zeros(count, dtype=np.int8),
        entangled=np.zeros(count, dtype=bool),
        parry_used=np.zeros(count, dtype=bool),
        parry_remaining=np.full(count, _parry_capacity(fighter), dtype=np.int8),
        seaguard_used=np.zeros(count, dtype=bool),
        corruption_used=np.zeros(count, dtype=bool),
        critical_used=np.zeros(count, dtype=bool),
        force_of_will_used=np.zeros(count, dtype=bool),
        force_of_will_active=np.zeros(count, dtype=bool),
        force_of_will_penalty=np.zeros(count, dtype=np.int8),
        disability=disability,
        mark_of_old_ones_used=np.zeros(count, dtype=bool),
        luck_used=np.zeros(count, dtype=bool),
        on_fire=np.zeros(count, dtype=bool),
        weapon_skill=columns["WS"],
        strength=columns["S"],
        toughness=columns["T"],
        initiative=columns["I"],
        attacks=columns["A"],
        broken_hands=np.zeros(count, dtype=np.uint8),
        hampered_main=np.zeros(count, dtype=np.int16),
        hampered_off=np.zeros(count, dtype=np.int16),
        starting_wounds=np.full(count, wounds, dtype=np.int16),
        initiative_missing=np.full(count, characteristics.initiative is None, dtype=bool),
        random_rolled=random_rolled,
        random_modifiers=random_modifiers,
        torture_strength_loss=np.zeros(count, dtype=np.int8),
        guiding_dream_result=guiding_dream,
        stupidity_failed=np.full(
            count,
            has(effects, "condition.stupidity-failed")
            and not has(effects, "condition.stupidity-exempt")
            and not effects.frenzy
            and not has(effects, "mechanic.psychology-immunity"),
            dtype=bool,
        ),
        massively_built_lost_turn=np.full(
            count, has(effects, "condition.massively-built-lost-turn"), dtype=bool,
        ),
        netted=np.full(count, netted, dtype=bool),
        fear_hit_sixes=np.zeros(count, dtype=bool),
        grappled=np.zeros(count, dtype=bool),
        grappling=np.zeros(count, dtype=bool),
        backley_penalties=_objects(tuple(backley.items()), count),
        mutations=_objects((), count),
        mutation_equipment=_objects(None, count),
        mutation_weapon_limbs=_objects((), count),
        mutated_hands=_objects((), count),
        atrophied_arms=np.zeros(count, dtype=np.int8),
        atrophied_legs=np.zeros(count, dtype=np.int8),
        transformed=np.zeros(count, dtype=bool),
        equipment_cast_off=np.zeros(count, dtype=bool),
        hillman_wolf=np.full(
            count, "compiler.hillman-wolf-form" in fighter.construction_tags, dtype=bool,
        ),
        mutation_tail=np.full(count, -1, dtype=np.int8),
        effective_fighter=_objects(None, count),
    )
    return state


def require_characteristics(
    fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
    rng: np.random.Generator, needed,
) -> None:
    """Roll an Inconsistency value only when the current operation needs it.

    ``rows`` names the simulations whose operation needs the characteristic;
    the value is drawn at the call site, in declared order, and reused for the
    rest of the round.  Rows outside ``rows`` are untouched.
    """
    if not has(fighter.global_effects, "mechanic.inconsistency") or rows.size == 0:
        return
    needed = set(needed)
    for characteristic, dice, sides, bonus in fighter.random_characteristics:
        if characteristic not in needed:
            continue
        bit = STAT_BITS[characteristic]
        pending = (state.random_rolled[rows] & bit) == 0
        if not pending.any():
            continue
        selected = rows[pending]
        rolls = np.zeros(selected.size, dtype=np.int16)
        for _ in range(dice):
            rolls += rng.integers(1, sides + 1, selected.size, dtype=np.int16)
        delta = state.random_modifiers[STATS.index(characteristic), selected]
        if characteristic == "S":
            delta = delta - state.torture_strength_loss[selected]
        getattr(state, STAT_ATTRIBUTES[characteristic])[selected] = np.maximum(
            1, rolls + bonus + delta,
        )
        state.random_rolled[selected] |= bit


def refresh_random_characteristics(
    fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
    rng: np.random.Generator, *, lazy_inconsistency: bool = False,
) -> None:
    """Start a new round for ``rows`` and refresh variable characteristics.

    The rolled mask is per round, exactly as ``rounds.resolve_round`` clears
    ``random_rolled`` when the turn advances.  With ``lazy_inconsistency`` an
    Inconsistency profile waits for its next operation's own draw, as the
    modular refresh does; a profile whose whole WS/S/T/A line is random is
    re-rolled at once.  The default keeps the engine's historical eager draw
    until the operators call :func:`require_characteristics`.
    """
    state.random_rolled[rows] = 0
    random_stats = {characteristic for characteristic, *_ in fighter.random_characteristics}
    if not {"WS", "S", "T", "A"}.issubset(random_stats):
        return
    inconsistency = has(fighter.global_effects, "mechanic.inconsistency")
    if inconsistency and lazy_inconsistency:
        return
    values: dict[str, np.ndarray] = {}
    for characteristic, dice, sides, bonus in fighter.random_characteristics:
        rolls = np.zeros(rows.size, dtype=np.int16)
        for _ in range(dice):
            rolls += rng.integers(1, sides + 1, rows.size, dtype=np.int16)
        values[characteristic] = rolls + bonus
    state.weapon_skill[rows] = values["WS"]
    state.strength[rows] = np.maximum(1, values["S"] - state.torture_strength_loss[rows])
    state.toughness[rows] = values["T"] + fighter.global_effects.toughness_bonus
    state.initiative[rows] = values.get("I", state.initiative[rows])
    state.attacks[rows] = values.get("A", state.attacks[rows])
    if inconsistency:
        for characteristic, *_ in fighter.random_characteristics:
            state.random_rolled[rows] |= STAT_BITS[characteristic]


def charge_allowed(fighter: CompiledFighter, opponent: CompiledFighter) -> bool:
    """Whether this duelist may declare the initial charge (modular contract)."""
    effects = fighter.global_effects
    return (
        not has(effects, "mechanic.cannot-charge")
        and not has(effects, "condition.alchemist-addicted")
        and (
            not has(effects, "mechanic.shallya-strictures")
            or any(has(opponent.global_effects, tag) for tag in _CHARGE_TARGETS)
        )
    )


def validate_duel_start(
    first: CompiledFighter, second: CompiledFighter,
    context: DuelContext | None = None,
) -> tuple[bool, bool] | None:
    """Validate the supplied duel facts before a batch initialises.

    Returns the supplied charge flags ``(first, second)`` when the context
    states who charges and ``None`` when charges are still to be sampled.
    Raises the same ``ValueError`` the modular ``initialize_duel`` raises for
    an impossible supplied snapshot; sampling itself stays with the caller.
    """
    for fighter in (first, second):
        if "weapon.lance" in fighter.main_weapon.tags:
            raise ValueError(
                "weapon.lance is outside the one-against-one runtime: "
                "mounted combat is not supported"
            )
    for fighter, opponent in ((first, second), (second, first)):
        if (has(fighter.global_effects, "condition.guiding-dream-target")
                and not has(opponent.global_effects, "fighter-kind.hero")):
            raise ValueError("Guiding Dream requires the nominated opposing model to be a Hero")
    prepared = prepare_duel_context(first, second, context)
    if prepared is None or prepared.facts.charging is None:
        return None
    allowed = (
        charge_allowed(first, second),
        charge_allowed(second, first),
    )
    in_base_contact = (
        prepared.facts.contacts is not None
        and any(
            {a, b} == {prepared.facts.first_id, prepared.facts.second_id}
            for a, b in prepared.facts.contacts
        )
    )
    charged = prepared.charge_flags(True)
    if any(charging and not permitted for charging, permitted in zip(charged, allowed)):
        raise ValueError("Charging configuration violates Cannot Charge or Shallyan Strictures")
    if in_base_contact and (charged[0] or charged[1]):
        raise ValueError(
            "A supplied charge contradicts the supplied base contact between the duelists"
        )
    for charging, fighter, opponent in (
        (charged[0], first, second), (charged[1], second, first),
    ):
        if (any(has(fighter.global_effects, tag)
                for tag in ("condition.impetuous-charge", "condition.nuttaz-charge"))
                and not charging):
            raise ValueError(
                "A supplied compulsory charge requires its initial in-range charging attempt"
            )
        if has(fighter.global_effects, "condition.witch-finder-charge"):
            if (
                not has(fighter.global_effects, "mechanic.solkan-witch-finder")
                or not charging
                or not any(has(opponent.global_effects, tag) for tag in _WITCH_FINDER_TARGETS)
            ):
                raise ValueError(
                    "Supplied Witch-finder charge requires its named enemy and charging attempt"
                )
    return charged

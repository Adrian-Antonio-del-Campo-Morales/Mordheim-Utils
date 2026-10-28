"""Vectorized engine: run constants, ledger types, tag predicates
and compile-time helpers shared by every layer."""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from mordheim_core.models import CompiledFighter, EffectSet

STANDING, KNOCKED_DOWN, STUNNED, PARALYZED, OUT = range(5)

#: ``FighterState.djinn_power`` / ``last_djinn_power`` (``None`` / ``"curse"``
#: / ``"luck"``) as an int8 column.
DJINN_NONE, DJINN_CURSE, DJINN_LUCK = 0, 1, 2
DJINN_POWER_NAMES = {DJINN_CURSE: "curse", DJINN_LUCK: "luck"}


class RowResources:
    """Per-row port of the modular ``FighterState.resources_spent`` set.

    The scalar state keeps a frozenset of spent resource names; a batch keeps
    one boolean column per name, created on first use.  ``spend`` marks rows,
    ``spent`` reads a column (all-False when the name was never spent) and
    ``release`` is the ``resources_spent - {name}`` transition.  Names are the
    modular ones, so a ported clause spends exactly the string the oracle does.
    """

    __slots__ = ("count", "_columns")

    def __init__(self, count: int) -> None:
        self.count = int(count)
        self._columns: dict[str, np.ndarray] = {}

    def spent(self, name: str) -> np.ndarray:
        column = self._columns.get(name)
        if column is None:
            column = np.zeros(self.count, dtype=bool)
            self._columns[name] = column
        return column

    def available(self, name: str, rows: np.ndarray | None = None) -> np.ndarray:
        column = ~self.spent(name)
        return column if rows is None else column[rows]

    def spend(self, name: str, rows: np.ndarray | None = None) -> None:
        column = self.spent(name)
        if rows is None:
            column[:] = True
        else:
            column[rows] = True

    def release(self, name: str, rows: np.ndarray | None = None) -> None:
        column = self.spent(name)
        if rows is None:
            column[:] = False
        else:
            column[rows] = False

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._columns))

def _run_starts(values: np.ndarray) -> np.ndarray:
    """First index of each run in an ascending-sorted array (O(n), no sort)."""
    if values.size < 2:
        return np.arange(values.size, dtype=np.intp)
    changed = np.empty(values.size, dtype=bool)
    changed[0] = True
    np.not_equal(values[1:], values[:-1], out=changed[1:])
    return np.flatnonzero(changed)

@dataclass(slots=True)
class CombatState:
    wounds: np.ndarray
    condition: np.ndarray
    initiative_penalty: np.ndarray
    initiative_floor: np.ndarray
    frenzy: np.ndarray
    lucky_charm: np.ndarray
    crimson_initiative: np.ndarray
    attack_penalty: np.ndarray
    entangled: np.ndarray
    parry_used: np.ndarray
    parry_remaining: np.ndarray
    #: Per-phase resources: Seaguard Spear Master rerolls one failed hit in the
    #: opening round, and a corrupted defender forces one hit to be rerolled.
    #: The driver clears both with ``parry_used`` at the start of every round.
    seaguard_used: np.ndarray
    corruption_used: np.ndarray
    critical_used: np.ndarray
    force_of_will_used: np.ndarray
    force_of_will_active: np.ndarray
    force_of_will_penalty: np.ndarray
    disability: np.ndarray
    mark_of_old_ones_used: np.ndarray
    luck_used: np.ndarray
    on_fire: np.ndarray
    weapon_skill: np.ndarray
    strength: np.ndarray
    toughness: np.ndarray
    initiative: np.ndarray
    attacks: np.ndarray
    broken_hands: np.ndarray
    hampered_main: np.ndarray
    hampered_off: np.ndarray
    # --- Initialisation, recovery and per-row bookkeeping -------------------
    #: Wound total ``initialize_fighter`` computed for this fighter.  Recovery
    #: and the wounded-attacks test compare against it instead of re-deriving
    #: the printed profile, which gear can fold a Wound into.
    starting_wounds: np.ndarray
    #: ``True`` when the printed profile fixes no Initiative.  The numeric
    #: column is an ordering placeholder; the absence itself is kept here.
    initiative_missing: np.ndarray
    #: Bit mask of the lazy Inconsistency characteristics already rolled for
    #: the current round (1 WS, 2 S, 4 T, 8 I, 16 A).
    random_rolled: np.ndarray
    #: Fixed delta per characteristic (``("WS", "S", "T", "I", "A")``) that
    #: a lazy roll adds to its die: the supplied permanently fixed value the
    #: fighter keeps for the whole duel.
    random_modifiers: np.ndarray
    torture_strength_loss: np.ndarray
    #: Battle-start Guiding Dream D6; 0 when the fighter has no such roll.
    guiding_dream_result: np.ndarray
    stupidity_failed: np.ndarray
    massively_built_lost_turn: np.ndarray
    netted: np.ndarray
    #: Fear's per-row "natural sixes only" fact.  The driver copies G05's
    #: ``PsychologyResources.fear_hit_sixes`` here each round so every attack
    #: path (weapons, bonuses, holds) reads the same mask.
    fear_hit_sixes: np.ndarray
    #: Close-combat hold, per row: the victim is held and the holder grips it.
    grappled: np.ndarray
    grappling: np.ndarray
    #: Alchemist/Backley penalties kept as the ``(stat, points)`` pairs the
    #: modular state stores, so a later brew update can restore them.
    backley_penalties: np.ndarray
    # --- Equipment, mutated members and shape changes -----------------------
    #: Per row, because a batch may roll different brands on different rows.
    mutations: np.ndarray
    mutation_equipment: np.ndarray
    mutation_weapon_limbs: np.ndarray
    mutated_hands: np.ndarray
    atrophied_arms: np.ndarray
    atrophied_legs: np.ndarray
    transformed: np.ndarray
    equipment_cast_off: np.ndarray
    hillman_wolf: np.ndarray
    #: Selected prehensile tail index, -1 when none is selected.  The modular
    #: state spends ``mutation-tail.<n>``; the array keeps the same fact.
    mutation_tail: np.ndarray
    #: Per-row cache of the projected ``CompiledFighter``.  ``None`` means the
    #: printed fighter is still the effective one; the mutation helpers fill it.
    effective_fighter: np.ndarray
    # --- Phase 2: round actions, control powers and personal roll resources --
    #: Generic per-row ``resources_spent`` (see :class:`RowResources`).  The
    #: dedicated columns above keep their names; new ported clauses spend the
    #: modular resource string here instead of adding a column each.
    resources: RowResources
    #: Ranald's Luck adjusted one owned roll by one, once per battle.
    ranalds_luck_used: np.ndarray
    #: Oracle / Augur re-rolled one owned roll, once per battle.
    one_roll_reroll_used: np.ndarray
    #: Feral Instinct: this own turn's Leadership test failed.
    feral_instinct_failed: np.ndarray
    #: Lunatics: this round's D6 and the Stupidity it imposes (4+).
    lunatic_result: np.ndarray
    lunatic_stupidity: np.ndarray
    #: Djinn's Curse: the power chosen this turn and the one chosen last turn
    #: (``DJINN_NONE`` / ``DJINN_CURSE`` / ``DJINN_LUCK``).
    djinn_power: np.ndarray
    last_djinn_power: np.ndarray
    #: Devoted to the Vampire: the Frenzy the clause granted (not a rolled one).
    devoted_frenzy: np.ndarray
    #: Danse Macabre: still controlled until an own-turn test is passed.
    danse_macabre_controlled: np.ndarray
    #: Dark Jester: the one trick active this round, if any.
    dodge_trick_active: np.ndarray
    banter_trick_active: np.ndarray
    trip_trick_active: np.ndarray
    #: Needle and Thread: the victim's mouth is sewn shut.
    mouth_sewn: np.ndarray
    #: Drenok's Berserker: fighting on at zero Wounds this player turn.
    drenok_fighting: np.ndarray
    #: Electrical Touch: first round index at which the jolt is available again.
    electrical_available_at: np.ndarray
    #: A failed control test (Mark of Shornaal, Hypnotic Gaze) lets every
    #: attack hit the victim automatically this phase.
    charm_auto_hit: np.ndarray

@dataclass(slots=True)
class PreparedAttack:
    weapon: EffectSet
    effect: EffectSet
    active: np.ndarray
    strength: np.ndarray
    armour_strength: np.ndarray
    hit_target: np.ndarray
    rolls: np.ndarray
    hit_rows: np.ndarray
    rerolled: np.ndarray
    #: Physical face of the die that produced each row's final hit, before a
    #: granted success (Mark of the Old Ones) substitutes the target number.
    #: Six-triggered rules read this, never the substituted value.
    natural: np.ndarray | None = None

@dataclass(slots=True)
class VectorAttackObservation:
    """Single-row phase observation used by exact semantic replay."""
    hit: bool = False
    hit_roll: int | None = None
    hit_target: int | None = None
    parried: bool = False
    wounded: bool = False
    saved: bool = False
    damage: int = 0
    critical: bool = False

@dataclass(frozen=True, slots=True)
class VectorBatchObservation:
    """Per-row terminal state exposed only to verification and diagnostics."""

    winner: np.ndarray
    rounds: np.ndarray
    first_wounds: np.ndarray
    second_wounds: np.ndarray
    first_condition: np.ndarray
    second_condition: np.ndarray
    first_resources: tuple[tuple[str, np.ndarray], ...]
    second_resources: tuple[tuple[str, np.ndarray], ...]

@dataclass(frozen=True, slots=True)
class OptionalPhasePlan:
    """Immutable switches for stateful phases that a duel can never enter."""

    first_force_of_will: bool
    second_force_of_will: bool
    first_spines: bool
    second_spines: bool
    first_netter: bool
    second_netter: bool
    first_black_hunger: bool
    second_black_hunger: bool
    first_entangle: bool
    second_entangle: bool
    first_can_burn: bool
    second_can_burn: bool

def has(effect: EffectSet, mechanic_id: str) -> bool:
    return mechanic_id in effect.tags

def _has_weapon_tag(fighter: CompiledFighter, mechanic_id: str) -> bool:
    return any(has(weapon, mechanic_id) for weapon in (
        fighter.main_weapon,
        *((fighter.off_hand,) if fighter.off_hand is not None else ()),
        *fighter.extra_attacks,
    ))

def _parry_capacity(fighter: CompiledFighter) -> int:
    """Return the number of parries available in a close-combat phase."""
    effects = fighter.global_effects
    available = sum((
        fighter.main_weapon.parry,
        bool(fighter.off_hand and fighter.off_hand.parry),
        has(fighter.main_weapon, "weapon.double-bladed-sword"),
        effects.parry,
        has(effects, "skill.miniath"),
        has(effects, "skill.axe-master") and any(
            has(weapon, tag)
            for weapon in (fighter.main_weapon, fighter.off_hand or EffectSet())
            for tag in ("weapon.axe", "weapon.dwarf-axe")
        ),
        has(effects, "skill.shield-mastery") and has(effects, "defence.shield"),
    ))
    two_parries = (
        has(effects, "skill.unbeatable-warrior")
        or has(fighter.main_weapon, "weapon.double-bladed-sword")
    )
    return min(2 if two_parries else 1, int(available))

def _claim_criticals(candidate: np.ndarray, rows: np.ndarray, state: CombatState) -> np.ndarray:
    """Allow at most one critical per attacker and close-combat phase."""
    accepted = np.zeros(candidate.size, dtype=bool)
    positions = np.flatnonzero(candidate)
    if positions.size == 0:
        return accepted
    eligible = positions[~state.critical_used[rows[positions]]]
    if eligible.size == 0:
        return accepted
    eligible_values = rows[eligible]
    first = _run_starts(eligible_values)
    accepted[eligible[first]] = True
    state.critical_used[eligible_values[first]] = True
    return accepted

def _critical_wound_threshold(effect: EffectSet, weapon: EffectSet, poison_blocked: bool) -> int:
    """Return the natural To Wound roll that produces a critical hit."""
    if (has(effect, "poison.wolfsbane") and not poison_blocked) or has(effect, "mechanic.body-slam"):
        return 5
    if has(effect, "skill.art-of-silent-death"):
        return 5
    if has(effect, "skill.unarmed-critical-strikes") and has(weapon, "weapon.fist"):
        return 5
    return 6

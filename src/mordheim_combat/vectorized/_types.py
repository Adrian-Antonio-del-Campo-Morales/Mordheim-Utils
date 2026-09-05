"""Vectorized engine: run constants, ledger types, tag predicates
and compile-time helpers shared by every layer."""
from __future__ import annotations

import numpy as np
from dataclasses import dataclass
from mordheim_core.models import CompiledFighter, EffectSet

STANDING, KNOCKED_DOWN, STUNNED, PARALYZED, OUT = range(5)

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
        effects.parry,
        has(effects, "skill.miniath"),
        has(effects, "skill.axe-master") and any(
            has(weapon, tag)
            for weapon in (fighter.main_weapon, fighter.off_hand or EffectSet())
            for tag in ("weapon.axe", "weapon.dwarf-axe")
        ),
        has(effects, "skill.shield-mastery") and has(effects, "defence.shield"),
    ))
    return min(2 if has(effects, "skill.unbeatable-warrior") else 1, int(available))

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

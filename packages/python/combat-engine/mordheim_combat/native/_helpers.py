"""Tag and compile-time decisions shared by the native compile layer and core.

Every helper here is the exact formula the compiled core depends on: the Cython
extension folds these results into scalar flags once per duel instead of
repeating the decisions inside its hot loops.  They live in the native package
because only the native engine still uses them; the modular engine keeps its own
scalar implementations.
"""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import replace
from functools import lru_cache

from mordheim_combat.phases import ignores_unarmed_penalties
from mordheim_core.effects import merge_effects
from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet


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


def _critical_wound_threshold(effect: EffectSet, weapon: EffectSet,
                              poison_blocked: bool) -> int:
    """Return the natural To Wound roll that produces a critical hit."""
    if ((has(effect, "poison.wolfsbane") and not poison_blocked)
            or has(effect, "mechanic.body-slam")):
        return 5
    if has(effect, "skill.art-of-silent-death"):
        return 5
    if has(effect, "skill.unarmed-critical-strikes") and has(weapon, "weapon.fist"):
        return 5
    return 6


def special_save_targets(defender: CompiledFighter,
                         incoming: EffectSet) -> tuple[int, int]:
    ward = defender.global_effects.ward_save
    if defender.global_effects.step_aside:
        ward = min(ward, 4 if has(defender.global_effects, "skill.vampire-reflexes") else 5)
    if defender.global_effects.step_aside and has(defender.global_effects, "skill.elven-agility"):
        ward = min(ward, 4)
    if defender.global_effects.ward_save_mundane_only and has(incoming, "attack.magical"):
        ward = 7
    regeneration = defender.global_effects.regeneration_save
    if (
        defender.global_effects.regeneration_blocked_by_fire and has(incoming, "attack.fire")
        or defender.global_effects.regeneration_blocked_by_blessed and has(incoming, "attack.blessed")
    ):
        regeneration = 7
    return ward, regeneration


@lru_cache(maxsize=1024)
def _compiled_attack_effect(
    attacker: CompiledFighter, defender: CompiledFighter, weapon: EffectSet,
) -> tuple[EffectSet, EffectSet, bool]:
    """Compile immutable weapon/global interactions outside the hot row loop."""
    poison_immune = defender.global_effects.poison_immunity or has(
        defender.global_effects, "poison_immune"
    )
    if poison_immune:
        if weapon == attacker.main_weapon and attacker.main_weapon_without_poison is not None:
            weapon = attacker.main_weapon_without_poison
        elif weapon == attacker.off_hand and attacker.off_hand_without_poison is not None:
            weapon = attacker.off_hand_without_poison
    effect = weapon if has(weapon, "mechanic.body-slam") else merge_effects(
        weapon, attacker.global_effects,
    )
    if has(effect, "mechanic.death-blow") and attacker.characteristics.attacks < 2:
        effect = replace(
            effect,
            hit_modifier=effect.hit_modifier - 1,
            wound_modifier=effect.wound_modifier - 1,
            injury_modifier=effect.injury_modifier - 1,
        )
    unarmed_adjustment = ignores_unarmed_penalties(effect) and has(weapon, "weapon.fist")
    if unarmed_adjustment:
        effect = merge_effects(effect, EffectSet(target_armour_bonus=-1))
    return weapon, effect, unarmed_adjustment


def _can_ignite(attacker: CompiledFighter, defender: CompiledFighter) -> bool:
    """Whether any ordinary attack in this matchup can set the defender on fire."""
    weapons = (
        attacker.main_weapon,
        *((attacker.off_hand,) if attacker.off_hand is not None else ()),
        *attacker.extra_attacks,
    )
    return any(
        _compiled_attack_effect(attacker, defender, weapon)[1].ignition_threshold <= 6
        for weapon in weapons
    )


def _optional_phase_plan(first: CompiledFighter,
                         second: CompiledFighter) -> OptionalPhasePlan:
    """Compile optional round phases once instead of probing them for every round."""
    return OptionalPhasePlan(
        first_force_of_will=has(first.global_effects, "mechanic.force-of-will"),
        second_force_of_will=has(second.global_effects, "mechanic.force-of-will"),
        first_spines=has(first.global_effects, "spines"),
        second_spines=has(second.global_effects, "spines"),
        first_netter=has(first.global_effects, "mechanic.netter"),
        second_netter=has(second.global_effects, "mechanic.netter"),
        first_black_hunger=has(first.global_effects, "mechanic.black-hunger"),
        second_black_hunger=has(second.global_effects, "mechanic.black-hunger"),
        first_entangle=_has_weapon_tag(first, "weapon.chained-squig"),
        second_entangle=_has_weapon_tag(second, "weapon.chained-squig"),
        first_can_burn=_can_ignite(second, first),
        second_can_burn=_can_ignite(first, second),
    )

"""Primitive, immutable boundary consumed by optimized combat backends."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import fields
from typing import Collection

from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet
from mordheim_core.models import DuelContext
from mordheim_core.context import PreparedDuelContext, prepare_duel_context


EFFECT_VALUE_FIELDS = tuple(field.name for field in fields(EffectSet) if field.name != "tags")


@dataclass(frozen=True, slots=True)
class EffectKernelPlan:
    tag_mask: int
    values: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class FighterKernelPlan:
    characteristics: tuple[int, int, int, int, int, int]
    global_effects: EffectKernelPlan
    main_weapon: EffectKernelPlan
    off_hand: EffectKernelPlan | None
    extra_attacks: tuple[EffectKernelPlan, ...]
    armour_save: int
    natural_armour_save: int
    natural_armour_worst_save: int
    helmet_save: int
    injury_profile: int
    ballistic_skill: int
    off_hand_attacks: bool
    mounted: bool
    movement: int | None = None
    leadership: int | None = None


@dataclass(frozen=True, slots=True)
class DuelKernelPlan:
    version: int
    tag_ids: tuple[str, ...]
    first: FighterKernelPlan
    second: FighterKernelPlan
    optimization_eligible: bool
    context: PreparedDuelContext | None = None


def _effects(fighter: CompiledFighter) -> tuple[EffectSet, ...]:
    return (
        fighter.global_effects, fighter.main_weapon,
        *((fighter.off_hand,) if fighter.off_hand is not None else ()),
        *fighter.extra_attacks,
    )


def _effect_plan(effect: EffectSet, tag_indices: dict[str, int]) -> EffectKernelPlan:
    mask = 0
    for tag in effect.tags:
        mask |= 1 << tag_indices[tag]
    return EffectKernelPlan(
        mask,
        tuple(int(getattr(effect, name)) for name in EFFECT_VALUE_FIELDS),
    )


def _fighter_plan(fighter: CompiledFighter, tag_indices: dict[str, int]) -> FighterKernelPlan:
    stats = fighter.characteristics
    return FighterKernelPlan(
        characteristics=(
            stats.weapon_skill, stats.strength, stats.toughness,
            stats.wounds, stats.initiative, stats.attacks,
        ),
        global_effects=_effect_plan(fighter.global_effects, tag_indices),
        main_weapon=_effect_plan(fighter.main_weapon, tag_indices),
        off_hand=(
            _effect_plan(fighter.off_hand, tag_indices)
            if fighter.off_hand is not None else None
        ),
        extra_attacks=tuple(_effect_plan(effect, tag_indices) for effect in fighter.extra_attacks),
        armour_save=fighter.armour_save,
        natural_armour_save=fighter.natural_armour_save,
        natural_armour_worst_save=fighter.natural_armour_worst_save,
        helmet_save=fighter.helmet_save,
        injury_profile=fighter.injury_profile,
        ballistic_skill=fighter.ballistic_skill,
        off_hand_attacks=fighter.off_hand_attacks,
        mounted=fighter.mounted,
        movement=stats.movement, leadership=stats.leadership,
    )


def require_optimized_support(first: CompiledFighter, second: CompiledFighter) -> None:
    """Refuse modular-only choices before an optimized engine can omit them."""
    if any(fighter.vomit_attack is not None for fighter in (first, second)):
        raise ValueError("optional Vomit Attack currently requires the modular engine; optimized ports are pending")
    if any("trait.spectral-touch" in effect.tags
           for fighter in (first, second) for effect in _effects(fighter)):
        raise ValueError("Spectral Touch currently requires the modular engine; optimized ports are pending")
    if any("skill.shifty" in effect.tags
           for fighter in (first, second) for effect in _effects(fighter)):
        raise ValueError("Shifty currently requires the modular engine; optimized ports are pending")
    if any("mechanic.killing-blow" in effect.tags
           for fighter in (first, second) for effect in _effects(fighter)):
        raise ValueError("Killing Blow currently requires the modular engine; optimized ports are pending")
    if any(set(effect.tags) & {"weapon.pry-bar", "weapon.kanabo", "weapon.wizards-staff", "weapon.katana", "weapon.shock-rod", "weapon.skull-busta", "weapon.long-daggers", "weapon.knuckledusters"}
           for fighter in (first, second) for effect in _effects(fighter)):
        raise ValueError("L06 weapon profiles currently require the modular engine; optimized ports are pending")


def compile_duel_plan(
    first: CompiledFighter, second: CompiledFighter,
    *, certified_tags: Collection[str] | None = None,
    context: DuelContext | None = None,
) -> DuelKernelPlan:
    require_optimized_support(first, second)
    tag_ids = tuple(sorted({tag for fighter in (first, second) for effect in _effects(fighter)
                            for tag in effect.tags}))
    indices = {tag: index for index, tag in enumerate(tag_ids)}
    eligible = certified_tags is None or set(tag_ids) <= set(certified_tags)
    return DuelKernelPlan(
        1, tag_ids, _fighter_plan(first, indices), _fighter_plan(second, indices), eligible,
        prepare_duel_context(first, second, context),
    )

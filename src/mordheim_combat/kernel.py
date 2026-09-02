"""Primitive, immutable boundary consumed by optimized combat backends."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import fields
from typing import Collection

from mordheim_core.models import CompiledFighter
from mordheim_core.models import EffectSet


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


@dataclass(frozen=True, slots=True)
class DuelKernelPlan:
    version: int
    tag_ids: tuple[str, ...]
    first: FighterKernelPlan
    second: FighterKernelPlan
    optimization_eligible: bool


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
    )


def compile_duel_plan(
    first: CompiledFighter, second: CompiledFighter,
    *, certified_tags: Collection[str] | None = None,
) -> DuelKernelPlan:
    tag_ids = tuple(sorted({tag for fighter in (first, second) for effect in _effects(fighter)
                            for tag in effect.tags}))
    indices = {tag: index for index, tag in enumerate(tag_ids)}
    eligible = certified_tags is None or set(tag_ids) <= set(certified_tags)
    return DuelKernelPlan(
        1, tag_ids, _fighter_plan(first, indices), _fighter_plan(second, indices), eligible,
    )

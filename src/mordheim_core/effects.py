"""domain.effects: responsibility extracted without altering the rules."""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import fields
from mordheim_core.models import EffectSet


@dataclass(frozen=True, slots=True)
class ExecutionEffect:
    """A single, data-defined effect and the context in which it is applied."""
    effect: EffectSet
    trigger: str
    application: str
    stacking: str


def merge_effects(left: EffectSet, right: EffectSet) -> EffectSet:
    values = {}
    for field in fields(EffectSet):
        a, b = getattr(left, field.name), getattr(right, field.name)
        if field.name == "tags": values[field.name] = tuple(dict.fromkeys((*a,*b)))
        elif isinstance(a, bool): values[field.name] = a or b
        elif field.name in {"ward_save","regeneration_save","maximum_wound_target","armour_save_floor","ignition_threshold","caught_fire_threshold"}: values[field.name] = min(a, b)
        elif field.name in {"damage","damage_die_sides","out_of_action_threshold"}: values[field.name] = max(a, b)
        elif field.name == "priority":
            # Zero is the neutral value.  A plain material/global effect must
            # not erase a weapon's Strike Last modifier, while an explicit
            # Strike First effect still takes precedence when both exist.
            values[field.name] = b if a == 0 else a if b == 0 else max(a, b)
        else: values[field.name] = a + b
    return EffectSet(**values)


def merge_best_effects(left: EffectSet, right: EffectSet) -> EffectSet:
    """Keep the best independent value for a non-stacking effect."""
    values = {}
    for field in fields(EffectSet):
        a, b = getattr(left, field.name), getattr(right, field.name)
        if field.name == "tags": values[field.name] = tuple(dict.fromkeys((*a, *b)))
        elif isinstance(a, bool): values[field.name] = a or b
        elif field.name in {"ward_save", "regeneration_save", "maximum_wound_target", "armour_save_floor", "incoming_strength_modifier", "armour_strength_modifier", "ignition_threshold", "caught_fire_threshold"}:
            values[field.name] = min(a, b)
        elif field.name == "priority":
            values[field.name] = b if a == 0 else a if b == 0 else max(a, b)
        else: values[field.name] = max(a, b)
    return EffectSet(**values)


def apply_execution_effects(base: EffectSet, effect_ids, effects: Mapping[str, ExecutionEffect],
                            trigger: str, application: str) -> EffectSet:
    """Apply only effects declared for one executable runtime context."""
    result = base
    applied_once: set[str] = set()
    for effect_id in effect_ids:
        definition = effects[effect_id]
        if definition.trigger != trigger or definition.application != application:
            continue
        if definition.stacking == "once" and effect_id in applied_once:
            continue
        result = merge_best_effects(result, definition.effect) if definition.stacking == "best" else merge_effects(result, definition.effect)
        if definition.stacking == "once":
            applied_once.add(effect_id)
    return result

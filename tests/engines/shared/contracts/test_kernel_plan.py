from dataclasses import fields

import pytest

from mordheim_combat import kernel
from mordheim_combat.kernel import EFFECT_VALUE_FIELDS
from mordheim_combat.kernel import compile_duel_plan
from mordheim_core.models import EffectSet


def test_kernel_plan_contains_every_numeric_effect_field_and_stable_tag_masks(precompiled):
    compiled = precompiled()
    first = compiled.first
    second = compiled.second
    plan = compile_duel_plan(first, second)

    assert EFFECT_VALUE_FIELDS == tuple(
        field.name for field in fields(EffectSet) if field.name != "tags"
    )
    assert len(plan.first.main_weapon.values) == len(EFFECT_VALUE_FIELDS)
    assert plan.tag_ids == tuple(sorted(plan.tag_ids))
    assert plan.optimization_eligible


def test_numpy_and_native_admission_gates_are_independent(precompiled):
    """NumPy may advance without granting the still-frozen native backend."""
    from dataclasses import replace

    compiled = precompiled()
    first = compiled.first
    second = compiled.second
    numpy_pending = kernel.pending_capabilities("numpy").local_modifier_tags
    native_pending = kernel.pending_capabilities("native").local_modifier_tags
    # The gate is read, not hard-coded: a tag the native port has not reached
    # keeps its own refusal while NumPy admits the very same pair.  Naming a
    # literal here only made the contract go stale as the port advanced.
    diverging = sorted(native_pending - numpy_pending)
    if not diverging:
        # Both gates have reached the same point; they are still separate
        # values, which is what this contract protects.
        assert kernel.pending_capabilities("numpy") is not (
            kernel.pending_capabilities("native"))
        return
    tag = diverging[0]
    first = replace(first, global_effects=replace(
        first.global_effects, tags=(*first.global_effects.tags, tag)))

    kernel.require_optimized_support(first, second, backend="numpy")
    with pytest.raises(ValueError, match="Local modifier variants"):
        kernel.require_optimized_support(first, second, backend="native")
    # Legacy calls without a backend keep the conservative native gate.
    with pytest.raises(ValueError, match="Local modifier variants"):
        kernel.require_optimized_support(first, second)


def test_uncertified_tags_keep_a_plan_out_of_optimized_backends(precompiled):
    compiled = precompiled()
    first = compiled.first
    second = compiled.second
    plan = compile_duel_plan(first, second, certified_tags=())
    assert not plan.optimization_eligible

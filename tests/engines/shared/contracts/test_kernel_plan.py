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
    compiled = precompiled()
    first = compiled.first
    second = compiled.second
    # ``mechanic.magical-void`` is now a real NumPy port, so its own gate has
    # already dropped it while the native gate still holds it back. The
    # independence this test guards is therefore observable directly, with no
    # need to simulate the port by patching the pending table.
    assert "mechanic.magical-void" in kernel.NUMPY_CONNECTED_TAGS
    assert "mechanic.magical-void" not in kernel.pending_capabilities(
        "numpy").local_modifier_tags
    assert "mechanic.magical-void" in kernel.pending_capabilities(
        "native").local_modifier_tags

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

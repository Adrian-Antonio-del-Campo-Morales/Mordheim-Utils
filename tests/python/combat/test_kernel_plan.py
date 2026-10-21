from dataclasses import fields
from dataclasses import replace

import pytest

from mordheim_combat import kernel
from mordheim_combat.kernel import EFFECT_VALUE_FIELDS
from mordheim_combat.kernel import compile_duel_plan
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import EffectSet
from mordheim_core.models import FighterBuild


def fighter(**changes):
    values = {"ruleset": "mordheim", "characteristics": Characteristics(3, 3, 3, 1, 3, 1)}
    values.update(changes)
    return compile_fighter(FighterBuild(**values))


@pytest.mark.phase5_vectorized
def test_kernel_plan_contains_every_numeric_effect_field_and_stable_tag_masks():
    first = fighter(main_weapon_id="weapon.sword", off_hand_id="weapon.dagger")
    second = fighter(skill_ids=("skill.regeneration",))
    plan = compile_duel_plan(first, second)

    assert EFFECT_VALUE_FIELDS == tuple(
        field.name for field in fields(EffectSet) if field.name != "tags"
    )
    assert len(plan.first.main_weapon.values) == len(EFFECT_VALUE_FIELDS)
    assert plan.tag_ids == tuple(sorted(plan.tag_ids))
    assert plan.optimization_eligible


@pytest.mark.phase5_vectorized
def test_numpy_and_native_admission_gates_are_independent(monkeypatch):
    """NumPy may advance without granting the still-frozen native backend."""
    first = fighter(skill_ids=("mechanic.magical-void",))
    second = fighter()
    pending = kernel.pending_capabilities("numpy")
    assert "mechanic.magical-void" in pending.local_modifier_tags

    # A NumPy port drops the behavior from its own gate only.
    monkeypatch.setitem(kernel._PENDING, "numpy", replace(
        pending,
        local_modifier_tags=pending.local_modifier_tags - {"mechanic.magical-void"},
    ))
    kernel.require_optimized_support(first, second, backend="numpy")
    with pytest.raises(ValueError, match="Local modifier variants"):
        kernel.require_optimized_support(first, second, backend="native")
    # Legacy calls without a backend keep the conservative native gate.
    with pytest.raises(ValueError, match="Local modifier variants"):
        kernel.require_optimized_support(first, second)


@pytest.mark.phase5_vectorized
def test_uncertified_tags_keep_a_plan_out_of_optimized_backends():
    first = fighter(main_weapon_id="weapon.sword")
    second = fighter()
    plan = compile_duel_plan(first, second, certified_tags=())
    assert not plan.optimization_eligible

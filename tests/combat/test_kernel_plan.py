from dataclasses import fields

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


def test_uncertified_tags_keep_a_plan_out_of_optimized_backends():
    first = fighter(main_weapon_id="weapon.sword")
    second = fighter()
    plan = compile_duel_plan(first, second, certified_tags=())
    assert not plan.optimization_eligible

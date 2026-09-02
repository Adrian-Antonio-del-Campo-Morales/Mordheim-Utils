"""Fallos deliberados limitados a una ejecución y restaurados incluso al fallar."""
from contextlib import contextmanager, ExitStack
from dataclasses import replace

from mordheim_combat_lab.combat.modular import attacks, pools, aftermath, contexts, state, rounds
from mordheim_combat_lab.construction import compiler, selection, restrictions


@contextmanager
def runtime_fault(fault: str):
    from unittest.mock import patch

    if fault not in {"retain-critical-allowance", "retain-parry-capacity", "retain-consumable",
                     "retain-lucky-charm", "suppress-skill-access-grant", "suppress-bound-equipment-restrictions", "suppress-category-prohibitions",
                     "suppress-required-initial-choices", "suppress-possessed-mutation-limit",
                     "suppress-special-rule-access", "suppress-profile-restrictions",
                     "suppress-profile-declared-strength-access"}:
        raise ValueError(f"unknown isolated runtime mutation {fault}")
    with ExitStack() as stack:
        if fault == "suppress-required-initial-choices":
            stack.enter_context(patch.object(restrictions, "_validate_required_initial_choices",
                                            lambda *args, **kwargs: None))
        elif fault == "suppress-possessed-mutation-limit":
            stack.enter_context(patch.object(restrictions, "_validate_possessed_mutation_limit",
                                            lambda *args, **kwargs: None))
        elif fault == "suppress-special-rule-access":
            from mordheim_combat_lab.verification import scenarios
            stack.enter_context(patch.object(scenarios, "available_special_rules",
                                            lambda *args, **kwargs: ()))
        elif fault == "suppress-profile-restrictions":
            for consumer in (restrictions, compiler):
                stack.enter_context(patch.object(consumer, "_validate_profile_selections",
                                                lambda *args, **kwargs: None))
        elif fault == "suppress-profile-declared-strength-access":
            original_profile = compiler._profile
            original_bindings = compiler.runtime_bindings

            def omit_strength(*args, **kwargs):
                characteristics, traits, package, profile, random = original_profile(*args, **kwargs)
                if profile is not None:
                    profile = {**profile, "skill_access": [
                        category for category in profile.get("skill_access", ())
                        if category != "strength"
                    ]}
                return characteristics, traits, package, profile, random

            stack.enter_context(patch.object(compiler, "_profile", omit_strength))
            stack.enter_context(patch.object(compiler, "runtime_bindings", lambda *args, **kwargs: tuple(
                binding for binding in original_bindings(*args, **kwargs)
                if not (binding.get("id") == "profile.skill-access"
                        and (binding.get("parameters") or {}).get("category") == "strength")
            )))
        elif fault == "suppress-category-prohibitions":
            stack.enter_context(patch.object(restrictions, "_validate_category_prohibitions",
                                            lambda *args, **kwargs: None))
        elif fault == "suppress-bound-equipment-restrictions":
            stack.enter_context(patch.object(restrictions, "_validate_bound_equipment_restrictions",
                                            lambda *args, **kwargs: None))
        elif fault == "suppress-skill-access-grant":
            original = compiler.runtime_bindings

            def omit_skill_access(*args, **kwargs):
                return tuple(
                    {**binding, "parameters": {"category": "combat"}}
                    if binding.get("id") == "profile.skill-access" else binding
                    for binding in original(*args, **kwargs)
                )

            for consumer in (compiler, selection, restrictions):
                if hasattr(consumer, "runtime_bindings"):
                    stack.enter_context(patch.object(consumer, "runtime_bindings", omit_skill_access))
        elif fault == "retain-consumable":
            stack.enter_context(patch.object(state.FighterState, "spend", lambda value, resource: value))
        else:
            def faulty_replace(value, **changes):
                if isinstance(value, state.FighterState):
                    if fault == "retain-critical-allowance" and changes.get("critical_available") is False:
                        changes.pop("critical_available")
                    if (fault == "retain-parry-capacity" and "parries_remaining" in changes
                            and changes["parries_remaining"] < value.parries_remaining):
                        changes.pop("parries_remaining")
                    if fault == "retain-lucky-charm" and changes.get("lucky_charm") is False:
                        changes.pop("lucky_charm")
                return replace(value, **changes)

            for consumer in (attacks, pools, aftermath, contexts, state, rounds):
                if hasattr(consumer, "replace"):
                    stack.enter_context(patch.object(consumer, "replace", faulty_replace))
        yield

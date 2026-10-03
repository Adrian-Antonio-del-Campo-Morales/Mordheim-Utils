"""Compatibility entry points for the single shared eligibility implementation."""
from __future__ import annotations

from mordheim_construction.eligibility import validate


def _validate_bound_equipment_restrictions(build, main_weapon_id, profile_bindings, root=None, *, package=None, profile=None):
    validate("boundEquipment", build, root, main_weapon_id=main_weapon_id,
             profile_bindings=profile_bindings, package=package, profile=profile)


def _validate_category_prohibitions(build, main_weapon_id, compiler_contracts, compiler_bindings):
    validate("categoryProhibitions", build, main_weapon_id=main_weapon_id,
             compiler_contracts=compiler_contracts, compiler_bindings=compiler_bindings)


def _validate_required_initial_choices(build, compiler_contracts):
    validate("requiredInitial", build, compiler_contracts=compiler_contracts)


def _validate_possessed_mutation_limit(build, compiler_contracts):
    # Keep the verification mutation seam; the shared module counts actual choices.
    validate("mutationLimit", build, compiler_contracts=compiler_contracts)


def _validate_profile_selections(build, package, profile, root, main_weapon_id,
                                 profile_bindings=(), compiler_contracts=(), compiler_bindings=()):
    _validate_bound_equipment_restrictions(build, main_weapon_id, profile_bindings, root, package=package, profile=profile)
    _validate_category_prohibitions(build, main_weapon_id, compiler_contracts, compiler_bindings)
    args = dict(package=package, profile=profile, main_weapon_id=main_weapon_id,
                profile_bindings=profile_bindings, compiler_contracts=compiler_contracts,
                compiler_bindings=compiler_bindings)
    validate("profileSelections", build, root, **args)
    _validate_required_initial_choices(build, compiler_contracts)
    validate("initialChoices", build, root, **args)
    _validate_possessed_mutation_limit(build, compiler_contracts)
    validate("profileTail", build, root, **args)

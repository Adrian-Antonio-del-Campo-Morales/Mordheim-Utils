"""Supplied profile states whose equipment access changes with that state."""
from dataclasses import replace


def prepare_source_profile(build, characteristics, traits, package, profile,
                           random_characteristics):
    """Apply Condemned's printed Fate without simulating experience advances."""
    fixed = build.trait_overrides.get("condemned_fixed_characteristics", [])
    native = (build.collection == "mordheim"
              and build.band_id == "marauders-of-chaos"
              and build.profile_id == "condemned")
    if not isinstance(fixed, list) or any(key not in ("WS", "S", "T", "A") for key in fixed):
        raise ValueError("Condemned fixed characteristics must be a list of WS, S, T or A")
    if len(fixed) != len(set(fixed)):
        raise ValueError("Condemned fixed characteristics must be distinct")
    if fixed and not native:
        raise ValueError("Only the Condemned has permanently fixed variable characteristics")
    if not native:
        return build, characteristics, traits, package, profile, random_characteristics
    if fixed and build.characteristics is None:
        raise ValueError("Supply the Condemned's permanently fixed characteristic values")
    random_characteristics = tuple(row for row in random_characteristics if row[0] not in fixed)
    if len(fixed) < 4:
        if (build.main_weapon_id not in {"weapon.dagger", "weapon.fist", "weapon.natural-attacks"}
                or build.off_hand_id or build.extra_hand_id or build.defence_ids
                or build.armour_id != "armour.no-armour"
                or build.main_material_id != "material.normal"
                or build.main_poison_id or build.off_poison_id or build.preparation_ids):
            raise ValueError("The Condemned uses no equipment while a characteristic remains variable")
        # The build's default dagger represents no explicit weapon selection.
        # Fate grants penalty-free unarmed blows; possession of idle items is
        # not a printed prohibition and does not erase the carried inventory.
        build = replace(build, main_weapon_id="weapon.natural-attacks")
    return build, characteristics, traits, package, profile, random_characteristics

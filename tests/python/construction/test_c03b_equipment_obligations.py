"""Printed C03b equipment obligations, using canonical construction."""
import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import FighterBuild


def test_fog_fragments_require_a_censer_only_when_carried():
    def build(items, weapon="weapon.dagger"):
        return FighterBuild("mordheim", collection="trollheim",
                            band_id="lustria-clan-pestilens", profile_id="plague-priest",
                            main_weapon_id=weapon, owned_item_ids=items)

    assert compile_fighter(build(()))
    with pytest.raises(ValueError, match="weapon.censer"):
        compile_fighter(build(("fog_warpstone_fragments",)))
    # The requirement is possession, not an obligation to attack with the censer.
    assert compile_fighter(build(("fog_warpstone_fragments", "censer")))
    assert compile_fighter(build(("fog_warpstone_fragments",), "weapon.censer"))


def test_starting_leader_must_carry_the_headdress_without_obliging_other_profiles():
    def build(profile, items=()):
        return FighterBuild("mordheim", collection="trollheim",
                            band_id="lustria-savage-goblins", profile_id=profile,
                            main_weapon_id="weapon.dagger", owned_item_ids=items)

    with pytest.raises(ValueError, match="feather_headdress"):
        compile_fighter(build("witch-doctor"))
    assert compile_fighter(build("witch-doctor", ("feather_headdress",)))
    assert compile_fighter(build("big-boss"))

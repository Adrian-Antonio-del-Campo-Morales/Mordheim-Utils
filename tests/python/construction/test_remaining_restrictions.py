"""C03c construction restrictions, separate from excluded item producers."""
import pytest

from mordheim_construction.compiler import compile_fighter
from mordheim_construction.eligibility import call, desktop_call
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands


pytestmark = pytest.mark.eligibility


def test_kumfy_gear_rejects_both_forbidden_combinations_in_owned_and_active_equipment():
    def build(items, armour="armour.no-armour"):
        return FighterBuild("mordheim", band_id="savage-orcs-kaz", profile_id="boss",
                            main_weapon_id="weapon.club", owned_item_ids=items,
                            armour_id=armour)

    assert compile_fighter(build(("kumfy_gear",)))
    for forbidden in ("warpaint", "light_armour"):
        with pytest.raises(ValueError, match="cannot be combined"):
            compile_fighter(build(("kumfy_gear", forbidden)))
        assert compile_fighter(build((forbidden,)))
    with pytest.raises(ValueError, match="cannot be combined"):
        compile_fighter(build(("kumfy_gear",), "armour.light-armour"))
    assert compile_fighter(build((), "armour.light-armour"))


def test_hunting_bird_requires_the_declared_falconer_capability():
    pack = next(p for p in load_bands("mordheim") if p.band["id"] == "watchmen-mim")
    sergeant = next(p for p in pack.profiles if p["id"] == "sergeants")
    captain = next(p for p in pack.profiles if p["id"] == "watch-captain")
    for profile, allowed in ((sergeant, True), ({**sergeant, "rule_ids": []}, False),
                             (captain, False)):
        build = FighterBuild("mordheim", band_id="watchmen-mim", profile_id=profile["id"])
        facts = desktop_call("profileFacts", build, package=pack, profile=profile)
        assert ("hunting_bird" in {e["item_id"] for e in facts["equipment_access"]}) == allowed
        issue = call("equipmentIssue", {"profile": facts, "item_id": "hunting_bird",
                                       "item": {"id": "hunting_bird", "kind": "miscellaneous"}})
        assert (issue is None) == allowed

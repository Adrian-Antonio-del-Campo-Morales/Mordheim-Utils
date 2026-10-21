"""C03c: printed special-list access and supplied construction phase."""
import pytest

from mordheim_construction.eligibility import call, desktop_call, package_facts
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import load_bands

pytestmark = pytest.mark.eligibility


def package(band):
    return next(pack for pack in load_bands("mordheim") if pack.band["id"] == band)


def test_high_elven_special_list_reaches_the_high_elf_bearers_and_direct_selection():
    pack = package("high-elves-lus")
    catalogue = {"packages": {}, "foreign_packages": {}, "mechanics": {},
                 "mappings": {}, "skills": {}, "items": {}}
    for profile in pack.profiles:
        facts = call("profileFacts", package_facts(pack), profile, None, catalogue)
        offered = {entry["item_id"] for entry in facts["equipment_access"]}
        assert {"elven_wine", "elven_cloak"} <= offered, profile["id"]
        issue = call("equipmentIssue", {"profile": facts, "item_id": "elven_wine",
                                       "item": {"id": "elven_wine", "kind": "miscellaneous"}})
        assert issue is None, (profile["id"], issue)


def test_runestones_allow_starting_heroes_but_only_weaver_after_creation():
    pack = package("shadow-warriors")
    for phase, allowed in (((), {"shadow-master", "shadow-walker", "shadow-weaver"}),
                           (("equipment.post-creation",), {"shadow-weaver"})):
        for profile in pack.profiles:
            build = FighterBuild("mordheim", band_id="shadow-warriors",
                                 profile_id=profile["id"], variant_ids=phase)
            facts = desktop_call("profileFacts", build, package=pack, profile=profile)
            offers = {entry["item_id"] for entry in facts["equipment_access"]}
            assert ("elven_runestones" in offers) == (profile["id"] in allowed)
            issue = call("equipmentIssue", {"profile": facts, "item_id": "elven_runestones",
                         "item": {"id": "elven_runestones", "kind": "miscellaneous"}})
            assert (issue is None) == (profile["id"] in allowed), (profile["id"], phase, issue)

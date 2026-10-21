"""The construction contract of the Clockworkers constructs.

Every expectation is a printed line of the canonical band package read live
through the shared module: the slot capacities and the in-built clause of
``profiles.yaml``, the per-piece slot costs and the named recipients of
``equipment-access.yaml`` and the ``profile.equipment-restrictions`` binding of
``special-rules.yaml``.  The block had no discriminator at all, so this file
covers only the boundaries the package names: slots and their per-piece costs,
the single armour slot, and the named recipients of the offer *and* of a direct
selection.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from mordheim_construction.eligibility import configuration_context, construction_call, desktop_call
from mordheim_core.models import FighterBuild
from mordheim_knowledge.loader import knowledge_root, load_bands

pytestmark = pytest.mark.phase2_construction

ROOT = knowledge_root()
PACKAGES = {str(pack.band["id"]): pack for collection in ("mordheim", "trollheim")
            for pack in load_bands(collection, Path(ROOT))}
BAND = "clockworkers-sc"


def row(profile_id: str) -> dict:
    """The canonical profile row of the loaded package, never a synthetic one."""
    return next(profile for profile in PACKAGES[BAND].profiles if str(profile["id"]) == profile_id)


def build(profile_id: str) -> FighterBuild:
    return FighterBuild("mordheim", band_id=BAND, profile_id=profile_id)


def codes(profile_id: str, possession: tuple[str, ...]) -> set[str]:
    """Construction verdicts of one complete supplied kit."""
    profile = row(profile_id)
    context = configuration_context(build(profile_id), PACKAGES[BAND], profile,
                                    possession=possession, slots={"main_weapon_id": "weapon.fist"})
    return {str(issue["code"])
            for issue in construction_call("validateConstruction", build(profile_id), context, root=ROOT)}


def offers(profile_id: str) -> set[str]:
    facts = desktop_call("profileFacts", build(profile_id), ROOT,
                         package=PACKAGES[BAND], profile=row(profile_id))
    return {str(offer["item_id"]) for offer in facts["equipment_access"] or ()}


def test_the_soldier_counts_two_equipment_slots_and_the_fiend_four():
    assert "equipment_limit_exceeded" not in codes("clockwork-soldiers", ("hammer", "shield"))
    assert "equipment_limit_exceeded" in codes("clockwork-soldiers", ("hammer", "mace", "shield"))
    # The printed clause replaces the normal weapon maximums with slots: four
    # one-handed weapons fill the fiend's four slots without a hands refusal.
    assert "equipment_limit_exceeded" not in codes("clockwork-fiend", ("hammer", "mace", "axe", "sword"))
    assert "equipment_limit_exceeded" in codes("clockwork-fiend", ("hammer", "mace", "axe", "sword", "shield"))


def test_a_two_slot_piece_costs_two_of_the_printed_slots():
    # The clockwork rifle and the double-handed weapon are two slots each.
    assert "equipment_limit_exceeded" in codes("clockwork-soldiers", ("clockwork_rifle", "great_weapon"))
    assert "equipment_limit_exceeded" not in codes("clockwork-fiend", ("clockwork_rifle", "great_weapon"))
    # A second two-slot piece no longer fits a four-slot construct.
    assert "equipment_limit_exceeded" in codes("clockwork-fiend", ("clockwork_rifle", "great_weapon", "shield"))


def test_the_single_armour_slot_is_separate_from_the_equipment_slots():
    for profile_id in ("clockwork-soldiers", "clockwork-fiend"):
        assert "equipment_limit_exceeded" in codes(profile_id, ("light_armour", "heavy_armour"))
    assert "equipment_limit_exceeded" not in codes("clockwork-soldiers", ("light_armour", "hammer", "shield"))


RECIPIENT_LINES = ("clockwork_rifle", "heavy_armour")
RECIPIENTS = ("master-of-clocks", "dwarf-engineer")
PEERS = ("metallurgist", "apprentices", "handymen")


def test_a_named_line_reaches_its_recipients_and_no_peer_of_the_same_list():
    for item_id in RECIPIENT_LINES:
        for profile_id in RECIPIENTS:
            assert item_id in offers(profile_id), (item_id, profile_id)
        for profile_id in PEERS:
            assert item_id not in offers(profile_id), (item_id, profile_id)


def test_the_same_restriction_refuses_a_direct_selection():
    for item_id in RECIPIENT_LINES:
        for profile_id in RECIPIENTS:
            assert "equipment_not_permitted" not in codes(profile_id, (item_id,)), (item_id, profile_id)
        for profile_id in PEERS:
            assert "equipment_not_permitted" in codes(profile_id, (item_id,)), (item_id, profile_id)


def test_a_legal_construct_kit_configures_and_compiles():
    from mordheim_combat import phases
    from mordheim_combat.modular.state import initialize_fighter
    from mordheim_construction.compiler import compile_fighter
    from mordheim_core.dice import ScriptedDice

    assert codes("clockwork-fiend", ("hammer", "shield", "light_armour")) == set()
    fighter = compile_fighter(FighterBuild("mordheim", band_id=BAND, profile_id="clockwork-fiend",
                                           main_weapon_id="weapon.mace", off_hand_id="defence.shield",
                                           armour_id="armour.light-armour"))
    state = initialize_fighter(fighter, ScriptedDice({}), "init")
    assert state.condition == phases.Condition.STANDING and state.active

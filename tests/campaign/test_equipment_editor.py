"""Per-warrior equipment editor: roster/stash reassignment at any moment.

The moves are legal outside the post-battle sequence (tabletop equipment
reallocation), keep the warband total constant (no buy/sell), and keep the
inventory ledger counters (owned/equipped/stash) consistent.
"""
from __future__ import annotations

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.domain.models import EquipmentEntryVM, WarriorVM
from mordheim_campaign.domain.builders import make_example_state
from mordheim_campaign.ui.equipment_display import equipment_quantity_suffix


def _controller() -> AppController:
    controller = AppController()
    controller.replace_state(make_example_state(controller.port))
    return controller


def test_assign_and_return_round_trip_keeps_ledger_consistent():
    controller = _controller()
    campaign = controller.state.campaign
    herbs = next(item for item in campaign.inventory if item.stash > 0)
    warrior = campaign.warriors[0]
    before = (herbs.owned, herbs.equipped, herbs.stash)

    ok, message = controller.assign_stash_item(herbs.id, warrior.id)
    assert ok, message
    assert any(entry.item_id == herbs.id for entry in warrior.equipment)
    assert (herbs.owned, herbs.equipped, herbs.stash) == (before[0], before[1] + 1, before[2] - 1)

    ok, message = controller.return_equipped_item(herbs.id, warrior.id)
    assert ok, message
    assert all(entry.item_id != herbs.id for entry in warrior.equipment)
    assert (herbs.owned, herbs.equipped, herbs.stash) == before


def test_return_rejects_items_the_warrior_does_not_carry():
    controller = _controller()
    campaign = controller.state.campaign
    herbs = next(item for item in campaign.inventory if item.stash > 0)
    warrior = campaign.warriors[0]
    ok, message = controller.return_equipped_item(herbs.id, warrior.id)
    assert not ok and "does not carry" in message


def test_assign_rejects_when_stash_is_empty():
    controller = _controller()
    campaign = controller.state.campaign
    item = next(row for row in campaign.inventory if row.stash > 0)
    item.stash = 0
    ok, message = controller.assign_stash_item(item.id, campaign.warriors[0].id)
    assert not ok and "stash" in message


def test_moves_work_without_a_pending_post_battle():
    controller = _controller()
    # Post-battle #8 is pending in the example; mark it complete so no
    # sequence is active — the editor must still work.
    controller.state.campaign.post_battle(8).complete = True
    campaign = controller.state.campaign
    assert campaign.pending_post_battle is None
    item = next(row for row in campaign.inventory if row.stash > 0)
    ok, _ = controller.assign_stash_item(item.id, campaign.warriors[0].id)
    assert ok
    ok, _ = controller.return_equipped_item(item.id, campaign.warriors[0].id)
    assert ok


def test_moves_survive_save_load(tmp_path):
    from mordheim_campaign.persistence import load_campaign, save_campaign

    controller = _controller()
    campaign = controller.state.campaign
    item = next(row for row in campaign.inventory if row.stash > 0)
    warrior = campaign.warriors[0]
    controller.assign_stash_item(item.id, warrior.id)
    reloaded = load_campaign(save_campaign(tmp_path / "eq.mordheim", controller.state))
    warrior2 = next(w for w in reloaded.campaign.warriors if w.id == warrior.id)
    item2 = next(row for row in reloaded.campaign.inventory if row.id == item.id)
    assert any(entry.item_id == item.id for entry in warrior2.equipment)
    assert item2.equipped == item.equipped and item2.stash == item.stash


def test_henchman_group_carries_equipment_as_a_group():
    controller = _controller()
    campaign = controller.state.campaign
    group = next(w for w in campaign.warriors if w.quantity > 1)
    item = next(row for row in campaign.inventory if row.stash > 0)
    item.owned += max(0, group.quantity - item.stash)
    item.stash = group.quantity
    ok, message = controller.assign_stash_item(item.id, group.id)
    assert ok, message
    assert any(entry.item_id == item.id and entry.quantity == group.quantity for entry in group.equipment)
    assert item.stash == 0

    ok, message = controller.return_equipped_item(item.id, group.id)
    assert ok, message
    assert item.stash == group.quantity


def test_henchman_equipment_display_uses_copies_per_member():
    group = WarriorVM("g", "Group", "Henchmen", "henchman", {}, [], [], 0, quantity=3)

    one_each = EquipmentEntryVM("dagger", "Dagger", 3, per_model=True)
    two_each = EquipmentEntryVM("dagger", "Dagger", 6, per_model=True)

    assert equipment_quantity_suffix(group, one_each) == ""
    assert equipment_quantity_suffix(group, two_each) == " ×2"
    assert one_each.quantity == 3


def test_bought_dagger_stays_separate_from_free_starting_dagger():
    controller = _controller()
    campaign = controller.state.campaign
    warrior = campaign.warriors[0]
    dagger = next(row for row in campaign.inventory if row.id == "dagger")
    warrior.equipment = [
        EquipmentEntryVM("dagger", "Dagger", 1, "starting_grant", 0, True, False),
    ]
    dagger.stash = 1

    ok, message = controller.assign_stash_item("dagger", warrior.id)

    assert ok, message
    entries = [row for row in warrior.equipment if row.item_id == "dagger"]
    assert len(entries) == 2
    assert any(row.acquisition == "starting_grant" and not row.transferable for row in entries)
    assert any(row.acquisition == "stash_assignment" and row.transferable for row in entries)

    ok, message = controller.return_equipped_item("dagger", warrior.id)
    assert ok, message
    assert len(warrior.equipment) == 1
    assert warrior.equipment[0].acquisition == "starting_grant"
    assert not warrior.equipment[0].transferable


def test_stash_assignment_enforces_weapon_carriage_limit():
    controller = _controller()
    campaign = controller.state.campaign
    warrior = campaign.warriors[0]
    dagger = next(row for row in campaign.inventory if row.id == "dagger")
    warrior.equipment = [
        EquipmentEntryVM("dagger", "Dagger", 2, "purchase", 2, False, True),
    ]
    dagger.stash = 1

    ok, message = controller.assign_stash_item("dagger", warrior.id)

    assert not ok and "two weapons" in message
    assert dagger.stash == 1

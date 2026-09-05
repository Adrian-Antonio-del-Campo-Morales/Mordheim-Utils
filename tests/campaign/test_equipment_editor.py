"""Per-warrior equipment editor: roster/stash reassignment at any moment.

The moves are legal outside the post-battle sequence (tabletop equipment
reallocation), keep the warband total constant (no buy/sell), and keep the
inventory ledger counters (owned/equipped/stash) consistent.
"""
from __future__ import annotations

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.state import make_example_state


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
    assert herbs.name in warrior.equipment
    assert (herbs.owned, herbs.equipped, herbs.stash) == (before[0], before[1] + 1, before[2] - 1)

    ok, message = controller.return_equipped_item(herbs.id, warrior.id)
    assert ok, message
    assert herbs.name not in warrior.equipment
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
    assert item.name in warrior2.equipment
    assert item2.equipped == item.equipped and item2.stash == item.stash


def test_henchman_group_carries_equipment_as_a_group():
    controller = _controller()
    campaign = controller.state.campaign
    group = next(w for w in campaign.warriors if w.quantity > 1)
    item = next(row for row in campaign.inventory if row.stash > 0)
    ok, message = controller.assign_stash_item(item.id, group.id)
    assert ok, message
    assert item.name in group.equipment

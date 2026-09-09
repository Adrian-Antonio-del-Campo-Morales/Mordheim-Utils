import copy
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.post_battle_engine import PostBattleEngine
from mordheim_campaign.application.post_battle_resolution import PostBattleResolver
from mordheim_campaign.application.state import EquipmentEntryVM, InventoryItemVM, make_example_state
from mordheim_campaign.persistence import save_campaign, load_campaign

@pytest.fixture
def pending():
    port = KnowledgePort()
    state = make_example_state(port)
    return AppController(state, port=port)

def test_recovery_decisions_survive_continue_reload_and_do_not_repeat(pending, monkeypatch, tmp_path):
    from mordheim_campaign.ui.views.moments.post_battle_moment import PostBattleMoment, messagebox
    monkeypatch.setattr(messagebox, 'showerror', lambda *a, **k: None)
    c = pending.state.campaign
    post = c.pending_post_battle
    post.active_step = 0
    post.completed_steps.clear()
    hero = next(w for w in c.warriors if w.kind == 'hero')
    c.battle(post.battle_number).out_of_action_ids = [hero.id]
    rolls = post.step_state.setdefault('injuries', {})
    rolls[hero.id + ':1'] = {'complete': True, 'finals': [{'roll': 61}]}
    moment = PostBattleMoment.__new__(PostBattleMoment)
    moment.controller = pending
    moment._pending_injury_rolls = rolls
    moment._rebuild = lambda: None
    moment._advance_step()
    assert post.active_step == 0
    assert len(post.follow_ups_for_step(0)) == 1
    assert post.unacknowledged_follow_ups(0)[0]['type'] == 'prisoner'
    moment._advance_step()
    assert len(post.follow_ups_for_step(0)) == 1
    restored = load_campaign(save_campaign(tmp_path / 'capture.mordheim', pending.state))
    pending.replace_state(restored)
    post = restored.campaign.pending_post_battle
    assert post.step_state['injuries_applied']
    engine = pending.post_battle_engine()
    row = post.follow_ups_for_step(0)[0]
    assert engine.resolve_captured(row['id'], resolution='exchange')[0]
    moment._pending_injury_rolls = post.step_state['injuries']
    moment._advance_step()
    assert post.active_step == 1
    assert not post.follow_ups_for_step(0)

def test_commit_rejects_unresolved_injury_followup(pending):
    post = pending.state.campaign.pending_post_battle
    post.completed_steps = set(range(8))
    post.pending_follow_ups.append({'id': 'capture', 'step': 0, 'type': 'prisoner'})
    assert not pending.post_battle_engine().commit()[0]

def test_upgraded_weapon_roundtrip_every_location(pending, tmp_path):
    c = pending.state.campaign
    item = InventoryItemVM('upgrade:sword', 'Upgraded sword', 'Weapon', 2, 1, 1, base_item_id='sword')
    c.inventory.append(item)
    c.warriors[0].equipment.append(EquipmentEntryVM(item.id, item.name, base_item_id='sword'))
    c.current_state.inventory = copy.deepcopy(c.inventory)
    c.current_state.roster = copy.deepcopy(c.warriors)
    restored = load_campaign(save_campaign(tmp_path / 'upgrade.mordheim', pending.state)).campaign
    assert restored.inventory == c.inventory
    assert restored.warriors == c.warriors
    assert restored.current_state == c.current_state

@pytest.mark.parametrize('name', ['Captain', 'Mate', 'Vampire', 'Priest'])
def test_custom_names_do_not_change_equipment_eligibility(pending, name):
    hero = pending.state.campaign.warriors[0]
    engine = pending.post_battle_engine()
    before = engine._profile_assignment_violation('parrot', hero)
    assert before
    hero.name = name
    assert engine._profile_assignment_violation('parrot', hero) == before
    hero.profile_id = 'pirate-captain'
    assert engine._profile_assignment_violation('parrot', hero) is None

def test_arm_limit_applies_after_reload_and_allows_replacement(pending, tmp_path):
    hero = pending.state.campaign.warriors[0]
    hero.equipment.clear()
    engine = pending.post_battle_engine()
    outcome = PostBattleResolver(pending.port).resolve_injury_subtable('hero', 'campaign.serious-injury.hero.23-arm-wound', 1)
    assert engine.apply_serious_injury(hero.id, outcome)[0]
    hero.equipment.append(EquipmentEntryVM('sword', 'Sword'))
    restored = load_campaign(save_campaign(tmp_path / 'arm.mordheim', pending.state))
    engine = PostBattleEngine(pending.port, restored.campaign, restored.campaign.pending_post_battle)
    hero = restored.campaign.warriors[0]
    assert engine.loadout_violation(hero, 'sword')
    hero.equipment.clear()
    assert engine.loadout_violation(hero, 'sword') is None

def test_historical_warriors_use_snapshot(pending, monkeypatch):
    import mordheim_campaign.ui.views.moments.state_moment as ui
    snapshot = copy.deepcopy(pending.state.campaign.current_state)
    old_names = [w.name for w in snapshot.roster]
    pending.state.campaign.warriors.clear()
    monkeypatch.setattr(ui.tk, 'Frame', MagicMock())
    monkeypatch.setattr(ui, 'ScrollableFrame', MagicMock())
    cards = MagicMock()
    monkeypatch.setattr(ui, 'WarriorCard', cards)
    ui.WarbandStateMoment._warriors(SimpleNamespace(controller=pending, snapshot=snapshot))
    assert [call.args[1].name for call in cards.call_args_list] == old_names

def test_historical_inventory_uses_snapshot_and_cannot_be_dragged(pending, monkeypatch):
    import mordheim_campaign.ui.panels.inventory as ui
    snapshot = copy.deepcopy(pending.state.campaign.current_state)
    snapshot.inventory = [InventoryItemVM('sword', 'Historical sword', 'Weapon', 1, 0, 1)]
    pending.state.campaign.inventory.clear()
    # Exercise widget setup without creating a window.
    monkeypatch.setattr(ui.tk.Frame, '__init__', lambda *a, **k: None)
    for name in ('Frame', 'Label'):
        monkeypatch.setattr(ui.tk, name, MagicMock())
    monkeypatch.setattr(ui, 'SummaryStrip', MagicMock())
    monkeypatch.setattr(ui, 'BorderedFrame', MagicMock())
    monkeypatch.setattr(ui, 'ScrollableFrame', MagicMock())
    panel = ui.InventoryWorkspace.__new__(ui.InventoryWorkspace)
    panel.columnconfigure = MagicMock()
    panel.rowconfigure = MagicMock()
    panel._make_draggable = MagicMock()
    ui.InventoryWorkspace.__init__(panel, None, pending, snapshot=snapshot)
    assert panel.roster is snapshot.roster
    assert panel.inventory is snapshot.inventory
    assert panel.read_only
    panel._make_draggable.assert_not_called()
    texts = [str(call.kwargs.get('text', '')) for call in ui.tk.Label.call_args_list]
    assert any('Historical sword' in text for text in texts)

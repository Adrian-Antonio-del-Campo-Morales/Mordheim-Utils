"""Regressions for WM-20 through WM-23."""
from unittest.mock import MagicMock, patch
import pytest
from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.domain.models import EquipmentEntryVM, InventoryItemVM
from mordheim_campaign.domain.builders import make_example_state
from mordheim_campaign.ui.dialogs.equipment_editor import EquipmentEditorDialog

@pytest.fixture(scope='module')
def port():
    return KnowledgePort()

@pytest.fixture
def controller(port):
    return AppController(make_example_state(port), port=port)

def group_with_weapons(controller, copies=1):
    engine = controller.post_battle_engine()
    group = next(w for w in engine.campaign.warriors if w.kind == 'henchman')
    group.quantity = 2
    group.experience = 0
    group.equipment = [EquipmentEntryVM('hammer', 'Hammer', 2*copies, 'purchase', 3, True, True)]
    engine.campaign.inventory = [InventoryItemVM('hammer', 'Hammer', 'Weapon', 3*copies, 2*copies, copies, 3)]
    return engine, group

@pytest.mark.parametrize('copies', [1, 2])
def test_picker_allows_only_missing_group_copies(controller, copies):
    engine, group = group_with_weapons(controller, copies)
    engine.post.gold_delta += 1000
    assert engine.add_member_to_group(group.id)[0]
    engine.campaign.warriors = [group]
    dialog = MagicMock()
    dialog.controller = controller
    with patch('mordheim_campaign.ui.dialogs.equipment_editor.tk.Toplevel') as window, \
         patch('mordheim_campaign.ui.dialogs.equipment_editor.tk.Label'), \
         patch('mordheim_campaign.ui.dialogs.equipment_editor.tk.Listbox'), \
         patch('mordheim_campaign.ui.dialogs.equipment_editor.ttk.Button'):
        EquipmentEditorDialog._assign_pick(dialog, 'hammer')
    window.assert_called_once()
    assert engine.move_stash_to_warrior('hammer', group.id)[0]
    assert group.equipment[0].quantity == 3*copies
    assert not engine.post.equipment_obligations

def test_hireling_uses_hero_resolution_with_henchman_thresholds(controller):
    engine = controller.post_battle_engine()
    warrior = engine.hireling_warrior(controller.post_battle_content().hired_swords()[0])
    engine.campaign.warriors.append(warrior)
    assert engine.add_xp(warrior.id, 20)[0]
    rows = [r for r in engine.post.pending_advances if r['warrior_id'] == warrior.id]
    thresholds = controller.post_battle_resolver().advance_thresholds('henchman')
    assert [r['threshold'] for r in rows] == [t for t in thresholds if 0 < t <= 20]
    assert all(r['table'] == 'hero' for r in rows)
    assert engine.resolve_pending_advance(warrior.id, 10)[0]
    assert all(o.kind != 'promote_henchman' for o in engine.advance_options(warrior.id))
    assert any(o.kind == 'choose_skill' for o in engine.advance_options(warrior.id))
    rows[0]['table'] = 'henchman'
    engine.sync_pending_advances()
    assert rows[0]['table'] == 'hero'

@pytest.mark.parametrize('copies', [1, 2])
def test_prisoner_creates_full_equipment_obligation_without_payment(controller, copies):
    engine, group = group_with_weapons(controller, copies)
    before = engine.projected_gold(), engine.post.veteran_pool
    engine._process_followup_queue({}, [{'type':'prisoner_join_group', 'warrior_id':group.id}], [])
    assert group.quantity == 3
    assert (engine.projected_gold(), engine.post.veteran_pool) == before
    assert engine.post.equipment_obligations[0]['quantity'] == copies
    assert engine.move_stash_to_warrior('hammer', group.id)[0]
    assert not engine.post.equipment_obligations

def test_prisoner_respects_group_limit(controller):
    engine, group = group_with_weapons(controller)
    maximum = controller.port.profile(engine.campaign.collection, engine.campaign.band_id, group.profile_id).group_maximum
    group.quantity = maximum
    engine._process_followup_queue({}, [{'type':'prisoner_join_group', 'warrior_id':group.id}], [])
    assert group.quantity == maximum

@pytest.mark.parametrize('upgraded', [False, True])
def test_weapon_access_requires_skill_and_uses_base_id(controller, upgraded):
    engine = controller.post_battle_engine()
    warrior = engine.campaign.warriors[0]
    warrior.equipment = []
    item_id = 'upgrade:bow' if upgraded else 'bow'
    engine.campaign.inventory = [InventoryItemVM(item_id, 'Bow', 'Weapon', 1, 0, 1, 10, base_item_id='bow' if upgraded else '')]
    assert not controller.assign_stash_item(item_id, warrior.id)[0]
    assert engine.campaign.inventory[0].stash == 1
    warrior.skills.append('Weapons Expert')
    assert controller.assign_stash_item(item_id, warrior.id)[0]

def test_free_profile_reward_uses_same_group_invariants(controller):
    engine, group = group_with_weapons(controller, 2)
    profile = controller.port.profile(engine.campaign.collection, engine.campaign.band_id, group.profile_id)
    before = engine.projected_gold()
    engine._process_followup_queue({}, [{'type':'grant_free_profile', 'profile_name':profile.name}], [])
    assert group.quantity == 3
    assert engine.projected_gold() == before
    assert engine.post.equipment_obligations[0]['quantity'] == 2

def test_skill_roll_survives_undoable_transaction_and_can_be_completed(controller):
    engine = controller.post_battle_engine()
    warrior = engine.hireling_warrior(controller.post_battle_content().hired_swords()[0])
    engine.campaign.warriors.append(warrior)
    engine.add_xp(warrior.id, 20)
    assert controller.perform_undoable('Roll advancement', lambda: engine.resolve_pending_advance(warrior.id, 10))[0]
    row = engine.post.pending_advance_for(warrior.id)
    assert row['roll_total'] == 10 and not row['committed']
    assert engine.commit_pending_advance(warrior.id, option_kind='choose_skill', skill_name='Weapons Expert')[0]
    assert row['committed'] and 'Weapons Expert' in warrior.skills

def test_free_profile_reward_creates_new_group_without_charging(controller):
    engine, group = group_with_weapons(controller)
    profile = controller.port.profile(engine.campaign.collection, engine.campaign.band_id, group.profile_id)
    engine.campaign.warriors = [w for w in engine.campaign.warriors if w.profile_id != profile.profile_id]
    before = engine.projected_gold()
    engine._process_followup_queue({}, [{'type':'grant_free_profile', 'profile_name':profile.name}], [])
    recruited = [w for w in engine.campaign.warriors if w.profile_id == profile.profile_id]
    assert len(recruited) == 1 and recruited[0].quantity == 1
    assert engine.projected_gold() == before

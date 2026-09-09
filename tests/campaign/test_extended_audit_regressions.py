"""Campaign transition regressions from the extended warband-manager audit."""
import copy
import json
from unittest.mock import MagicMock

import pytest

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.post_battle_engine import PostBattleEngine
from mordheim_campaign.application.post_battle_resolution import PostBattleResolver
from mordheim_campaign.domain.models import EquipmentEntryVM, InventoryItemVM
from mordheim_campaign.domain.builders import make_draft_state, make_example_state
from mordheim_campaign.persistence import CampaignFileError, load_campaign, save_campaign

@pytest.fixture(scope='module')
def port():
    return KnowledgePort()

@pytest.fixture
def draft(port):
    return AppController(make_draft_state(port, 'sisters-of-sigmar'), port=port)

@pytest.fixture
def pending(port):
    return AppController(make_example_state(port), port=port)

def record(controller):
    scenario_id, name, _ = controller.port.scenario_options()[0]
    assert controller.record_battle(scenario_id=scenario_id, scenario_name=name, opponent='Audit',
                                   result='Draw', xp_delta=0, casualties=0, out_of_action_ids=[])[0]
    return controller.post_battle_engine()

def test_draft_identifiers_stay_unique_after_removal(draft):
    for _ in range(2):
        assert draft.add_draft_warriors('sister-superior')[0]
    heroes = [w for w in draft.state.campaign.warriors if w.profile_id == 'sister-superior']
    assert draft.remove_draft_warrior(heroes[0].id)[0]
    assert draft.add_draft_warriors('sister-superior')[0]
    warriors = draft.state.campaign.warriors
    assert len({w.id for w in warriors}) == len(warriors)
    replacement = next(w for w in warriors if w.profile_id == 'sister-superior' and w.id != heroes[1].id)
    assert draft.rename_draft_warrior(replacement.id, 'Replacement')[0]
    assert heroes[1].name != 'Replacement'

def test_recruits_keep_unique_ids_after_dismissal_and_reload(draft, tmp_path):
    draft.commit_initial_warband()
    engine = record(draft)
    for _ in range(2):
        assert engine.recruit_band_profile('sister-superior')[0]
    heroes = [w for w in engine.campaign.warriors if w.profile_id == 'sister-superior']
    assert engine.dismiss_warrior(heroes[0].id)[0]
    draft.replace_state(load_campaign(save_campaign(tmp_path/'recruit.mordheim', draft.state)))
    engine = draft.post_battle_engine()
    assert engine.recruit_band_profile('sister-superior')[0]
    ids = [w.id for w in engine.campaign.warriors]
    assert len(ids) == len(set(ids))
    assert heroes[0].id not in ids  # previous event log keeps the old identity reserved

def test_creation_requires_the_canonical_leader(draft, tmp_path):
    assert draft.add_draft_warriors('sister-superior')[0]
    leader = next(w for w in draft.state.campaign.warriors if w.profile_id == 'sigmarite-matriarch')
    assert draft.remove_draft_warrior(leader.id)[0]
    assert not draft.state.campaign.draft_is_legal
    restored = load_campaign(save_campaign(tmp_path/'draft.mordheim', draft.state))
    draft.replace_state(restored)
    draft.commit_initial_warband()
    assert draft.state.campaign.is_draft
    assert draft.add_draft_warriors('sigmarite-matriarch')[0]
    draft.commit_initial_warband()
    assert not draft.state.campaign.is_draft

def test_advances_are_earned_once_across_three_battles(draft, tmp_path):
    hero_id = draft.state.campaign.warriors[0].id
    draft.commit_initial_warband()
    engine = record(draft)
    engine.apply_battle_experience()
    assert not engine.post.pending_advances  # recruitment XP is already included in profile
    assert engine.add_xp(hero_id, 20)[0]
    assert [r['threshold'] for r in engine.post.pending_advances] == [40]
    assert engine.resolve_pending_advance(hero_id, 8, subroll=2, threshold=40)[0]
    engine.post.completed_steps = set(range(8))
    assert engine.commit()[0]
    draft.replace_state(load_campaign(save_campaign(tmp_path/'after1.mordheim', draft.state)))
    engine = record(draft)
    engine.apply_battle_experience()
    assert not engine.post.pending_advances
    engine.post.completed_steps = set(range(8))
    assert engine.commit()[0]
    engine = record(draft)
    assert engine.add_xp(hero_id, 25)[0]
    assert [r['threshold'] for r in engine.post.pending_advances] == [65]

def test_unresolved_advance_prevents_final_commit(pending):
    engine = pending.post_battle_engine()
    engine.sync_pending_advances()
    engine.post.completed_steps = set(range(8))
    assert not engine.commit()[0]

@pytest.mark.parametrize('resolution', ['lost', 'exchange'])
def test_capture_does_not_leave_an_unresolvable_advance(pending, monkeypatch, resolution):
    from mordheim_campaign.ui.views.moments.post_battle_moment import PostBattleMoment, messagebox
    monkeypatch.setattr(messagebox, 'showerror', lambda *a, **k: None)
    engine = pending.post_battle_engine()
    post = engine.post
    post.experience_applied = False
    post.active_step = 0
    post.completed_steps.clear()
    hero = engine.campaign.warriors[0]
    engine.campaign.battle(post.battle_number).out_of_action_ids = [hero.id]
    moment = PostBattleMoment.__new__(PostBattleMoment)
    moment.controller = pending
    moment._rebuild = lambda: None
    moment._pending_injury_rolls = post.step_state.setdefault('injuries', {})
    moment._pending_injury_rolls[hero.id+':1'] = {'complete':True, 'finals':[{'roll':61}]}
    moment._advance_step()
    assert engine.resolve_captured(post.follow_ups_for_step(0)[0]['id'], resolution=resolution)[0]
    moment._advance_step()
    assert post.active_step == 1
    if resolution == 'lost':
        assert not [r for r in post.pending_advances if r['warrior_id'] == hero.id and not r['committed']]
        moment._advance_step()
        assert post.active_step == 2
    else:
        assert any(r['warrior_id'] == hero.id for r in post.pending_advances)

@pytest.mark.parametrize('weapons_per_model', [1,2])
def test_partial_henchman_death_conserves_inventory(pending, weapons_per_model):
    engine = pending.post_battle_engine()
    warrior = next(w for w in engine.campaign.warriors if w.kind == 'henchman' and w.quantity == 2)
    copies = 2 * weapons_per_model
    warrior.equipment = [EquipmentEntryVM('sword', 'Sword', copies, 'purchase', 10, True)]
    engine.campaign.inventory = [InventoryItemVM('sword','Sword','Weapon',copies,copies,0,10)]
    outcome = PostBattleResolver(pending.port).resolve_henchman_serious_injury(1)
    assert engine.apply_serious_injury(warrior.id, outcome)[0]
    stock = engine.campaign.inventory[0]
    assert warrior.quantity == 1 and warrior.equipment[0].quantity == weapons_per_model
    assert stock.owned == stock.equipped == weapons_per_model and stock.stash == 0
    assert engine.apply_serious_injury(warrior.id, outcome)[0]
    assert warrior not in engine.campaign.warriors
    assert stock.owned == stock.equipped == stock.stash == 0

def test_absent_hero_cannot_explore(draft):
    assert draft.add_draft_warriors('sister-superior')[0]
    draft.commit_initial_warband()
    draft.state.campaign.warriors[0].games_to_miss = 1
    engine = record(draft)
    battle = engine.campaign.battle(engine.post.battle_number)
    assert len(battle.absentees) == 1
    assert engine.eligible_exploration_heroes(battle) == 1

def test_zero_dice_exploration_is_a_resolved_step(pending, monkeypatch):
    from mordheim_campaign.ui.views.moments.post_battle_moment import PostBattleMoment, messagebox
    monkeypatch.setattr(messagebox, 'showerror', lambda *a, **k: None)
    engine = pending.post_battle_engine()
    engine.post.active_step = 2
    engine.post.completed_steps = {0,1}
    battle = engine.campaign.battle(engine.post.battle_number)
    battle.result = 'Defeat'
    battle.out_of_action_ids = [w.id for w in engine.campaign.warriors if w.kind=='hero']
    resolver = PostBattleResolver(pending.port)
    assert resolver.exploration_dice(engine.eligible_exploration_heroes(battle), False) == 0
    moment = PostBattleMoment.__new__(PostBattleMoment)
    moment.controller = pending
    moment._rebuild = lambda: None
    moment.after_idle = lambda *a: None
    moment._pending_exploration = engine.post.step_state.setdefault('exploration', {})
    assert not moment._advance_step_impl()[0]  # unresolved is different from empty
    moment._apply_exploration_roll([], resolver, moment._pending_exploration)
    assert moment._advance_step_impl()[0]
    assert engine.post.active_step == 3

def test_zombies_cannot_receive_equipment_or_experience(port):
    controller = AppController(make_draft_state(port,'undead'),port=port)
    assert controller.add_draft_warriors('zombies')[0]
    controller.commit_initial_warband()
    engine = record(controller)
    zombie = next(w for w in engine.campaign.warriors if w.profile_id=='zombies')
    assert engine.buy_item('sword',1,10)[0]
    assert not engine.assign_item('sword', zombie.id)[0]
    assert not engine.add_xp(zombie.id,8)[0]
    scenario_id = port.scenario_options()[0][0]
    awards = controller.scenario_rewards().compute_for(scenario_id, engine.campaign.warriors,result='Draw')
    assert not awards.get(zombie.id,0)
    battle = engine.campaign.battle(engine.post.battle_number)
    battle.xp_awards = {zombie.id:8}
    engine.apply_battle_experience()
    assert zombie.experience == 0
    assert not any(row['warrior_id']==zombie.id for row in engine.post.pending_advances)
    assert port.can_gain_experience('undead','ghouls')
    assert not port.can_gain_experience('undead','dire-wolves')

def test_free_dagger_does_not_prevent_two_handed_equipment(port):
    controller = AppController(make_draft_state(port,'mercenaries'),port=port)
    warrior = controller.state.campaign.warriors[0]
    assert any(e.item_id=='dagger' and not e.transferable for e in warrior.equipment)
    assert controller.buy_draft_equipment(warrior.id,'great_weapon')[0]

def test_variable_price_conserves_paid_gold_and_refunds(port, tmp_path):
    controller = AppController(make_draft_state(port,'lustria-clan-pestilens'),port=port)
    start = controller.state.campaign.draft_treasury
    assert controller.buy_draft_stash_item('fog_warpstone_fragments',1,106)[0]
    assert controller.buy_draft_stash_item('fog_warpstone_fragments',1,101)[0]
    assert controller.state.campaign.draft_treasury == start-207
    controller.replace_state(load_campaign(save_campaign(tmp_path/'costs.mordheim',controller.state)))
    assert controller.state.campaign.draft_treasury == start-207
    assert controller.remove_draft_stash_item('fog_warpstone_fragments')[0]
    assert controller.state.campaign.draft_treasury == start-101
    assert controller.remove_draft_stash_item('fog_warpstone_fragments')[0]
    assert controller.state.campaign.draft_treasury == start

@pytest.mark.parametrize('copies', [1, 2])
def test_promotion_preserves_upgraded_weapon_metadata(pending, copies):
    engine = pending.post_battle_engine()
    warrior = next(w for w in engine.campaign.warriors if w.kind=='henchman' and w.quantity==2)
    warrior.equipment = [EquipmentEntryVM('upgrade:sword','Upgraded Sword',2*copies,'stash_assignment',20,True,True,['Poisoned'],'sword')]
    assert engine.promote_henchman(warrior.id)[0]
    hero = next(w for w in engine.campaign.warriors if '#promoted' in w.id)
    entry = hero.equipment[0]
    assert entry.base_item_id=='sword' and entry.special_rules==['Poisoned'] and entry.quantity==copies
    assert warrior.equipment[0].quantity==copies and warrior.equipment[0].special_rules==['Poisoned']
    entry.special_rules.append('Hero only')
    assert 'Hero only' not in warrior.equipment[0].special_rules

@pytest.mark.parametrize('selection',['state:99999','state:bad','post:99999','post','battle:x','unknown:0'])
def test_invalid_selection_falls_back_to_current_state(pending,tmp_path,selection):
    path = save_campaign(tmp_path/'invalid.mordheim',pending.state)
    payload=json.loads(path.read_text(encoding='utf-8')); payload['view']['selected_moment']=selection
    path.write_text(json.dumps(payload),encoding='utf-8')
    restored=load_campaign(path)
    assert restored.selected_moment==f'state:{restored.campaign.current_state_number}'

@pytest.mark.parametrize('version',['invalid',None,[],3.5])
def test_invalid_version_is_a_campaign_file_error(pending,tmp_path,version):
    path=save_campaign(tmp_path/'invalid.mordheim',pending.state)
    payload=json.loads(path.read_text(encoding='utf-8'));payload['format_version']=version
    path.write_text(json.dumps(payload),encoding='utf-8')
    with pytest.raises(CampaignFileError): load_campaign(path)

def test_duplicate_warrior_ids_are_rejected_on_load(pending,tmp_path):
    path=save_campaign(tmp_path/'duplicates.mordheim',pending.state)
    payload=json.loads(path.read_text(encoding='utf-8'))
    payload['campaign']['warriors'][1]['id']=payload['campaign']['warriors'][0]['id']
    path.write_text(json.dumps(payload),encoding='utf-8')
    with pytest.raises(CampaignFileError,match='Duplicate'): load_campaign(path)

def test_failed_save_preserves_last_valid_file(pending,tmp_path,monkeypatch):
    from mordheim_campaign.persistence import campaigns
    path=save_campaign(tmp_path/'atomic.mordheim',pending.state)
    original=path.read_bytes()
    pending.state.campaign.campaign_name='Changed'
    def fail(*a): raise OSError('simulated replacement failure')
    monkeypatch.setattr(campaigns.os,'replace',fail)
    with pytest.raises(CampaignFileError): save_campaign(path,pending.state)
    assert path.read_bytes()==original
    assert list(tmp_path.iterdir())==[path]

def test_recruit_group_preserves_two_weapons_per_member(pending):
    engine = pending.post_battle_engine()
    group = next(w for w in engine.campaign.warriors if w.kind == 'henchman')
    group.quantity = 2
    group.experience = 0
    group.equipment = [EquipmentEntryVM('hammer', 'Hammer', 4, 'purchase', 3, True, True)]
    engine.campaign.inventory = [InventoryItemVM('hammer', 'Hammer', 'close-combat-weapon', owned=6, equipped=4, stash=2, value=3)]
    engine.post.gold_delta += 1000
    assert engine.group_recruitment_quote(group.id)[1]['requirements'][0]['copies_per_model'] == 2
    assert engine.add_member_to_group(group.id)[0]
    assert engine.post.equipment_obligations[0]['quantity'] == 2
    assert engine.move_stash_to_warrior('hammer', group.id)[0]
    assert group.equipment[0].quantity == 6
    assert not engine.post.equipment_obligations
    assert not engine.move_stash_to_warrior('hammer', group.id)[0]

def test_draft_upgrade_charges_only_incremental_cost(draft, monkeypatch):
    from types import SimpleNamespace
    offer = SimpleNamespace(item_id='test_upgrade', name='Upgrade', price_upgrade_multiplier=2)
    monkeypatch.setattr(draft, 'draft_stash_offers', lambda: [offer])
    campaign = draft.state.campaign
    campaign.inventory = [InventoryItemVM('hammer', 'Hammer', 'close-combat-weapon',
                                          owned=1, equipped=0, stash=1, value=3)]
    before = campaign.draft_treasury
    assert draft.buy_draft_weapon_upgrade(offer, 'hammer', 6)[0]
    assert campaign.draft_treasury == before - 6
    upgraded = next(row for row in campaign.inventory if row.id == 'test_upgrade:hammer')
    assert upgraded.total_acquisition_cost == 9
    assert upgraded.owned == upgraded.stash == 1

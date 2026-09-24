"""Mixed-price refunds and acquisition accounting."""
import pytest
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.controller import AppController
from mordheim_campaign.domain.builders import make_draft_state
from mordheim_campaign.persistence import save_campaign,load_campaign

@pytest.fixture(scope='module')
def port(): return KnowledgePort()

@pytest.mark.parametrize('prices',[(a,b) for a in range(26,32) for b in range(26,32)])
@pytest.mark.parametrize('dismiss',[False,True])
@pytest.mark.parametrize('remove_first',[False,True])
def test_personal_equipment_refund_matches_actual_purchase(port,tmp_path,prices,remove_first,dismiss):
    c=AppController(make_draft_state(port,'lustria-clan-pestilens'),port=port)
    assert c.add_draft_warriors('pestilens-sorcerer')[0]
    heroes=[w for w in c.state.campaign.warriors if w.kind=='hero'][:2]
    start=c.state.campaign.draft_treasury
    for w,price in zip(heroes,prices):
        assert c.buy_draft_equipment(w.id,'rat_familiar_scroll',price)[0]
    assert c.state.campaign.draft_treasury==start-sum(prices)
    c.replace_state(load_campaign(save_campaign(tmp_path/'prices.mordheim',c.state)))
    index=0 if remove_first else 1
    refund=prices[index]+(heroes[index].cost if dismiss else 0)
    before=c.state.campaign.draft_treasury
    if dismiss:
        assert c.remove_draft_warrior(heroes[index].id)[0]
    else:
        assert c.remove_draft_equipment(heroes[index].id,'rat_familiar_scroll')[0]
    assert c.state.campaign.draft_treasury==before+refund

@pytest.mark.parametrize('prices',[(26,31),(31,26)])
@pytest.mark.parametrize('returned',[0,1])
def test_return_to_stash_refunds_the_returned_copy(port,tmp_path,prices,returned):
    c=AppController(make_draft_state(port,'lustria-clan-pestilens'),port=port)
    assert c.add_draft_warriors('pestilens-sorcerer')[0]
    heroes=[w for w in c.state.campaign.warriors if w.kind=='hero'][:2]
    for w,price in zip(heroes,prices):
        assert c.buy_draft_equipment(w.id,'rat_familiar_scroll',price)[0]
    before=c.state.campaign.draft_treasury
    assert c.return_equipped_item('rat_familiar_scroll',heroes[returned].id)[0]
    assert c.state.campaign.draft_treasury==before
    c.replace_state(load_campaign(save_campaign(tmp_path/'stash.mordheim',c.state)))
    assert c.remove_draft_stash_item('rat_familiar_scroll')[0]
    assert c.state.campaign.draft_treasury==before+prices[returned]

@pytest.mark.parametrize('prices',[(26,31),(31,26)])
def test_assignment_preserves_copy_cost_before_other_refund(port,tmp_path,prices):
    c=AppController(make_draft_state(port,'lustria-clan-pestilens'),port=port)
    hero=c.state.campaign.warriors[0]
    for price in prices:
        assert c.buy_draft_stash_item('rat_familiar_scroll',1,price)[0]
    before=c.state.campaign.draft_treasury
    assert c.assign_stash_item('rat_familiar_scroll',hero.id)[0]
    entry=next(i for i in hero.equipment if i.item_id=='rat_familiar_scroll')
    assert entry.unit_cost==prices[0]
    c.replace_state(load_campaign(save_campaign(tmp_path/'assigned.mordheim',c.state)))
    assert c.remove_draft_stash_item('rat_familiar_scroll')[0]
    assert c.state.campaign.draft_treasury==before+prices[1]

def test_mixed_price_group_assignment_and_refund(port,tmp_path):
    c=AppController(make_draft_state(port,'lustria-pirates'),port=port)
    assert c.add_draft_warriors('crew',2)[0]
    group=next(w for w in c.state.campaign.warriors if w.profile_id=='crew')
    if group.quantity!=2:
        assert c.adjust_draft_group(group.id,2-group.quantity)[0]
    for price in (42,51,48):
        assert c.buy_draft_stash_item('pirate_flag',1,price)[0]
    result=c.assign_stash_item('pirate_flag',group.id)
    assert result[0],result
    entry=next(i for i in group.equipment if i.item_id=='pirate_flag')
    assert entry.copy_costs==[42,51]
    c.replace_state(load_campaign(save_campaign(tmp_path/'group.mordheim',c.state)))
    before=c.state.campaign.draft_treasury
    assert c.remove_draft_stash_item('pirate_flag')[0]
    assert c.state.campaign.draft_treasury==before+48
    assert c.return_equipped_item('pirate_flag',group.id)[0]
    assert c.remove_draft_stash_item('pirate_flag',2)[0]
    assert c.state.campaign.draft_treasury==before+48+42+51

def test_mixed_cost_group_resize_preserves_remaining_cost(port):
    c=AppController(make_draft_state(port,'lustria-pirates'),port=port)
    assert c.add_draft_warriors('crew',2)[0]
    group=next(w for w in c.state.campaign.warriors if w.profile_id=='crew')
    for price in (42,51,48):
        assert c.buy_draft_stash_item('pirate_flag',1,price)[0]
    assert c.assign_stash_item('pirate_flag',group.id)[0]
    assert c.adjust_draft_group(group.id,1)[0]
    entry=next(i for i in group.equipment if i.item_id=='pirate_flag')
    assert entry.copy_costs==[42,51,48]
    assert c.adjust_draft_group(group.id,-2)[0]
    assert entry.copy_costs==[42]
    before=c.state.campaign.draft_treasury
    assert c.remove_draft_stash_item('pirate_flag',2)[0]
    assert c.state.campaign.draft_treasury==before+51+48

def test_heroes_cannot_be_recruited_as_a_multi_member_row(port):
    c=AppController(make_draft_state(port,'lustria-clan-pestilens'),port=port)
    assert not c.add_draft_warriors('monk-initiates',2)[0]
    c.commit_initial_warband()
    scenario,name,_=port.scenario_options()[0]
    assert c.record_battle(scenario_id=scenario,scenario_name=name,opponent='Audit',result='Draw',xp_delta=0,casualties=0)[0]
    assert not c.post_battle_engine().recruit_band_profile('monk-initiates',2,free=True)[0]

@pytest.mark.parametrize('prices',[(42,51),(51,42),(46,46)])
@pytest.mark.parametrize('action',['promote','death','dismiss'])
def test_mixed_costs_survive_group_transitions(port,tmp_path,prices,action):
    import copy
    c=AppController(make_draft_state(port,'lustria-pirates'),port=port)
    assert c.add_draft_warriors('crew',2)[0]
    group=next(w for w in c.state.campaign.warriors if w.profile_id=='crew')
    for price in prices:
        assert c.buy_draft_stash_item('pirate_flag',1,price)[0]
    assert c.assign_stash_item('pirate_flag',group.id)[0]
    c.commit_initial_warband()
    scenario,name,_=port.scenario_options()[0]
    assert c.record_battle(scenario_id=scenario,scenario_name=name,opponent='Audit',result='Draw',xp_delta=0,casualties=0)[0]
    engine=c.post_battle_engine()
    if action=='promote':
        engine.add_xp(group.id,8)
        assert engine.resolve_pending_advance(group.id,10)[0]
        operation=lambda:engine.commit_pending_advance(group.id,option_kind='promote_henchman')
    elif action=='death':
        outcome=c.post_battle_resolver().resolve_henchman_serious_injury(1)
        operation=lambda:engine.apply_serious_injury(group.id,outcome)
    else:
        operation=lambda:engine.dismiss_warrior(group.id,one_member=True)
    before=copy.deepcopy(c.state)
    assert c.perform_undoable('transition',operation)[0]
    entry=next(i for i in group.equipment if i.item_id=='pirate_flag')
    assert entry.copy_costs==[prices[1]]
    stock=next(i for i in c.state.campaign.inventory if i.id=='pirate_flag')
    assert stock.owned==stock.equipped+stock.stash
    if action=='death':
        assert stock.acquisition_costs==[prices[1]]
    elif action=='dismiss':
        assert c.state.campaign.stash_acquisition_costs(stock)==[prices[0]]
    else:
        hero=next(w for w in c.state.campaign.warriors if '#promoted' in w.id)
        assert next(i for i in hero.equipment if i.item_id=='pirate_flag').copy_costs==[prices[0]]
    assert load_campaign(save_campaign(tmp_path/'transition.mordheim',c.state)).campaign==c.state.campaign
    assert c.undo()[0]
    assert c.state==before

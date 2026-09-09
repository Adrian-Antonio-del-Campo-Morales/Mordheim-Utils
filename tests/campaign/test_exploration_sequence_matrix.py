"""Exploration choice chains across matching-dice results."""
import copy
import pytest
from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.state import make_draft_state
from mordheim_campaign.persistence import load_campaign, save_campaign

@pytest.fixture(scope='module')
def port(): return KnowledgePort()

@pytest.mark.parametrize('band',['sisters-of-sigmar','undead','skaven-clan-eshin','cult-of-the-possessed','witch-hunters','lizardmen'])
@pytest.mark.parametrize('count',range(2,7))
@pytest.mark.parametrize('face',range(1,7))
@pytest.mark.parametrize('high',[False,True])
def test_exploration_chain_roundtrip(port,tmp_path,count,face,high,band):
    c=AppController(make_draft_state(port,band),port=port)
    c.commit_initial_warband()
    scenario,name,_=port.scenario_options()[0]
    assert c.record_battle(scenario_id=scenario,scenario_name=name,opponent='Audit',result='Draw',xp_delta=0,casualties=0)[0]
    engine=c.post_battle_engine()
    assert engine.apply_exploration((face,)*count)[0]
    for step in range(30):
        engine=c.post_battle_engine()
        pending=engine.exploration_followup_pending()
        if pending is None:
            break
        restored=load_campaign(save_campaign(tmp_path/'choice.mordheim',c.state))
        assert restored.campaign==c.state.campaign
        c.replace_state(restored)
        engine=c.post_battle_engine()
        before=copy.deepcopy(c.state)
        kind=pending['kind']
        if kind=='roll':
            roll=pending.get('dice_count',1)*(pending.get('dice_sides',6) if high else 1)
            args={'roll':roll}
        elif kind=='choose_hero':
            heroes=[w for w in c.state.campaign.warriors if w.kind=='hero']
            assert heroes, pending
            args={'hero_id':heroes[0].id}
        elif kind=='choose_option':
            assert pending['options'],pending
            args={'option_id':pending['options'][-1 if high else 0]['id']}
        elif kind=='choose_warriors':
            args={'warrior_ids':[r['id'] for r in pending['options'][:pending.get('maximum',1)]]}
        else:
            pytest.fail(str(pending))
        assert c.perform_undoable('choice',lambda:engine.advance_exploration_followup(**args))[0],pending
        after=copy.deepcopy(c.state)
        assert c.undo()[0]
        assert c.state==before
        engine=c.post_battle_engine()
        assert c.perform_undoable('choice',lambda:engine.advance_exploration_followup(**args))[0]
        assert c.state==after
    else:
        pytest.fail('Exploration did not finish in 30 decisions')

@pytest.fixture
def pending_controller(port):
    from mordheim_campaign.application.state import make_example_state
    return AppController(make_example_state(port),port=port)

@pytest.mark.parametrize('recipient',['missing','henchman','removed'])
def test_invalid_reward_recipient_keeps_pending_state(pending_controller,recipient):
    c=pending_controller
    engine=c.post_battle_engine()
    hero=next(w for w in engine.campaign.warriors if w.kind=='hero')
    target={'missing':'no-longer-present','henchman':next(w.id for w in engine.campaign.warriors if w.kind=='henchman'),'removed':hero.id}[recipient]
    engine._add_follow_up(2,{'type':'exploration_followup','queue':[{'type':'grant','recipient':'hero','resources':{'experience':{'kind':'fixed','value':2}}}],'messages':[]})
    assert engine.exploration_followup_pending()['kind']=='choose_hero'
    if recipient=='removed':
        engine.campaign.warriors.remove(hero)
    before=copy.deepcopy(c.state)
    ok,message=engine.advance_exploration_followup(hero_id=target)
    assert not ok
    assert c.state==before

@pytest.mark.parametrize('roll',[0,-1,7,100])
def test_out_of_range_reward_roll_keeps_pending_state(pending_controller,roll):
    c=pending_controller
    engine=c.post_battle_engine()
    engine._add_follow_up(2,{'type':'exploration_followup','queue':[{'type':'grant','recipient':'warband','resources':{'gold_crowns':{'kind':'dice','dice':{'count':1,'sides':6}}}}],'messages':[]})
    assert engine.exploration_followup_pending()['kind']=='roll'
    before=copy.deepcopy(c.state)
    assert not engine.advance_exploration_followup(roll=roll)[0]
    assert c.state==before

@pytest.mark.parametrize('roll',[1,13,2.5,True])
def test_two_dice_reward_rejects_invalid_total(pending_controller,roll):
    c=pending_controller
    engine=c.post_battle_engine()
    engine._add_follow_up(2,{'type':'exploration_followup','queue':[{'type':'grant','recipient':'warband','resources':{'gold_crowns':{'kind':'dice','dice':{'count':2,'sides':6}}}}],'messages':[]})
    engine.exploration_followup_pending()
    before=copy.deepcopy(c.state)
    assert not engine.advance_exploration_followup(roll=roll)[0]
    assert c.state==before

def test_removed_multi_choice_recipient_is_rejected(pending_controller):
    c=pending_controller
    engine=c.post_battle_engine()
    warrior=engine.campaign.warriors[0]
    engine._add_follow_up(2,{'type':'exploration_followup','queue':[], 'pending':{'kind':'choose_warriors','options':[{'id':warrior.id}],'maximum':1},'messages':[]})
    engine.campaign.warriors.remove(warrior)
    before=copy.deepcopy(c.state)
    assert not engine.advance_exploration_followup(warrior_ids=[warrior.id])[0]
    assert c.state==before

@pytest.mark.parametrize('node',[
    {'type':'grant_special_item','item_id':'audit.relic','name':'Relic','text':'Test relic'},
    {'type':'grant','recipient':'hero','resources':{'experience':{'kind':'fixed','value':2}}},
    {'type':'grant_rule','recipient':'hero','text':'Test personal rule'},
])
@pytest.mark.parametrize('already_pending',[False,True])
def test_rewards_without_heroes_do_not_require_impossible_choice(pending_controller,node,already_pending):
    c=pending_controller
    engine=c.post_battle_engine()
    engine._add_follow_up(2,{'type':'exploration_followup','queue':[node],'messages':[]})
    if already_pending:
        assert engine.exploration_followup_pending()['kind']=='choose_hero'
    engine.campaign.warriors[:]=[w for w in engine.campaign.warriors if w.kind!='hero']
    choice=engine.exploration_followup_pending()
    assert choice['kind']=='choose_option'
    assert engine.advance_exploration_followup(option_id=choice['options'][0]['id'])[0]
    assert engine.exploration_followup_pending() is None
    assert not any(r.get('type')=='exploration_followup' for r in engine.post.pending_follow_ups)
    if node['type']=='grant_special_item':
        stock=next(i for i in engine.campaign.inventory if i.id=='audit.relic')
        assert stock.owned==stock.stash==1 and stock.equipped==0

@pytest.mark.parametrize('roll',range(1,7))
def test_lost_unique_artefact_roll_requests_reroll(pending_controller,roll):
    c=pending_controller
    engine=c.post_battle_engine()
    table=c.port.campaign_catalog().catalogue('exploration-and-income.yaml')['magical_artefacts']['results']
    artefact=next(a for a in table if int(a['roll'])==roll)
    item_id='magical_artefact.'+artefact['id'].removeprefix('campaign.magical-artefact.')
    engine.campaign.unique_reward_ids.append(item_id)
    engine._add_follow_up(2,{'type':'exploration_followup','queue':[{'type':'magical_artefact_table'}],'messages':[]})
    assert engine.exploration_followup_pending()['kind']=='roll'
    assert engine.advance_exploration_followup(roll=roll)[0]
    assert engine.exploration_followup_pending()['kind']=='roll'

def test_exhausted_artefact_table_has_finishable_resolution(pending_controller):
    c=pending_controller
    engine=c.post_battle_engine()
    table=c.port.campaign_catalog().catalogue('exploration-and-income.yaml')['magical_artefacts']['results']
    engine.campaign.unique_reward_ids.extend('magical_artefact.'+a['id'].removeprefix('campaign.magical-artefact.') for a in table)
    engine._add_follow_up(2,{'type':'exploration_followup','queue':[{'type':'magical_artefact_table'}],'messages':[]})
    pending=engine.exploration_followup_pending()
    assert pending['kind']=='choose_option'
    assert engine.advance_exploration_followup(option_id=pending['options'][0]['id'])[0]
    assert engine.exploration_followup_pending() is None


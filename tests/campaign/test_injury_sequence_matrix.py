"""Cross-operation regressions for injury, inventory and persistence."""
import copy
from collections import Counter
import pytest
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.state import make_draft_state
from mordheim_campaign.persistence import save_campaign, load_campaign

@pytest.fixture(scope='module')
def port():
    return KnowledgePort()

@pytest.fixture
def campaign(port):
    c = AppController(make_draft_state(port,'sisters-of-sigmar'),port=port)
    assert c.add_draft_warriors('sister-superior')[0]
    other = next(w for w in c.state.campaign.warriors if w.profile_id=='sister-superior')
    assert c.buy_draft_equipment(other.id,'dagger')[0]
    c.commit_initial_warband()
    scenario,name,_=port.scenario_options()[0]
    assert c.record_battle(scenario_id=scenario,scenario_name=name,opponent='Audit',result='Draw',xp_delta=0,casualties=0)[0]
    return c

def inventory_invariant(c):
    carried=Counter()
    for w in c.state.campaign.warriors:
        for item in w.equipment:
            if item.transferable:
                carried[item.item_id]+=item.quantity
    for stock in c.state.campaign.inventory:
        assert stock.owned==stock.equipped+stock.stash
        assert stock.equipped==carried.pop(stock.id,0),stock.id
        assert min(stock.owned,stock.equipped,stock.stash)>=0
    assert not +carried

@pytest.mark.parametrize('roll',[10*t+u for t in range(1,7) for u in range(1,7)])
def test_each_hero_injury_preserves_other_equipment_and_roundtrips(campaign,tmp_path,roll):
    c=campaign
    engine=c.post_battle_engine()
    victim=next(w for w in c.state.campaign.warriors if w.profile_id=='sigmarite-matriarch')
    before=copy.deepcopy(c.state)
    outcome=c.post_battle_resolver().resolve_hero_serious_injury(roll)
    assert c.perform_undoable('injury',lambda:engine.apply_serious_injury(victim.id,outcome))[0]
    inventory_invariant(c)
    restored=load_campaign(save_campaign(tmp_path/'injury.mordheim',c.state))
    assert restored.campaign==c.state.campaign
    assert c.undo()[0]
    assert c.state==before

def test_exploration_death_preserves_other_warriors_inventory(campaign):
    c=campaign
    engine=c.post_battle_engine()
    victim=next(w for w in c.state.campaign.warriors if w.profile_id=='sigmarite-matriarch')
    engine._process_followup_queue({'hero_id':victim.id},[{'type':'roster.remove_warrior','subject':'$searching_hero'}],[])
    assert victim not in c.state.campaign.warriors
    inventory_invariant(c)

@pytest.mark.parametrize('extra', ['light_armour', 'buckler', 'helmet'])
def test_pit_loss_discards_creation_weapons_but_keeps_miscellaneous(campaign, extra):
    c=campaign
    engine=c.post_battle_engine()
    victim=next(w for w in c.state.campaign.warriors if w.profile_id=='sister-superior')
    price=c.port.trading_post_price(extra)
    engine.post.gold_delta += 100
    assert engine.buy_item(extra,1,price)[0]
    assert c.assign_stash_item(extra,victim.id)[0]
    assert engine.buy_item('lantern',1,10)[0]
    assert c.assign_stash_item('lantern',victim.id)[0]
    engine.post.pending_follow_ups.append({'id':'pit-test','warrior_id':victim.id,'encounter_id':'campaign.encounter.sold-to-the-pits'})
    assert engine.resolve_sold_to_pits('pit-test',won=False,injury_roll=41)[0]
    assert all(i.item_id not in {'dagger',extra} for i in victim.equipment)
    assert any(i.item_id=='lantern' for i in victim.equipment)
    inventory_invariant(c)

@pytest.mark.parametrize('roll',[10*t+u for t in range(1,7) for u in range(1,7)])
def test_pit_injury_branches_roundtrip_and_undo(campaign,tmp_path,roll):
    c=campaign
    victim=next(w for w in c.state.campaign.warriors if w.profile_id=='sister-superior')
    c.post_battle_engine().post.pending_follow_ups.append({'id':'pit','warrior_id':victim.id,'encounter_id':'campaign.encounter.sold-to-the-pits'})
    c.replace_state(load_campaign(save_campaign(tmp_path/'pending.mordheim',c.state)))
    before=copy.deepcopy(c.state)
    engine=c.post_battle_engine()
    assert c.perform_undoable('pit',lambda:engine.resolve_sold_to_pits('pit',won=False,injury_roll=roll))[0]
    inventory_invariant(c)
    assert load_campaign(save_campaign(tmp_path/'resolved.mordheim',c.state)).campaign==c.state.campaign
    assert not engine.resolve_sold_to_pits('pit',won=False,injury_roll=roll)[0]
    assert c.undo()[0]
    assert c.state==before

@pytest.mark.parametrize('resolution',['ransom','exchange','lost'])
def test_captive_reload_resolution_once_and_undo(campaign,tmp_path,resolution):
    c=campaign
    victim=next(w for w in c.state.campaign.warriors if w.profile_id=='sister-superior')
    c.post_battle_engine().post.pending_follow_ups.append({'id':'capture','type':'prisoner','warrior_id':victim.id,'step':0})
    c.replace_state(load_campaign(save_campaign(tmp_path/'captive.mordheim',c.state)))
    before=copy.deepcopy(c.state)
    engine=c.post_battle_engine()
    assert c.perform_undoable('capture',lambda:engine.resolve_captured('capture',resolution=resolution,ransom=10))[0]
    inventory_invariant(c)
    assert not engine.resolve_captured('capture',resolution=resolution,ransom=10)[0]
    assert c.undo()[0]
    assert c.state==before

@pytest.mark.parametrize('initial',[23,24,25,56])
@pytest.mark.parametrize('roll',range(1,7))
def test_injury_subtables_reload_and_undo(campaign,tmp_path,initial,roll):
    c=campaign
    engine=c.post_battle_engine()
    victim=c.state.campaign.warriors[0]
    assert engine.apply_serious_injury(victim.id,c.post_battle_resolver().resolve_hero_serious_injury(initial))[0]
    followup=next(r for r in engine.post.pending_follow_ups if r.get('result_id')==c.post_battle_resolver().resolve_hero_serious_injury(initial).result_id)
    c.replace_state(load_campaign(save_campaign(tmp_path/'subtable.mordheim',c.state)))
    before=copy.deepcopy(c.state)
    engine=c.post_battle_engine()
    assert c.perform_undoable('subtable',lambda:engine.resolve_injury_followup(followup['id'],roll))[0]
    inventory_invariant(c)
    ids=[r['id'] for r in engine.post.pending_follow_ups]
    assert len(ids)==len(set(ids))
    assert c.undo()[0]
    assert c.state==before

def test_followup_ids_not_reused_while_another_is_pending(campaign):
    engine=campaign.post_battle_engine()
    a,b=campaign.state.campaign.warriors[:2]
    outcome=campaign.post_battle_resolver().resolve_hero_serious_injury(61)
    assert engine.apply_serious_injury(a.id,outcome)[0]
    assert engine.apply_serious_injury(b.id,outcome)[0]
    first=engine.post.pending_follow_ups[0]
    assert engine.resolve_captured(first['id'],resolution='exchange')[0]
    assert engine.apply_serious_injury(a.id,outcome)[0]
    ids=[r['id'] for r in engine.post.pending_follow_ups]
    assert len(ids)==len(set(ids))

    target=next(r for r in engine.post.pending_follow_ups if r.get('warrior_id')==a.id)
    assert engine.resolve_captured(target['id'],resolution='lost')[0]
    assert a not in engine.campaign.warriors and b in engine.campaign.warriors
    assert len(engine.post.pending_follow_ups)==1
    assert engine.post.pending_follow_ups[0]['warrior_id']==b.id

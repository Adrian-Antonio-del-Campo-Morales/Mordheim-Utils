"""Cross-band and seeded sequence checks for campaign invariants."""
import copy
import random
from collections import Counter
import pytest
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.state import make_draft_state
from mordheim_campaign.persistence import save_campaign, load_campaign

@pytest.fixture(scope='module')
def port():
    return KnowledgePort()

def check(c):
    campaign = c.state.campaign
    assert len({w.id for w in campaign.warriors}) == len(campaign.warriors)
    carried = Counter()
    for warrior in campaign.warriors:
        assert warrior.quantity > 0
        for item in warrior.equipment:
            assert item.quantity >= 0
            if item.transferable and item.acquisition != "fixed":
                carried[item.item_id] += item.quantity
    for item in campaign.inventory:
        assert item.owned == item.equipped + item.stash
        assert min(item.owned, item.equipped, item.stash) >= 0
        assert item.equipped == carried.pop(item.id, 0), item.id
        assert len(item.acquisition_costs) in (0, item.owned)
    assert not +carried, carried
    assert campaign.draft_treasury >= 0

def test_all_bands_purchase_refund_save_and_undo(port, tmp_path):
    for option in port.options():
        c = AppController(make_draft_state(port, option.band_id), port=port)
        check(c)
        for warrior in list(c.state.campaign.warriors):
            for offer in c.draft_equipment_offers(warrior.id):
                if not isinstance(offer.cost, int):
                    continue
                before = copy.deepcopy(c.state)
                result = c.perform_undoable('matrix buy', lambda: c.buy_draft_equipment(warrior.id, offer.item_id))
                check(c)
                if result[0]:
                    assert c.undo()[0]
                    assert c.state == before, (option.band_id, offer.item_id)
                else:
                    assert c.state == before
        restored = load_campaign(save_campaign(tmp_path/'band.mordheim', c.state))
        assert restored.campaign == c.state.campaign, option.band_id

@pytest.mark.parametrize('seed', range(20))
def test_seeded_draft_sequences(port, tmp_path, seed):
    rng = random.Random(seed)
    c = AppController(make_draft_state(port, 'sisters-of-sigmar'), port=port)
    for step in range(80):
        warrior = rng.choice(c.state.campaign.warriors)
        action = rng.randrange(7)
        if action == 0:
            offers = [o for o in c.draft_equipment_offers(warrior.id) if isinstance(o.cost,int)]
            if offers:
                offer = rng.choice(offers)
                c.perform_undoable('buy', lambda: c.buy_draft_equipment(warrior.id, offer.item_id))
        elif action == 1 and warrior.kind == 'henchman':
            c.perform_undoable('resize', lambda: c.adjust_draft_group(warrior.id, rng.choice([-1,1])))
        elif action == 2:
            items = [i for i in warrior.equipment if i.transferable]
            if items:
                item = rng.choice(items)
                c.perform_undoable('return', lambda: c.return_equipped_item(item.item_id,warrior.id))
        elif action == 3:
            stock = [i for i in c.state.campaign.inventory if i.stash]
            if stock:
                item = rng.choice(stock)
                c.perform_undoable('assign', lambda: c.assign_stash_item(item.id,warrior.id))
        elif action == 4:
            c.undo()
        elif action == 5:
            restored = load_campaign(save_campaign(tmp_path/'sequence.mordheim', c.state))
            assert restored.campaign == c.state.campaign
            c.replace_state(restored)
        else:
            items = [i for i in warrior.equipment if i.acquisition == 'purchase']
            if items:
                item = rng.choice(items)
                c.perform_undoable('refund', lambda: c.remove_draft_equipment(warrior.id,item.item_id))
        check(c)

@pytest.mark.parametrize('seed', range(20))
def test_seeded_postbattle_sequences(port, tmp_path, seed):
    rng = random.Random(seed)
    c = AppController(make_draft_state(port, 'sisters-of-sigmar'), port=port)
    c.commit_initial_warband()
    scenario, name, _ = port.scenario_options()[0]
    assert c.record_battle(scenario_id=scenario, scenario_name=name, opponent='Sequence', result='Draw', xp_delta=0, casualties=0)[0]
    c.state.campaign.pending_post_battle.gold_delta += 1000
    for step in range(100):
        engine = c.post_battle_engine()
        groups = [w for w in c.state.campaign.warriors if w.kind == 'henchman']
        if not groups:
            engine.recruit_band_profile('sigmarite-sister')
            groups = [w for w in c.state.campaign.warriors if w.kind == 'henchman']
        group = rng.choice(groups)
        action = rng.randrange(8)
        before = copy.deepcopy(c.state)
        if action == 0:
            result = c.perform_undoable('buy', lambda: engine.buy_item('hammer', rng.randint(1,5), 3))
        elif action == 1:
            result = c.perform_undoable('assign', lambda: c.assign_stash_item('hammer',group.id))
        elif action == 2:
            result = c.perform_undoable('return', lambda: c.return_equipped_item('hammer',group.id))
        elif action == 3:
            result = c.perform_undoable('recruit', lambda: engine.add_member_to_group(group.id))
        elif action == 4:
            result = c.perform_undoable('dismiss', lambda: engine.dismiss_warrior(group.id, one_member=True))
        elif action == 5:
            result = c.perform_undoable('sell', lambda: engine.sell_item('hammer',1))
        elif action == 6:
            restored = load_campaign(save_campaign(tmp_path/'post.mordheim',c.state))
            assert restored.campaign == c.state.campaign
            c.replace_state(restored)
            result = None
        else:
            c.undo()
            result = None
        if result and not result[0]:
            assert c.state == before
        check(c)


def test_all_bands_commit_fixed_inventory_and_reload(port, tmp_path):
    for option in port.options():
        c = AppController(make_draft_state(port, option.band_id), port=port)
        c.commit_initial_warband()
        assert not c.state.campaign.is_draft, option.band_id
        carried = Counter()
        for w in c.state.campaign.warriors:
            for item in w.equipment:
                if item.transferable:
                    carried[item.item_id] += item.quantity
        stock = {i.id:i.equipped for i in c.state.campaign.inventory}
        assert dict(+carried) == {k:v for k,v in stock.items() if v}, option.band_id
        restored = load_campaign(save_campaign(tmp_path/'committed.mordheim', c.state))
        assert restored.campaign == c.state.campaign

def test_recruited_fixed_equipment_is_registered(port):
    for option in port.options():
        profiles = [p for p in port.profiles(option.collection,option.band_id) if p.fixed_equipment]
        if not profiles:
            continue
        c = AppController(make_draft_state(port,option.band_id),port=port)
        c.commit_initial_warband()
        scenario,name,_ = port.scenario_options()[0]
        assert c.record_battle(scenario_id=scenario,scenario_name=name,opponent='Inventory',result='Draw',xp_delta=0,casualties=0)[0]
        engine = c.post_battle_engine()
        engine.campaign.warriors.clear()
        engine.campaign.inventory.clear()
        for profile in profiles:
            ok,message = engine.recruit_band_profile(profile.profile_id,free=True)
            if not ok:
                continue
            warrior = engine.campaign.warriors[-1]
            for item in warrior.equipment:
                if item.transferable:
                    stock = next((i for i in engine.campaign.inventory if i.id == item.item_id),None)
                    assert stock is not None, (option.band_id,profile.profile_id,item.item_id)
                    assert stock.equipped >= item.quantity

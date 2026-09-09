"""Malformed save boundaries: fail as CampaignFileError."""
import json
import pytest
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.application.state import make_draft_state,InventoryItemVM
from mordheim_campaign.persistence import save_campaign,load_campaign,CampaignFileError

@pytest.fixture(scope='module')
def port(): return KnowledgePort()

@pytest.mark.parametrize('field,value',[
 ('owned',-1),('equipped',-1),('stash',-1),('owned',5),('acquisition_costs',[-1]),
 ('owned',1.5),('owned',True),('stash',[]),('acquisition_costs',[2.5]),
])
def test_invalid_inventory_rejected(port,tmp_path,field,value):
    state=make_draft_state(port,'sisters-of-sigmar')
    state.campaign.inventory=[InventoryItemVM('hammer','Hammer','Weapon',1,0,1,3)]
    path=save_campaign(tmp_path/'bad.mordheim',state)
    payload=json.loads(path.read_text(encoding='utf-8'))
    payload['campaign']['inventory'][0][field]=value
    path.write_text(json.dumps(payload),encoding='utf-8')
    with pytest.raises(CampaignFileError):load_campaign(path)

@pytest.mark.parametrize('value',['broken',None,-1,[],1.5,True])
@pytest.mark.parametrize('historic',[False,True])
def test_invalid_equipment_quantity_rejected(port,tmp_path,value,historic):
    state=make_draft_state(port,'sisters-of-sigmar')
    path=save_campaign(tmp_path/'bad.mordheim',state)
    payload=json.loads(path.read_text(encoding='utf-8'))
    if historic:
        from copy import deepcopy
        payload['campaign']['states']=[{'number':0,'roster':deepcopy(payload['campaign']['warriors'])}]
        payload['campaign']['states'][0]['roster'][0]['equipment'][0]['quantity']=value
    else:
        payload['campaign']['warriors'][0]['equipment'][0]['quantity']=value
    path.write_text(json.dumps(payload),encoding='utf-8')
    with pytest.raises(CampaignFileError):load_campaign(path)

def test_nonfinite_number_is_controlled_error(port,tmp_path):
    state=make_draft_state(port,'sisters-of-sigmar')
    path=save_campaign(tmp_path/'bad.mordheim',state)
    payload=json.loads(path.read_text(encoding='utf-8'))
    payload['campaign']['starting_gold']=float('inf')
    path.write_text(json.dumps(payload),encoding='utf-8')
    with pytest.raises(CampaignFileError):load_campaign(path)

@pytest.mark.parametrize('case',['duplicate_followup','orphan_advance','duplicate_advance'])
def test_invalid_pending_references_are_rejected(port,tmp_path,case):
    from mordheim_campaign.application.state import make_example_state
    state=make_example_state(port)
    post=state.campaign.pending_post_battle
    if case=='duplicate_followup':
        post.pending_follow_ups=[{'id':'same','step':0,'type':'prisoner','warrior_id':'matriarch'},
                                 {'id':'same','step':0,'type':'prisoner','warrior_id':'veriet'}]
    else:
        advance={'warrior_id':'absent' if case=='orphan_advance' else 'matriarch','threshold':20,'table':'hero','committed':False}
        post.pending_advances=[advance] if case=='orphan_advance' else [advance,dict(advance)]
    path=save_campaign(tmp_path/'pending.mordheim',state)
    with pytest.raises(CampaignFileError):load_campaign(path)

@pytest.mark.parametrize('value',[1.5,True,'2'])
def test_member_count_is_not_silently_coerced(port,tmp_path,value):
    state=make_draft_state(port,'sisters-of-sigmar')
    path=save_campaign(tmp_path/'members.mordheim',state)
    payload=json.loads(path.read_text(encoding='utf-8'))
    payload['campaign']['warriors'][0]['quantity']=value
    path.write_text(json.dumps(payload),encoding='utf-8')
    with pytest.raises(CampaignFileError):load_campaign(path)

def test_completed_advance_for_lost_warrior_is_valid_history(port,tmp_path):
    from mordheim_campaign.application.state import make_example_state
    state=make_example_state(port)
    state.campaign.pending_post_battle.pending_advances=[{'warrior_id':'lost-warrior','threshold':20,'table':'hero','committed':True}]
    restored=load_campaign(save_campaign(tmp_path/'history.mordheim',state))
    assert restored.campaign==state.campaign

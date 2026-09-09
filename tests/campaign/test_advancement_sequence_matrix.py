"""Advancement dice, persistence and decision validation."""
import copy
import pytest
from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.knowledge_port import KnowledgePort
from mordheim_campaign.domain.builders import make_example_state
from mordheim_campaign.persistence import save_campaign,load_campaign

@pytest.fixture(scope='module')
def port(): return KnowledgePort()

@pytest.mark.parametrize('warrior_id',['matriarch','novices'])
@pytest.mark.parametrize('roll',range(2,13))
@pytest.mark.parametrize('subroll',range(1,7))
def test_advancement_rolls_roundtrip_and_undo(port,tmp_path,warrior_id,roll,subroll):
    c=AppController(make_example_state(port),port=port)
    engine=c.post_battle_engine()
    engine.add_xp(warrior_id,4)
    before=copy.deepcopy(c.state)
    result=c.perform_undoable('roll',lambda:engine.resolve_pending_advance(warrior_id,roll,subroll=subroll))
    assert result[0],result
    after=copy.deepcopy(c.state)
    restored=load_campaign(save_campaign(tmp_path/'advance.mordheim',c.state))
    assert restored.campaign==c.state.campaign
    assert c.undo()[0]
    assert c.state==before
    assert c.perform_undoable('roll',lambda:c.post_battle_engine().resolve_pending_advance(warrior_id,roll,subroll=subroll))[0]
    assert c.state==after

@pytest.mark.parametrize('choice',['choose_skill','generate_spell','duplicate_spell','promote_henchman'])
def test_skill_choice_rejected_for_characteristic_roll(port,choice):
    c=AppController(make_example_state(port),port=port)
    engine=c.post_battle_engine()
    engine.sync_pending_advances()
    assert engine.resolve_pending_advance('matriarch',7)[0]
    before=copy.deepcopy(c.state)
    result=c.perform_undoable('choice',lambda:engine.commit_pending_advance('matriarch',option_kind=choice,skill_name='Weapons Training'))
    assert not result[0]
    assert result[1] == "This choice is not offered by the resolved advance."
    assert c.state==before


@pytest.mark.parametrize('quantity',range(1,6))
@pytest.mark.parametrize('copies',[1,2])
@pytest.mark.parametrize('threshold',[8,16])
def test_promotion_selects_exact_threshold_and_preserves_equipment(port,tmp_path,quantity,copies,threshold):
    from mordheim_campaign.domain.models import EquipmentEntryVM, InventoryItemVM
    c=AppController(make_example_state(port),port=port)
    engine=c.post_battle_engine()
    group=next(w for w in c.state.campaign.warriors if w.id=='novices')
    group.quantity=quantity
    group.equipment=[EquipmentEntryVM('hammer','Hammer',quantity*copies,'purchase',3,True,True)]
    c.state.campaign.inventory=[InventoryItemVM('hammer','Hammer','Weapon',quantity*copies,quantity*copies,0,3)]
    engine.add_xp(group.id,12)
    for rung in (8,16):
        assert engine.resolve_pending_advance(group.id,10,threshold=rung)[0]
    before=copy.deepcopy(c.state)
    assert c.perform_undoable('promote',lambda:engine.commit_pending_advance(group.id,option_kind='promote_henchman',threshold=threshold))[0]
    hero=next(w for w in c.state.campaign.warriors if '#promoted' in w.id)
    assert hero.equipment[0].quantity==copies
    if quantity>1:
        assert group.quantity==quantity-1
        assert group.equipment[0].quantity==(quantity-1)*copies
        assert engine.post.pending_advance_for(group.id,threshold)['roll_total'] is None
        other=16 if threshold==8 else 8
        assert engine.post.pending_advance_for(group.id,other)['roll_total']==10
    assert load_campaign(save_campaign(tmp_path/'promotion.mordheim',c.state)).campaign==c.state.campaign
    assert c.undo()[0]
    assert c.state==before

def test_all_profiles_retain_canonical_starting_skills(port):
    from mordheim_campaign.domain.builders import warrior_vm
    for option in port.options():
        for profile in port.profiles(option.collection,option.band_id):
            warrior=warrior_vm(port,profile)
            assert set(profile.starting_skills)<=set(warrior.skills),(option.band_id,profile.profile_id,profile.starting_skills)

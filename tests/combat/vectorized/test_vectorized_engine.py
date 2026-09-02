"""Regresiones del motor vectorizado."""
from __future__ import annotations

from dataclasses import replace
from mordheim_combat_lab.combat.vectorized import simulate_duel
from mordheim_combat_lab.construction.compiler import compile_fighter
from mordheim_combat_lab.domain.models import Characteristics
from mordheim_combat_lab.domain.models import DuelRequest
from mordheim_combat_lab.domain.models import EffectSet
from mordheim_combat_lab.domain.models import FighterBuild
from mordheim_combat_lab.domain.models import SimulationCancelled
import numpy as np
import pytest as pytest
from threading import Event


class FixedRng:
    def __init__(self, *values): self.values=list(values)
    def integers(self, low, high=None, size=None, dtype=None):
        value=self.values.pop(0)
        result=np.asarray(value if np.ndim(value) else np.full(size or 1,value),dtype=dtype)
        return result if size is not None else result.item()


def fighter(**changes):
    values=dict(weapon_skill=3,strength=3,toughness=3,wounds=1,initiative=3,attacks=1);values.update(changes)
    return compile_fighter(FighterBuild("mordheim",Characteristics(**values)))


def test_seeded_duel_is_reproducible_and_counts_are_complete():
    request=DuelRequest(fighter(),fighter(),10_000,seed=91,batch_size=2_000)
    first=simulate_duel(request);second=simulate_duel(request)
    assert first==second
    assert first.first_wins+first.second_wins+first.unresolved==10_000
    assert pytest.approx(first.first_win_rate+first.second_win_rate+first.unresolved_rate)==100


def test_symmetric_duel_is_statistically_symmetric_across_chunk_sizes():
    unit=fighter()
    small=simulate_duel(DuelRequest(unit,unit,20_000,seed=7,batch_size=1_000))
    large=simulate_duel(DuelRequest(unit,unit,20_000,seed=7,batch_size=20_000))
    assert abs(small.first_win_rate-small.second_win_rate)<2
    assert abs(large.first_win_rate-large.second_win_rate)<2
    assert abs(small.first_win_rate-large.first_win_rate)<2


def test_higher_strength_has_expected_advantage():
    strong=simulate_duel(DuelRequest(fighter(strength=5),fighter(),20_000,seed=5))
    assert strong.first_win_rate>strong.second_win_rate


def test_shield_does_not_grant_an_attack_but_second_weapon_does():
    from mordheim_combat_lab.combat.vectorized import attack_count
    import numpy as np
    stats=Characteristics(3,3,3,1,3,1)
    shield=compile_fighter(FighterBuild("mordheim",stats,off_hand_id="defence.shield"))
    dagger=compile_fighter(FighterBuild("mordheim",stats,off_hand_id="weapon.dagger"))
    charging=np.zeros(1,dtype=bool)
    assert attack_count(shield,charging)[0]==1
    assert attack_count(dagger,charging)[0]==2


def test_conditional_hit_rerolls_and_berserker_only_apply_while_charging():
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import _prepare_weapon_attack
    stats=Characteristics(3,3,3,1,3,1)
    attacker=compile_fighter(FighterBuild(
        "mordheim",stats,skill_ids=("skill.berserker","skill.infallible")))
    defender=compile_fighter(FighterBuild("mordheim",stats))
    attacker_state=_new_state(attacker,2,np.random.default_rng(1))
    defender_state=_new_state(defender,2,np.random.default_rng(2))
    # A 3 misses at the normal 4+ target but hits at the 3+ Berserker target.
    prepared=_prepare_weapon_attack(attacker,defender,attacker.main_weapon,np.array([0,1]),
                                    np.array([True,False]),attacker_state,defender_state,
                                    FixedRng([3,3],6),True)
    assert prepared.hit_rows.tolist()==[0]


def test_sweep_replaces_all_attacks_with_one_initiative_test():
    from mordheim_combat_lab.combat.vectorized import attack_count
    attacker=compile_fighter(FighterBuild(
        "mordheim",Characteristics(3,3,3,1,3,4),main_weapon_id="weapon.double-handed-weapon",
        skill_ids=("skill.sweep",)))
    assert attack_count(attacker,np.zeros(3,dtype=bool)).tolist()==[1,1,1]


def test_cancellation_is_checked_between_batches():
    event=Event();event.set()
    with pytest.raises(SimulationCancelled):simulate_duel(DuelRequest(fighter(),fighter(),100,cancel_event=event))


def test_invalid_request_and_result_are_rejected():
    from mordheim_combat_lab.domain.models import DuelResult
    with pytest.raises(ValueError):DuelRequest(fighter(),fighter(),0)
    with pytest.raises(ValueError):DuelResult(1,1,1,2)


def test_armour_poison_and_regeneration_change_aggregate_outcomes():
    stats=Characteristics(4,4,3,2,4,2)
    plain=compile_fighter(FighterBuild("mordheim",stats))
    armoured=compile_fighter(FighterBuild("mordheim",stats,armour_id="armour.gromril-armour",off_hand_id="defence.shield"))
    poisoned=compile_fighter(FighterBuild("mordheim",stats,main_poison_id="poison.bloodroot"))
    regenerating=compile_fighter(FighterBuild("mordheim",stats,skill_ids=("skill.regeneration",)))
    vs_plain=simulate_duel(DuelRequest(plain,plain,20_000,seed=31))
    vs_armour=simulate_duel(DuelRequest(plain,armoured,20_000,seed=31))
    with_poison=simulate_duel(DuelRequest(poisoned,plain,20_000,seed=31))
    vs_regeneration=simulate_duel(DuelRequest(plain,regenerating,20_000,seed=31))
    assert vs_armour.first_win_rate<vs_plain.first_win_rate
    assert with_poison.first_win_rate>vs_plain.first_win_rate
    assert vs_regeneration.first_win_rate<vs_plain.first_win_rate


def test_wound_modifier_improves_the_wound_roll_target():
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import _resolve_weapon
    from mordheim_combat_lab.domain.models import EffectSet
    defender=fighter()
    plain=replace(fighter(),main_weapon=EffectSet(automatic_hit=True))
    improved=replace(fighter(),main_weapon=EffectSet(automatic_hit=True,wound_modifier=1))
    plain_attacker_state=_new_state(plain,1,np.random.default_rng(1))
    improved_attacker_state=_new_state(improved,1,np.random.default_rng(1))
    plain_defender_state=_new_state(defender,1,np.random.default_rng(2))
    improved_defender_state=_new_state(defender,1,np.random.default_rng(2))
    active=np.array([0]); charging=np.zeros(1,dtype=bool)
    _resolve_weapon(plain,defender,plain.main_weapon,active,charging,plain_attacker_state,plain_defender_state,FixedRng(3),False)
    _resolve_weapon(improved,defender,improved.main_weapon,active,charging,improved_attacker_state,improved_defender_state,FixedRng(3,1,1),False)
    assert plain_defender_state.wounds[0]==1
    assert improved_defender_state.wounds[0]==0


def test_scorpion_tail_loses_strength_against_poison_immunity():
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import _prepare_weapon_attack
    attacker=replace(fighter(),main_weapon=EffectSet(tags=("rule.scorpion-tail",),fixed_strength=5))
    plain=fighter()
    immune=replace(fighter(),global_effects=EffectSet(poison_immunity=True))
    active=np.array([0]);charging=np.zeros(1,dtype=bool)
    normal=_prepare_weapon_attack(attacker,plain,attacker.main_weapon,active,charging,
        _new_state(attacker,1,np.random.default_rng(1)),_new_state(plain,1,np.random.default_rng(2)),FixedRng(6),False)
    resisted=_prepare_weapon_attack(attacker,immune,attacker.main_weapon,active,charging,
        _new_state(attacker,1,np.random.default_rng(1)),_new_state(immune,1,np.random.default_rng(2)),FixedRng(6),False)
    assert normal.strength.tolist()==[5]
    assert resisted.strength.tolist()==[2]


def test_acid_blood_retaliates_once_per_wound_lost():
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import _resolve_weapon
    attacker=replace(fighter(wounds=3),main_weapon=EffectSet(automatic_hit=True,fixed_strength=10))
    defender=replace(fighter(wounds=2),global_effects=EffectSet(tags=("acid_blood",)))
    attacker_state=_new_state(attacker,1,np.random.default_rng(1))
    defender_state=_new_state(defender,1,np.random.default_rng(2))
    _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([0]),np.zeros(1,dtype=bool),
                    attacker_state,defender_state,FixedRng(2,1,6,1),False)
    assert defender_state.wounds[0]==1
    assert attacker_state.wounds[0]==2


def test_spines_resolve_simultaneously_at_the_start_of_the_phase():
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import _resolve_spines
    spined=replace(fighter(),global_effects=EffectSet(tags=("spines",)))
    plain=fighter(wounds=2)
    first_state=_new_state(spined,1,np.random.default_rng(1))
    second_state=_new_state(plain,1,np.random.default_rng(2))
    charging=np.zeros(1,dtype=bool)
    _resolve_spines(spined,plain,np.array([0]),charging,charging,
                    first_state,second_state,FixedRng(6,1))
    assert second_state.wounds[0]==1


@pytest.mark.parametrize("protection", (EffectSet(ward_save=2), EffectSet(regeneration_save=2)))
def test_profile_two_is_not_out_when_a_special_save_ignores_the_wound(protection):
    from mordheim_combat_lab.combat.vectorized import STANDING
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import _resolve_weapon
    from mordheim_combat_lab.domain.models import EffectSet
    attacker=replace(fighter(),main_weapon=EffectSet(automatic_hit=True))
    defender=replace(fighter(),global_effects=protection,injury_profile=2)
    attacker_state=_new_state(attacker,1,np.random.default_rng(1))
    defender_state=_new_state(defender,1,np.random.default_rng(2))
    _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([0]),np.zeros(1,dtype=bool),
                    attacker_state,defender_state,FixedRng(6,6,2),False)
    assert defender_state.condition[0]==STANDING
    assert defender_state.wounds[0]==1


def test_summoned_bat_loses_two_wounds_before_removal_without_injury_dice():
    from mordheim_combat_lab.combat.vectorized import _new_state, _resolve_weapon, OUT, STANDING

    class NonemptyDice(FixedRng):
        def integers(self, low, high=None, size=None, dtype=None):
            if size == 0:
                return np.empty(0, dtype=dtype or np.int64)
            return super().integers(low, high, size, dtype)

    attacker = replace(fighter(), main_weapon=EffectSet(automatic_hit=True))
    defender = compile_fighter(FighterBuild(
        "mordheim", collection="trollheim", band_id="chaos-streets-undead-bloodlines",
        profile_id="vampire-bat",
    ))
    assert defender.injury_profile == 4
    attacker_state = _new_state(attacker, 1, np.random.default_rng(1))
    defender_state = _new_state(defender, 1, np.random.default_rng(2))
    for remaining, condition in ((1, STANDING), (0, OUT)):
        dice = NonemptyDice(5)  # Only the non-critical wound roll; never an injury roll.
        _resolve_weapon(
            attacker, defender, attacker.main_weapon, np.array([0]), np.zeros(1, dtype=bool),
            attacker_state, defender_state, dice, False,
        )
        assert dice.values == []
        assert defender_state.wounds[0] == remaining
        assert defender_state.condition[0] == condition


def test_charge_conditions_are_isolated_per_vector_row():
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import _resolve_weapon
    from mordheim_combat_lab.domain.models import EffectSet
    base=fighter()
    attacker=replace(base,main_weapon=EffectSet(tags=("weapon.chained-squig",)),global_effects=EffectSet(tags=("skill.infallible",)))
    defender=fighter()
    attacker_state=_new_state(attacker,2,np.random.default_rng(1));defender_state=_new_state(defender,2,np.random.default_rng(2))
    _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([0,1]),np.array([True,False]),attacker_state,defender_state,FixedRng([1,1],6,1),True)
    assert defender_state.entangled.tolist()==[True,False]


def test_parry_is_one_attempt_per_phase_and_respects_strength_limit():
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import _parry_hits
    defender=compile_fighter(FighterBuild("mordheim",Characteristics(3,3,3,1,3,1),main_weapon_id="weapon.sword"))
    state=_new_state(defender,2,np.random.default_rng(1))
    effect=defender.main_weapon
    remaining,blocked=_parry_hits(defender,effect,np.array([0]),np.array([4]),np.array([3]),state,FixedRng(6))
    assert remaining.size==0 and blocked.tolist()==[0]
    remaining,blocked=_parry_hits(defender,effect,np.array([0]),np.array([2]),np.array([3]),state,FixedRng(6))
    assert remaining.tolist()==[0] and blocked.size==0
    remaining,blocked=_parry_hits(defender,effect,np.array([1]),np.array([2]),np.array([6]),state,FixedRng(6))
    assert remaining.tolist()==[1] and blocked.size==0
    fresh=_new_state(defender,1,np.random.default_rng(2))
    remaining,blocked=_parry_hits(defender,effect,np.array([0,0]),np.array([3,5]),np.array([3,3]),fresh,FixedRng([6,6]))
    assert remaining.size==1 and blocked.size==1


def test_unbeatable_warrior_parries_twice_with_two_parry_weapons():
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import _parry_hits
    defender=compile_fighter(FighterBuild(
        "mordheim",Characteristics(3,3,3,1,3,1),main_weapon_id="weapon.sword",
        off_hand_id="weapon.sword",skill_ids=("skill.unbeatable-warrior",)))
    state=_new_state(defender,1,np.random.default_rng(1))
    remaining,blocked=_parry_hits(defender,defender.main_weapon,np.array([0,0]),
                                  np.array([3,4]),np.array([3,3]),state,FixedRng([6,6]))
    assert remaining.size==0 and blocked.tolist()==[0,0]


def test_parry_selects_highest_hit_across_main_and_off_hand(monkeypatch):
    import mordheim_combat_lab.combat.vectorized as engine
    attacker=compile_fighter(FighterBuild("mordheim",Characteristics(3,3,3,1,3,1),main_weapon_id="weapon.mace",off_hand_id="weapon.dagger"))
    defender=compile_fighter(FighterBuild("mordheim",Characteristics(3,3,3,1,3,1),main_weapon_id="weapon.sword"))
    attacker_state=engine._new_state(attacker,1,np.random.default_rng(1));defender_state=engine._new_state(defender,1,np.random.default_rng(2))
    def prepare(_attacker,_defender,weapon,active,_charging,_attacker_state,_defender_state,_rng,_first_round):
        if active.size==0:return None
        roll=3 if engine.has(weapon,"weapon.mace") else 5
        return engine.PreparedAttack(
            weapon,weapon,active,np.array([3]),np.array([3]),np.array([4]),
            np.array([roll],dtype=np.int8),active,np.array([False]),
        )
    selected=[]
    def capture(*args,**kwargs): selected.append((kwargs["prepared"].rolls[0],kwargs["parry_rows"].tolist()))
    monkeypatch.setattr(engine,"_prepare_weapon_attack",prepare);monkeypatch.setattr(engine,"_resolve_weapon",capture)
    engine.resolve_attacks(attacker,defender,np.array([0]),np.array([2]),np.array([False]),attacker_state,defender_state,np.random.default_rng(3),False)
    assert selected==[(3,[]),(5,[0])]


def test_only_one_critical_can_be_claimed_per_row_and_phase():
    from mordheim_combat_lab.combat.vectorized import _claim_criticals
    from mordheim_combat_lab.combat.vectorized import _new_state
    unit=fighter();state=_new_state(unit,2,np.random.default_rng(1))
    assert _claim_criticals(np.array([True,True]),np.array([0,1]),state).tolist()==[True,True]
    assert _claim_criticals(np.array([True,True]),np.array([0,1]),state).tolist()==[False,False]


def test_incapacitated_states_are_resolved_separately():
    from mordheim_combat_lab.combat.vectorized import KNOCKED_DOWN
    from mordheim_combat_lab.combat.vectorized import OUT
    from mordheim_combat_lab.combat.vectorized import STUNNED
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import _resolve_weapon
    from mordheim_combat_lab.domain.models import EffectSet
    attacker=replace(fighter(),main_weapon=EffectSet(automatic_hit=True))
    defender=fighter(wounds=2)
    attacker_state=_new_state(attacker,3,np.random.default_rng(1));defender_state=_new_state(defender,3,np.random.default_rng(2))
    defender_state.condition[:]=[KNOCKED_DOWN,KNOCKED_DOWN,STUNNED]
    _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([0]),np.zeros(3,dtype=bool),attacker_state,defender_state,FixedRng(1),False)
    _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([1]),np.zeros(3,dtype=bool),attacker_state,defender_state,FixedRng(6,6),False)
    _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([2]),np.zeros(3,dtype=bool),attacker_state,defender_state,FixedRng(),False)
    assert defender_state.condition.tolist()==[KNOCKED_DOWN,OUT,OUT]


def test_random_profile_characteristics_are_rolled_per_simulation_row():
    from mordheim_combat_lab.combat.vectorized import _new_state
    condemned=compile_fighter(FighterBuild("mordheim",band_id="marauders-of-chaos",profile_id="condemned"))
    spawn=compile_fighter(FighterBuild("mordheim",band_id="marauders-of-chaos",profile_id="spawn-of-chaos"))
    condemned_state=_new_state(condemned,200,np.random.default_rng(41));spawn_state=_new_state(spawn,200,np.random.default_rng(42))
    assert condemned_state.weapon_skill.min()>=1 and condemned_state.weapon_skill.max()<=6
    assert condemned_state.strength.min()>=1 and condemned_state.strength.max()<=6
    assert condemned_state.toughness.min()>=1 and condemned_state.toughness.max()<=6
    assert condemned_state.attacks.min()>=1 and condemned_state.attacks.max()<=3
    assert spawn_state.attacks.min()>=2 and spawn_state.attacks.max()<=7
    assert np.unique(condemned_state.weapon_skill).size>1 and np.unique(spawn_state.attacks).size>1


def test_lustria_scaly_skin_keeps_its_shared_six_plus_floor():
    from mordheim_combat_lab.combat.vectorized import STANDING
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import _resolve_weapon
    from mordheim_combat_lab.domain.models import EffectSet
    attacker=replace(fighter(),main_weapon=EffectSet(fixed_strength=10,automatic_hit=True))
    defender=compile_fighter(FighterBuild(
        "mordheim",band_id="lustria-lizardmen",profile_id="saurus-totem-warrior",
        collection="trollheim"))
    attacker_state=_new_state(attacker,1,np.random.default_rng(1))
    defender_state=_new_state(defender,1,np.random.default_rng(2))
    _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([0]),np.zeros(1,dtype=bool),
                    attacker_state,defender_state,FixedRng(5,6),False)
    assert defender_state.condition[0]==STANDING and defender_state.wounds[0]==1


def test_shared_hard_to_kill_and_fragile_injury_profiles():
    from mordheim_combat_lab.combat.vectorized import STUNNED
    from mordheim_combat_lab.combat.vectorized import OUT
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import _resolve_weapon
    from mordheim_combat_lab.domain.models import EffectSet
    attacker=replace(fighter(),main_weapon=EffectSet(fixed_strength=10,automatic_hit=True))
    hard=compile_fighter(FighterBuild(
        "mordheim",band_id="chaos-streets-dwarf-treasure-hunters",profile_id="beardlings",
        collection="trollheim"))
    hard=replace(hard,main_weapon=EffectSet())
    fragile=compile_fighter(FighterBuild(
        "mordheim",band_id="khemri-necromancers",profile_id="nehekharan-vultures",
        collection="trollheim"))
    # Written Hard to Kill table: 1-2 Knocked Down, 3-5 Stunned, 6 Out.
    for defender,injury_roll,expected in ((hard,3,STUNNED),(fragile,4,OUT)):
        attacker_state=_new_state(attacker,1,np.random.default_rng(3))
        defender_state=_new_state(defender,1,np.random.default_rng(4))
        _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([0]),np.zeros(1,dtype=bool),
                        attacker_state,defender_state,FixedRng(5,injury_roll,injury_roll),False)
        assert defender_state.condition[0]==expected


def test_skink_hunter_priority_distinguishes_first_round_from_always():
    from mordheim_combat_lab.combat.vectorized import priority
    skink=replace(fighter(),global_effects=EffectSet(tags=("species.skink",)))
    first_round_only=replace(fighter(),global_effects=EffectSet(tags=("mechanic.strike-first-vs-skinks-first-round",)))
    always=replace(fighter(),global_effects=EffectSet(tags=("mechanic.strike-first-vs-skinks-always",)))
    flags=np.zeros(1,dtype=bool)
    assert priority(first_round_only,skink,True,flags,flags,flags)[0]==20
    assert priority(first_round_only,skink,False,flags,flags,flags)[0]==0
    assert priority(always,skink,False,flags,flags,flags)[0]==20


def test_master_of_blades_rerolls_only_with_two_dwarf_axes():
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import _parry_hits
    axe=EffectSet(tags=("weapon.dwarf-axe",),parry=True)
    core=replace(fighter(),main_weapon=axe,off_hand=axe,global_effects=EffectSet(tags=("skill.unbeatable-warrior",)))
    master=replace(core,global_effects=EffectSet(tags=("skill.unbeatable-warrior","skill.sword-master")))
    core_state=_new_state(core,1,np.random.default_rng(1))
    master_state=_new_state(master,1,np.random.default_rng(1))
    remaining,_=_parry_hits(core,axe,np.array([0]),np.array([4]),np.array([3]),core_state,FixedRng(3))
    rerolled,_=_parry_hits(master,axe,np.array([0]),np.array([4]),np.array([3]),master_state,FixedRng(3,6))
    assert remaining.tolist()==[0]
    assert rerolled.size==0


def test_scarecrow_catches_fire_on_three_plus_instead_of_brazier_five_plus():
    from mordheim_combat_lab.combat.vectorized import _new_state
    from mordheim_combat_lab.combat.vectorized import _resolve_weapon
    brazier=EffectSet(tags=("weapon.brazier-iron","attack.fire"),automatic_hit=True,ignition_threshold=5)
    attacker=replace(fighter(),main_weapon=brazier)
    ordinary=fighter(wounds=2)
    scarecrow=replace(ordinary,global_effects=EffectSet(tags=("flammable",),caught_fire_threshold=3))
    ordinary_state=_new_state(ordinary,1,np.random.default_rng(1));scarecrow_state=_new_state(scarecrow,1,np.random.default_rng(1))
    attacker_state=_new_state(attacker,1,np.random.default_rng(2))
    _resolve_weapon(attacker,ordinary,brazier,np.array([0]),np.zeros(1,dtype=bool),attacker_state,ordinary_state,FixedRng(4,1),False)
    attacker_state=_new_state(attacker,1,np.random.default_rng(2))
    _resolve_weapon(attacker,scarecrow,brazier,np.array([0]),np.zeros(1,dtype=bool),attacker_state,scarecrow_state,FixedRng(4,1),False)
    assert not ordinary_state.on_fire[0]
    assert scarecrow_state.on_fire[0]

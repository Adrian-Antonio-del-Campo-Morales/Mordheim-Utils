"""Game-rule regressions of the vectorized engine."""
from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

from mordheim_combat.vectorized import simulate_duel
from mordheim_core.models import DuelRequest
from mordheim_core.models import EffectSet

class FixedRng:
    def __init__(self, *values): self.values=list(values)
    def integers(self, low, high=None, size=None, dtype=None):
        value=self.values.pop(0)
        result=np.asarray(value if np.ndim(value) else np.full(size or 1,value),dtype=dtype)
        return result if size is not None else result.item()

def test_higher_strength_has_expected_advantage(vector_case):
    case=vector_case("test_vectorized_engine/test_higher_strength_has_expected_advantage-0-0")
    strong=simulate_duel(DuelRequest(case.first,case.second,20_000,seed=5))
    assert strong.first_win_rate>strong.second_win_rate

def test_shield_does_not_grant_an_attack_but_second_weapon_does(vector_case):
    from mordheim_combat.vectorized import attack_count
    import numpy as np
    case=vector_case("test_vectorized_engine/test_shield_does_not_grant_an_attack_but_second_weapon_does-0-0")
    shield,dagger=case.first,case.second
    charging=np.zeros(1,dtype=bool)
    assert attack_count(shield,charging)[0]==1
    assert attack_count(dagger,charging)[0]==2

def test_conditional_hit_rerolls_and_berserker_only_apply_while_charging(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _prepare_weapon_attack
    case=vector_case("test_vectorized_engine/test_conditional_hit_rerolls_and_berserker_only_apply_while_charging-0-0")
    attacker,defender=case.first,case.second
    attacker_state=_new_state(attacker,2,np.random.default_rng(1))
    defender_state=_new_state(defender,2,np.random.default_rng(2))
    # A 3 misses at the normal 4+ target but hits at the 3+ Berserker target.
    prepared=_prepare_weapon_attack(attacker,defender,attacker.main_weapon,np.array([0,1]),
                                    np.array([True,False]),attacker_state,defender_state,
                                    FixedRng([3,3],6),True)
    assert prepared.hit_rows.tolist()==[0]

def test_sweep_replaces_all_attacks_with_one_initiative_test(vector_case):
    from mordheim_combat.vectorized import attack_count
    case=vector_case("test_vectorized_engine/test_sweep_replaces_all_attacks_with_one_initiative_test-0-0")
    attacker=case.first
    assert attack_count(attacker,np.zeros(3,dtype=bool)).tolist()==[1,1,1]

def test_armour_poison_and_regeneration_change_aggregate_outcomes(vector_case):
    base=vector_case("test_vectorized_engine/test_armour_poison_and_regeneration_change_aggregate_outcomes-0-0")
    armoured_case=vector_case("test_vectorized_engine/test_armour_poison_and_regeneration_change_aggregate_outcomes-0-1")
    poisoned_case=vector_case("test_vectorized_engine/test_armour_poison_and_regeneration_change_aggregate_outcomes-0-2")
    regenerating_case=vector_case("test_vectorized_engine/test_armour_poison_and_regeneration_change_aggregate_outcomes-0-3")
    plain=base.first
    armoured=armoured_case.second
    poisoned=poisoned_case.first
    regenerating=regenerating_case.second
    vs_plain=simulate_duel(DuelRequest(plain,plain,20_000,seed=31))
    vs_armour=simulate_duel(DuelRequest(plain,armoured,20_000,seed=31))
    with_poison=simulate_duel(DuelRequest(poisoned,plain,20_000,seed=31))
    vs_regeneration=simulate_duel(DuelRequest(plain,regenerating,20_000,seed=31))
    assert vs_armour.first_win_rate<vs_plain.first_win_rate
    assert with_poison.first_win_rate>vs_plain.first_win_rate
    assert vs_regeneration.first_win_rate<vs_plain.first_win_rate

def test_wound_modifier_improves_the_wound_roll_target(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon
    from mordheim_core.models import EffectSet
    plain_case=vector_case("test_vectorized_engine/test_wound_modifier_improves_the_wound_roll_target-0-0")
    improved_case=vector_case("test_vectorized_engine/test_wound_modifier_improves_the_wound_roll_target-0-1")
    defender=plain_case.second
    plain=plain_case.first
    improved=improved_case.first
    plain_attacker_state=_new_state(plain,1,np.random.default_rng(1))
    improved_attacker_state=_new_state(improved,1,np.random.default_rng(1))
    plain_defender_state=_new_state(defender,1,np.random.default_rng(2))
    improved_defender_state=_new_state(defender,1,np.random.default_rng(2))
    active=np.array([0]); charging=np.zeros(1,dtype=bool)
    _resolve_weapon(plain,defender,plain.main_weapon,active,charging,plain_attacker_state,plain_defender_state,FixedRng(3),False)
    _resolve_weapon(improved,defender,improved.main_weapon,active,charging,improved_attacker_state,improved_defender_state,FixedRng(3,1,1),False)
    assert plain_defender_state.wounds[0]==1
    assert improved_defender_state.wounds[0]==0

def test_scorpion_tail_loses_strength_against_poison_immunity(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _prepare_weapon_attack
    normal_case=vector_case("test_vectorized_engine/test_scorpion_tail_loses_strength_against_poison_immunity-0-0")
    immune_case=vector_case("test_vectorized_engine/test_scorpion_tail_loses_strength_against_poison_immunity-0-1")
    attacker=normal_case.first
    plain=normal_case.second
    immune=immune_case.second
    active=np.array([0]);charging=np.zeros(1,dtype=bool)
    normal=_prepare_weapon_attack(attacker,plain,attacker.main_weapon,active,charging,
        _new_state(attacker,1,np.random.default_rng(1)),_new_state(plain,1,np.random.default_rng(2)),FixedRng(6),False)
    resisted=_prepare_weapon_attack(attacker,immune,attacker.main_weapon,active,charging,
        _new_state(attacker,1,np.random.default_rng(1)),_new_state(immune,1,np.random.default_rng(2)),FixedRng(6),False)
    assert normal.strength.tolist()==[5]
    assert resisted.strength.tolist()==[2]

def test_acid_blood_retaliates_once_per_wound_lost(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon
    case=vector_case("test_vectorized_engine/test_acid_blood_retaliates_once_per_wound_lost-0-0")
    attacker,defender=case.first,case.second
    attacker_state=_new_state(attacker,1,np.random.default_rng(1))
    defender_state=_new_state(defender,1,np.random.default_rng(2))
    _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([0]),np.zeros(1,dtype=bool),
                    attacker_state,defender_state,FixedRng(2,6),False)
    assert defender_state.wounds[0]==1
    assert attacker_state.wounds[0]==2

def test_spines_resolve_simultaneously_at_the_start_of_the_phase(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_spines
    case=vector_case("test_vectorized_engine/test_spines_resolve_simultaneously_at_the_start_of_the_phase-0-0")
    spined,plain=case.first,case.second
    first_state=_new_state(spined,1,np.random.default_rng(1))
    second_state=_new_state(plain,1,np.random.default_rng(2))
    charging=np.zeros(1,dtype=bool)
    _resolve_spines(spined,plain,np.array([0]),charging,charging,
                    first_state,second_state,FixedRng(6,1))
    assert second_state.wounds[0]==1

@pytest.mark.parametrize("protection", (EffectSet(ward_save=2), EffectSet(regeneration_save=2)))
def test_profile_two_is_not_out_when_a_special_save_ignores_the_wound(protection, vector_case):
    from mordheim_combat.vectorized import STANDING
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon
    from mordheim_core.models import EffectSet
    index = 0 if protection.ward_save == 2 else 1
    case=vector_case(f"test_vectorized_engine/test_profile_two_is_not_out_when_a_special_save_ignores_the_wound-{index}-0")
    attacker,defender=case.first,case.second
    attacker_state=_new_state(attacker,1,np.random.default_rng(1))
    defender_state=_new_state(defender,1,np.random.default_rng(2))
    _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([0]),np.zeros(1,dtype=bool),
                    attacker_state,defender_state,FixedRng(6,6,2),False)
    assert defender_state.condition[0]==STANDING
    assert defender_state.wounds[0]==1

def test_summoned_bat_loses_two_wounds_before_removal_without_injury_dice(vector_case):
    from mordheim_combat.vectorized import _new_state, _resolve_weapon, OUT, STANDING
    case=vector_case("test_vectorized_engine/test_summoned_bat_loses_two_wounds_before_removal_without_injury_dice-0-0")

    class NonemptyDice(FixedRng):
        def integers(self, low, high=None, size=None, dtype=None):
            if size == 0:
                return np.empty(0, dtype=dtype or np.int64)
            return super().integers(low, high, size, dtype)

    attacker, defender = case.first, case.second
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

def test_parry_is_one_attempt_per_phase_and_respects_strength_limit(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _parry_hits
    case=vector_case("test_vectorized_engine/test_parry_is_one_attempt_per_phase_and_respects_strength_limit-0-0")
    defender=case.first
    state=_new_state(defender,2,np.random.default_rng(1))
    effect=defender.main_weapon
    remaining,blocked,_=_parry_hits(defender,effect,np.array([0]),np.array([4]),np.array([3]),state,FixedRng(6))
    assert remaining.size==0 and blocked.tolist()==[0]
    remaining,blocked,_=_parry_hits(defender,effect,np.array([0]),np.array([2]),np.array([3]),state,FixedRng(6))
    assert remaining.tolist()==[0] and blocked.size==0
    remaining,blocked,_=_parry_hits(defender,effect,np.array([1]),np.array([2]),np.array([6]),state,FixedRng(6))
    assert remaining.tolist()==[1] and blocked.size==0
    fresh=_new_state(defender,1,np.random.default_rng(2))
    # One parry attempt for the row: the defender's die is drawn for the one
    # eligible (highest) hit only, as ``phases.resolve_parry`` draws none for
    # an ineligible attempt.
    remaining,blocked,_=_parry_hits(defender,effect,np.array([0,0]),np.array([3,5]),np.array([3,3]),fresh,FixedRng([6]))
    assert remaining.size==1 and blocked.size==1

def test_unbeatable_warrior_parries_twice_with_two_parry_weapons(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _parry_hits
    case=vector_case("test_vectorized_engine/test_unbeatable_warrior_parries_twice_with_two_parry_weapons-0-0")
    defender=case.first
    state=_new_state(defender,1,np.random.default_rng(1))
    remaining,blocked,_=_parry_hits(defender,defender.main_weapon,np.array([0,0]),
                                    np.array([3,4]),np.array([3,3]),state,FixedRng([6,6]))
    assert remaining.size==0 and blocked.tolist()==[0,0]

def test_parry_selects_highest_hit_across_main_and_off_hand(monkeypatch, vector_case):
    import mordheim_combat.vectorized as engine
    import mordheim_combat.vectorized._attacks as engine_attacks
    case=vector_case("test_vectorized_engine/test_parry_selects_highest_hit_across_main_and_off_hand-0-0")
    attacker,defender=case.first,case.second
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
    monkeypatch.setattr(engine_attacks,"_prepare_weapon_attack",prepare);monkeypatch.setattr(engine_attacks,"_resolve_weapon",capture)
    engine.resolve_attacks(attacker,defender,np.array([0]),np.array([2]),np.array([False]),attacker_state,defender_state,np.random.default_rng(3),False)
    assert selected==[(3,[]),(5,[0])]

def test_only_one_critical_can_be_claimed_per_row_and_phase(vector_case):
    from mordheim_combat.vectorized import _claim_criticals
    from mordheim_combat.vectorized import _new_state
    case=vector_case("test_vectorized_engine/test_only_one_critical_can_be_claimed_per_row_and_phase-0-0")
    unit=case.first;state=_new_state(unit,2,np.random.default_rng(1))
    assert _claim_criticals(np.array([True,True]),np.array([0,1]),state).tolist()==[True,True]
    assert _claim_criticals(np.array([True,True]),np.array([0,1]),state).tolist()==[False,False]

def test_incapacitated_states_are_resolved_separately(vector_case):
    from mordheim_combat.vectorized import KNOCKED_DOWN
    from mordheim_combat.vectorized import OUT
    from mordheim_combat.vectorized import STUNNED
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon
    from mordheim_core.models import EffectSet
    case=vector_case("test_vectorized_engine/test_incapacitated_states_are_resolved_separately-0-0")
    attacker,defender=case.first,case.second
    attacker_state=_new_state(attacker,3,np.random.default_rng(1));defender_state=_new_state(defender,3,np.random.default_rng(2))
    defender_state.condition[:]=[KNOCKED_DOWN,KNOCKED_DOWN,STUNNED]
    _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([0]),np.zeros(3,dtype=bool),attacker_state,defender_state,FixedRng(1),False)
    _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([1]),np.zeros(3,dtype=bool),attacker_state,defender_state,FixedRng(6,6),False)
    _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([2]),np.zeros(3,dtype=bool),attacker_state,defender_state,FixedRng(),False)
    assert defender_state.condition.tolist()==[KNOCKED_DOWN,OUT,OUT]

def test_lustria_scaly_skin_keeps_its_shared_six_plus_floor(vector_case):
    from mordheim_combat.vectorized import STANDING
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon
    from mordheim_core.models import EffectSet
    case=vector_case("test_vectorized_engine/test_lustria_scaly_skin_keeps_its_shared_six_plus_floor-0-0")
    attacker,defender=case.first,case.second
    attacker_state=_new_state(attacker,1,np.random.default_rng(1))
    defender_state=_new_state(defender,1,np.random.default_rng(2))
    _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([0]),np.zeros(1,dtype=bool),
                    attacker_state,defender_state,FixedRng(5,6),False)
    assert defender_state.condition[0]==STANDING and defender_state.wounds[0]==1

def test_shared_hard_to_kill_and_fragile_injury_profiles(vector_case):
    from mordheim_combat.vectorized import STUNNED
    from mordheim_combat.vectorized import OUT
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon
    from mordheim_core.models import EffectSet
    case=vector_case("test_vectorized_engine/test_shared_hard_to_kill_and_fragile_injury_profiles-0-0")
    base=vector_case("test_vectorized_engine/test_seeded_duel_is_reproducible_and_counts_are_complete-0-0").first
    attacker=replace(base,main_weapon=EffectSet(fixed_strength=10,automatic_hit=True))
    hard=replace(case.first,main_weapon=EffectSet())
    fragile=case.second
    # Written Hard to Kill table: 1-2 Knocked Down, 3-5 Stunned, 6 Out.
    for defender,injury_roll,expected in ((hard,3,STUNNED),(fragile,4,OUT)):
        attacker_state=_new_state(attacker,1,np.random.default_rng(3))
        defender_state=_new_state(defender,1,np.random.default_rng(4))
        _resolve_weapon(attacker,defender,attacker.main_weapon,np.array([0]),np.zeros(1,dtype=bool),
                        attacker_state,defender_state,FixedRng(5,injury_roll,injury_roll),False)
        assert defender_state.condition[0]==expected

def test_skink_hunter_priority_distinguishes_first_round_from_always(vector_case):
    from mordheim_combat.vectorized import priority
    case=vector_case("test_vectorized_engine/test_skink_hunter_priority_distinguishes_first_round_from_always-0-0")
    base=case.first
    skink=replace(base,global_effects=EffectSet(tags=("species.skink",)))
    first_round_only=replace(base,global_effects=EffectSet(tags=("mechanic.strike-first-vs-skinks-first-round",)))
    always=replace(base,global_effects=EffectSet(tags=("mechanic.strike-first-vs-skinks-always",)))
    flags=np.zeros(1,dtype=bool)
    assert priority(first_round_only,skink,True,flags,flags,flags)[0]==20
    assert priority(first_round_only,skink,False,flags,flags,flags)[0]==0
    assert priority(always,skink,False,flags,flags,flags)[0]==20

def test_two_dwarf_axes_reroll_independently_of_master_of_blades(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _parry_hits
    case=vector_case("test_vectorized_engine/test_two_dwarf_axes_reroll_independently_of_master_of_blades-0-0")
    axe=EffectSet(tags=("weapon.dwarf-axe",),parry=True)
    core=replace(case.first,main_weapon=axe,off_hand=axe,global_effects=EffectSet(tags=("skill.unbeatable-warrior",)))
    master=replace(core,global_effects=EffectSet(tags=("skill.unbeatable-warrior","skill.sword-master")))
    core_state=_new_state(core,1,np.random.default_rng(1))
    master_state=_new_state(master,1,np.random.default_rng(1))
    remaining,_,_=_parry_hits(core,axe,np.array([0]),np.array([4]),np.array([3]),core_state,FixedRng(3,6))
    rerolled,_,_=_parry_hits(master,axe,np.array([0]),np.array([4]),np.array([3]),master_state,FixedRng(3,6))
    assert remaining.size==0
    assert rerolled.size==0

def test_scarecrow_catches_fire_on_three_plus_instead_of_brazier_five_plus(vector_case):
    from mordheim_combat.vectorized import _new_state
    from mordheim_combat.vectorized import _resolve_weapon
    ordinary_case=vector_case("test_vectorized_engine/test_scarecrow_catches_fire_on_three_plus_instead_of_brazier_five_plus-0-0")
    scarecrow_case=vector_case("test_vectorized_engine/test_scarecrow_catches_fire_on_three_plus_instead_of_brazier_five_plus-0-1")
    brazier=EffectSet(tags=("weapon.brazier-iron","attack.fire"),automatic_hit=True,ignition_threshold=5)
    attacker=ordinary_case.first
    ordinary=ordinary_case.second
    scarecrow=scarecrow_case.second
    ordinary_state=_new_state(ordinary,1,np.random.default_rng(1));scarecrow_state=_new_state(scarecrow,1,np.random.default_rng(1))
    attacker_state=_new_state(attacker,1,np.random.default_rng(2))
    _resolve_weapon(attacker,ordinary,brazier,np.array([0]),np.zeros(1,dtype=bool),attacker_state,ordinary_state,FixedRng(4,1),False)
    attacker_state=_new_state(attacker,1,np.random.default_rng(2))
    _resolve_weapon(attacker,scarecrow,brazier,np.array([0]),np.zeros(1,dtype=bool),attacker_state,scarecrow_state,FixedRng(4,1),False)
    assert not ordinary_state.on_fire[0]
    assert scarecrow_state.on_fire[0]

"""Vectorized engine: per-round state machines, batch loop and the
public simulate_duel/available_backends entry points."""
from __future__ import annotations

import numpy as np
from dataclasses import replace
from mordheim_core.dice import DecisionPolicy
from mordheim_core.models import CompiledFighter, DuelRequest, DuelResult, EffectSet, SimulationCancelled
from mordheim_combat.vectorized._types import CombatState, KNOCKED_DOWN, OUT, PARALYZED, STANDING, STUNNED, VectorBatchObservation, _parry_capacity, has
from mordheim_combat.vectorized._operators import _characteristic_test, attack_count, effective_initiative, priority
from mordheim_combat.vectorized._attacks import _optional_phase_plan, _prepare_weapon_attack, _resolve_weapon, resolve_attacks

def _new_state(fighter: CompiledFighter, count: int, rng: np.random.Generator) -> CombatState:
    wounds = fighter.characteristics.wounds + int(has(fighter.global_effects, "skill.monstrous"))
    crimson = rng.integers(1,4,count,dtype=np.int8) if has(fighter.global_effects,"preparation.crimson-shade") else np.zeros(count,dtype=np.int8)
    characteristic_values={
        "WS":np.full(count,fighter.characteristics.weapon_skill,dtype=np.int16),
        "S":np.full(count,fighter.characteristics.strength,dtype=np.int16),
        "T":np.full(count,fighter.characteristics.toughness+fighter.global_effects.toughness_bonus,dtype=np.int16),
        "I":np.full(count,fighter.characteristics.initiative,dtype=np.int16),
        "A":np.full(count,fighter.characteristics.attacks,dtype=np.int16),
    }
    for key,dice,sides,bonus in fighter.random_characteristics:
        rolls=np.zeros(count,dtype=np.int16)
        for _ in range(dice):rolls+=rng.integers(1,sides+1,count,dtype=np.int16)
        characteristic_values[key]=rolls+bonus
    state=CombatState(np.full(count, wounds, dtype=np.int16), np.zeros(count, dtype=np.int8),
                       np.zeros(count, dtype=np.int8), np.ones(count, dtype=np.int8),
                       np.full(count, fighter.global_effects.frenzy),
                       np.full(count, has(fighter.global_effects, "defence.lucky-charm")),crimson,
                       np.zeros(count,dtype=np.int8),np.zeros(count,dtype=bool),
                       np.zeros(count,dtype=bool),np.full(count,_parry_capacity(fighter),dtype=np.int8),np.zeros(count,dtype=bool),
                       np.zeros(count,dtype=bool),np.zeros(count,dtype=bool),np.zeros(count,dtype=np.int8),
                       np.zeros(count,dtype=np.int8),np.zeros(count,dtype=bool),np.zeros(count,dtype=bool),np.zeros(count,dtype=bool),
                       characteristic_values["WS"],characteristic_values["S"],
                       characteristic_values["T"],characteristic_values["I"],
                       characteristic_values["A"])
    if has(fighter.global_effects,"mechanic.disability"):
        state.disability[:]=rng.integers(1,7,count,dtype=np.int8)
        state.initiative[state.disability==1]=np.maximum(1,state.initiative[state.disability==1]-1)
        state.weapon_skill[state.disability==2]=np.maximum(1,state.weapon_skill[state.disability==2]-1)
        state.toughness[state.disability==4]=np.maximum(1,state.toughness[state.disability==4]-1)
        state.strength[state.disability==5]=np.maximum(1,state.strength[state.disability==5]-1)
    return state

def _resolve_spines(first: CompiledFighter, second: CompiledFighter,
                    rows: np.ndarray, charge1: np.ndarray, charge2: np.ndarray,
                    state1: CombatState, state2: CombatState,
                    rng: np.random.Generator) -> None:
    """Resolve simultaneous, non-critical Spines hits at phase start."""
    spines=EffectSet(
        tags=("rule.spines", "effect.no-critical"), fixed_strength=1,
        automatic_hit=True, cannot_be_parried=True)
    prepared1=(
        _prepare_weapon_attack(first,second,spines,rows,charge1,state1,state2,rng,False)
        if has(first.global_effects,"spines") else None)
    prepared2=(
        _prepare_weapon_attack(second,first,spines,rows,charge2,state2,state1,rng,False)
        if has(second.global_effects,"spines") else None)
    if prepared1 is not None:
        _resolve_weapon(first,second,spines,rows,charge1,state1,state2,rng,False,prepared=prepared1)
    if prepared2 is not None:
        _resolve_weapon(second,first,spines,rows,charge2,state2,state1,rng,False,prepared=prepared2)

def _rescue_force_of_will(fighter: CompiledFighter, state: CombatState,
                          rows: np.ndarray, rng: np.random.Generator) -> None:
    if not has(fighter.global_effects,"mechanic.force-of-will") or rows.size==0:return
    eligible=rows[(state.condition[rows]==OUT)&~state.force_of_will_used[rows]]
    if eligible.size==0:return
    state.force_of_will_used[eligible]=True
    success=_characteristic_test(fighter,state.toughness[eligible],rng)
    rescued=eligible[success]
    state.condition[rescued]=STANDING
    state.wounds[rescued]=1
    state.force_of_will_active[rescued]=True

def _sustain_force_of_will(fighter: CompiledFighter, state: CombatState,
                           rng: np.random.Generator,
                           rows: np.ndarray | None = None) -> None:
    if not has(fighter.global_effects,"mechanic.force-of-will"):return
    eligible = state.force_of_will_active & (state.condition != OUT)
    if rows is not None:
        selected = np.zeros(state.wounds.size, dtype=bool)
        selected[rows] = True
        eligible &= selected
    active=np.flatnonzero(eligible)
    if active.size==0:return
    state.force_of_will_penalty[active]+=1
    target=np.maximum(0,state.toughness[active]-state.force_of_will_penalty[active])
    failed=rng.integers(1,7,active.size)>target
    removed=active[failed]
    state.condition[removed]=OUT
    state.force_of_will_active[removed]=False

def _black_hunger_backlash(fighter: CompiledFighter, state: CombatState,
                           rows: np.ndarray, rng: np.random.Generator) -> None:
    if not has(fighter.global_effects,"mechanic.black-hunger") or rows.size==0:return
    active=rows[state.condition[rows]!=OUT]
    if active.size==0:return
    hits=rng.integers(1,4,active.size)
    backlash=EffectSet(tags=("mechanic.black-hunger-backlash","effect.no-critical"),fixed_strength=3,
                       automatic_hit=True,cannot_be_parried=True,ignore_armour=True)
    for index in range(3):
        hit_rows=active[hits>index]
        _resolve_weapon(fighter,fighter,backlash,hit_rows,np.zeros(state.wounds.size,dtype=bool),state,state,rng,False)
        _rescue_force_of_will(fighter,state,hit_rows,rng)

def _resolve_fire(victim: CompiledFighter, opponent: CompiledFighter,
                   victim_state: CombatState, opponent_state: CombatState,
                   rng: np.random.Generator,
                   rows: np.ndarray | None = None) -> None:
    """Resolve the Recovery-phase test and S4 hit for warriors on fire."""
    burning=np.flatnonzero(victim_state.on_fire&(victim_state.condition!=OUT))
    if rows is not None:
        burning = np.intersect1d(burning, rows, assume_unique=True)
    if burning.size==0:return
    extinguished=rng.integers(1,7,burning.size)>=4
    victim_state.on_fire[burning[extinguished]]=False
    still_burning=burning[~extinguished]
    if still_burning.size==0:return
    fire=EffectSet(tags=("attack.fire","effect.no-critical"),fixed_strength=4,
                   automatic_hit=True,cannot_be_parried=True)
    source=replace(opponent,main_weapon=fire,off_hand=None,global_effects=EffectSet(),extra_attacks=())
    _resolve_weapon(source,victim,fire,still_burning,np.zeros(victim_state.wounds.size,dtype=bool),
                    opponent_state,victim_state,rng,False)

def _resolve_netter_charge(netter: CompiledFighter, target: CompiledFighter,
                           rows: np.ndarray, netter_state: CombatState,
                           target_state: CombatState,
                           rng: np.random.Generator) -> np.ndarray:
    """Resolve Netter's first-round charge reaction and return caught rows."""
    if rows.size == 0 or not has(netter.global_effects,"mechanic.netter"):
        return np.empty(0,dtype=np.int64)
    hits=rng.integers(1,7,rows.size)>=max(2,7-netter.ballistic_skill)
    escape=_characteristic_test(target,target_state.strength[rows],rng)
    caught=rows[hits&~escape]
    target_state.condition[caught]=KNOCKED_DOWN
    return caught

def _resource_observation(state: CombatState) -> tuple[tuple[str, np.ndarray], ...]:
    return (
        ("lucky-charm", ~state.lucky_charm.copy()),
        ("force-of-will", state.force_of_will_used.copy()),
        ("mark-of-the-old-ones", state.mark_of_old_ones_used.copy()),
        ("luck", state.luck_used.copy()),
    )

def _simulate_batch_core(first: CompiledFighter, second: CompiledFighter, count: int,
                         rng: np.random.Generator, maximum_rounds: int,
                         decisions: DecisionPolicy | None = None,
                         *, observe: bool = False
                         ) -> tuple[int, int, int] | VectorBatchObservation:
    state1, state2 = _new_state(first,count,rng), _new_state(second,count,rng)
    first_charges = rng.random(count) < .5
    rounds = np.zeros(count, dtype=np.int16) if observe else None
    optional = _optional_phase_plan(first, second)
    entangle_effect = (
        EffectSet(tags=("effect.chained-squig-entangle",),fixed_strength=3,automatic_hit=True)
        if optional.first_entangle or optional.second_entangle else None
    )
    for round_index in range(maximum_rounds):
        unresolved = (state1.condition != OUT) & (state2.condition != OUT)
        if not unresolved.any():
            break
        if round_index:
            active_rows = np.flatnonzero(unresolved)
            if optional.first_force_of_will:
                _sustain_force_of_will(first,state1,rng,active_rows)
            if optional.second_force_of_will:
                _sustain_force_of_will(second,state2,rng,active_rows)
            if optional.first_can_burn:
                _resolve_fire(first,second,state1,state2,rng,active_rows)
            if optional.second_can_burn:
                _resolve_fire(second,first,state2,state1,rng,active_rows)
            if optional.first_force_of_will:
                _rescue_force_of_will(first, state1, active_rows, rng)
            if optional.second_force_of_will:
                _rescue_force_of_will(second, state2, active_rows, rng)
        unresolved = (state1.condition != OUT) & (state2.condition != OUT)
        if not unresolved.any():
            break
        active_rows = np.flatnonzero(unresolved)
        if rounds is not None:
            rounds[unresolved] += 1
        state1.parry_used[:] = False; state2.parry_used[:] = False
        state1.parry_remaining[:] = _parry_capacity(first)
        state2.parry_remaining[:] = _parry_capacity(second)
        state1.critical_used[:] = False; state2.critical_used[:] = False
        if has(first.global_effects,"mechanic.spawn-special-attacks"):
            state1.attacks[:]=rng.integers(1,7,count,dtype=np.int16)+1
        if has(second.global_effects,"mechanic.spawn-special-attacks"):
            state2.attacks[:]=rng.integers(1,7,count,dtype=np.int16)+1
        stunned1, stunned2 = state1.condition == STUNNED, state2.condition == STUNNED
        stood1, stood2 = state1.condition == KNOCKED_DOWN, state2.condition == KNOCKED_DOWN
        state1.condition[stunned1] = KNOCKED_DOWN; state2.condition[stunned2] = KNOCKED_DOWN
        state1.condition[stood1 & ~stunned1] = STANDING; state2.condition[stood2 & ~stunned2] = STANDING
        paralyzed1, paralyzed2 = state1.condition == PARALYZED, state2.condition == PARALYZED
        paralyzed_rows1=np.flatnonzero(paralyzed1)
        paralyzed_rows2=np.flatnonzero(paralyzed2)
        if paralyzed_rows1.size:
            recover1=_characteristic_test(first,state1.toughness[paralyzed_rows1],rng)
            state1.condition[paralyzed_rows1[recover1]] = STANDING
        if paralyzed_rows2.size:
            recover2=_characteristic_test(second,state2.toughness[paralyzed_rows2],rng)
            state2.condition[paralyzed_rows2[recover2]] = STANDING
        first_round = round_index == 0
        charge1 = first_charges if first_round else np.zeros(count,dtype=bool)
        charge2 = ~first_charges if first_round else np.zeros(count,dtype=bool)
        if first_round:
            if optional.first_netter:
                rows=np.flatnonzero(unresolved&charge1)
                _resolve_netter_charge(first,second,rows,state1,state2,rng)
            if optional.second_netter:
                rows=np.flatnonzero(unresolved&charge2)
                _resolve_netter_charge(second,first,rows,state2,state1,rng)
        if optional.first_spines or optional.second_spines:
            _resolve_spines(first,second,active_rows,charge1,charge2,state1,state2,rng)
        if optional.first_force_of_will:
            _rescue_force_of_will(first,state1,active_rows,rng)
        if optional.second_force_of_will:
            _rescue_force_of_will(second,state2,active_rows,rng)
        if optional.second_entangle:
            entangled1=np.flatnonzero(state1.entangled&(state2.condition==STANDING)&unresolved)
            _resolve_weapon(second,first,entangle_effect,entangled1,charge2,state2,state1,rng,False)
        if optional.first_entangle:
            entangled2=np.flatnonzero(state2.entangled&(state1.condition==STANDING)&unresolved)
            _resolve_weapon(first,second,entangle_effect,entangled2,charge1,state1,state2,rng,False)
        charged1, charged2 = charge2, charge1
        attacks1=attack_count(first,charge1,first_round,state1.frenzy,charged1,state1.attack_penalty,state1.wounds<first.characteristics.wounds,state1.attacks)
        attacks2=attack_count(second,charge2,first_round,state2.frenzy,charged2,state2.attack_penalty,state2.wounds<second.characteristics.wounds,state2.attacks)
        attacks1=np.where(attacks1>0,np.maximum(1,attacks1+second.global_effects.incoming_attacks_modifier),0)
        attacks2=np.where(attacks2>0,np.maximum(1,attacks2+first.global_effects.incoming_attacks_modifier),0)
        attacks1[state1.on_fire]=0;attacks2[state2.on_fire]=0
        if has(first.global_effects,"animal_friendship") and has(second.global_effects,"species.animal"):
            attacks2[:]=0
        if has(second.global_effects,"animal_friendship") and has(first.global_effects,"species.animal"):
            attacks1[:]=0
        state1.attack_penalty[:]=0;state2.attack_penalty[:]=0
        if first_round and has(first.main_weapon,"weapon.serpent-whip"):attacks1+=charge1|charged1
        if first_round and has(second.main_weapon,"weapon.serpent-whip"):attacks2+=charge2|charged2
        if first_round and has(first.main_weapon,"weapon.boar-spear"):attacks2[charge2]=np.maximum(1,attacks2[charge2]-1)
        if first_round and has(second.main_weapon,"weapon.boar-spear"):attacks1[charge1]=np.maximum(1,attacks1[charge1]-1)
        if first_round and has(first.global_effects,"skill.sigmar-s-sign") and has(second.global_effects,"undead_or_possessed"):
            attacks2=np.where(attacks2>0,np.maximum(1,attacks2-1),0)
        if first_round and has(second.global_effects,"skill.sigmar-s-sign") and has(first.global_effects,"undead_or_possessed"):
            attacks1=np.where(attacks1>0,np.maximum(1,attacks1-1),0)
        p1,p2=priority(first,second,first_round,charge1,charged1,stood1),priority(second,first,first_round,charge2,charged2,stood2)
        i1,i2=effective_initiative(first,state1),effective_initiative(second,state2)
        first_acts=(p1>p2)|((p1==p2)&(i1>i2));ties=(p1==p2)&(i1==i2)
        first_acts[ties]=rng.random(int(ties.sum()))<.5
        rows=np.flatnonzero(unresolved&(state1.condition==STANDING)&first_acts)
        resolve_attacks(first,second,rows,attacks1,charge1,state1,state2,rng,first_round,decisions)
        if optional.first_force_of_will:_rescue_force_of_will(first,state1,rows,rng)
        if optional.second_force_of_will:_rescue_force_of_will(second,state2,rows,rng)
        reply=rows[state2.condition[rows]==STANDING]
        resolve_attacks(second,first,reply,attacks2,charge2,state2,state1,rng,first_round,decisions)
        if optional.first_force_of_will:_rescue_force_of_will(first,state1,reply,rng)
        if optional.second_force_of_will:_rescue_force_of_will(second,state2,reply,rng)
        rows=np.flatnonzero(unresolved&(state2.condition==STANDING)&~first_acts)
        resolve_attacks(second,first,rows,attacks2,charge2,state2,state1,rng,first_round,decisions)
        if optional.first_force_of_will:_rescue_force_of_will(first,state1,rows,rng)
        if optional.second_force_of_will:_rescue_force_of_will(second,state2,rows,rng)
        reply=rows[state1.condition[rows]==STANDING]
        resolve_attacks(first,second,reply,attacks1,charge1,state1,state2,rng,first_round,decisions)
        if optional.first_force_of_will:_rescue_force_of_will(first,state1,reply,rng)
        if optional.second_force_of_will:_rescue_force_of_will(second,state2,reply,rng)
        if optional.first_black_hunger:
            _black_hunger_backlash(first,state1,active_rows,rng)
        if optional.second_black_hunger:
            _black_hunger_backlash(second,state2,active_rows,rng)
    a=int(np.count_nonzero((state2.condition==OUT)&(state1.condition!=OUT)))
    b=int(np.count_nonzero((state1.condition==OUT)&(state2.condition!=OUT)))
    if observe:
        winner = np.zeros(count, dtype=np.int8)
        winner[(state2.condition == OUT) & (state1.condition != OUT)] = 1
        winner[(state1.condition == OUT) & (state2.condition != OUT)] = -1
        return VectorBatchObservation(
            winner=winner,
            rounds=rounds if rounds is not None else np.zeros(count, dtype=np.int16),
            first_wounds=state1.wounds.copy(),
            second_wounds=state2.wounds.copy(),
            first_condition=state1.condition.copy(),
            second_condition=state2.condition.copy(),
            first_resources=_resource_observation(state1),
            second_resources=_resource_observation(state2),
        )
    return a,b,count-a-b

def simulate_batch(first: CompiledFighter, second: CompiledFighter, count: int,
                   rng: np.random.Generator, maximum_rounds: int,
                   decisions: DecisionPolicy | None = None) -> tuple[int, int, int]:
    result = _simulate_batch_core(first, second, count, rng, maximum_rounds, decisions)
    assert isinstance(result, tuple)
    return result

def simulate_batch_observed(first: CompiledFighter, second: CompiledFighter, count: int,
                            rng: np.random.Generator, maximum_rounds: int,
                            decisions: DecisionPolicy | None = None) -> VectorBatchObservation:
    result = _simulate_batch_core(
        first, second, count, rng, maximum_rounds, decisions, observe=True,
    )
    assert isinstance(result, VectorBatchObservation)
    return result

def available_backends() -> tuple[str, ...]:
    """Return executable production backends in selection order."""
    try:
        from mordheim_combat import _combat_native
    except ImportError:
        return ("numpy",)
    return ("native", "numpy") if hasattr(_combat_native, "simulate_duel") else ("numpy",)

def _simulate_duel_numpy(request: DuelRequest) -> DuelResult:
    rng=np.random.default_rng(request.seed);a=b=u=0;remaining=request.simulations
    while remaining:
        if request.cancel_event is not None and request.cancel_event.is_set():
            raise SimulationCancelled("simulation cancelled")
        count=min(remaining,request.batch_size)
        x,y,z=simulate_batch(
            request.first,request.second,count,rng,request.maximum_rounds,
            request.decision_policy,
        )
        a+=x;b+=y;u+=z;remaining-=count
    return DuelResult(a,b,u,request.simulations)

def simulate_duel(request: DuelRequest, *, backend: str = "auto") -> DuelResult:
    """Run a duel through the selected backend without changing `DuelRequest`."""
    if backend not in {"auto", "numpy", "native"}:
        raise ValueError(f"unknown combat backend: {backend}")
    selected = available_backends()[0] if backend == "auto" else backend
    if selected == "numpy":
        return _simulate_duel_numpy(request)
    try:
        from mordheim_combat import _combat_native
    except ImportError as error:
        raise RuntimeError("native combat backend is not available") from error
    if not hasattr(_combat_native, "simulate_duel"):
        raise RuntimeError("native combat backend is not available")
    from mordheim_combat.kernel import compile_duel_plan

    plan = compile_duel_plan(request.first, request.second)
    if not plan.optimization_eligible:
        return _simulate_duel_numpy(request)
    supports = getattr(_combat_native, "supports_plan", lambda _plan: False)
    if not supports(plan):
        if backend == "native":
            raise RuntimeError("native combat backend does not support this duel plan")
        return _simulate_duel_numpy(request)
    return _combat_native.simulate_duel(request, plan)

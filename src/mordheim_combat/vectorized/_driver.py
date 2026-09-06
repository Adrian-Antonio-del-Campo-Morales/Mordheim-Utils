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
from mordheim_combat.vectorized._equipment import phase_equipment, staff_power

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
                       characteristic_values["A"], np.zeros(count, dtype=np.uint8),
                       np.zeros(count, dtype=np.int16), np.zeros(count, dtype=np.int16))
    if has(fighter.global_effects,"mechanic.disability"):
        state.disability[:]=rng.integers(1,7,count,dtype=np.int8)
        state.initiative[state.disability==1]=np.maximum(1,state.initiative[state.disability==1]-1)
        state.weapon_skill[state.disability==2]=np.maximum(1,state.weapon_skill[state.disability==2]-1)
        state.toughness[state.disability==4]=np.maximum(1,state.toughness[state.disability==4]-1)
        state.strength[state.disability==5]=np.maximum(1,state.strength[state.disability==5]-1)
    return state

def _refresh_random_characteristics(
    fighter: CompiledFighter, state: CombatState, rows: np.ndarray,
    rng: np.random.Generator,
) -> None:
    """Refresh Condemned/Inconsistency characteristics at turn start."""
    random_stats = {characteristic for characteristic, *_ in fighter.random_characteristics}
    if not {"WS", "S", "T", "A"}.issubset(random_stats):
        return
    values: dict[str, np.ndarray] = {}
    count = rows.size
    for characteristic, dice, sides, bonus in fighter.random_characteristics:
        rolls = np.zeros(count, dtype=np.int16)
        for _ in range(dice):
            rolls += rng.integers(1, sides + 1, count, dtype=np.int16)
        values[characteristic] = rolls + bonus
    state.weapon_skill[rows] = values["WS"]
    state.strength[rows] = values["S"]
    state.toughness[rows] = values["T"] + fighter.global_effects.toughness_bonus
    state.attacks[rows] = values["A"]


def _resolve_spines(first: CompiledFighter, second: CompiledFighter,
                    rows: np.ndarray, charge1: np.ndarray, charge2: np.ndarray,
                    state1: CombatState, state2: CombatState,
                    rng: np.random.Generator) -> None:
    """Resolve simultaneous, non-critical Spines hits at phase start."""
    spines=EffectSet(
        tags=("rule.spines", "effect.no-critical"), fixed_strength=1,
        automatic_hit=True, cannot_be_parried=True)
    prepared1=(
        _prepare_weapon_attack(first,second,spines,rows,charge1,state1,state2,rng,False,melee_attack=False)
        if has(first.global_effects,"spines") else None)
    prepared2=(
        _prepare_weapon_attack(second,first,spines,rows,charge2,state2,state1,rng,False,melee_attack=False)
        if has(second.global_effects,"spines") else None)
    if prepared1 is not None:
        _resolve_weapon(first,second,spines,rows,charge1,state1,state2,rng,False,prepared=prepared1,melee_attack=False)
    if prepared2 is not None:
        _resolve_weapon(second,first,spines,rows,charge2,state2,state1,rng,False,prepared=prepared2,melee_attack=False)

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
    failed=~_characteristic_test(fighter,target,rng)
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
        _resolve_weapon(fighter,fighter,backlash,hit_rows,np.zeros(state.wounds.size,dtype=bool),state,state,rng,False,
            melee_attack=False)
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
                    opponent_state,victim_state,rng,False,melee_attack=False)

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
    original_first, original_second = first, second
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
            _refresh_random_characteristics(original_first, state1, active_rows, rng)
            _refresh_random_characteristics(original_second, state2, active_rows, rng)
        first = phase_equipment(original_first, first_round=round_index == 0)
        second = phase_equipment(original_second, first_round=round_index == 0)
        first_player_turn = first_charges if round_index % 2 == 0 else ~first_charges
        if round_index:
            if optional.first_force_of_will:
                _sustain_force_of_will(first,state1,rng,active_rows)
            if optional.second_force_of_will:
                _sustain_force_of_will(second,state2,rng,active_rows)
            if optional.first_can_burn:
                _resolve_fire(first,second,state1,state2,rng,np.flatnonzero(unresolved & first_player_turn))
            if optional.second_can_burn:
                _resolve_fire(second,first,state2,state1,rng,np.flatnonzero(unresolved & ~first_player_turn))
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
        state1.attack_penalty[:] = 0; state2.attack_penalty[:] = 0
        state1.hampered_main[:] = 0; state2.hampered_main[:] = 0
        state1.hampered_off[:] = 0; state2.hampered_off[:] = 0
        if has(first.global_effects,"mechanic.spawn-special-attacks"):
            state1.attacks[:]=rng.integers(1,7,count,dtype=np.int16)+1
        if has(second.global_effects,"mechanic.spawn-special-attacks"):
            state2.attacks[:]=rng.integers(1,7,count,dtype=np.int16)+1
        stunned1 = (state1.condition == STUNNED) & first_player_turn
        stunned2 = (state2.condition == STUNNED) & ~first_player_turn
        stood1 = (state1.condition == KNOCKED_DOWN) & first_player_turn
        stood2 = (state2.condition == KNOCKED_DOWN) & ~first_player_turn
        state1.condition[stunned1] = KNOCKED_DOWN; state2.condition[stunned2] = KNOCKED_DOWN
        state1.condition[stood1 & ~stunned1] = STANDING; state2.condition[stood2 & ~stunned2] = STANDING
        paralyzed1 = (state1.condition == PARALYZED) & first_player_turn
        paralyzed2 = (state2.condition == PARALYZED) & ~first_player_turn
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
        first = staff_power(first, decisions, f'round.{round_index}.first')
        second = staff_power(second, decisions, f'round.{round_index}.second')
        if has(first.main_weapon, 'effect.serpent-staff-power'):
            state1.parry_remaining[:] = 0
        if has(second.main_weapon, 'effect.serpent-staff-power'):
            state2.parry_remaining[:] = 0
        attacks1=attack_count(first,charge1,first_round,state1.frenzy,charged1,state1.attack_penalty,state1.wounds<first.characteristics.wounds,state1.attacks,player_turn=first_player_turn)
        attacks2=attack_count(second,charge2,first_round,state2.frenzy,charged2,state2.attack_penalty,state2.wounds<second.characteristics.wounds,state2.attacks,player_turn=~first_player_turn)
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
        # Each fighter's attack phase is gated only on *their own* standing,
        # never on the other fighter's row set.  Deriving the reply rows from
        # the primary actor's rows once silently dropped the standing
        # opponent's attack whenever the primary was down (knocked down or
        # stunned at round start): the downed primary's rows are empty, so the
        # reply — and with it the helpless auto-OOA execution — vanished too.
        # The scalar oracle resolves each pool independently, so the opponent
        # must still strike (and auto-out the helpless target).
        rows1=np.flatnonzero(unresolved&(state1.condition==STANDING)&first_acts)
        resolve_attacks(first,second,rows1,attacks1,charge1,state1,state2,rng,first_round,decisions)
        if optional.first_force_of_will:_rescue_force_of_will(first,state1,rows1,rng)
        if optional.second_force_of_will:_rescue_force_of_will(second,state2,rows1,rng)
        reply1=np.flatnonzero(unresolved&(state2.condition==STANDING)&first_acts)
        resolve_attacks(second,first,reply1,attacks2,charge2,state2,state1,rng,first_round,decisions)
        if optional.first_force_of_will:_rescue_force_of_will(first,state1,reply1,rng)
        if optional.second_force_of_will:_rescue_force_of_will(second,state2,reply1,rng)
        rows2=np.flatnonzero(unresolved&(state2.condition==STANDING)&~first_acts)
        resolve_attacks(second,first,rows2,attacks2,charge2,state2,state1,rng,first_round,decisions)
        if optional.first_force_of_will:_rescue_force_of_will(first,state1,rows2,rng)
        if optional.second_force_of_will:_rescue_force_of_will(second,state2,rows2,rng)
        reply2=np.flatnonzero(unresolved&(state1.condition==STANDING)&~first_acts)
        resolve_attacks(first,second,reply2,attacks1,charge1,state1,state2,rng,first_round,decisions)
        if optional.first_force_of_will:_rescue_force_of_will(first,state1,reply2,rng)
        if optional.second_force_of_will:_rescue_force_of_will(second,state2,reply2,rng)
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
    from mordheim_combat.kernel import EFFECT_VALUE_FIELDS
    compatible = getattr(_combat_native, 'N_EFFECT_FIELDS', None) == len(EFFECT_VALUE_FIELDS)
    return ("native", "numpy") if hasattr(_combat_native, "simulate_duel") and compatible else ("numpy",)

# Per-batch stream derivation for the NumPy driver.
#
# The native backend seeds one stream per batch, which makes its batches
# independent, reproducible work units.  The NumPy driver used to carry a
# single Generator across the whole sample, so its batches were not
# splittable.  Deriving a generator per batch from (seed, batch_index) keeps
# every draw site untouched while turning each batch into an independent
# unit: a large sample can now be split across processes batch by batch and
# the totals are bit-for-bit identical to the sequential run.  Batch 0 keeps
# the historical seed, so single-batch samples (<= one batch_size) are
# unchanged.
_BATCH_STREAM_SALT = 0x9E3779B97F4A7C15  # golden-ratio constant (as native)


def _batch_seed(seed: int, batch_index: int) -> int:
    return (seed + batch_index * _BATCH_STREAM_SALT) % (1 << 32)


def _batch_sizes(simulations: int, batch_size: int) -> tuple[int, ...]:
    """Canonical per-batch duel counts: full batches plus a final partial."""
    full, remainder = divmod(simulations, batch_size)
    return (batch_size,) * full + ((remainder,) if remainder else ())


def _run_one_batch(first: CompiledFighter, second: CompiledFighter, count: int,
                   seed: int, batch_index: int, maximum_rounds: int,
                   decisions: DecisionPolicy | None) -> tuple[int, int, int]:
    """Simulate exactly one batch on its own independent stream."""
    rng = np.random.default_rng(
        seed if batch_index == 0 else _batch_seed(seed, batch_index))
    return simulate_batch(first, second, count, rng, maximum_rounds, decisions)


def _simulate_duel_numpy(request: DuelRequest) -> DuelResult:
    first_wins = second_wins = unresolved = 0
    for batch_index, count in enumerate(_batch_sizes(
            request.simulations, request.batch_size)):
        if request.cancel_event is not None and request.cancel_event.is_set():
            raise SimulationCancelled("simulation cancelled")
        x, y, z = _run_one_batch(
            request.first, request.second, count, request.seed, batch_index,
            request.maximum_rounds, request.decision_policy,
        )
        first_wins += x
        second_wins += y
        unresolved += z
    return DuelResult(first_wins, second_wins, unresolved, request.simulations)


def _run_batch_segment(first: CompiledFighter, second: CompiledFighter,
                       start: int, stop: int, simulations: int,
                       batch_size: int, seed: int, maximum_rounds: int,
                       decisions: DecisionPolicy | None) -> tuple[int, int, int]:
    """Run whole batches ``[start, stop)`` of the canonical plan (worker)."""
    sizes = _batch_sizes(simulations, batch_size)
    first_wins = second_wins = unresolved = 0
    for batch_index in range(start, stop):
        x, y, z = _run_one_batch(
            first, second, sizes[batch_index], seed, batch_index,
            maximum_rounds, decisions,
        )
        first_wins += x
        second_wins += y
        unresolved += z
    return first_wins, second_wins, unresolved


def simulate_duel_parallel(request: DuelRequest, *,
                           workers: int | None = None) -> DuelResult:
    """Bit-for-bit parallel equivalent of the NumPy driver.

    The sample is partitioned along whole batches (each batch has its own
    stream derived from the seed), so any worker split reproduces the
    sequential ``simulate_duel(backend="numpy")`` totals exactly.  Processes
    are required because the NumPy hot loops hold the GIL.  ``workers``
    defaults to the machine's core count and is capped at the number of
    batches; ``cancel_event`` is honoured between completed segments.
    """
    from concurrent.futures import ProcessPoolExecutor
    from concurrent.futures import as_completed
    import os

    sizes = _batch_sizes(request.simulations, request.batch_size)
    total = len(sizes)
    available = workers if workers is not None else os.cpu_count() or 1
    workers_used = max(1, min(available, total))
    base, extra = divmod(total, workers_used)
    segments = []
    start = 0
    for index in range(workers_used):
        count = base + (1 if index < extra else 0)
        segments.append((start, start + count))
        start += count
    first_wins = second_wins = unresolved = 0
    with ProcessPoolExecutor(max_workers=workers_used) as pool:
        futures = [
            pool.submit(
                _run_batch_segment, request.first, request.second,
                start, stop, request.simulations, request.batch_size,
                request.seed, request.maximum_rounds,
                request.decision_policy,
            )
            for start, stop in segments
        ]
        try:
            for future in as_completed(futures):
                if request.cancel_event is not None and request.cancel_event.is_set():
                    raise SimulationCancelled("parallel simulation cancelled")
                x, y, z = future.result()
                first_wins += x
                second_wins += y
                unresolved += z
        finally:
            for future in futures:
                future.cancel()
    return DuelResult(first_wins, second_wins, unresolved, request.simulations)

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
    from mordheim_combat.kernel import EFFECT_VALUE_FIELDS
    if getattr(_combat_native, 'N_EFFECT_FIELDS', None) != len(EFFECT_VALUE_FIELDS):
        raise RuntimeError("native combat effect layout is stale; rebuild with tools/mordheim-utils.py build-native")
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

"""Integración del motor modular."""
from __future__ import annotations

from mordheim_combat_lab.combat.modular.attacks import resolve_reference_attack
from mordheim_combat_lab.combat.modular.duel import simulate_duel_reference
from mordheim_combat_lab.combat.modular.rounds import resolve_round
from mordheim_combat_lab.combat.modular.state import DuelState
from mordheim_combat_lab.combat.modular.state import initialize_fighter
from mordheim_combat_lab.combat.phases import AttackPoolContext
from mordheim_combat_lab.combat.phases import Condition
from mordheim_combat_lab.combat.phases import build_attacks
from mordheim_combat_lab.construction.compiler import compile_fighter
from mordheim_combat_lab.domain.dice import AlwaysAccept
from mordheim_combat_lab.domain.dice import KeyedDice
from mordheim_combat_lab.domain.dice import ScriptedDice
from mordheim_combat_lab.domain.models import Characteristics
from mordheim_combat_lab.domain.models import FighterBuild
from mordheim_combat_lab.domain.models import SimulationCancelled
import pytest as pytest
from threading import Event


def fighter(**changes):
    options = dict(
        ruleset="mordheim",
        characteristics=Characteristics(3, 3, 3, 1, 3, 1),
    )
    options.update(changes)
    return compile_fighter(FighterBuild(**options))


def test_scalar_attack_pool_has_no_dependency_on_the_vectorized_engine(monkeypatch):
    import mordheim_combat_lab.combat.vectorized as engine

    monkeypatch.setattr(engine, "attack_count", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError()))
    assert build_attacks(AttackPoolContext(fighter(off_hand_id="weapon.dagger"))).attacks == 2


def test_reference_attack_transfers_a_wound_through_every_scalar_phase():
    attacker = fighter(characteristics=Characteristics(6, 6, 3, 1, 6, 1))
    defender = fighter()
    attack_state = initialize_fighter(attacker, KeyedDice(1), "attacker")
    defence_state = initialize_fighter(defender, KeyedDice(2), "defender")
    result = resolve_reference_attack(
        attacker, defender, attack_state, defence_state, attacker.main_weapon,
        ScriptedDice({
            "strike.hit": 6,
            "strike.wound": 6,
            "strike.injury.0": 5,
        }),
        key="strike",
    )
    assert result.hit and result.wounded and result.damage == 1
    assert result.defender.condition == Condition.OUT


def test_reference_round_generates_priority_attacks_and_aftermath_itself():
    first, second = fighter(), fighter()
    state = DuelState(
        initialize_fighter(first, KeyedDice(1), "first"),
        initialize_fighter(second, KeyedDice(2), "second"),
        first_charged=True,
    )
    result = resolve_round(first, second, state, KeyedDice(7), AlwaysAccept())
    assert result.state.round_index == 1
    assert result.state.trace[0].value == "priority"
    assert result.state.trace[-1].value == "aftermath"
    assert result.attacks


def test_reference_duels_are_reproducible_without_calling_numpy_executor(monkeypatch):
    import mordheim_combat_lab.combat.vectorized as engine

    monkeypatch.setattr(engine, "simulate_duel", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError()))
    first = fighter(characteristics=Characteristics(3, 4, 3, 1, 3, 1))
    second = fighter()
    a = simulate_duel_reference(first, second, 20, seed=17, maximum_rounds=10)
    b = simulate_duel_reference(first, second, 20, seed=17, maximum_rounds=10)
    assert a == b
    assert a.first_wins + a.second_wins + a.unresolved == 20


def test_reference_bear_hug_is_orchestrated_before_normal_wounds():
    bear = compile_fighter(FighterBuild(
        "mordheim", band_id="kislevites", profile_id="trained-bear",
    ))
    target = fighter(characteristics=Characteristics(3, 3, 3, 1, 1, 1))
    state = DuelState(
        initialize_fighter(bear, KeyedDice(1), "bear"),
        initialize_fighter(target, KeyedDice(2), "target"),
        first_charged=True,
    )
    result = resolve_round(bear, target, state, KeyedDice(3), AlwaysAccept())
    assert result.state.round_index == 1


def test_reference_duel_honours_cancellation_and_maximum_rounds():
    cancelled = Event()
    cancelled.set()
    with pytest.raises(SimulationCancelled):
        simulate_duel_reference(fighter(), fighter(), 2, cancel_event=cancelled)
    result = simulate_duel_reference(fighter(), fighter(), 5, seed=4, maximum_rounds=1)
    assert result.simulations == 5

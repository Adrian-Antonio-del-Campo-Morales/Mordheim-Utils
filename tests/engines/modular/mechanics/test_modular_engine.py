"""Integration of the modular engine."""
from __future__ import annotations

from mordheim_combat.modular.attacks import resolve_reference_attack
from mordheim_combat.modular.duel import simulate_duel_reference
from mordheim_combat.modular.rounds import resolve_round
from mordheim_combat.modular.state import DuelState
from mordheim_combat.modular.state import initialize_fighter
from mordheim_combat.phases import AttackPoolContext
from mordheim_combat.phases import Condition
from mordheim_combat.phases import build_attacks
from mordheim_core.dice import AlwaysAccept
from mordheim_core.dice import KeyedDice
from mordheim_core.dice import ScriptedDice
from mordheim_core.models import SimulationCancelled
import pytest as pytest
from threading import Event




def test_reference_attack_transfers_a_wound_through_every_scalar_phase(precompiled):
    compiled = precompiled()
    attacker, defender = compiled.first, compiled.second
    attack_state = initialize_fighter(attacker, KeyedDice(1), "attacker")
    defence_state = initialize_fighter(defender, KeyedDice(2), "defender")
    result = resolve_reference_attack(
        attacker, defender, attack_state, defence_state, attacker.main_weapon,
        ScriptedDice({
            "strike.hit": 6,
            "strike.wound": 6,
            "strike.critical": 1,
            "strike.injury.0": 5,
            "strike.injury.1": 1,
        }),
        key="strike",
    )
    assert result.hit and result.wounded and result.damage == 2
    assert result.defender.condition == Condition.OUT






def test_reference_bear_hug_is_orchestrated_before_normal_wounds(precompiled):
    compiled = precompiled()
    bear, target = compiled.first, compiled.second
    state = DuelState(
        initialize_fighter(bear, KeyedDice(1), "bear"),
        initialize_fighter(target, KeyedDice(2), "target"),
        first_charged=True,
    )
    result = resolve_round(bear, target, state, KeyedDice(3), AlwaysAccept())
    assert result.state.round_index == 1

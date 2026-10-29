"""Pure phase contracts."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from mordheim_combat.phases import ArmourContext
from mordheim_combat.phases import AttackPoolContext
from mordheim_combat.phases import BearHugContext
from mordheim_combat.phases import Condition
from mordheim_combat.phases import HitContext
from mordheim_combat.phases import InjuryContext
from mordheim_combat.phases import ParryContext
from mordheim_combat.phases import Phase
from mordheim_combat.phases import PriorityContext
from mordheim_combat.phases import RoundContext
from mordheim_combat.phases import SpecialSaveContext
from mordheim_combat.phases import StrikeContext
from mordheim_combat.phases import WoundContext
from mordheim_combat.phases import armour_target
from mordheim_combat.phases import build_attacks
from mordheim_combat.phases import resolve_armour
from mordheim_combat.phases import resolve_attack
from mordheim_combat.phases import resolve_bear_hug
from mordheim_combat.phases import resolve_hit
from mordheim_combat.phases import resolve_injury
from mordheim_combat.phases import resolve_parry
from mordheim_combat.phases import resolve_priority
from mordheim_combat.phases import resolve_strike_sequence
from mordheim_combat.phases import resolve_special_save
from mordheim_combat.phases import resolve_wound
from mordheim_combat.phases import to_hit_target
from mordheim_combat.phases import wound_target
from mordheim_core.dice import AlwaysAccept
from mordheim_core.dice import AlwaysReject
from mordheim_core.dice import KeyedDice
from mordheim_core.dice import RollRequest
from mordheim_core.dice import ScriptedDice
from mordheim_core.dice import exact_distribution
import numpy as np
import pytest as pytest


class VectorTape:
    def __init__(self,*values):
        self.values=list(values)

    def integers(self,low,high=None,size=None,dtype=None):
        value=self.values.pop(0)
        result=np.asarray(value if np.ndim(value) else np.full(size or 1,value),dtype=dtype)
        return result if size is not None else result.item()


def test_attack_and_round_orchestrators_prove_phase_order_and_short_circuiting():
    strike = StrikeContext(
        hit=HitContext(3, 3),
        wound=WoundContext(3, 3),
        armour=ArmourContext(7),
    )
    result = resolve_attack(strike, ScriptedDice((6, 6, 5)))
    assert result.trace == (
        Phase.HIT,
        Phase.WOUND,
        Phase.ARMOUR,
        Phase.SPECIAL_SAVE,
        Phase.INJURY,
    )
    missed = resolve_attack(strike, ScriptedDice((1,)))
    assert missed.trace == (Phase.HIT,)
    round_result = resolve_strike_sequence(RoundContext(0, (strike,)), ScriptedDice((6, 6, 5)))
    assert round_result.state.trace == (
        Phase.DUEL_START,
        Phase.PRIORITY,
        Phase.ATTACKS,
        Phase.HIT,
        Phase.WOUND,
        Phase.ARMOUR,
        Phase.SPECIAL_SAVE,
        Phase.INJURY,
        Phase.AFTERMATH,
    )
    assert (round_result.state.attacks, round_result.state.hits, round_result.state.wounds) == (1, 1, 1)


def test_keyed_dice_replays_semantic_rolls_independently_of_request_order():
    first = KeyedDice(41)
    a = first.roll(RollRequest("round.0.hit"))
    b = first.roll(RollRequest("round.0.wound"))
    second = KeyedDice(41)
    assert second.roll(RollRequest("round.0.wound")) == b
    assert second.roll(RollRequest("round.0.hit")) == a

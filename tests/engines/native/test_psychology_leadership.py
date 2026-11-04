"""Psychology and Leadership in the compiled core: one contract per capability.

Each case takes the frozen ``scenario/basic`` pair, grants the tags the
capability reads and drives the native batch core alone with a strict die
tape, so the outcome is a fixed fact of the oracle's rules (which dice were
drawn, which decision keys were asked, what the warriors did).  Nothing here
samples the modular oracle or compares engines.
"""
from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from pathlib import Path

import numpy as np
import pytest

from mordheim_core.models import DuelContext, LocalParticipant
from tools.verification.compiled_cases import load_cases

native = pytest.importorskip("mordheim_combat._combat_native")

_CORPUS = Path(__file__).resolve().parents[1] / "fixtures" / "compiled-cases.json"
_STILL = DuelContext(charging=(), active_participant="first")


@lru_cache(maxsize=1)
def _pair():
    case = load_cases(_CORPUS)["scenario/basic"]
    return case.first, case.second


def _tagged(fighter, *tags, leadership=None):
    effects = replace(fighter.global_effects, tags=(*fighter.global_effects.tags, *tags))
    stats = fighter.characteristics if leadership is None else replace(
        fighter.characteristics, leadership=leadership)
    return replace(fighter, global_effects=effects, characteristics=stats)


class _Tape:
    """Strict die tape: every integer draw is scripted, ties pick the first."""

    def __init__(self, *values):
        self.values = list(values)

    def integers(self, low, high, size=None):
        count = 1 if size is None else int(size)
        if count > len(self.values):
            raise AssertionError("die tape exhausted")
        drawn, self.values = self.values[:count], self.values[count:]
        return np.asarray(drawn, dtype=np.int8)

    def random(self, size=None):
        return np.zeros(size)

    def finish(self):
        assert not self.values, f"unused dice {self.values}"


class _Accept:
    def __init__(self):
        self.keys = []

    def choose(self, key, context=None):
        self.keys.append(key)
        return True


def test_failed_fear_test_cancels_the_charge_and_leaves_the_duel_unresolved():
    first, second = _pair()
    first = _tagged(first, "mechanic.causes-fear")
    context = DuelContext(charging=("second",), active_participant="second")
    tape = _Tape(6, 6)  # the charger's Fear test, 12 against Leadership 7
    trace = {}
    result = native.simulate_batch_observed(first, second, 1, tape, 3, _Accept(), context=context, trace=trace)
    tape.finish()
    # The failed voluntary charge never makes contact: no blow is struck in
    # that round and no later round opens.
    assert int(result.rounds[0]) == 1 and int(result.winner[0]) == 0
    assert int(result.first_wounds[0]) == first.characteristics.wounds
    assert int(result.second_wounds[0]) == second.characteristics.wounds
    assert trace["phases"].count("attacks") == 0


def test_stupidity_is_exempted_by_a_nearby_handler_and_tested_without_one():
    first, second = _pair()
    first = _tagged(first, "mechanic.stupidity", "mechanic.bear-handler-recipient")
    tamer = replace(_tagged(second, "mechanic.bear-handler"), fighter_id="tamer")

    def run(inches, tape):
        context = DuelContext(
            nearby=(LocalParticipant("tamer", "first", tamer),),
            distances=(("first", "tamer", inches),),
            charging=(), active_participant="first",
        )
        result = native.simulate_batch_observed(first, second, 1, tape, 1, _Accept(), context=context)
        tape.finish()
        return result

    # Within six inches: no test; the bearer strikes (one hit die each).
    run(4.0, _Tape(1, 1))
    # Beyond six inches: the test is taken (6+6 fails Leadership 7) and the
    # stupid warrior strikes no one, so only the opponent draws a hit die.
    run(8.0, _Tape(6, 6, 1))


def test_a_nearby_leader_lends_his_leadership_and_the_reroll_is_offered():
    first, second = _pair()
    first = _tagged(first, "mechanic.stupidity", "mechanic.leadership-reroll", "band.test", leadership=5)
    boss = replace(_tagged(second, "mechanic.leader-six", "band.test", leadership=10), fighter_id="boss")
    context = DuelContext(
        nearby=(LocalParticipant("boss", "first", boss),),
        distances=(("first", "boss", 5.0),),
        charging=(), active_participant="first",
    )
    policy = _Accept()
    # 6+6 fails even the borrowed 10; the re-roll's 3+3 passes it; then both
    # warriors strike once and miss.
    tape = _Tape(6, 6, 3, 3, 1, 1)
    native.simulate_batch_observed(first, second, 1, tape, 1, policy, context=context)
    tape.finish()
    assert policy.keys == ["round.0.first.stupidity.leader.boss", "round.0.first.stupidity.reroll"]


def test_hypnotic_gaze_bars_the_victim_and_makes_hits_against_it_automatic():
    first, second = _pair()
    second = _tagged(second, "mechanic.hypnotic-gaze")
    policy = _Accept()
    # The victim fails the gaze (6+6 against 7): it strikes nobody and the
    # Vampire's single blow needs no hit die, only its wound roll (a 1 fails).
    tape = _Tape(6, 6, 1)
    result = native.simulate_batch_observed(first, second, 1, tape, 1, policy, context=_STILL)
    tape.finish()
    assert "round.0.first.hypnotic-gaze" in policy.keys
    assert int(result.second_wounds[0]) == second.characteristics.wounds


def test_lahmia_seduction_releases_on_a_hit_without_wounds_and_retains_recovery():
    first, second = _pair()
    first = _tagged(first, "mechanic.lahmia-seduction")
    second = _tagged(second, "sex.male")
    regain = "round.1.second.lahmia-seduction.regain-control"
    for script, needs_recovery in (
        # Failed control test; hit without a wound; both attack next turn.
        ((6, 6, 6, 1, 1, 1), False),
        # A miss preserves control; failed Recovery keeps the victim barred.
        ((6, 6, 1, 6, 6, 1), True),
        # A miss preserves control; successful Recovery lets both attack.
        ((6, 6, 1, 1, 1, 1, 1), True),
    ):
        tape, policy = _Tape(*script), _Accept()
        result = native.simulate_batch_observed(
            first, second, 1, tape, 2, policy, context=_STILL)
        tape.finish()
        assert (regain in policy.keys) is needs_recovery
        assert int(result.rounds[0]) == 2
        assert int(result.first_wounds[0]) == first.characteristics.wounds
        assert int(result.second_wounds[0]) == second.characteristics.wounds

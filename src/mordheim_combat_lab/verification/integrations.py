"""verification.integrations: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from contextlib import ExitStack
import mordheim_combat.modular.duel as duel
import mordheim_combat.modular.rounds as rounds
import mordheim_combat.modular.state as combat_state
import mordheim_combat.phases as phases
from mordheim_core.models import SimulationCancelled
from mordheim_combat_lab.verification.dice import StrictDecisions
from mordheim_combat_lab.verification.dice import StrictDice
from mordheim_combat_lab.verification.reports import EvidenceMismatch
from mordheim_combat_lab.verification.reports import INTEGRATION_CHECKS
from mordheim_combat_lab.verification.scenarios import _build
from pathlib import Path
from threading import Event
from unittest.mock import patch


def verify_integrations(root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Small integration witnesses, not exhaustive duels or a second rules engine."""
    passed, errors = [], []
    first = _build({"main_weapon_id": "weapon.mace"}, root)
    second = _build({"characteristics": dict(weapon_skill=3, strength=3, toughness=3,
                     wounds=1, initiative=3, attacks=1), "armour_id": "armour.light-armour",
                     "defence_ids": ["defence.enchanted-skins"]}, root)

    def require(condition, message):
        if not condition:
            raise EvidenceMismatch(message)

    def phase_order():
        dice = StrictDice([
            {"key": "round.0.first.attack.0.hit", "value": 4},
            {"key": "round.0.first.attack.0.wound", "value": 4},
            {"key": "round.0.first.attack.0.armour", "value": 1},
            {"key": "round.0.first.attack.0.special.ward", "value": 1},
            {"key": "round.0.first.attack.0.injury.0", "value": 5},
        ])
        order = []
        def observe(name, resolver):
            def call(*args, **kwargs):
                order.append(name)
                return resolver(*args, **kwargs)
            return call
        expected = ["resolve_priority", "resolve_priority", "build_attacks", "build_attacks",
                    "resolve_hit", "resolve_wound", "resolve_armour", "resolve_special_save",
                    "resolve_injury"]
        with ExitStack() as stack:
            for name in set(expected):
                stack.enter_context(patch.object(phases, name, observe(name, getattr(phases, name))))
            duel_state = combat_state.DuelState(combat_state.initialize_fighter(first, dice, "first"),
                                        combat_state.initialize_fighter(second, dice, "second"),
                                        first_charged=True)
            result = rounds.resolve_round(first, second, duel_state, dice, StrictDecisions([]))
        dice.finish()
        require(order == expected, f"actual phase calls {order!r} != {expected!r}")
        require(result.state.round_index == 1 and result.state.second.condition == phases.Condition.OUT,
                "round failed to transfer lethal injury or increment round")
        require(result.state.first.wounds == 3, "out-of-action defender retaliated")

    def maximum_rounds():
        class Misses:
            def roll(self, request):
                return 1
        with patch.object(duel, "SeededDice", lambda seed: Misses()), patch.object(
                rounds, "resolve_round", wraps=rounds.resolve_round) as round_mock:
            result = duel.simulate_duel_reference(first, first, 3, maximum_rounds=2)
        require(round_mock.call_count == 6, "maximum round limit was not respected")
        require((result.first_wins, result.second_wins, result.unresolved, result.simulations) == (0, 0, 3, 3),
                "unresolved simulations were miscounted")

    def cancellation():
        cancelled = Event()
        cancelled.set()
        try:
            duel.simulate_duel_reference(first, second, 2, cancel_event=cancelled)
        except SimulationCancelled:
            pass
        else:
            raise EvidenceMismatch("cancelled simulation was executed")
        cancelled.clear()
        original = rounds.resolve_round
        def cancel_after_round(*args, **kwargs):
            result = original(*args, **kwargs)
            cancelled.set()
            return result
        with patch.object(rounds, "resolve_round", side_effect=cancel_after_round) as round_mock:
            try:
                duel.simulate_duel_reference(first, second, 3, maximum_rounds=2, cancel_event=cancelled)
            except SimulationCancelled:
                require(round_mock.call_count == 1, "cancellation was not observed after the first round")
            else:
                raise EvidenceMismatch("mid-simulation cancellation was ignored")

    def reproducibility():
        a = duel.simulate_duel_reference(first, second, 12, seed=23, maximum_rounds=5)
        b = duel.simulate_duel_reference(first, second, 12, seed=23, maximum_rounds=5)
        require(a == b, "same seed produced different duel results")
        require(a.first_wins + a.second_wins + a.unresolved == 12, "result counts do not add up")

    for name, run in zip(INTEGRATION_CHECKS, (phase_order, maximum_rounds, cancellation, reproducibility)):
        try:
            run()
        except Exception as error:
            errors.append(f"integration/{name}: {type(error).__name__}: {error}")
        else:
            passed.append(name)
    return tuple(passed), tuple(errors)

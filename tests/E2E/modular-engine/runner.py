"""Deterministic E2E execution through the production modular combat pipeline."""
from __future__ import annotations

from dataclasses import fields, is_dataclass, replace
from enum import Enum
from pathlib import Path

import mordheim_combat.modular.state as combat_state
import mordheim_combat.modular.rounds as rounds
import mordheim_combat.phases as phases
from mordheim_construction.compiler import compile_fighter
from mordheim_core.dice import DecisionPolicy, DiceSource
from mordheim_core.models import Characteristics, DuelContext, FighterBuild, LocalParticipant

from .corpus import CorpusError, assert_observations, lookup_observation
from .dice import EvidenceMismatch, StrictDecisions, StrictDice

#: The harness vocabulary keeps the copied-support name; the implementation is the
#: pure corpus lookup itself, so there is no second dotted-path reader to drift.
_lookup = lookup_observation

#: Fields ``execute_case`` accepts: the runner vocabulary plus the corpus metadata
#: (``audit_id``, ``covers``) and the refusal contract (``expect_error``), which is
#: interpreted by ``check_case`` and never reaches the engine.
CASE_FIELDS = frozenset({
    "id", "audit_id", "covers", "fighters", "initial_state", "duel_context", "maximum_rounds",
    "rolls", "decisions", "expect_initial", "expect_rounds", "expect_final", "expect_events",
    "expect_fighters", "expect_error",
})
#: Observation fields a refusal may not be combined with.
OBSERVATION_FIELDS = ("expect_initial", "expect_rounds", "expect_final", "expect_events",
                      "expect_fighters")


def _plain(value):
    if isinstance(value, Enum):
        return value.name
    if is_dataclass(value):
        return {f.name: _plain(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, dict):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(v) for v in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_plain(v) for v in value)
    return value


def _build(values: dict, root: Path):
    values = dict(values)
    if "characteristics" in values:
        values["characteristics"] = Characteristics(**values["characteristics"])
    elif not values.get("profile_id"):
        values["characteristics"] = Characteristics(3, 3, 3, 3, 3, 1)
    for name in ("defence_ids", "skill_ids", "preparation_ids", "special_rule_ids", "variant_ids"):
        if name in values:
            values[name] = tuple(values[name])
    return compile_fighter(FighterBuild("mordheim", **values), root)


def _state(fighter, values: dict, dice: DiceSource, key: str):
    current = combat_state.initialize_fighter(fighter, dice, key)
    return _apply_state(current, values)


def _check_fields(value, allowed, label):
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    unknown = set(value) - set(allowed)
    if unknown:
        raise ValueError(f"unknown {label} fields: {sorted(unknown)}")


def _apply_state(current, values: dict):
    _check_fields(values, (field.name for field in fields(current)), "initial state")
    values = dict(values)
    if "condition" in values:
        if not isinstance(values["condition"], str) or values["condition"] not in phases.Condition.__members__:
            raise ValueError(f"unknown condition: {values['condition']!r}")
        values["condition"] = phases.Condition[values["condition"]]
    for name in ("resources_spent", "broken_hands", "hampered_hands"):
        if name in values:
            entries = values[name]
            if not isinstance(entries, (list, tuple, set, frozenset)) or any(
                    not isinstance(entry, str) for entry in entries):
                raise ValueError(f"{name} must contain strings")
            values[name] = tuple(entries) if name == "hampered_hands" else frozenset(entries)
    for name, value in values.items():
        previous = getattr(current, name)
        if isinstance(previous, bool) and not isinstance(value, bool):
            raise ValueError(f"{name} must be a boolean")
        if type(previous) is int and type(value) is not int:
            raise ValueError(f"{name} must be an integer")
    if "last_shadow_dance" in values and values["last_shadow_dance"] is not None and not isinstance(
            values["last_shadow_dance"], str):
        raise ValueError("last_shadow_dance must be a string or null")
    return replace(current, **values)


def _duel_context(values, root: Path):
    if values is None:
        return None
    _check_fields(values, (field.name for field in fields(DuelContext)), "duel context")
    values = dict(values)
    nearby = []
    for provider in values.get("nearby", ()):
        _check_fields(provider, (field.name for field in fields(LocalParticipant)), "nearby participant")
        provider = dict(provider)
        provider["fighter"] = _build(provider["fighter"], root)
        nearby.append(LocalParticipant(**provider))
    values["nearby"] = tuple(nearby)
    return DuelContext(**values)


def _snapshot(state):
    observed = _plain(state)
    observed["first_player_turn"] = state.first_player_turn
    observed["initial_charge_flags"] = _plain(state.initial_charge_flags)
    first_id, second_id = (("first", "second") if state.context is None else
                           (state.context.facts.first_id, state.context.facts.second_id))
    observed["active_participant"] = first_id if state.first_player_turn else second_id
    return observed


def _termination(state):
    if not state.first.active and not state.second.active:
        return "both_out"
    if not state.first.active:
        return "first_out"
    if not state.second.active:
        return "second_out"
    if not state.engaged:
        return "disengaged"
    return None


class _RecordingDice:
    def __init__(self, source: DiceSource, events: list):
        self.source, self.events = source, events

    def roll(self, request):
        value = self.source.roll(request)
        self.events.append({"kind": "roll", "key": request.key, "sides": request.sides, "value": value})
        return value


class _RecordingDecisions:
    def __init__(self, source: DecisionPolicy, events: list):
        self.source, self.events = source, events

    def choose(self, key, context=None):
        value = self.source.choose(key, context)
        self.events.append({"kind": "decision", "key": key, "value": value})
        return value


def execute_case(case: dict, root: Path, dice: DiceSource, decisions: DecisionPolicy) -> dict:
    """Build and initialize once, then carry the real state through combat phases."""
    _check_fields(case, CASE_FIELDS, "E2E case")
    maximum = case.get("maximum_rounds", 1)
    if type(maximum) is not int or maximum < 1:
        raise ValueError("maximum_rounds must be a positive integer")
    builds = case.get("fighters", {})
    overrides = case.get("initial_state", {})
    _check_fields(builds, {"first", "second"}, "fighters")
    _check_fields(overrides, {"first", "second"}, "initial_state")
    first, second = (_build(builds.get(side, {}), root) for side in ("first", "second"))
    context = _duel_context(case.get("duel_context"), root)
    events = []
    recorded_dice = _RecordingDice(dice, events)
    recorded_decisions = _RecordingDecisions(decisions, events)
    state = combat_state.initialize_duel(first, second, recorded_dice, context=context)
    state = replace(state,
        first=_apply_state(state.first, overrides.get("first", {})),
        second=_apply_state(state.second, overrides.get("second", {})),
    )
    initial = _snapshot(state)
    ledger = []
    for _ in range(maximum):
        if _termination(state) is not None:
            break
        active = _snapshot(state)["active_participant"]
        index = state.round_index
        outcome = rounds.resolve_round(first, second, state, recorded_dice, recorded_decisions)
        state = outcome.state
        ledger.append({"round_index": index, "active_participant": active,
                       "state": _snapshot(state), "attacks": _plain(outcome.attacks)})
    return {
        "fighters": _plain({"first": first, "second": second}),
        "initial": initial,
        "rounds": ledger,
        "final": {"state": _snapshot(state), "rounds_executed": len(ledger),
                  "termination_reason": _termination(state) or "horizon"},
        "events": events,
    }


def _assert_observations(observed, expected, label):
    """Delegate the pure dotted-path assertion; keep the evidence-mismatch type."""
    try:
        assert_observations(observed, expected, label)
    except CorpusError as error:
        raise EvidenceMismatch(str(error)) from error


def _declared_rejection(case: dict) -> str | None:
    """Return the declared refusal reason, or ``None`` for an observational case."""
    if "expect_error" not in case:
        return None
    declared = case["expect_error"]
    if not isinstance(declared, str) or not declared.strip():
        raise ValueError("expect_error must be a nonempty string")
    combined = [name for name in OBSERVATION_FIELDS if name in case]
    if combined:
        raise ValueError(
            f"expect_error cannot be combined with an observation: {sorted(combined)}")
    return declared


def check_case(case: dict, root: Path) -> dict:
    """Run one strict E2E scenario and check every declared observation.

    A scenario may declare ``expect_error`` instead of an observation: the build
    must then be refused and the diagnostic must name the authored reason
    fragment, so an unrelated failure cannot satisfy the declaration and a case
    that runs at all fails with ``but the case ran``.
    """
    if not isinstance(case, dict):
        raise ValueError("E2E case must be a mapping")
    rejection = _declared_rejection(case)
    if rejection is None and not any(
            case.get(name) for name in ("expect_initial", "expect_rounds", "expect_final")) and (
            "expect_events" not in case) and ("expect_fighters" not in case):
        raise ValueError("an E2E case must assert an observation")
    dice = StrictDice(case.get("rolls", []))
    decisions = StrictDecisions(case.get("decisions", []))
    try:
        observed = execute_case(case, root, dice, decisions)
    except EvidenceMismatch as error:
        if rejection is None:
            raise
        raise EvidenceMismatch(
            f"expected the refusal {rejection!r}, but the case ran: {error}") from error
    except Exception as error:  # noqa: BLE001 - any rejected build is the declared refusal
        if rejection is None:
            raise
        if rejection not in str(error):
            raise EvidenceMismatch(
                f"rejection does not name {rejection!r}: {type(error).__name__}: {error}") from error
        return {"refused": True, "expect_error": rejection, "error": str(error)}
    if rejection is not None:
        raise EvidenceMismatch(f"expected the refusal {rejection!r}, but the case ran")
    dice.finish()
    decisions.finish()
    for name, output in (("expect_initial", "initial"), ("expect_final", "final"),
                         ("expect_fighters", "fighters")):
        if name in case:
            _assert_observations(observed[output], case[name], output)
    if "expect_rounds" in case:
        checkpoints = case["expect_rounds"]
        if not isinstance(checkpoints, dict) or not checkpoints:
            raise ValueError("expect_rounds must be a nonempty mapping")
        for index, expected in checkpoints.items():
            if isinstance(index, bool) or not (
                    isinstance(index, int) or isinstance(index, str) and index.isdecimal()):
                raise ValueError("round checkpoints must be non-negative integer indices")
            index = int(index)
            if index < 0:
                raise ValueError("round checkpoints must be non-negative integer indices")
            if index >= len(observed["rounds"]):
                raise EvidenceMismatch(f"round checkpoint {index} was not executed")
            _assert_observations(observed["rounds"][index], expected, f"rounds.{index}")
    if "expect_events" in case:
        if not isinstance(case["expect_events"], list):
            raise ValueError("expect_events must be an ordered list")
        if observed["events"] != case["expect_events"]:
            raise EvidenceMismatch(f"events: got {observed['events']!r}, expected {case['expect_events']!r}")
    return observed

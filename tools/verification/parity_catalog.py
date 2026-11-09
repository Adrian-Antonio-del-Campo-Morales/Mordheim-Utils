"""Every tool's ``--scenarios`` selection, resolved to runnable cases.

One vocabulary selects duels in every engine tool (benchmark, calibrate,
parity, samples).  Several values select their union, in the order given:

``small`` | ``normal`` | ``big``
    the cumulative levels of the 43 precompiled scenarios
``<name>`` | ``scenario/<name>``
    one precompiled scenario
``realistic-50`` | ``realistic-100``
    the cumulative curated sets of realistic duels
``realistic/<nnn>``
    one curated realistic duel
``e2e``
    every E2E statistical delivery
``<case_key>`` | ``<audit_id::id>``
    one E2E delivery
``battery``
    every case of the statistical battery
``battery/<id>``
    one battery case

A curated realistic duel is a frozen corpus case like a precompiled scenario,
so it resolves the same way and no tool learns a second loading path.

``select`` turns the values into ordered entries without loading anything;
``load`` turns entries into runnable :class:`CampaignScenario` objects and
lists, with its reason, every entry a tool cannot run.  Precompiled scenarios
come from ``tests/engines/fixtures/compiled-cases.json`` (never compiled),
E2E deliveries go through their admission rules, and battery cases are
compiled from the knowledge base.  An input the engines' sample paths cannot
pass on (initial-state overrides, auxiliary participants, scripted dice or
decisions) rejects the case instead of running a different duel.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Mapping, NamedTuple, Sequence

from tests.engines.fixtures.precompiled_catalog import LEVELS
from tests.engines.fixtures.precompiled_catalog import SCENARIO_KEYS
from tests.engines.fixtures.precompiled_catalog import is_scenario_token
from tests.engines.fixtures.precompiled_catalog import scenarios_for_level
from tests.engines.fixtures.precompiled_catalog import select_scenarios
from tests.engines.fixtures.realistic_sets import REALISTIC_LEVELS
from tests.engines.fixtures.realistic_sets import is_realistic_token
from tests.engines.fixtures.realistic_sets import realistic_keys
from tools.verification.compiled_cases import CaseLimits
from tools.verification.compiled_cases import CaseOrigin
from tools.verification.compiled_cases import CompiledCase
from tools.verification.compiled_cases import encode_case
from tools.verification.e2e_parity import expressiveness

CORPUS = Path(__file__).resolve().parents[2] / "tests" / "engines" / "fixtures" / "compiled-cases.json"

#: The named sets ``--scenarios`` accepts besides individual names.
SETS = (*LEVELS, *REALISTIC_LEVELS, "e2e", "battery")

BATTERY_PREFIX = "battery/"


class Entry(NamedTuple):
    """One selected case: its key, its display name and its catalogue."""

    key: str
    name: str
    kind: str  # "scenario", "e2e" or "battery"


@dataclass(frozen=True, slots=True)
class CampaignScenario:
    """One selected case, resolved to the frozen inputs every engine runs."""

    key: str
    name: str
    case: CompiledCase
    kind: str = "scenario"


def _entries(level: str) -> tuple[tuple[str, str], ...]:
    return tuple(
        (SCENARIO_KEYS[scenario.name], scenario.name)
        for scenario in scenarios_for_level(level)
    )


#: Every maintained scenario as ``(corpus key, name)``, in catalogue order.
CATALOGUE: tuple[tuple[str, str], ...] = _entries("big")


def _battery_cases() -> dict:
    from mordheim_combat_lab.verification.parity import _battery_cases as battery

    return {str(case.id): case for case in battery.battery_cases()}


def _e2e_index() -> Mapping:
    from tools.verification import e2e_parity

    index, defects = e2e_parity.discover()
    if defects or not index:
        raise ValueError("; ".join(defects) or "the E2E delivery catalogue is empty")
    return index


def select(scenarios: Sequence[str] = ("small",)) -> tuple[Entry, ...]:
    """Resolve ``--scenarios`` values to ordered, de-duplicated entries.

    Raises ``ValueError`` naming every value that selects nothing.  The E2E
    catalogue is only read when a value needs it.
    """
    from tools.verification import e2e_parity

    entries: dict[str, Entry] = {}
    battery = index = None
    unknown: list[str] = []
    for token in dict.fromkeys(scenarios):
        if is_scenario_token(token):
            for scenario in select_scenarios((token,)):
                key = SCENARIO_KEYS[scenario.name]
                entries.setdefault(key, Entry(key, scenario.name, "scenario"))
        elif is_realistic_token(token):
            # A curated duel is a frozen case: the same "scenario" kind loads it.
            for key in realistic_keys(token):
                entries.setdefault(key, Entry(key, key, "scenario"))
        elif token == "battery" or token.startswith(BATTERY_PREFIX):
            battery = battery if battery is not None else _battery_cases()
            names = list(battery) if token == "battery" else [token[len(BATTERY_PREFIX):]]
            for name in names:
                if name not in battery:
                    unknown.append(token)
                    break
                entries.setdefault(BATTERY_PREFIX + name, Entry(BATTERY_PREFIX + name, name, "battery"))
        else:
            index = index if index is not None else _e2e_index()
            deliveries = (
                [index[key] for key in sorted(index)] if token == "e2e"
                else [e2e_parity.resolve(index, token)]
            )
            if deliveries == [None]:
                unknown.append(token)
                continue
            for delivery in deliveries:
                entries.setdefault(
                    delivery.case_key, Entry(delivery.case_key, delivery.test_id, "e2e"))
    if unknown:
        raise ValueError(
            "unknown scenario(s) " + ", ".join(repr(token) for token in unknown)
            + f"; use {', '.join(SETS)}, a scenario name, battery/<id> or an E2E "
            "delivery key"
        )
    return tuple(entries.values())


def _battery_case(entry: Entry, definitions: dict, root) -> CompiledCase:
    """Compile one battery case into the frozen-case shape the tools run."""
    from mordheim_combat_lab.verification.parity import _battery_cases as battery
    from mordheim_construction.compiler import compile_fighter

    definition = definitions[entry.name]
    limit = battery.input_limit(definition)
    if limit is not None:
        raise ValueError(limit)
    if dict(getattr(definition, "decisions", None) or {}):
        raise ValueError(
            "scripted decisions; only check parity's per-duel comparison runs them")
    case = CompiledCase(
        case_key=entry.key,
        origin=CaseOrigin("battery", entry.name,
                          "apps/combat-lab/mordheim_combat_lab/verification/parity/_battery_cases.py",
                          "0" * 64),
        first=compile_fighter(definition.first, root),
        second=compile_fighter(definition.second, root),
        context=battery.resolve_context(getattr(definition, "context", None), root),
        limits=CaseLimits(maximum_rounds=int(getattr(definition, "maximum_rounds", 50))),
    )
    return replace(case, fingerprints=encode_case(case)["fingerprints"])


def load(
    entries: Sequence[Entry], cases: Mapping[str, CompiledCase] | None = None,
) -> tuple[tuple[CampaignScenario, ...], tuple[tuple[str, str], ...]]:
    """Resolve entries to runnable cases.

    Returns the ready cases and, per entry that cannot run, the
    ``(key, reason)`` pair a report must list as not run.  A missing frozen
    case is never replaced by a compiled fighter.  ``cases`` supplies an
    already loaded frozen corpus.
    """
    from tools.verification import e2e_parity

    scenarios: list[CampaignScenario] = []
    rejected: list[tuple[str, str]] = []
    corpus = cases
    battery = index = policy = root = None
    for entry in entries:
        if entry.kind == "scenario":
            if corpus is None:
                from tools.verification.compiled_cases import load_cases

                corpus = load_cases(CORPUS)
            case = corpus.get(entry.key)
            if case is None:
                rejected.append((entry.key, f"the frozen corpus has no case {entry.key}"))
                continue
        elif entry.kind == "e2e":
            if index is None:
                index = _e2e_index()
                policy = e2e_parity.decision_policy_evidence()
                if not policy["corresponds"]:
                    # Without corresponding default policies no sample means
                    # anything; this is a fault of the run, not of a case.
                    raise ValueError(f"cannot admit E2E deliveries: {policy['detail']}")
            delivery = index[entry.key]
            admission = e2e_parity.admit(
                delivery.with_validation(e2e_parity.validate(delivery)),
                policy_corresponds=policy["corresponds"],
            )
            if admission.state != "admitted":
                rejected.append((entry.key, f"{admission.state}: {admission.detail}"))
                continue
            case = replace(admission.case, limits=replace(
                admission.case.limits, maximum_rounds=e2e_parity.CAMPAIGN_MAXIMUM_ROUNDS))
        else:
            if battery is None:
                from mordheim_knowledge.loader import knowledge_root

                battery, root = _battery_cases(), knowledge_root()
            try:
                case = _battery_case(entry, battery, root)
            except Exception as error:  # an unrunnable case is reported, not raised
                rejected.append((entry.key, f"incompatible: {error}"))
                continue
        limits = expressiveness(case)
        if limits:
            rejected.append((entry.key, "incompatible: " + "; ".join(limits)))
            continue
        scenarios.append(CampaignScenario(entry.key, entry.name, case, entry.kind))
    return tuple(scenarios), tuple(rejected)


def resolve(
    scenarios: Sequence[str] = ("small",),
) -> tuple[tuple[CampaignScenario, ...], tuple[tuple[str, str], ...], tuple[Entry, ...]]:
    """``--scenarios`` values to ``(runnable cases, rejected, selected entries)``."""
    entries = select(scenarios)
    runnable, rejected = load(entries)
    return runnable, rejected, entries


__all__ = (
    "CATALOGUE",
    "CORPUS",
    "LEVELS",
    "SETS",
    "CampaignScenario",
    "Entry",
    "is_scenario_token",
    "load",
    "resolve",
    "select",
)

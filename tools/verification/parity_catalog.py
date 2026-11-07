"""The precompiled parity catalogue: 43 frozen scenarios, their keys and levels.

Every scenario addresses ``tests/engines/fixtures/compiled-cases.json`` through
one uniform key, ``scenario/<name>``.  The definitions, the names and the three
cumulative levels (``small``, ``normal``, ``big``) live in
``tests.engines.fixtures.precompiled_catalog``, whose ``select_scenarios``
resolves every tool's ``--scenarios`` values; this module derives the corpus
keys, and never samples an engine, compiles a fighter or runs a duel.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from tests.engines.fixtures.precompiled_catalog import LEVELS
from tests.engines.fixtures.precompiled_catalog import SCENARIO_KEYS
from tests.engines.fixtures.precompiled_catalog import is_scenario_token
from tests.engines.fixtures.precompiled_catalog import scenarios_for_level
from tests.engines.fixtures.precompiled_catalog import select_scenarios
from tools.verification.compiled_cases import CompiledCase
from tools.verification.e2e_parity import expressiveness

CORPUS = Path(__file__).resolve().parents[2] / "tests" / "engines" / "fixtures" / "compiled-cases.json"


@dataclass(frozen=True, slots=True)
class CampaignScenario:
    """One frozen scenario, already resolved against the corpus."""

    key: str
    name: str
    case: CompiledCase


def _entries(level: str) -> tuple[tuple[str, str], ...]:
    return tuple(
        (SCENARIO_KEYS[scenario.name], scenario.name)
        for scenario in scenarios_for_level(level)
    )


#: Every maintained scenario as ``(corpus key, name)``, in catalogue order.
CATALOGUE: tuple[tuple[str, str], ...] = _entries("big")


def select(scenarios: Sequence[str] = ("small",)) -> tuple[tuple[str, str], ...]:
    """Return the ``(corpus key, name)`` entries for ``--scenarios`` values.

    A value is a level (``small``, ``normal``, ``big``), a scenario name or its
    corpus key (``scenario/<name>``); several values select their union, in
    catalogue order.  An unknown value raises ``ValueError``.
    """
    return tuple(
        (SCENARIO_KEYS[scenario.name], scenario.name)
        for scenario in select_scenarios(scenarios)
    )


def load(
    keys: Sequence[tuple[str, str]], cases: Mapping[str, CompiledCase],
) -> tuple[tuple[CampaignScenario, ...], tuple[tuple[str, str], ...]]:
    """Resolve catalogue entries against loaded frozen cases.

    Returns the ready scenarios and, per entry the corpus does not contain, the
    ``(key, reason)`` pair a report must list as not run.  A missing frozen case
    is never replaced by a compiled fighter, and a case carrying inputs the
    samplers cannot pass on (initial-state overrides, auxiliary participants,
    scripted dice or decisions) is rejected rather than sampled without them.
    """
    scenarios: list[CampaignScenario] = []
    rejected: list[tuple[str, str]] = []
    for key, name in keys:
        case = cases.get(key)
        if case is None:
            rejected.append((key, f"the frozen corpus has no case {key}"))
            continue
        limits = expressiveness(case)
        if limits:
            rejected.append((key, "incompatible: " + "; ".join(limits)))
            continue
        scenarios.append(CampaignScenario(key, name, case))
    return tuple(scenarios), tuple(rejected)


__all__ = (
    "CATALOGUE",
    "CORPUS",
    "LEVELS",
    "is_scenario_token",
    "CampaignScenario",
    "load",
    "select",
)

"""The precompiled parity catalogue: 43 frozen scenarios, their keys and levels.

Every scenario addresses ``tests/engines/fixtures/compiled-cases.json`` through
one uniform key, ``scenario/<name>``.  The definitions, the names and the three
cumulative levels live in ``tests.engines.fixtures.precompiled_catalog``; this
module derives the corpus keys and resolves a selection, and never samples an
engine, compiles a fighter or runs a duel.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from tests.engines.fixtures.precompiled_catalog import LEVELS
from tests.engines.fixtures.precompiled_catalog import SCENARIO_KEYS
from tests.engines.fixtures.precompiled_catalog import scenarios_for_level
from tools.verification.compiled_cases import CompiledCase

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
CATALOGUE: tuple[tuple[str, str], ...] = _entries("long")


def select(
    *, level: str = "small", keys: Sequence[str] = (),
) -> tuple[tuple[str, str], ...]:
    """Return the catalogue entries a campaign should run.

    ``level`` is one of the cumulative scenario levels (``small`` by default).
    ``keys`` narrows the selection to uniform corpus keys
    (``scenario/<name>``); naming a key outside the level is an error rather
    than a silent omission.
    """
    chosen = _entries(level)
    if not keys:
        return chosen
    wanted = set(keys)
    available = {entry[0] for entry in chosen}
    missing = sorted(wanted - available)
    if missing:
        raise ValueError(
            "scenario key(s) not selected: "
            + ", ".join(missing)
            + f" (level {level!r} covers {len(chosen)} entries; "
            "widen --level or fix the key)"
        )
    return tuple(entry for entry in chosen if entry[0] in wanted)


def load(
    keys: Sequence[tuple[str, str]], cases: Mapping[str, CompiledCase],
) -> tuple[tuple[CampaignScenario, ...], tuple[tuple[str, str], ...]]:
    """Resolve catalogue entries against loaded frozen cases.

    Returns the ready scenarios and, per entry the corpus does not contain, the
    ``(key, reason)`` pair a report must list as not run.  A missing frozen case
    is never replaced by a compiled fighter.
    """
    scenarios: list[CampaignScenario] = []
    rejected: list[tuple[str, str]] = []
    for key, name in keys:
        case = cases.get(key)
        if case is None:
            rejected.append((key, f"the frozen corpus has no case {key}"))
            continue
        scenarios.append(CampaignScenario(key, name, case))
    return tuple(scenarios), tuple(rejected)


__all__ = (
    "CATALOGUE",
    "CORPUS",
    "LEVELS",
    "CampaignScenario",
    "load",
    "select",
)

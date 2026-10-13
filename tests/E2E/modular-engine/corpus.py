"""Declarative E2E scenario corpus: loading and structural validation.

Each YAML document under ``cases/`` is a list of scenario mappings written in
the vocabulary documented in README.md.  A scenario declares the audit ID it
belongs to (``audit_id``) and the clause references it demonstrates
(``covers``); execution stays in ``runner.check_case``.  This module only
loads and validates declarations, so a malformed fixture fails with the file,
index and scenario ID that produced it.  Cross-checking ``audit_id`` and
``covers`` against the canonical audit register belongs to ``test_inventory``.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

CASES_DIRECTORY = Path(__file__).parent / "cases"

#: Fields added by the corpus on top of the runner's case vocabulary.
METADATA_FIELDS = frozenset({"audit_id", "covers"})
#: Fields accepted by ``runner.execute_case``.
RUNNER_FIELDS = frozenset({
    "id", "fighters", "initial_state", "duel_context", "maximum_rounds",
    "rolls", "decisions", "expect_initial", "expect_rounds", "expect_final",
    "expect_events", "expect_error",
})
KNOWN_FIELDS = RUNNER_FIELDS | METADATA_FIELDS
ASSERTION_FIELDS = ("expect_initial", "expect_rounds", "expect_final", "expect_events",
                    "expect_error")


class CorpusError(ValueError):
    """A malformed or inconsistent declarative scenario definition."""


@dataclass(frozen=True)
class Scenario:
    audit_id: str
    scenario_id: str
    covers: tuple[str, ...]
    case: dict
    source: str

    @property
    def test_id(self) -> str:
        """The ``audit-ID::scenario-ID`` collection identity."""
        return f"{self.audit_id}::{self.scenario_id}"


def _fail(source, index, message, scenario_id=None):
    where = f"{source}[{index}]"
    if scenario_id:
        where += f" ({scenario_id})"
    raise CorpusError(f"{where}: {message}")


def _text(value, label, source, index, scenario_id=None):
    if not isinstance(value, str) or not value.strip():
        _fail(source, index, f"{label} must be a nonempty string", scenario_id)
    return value


def validate_scenario(raw, source: str, index: int) -> Scenario:
    """Validate one declared scenario and return its corpus record."""
    if not isinstance(raw, dict):
        _fail(source, index, "a scenario must be a mapping")
    unknown = sorted(set(raw) - KNOWN_FIELDS)
    if unknown:
        _fail(source, index, f"unknown scenario fields: {unknown}")
    scenario_id = _text(raw.get("id"), "id", source, index)
    audit_id = _text(raw.get("audit_id"), "audit_id", source, index, scenario_id)
    covers = raw.get("covers")
    if not isinstance(covers, list) or not covers:
        _fail(source, index, "covers must be a nonempty list of clause ids", scenario_id)
    for clause in covers:
        _text(clause, "covers entry", source, index, scenario_id)
    if not any(raw.get(name) for name in ASSERTION_FIELDS):
        _fail(source, index, "a scenario must assert an observation", scenario_id)
    if "expect_error" in raw and (not isinstance(raw["expect_error"], str)
                                 or not raw["expect_error"].strip()):
        _fail(source, index, "expect_error must be a nonempty string", scenario_id)
    for name in ("rolls", "decisions"):
        if name in raw and not isinstance(raw[name], list):
            _fail(source, index, f"{name} must be a list", scenario_id)
    for name in ("fighters", "initial_state", "duel_context"):
        if name in raw and raw[name] is not None and not isinstance(raw[name], dict):
            _fail(source, index, f"{name} must be a mapping", scenario_id)
    return Scenario(audit_id, scenario_id, tuple(covers), dict(raw), source)


def load_corpus(cases_directory: Path | None = None) -> list[Scenario]:
    """Load every ``*.yaml`` scenario under the case directory in file order."""
    directory = CASES_DIRECTORY if cases_directory is None else Path(cases_directory)
    scenarios: list[Scenario] = []
    declared: dict[str, str] = {}
    for path in sorted(directory.rglob("*.yaml")):
        source = path.relative_to(directory).as_posix()
        documents = yaml.safe_load(path.read_text(encoding="utf-8"))
        if documents is None:
            documents = []
        if not isinstance(documents, list):
            raise CorpusError(f"{source}: a corpus file must be a list of scenarios")
        for index, raw in enumerate(documents):
            scenario = validate_scenario(raw, source, index)
            if scenario.test_id in declared:
                raise CorpusError(
                    f"{source}[{index}]: duplicate scenario {scenario.test_id!r} "
                    f"(first declared in {declared[scenario.test_id]})")
            declared[scenario.test_id] = source
            scenarios.append(scenario)
    return scenarios


def group_by_audit(scenarios: Iterable[Scenario]) -> dict[str, list[Scenario]]:
    grouped: dict[str, list[Scenario]] = {}
    for scenario in scenarios:
        grouped.setdefault(scenario.audit_id, []).append(scenario)
    return grouped

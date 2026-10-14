"""Declarative E2E scenario corpus: loading, static contract and pure assertions.

Each YAML document under ``cases/`` is a list of scenario mappings written in
the vocabulary documented in README.md.  A scenario declares the audit ID it
belongs to (``audit_id``) and the clause references it demonstrates
(``covers``); execution stays in ``runner.check_case``.  This module only
loads and validates declarations, so a malformed fixture fails with the file,
index and scenario ID that produced it.  Cross-checking ``audit_id`` and
``covers`` against the canonical audit register belongs to ``test_inventory``.

The static contract lives in :func:`scenario_contract_errors`, a pure function
that decides nothing normative (no keyword bans, no fixture-key precedents) and
imports nothing from the combat packages, so the loader, the contract tests and
:class:`validate_corpus` (charts) can share it.  The dotted-path assertion the
runner applies to observations is also pure here
(:func:`assert_observations`); ``runner`` delegates to it and re-raises its
messages as the runtime evidence mismatch, keeping the observable contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import yaml

CASES_DIRECTORY = Path(__file__).parent / "cases"

#: Fields added by the corpus on top of the runner's case vocabulary.
METADATA_FIELDS = frozenset({"audit_id", "covers"})
#: Fields accepted by ``runner.execute_case`` / ``runner.check_case``.
RUNNER_FIELDS = frozenset({
    "id", "fighters", "initial_state", "duel_context", "maximum_rounds",
    "rolls", "decisions", "expect_initial", "expect_rounds", "expect_final",
    "expect_events", "expect_fighters", "expect_error",
})
#: Observation fields: a legitimate case always has at least one of these
#: declared (an empty ``expect_events`` list is the documented way to assert
#: that no event happens at all), and none may coexist with a refusal.
OBSERVATION_FIELDS = (
    "expect_initial", "expect_rounds", "expect_final", "expect_events",
    "expect_fighters",
)
#: The refusal contract: a scenario may instead declare ``expect_error`` alone.
REFUSAL_FIELD = "expect_error"
#: Every assertion channel a scenario may use.
ASSERTION_FIELDS = OBSERVATION_FIELDS + (REFUSAL_FIELD,)
#: ``fighters`` and ``initial_state`` address exactly these participants.
FIGHTER_KEYS = frozenset({"first", "second"})

KNOWN_FIELDS = RUNNER_FIELDS | METADATA_FIELDS


class CorpusError(ValueError):
    """A malformed or inconsistent declarative scenario definition."""


class ObservationMismatch(CorpusError):
    """A declared observation path does not match the observed structure."""


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


def _is_int(value):
    """True for a real integer; ``bool`` is an int subclass and is rejected."""
    return isinstance(value, int) and not isinstance(value, bool)


def scenario_contract_errors(raw: dict) -> list[str]:
    """Return every purely static contract violation of one scenario mapping.

    Must be called with a mapping that passed the vocabulary and identity
    checks, but every failure here is reported rather than raised so callers
    can aggregate.  Enforced: the refusal channel is exclusive, ``fighters``
    and ``initial_state`` address exactly ``first`` / ``second``,
    ``maximum_rounds`` is a positive integer (bool rejected), dice and
    decision scripts match the strict sources' declared shape, every
    observation map is a nonempty mapping of nonempty dotted paths (or, for
    ``expect_events``, a possibly empty list) and round checkpoints are
    non-negative integer indices.  It never decides normative legality and
    never requires a new rule key to have appeared in earlier fixtures.
    """
    errors: list[str] = []

    maximum = raw.get("maximum_rounds", 1)
    if not _is_int(maximum) or maximum < 1:
        errors.append(f"maximum_rounds must be a positive integer, got {maximum!r}")

    for carrier in ("fighters", "initial_state"):
        if carrier not in raw:
            continue
        container = raw[carrier]
        if container is None:
            # The runner's own field check rejects None at execution time; the
            # static contract mirrors that instead of deferring the failure.
            errors.append(f"{carrier} must be a mapping")
            continue
        if not isinstance(container, dict):
            errors.append(f"{carrier} must be a mapping")
            continue
        unknown = sorted(set(container) - FIGHTER_KEYS)
        if unknown:
            errors.append(
                f"{carrier} uses unknown participants: {unknown}; "
                f"allowed: {sorted(FIGHTER_KEYS)}")

    rolls = raw.get("rolls", [])
    if not isinstance(rolls, list):
        errors.append("rolls must be a list")
    else:
        for position, entry in enumerate(rolls):
            prefix = f"rolls entry {position}"
            if not isinstance(entry, dict):
                errors.append(f"{prefix} must be a mapping")
                continue
            key = entry.get("key")
            if not isinstance(key, str) or not key.strip():
                errors.append(f"{prefix} must declare a nonempty string key")
            if not _is_int(entry.get("value")):
                errors.append(
                    f"{prefix} must declare an integer die value; booleans are not dice values")
            else:
                sides = entry.get("sides", 6)
                if not _is_int(sides) or sides < 1:
                    errors.append(f"{prefix} must declare a positive integer side count")
                elif not 1 <= entry["value"] <= sides:
                    errors.append(
                        f"{prefix} die value {entry['value']} is outside the faces 1..{sides}"
                        + ("" if "sides" in entry else " (the default die is d6)"))
            unknown = sorted(set(entry) - {"key", "value", "sides"})
            if unknown:
                errors.append(f"{prefix} declares unknown fields: {unknown}")

    decisions = raw.get("decisions", [])
    if not isinstance(decisions, list):
        errors.append("decisions must be a list")
    else:
        for position, entry in enumerate(decisions):
            prefix = f"decisions entry {position}"
            if not isinstance(entry, dict):
                errors.append(f"{prefix} must be a mapping")
                continue
            key = entry.get("key")
            if not isinstance(key, str) or not key.strip():
                errors.append(f"{prefix} must declare a nonempty string key")
            if not isinstance(entry.get("value"), bool):
                errors.append(f"{prefix} values must be booleans")
            unknown = sorted(set(entry) - {"key", "value"})
            if unknown:
                errors.append(f"{prefix} declares unknown fields: {unknown}")

    for channel in ("expect_initial", "expect_final", "expect_fighters"):
        if channel in raw:
            expected = raw[channel]
            if (not isinstance(expected, dict) or not expected
                    or any(not isinstance(path, str) or not path for path in expected)):
                errors.append(
                    f"{channel} must be a nonempty mapping of nonempty dotted paths")

    if "expect_rounds" in raw:
        checkpoints = raw["expect_rounds"]
        if not isinstance(checkpoints, dict) or not checkpoints:
            errors.append("expect_rounds must be a nonempty mapping")
        else:
            for index, expected in checkpoints.items():
                index_ok = (
                    (isinstance(index, str) and index.isdecimal())
                    or (isinstance(index, int) and not isinstance(index, bool)))
                if not index_ok or int(index) < 0:
                    errors.append("round checkpoints must be non-negative integer indices")
                    continue
                if not isinstance(expected, dict) or not expected:
                    errors.append(f"round checkpoint {index} must be a nonempty mapping")

    if "expect_events" in raw and not isinstance(raw["expect_events"], list):
        errors.append("expect_events must be an ordered list (an empty list is valid)")

    if "expect_error" in raw:
        declared = raw["expect_error"]
        if not isinstance(declared, str) or not declared.strip():
            errors.append("expect_error must be a nonempty string")
        combined = [channel for channel in OBSERVATION_FIELDS if channel in raw]
        if combined:
            errors.append(
                f"expect_error cannot be combined with an observation: {sorted(combined)}")
    elif not (any(raw.get(channel) for channel in
                  ("expect_initial", "expect_rounds", "expect_final"))
              or "expect_events" in raw
              or "expect_fighters" in raw):
        errors.append("a scenario must assert an observation")

    return errors


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
    for error in scenario_contract_errors(raw):
        _fail(source, index, error, scenario_id)
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


def lookup_observation(observed, path: str, label: str = ""):
    """Resolve one dotted path against the observed structure.

    Pure, engine-free support shared with the runner; unknown segments and
    out-of-face list indices fail with the documented mismatch.
    """
    where = f"{label}.{path}" if label else path
    current = observed
    try:
        for part in path.split("."):
            current = current[int(part)] if isinstance(current, list) else current[part]
    except (KeyError, IndexError, ValueError, TypeError) as error:
        raise ObservationMismatch(f"{where}: observation does not exist") from error
    return current


def assert_observations(observed, expected: dict, label: str):
    """Compare a nonempty mapping of dotted paths with the observed structure.

    The comparison is value equality plus a strict bool/int split, so an
    expected ``true`` never matches an observed ``1``: the assertion rejects a
    bool substituted for an int and vice versa.
    """
    if not isinstance(expected, dict) or not expected:
        raise CorpusError(f"{label} expectations must be a nonempty mapping")
    for path, value in expected.items():
        if not isinstance(path, str) or not path:
            raise CorpusError(f"{label} observation paths must be nonempty strings")
        actual = lookup_observation(observed, path, label)
        if actual != value or isinstance(actual, bool) != isinstance(value, bool):
            where = f"{label}.{path}"
            raise ObservationMismatch(f"{where}: got {actual!r}, expected {value!r}")

"""Canonical audit-ID coverage: reconciliation, report and completeness gate.

The identity inventory of the knowledge base (``mordheim_knowledge.clauses``:
every core rule, mechanic, item and classified rule effect, with the clauses a
record declares when its printed text splits) is the canonical source of audit
identities and is never rewritten here.  A scenario must reference a declared
``core/``, ``mechanic/`` or ``rule/`` identity and, when that identity declares
clauses, one of its clauses; an identity without clauses is one undivided
obligation that any scenario naming it covers.  Scenarios of a declared identity
the runtime does not admit (a ``NO`` or ``LATER`` effect) are reported apart and
never count towards coverage.

Ordinary runs reconcile the declared corpus against the inventory and print the
coverage report.  The stricter gate that fails on any admitted identity without
scenarios or any uncovered admitted clause runs only when
``MORDHEIM_CONFORMANCE_REQUIRE_COMPLETE=1`` is set, mirroring the existing
``verify --require-complete`` convention.  This is conformance coverage evidence, not
behavioural proof: the scenarios must also run and pass.
"""
from __future__ import annotations

import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pytest

from mordheim_knowledge.clauses import admitted_clauses, declared_clauses, load_identities
from mordheim_conformance.corpus import Scenario, group_by_audit, load_corpus

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
#: Identity kinds the conformance corpus may declare; items are covered by deterministic tests.
ADMITTED_KINDS = ("core", "mechanic", "rule")
REQUIRE_COMPLETE_ENV = "MORDHEIM_CONFORMANCE_REQUIRE_COMPLETE"

CORPUS = load_corpus()
BY_AUDIT = group_by_audit(CORPUS)


def read_inventory():
    """Return the clause inventory grouped by identity and scope.

    ``declared`` holds every identity with the clause ids it declares
    (referential integrity for a scenario's ``covers``); ``admitted`` holds the
    admitted ``core/``, ``mechanic/`` and ``rule/`` identities with their
    in-scope clause ids, an empty set for an undivided identity (the coverage
    denominator).
    """
    identities = load_identities()
    declared = declared_clauses(identities)
    admitted = admitted_clauses(identities, ADMITTED_KINDS)
    return declared, admitted, set(admitted)


@dataclass(frozen=True)
class Coverage:
    scenario_count: int
    covered_clauses: dict[str, set[str]]
    admitted_clauses: dict[str, set[str]]
    admitted_ids: frozenset[str]
    #: Declared identities with scenarios that the runtime does not admit (NO/LATER effects).
    outside_scope: tuple[str, ...] = ()

    @property
    def covered_ids(self) -> set[str]:
        return set(self.covered_clauses)

    @property
    def missing_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self.admitted_ids - self.covered_ids))

    def uncovered(self) -> dict[str, tuple[str, ...]]:
        gaps = {}
        for current, clauses in self.admitted_clauses.items():
            missing = clauses - self.covered_clauses.get(current, set())
            if missing:
                gaps[current] = tuple(sorted(missing))
        return gaps

    def complete_ids(self) -> tuple[str, ...]:
        """Identities whose every in-scope clause is named, or undivided identities with a scenario."""
        return tuple(sorted(
            current for current, clauses in self.admitted_clauses.items()
            if current in self.covered_clauses and not (clauses - self.covered_clauses.get(current, set()))
        ))

    def render(self, *, missing_limit: int = 20) -> str:
        admitted_clause_count = sum(len(c) for c in self.admitted_clauses.values())
        covered_clause_count = sum(
            len(clauses & self.covered_clauses.get(current, set()))
            for current, clauses in self.admitted_clauses.items()
        )
        gaps = {current: clauses for current, clauses in self.uncovered().items()
                if current in self.covered_clauses}
        missing = self.missing_ids
        lines = [
            "Rules-conformance coverage",
            f"  scenarios declared: {self.scenario_count}",
            f"  audit identities with scenarios: {len(self.covered_ids)} / {len(self.admitted_ids)} admitted",
            f"  admitted clauses covered: {covered_clause_count} / {admitted_clause_count}",
            f"  identities with complete admitted-clause coverage: {len(self.complete_ids())}",
            f"  admitted identities without scenarios: {len(missing)}",
            "  complete coverage means every in-scope clause of a split identity has a scenario that",
            "  declares it, or an undivided identity has a scenario; it is a reference count, not",
            "  semantic certification of the identity",
        ]
        lines.extend(f"    {current}" for current in missing[:missing_limit])
        if len(missing) > missing_limit:
            lines.append(f"    ... {len(missing) - missing_limit} more")
        if self.outside_scope:
            lines.append(f"  scenarios on identities outside the admitted scope (NO/LATER effects): {len(self.outside_scope)}")
            lines.extend(f"    {current}" for current in self.outside_scope)
        for current in sorted(gaps):
            lines.append(f"  pending clauses in a covered identity: {current} {list(gaps[current])}")
        return "\n".join(lines)


def coverage(scenarios: Iterable[Scenario] | None = None) -> Coverage:
    """Coverage over the admitted identities; scenarios of declared but not admitted identities are kept apart."""
    scenarios = list(CORPUS if scenarios is None else scenarios)
    grouped = group_by_audit(scenarios)
    _, admitted, admitted_ids = read_inventory()
    covered = {current: {clause for scenario in group for clause in scenario.covers}
               for current, group in grouped.items() if current in admitted_ids}
    outside = tuple(sorted(current for current in grouped if current not in admitted_ids))
    return Coverage(len(scenarios), covered, admitted, frozenset(admitted_ids), outside)


@pytest.mark.evidence
def test_corpus_references_admitted_identities_and_clauses():
    declared, admitted, admitted_ids = read_inventory()
    for scenario in CORPUS:
        assert scenario.audit_id in declared, (
            f"{scenario.test_id}: audit id is not a knowledge-base identity")
        for clause in scenario.covers:
            assert clause in declared[scenario.audit_id], (
                f"{scenario.test_id}: clause {clause!r} is not a clause of {scenario.audit_id}")
            if scenario.audit_id in admitted_ids:
                assert clause in admitted[scenario.audit_id], (
                    f"{scenario.test_id}: clause {clause!r} is not an admitted clause of "
                    f"{scenario.audit_id}")


@pytest.mark.evidence
def test_coverage_report_reconciliation():
    report = coverage()
    print(report.render())
    assert report.scenario_count == len(CORPUS)
    assert report.covered_ids <= set(report.admitted_ids)
    assert set(report.uncovered()) <= set(report.admitted_ids)


@pytest.mark.evidence
def test_completeness_gate():
    """Fail the full gate only when completeness is explicitly requested.

    The failure stays readable for a large corpus: it reports counts plus a
    bounded sample.  Run ``test_coverage_report_reconciliation -s`` for the
    full report while the corpus is being built out.
    """
    report = coverage()
    if os.environ.get(REQUIRE_COMPLETE_ENV) != "1":
        return
    sample = 10
    gaps = report.uncovered()
    problems = []
    if report.missing_ids:
        missing = list(report.missing_ids)
        problems.append(
            f"{len(missing)} admitted identities without scenarios, e.g. {missing[:sample]}")
    if gaps:
        pending = {current: list(clauses) for current, clauses in sorted(gaps.items())[:sample]}
        problems.append(
            f"{len(gaps)} identities with uncovered admitted clauses, e.g. {pending}")
    if problems:
        pytest.fail("; ".join(problems))

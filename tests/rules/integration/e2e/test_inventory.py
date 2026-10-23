"""Canonical audit-ID coverage: reconciliation, report and completeness gate.

The register (``sources/knowledge/verification/clause-contracts.csv``) is read
as the canonical source of audit identities and clauses and is never rewritten
here.  A scenario may only reference an admitted ``core/``, ``mechanic/`` or
``rule/`` identity and an in-scope clause of that identity; sharing a binding
does not admit an excluded clause.

Ordinary runs reconcile the declared corpus against the register and print the
coverage report.  The stricter gate that fails on any admitted identity without
scenarios or any uncovered admitted clause runs only when
``MORDHEIM_E2E_REQUIRE_COMPLETE=1`` is set, mirroring the existing
``verify --require-complete`` convention.  This is E2E coverage evidence and
never replaces the maintained ``semantic_status`` of the reference suite.
"""
from __future__ import annotations

import csv
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import pytest

from mordheim_modular_e2e.corpus import Scenario, group_by_audit, load_corpus

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
REGISTER = REPOSITORY_ROOT / "sources" / "knowledge" / "verification" / "clause-contracts.csv"
ADMITTED_PREFIXES = ("core/", "mechanic/", "rule/")
IN_SCOPE = "YES"
REQUIRE_COMPLETE_ENV = "MORDHEIM_E2E_REQUIRE_COMPLETE"

CORPUS = load_corpus()
BY_AUDIT = group_by_audit(CORPUS)


def read_register():
    """Return the register grouped by current identity and scope.

    ``declared`` holds every printed clause of every identity (referential
    integrity for a scenario's ``covers``); ``admitted`` holds only the
    in-scope clauses of the admitted ``core/``, ``mechanic/`` and ``rule/``
    identities (the coverage denominator).
    """
    with REGISTER.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    declared: dict[str, set[str]] = {}
    admitted: dict[str, set[str]] = {}
    for row in rows:
        current = row["id"]
        declared.setdefault(current, set()).add(row["clause_id"])
        if row["clause_scope"] == IN_SCOPE and current.startswith(ADMITTED_PREFIXES):
            admitted.setdefault(current, set()).add(row["clause_id"])
    return declared, admitted, set(admitted)


@dataclass(frozen=True)
class Coverage:
    scenario_count: int
    covered_clauses: dict[str, set[str]]
    admitted_clauses: dict[str, set[str]]
    admitted_ids: frozenset[str]

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
        return tuple(sorted(
            current for current, clauses in self.admitted_clauses.items()
            if clauses and not (clauses - self.covered_clauses.get(current, set()))
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
            "E2E modular engine coverage",
            f"  scenarios declared: {self.scenario_count}",
            f"  audit identities with scenarios: {len(self.covered_ids)} / {len(self.admitted_ids)} admitted",
            f"  admitted clauses covered: {covered_clause_count} / {admitted_clause_count}",
            f"  identities with complete admitted-clause coverage: {len(self.complete_ids())}",
            f"  admitted identities without scenarios: {len(missing)}",
            "  complete admitted-clause coverage means every in-scope clause has a scenario that",
            "  declares it; it is a reference count, not semantic certification of the identity",
        ]
        lines.extend(f"    {current}" for current in missing[:missing_limit])
        if len(missing) > missing_limit:
            lines.append(f"    ... {len(missing) - missing_limit} more")
        for current in sorted(gaps):
            lines.append(f"  pending clauses in a covered identity: {current} {list(gaps[current])}")
        return "\n".join(lines)


def coverage(scenarios: Iterable[Scenario] | None = None) -> Coverage:
    scenarios = list(CORPUS if scenarios is None else scenarios)
    grouped = group_by_audit(scenarios)
    covered = {current: {clause for scenario in group for clause in scenario.covers}
               for current, group in grouped.items()}
    _, admitted, admitted_ids = read_register()
    return Coverage(len(scenarios), covered, admitted, frozenset(admitted_ids))


@pytest.mark.evidence
def test_corpus_references_admitted_identities_and_clauses():
    declared, admitted, admitted_ids = read_register()
    for scenario in CORPUS:
        assert scenario.audit_id in declared, (
            f"{scenario.test_id}: audit id is not in the register")
        assert scenario.audit_id in admitted_ids, (
            f"{scenario.test_id}: audit id is not admitted ({scenario.source})")
        for clause in scenario.covers:
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

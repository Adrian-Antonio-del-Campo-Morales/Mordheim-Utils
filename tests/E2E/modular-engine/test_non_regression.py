"""Accepted coverage evidence and the non-regression control that protects it.

``evidence/coverage-baseline.yaml`` is a reviewed test artefact, not another
editorial rules register.  For every identity the corpus had already accepted it
records the protected scenario identities and the clause references each
scenario demonstrates.

The control compares that reference with the live corpus set-wise.  Counting
scenarios or clauses would let a substitution pass: replacing a reviewed
scenario with a different one that happens to keep the count hides a real loss.
Here a missing identity, a missing scenario, a scenario that dropped a clause
reference, and a clause that is no longer admitted are each a regression.

The reference is never rewritten by this module, and a moved register revision
does not by itself pass or fail the check: the accepted clauses are re-verified
against the register's current scope instead of trusting the recorded digest.

This is E2E coverage evidence.  It is separate from the opt-in global
completeness gate in ``test_inventory.py``, which still lists every pending
identity and clause and still fails when completeness is requested.
"""
from __future__ import annotations

import csv
import hashlib
from dataclasses import replace
from pathlib import Path

import yaml

from mordheim_modular_e2e.corpus import Scenario, group_by_audit, load_corpus

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
BASELINE_PATH = Path(__file__).parent / "evidence" / "coverage-baseline.yaml"
ADMITTED_PREFIXES = ("core/", "mechanic/", "rule/")
IN_SCOPE = "YES"

CORPUS = load_corpus()


def load_baseline(path: Path | None = None) -> dict:
    """Read the accepted-evidence reference; it is read-only for the tests."""
    document = yaml.safe_load((BASELINE_PATH if path is None else path).read_text(encoding="utf-8"))
    if not isinstance(document, dict) or not isinstance(document.get("identities"), dict):
        raise ValueError("the coverage baseline must declare an identities mapping")
    for audit_id, entry in document["identities"].items():
        if not isinstance(entry, dict) or not isinstance(entry.get("scenarios"), dict):
            raise ValueError(f"the coverage baseline entry {audit_id!r} must declare scenarios")
    return document


def register_view(baseline: dict) -> tuple[dict[str, set[str]], str]:
    """Return the currently admitted clauses and the register digest."""
    path = REPOSITORY_ROOT / baseline["register"]["path"]
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    admitted: dict[str, set[str]] = {}
    for row in rows:
        if row["clause_scope"] == IN_SCOPE and row["current_id"].startswith(ADMITTED_PREFIXES):
            admitted.setdefault(row["current_id"], set()).add(row["clause_id"])
    return admitted, hashlib.sha256(path.read_bytes()).hexdigest()


def regressions(baseline: dict, scenarios: list[Scenario],
                admitted: dict[str, set[str]]) -> list[str]:
    """Set-wise losses of accepted evidence in a candidate corpus."""
    by_identity = group_by_audit(scenarios)
    problems: list[str] = []
    for audit_id, accepted in sorted(baseline["identities"].items()):
        declared = {scenario.scenario_id: set(scenario.covers)
                    for scenario in by_identity.get(audit_id, [])}
        if not declared:
            problems.append(f"{audit_id}: accepted identity has no scenarios left")
            continue
        for name, clauses in sorted(accepted["scenarios"].items()):
            if name not in declared:
                problems.append(f"{audit_id}::{name}: accepted scenario is gone")
                continue
            dropped = set(clauses) - declared[name]
            if dropped:
                problems.append(
                    f"{audit_id}::{name}: accepted clause references dropped: {sorted(dropped)}")
        for clause in accepted.get("clauses", ()):
            if not any(clause in clauses for clauses in declared.values()):
                problems.append(
                    f"{audit_id}: accepted clause {clause!r} is no longer demonstrated")
            elif clause not in admitted.get(audit_id, set()):
                problems.append(
                    f"{audit_id}: accepted clause {clause!r} is no longer an admitted clause")
    return problems


def test_accepted_coverage_does_not_regress():
    baseline = load_baseline()
    admitted, _ = register_view(baseline)
    problems = regressions(baseline, CORPUS, admitted)
    assert not problems, "accepted E2E coverage regressed:\n  " + "\n  ".join(problems)


def test_register_revision_stays_traceable(capsys):
    """Report the register revision and re-verify the accepted clauses against it."""
    baseline = load_baseline()
    admitted, digest = register_view(baseline)
    recorded = baseline["register"]["sha256"]
    with capsys.disabled():
        print(f"coverage baseline register digest: recorded {recorded}, current {digest}")
        if digest != recorded:
            print("the register moved: every accepted clause is re-checked against its current scope")
    assert regressions(baseline, CORPUS, admitted) == []


def _without(scenarios, audit_id, scenario_id):
    return [scenario for scenario in scenarios
            if not (scenario.audit_id == audit_id and scenario.scenario_id == scenario_id)]


def test_the_control_detects_a_lost_scenario_identity_or_reference():
    """Isolated demonstration that the control detects loss and substitution.

    Each doctored corpus keeps the scenario count unchanged where the loss is a
    substitution, which is exactly what a count-based check would miss.
    """
    baseline = load_baseline()
    admitted, _ = register_view(baseline)
    assert regressions(baseline, CORPUS, admitted) == []

    holder = next(audit_id for audit_id, entry in sorted(baseline["identities"].items())
                  if len(entry["scenarios"]) > 1)
    victim = sorted(baseline["identities"][holder]["scenarios"])[0]

    dropped = regressions(baseline, _without(CORPUS, holder, victim), admitted)
    assert any("is gone" in problem for problem in dropped), dropped

    renamed = [replace(scenario, scenario_id="renamed-substitute")
               if scenario.audit_id == holder and scenario.scenario_id == victim
               else scenario for scenario in CORPUS]
    assert len(renamed) == len(CORPUS), "the substitution keeps the scenario count"
    substituted = regressions(baseline, renamed, admitted)
    assert any("is gone" in problem for problem in substituted), substituted

    narrow_holder, narrow_victim = next(
        (audit_id, name)
        for audit_id, entry in sorted(baseline["identities"].items())
        for name, clauses in sorted(entry["scenarios"].items()) if len(clauses) > 1)
    narrowed = [replace(scenario, covers=scenario.covers[:1])
                if scenario.audit_id == narrow_holder and scenario.scenario_id == narrow_victim
                else scenario for scenario in CORPUS]
    assert len(narrowed) == len(CORPUS)
    trimmed = regressions(baseline, narrowed, admitted)
    assert any("clause references dropped" in problem for problem in trimmed), trimmed

    empty_identity = [scenario for scenario in CORPUS if scenario.audit_id != holder]
    emptied = regressions(baseline, empty_identity, admitted)
    assert any("has no scenarios left" in problem for problem in emptied), emptied


def test_the_control_detects_a_clause_that_left_the_admitted_scope():
    """A register change that withdraws an accepted clause invalidates the evidence."""
    baseline = load_baseline()
    admitted, _ = register_view(baseline)
    holder = sorted(baseline["identities"])[0]
    withdrawn = {**admitted, holder: set()}
    problems = regressions(baseline, CORPUS, withdrawn)
    assert any("is no longer an admitted clause" in problem for problem in problems), problems


def test_the_completeness_gate_stays_separate_from_this_reference():
    """The reference protects accepted evidence; it never claims completeness."""
    baseline = load_baseline()
    admitted, _ = register_view(baseline)
    assert set(baseline["identities"]) < set(admitted), (
        "the reference is expected to be a strict subset of the admitted identities; "
        "the global completeness gate is what reports the rest")

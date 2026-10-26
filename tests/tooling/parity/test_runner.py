"""Behavioural checks for the shared parity runner.

These tests protect the comparator (outcome codes, tolerances, shifted
distributions, malformed samples), the runner's refusal to pass a case it did
not execute, compare and approve, the per-case simulation budgets, the pooled
oracle path, escalation limits and truncation-horizon configuration.
They compile no fighter and sample no engine.
"""
from types import SimpleNamespace

import math

import numpy as np
import pytest

from mordheim_combat_lab.verification.parity import ParityCase
from mordheim_combat_lab.verification.parity import run_parity
from mordheim_combat_lab.verification.parity import _runner
from mordheim_combat_lab.verification.parity._runner import (
    MagnitudeComparison,
    ParityRow,
    escalation_plan,
)
from mordheim_combat_lab.verification.parity._statistical import (
    compare_outcome_rates,
    outcome_counts,
    outcome_rates,
    six_sigma_tolerance,
)
from tests.engines.fixtures.precompiled_catalog import benchmark_case_key



def observation(*, winner, rounds=None, wounds=None, conditions=None):
    rounds = np.zeros_like(np.asarray(winner)) if rounds is None else rounds
    wounds = np.zeros_like(np.asarray(winner)) if wounds is None else wounds
    conditions = np.zeros_like(np.asarray(winner)) if conditions is None else conditions
    return SimpleNamespace(
        winner=np.asarray(winner), resolution_rounds=np.asarray(rounds),
        rounds=np.asarray(rounds), first_wounds=np.asarray(wounds),
        second_wounds=np.asarray(wounds), first_condition=np.asarray(conditions),
        second_condition=np.asarray(conditions),
    )


def test_outcome_counts_accept_only_the_oracle_codes():
    assert outcome_counts(np.array([0, 0, 1, 2, 2, 2])) == (2, 1, 3)
    for invalid in (np.array([7, -1]), np.array([0.5, 1.0]),
                    np.array([True, False])):
        with pytest.raises(ValueError):
            outcome_counts(invalid)


def test_outcome_rates_and_the_six_sigma_tolerance():
    assert outcome_rates((2, 1, 1), 4) == (0.5, 0.25, 0.25)
    assert six_sigma_tolerance(0.0, 0.0, 64) == pytest.approx(0.0025)
    expected = 6 * np.sqrt(0.25 / 64 + 0.25 / 64)
    assert six_sigma_tolerance(0.5, 0.5, 64) == pytest.approx(expected)


def test_compare_outcome_rates_passes_identical_and_flags_shifted_samples():
    assert compare_outcome_rates((40, 20, 4), (40, 20, 4), 64)[3] is True

    shifted = compare_outcome_rates((40, 20, 4), (4, 20, 40), 64)
    assert shifted[3] is False
    modular_rates, candidate_rates, tolerances, _ = shifted
    assert modular_rates[0] == pytest.approx(0.625)
    assert candidate_rates[0] == pytest.approx(0.0625)
    assert len(tolerances) == 3


def test_winner_codes_reject_malformed_samples_in_either_engine():
    assert list(_runner._winner_codes(np.array([1, -1, 0, 1]))) == [0, 1, 2, 0]
    for malformed in (np.array([1, 2]), np.array([1.0, -1.0])):
        with pytest.raises(_runner.OutcomeCodeError):
            _runner._winner_codes(malformed)
    # The oracle is validated before the candidate convention is applied.
    with pytest.raises(_runner.OutcomeCodeError):
        _runner._winner_comparison(
            observation(winner=[0, 1, 3]), observation(winner=[1, -1, 0]), 3,
        )
    # The candidate's own 0 means unresolved, never a first win.
    valid = _runner._winner_comparison(
        observation(winner=[0, 1, 2]), observation(winner=[1, -1, 0]), 3,
    )
    assert valid.passed is True


def test_distribution_and_shape_checks_detect_a_shifted_or_short_sample():
    left = np.array([0, 1] * 32)
    assert _runner._distribution("rounds", left, left, 64).passed is True
    assert _runner._distribution(
        "rounds", left, np.zeros(64, dtype=int), 64,
    ).passed is False

    oracle = observation(winner=[0, 1, 2])
    assert _runner._shape_mismatch(
        oracle, observation(winner=[0, 1]), 3,
    ) is not None
    assert _runner._shape_mismatch(oracle, oracle, 3) is None


def test_compare_case_always_compares_the_winner_and_rejects_unknown_magnitudes():
    oracle = observation(winner=[0, 0, 1, 2], rounds=[1, 2, 3, 4])
    candidate = observation(winner=[1, 1, -1, 0], rounds=[1, 2, 4, 4])
    comparisons, failure = _runner._compare_case(
        ("winner", "rounds"), oracle, candidate, 4,
    )
    assert [item.magnitude for item in comparisons] == ["winner", "rounds"]
    assert comparisons[0].modular_rates[0] == pytest.approx(0.5)
    assert comparisons[0].candidate_rates[0] == pytest.approx(0.5)
    assert failure is None
    with pytest.raises(ValueError):
        _runner._compare_case(("parry-attempts",), oracle, oracle, 1)


def test_blocked_case_is_never_executed_or_compared():
    run = _runner.run_parity((
        _runner.ParityCase(
            label="blocked", first=None, second=None,
            simulations=1,
            blocked_by="state:G00/G02",
        ),
    ))
    row = run.rows[0]
    assert row.status == "INCOMPATIBLE"
    assert row.blocked_by == "state:G00/G02"
    assert row.executed is False and row.compared is False
    assert row.approved is False


def test_malformed_outcome_codes_are_an_own_error(monkeypatch):
    monkeypatch.setattr(
        _runner, "simulate_duel_observed",
        lambda *args, **kwargs: observation(winner=[0, 3]),
    )
    monkeypatch.setattr(
        _runner, "_candidate_sample",
        lambda *args, **kwargs: observation(winner=[1, 0]),
    )
    monkeypatch.setattr(_runner, "_same_sample", lambda left, right: True)
    run = _runner.run_parity((
        _runner.ParityCase(
            label="malformed", first=None, second=None, simulations=2,
            magnitudes=("winner",),
        ),
    ), candidate="observed", repeat_candidate=True)
    row = run.rows[0]
    assert row.status == "NOT_RUN"
    assert row.detail.startswith("NOT_RUN:outcome-codes")
    assert row.executed is True and row.compared is False
    assert row.approved is False


def test_parallel_oracle_preserves_seed_ranges_and_all_terminal_rows():
    # Synthetic samples only: no process or engine is started by this check.
    from concurrent.futures import Future

    submissions = []

    class Executor:
        def submit(self, function, first, second, count, **options):
            submissions.append((function, count, options))
            indices = np.arange(options["seed"], options["seed"] + count)
            future = Future()
            future.set_result(observation(
                winner=indices % 3, rounds=indices, wounds=indices + 1,
                conditions=indices % 4,
            ))
            return future

    merged = _runner._observed_reference(
        _runner.ParityCase(
            label="case", first=None, second=None, seed=20, maximum_rounds=50,
        ),
        7, workers=3, executor=Executor(),
    )
    assert [(count, options["seed"]) for _, count, options in submissions] == [
        (3, 20), (2, 23), (2, 25),
    ]
    assert all(function is _runner.simulate_duel_observed
               for function, _, _ in submissions)
    indices = np.arange(20, 27)
    for name, expected in (
        ("winner", indices % 3), ("resolution_rounds", indices),
        ("first_wounds", indices + 1), ("second_wounds", indices + 1),
        ("first_condition", indices % 4), ("second_condition", indices % 4),
    ):
        np.testing.assert_array_equal(getattr(merged, name), expected)
    assert merged.simulations == 7 and merged.maximum_rounds == 50


def _pair(cases, scenario_id: str = "basic"):
    return cases[benchmark_case_key(scenario_id)]


def _case(cases, *, label, simulations, scenario_id="basic"):
    pair = _pair(cases, scenario_id)
    return ParityCase(
        label=label, first=pair.first, second=pair.second,
        maximum_rounds=pair.limits.maximum_rounds, simulations=simulations,
        seed=3,
    )


def _prepared_matrix(cases):
    """Cases and prepared rows whose first-pass samples cover the trigger bands."""
    pair = _pair(cases)
    delta = math.sqrt(2 * .25 / 10_000)
    profiles = {
        "border": ((0.5, 0.5, 0.0),
                   (0.5 + 4 * delta, 0.5 - 4 * delta, 0.0)),
        "grind": ((0.3, 0.3, 0.4), (0.3, 0.3, 0.4)),
        "broken": ((0.5, 0.5, 0.0),
                   (0.5 + 7 * delta, 0.5 - 7 * delta, 0.0)),
        "clean": ((0.5, 0.5, 0.0),
                  (0.5 + delta, 0.5 - delta, 0.0)),
    }
    prepared = []
    rows = []
    for label, (modular, candidate) in profiles.items():
        case = ParityCase(
            label=f"matrix:{label}", first=pair.first, second=pair.second,
            maximum_rounds=pair.limits.maximum_rounds, simulations=10_000,
        )
        prepared.append((case, 10_000))
        rows.append(ParityRow(
            case=case.label, backend="numpy",
            maximum_rounds=case.maximum_rounds, simulations=10_000,
            status="PASS",
            comparisons=(MagnitudeComparison(
                "winner", modular, candidate, (0.05, 0.05, 0.05), True,
            ),),
        ))
    return tuple(prepared), tuple(rows)


def test_runner_charges_each_case_its_own_modular_budget(cases):
    run = run_parity(
        (_case(cases, label="matrix:basic", simulations=60),),
        backends=("numpy",), candidate="counts",
    )
    # Without the native backend: one matrix row per case, no cross rows.
    assert run.modular_duels == 60
    assert len(run.rows) == 1
    assert run.rows[0].case == "matrix:basic"
    assert run.rows[0].backend == "numpy"

    run = run_parity(
        (
            _case(cases, label="matrix:basic", simulations=200),
            _case(cases, label="matrix:long", simulations=60, scenario_id="long"),
        ),
        backends=("numpy",), candidate="counts",
    )
    assert run.modular_duels == 260
    assert {(row.case, row.simulations) for row in run.rows} == {
        ("matrix:basic", 200), ("matrix:long", 60),
    }


def test_runner_pooled_oracle_matches_the_sequential_path(cases):
    case = _case(cases, label="matrix:basic", simulations=200)
    sequential = run_parity((case,), backends=("numpy",), candidate="counts")
    pooled = run_parity(
        (case,), backends=("numpy",), candidate="counts", workers=2,
    )
    assert pooled.modular_duels == sequential.modular_duels == 200
    def fields(rows):
        return [(
            row.case, row.simulations, row.winner.modular_rates,
            row.winner.candidate_rates, row.winner.tolerances, row.winner.passed,
        ) for row in rows]
    assert fields(pooled.rows) == fields(sequential.rows)


def test_cross_rows_require_the_native_backend(cases):
    from mordheim_combat.vectorized import available_backends
    installed = "native" in available_backends()
    matrix = run_parity(
        (_case(cases, label="matrix:basic", simulations=40),),
        backends=("numpy", "native") if installed else ("numpy",),
        candidate="counts",
    )
    assert len(matrix.rows) == (2 if installed else 1)
    if installed:
        cross = run_parity(
            (_case(cases, label="cross:basic", simulations=100),),
            backends=("native",), reference="numpy", candidate="counts",
        )
        assert len(cross.rows) == 1
        assert cross.rows[0].simulations == 100
        assert cross.rows[0].backend == "native"


def test_escalation_plan_marks_suspicious_and_unresolved_pairs(cases):
    prepared, rows = _prepared_matrix(cases)
    plan = escalation_plan(
        prepared, rows, factor=2, sigma=3.0, unresolved=0.01,
        remaining=None,
    )
    # The 4-sigma case (doubling decides defect vs noise) and the
    # unresolved-prone case escalate; the conclusive 7-sigma failure and the
    # clean 1-sigma case stay at the base sample.
    assert [(case.label, size) for case, size in plan] == [
        ("matrix:border", 20_000), ("matrix:grind", 20_000),
    ]


def test_escalation_plan_respects_the_modular_ceiling(cases):
    prepared, rows = _prepared_matrix(cases)
    plan = escalation_plan(
        prepared, rows, factor=2, sigma=3.0, unresolved=0.01,
        remaining=10_000,
    )
    # Only the highest-priority case fits in the remaining budget.
    assert [case.label for case, _ in plan] == ["matrix:border"]


def test_runner_escalates_and_clamps_to_the_ceiling(cases):
    cases_ = tuple(
        _case(cases, label=f"matrix:{label}", simulations=60)
        for label in ("a", "b", "c")
    )
    run = run_parity(
        cases_, backends=("numpy",), candidate="counts",
        escalate=True, escalate_sigma=0.0, max_modular_duels=240,
    )
    # Base 180 duels; exactly one case fits an escalation to 120 under the
    # 240-duel ceiling (tie-breaks keep insertion order: "a").
    assert {row.case: row.simulations for row in run.rows} == {
        "matrix:a": 120, "matrix:b": 60, "matrix:c": 60,
    }
    assert sum(row.escalated for row in run.rows) == 1
    assert run.modular_duels == 240


def test_no_fitting_horizon_is_rejected(cases):
    case = cases[benchmark_case_key("basic")]
    with pytest.raises(ValueError, match="no truncation horizon"):
        run_parity(
            (ParityCase(
                label="basic", first=case.first, second=case.second,
                maximum_rounds=5,
            ),),
            simulations=50, horizons=(8, 10),
        )


def test_modular_only_execution_does_not_sample_candidates_or_approve_parity(monkeypatch):
    calls = []

    def reference(case, size, **options):
        calls.append((case.label, size))
        return observation(winner=[0, 1])

    def candidate(*args, **options):
        raise AssertionError("reference-only execution must never sample a candidate")

    monkeypatch.setattr(_runner, "_observed_reference", reference)
    monkeypatch.setattr(_runner, "_candidate_sample", candidate)
    run = run_parity((ParityCase("reference", None, None, simulations=2),),
                     backends=("modular",), workers=1)
    assert calls == [("reference", 2)]
    assert run.modular_duels == 2
    row, = run.rows
    assert row.backend == "modular" and row.status == "COMPLETED"
    assert row.executed and not row.compared and not row.approved
    assert row.comparisons == ()

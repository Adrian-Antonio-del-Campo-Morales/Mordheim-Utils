"""Static proofs for the statistical parity battery runner.

These tests exercise the outcome comparator, stage recording, input limits and
coverage merge on synthetic samples.  They never compile a fighter, sample an
engine or run a candidate, and they require no internal-event witness.
"""
from types import SimpleNamespace

import numpy as np
import pytest

from mordheim_combat_lab.verification.parity import _battery_runner as runner
from mordheim_combat_lab.verification.parity._statistical import (
    compare_outcome_rates,
    outcome_counts,
    outcome_rates,
    six_sigma_tolerance,
)

pytestmark = pytest.mark.phase5_vectorized


def case(identifier="case", *, variant_id="B06.1", **options):
    values = dict(
        id=identifier, level="complete", variant=variant_id, origin="new:test",
        first=None, second=None, rows=8, seed=1, maximum_rounds=4,
        context=None, decisions={}, decision_scope="uniform",
        observables=("winner", "rounds"), blocked_by=None,
    )
    values.update(options)
    return SimpleNamespace(**values)


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


def result(identifier="a", status="PASS", *, backend="numpy", compared=None,
           approved=None, detail=""):
    executed = status in {"PASS", "DIVERGENCE"}
    return runner.BatteryCaseResult(
        case=identifier, level="complete", variant="B06.1", obligation="B06",
        backend=backend, status=status, keys=(), observables=("winner",), rows=8,
        executed=executed, compared=executed if compared is None else compared,
        approved=(status == "PASS") if approved is None else approved,
        detail=detail,
    )


def report(results, *, complete=False, accepted=False):
    return runner.BatteryReport(
        complete=complete, accepted=accepted, scope="profile", profile="quick",
        results=tuple(results),
        passed=tuple(item.case for item in results if item.status == "PASS"),
        divergences=tuple(item.case for item in results if item.status == "DIVERGENCE"),
        incompatible=tuple(item.case for item in results if item.status == "INCOMPATIBLE"),
        not_run=tuple(item.case for item in results if item.status == "NOT_RUN"),
        missing_variants=(),
    )


def test_outcome_counts_uses_the_oracle_codes():
    counts = outcome_counts(np.array([0, 0, 1, 2, 2, 2]))
    assert counts == (2, 1, 3)
    # A malformed code is neither a win nor an unresolved duel: it raises.
    with pytest.raises(ValueError):
        outcome_counts(np.array([7, -1]))
    with pytest.raises(ValueError):
        outcome_counts(np.array([0.5, 1.0]))
    with pytest.raises(ValueError):
        outcome_counts(np.array([True, False]))


def test_outcome_rates_and_the_shared_tolerance():
    assert outcome_rates((2, 1, 1), 4) == (0.5, 0.25, 0.25)
    assert six_sigma_tolerance(0.0, 0.0, 64) == pytest.approx(0.0025)
    expected = 6 * np.sqrt(0.25 / 64 + 0.25 / 64)
    assert six_sigma_tolerance(0.5, 0.5, 64) == pytest.approx(expected)


def test_compare_outcome_rates_passes_identical_samples_and_flags_a_shift():
    same = compare_outcome_rates((40, 20, 4), (40, 20, 4), 64)
    assert same[3] is True

    shifted = compare_outcome_rates((40, 20, 4), (4, 20, 40), 64)
    assert shifted[3] is False
    modular_rates, candidate_rates, tolerances, _ = shifted
    assert modular_rates[0] == pytest.approx(0.625)
    assert candidate_rates[0] == pytest.approx(0.0625)
    assert len(tolerances) == 3


def test_winner_codes_maps_the_candidate_convention():
    assert list(runner._winner_codes(np.array([1, -1, 0, 1]))) == [0, 1, 2, 0]
    # A code the candidate never publishes is malformed data, not unresolved.
    with pytest.raises(runner.OutcomeCodeError):
        runner._winner_codes(np.array([1, 2]))
    with pytest.raises(runner.OutcomeCodeError):
        runner._winner_codes(np.array([1.0, -1.0]))


def test_oracle_codes_are_validated_before_normalisation():
    oracle = observation(winner=[0, 1, 3])
    candidate = observation(winner=[1, -1, 0])
    with pytest.raises(runner.OutcomeCodeError):
        runner._winner_comparison(oracle, candidate, 3)
    # The candidate's own 0 is unresolved, never a first win.
    valid = runner._winner_comparison(
        observation(winner=[0, 1, 2]), observation(winner=[1, -1, 0]), 3,
    )
    assert valid.passed is True


def test_category_counts_reads_numbers_and_labels():
    counts = runner._category_counts(np.array([1, 2, 1]))
    assert counts[1] == 2 and counts[2] == 1
    labels = runner._category_counts(np.array(["a", "b", "a"]))
    assert labels["a"] == 2


def test_distribution_passes_and_reports_the_worst_category():
    left = np.array([0, 1] * 32)
    comparison = runner._distribution("rounds", left, left, 64)
    assert comparison.passed is True and comparison.magnitude == "rounds"
    assert len(comparison.modular_rates) == 2
    assert "rounds[" in comparison.detail

    shifted = np.zeros(64, dtype=int)
    failure = runner._distribution("rounds", left, shifted, 64)
    assert failure.passed is False
    assert "rounds[" in failure.detail


def test_shape_mismatch_detects_a_short_sample():
    oracle = observation(winner=[0, 1, 2])
    candidate = observation(winner=[0, 1])
    assert runner._shape_mismatch(oracle, candidate, 3) is not None
    assert runner._shape_mismatch(oracle, candidate, 3).startswith("candidate.winner")
    assert runner._shape_mismatch(oracle, oracle, 3) is None


def test_same_sample_is_exact():
    left = observation(winner=[0, 1], rounds=[1, 2])
    right = observation(winner=[0, 1], rounds=[1, 2])
    assert runner._same_sample(left, right) is True
    assert runner._same_sample(left, observation(winner=[0, 1], rounds=[1, 3])) is False


def test_compare_case_always_compares_the_winner_and_declared_magnitudes():
    oracle = observation(winner=[0, 0, 1, 2], rounds=[1, 2, 3, 4])
    candidate = observation(winner=[1, 1, -1, 0], rounds=[1, 2, 4, 4])
    comparisons, failure = runner._compare_case(("winner", "rounds"), oracle, candidate, 4)
    assert [item.magnitude for item in comparisons] == ["winner", "rounds"]
    # The candidate's 1/-1 are first/second wins in the oracle convention.
    assert comparisons[0].modular_rates[0] == pytest.approx(0.5)
    assert comparisons[0].candidate_rates[0] == pytest.approx(0.5)
    # Four rows cannot resolve a 25% category shift at the six-sigma gate.
    assert failure is None


def test_compare_case_rejects_a_magnitude_the_contract_does_not_define():
    oracle = observation(winner=[0])
    with pytest.raises(ValueError):
        runner._compare_case(("parry-attempts",), oracle, oracle, 1)


def test_result_records_the_magnitudes_it_compared():
    comparison = runner.MagnitudeComparison(
        magnitude="winner", modular_rates=(0.5, 0.5, 0.0),
        candidate_rates=(0.5, 0.5, 0.0), tolerances=(0.1, 0.1, 0.1), passed=True,
    )
    item = runner._result(
        case(), "numpy", "PASS", rows=8, comparisons=(comparison,),
        executed=True, compared=True, approved=True,
    )
    assert item.magnitudes == ("winner",)
    assert item.case == "case" and item.variant == "B06.1" and item.obligation == "B06"
    assert item.executed and item.compared and item.approved


def test_real_input_limit_blocks_and_witness_blocks_do_not(monkeypatch):
    blocked = case("blocked", blocked_by="state:G00/G02")
    assert runner.input_limit(blocked) == "state:G00/G02"
    witness_only = case("witness-only", blocked_by="witness:G06")
    assert runner.input_limit(witness_only) is None

    outcome = runner._run_case(blocked, backend="numpy", rows=8, root=None)
    assert outcome.status == "INCOMPATIBLE"
    assert outcome.blocked_by == "state:G00/G02"
    assert outcome.detail.startswith("INCOMPATIBLE:state")
    assert outcome.executed is False and outcome.compared is False
    assert outcome.approved is False


def test_per_row_decisions_are_a_real_limit():
    assert runner.input_limit(case(decision_scope="per-row")) is not None


def test_run_case_classifies_malformed_outcome_codes_as_an_own_error(monkeypatch):
    item = case("malformed")
    monkeypatch.setattr(runner, "compile_fighter", lambda build, root: object())
    monkeypatch.setattr(
        runner, "simulate_duel_observed",
        lambda *args, **kwargs: observation(winner=[0, 3]),
    )
    monkeypatch.setattr(
        runner, "_candidate_sample",
        lambda *args, **kwargs: observation(winner=[1, 0]),
    )
    monkeypatch.setattr(runner, "_same_sample", lambda left, right: True)
    outcome = runner._run_case(item, backend="numpy", rows=2, root=None)
    assert outcome.status == "NOT_RUN"
    assert outcome.detail.startswith("NOT_RUN:outcome-codes")
    assert outcome.executed is True and outcome.compared is False
    assert outcome.approved is False


def test_combine_reports_keeps_every_row_and_the_worst_verdict():
    numpy_report = report((result("a"), result("b")), complete=True, accepted=True)
    native_report = report(
        (result("a", "PASS", backend="native"),
         result("b", "DIVERGENCE", backend="native",
                detail="DIVERGENCE: winner[first]")),
        complete=False,
    )
    merged = runner.combine_reports(
        (numpy_report, native_report), profile="quick", backend="all",
    )
    assert len(merged.results) == 4
    assert merged.passed == ("a",)
    assert merged.divergences == ("b",)
    assert merged.complete is False and merged.accepted is False
    assert merged.scope == "profile"


def test_combine_reports_needs_at_least_one_run():
    with pytest.raises(ValueError):
        runner.combine_reports(())


def test_run_battery_reports_completeness_and_missing_variants(monkeypatch):
    item = case("a", variant_id="B06.1")
    monkeypatch.setattr(runner, "required_variants", lambda profile: ("B06.1", "B06.2"))
    monkeypatch.setattr(runner, "_run_case", lambda *args, **kwargs: result("a"))

    incomplete = runner.run_battery((item,), profile="complete", root=".")
    assert incomplete.scope == "profile"
    assert incomplete.missing_variants == ("B06.2",)
    assert incomplete.complete is False and incomplete.accepted is False

    monkeypatch.setattr(runner, "required_variants", lambda profile: ("B06.1",))
    complete = runner.run_battery((item,), profile="complete", root=".")
    assert complete.complete is True and complete.accepted is True
    assert complete.passed == ("a",)

    diagnostic = runner.run_battery((item,), root=".")
    assert diagnostic.scope == "provided"
    assert diagnostic.accepted is False and diagnostic.missing_variants == ()


def test_run_battery_is_incomplete_when_a_case_is_a_dependency(monkeypatch):
    item = case("a")
    monkeypatch.setattr(runner, "required_variants", lambda profile: ("B06.1",))
    monkeypatch.setattr(
        runner, "_run_case",
        lambda *args, **kwargs: result("a", "INCOMPATIBLE",
                                       detail="INCOMPATIBLE:state:G00/G02"),
    )
    incomplete = runner.run_battery((item,), profile="quick", root=".")
    assert incomplete.complete is False and incomplete.accepted is False
    assert incomplete.incompatible == ("a",)


def test_parallel_oracle_preserves_seed_ranges_and_all_terminal_rows():
    # Synthetic samples only: no process or motor is started by this check.
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

    merged = runner._oracle_sample(
        None, None, 7, seed=20, maximum_rounds=50, decisions=None,
        context=None, workers=3, executor=Executor(),
    )
    assert [(count, options["seed"]) for _, count, options in submissions] == [
        (3, 20), (2, 23), (2, 25),
    ]
    assert all(function is runner.simulate_duel_observed
               for function, _, _ in submissions)
    indices = np.arange(20, 27)
    for name, expected in (
        ("winner", indices % 3), ("resolution_rounds", indices),
        ("first_wounds", indices + 1), ("second_wounds", indices + 1),
        ("first_condition", indices % 4), ("second_condition", indices % 4),
    ):
        np.testing.assert_array_equal(getattr(merged, name), expected)
    assert merged.simulations == 7 and merged.maximum_rounds == 50


def test_run_battery_reuses_one_pool_and_passes_resolved_workers(monkeypatch):
    pools = []
    calls = []

    class Pool:
        def __init__(self, *, max_workers):
            pools.append(self)
            self.max_workers = max_workers

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    def resolve(workers, rows, horizon):
        assert workers == 10
        return 3

    def run(item, **options):
        calls.append(options)
        return result(item.id)

    monkeypatch.setattr(runner, "ProcessPoolExecutor", Pool)
    monkeypatch.setattr(runner, "resolve_oracle_workers", resolve)
    monkeypatch.setattr(runner, "_run_case", run)
    runner.run_battery((case("a"), case("b")), root=".", workers=10)
    assert len(pools) == 1 and pools[0].max_workers == 3
    assert len(calls) == 2
    assert all(call["workers"] == 3 and call["executor"] is pools[0]
               for call in calls)

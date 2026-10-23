"""Parity execution proofs: the modular oracle against the optimized backends.

Every duel input comes from the frozen corpus (``tests/engines/fixtures``)
keyed by the stable keys fixed in T01; no knowledge base is read and no
fighter is compiled.  Scenarios, seeds, samples and the six-sigma tolerances
are the historical ones.
"""
from mordheim_combat_lab.verification.parity import verify_vectorized_parity
from mordheim_combat_lab.verification.parity import compare_statistical_parity
from mordheim_combat_lab.verification.parity import certify_deep
from mordheim_combat_lab.verification.parity import escalation_plan
from mordheim_combat_lab.verification.parity import DeepPair
from mordheim_combat_lab.verification.parity import StatisticalParityResult
from mordheim_combat_lab.verification.parity import ParityReport
from mordheim_combat_lab.verification.parity import parity_report_payload
from mordheim_combat_lab.verification.parity import verify_specification_parity
from mordheim_combat_lab.cli.benchmarking import deep_test_scenarios
import pytest


@pytest.mark.phase5_vectorized
def test_vectorized_parity_inventory_is_complete_and_exact_checks_pass():
    report = verify_vectorized_parity()
    assert report.pending == ()
    assert report.divergences == ()
    assert report.complete
    assert set(report.exact_checks) == {
        "hit-targets", "wound-targets", "attack-pools", "priority",
        "keyed-dice-replay",
        "armour", "injury",
    }


@pytest.mark.phase5_vectorized
def test_semantic_specs_are_reused_as_a_case_level_parity_inventory():
    report = verify_specification_parity()
    assert len(report.cases) == 3743
    assert report.divergences == ()
    assert len(report.passed) == 3743
    assert report.pending == ()
    assert report.out_of_scope == ()
    assert {item.status for item in report.cases} <= {
        "PASS", "DIVERGENCE", "PENDING_ADAPTER", "OUT_OF_SCOPE",
    }
    assert all(
        item.status == "PASS"
        for item in report.cases if item.operation in {"attacks", "priority"}
    )


@pytest.mark.phase5_vectorized
def test_statistical_parity_reports_three_outcomes_and_six_sigma_tolerances(cases):
    fighter = cases["benchmark/basic"].first
    result = compare_statistical_parity("smoke", fighter, fighter, 20, seed=3)
    assert len(result.modular_rates) == len(result.vectorized_rates) == 3
    assert len(result.tolerances) == 3
    assert all(tolerance >= .0025 for tolerance in result.tolerances)


@pytest.mark.phase5_vectorized
def test_statistical_samples_record_per_engine_wall_times(cases):
    pair = _single_deep_pair(cases)
    result = compare_statistical_parity(
        "smoke", pair.first, pair.second, 40, seed=3,
        maximum_rounds=pair.maximum_rounds,
    )
    assert result.reference_seconds > 0  # the oracle sample was timed here
    assert result.candidate_seconds > 0
    # A precomputed oracle sample carries its caller-provided measurement.
    from mordheim_combat.modular.duel import simulate_duel_reference
    modular = simulate_duel_reference(
        pair.first, pair.second, 40, seed=3,
        maximum_rounds=pair.maximum_rounds,
    )
    replayed = compare_statistical_parity(
        "smoke", pair.first, pair.second, 40, seed=3,
        maximum_rounds=pair.maximum_rounds, modular=modular,
        reference_seconds=12.5,
    )
    assert replayed.reference_seconds == 12.5
    assert replayed.candidate_seconds > 0


def _single_deep_pair(cases):
    """The ``basic`` benchmark pair, loaded directly from the frozen corpus."""
    case = cases["benchmark/basic"]
    return DeepPair("basic", case.first, case.second, case.limits.maximum_rounds)


@pytest.mark.phase5_vectorized
def test_certify_deep_matrix_stays_within_the_modular_budget(cases):
    pair = _single_deep_pair(cases)
    samples, modular_duels = certify_deep(
        (pair,), simulations=60, cross_simulations=200, seed=3,
        native_installed=False,
    )
    # Without the native backend: one matrix row per pair, no cross rows.
    assert modular_duels == 60
    assert len(samples) == 1
    assert samples[0].scenario == "matrix:basic"
    assert samples[0].backend == "numpy"
    assert samples[0].simulations == 60
    assert isinstance(samples[0].passed, bool)


@pytest.mark.phase5_vectorized
def test_certify_deep_pooled_oracle_matches_the_sequential_path(cases):
    pair = _single_deep_pair(cases)
    kwargs = dict(simulations=200, cross_simulations=100, seed=3,
                  native_installed=False)
    sequential, sequential_duels = certify_deep((pair,), **kwargs)
    pooled, pooled_duels = certify_deep((pair,), workers=2, **kwargs)
    assert pooled_duels == sequential_duels == 200
    def fields(rows):
        return [(
            row.scenario, row.simulations, row.modular_rates,
            row.vectorized_rates, row.tolerances, row.passed,
        ) for row in rows]
    assert fields(pooled) == fields(sequential)


@pytest.mark.phase5_vectorized
def test_certify_deep_supports_per_pair_oracle_sample_sizes(cases):
    pair = _single_deep_pair(cases)
    pairs = (
        DeepPair("basic", pair.first, pair.second, 50, simulations=200),
        DeepPair("long", pair.first, pair.second, 75, simulations=60),
    )
    samples, modular_duels = certify_deep(
        pairs, simulations=10, cross_simulations=50, seed=3,
        native_installed=False,
    )
    assert modular_duels == 260
    assert {(row.scenario, row.simulations) for row in samples} == {
        ("matrix:basic", 200), ("matrix:long", 60),
    }


@pytest.mark.phase5_vectorized
def test_certify_deep_cross_rows_require_the_native_backend(cases):
    from mordheim_combat.vectorized import available_backends
    pair = _single_deep_pair(cases)
    samples, _ = certify_deep(
        (pair,), simulations=40, cross_simulations=100, seed=3,
        native_installed="native" in available_backends(),
    )
    matrix = [row for row in samples if row.scenario.startswith("matrix:")]
    cross = [row for row in samples if row.scenario.startswith("cross:")]
    assert len(matrix) >= 1
    if "native" in available_backends():
        assert len(matrix) == 2  # numpy + native matrix rows
        assert len(cross) == 1
        assert cross[0].simulations == 100
    else:
        assert cross == []


@pytest.mark.phase5_vectorized
def test_certify_deep_covers_the_full_archetype_matrix(cases):
    pairs = tuple(
        DeepPair(
            scenario.id, cases[f"parity/deep/{scenario.id}"].first,
            cases[f"parity/deep/{scenario.id}"].second,
            cases[f"parity/deep/{scenario.id}"].limits.maximum_rounds,
        )
        for scenario in deep_test_scenarios()
    )
    samples, modular_duels = certify_deep(
        pairs, simulations=30, cross_simulations=50, seed=3,
        native_installed=False,
    )
    assert modular_duels == len(pairs) * 30
    assert {row.scenario for row in samples} == {f"matrix:{s.label}" for s in pairs}


def _synthetic_row(label, backend, modular, vector, n):
    """StatisticalParityResult computed from rates with the six-sigma gate."""
    import math
    tolerances = tuple(
        max(.0025, 6 * math.sqrt(m * (1 - m) / n + v * (1 - v) / n))
        for m, v in zip(modular, vector)
    )
    passed = all(
        abs(left - right) <= tolerance
        for left, right, tolerance in zip(modular, vector, tolerances)
    )
    return StatisticalParityResult(
        scenario=label, backend=backend, simulations=n,
        modular_rates=modular, vectorized_rates=vector,
        tolerances=tolerances, passed=passed,
    )


def _prepared_matrix(cases):
    """Four DeepPairs whose first-pass samples cover the trigger bands."""
    import math
    pair = _single_deep_pair(cases)
    delta4 = 4 * math.sqrt(2 * .25 / 10_000)   # exactly four sigma at p=.5
    delta7 = 7 * math.sqrt(2 * .25 / 10_000)   # conclusive, above six sigma
    first, second = pair.first, pair.second
    prepared = tuple(
        (DeepPair(label, first, second, 50, simulations=10_000), 10_000, None)
        for label in ("border", "grind", "broken", "clean")
    )
    samples = (
        _synthetic_row("matrix:border", "numpy", (0.5, 0.5, 0.0),
                       (0.5 + delta4, 0.5 - delta4, 0.0), 10_000),
        _synthetic_row("matrix:grind", "numpy", (0.3, 0.3, 0.4),
                       (0.3, 0.3, 0.4), 10_000),
        _synthetic_row("matrix:broken", "numpy", (0.5, 0.5, 0.0),
                       (0.5 + delta7, 0.5 - delta7, 0.0), 10_000),
        _synthetic_row("matrix:clean", "numpy", (0.5, 0.5, 0.0),
                       (0.5 + math.sqrt(2 * .25 / 10_000),
                        0.5 - math.sqrt(2 * .25 / 10_000), 0.0), 10_000),
    )
    return prepared, samples


@pytest.mark.phase5_vectorized
def test_escalation_plan_marks_suspicious_and_unresolved_pairs(cases):
    prepared, samples = _prepared_matrix(cases)
    plan = escalation_plan(
        prepared, samples, factor=2, sigma=3.0, unresolved=0.01,
        remaining=None,
    )
    # The 4-sigma pair (doubling decides defect vs noise) and the
    # unresolved-prone pair escalate; the conclusive 7-sigma failure and the
    # clean 1-sigma pair stay at the base sample.
    assert {label: size for label, size in
            ((item.label, size) for item, size in plan)} == {
        "border": 20_000, "grind": 20_000,
    }
    assert [item.label for item, _ in plan] == ["border", "grind"]


@pytest.mark.phase5_vectorized
def test_escalation_plan_respects_the_modular_ceiling(cases):
    prepared, samples = _prepared_matrix(cases)
    plan = escalation_plan(
        prepared, samples, factor=2, sigma=3.0, unresolved=0.01,
        remaining=10_000,
    )
    # Only the highest-priority pair fits in the remaining budget.
    assert [item.label for item, _ in plan] == ["border"]


@pytest.mark.phase5_vectorized
def test_certify_deep_escalates_and_clamps_to_the_ceiling(cases):
    pair = _single_deep_pair(cases)
    pairs = tuple(
        DeepPair(label, pair.first, pair.second, 50, simulations=60)
        for label in ("a", "b", "c")
    )
    samples, modular_duels = certify_deep(
        pairs, simulations=10, cross_simulations=100, seed=3,
        native_installed=False, escalate=True, escalate_sigma=0.0,
        max_modular_duels=240,
    )
    # Base 180 duels; exactly one pair fits an escalation to 120 under the
    # 240-duel ceiling (tie-breaks keep insertion order: "a").
    assert {row.scenario: row.simulations for row in samples} == {
        "matrix:a": 120, "matrix:b": 60, "matrix:c": 60,
    }
    assert sum(row.escalated for row in samples) == 1
    escalated = next(row for row in samples if row.escalated)
    assert escalated.scenario == "matrix:a"
    assert escalated.simulations == 120
    assert modular_duels == 240
    payload = parity_report_payload(
        ParityReport(complete=True, obligations=(), verified=(),
                     pending=(), divergences=(), exact_checks=()),
        deep=samples,
    )
    row = next(item for item in payload["deep"]["samples"]
               if item["scenario"] == "matrix:a")
    assert row["escalated"] is True


@pytest.mark.phase5_vectorized
def test_certify_deep_does_not_escalate_by_default(cases):
    pair = _single_deep_pair(cases)
    samples, modular_duels = certify_deep(
        (pair,), simulations=60, cross_simulations=100, seed=3,
        native_installed=False,
    )
    assert modular_duels == 60
    assert all(not row.escalated for row in samples)

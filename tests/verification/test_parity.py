from mordheim_combat_lab.verification.parity import verify_vectorized_parity
from mordheim_combat_lab.verification.parity import compare_statistical_parity
from mordheim_combat_lab.verification.parity import certify_deep
from mordheim_combat_lab.verification.parity import DeepPair
from mordheim_combat_lab.verification.parity import ParityReport
from mordheim_combat_lab.verification.parity import parity_report_markdown
from mordheim_combat_lab.verification.parity import parity_report_payload
from mordheim_combat_lab.verification.parity import verify_specification_parity
from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
from mordheim_combat_lab.cli.benchmarking import deep_test_scenarios
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import FighterBuild


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


def test_parity_inventory_covers_fields_tags_and_complex_sequences():
    report = verify_vectorized_parity()
    kinds = {item.kind for item in report.obligations}
    assert kinds == {"field", "tag", "sequence"}
    assert all(item.evidence for item in report.obligations)


def test_semantic_specs_are_reused_as_a_case_level_parity_inventory():
    report = verify_specification_parity()
    assert len(report.cases) == 3727
    assert report.divergences == ()
    assert len(report.passed) == 3724
    assert len(report.pending) == 3
    assert report.out_of_scope == ()
    assert {item.status for item in report.cases} <= {
        "PASS", "DIVERGENCE", "PENDING_ADAPTER", "OUT_OF_SCOPE",
    }
    assert all(
        item.status == "PASS"
        for item in report.cases if item.operation in {"attacks", "priority"}
    )


def test_statistical_parity_reports_three_outcomes_and_six_sigma_tolerances():
    fighter = compile_fighter(FighterBuild(
        "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
    ))
    result = compare_statistical_parity("smoke", fighter, fighter, 20, seed=3)
    assert len(result.modular_rates) == len(result.vectorized_rates) == 3
    assert len(result.tolerances) == 3
    assert all(tolerance >= .0025 for tolerance in result.tolerances)


def test_statistical_samples_record_per_engine_wall_times():
    pair = _single_deep_pair()
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


def test_payload_and_markdown_record_total_elapsed_time():
    report = ParityReport(complete=True, obligations=(), verified=(),
                          pending=(), divergences=(), exact_checks=())
    payload = parity_report_payload(report, elapsed_seconds=12.25)
    assert payload["elapsed_seconds"] == 12.25
    markdown = parity_report_markdown(payload)
    assert "- Elapsed: `12.2s`" in markdown
    # A payload assembled from precomputed samples reports no total.
    untimed = parity_report_payload(report)
    assert untimed["elapsed_seconds"] is None
    assert "not recorded" in parity_report_markdown(untimed)


def test_deep_payload_rows_expose_per_engine_wall_times():
    pair = _single_deep_pair()
    samples, _ = certify_deep(
        (pair,), simulations=50, cross_simulations=100, seed=3,
        native_installed=False,
    )
    payload = parity_report_payload(
        ParityReport(complete=True, obligations=(), verified=(),
                     pending=(), divergences=(), exact_checks=()),
        deep=samples,
    )
    rows = payload["deep"]["samples"]
    assert all("reference_seconds" in row and "candidate_seconds" in row
               for row in rows)
    assert rows[0]["reference_seconds"] > 0
    assert rows[0]["candidate_seconds"] > 0
    markdown = parity_report_markdown(payload)
    assert "Time (ref/cand, s)" in markdown


def test_report_distinguishes_smoke_samples_from_certification_samples():
    report = verify_vectorized_parity()
    payload = parity_report_payload(report)
    assert payload["complete"]
    assert not payload["certification_sample_complete"]
    markdown = parity_report_markdown(payload)
    assert "Oracle: `combat.modular (read-only)`" in markdown
    assert "## Deterministic checks" in markdown


def test_report_exposes_semantic_case_statuses_without_claiming_completion():
    report = verify_vectorized_parity()
    specifications = verify_specification_parity()
    payload = parity_report_payload(report, specifications=specifications)
    assert not payload["complete"]
    assert payload["specifications"]["passed"]
    assert payload["specifications"]["pending"]
    markdown = parity_report_markdown(payload)
    assert "## Semantic specification parity" in markdown
    assert "PENDING_ADAPTER: `3`" in markdown


def _single_deep_pair():
    scenario = benchmark_scenarios()[0]
    first, second = compile_fighter(scenario.first), compile_fighter(scenario.second)
    return DeepPair("basic", first, second, scenario.maximum_rounds)


def test_certify_deep_matrix_stays_within_the_modular_budget():
    pair = _single_deep_pair()
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


def test_certify_deep_pooled_oracle_matches_the_sequential_path():
    pair = _single_deep_pair()
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


def test_certify_deep_supports_per_pair_oracle_sample_sizes():
    pair = _single_deep_pair()
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


def test_certify_deep_cross_rows_require_the_native_backend():
    from mordheim_combat.vectorized import available_backends
    pair = _single_deep_pair()
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


def test_certify_deep_covers_the_full_archetype_matrix():
    pairs = tuple(
        DeepPair(scenario.id, *(
            compile_fighter(scenario.first), compile_fighter(scenario.second),
        ), scenario.maximum_rounds)
        for scenario in deep_test_scenarios()
    )
    samples, modular_duels = certify_deep(
        pairs, simulations=30, cross_simulations=50, seed=3,
        native_installed=False,
    )
    assert modular_duels == len(pairs) * 30
    assert {row.scenario for row in samples} == {f"matrix:{s.label}" for s in pairs}


def test_deep_payload_exposes_samples_and_passes_only_when_all_pass():
    pair = _single_deep_pair()
    samples, _ = certify_deep(
        (pair,), simulations=50, cross_simulations=100, seed=3,
        native_installed=False,
    )
    report = ParityReport(complete=True, obligations=(), verified=(),
                          pending=(), divergences=(), exact_checks=())
    payload = parity_report_payload(report, deep=samples)
    deep = payload["deep"]
    assert isinstance(deep, dict)
    assert len(deep["samples"]) == len(samples)
    assert deep["complete"] == all(row.passed for row in samples)
    assert all("reference_rates" in row for row in deep["samples"])
    assert all("candidate_rates" in row for row in deep["samples"])
    markdown = parity_report_markdown(payload)
    assert "## Deep certification samples" in markdown
    assert "matrix:basic" in markdown

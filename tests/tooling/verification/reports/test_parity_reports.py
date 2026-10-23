"""Parity report formats, payloads and CLI states (tooling).

These checks describe the report contract (payload fields, markdown, exit
codes and backend selection), not the execution/parity measurements, which
stay in ``tests/python/verification/test_parity.py``.
"""
from mordheim_combat_lab.verification.parity import verify_vectorized_parity
from mordheim_combat_lab.verification.parity import certify_deep
from mordheim_combat_lab.verification.parity import DeepPair
from mordheim_combat_lab.verification.parity import ParityReport
from mordheim_combat_lab.verification.parity import parity_report_markdown
from mordheim_combat_lab.verification.parity import parity_report_payload
from mordheim_combat_lab.verification.parity import verify_specification_parity
from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
from mordheim_construction.compiler import compile_fighter
import pytest


def _single_deep_pair():
    scenario = benchmark_scenarios()[0]
    first, second = compile_fighter(scenario.first), compile_fighter(scenario.second)
    return DeepPair("basic", first, second, scenario.maximum_rounds)


@pytest.mark.evidence
def test_parity_inventory_covers_fields_tags_and_complex_sequences():
    report = verify_vectorized_parity()
    kinds = {item.kind for item in report.obligations}
    assert kinds == {"field", "tag", "sequence"}
    assert all(item.evidence for item in report.obligations)


@pytest.mark.evidence
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


@pytest.mark.evidence
def test_deep_payload_rows_expose_per_engine_wall_times():
    pair = _single_deep_pair()
    samples, _ = certify_deep(
        (pair,), simulations=50, cross_simulations=100, seed=3,
        native_installed=False,
    )
    payload = parity_report_payload(
        ParityReport(complete=True, obligations=(), verified=(),
                     pending=(), divergences=(), exact_checks=()),
        deep=samples, deep_pair_set="fast",
    )
    rows = payload["deep"]["samples"]
    assert payload["deep"]["pair_set"] == "fast"
    assert all("reference_seconds" in row and "candidate_seconds" in row
               for row in rows)
    assert rows[0]["reference_seconds"] > 0
    assert rows[0]["candidate_seconds"] > 0
    markdown = parity_report_markdown(payload)
    assert "Time (ref/cand, s)" in markdown
    assert "- Pair set: `fast`" in markdown


@pytest.mark.evidence
def test_report_distinguishes_smoke_samples_from_certification_samples():
    report = verify_vectorized_parity()
    payload = parity_report_payload(report)
    assert payload["complete"]
    assert not payload["certification_sample_complete"]
    markdown = parity_report_markdown(payload)
    assert "Oracle: `combat.modular (read-only)`" in markdown
    assert "## Deterministic checks" in markdown


@pytest.mark.evidence
def test_report_exposes_semantic_case_statuses_and_couples_completion_to_them():
    report = verify_vectorized_parity()
    specifications = verify_specification_parity()
    payload = parity_report_payload(report, specifications=specifications)
    assert payload["complete"]
    assert payload["specifications"]["passed"]
    assert not payload["specifications"]["pending"]
    markdown = parity_report_markdown(payload)
    assert "## Semantic specification parity" in markdown
    assert "PENDING_ADAPTER: `0`" in markdown
    # Completion is coupled to the semantic cases: while any case is still
    # pending, the certificate must not claim completion.
    from dataclasses import replace
    incomplete = replace(specifications, complete=False)
    payload = parity_report_payload(report, specifications=incomplete)
    assert not payload["complete"]


@pytest.mark.evidence
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


def _comparison(magnitude="winner", *, passed=True, detail="",
                modular=(0.5, 0.4, 0.1), candidate=(0.5, 0.4, 0.1),
                tolerances=(0.05, 0.05, 0.05)):
    from types import SimpleNamespace
    return SimpleNamespace(
        magnitude=magnitude, modular_rates=tuple(modular),
        candidate_rates=tuple(candidate), tolerances=tuple(tolerances),
        passed=passed, detail=detail,
    )


def _battery_result(case, variant, status, *, backend="numpy", detail="",
                    comparisons=(), executed=False, compared=False,
                    approved=False, blocked_by=None, keys=("k::v",),
                    **overrides):
    from types import SimpleNamespace
    values = dict(
        case=case, level="complete", variant=variant,
        obligation=variant.split(".")[0], backend=backend, status=status,
        keys=tuple(keys), observables=("winner",), rows=64, seed=2026,
        horizon=50, executed=executed, compared=compared, approved=approved,
        magnitudes=tuple(item.magnitude for item in comparisons),
        comparisons=tuple(comparisons), modular_seconds=0.0,
        candidate_seconds=0.0, detail=detail, blocked_by=blocked_by,
    )
    values.update(overrides)
    return SimpleNamespace(**values)


def _battery_report(results, *, complete=False, accepted=False, profile="quick"):
    from types import SimpleNamespace
    results = tuple(results)
    return SimpleNamespace(
        complete=complete, accepted=accepted, scope="profile", profile=profile,
        results=results,
        passed=tuple(row.case for row in results if row.status == "PASS"),
        divergences=tuple(row.case for row in results if row.status == "DIVERGENCE"),
        incompatible=tuple(row.case for row in results if row.status == "INCOMPATIBLE"),
        not_run=tuple(row.case for row in results if row.status == "NOT_RUN"),
        missing_variants=(),
    )


def _battery_payload(report, *, backend="numpy", backends=None):
    from mordheim_combat_lab.verification.parity._report import battery_report_payload
    return battery_report_payload(
        report, profile=report.profile, backend=backend,
        catalog_sha256="catalog-sha", inventory_sha256="inventory-sha",
        elapsed_seconds=1.5, backends=backends,
    )


@pytest.mark.evidence
def test_battery_payload_counts_stages_magnitudes_and_limits():
    comparisons = (_comparison("winner"), _comparison("rounds"))
    report = _battery_report((
        _battery_result("a", "B06.2", "PASS", executed=True, compared=True,
                        approved=True, comparisons=comparisons),
        _battery_result("b", "B06.2", "DIVERGENCE", executed=True, compared=True,
                        comparisons=(_comparison("winner", passed=False),),
                        detail="DIVERGENCE: winner[first]: modular=0.9, "
                               "candidate=0.1, tol=0.05"),
        _battery_result("c", "B08.4", "INCOMPATIBLE",
                        blocked_by="state:G00/G02",
                        detail="INCOMPATIBLE:state:G00/G02"),
        _battery_result("d", "B06.2", "NOT_RUN",
                        detail="NOT_RUN:native-stale: extension is not installed"),
        _battery_result("e", "B06.2", "NOT_RUN",
                        detail="NOT_RUN:compile:KeyError: missing weapon"),
    ))
    payload = _battery_payload(report)
    coverage = payload["coverage"]
    assert payload["execution"] == "run"
    assert coverage["declared"] == 5
    # A real input limit is not preparation evidence; a compile error still is.
    assert coverage["prepared"] == 4
    assert coverage["executed"] == 2
    assert coverage["compared"] == 2
    assert coverage["approved"] == 1
    assert coverage["divergent"] == 1
    assert coverage["incompatible"] == 1
    assert coverage["not_run"] == 2
    assert coverage["errors"] == 2
    assert coverage["dependency"] == 2
    # Statistical parity never proves rule sensitivity on its own.
    assert coverage["sensitivity_pending"] == 5
    assert payload["magnitudes"] == {
        "winner": {"cases": 2, "passed": 1},
        "rounds": {"cases": 1, "passed": 1},
    }
    assert payload["limits"] == {"c": "state:G00/G02"}
    assert payload["sensitivity"]["demonstrated"] == []
    assert payload["sensitivity"]["pending"] == ["a", "b", "c", "d", "e"]
    assert payload["cases"][0]["sensitivity"] == "pending"
    assert payload["cases"][1]["comparisons"][0]["passed"] is False
    assert payload["complete"] is False and payload["accepted"] is False


@pytest.mark.evidence
def test_battery_payload_groups_dependencies_by_owner():
    report = _battery_report((
        _battery_result("a", "B06.2", "INCOMPATIBLE",
                        detail="INCOMPATIBLE:state:G00/G02 owner=G00/G02"),
        _battery_result("b", "B08.4", "INCOMPATIBLE",
                        detail="INCOMPATIBLE:decision:per-row owner=P02"),
    ))
    payload = _battery_payload(report)
    owners = payload["coverage"]["dependencies_by_owner"]
    assert owners == {"G00/G02": ["a"], "P02": ["b"]}
    assert payload["variants"]["B06.2"]["dependencies"] == ["G00/G02"]
    assert payload["execution"] == "not-run"


@pytest.mark.evidence
def test_battery_payload_tracks_clause_keys_per_case():
    report = _battery_report((
        _battery_result("a", "B06.2", "PASS", keys=("a::x", "b::y"),
                        executed=True, compared=True, approved=True,
                        comparisons=(_comparison("winner"),)),
        _battery_result("b", "B06.2", "INCOMPATIBLE", keys=("a::x",),
                        blocked_by="state:G00/G02",
                        detail="INCOMPATIBLE:state:G00/G02"),
    ))
    payload = _battery_payload(report)
    clauses = payload["clauses"]
    assert clauses["a::x"] == {
        "cases": 2, "executed": 1, "compared": 1, "approved": 1,
        "divergent": 0, "incompatible": 1,
    }
    assert clauses["b::y"]["cases"] == 1


@pytest.mark.evidence
def test_battery_payload_keeps_backends_separate():
    from mordheim_combat_lab.verification.parity._report import battery_report_markdown
    report = _battery_report((
        _battery_result("a", "B06.2", "PASS", executed=True, compared=True,
                        approved=True, comparisons=(_comparison("winner"),)),
        _battery_result("a", "B06.2", "NOT_RUN", backend="native",
                        detail="NOT_RUN:native-stale: extension is stale"),
    ))
    payload = _battery_payload(report, backends=("numpy", "native"))
    rows = {row["backend"]: row for row in payload["backends"]}
    assert rows["numpy"]["available"] is True
    assert rows["numpy"]["compared"] == 1 and rows["numpy"]["approved"] == 1
    assert rows["native"]["available"] is False and rows["native"]["not_run"] == 1
    assert rows["native"]["executed"] == 0
    markdown = battery_report_markdown(payload)
    assert "## Backend availability" in markdown
    assert "| native | False |" in markdown


@pytest.mark.evidence
def test_battery_markdown_lists_magnitudes_limits_and_sensitivity():
    from mordheim_combat_lab.verification.parity._report import battery_report_markdown
    report = _battery_report((
        _battery_result("a", "B06.2", "PASS", executed=True, compared=True,
                        approved=True,
                        comparisons=(_comparison("winner"), _comparison("rounds"))),
        _battery_result("b", "B08.4", "INCOMPATIBLE", blocked_by="state:G00/G02",
                        detail="INCOMPATIBLE:state:G00/G02 owner=G00/G02"),
    ))
    payload = _battery_payload(report)
    markdown = battery_report_markdown(payload)
    assert "## Magnitudes compared" in markdown and "| winner | 1 | 1 |" in markdown
    assert "## Real input limits" in markdown and "`b`: `state:G00/G02`" in markdown
    assert "## Variants" in markdown and "Sensitivity pending" in markdown
    assert "six-sigma tolerance" in markdown
    assert "`sensitivity` is pending" in markdown


@pytest.mark.evidence
def test_battery_exception_before_observation_is_not_comparison():
    report = _battery_report((
        _battery_result("a", "B06.2", "DIVERGENCE",
                        detail="DIVERGENCE:exception:ValueError: boom"),
        _battery_result("b", "B06.2", "DIVERGENCE", executed=True, compared=True,
                        comparisons=(_comparison("winner", passed=False),),
                        detail="DIVERGENCE: winner[second]: modular=0.1, "
                               "candidate=0.3, tol=0.05"),
    ))
    payload = _battery_payload(report)
    coverage = payload["coverage"]
    # The exception never obtained both samples: not execution nor comparison.
    assert coverage["executed"] == 1
    assert coverage["compared"] == 1
    assert coverage["approved"] == 0
    assert coverage["divergent"] == 2
    assert coverage["errors"] == 2
    assert payload["cases"][0]["executed"] is False
    assert payload["cases"][0]["compared"] is False


@pytest.mark.evidence
def test_battery_malformed_outcome_codes_are_an_own_error():
    from mordheim_combat_lab.verification.parity._report import battery_failure_kind

    detail = "NOT_RUN:outcome-codes: oracle winner code(s) [3] outside [0, 1, 2]"
    assert battery_failure_kind("NOT_RUN", detail) == "error"
    # It never becomes a divergence or an unresolved terminal category.
    assert battery_failure_kind("NOT_RUN", "NOT_RUN:native-stale: absent") == "dependency"


@pytest.mark.evidence
def test_battery_command_fails_on_own_error_without_require_complete(monkeypatch):
    from types import SimpleNamespace

    from mordheim_combat_lab.cli import commands as cli
    from mordheim_combat_lab.verification.parity import _battery_cases as catalog
    from mordheim_combat_lab.verification.parity import _battery_runner as runner

    error_report = _battery_report((
        _battery_result("a", "B06.2", "NOT_RUN",
                        detail="NOT_RUN:compile: missing weapon owner=P01"),
    ))
    args = SimpleNamespace(
        profile="quick", backend="numpy", rows=None, json=True,
        output=None, require_complete=False,
    )
    monkeypatch.setattr(catalog, "battery_cases", lambda profile: ())
    monkeypatch.setattr(runner, "run_battery", lambda *a, **k: error_report)
    # An own error fails even without --require-complete.
    assert cli._battery_command(args, "quick") == 1

    dependency_report = _battery_report((
        _battery_result("a", "B06.2", "INCOMPATIBLE", blocked_by="state:G00/G02",
                        detail="INCOMPATIBLE:state:G00/G02 owner=G00/G02"),
    ))
    monkeypatch.setattr(runner, "run_battery", lambda *a, **k: dependency_report)
    # A real input limit leaves the run partial: incomplete, not failed.
    assert cli._battery_command(args, "quick") == 0
    args.require_complete = True
    assert cli._battery_command(args, "quick") == 1


@pytest.mark.evidence
def test_parity_cli_separates_the_battery_from_the_historical_certificate():
    from mordheim_combat_lab.cli.commands import build_parser, parity_command

    parser = build_parser()
    # The historical presets keep their defaults when --profile is absent.
    historical = parser.parse_args(["parity", "--level", "statistical"])
    assert historical.profile is None and historical.backend is None
    assert historical.level == "statistical" and historical.pair_set is None

    battery = parser.parse_args([
        "parity", "--profile", "quick", "--backend", "all", "--rows", "8",
    ])
    assert battery.profile == "quick" and battery.backend == "all"
    assert battery.rows == 8 and battery.level is None and battery.pair_set is None

    # An explicit legacy selector plus --profile would mix two measurements.
    mixed = parser.parse_args(["parity", "--profile", "quick", "--level", "deep"])
    assert parity_command(mixed) == 2
    mixed = parser.parse_args(["parity", "--profile", "complete",
                               "--pair-set", "mini"])
    assert parity_command(mixed) == 2
    mixed = parser.parse_args(["parity", "--profile", "deep", "--truncations"])
    assert parity_command(mixed) == 2
    # --backend needs a profile or statistical; --rows still needs a profile.
    assert parity_command(parser.parse_args(["parity", "--backend", "native"])) == 2
    assert parity_command(parser.parse_args(["parity", "--rows", "8"])) == 2
    # Calibration never stands in for acceptance.
    assert parity_command(parser.parse_args([
        "parity", "--profile", "quick", "--rows", "8", "--require-complete",
    ])) == 2


@pytest.mark.parametrize("backend,installed,expected", [
    ("numpy", ("numpy", "native"), ("numpy",)),
    ("native", ("numpy", "native"), ("native",)),
    ("all", ("numpy", "native"), ("numpy", "native")),
    (None, ("numpy", "native"), ("numpy", "native")),
    (None, ("numpy",), ("numpy",)),
    ("native", ("numpy",), ()),
    ("all", ("numpy",), ()),
])
@pytest.mark.evidence
def test_statistical_cli_selects_backends_and_shares_oracle(
    monkeypatch, backend, installed, expected,
):
    from types import SimpleNamespace
    from mordheim_combat import vectorized
    from mordheim_combat.modular import parallel
    from mordheim_combat_lab.cli import benchmarking, commands
    from mordheim_combat_lab.verification import parity

    oracle_calls = []
    candidates = []
    oracle = object()
    monkeypatch.setattr(vectorized, "available_backends", lambda: installed)
    monkeypatch.setattr(parity, "verify_vectorized_parity",
                        lambda: SimpleNamespace(complete=True))
    monkeypatch.setattr(parity, "verify_specification_parity",
                        lambda: SimpleNamespace(complete=True))
    monkeypatch.setattr(parity, "parity_report_payload", lambda *a, **kw: {})
    monkeypatch.setattr(benchmarking, "benchmark_scenarios", lambda: (
        SimpleNamespace(id="selection", maximum_rounds=1),
    ))
    monkeypatch.setattr(benchmarking, "compile_benchmark_fighters",
                        lambda scenario: (object(), object()))

    def sample(*args, **kwargs):
        oracle_calls.append(kwargs)
        return oracle

    def compare(*args, **kwargs):
        assert kwargs["modular"] is oracle
        candidates.append(kwargs["backend"])
        return SimpleNamespace(passed=True)

    monkeypatch.setattr(parallel, "run_oracle_sample", sample)
    monkeypatch.setattr(parity, "compare_statistical_parity", compare)
    argv = ["parity", "--level", "statistical", "--json",
            "--statistical-simulations", "1", "--workers", "1"]
    if backend is not None:
        argv += ["--backend", backend]
    args = commands.build_parser().parse_args(argv)
    assert commands.parity_command(args) == (0 if expected else 2)
    assert tuple(candidates) == expected
    assert len(oracle_calls) == (1 if expected else 0)


@pytest.mark.evidence
def test_statistical_backend_does_not_silently_select_truncation_backends():
    from mordheim_combat_lab.cli.commands import build_parser, parity_command

    args = build_parser().parse_args([
        "parity", "--level", "statistical", "--backend", "numpy", "--truncations",
    ])
    assert parity_command(args) == 2

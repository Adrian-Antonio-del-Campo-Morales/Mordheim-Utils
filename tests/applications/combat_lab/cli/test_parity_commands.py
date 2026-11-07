"""Combat Lab parity CLI: battery exit codes and parity command routing."""

import pytest


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
    monkeypatch.setattr(runner, "prepare_cases", lambda *a, **k: ((), {}))
    monkeypatch.setattr(runner, "battery_report", lambda *a, **k: error_report)
    # An own error fails even without --require-complete.
    assert cli._battery_command(args, "quick") == 1

    dependency_report = _battery_report((
        _battery_result("a", "B06.2", "INCOMPATIBLE", blocked_by="state:G00/G02",
                        detail="INCOMPATIBLE:state:G00/G02 owner=G00/G02"),
    ))
    monkeypatch.setattr(runner, "battery_report", lambda *a, **k: dependency_report)
    # A real input limit leaves the run partial: incomplete, not failed.
    assert cli._battery_command(args, "quick") == 0
    args.require_complete = True
    assert cli._battery_command(args, "quick") == 1


@pytest.mark.evidence
def test_parity_cli_separates_the_battery_from_the_historical_certificate():
    from mordheim_combat_lab.cli.commands import (
        _normalise_parity_args, build_parser, parity_command,
    )

    parser = build_parser()
    # The historical certificate: no battery profile, default candidates.
    historical = parser.parse_args(["parity", "--certificate", "statistical"])
    assert _normalise_parity_args(historical) is None
    assert historical.profile is None and historical.backend is None
    assert historical.level == "statistical"
    assert [item.id for item in historical.statistical_scenarios] == [
        item.id for item in _scenarios("small")]

    # The battery certificate takes its profile from --scenarios and its
    # width from --simulations.
    battery = parser.parse_args([
        "parity", "--certificate", "battery", "--scenarios", "battery-quick",
        "--backend", "numpy", "native", "--simulations", "8",
    ])
    assert _normalise_parity_args(battery) is None
    assert battery.profile == "quick" and battery.backend == "all"
    assert battery.rows == 8 and battery.level is None

    # A battery profile and a historical certificate are two measurements.
    for argv in (
        ["--certificate", "battery", "--scenarios", "battery-quick", "small"],
        ["--certificate", "deep", "--scenarios", "battery-complete"],
        ["--certificate", "battery", "--truncations"],
        ["--scenarios", "e2e", "small"],
        ["--certificate", "deterministic", "--scenarios", "small"],
        ["--backend", "modular", "numpy"],
    ):
        assert parity_command(parser.parse_args(["parity", *argv])) == 2, argv
    # --backend needs something to compare; --simulations something to size.
    assert parity_command(parser.parse_args(["parity", "--backend", "native"])) == 2
    assert parity_command(parser.parse_args(["parity", "--simulations", "8"])) == 2
    # The battery width is accepted together with --require-complete
    # (acceptance at a chosen width); see
    # test_rows_override_reaches_preparation_and_the_report.
    accepted = parser.parse_args([
        "parity", "--certificate", "battery", "--scenarios", "battery-quick",
        "--simulations", "8000", "--require-complete",
    ])
    assert _normalise_parity_args(accepted) is None
    assert accepted.rows == 8000 and accepted.require_complete


def _scenarios(level):
    from tests.engines.fixtures.precompiled_catalog import scenarios_for_level

    return scenarios_for_level(level)


@pytest.mark.parametrize("rows", [None, 8000])
def test_rows_override_reaches_preparation_and_the_report(monkeypatch, capsys, rows):
    import json
    from types import SimpleNamespace

    from mordheim_combat_lab.cli import commands as cli
    from mordheim_combat_lab.verification.parity import _battery_cases as catalog
    from mordheim_combat_lab.verification.parity import _battery_runner as runner

    widths = []
    monkeypatch.setattr(catalog, "battery_cases", lambda profile: ())
    monkeypatch.setattr(runner, "prepare_cases",
                        lambda cases, **kwargs: widths.append(kwargs["rows"]) or ((), {}))
    monkeypatch.setattr(runner, "battery_report", lambda *a, **k: _battery_report(()))
    args = SimpleNamespace(profile="quick", backend="numpy", rows=rows, json=True,
                           output=None, require_complete=True)
    cli._battery_command(args, "quick")
    assert widths == [rows]  # None keeps every case's declared width
    payload = json.loads(capsys.readouterr().out)
    assert payload["preparation"]["rows_override"] == rows


@pytest.mark.parametrize("backend,installed,expected", [
    (["numpy"], ("numpy", "native"), ("numpy",)),
    (["native"], ("numpy", "native"), ("native",)),
    (["numpy", "native"], ("numpy", "native"), ("numpy", "native")),
    (None, ("numpy", "native"), ("numpy", "native")),
    (None, ("numpy",), ("numpy",)),
    (["native"], ("numpy",), ()),
    (["numpy", "native"], ("numpy",), ()),
])
@pytest.mark.evidence
def test_statistical_cli_selects_backends_and_shares_oracle(
    monkeypatch, backend, installed, expected,
):
    from types import SimpleNamespace
    from mordheim_combat import vectorized
    from mordheim_combat.modular import parallel
    from mordheim_combat_lab.cli import benchmarking, commands, scenarios
    from mordheim_combat_lab.verification import parity

    oracle_calls = []
    candidates = []
    oracle = object()
    monkeypatch.setattr(vectorized, "available_backends", lambda: installed)
    monkeypatch.setattr(parity, "verify_vectorized_parity",
                        lambda: SimpleNamespace(complete=True))
    monkeypatch.setattr(parity, "parity_report_payload", lambda *a, **kw: {})
    monkeypatch.setattr(scenarios, "select_scenarios", lambda tokens: (
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
    argv = ["parity", "--certificate", "statistical", "--json",
            "--simulations", "1", "--workers", "1"]
    if backend is not None:
        argv += ["--backend", *backend]
    args = commands.build_parser().parse_args(argv)
    assert commands.parity_command(args) == (0 if expected else 2)
    assert tuple(candidates) == expected
    assert len(oracle_calls) == (1 if expected else 0)


@pytest.mark.evidence
def test_statistical_backend_does_not_silently_select_truncation_backends():
    from mordheim_combat_lab.cli.commands import build_parser, parity_command

    args = build_parser().parse_args([
        "parity", "--certificate", "statistical", "--backend", "numpy", "--truncations",
    ])
    assert parity_command(args) == 2


@pytest.mark.parametrize("selection,catalog,profile", [
    (["small"], "precompiled", None),
    (["battery-deep"], "battery", "deep"),
    (["small", "battery-quick"], "all", "quick"),
    ([], "all", None),  # --backend modular alone: both catalogues
])
def test_fixture_catalogue_modular_options_reach_the_catalogue_command(
    monkeypatch, selection, catalog, profile,
):
    from mordheim_combat_lab.cli import commands
    calls = []
    monkeypatch.setattr(commands, "_catalog_parity_command", lambda args: calls.append(args) or 0)
    argv = ["parity", "--backend", "modular", "--workers", "8"]
    if selection:
        argv += ["--scenarios", *selection]
    args = commands.build_parser().parse_args(argv)
    assert commands.parity_command(args) == 0
    assert calls == [args]
    assert args.catalog == catalog and args.backend == "modular"
    assert args.workers == 8 and args.profile == profile


@pytest.mark.parametrize("selection,count", [
    (["small"], 8), (["normal"], 30), (["big"], 43),
    (["long"], 1),             # a scenario name: that one scenario
    (["small", "long"], 9),    # several values: their union
])
def test_precompiled_catalogue_uses_unified_levels_and_execution_settings(
    monkeypatch, selection, count,
):
    from types import SimpleNamespace
    from mordheim_combat_lab.cli import benchmarking, commands
    from mordheim_combat_lab.verification import parity
    from mordheim_construction import compiler
    from tests.engines.fixtures.precompiled_catalog import select_scenarios

    def no_compile(*args, **kwargs):
        raise AssertionError("frozen scenarios must not compile fighters")

    monkeypatch.setattr(compiler, "compile_fighter", no_compile)
    selected = []

    def run(cases, **kwargs):
        selected.extend(cases)
        return SimpleNamespace(rows=(), modular_duels=0)

    monkeypatch.setattr(parity, "run_parity", run)
    argv = ["parity", "--scenarios", *selection, "--backend", "modular",
            "--simulations", "7", "--seed", "19", "--json"]
    # The stub emits no rows, so the command correctly reports an incomplete run.
    assert commands.parity_command(commands.build_parser().parse_args(argv)) == 1
    assert len(selected) == count
    assert all(case.label.startswith("scenario/") for case in selected)
    assert all(case.simulations == 7 and case.seed == 19 for case in selected)
    assert [case.label for case in selected] == [
        f"scenario/{item.name}" for item in select_scenarios(selection)]
    for scenario in select_scenarios(selection):
        assert benchmarking.compile_benchmark_fighters(scenario)

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


@pytest.mark.parametrize("catalog", ["precompiled", "battery", "all"])
def test_fixture_catalogue_modular_options_reach_the_catalogue_command(monkeypatch, catalog):
    from mordheim_combat_lab.cli import commands
    calls = []
    monkeypatch.setattr(commands, "_catalog_parity_command", lambda args: calls.append(args) or 0)
    args = commands.build_parser().parse_args([
        "parity", "--catalog", catalog, "--backend", "modular", "--workers", "8",
    ])
    assert commands.parity_command(args) == 0
    assert calls == [args]
    assert args.catalog == catalog and args.backend == "modular"
    assert args.workers == 8 and args.profile is None


@pytest.mark.parametrize("level,count", [(None, 8), ("small", 8), ("normal", 30), ("long", 43)])
def test_precompiled_catalogue_uses_unified_levels_and_execution_settings(monkeypatch, level, count):
    from types import SimpleNamespace
    from mordheim_combat_lab.cli import benchmarking, commands
    from mordheim_combat_lab.verification import parity
    from mordheim_construction import compiler
    from tests.engines.fixtures.precompiled_catalog import scenarios_for_level

    def no_compile(*args, **kwargs):
        raise AssertionError("frozen scenarios must not compile fighters")

    monkeypatch.setattr(compiler, "compile_fighter", no_compile)
    selected = []

    def run(cases, **kwargs):
        selected.extend(cases)
        return SimpleNamespace(rows=(), modular_duels=0)

    monkeypatch.setattr(parity, "run_parity", run)
    argv = ["parity", "--catalog", "precompiled", "--backend", "modular",
            "--simulations", "7", "--seed", "19", "--json"]
    if level is not None:
        argv += ["--level", level]
    # The stub emits no rows, so the command correctly reports an incomplete run.
    assert commands.parity_command(commands.build_parser().parse_args(argv)) == 1
    assert len(selected) == count
    assert all(case.label.startswith("scenario/") for case in selected)
    assert all(case.simulations == 7 and case.seed == 19 for case in selected)
    for scenario in scenarios_for_level(level or "small"):
        assert benchmarking.compile_benchmark_fighters(scenario)

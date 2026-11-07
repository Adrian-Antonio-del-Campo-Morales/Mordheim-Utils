"""Combat Lab parity CLI: what runs, how it is compared and how it exits."""

import json

import pytest

E2E_KEY = "e2e/core/combat-critical-hits/a-critical-table-modifier-shifts-the-applied-band"


def _stub_runner(monkeypatch, status="PASS"):
    """Replace the sampler: record the cases and answer one row per backend."""
    from types import SimpleNamespace

    from mordheim_combat_lab.verification import parity
    from mordheim_combat_lab.verification.parity import ParityRow

    calls = []

    def run(cases, **kwargs):
        cases = tuple(cases)
        calls.append((cases, kwargs))
        rows = tuple(
            ParityRow(case=case.label, backend=backend, maximum_rounds=case.maximum_rounds,
                      simulations=case.simulations or 0, status=status,
                      executed=True, compared=status == "PASS", approved=status == "PASS")
            for case in cases for backend in kwargs["backends"]
        )
        return SimpleNamespace(rows=rows, modular_duels=0)

    monkeypatch.setattr(parity, "run_parity", run)
    return calls


def _parity(argv):
    from mordheim_combat_lab.cli import commands

    return commands.parity_command(commands.build_parser().parse_args(["parity", *argv]))


@pytest.mark.evidence
def test_without_scenarios_only_the_exact_obligation_checks_run(monkeypatch, capsys):
    from types import SimpleNamespace

    from mordheim_combat_lab.verification import parity

    calls = _stub_runner(monkeypatch)
    report = SimpleNamespace(complete=False, obligations=("a", "b"), verified=("a",),
                             pending=("b",), divergences=(), exact_checks=("hit",))
    monkeypatch.setattr(parity, "verify_vectorized_parity", lambda: report)
    monkeypatch.setattr(parity, "parity_report_payload", lambda *a, **k: {"complete": False})
    assert _parity([]) == 0
    assert _parity(["--require-complete"]) == 1
    assert calls == []  # nothing sampled
    assert "1/2 obligations verified" in capsys.readouterr().out


@pytest.mark.evidence
def test_every_kind_of_scenario_runs_together_in_selection_order(monkeypatch, capsys):
    calls = _stub_runner(monkeypatch)
    # A precompiled scenario, a battery case with scripted decisions and an
    # E2E delivery: one runner, one report, the order asked.
    assert _parity(["--scenarios", "long", "battery/q08-death-blow-optional", E2E_KEY,
                    "--simulations", "7200", "--json"]) == 0
    (cases, options), = calls
    assert [case.label for case in cases] == [
        "scenario/long", "battery/q08-death-blow-optional", E2E_KEY]
    assert options["backends"] == ("numpy",) and options["candidate"] == "observed"
    assert cases[1].decisions is not None and cases[2].context is not None
    payload = json.loads(capsys.readouterr().out)
    assert payload["complete"] is True and payload["provenance"]["engine_digests"]


@pytest.mark.evidence
def test_rounds_replace_every_case_limit_once_per_value(monkeypatch):
    calls = _stub_runner(monkeypatch)
    assert _parity(["--scenarios", "basic", "--rounds", "2,60", "--json"]) == 0
    (cases, _), = calls
    # 60 exceeds basic's own 50-round limit: the value replaces it, it does
    # not merely truncate.
    assert [(case.label, case.maximum_rounds) for case in cases] == [
        ("scenario/basic@rounds=2", 2), ("scenario/basic@rounds=60", 60)]
    calls.clear()
    assert _parity(["--scenarios", "basic", "--rounds", "9", "--json"]) == 0
    assert [(case.label, case.maximum_rounds) for case in calls[0][0]] == [("scenario/basic", 9)]


@pytest.mark.parametrize("argv", [
    ["--scenarios", "basic", "--backend", "modular", "numpy"],
    ["--scenarios", "no-such-scenario"],
    ["--scenarios", "battery/no-such-case"],
])
def test_configuration_errors_exit_2_before_sampling(monkeypatch, argv):
    calls = _stub_runner(monkeypatch)
    assert _parity(argv) == 2
    assert calls == []


@pytest.mark.evidence
def test_declared_limitations_are_listed_not_failed(monkeypatch, capsys):
    # A battery case with an input limit is INCOMPATIBLE: listed with its
    # reason, never a failure, but the run is not complete.
    from mordheim_combat_lab.verification import parity
    from mordheim_combat_lab.verification.parity import _battery_cases as catalog

    def run(cases, **kwargs):
        from types import SimpleNamespace
        from mordheim_combat_lab.verification.parity import ParityRow

        rows = tuple(
            ParityRow(case=case.label, backend="numpy", maximum_rounds=case.maximum_rounds,
                      simulations=7200, status="INCOMPATIBLE" if case.blocked_by else "PASS",
                      approved=not case.blocked_by, blocked_by=case.blocked_by)
            for case in cases)
        return SimpleNamespace(rows=rows, modular_duels=0)

    monkeypatch.setattr(parity, "run_parity", run)
    blocked = next(f"battery/{case.id}" for case in catalog.battery_cases()
                   if catalog.input_limit(case))
    argv = ["--scenarios", "basic", blocked, "--simulations", "7200", "--json"]
    assert _parity(argv) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["summary"]["blocked"] == 1 and payload["summary"]["failed"] == 0
    assert payload["complete"] is False
    assert _parity([*argv, "--require-complete"]) == 1


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
    # The stub emits no rows, so the command correctly reports a failed run.
    assert commands.parity_command(commands.build_parser().parse_args(argv)) == 1
    assert len(selected) == count
    assert all(case.label.startswith("scenario/") for case in selected)
    assert all(case.simulations == 7 and case.seed == 19 for case in selected)
    assert [case.label for case in selected] == [
        f"scenario/{item.name}" for item in select_scenarios(selection)]
    for scenario in select_scenarios(selection):
        assert benchmarking.compile_benchmark_fighters(scenario)




@pytest.mark.evidence
def test_battery_cases_run_with_their_decisions_and_declared_limits(monkeypatch, capsys):
    calls = _stub_runner(monkeypatch)
    from mordheim_combat_lab.verification.parity import _battery_cases as catalog

    cases = catalog.battery_cases()
    scripted = next(case.id for case in cases if case.decisions)
    blocked = next(case.id for case in cases if catalog.input_limit(case))
    assert _parity(["--scenarios", f"battery/{scripted}", f"battery/{blocked}",
                    "--simulations", "7200", "--json"]) == 0
    # The scripted case runs with its script; the blocked one is reported.
    (prepared, _), = calls
    assert [case.label for case in prepared] == [f"battery/{scripted}"]
    assert prepared[0].decisions._choices  # the script travels with the case
    payload = json.loads(capsys.readouterr().out)
    statuses = {row["case"]: row["status"] for row in payload["results"]}
    assert statuses[f"battery/{blocked}"] == "INCOMPATIBLE"
    assert payload["summary"]["blocked"] == 1 and payload["complete"] is False

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_SCRIPT = REPO_ROOT / "tools" / "mordheim-utils.py"

COMMANDS = (
    "combat-lab",
    "warband-manager",
    "benchmark",
    "parity",
    "test-report",
    "coverage-gate",
    "verify",
    "audit",
    "validate",
    "tests",
    "combine-kb",
    "build-native",
    "doctor",
)

LAB_COMMANDS = ("benchmark", "parity", "test-report", "coverage-gate",
                "verify", "audit", "validate")


@pytest.fixture()
def cli():
    spec = importlib.util.spec_from_file_location("mordheim_utils_launcher", CLI_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _record_run(cli, monkeypatch):
    calls = []

    def fake_run(*argv):
        calls.append(list(argv))
        return 0

    monkeypatch.setattr(cli, "_run", fake_run)
    return calls


def test_help_lists_every_command(cli, capsys):
    assert cli.main(["--help"]) == 0
    output = capsys.readouterr().out
    for name in COMMANDS:
        assert name in output
    assert "mordheim-utils.py" in output


def test_bare_invocation_prints_help(cli, capsys):
    assert cli.main([]) == 0
    output = capsys.readouterr().out
    for name in COMMANDS:
        assert name in output


def test_unknown_command_is_rejected(cli, capsys):
    assert cli.main(["does-not-exist"]) == 2
    assert "unknown command" in capsys.readouterr().err


def test_combat_lab_launches_the_lab_ui(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["combat-lab"]) == 0
    assert calls == [[sys.executable, "-m", "mordheim_combat_lab", "ui"]]


def test_warband_manager_launches_the_campaign_app(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["warband-manager"]) == 0
    assert calls == [[sys.executable, "-m", "mordheim_campaign"]]


@pytest.mark.parametrize("name", LAB_COMMANDS)
def test_lab_commands_are_forwarded_to_the_lab_cli(cli, monkeypatch, name):
    calls = _record_run(cli, monkeypatch)
    assert cli.main([name]) == 0
    assert calls == [[sys.executable, "-m", "mordheim_combat_lab", name]]


def test_lab_command_forwards_arguments_verbatim(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["benchmark", "-n", "1000", "--json"]) == 0
    assert calls == [
        [sys.executable, "-m", "mordheim_combat_lab", "benchmark", "-n", "1000", "--json"]
    ]


def test_tests_forwards_pytest_flags_without_double_dash(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["tests", "--scope", "cli", "-q", "-p", "no:cacheprovider"]) == 0
    assert calls == [
        [sys.executable, "-m", "pytest", "tests/cli", "-q", "-p", "no:cacheprovider"]
    ]


def test_tests_forwards_pytest_flags_after_double_dash(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["tests", "--scope", "cli", "--", "-q", "-p", "no:cacheprovider"]) == 0
    assert calls == [[sys.executable, "-m", "pytest", "tests/cli", "-q", "-p", "no:cacheprovider"]]


def test_tests_default_scope_is_all(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["tests"]) == 0
    assert calls == [[sys.executable, "-m", "pytest", "tests"]]


def test_tests_rejects_unknown_scope(cli, capsys):
    assert cli.main(["tests", "--scope", "nope"]) == 2
    assert "unknown scope" in capsys.readouterr().err


def test_test_scope_paths_are_non_empty_and_known(cli):
    assert set(cli.SCOPE_PATHS) >= {
        "all", "engines", "modular", "vectorized", "native", "campaign",
        "knowledge", "verification", "construction", "ui", "cli", "architecture",
    }
    for paths in cli.SCOPE_PATHS.values():
        assert paths


def test_deterministic_scope_mirrors_the_coverage_gate_suites(cli):
    from mordheim_combat_lab.verification.coverage_gate import DEFAULT_SUITES

    assert cli.SCOPE_PATHS["deterministic"] == DEFAULT_SUITES


def test_combine_kb_forwards_to_the_kb_script(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    script = str(cli.COMBINE_KB_SCRIPT)
    assert cli.main(["combine-kb", "sources/knowledge", "-o", "outputs/kb"]) == 0
    assert calls == [
        [sys.executable, script, "sources/knowledge", "-o", "outputs/kb"]
    ]


def test_build_native_editable_install(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["build-native"]) == 0
    assert calls == [[sys.executable, "-m", "pip", "install", "-e", "."]]


def test_doctor_reports_environment(cli, capsys):
    assert cli.doctor_command() == 0
    output = capsys.readouterr().out
    assert "Python:" in output
    assert "optimized combat backends:" in output
    assert "modular reference engine:" in output
    assert "Combat Lab:" in output
    assert "Campaign Manager:" in output


def test_completion_offers_every_command(cli):
    candidates = cli._command_candidates([])
    assert set(candidates) == {name for name, _ in cli.COMMANDS}


def test_completion_filters_the_command_name(cli):
    assert cli._command_candidates(["bench"]) == ["benchmark"]
    assert "parity" in cli._command_candidates(["par"])
    assert cli._command_candidates(["doctor"]) == ["doctor"]


def test_completion_introspects_lab_options_and_choices(cli):
    # An empty trailing word models the cursor right after a space.
    options = cli._command_candidates(["benchmark", ""])
    assert "--deep" in options
    assert "--simulation-sizes" in options
    assert "--deep-simulation-sizes" in cli._command_candidates(["benchmark", "--deep-"])
    assert cli._command_candidates(["benchmark", "--backend", "nat"]) == ["native"]
    assert "all" in cli._command_candidates(["benchmark", "--backend", ""])


def test_completion_covers_tests_scope_values(cli):
    assert cli._command_candidates(["tests", "--scope", "vec"]) == ["vectorized"]
    assert cli._command_candidates(["tests", "--scope", "det"]) == ["deterministic"]
    assert "all" in cli._command_candidates(["tests", "--scope", ""])
    assert cli._command_candidates(["tests", "--scope=ver"]) == ["--scope=verification"]


def test_completion_is_empty_for_unknown_commands(cli):
    assert cli._command_candidates(["does-not-exist", "--x"]) == []
    assert cli._command_candidates(["doctor", "--nope"]) == []

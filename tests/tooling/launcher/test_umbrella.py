import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CLI_SCRIPT = REPO_ROOT / "tools" / "mordheim-utils.py"

COMMANDS = (
    "combat-lab",
    "verify",
    "report",
    "benchmark",
    "parity",
    "coverage-gate",
    "calibrate",
    "tests",
    "check-presentation",
    "run-ci",
    "doctor",
)

LAB_COMMANDS = ("benchmark", "parity", "coverage-gate", "verify", "calibrate")

# Most cases prove the launcher routes each command (and its flags) to the
# right entry point; the help-listing case is the visible surface, so it is
# marked separately.


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


@pytest.mark.phase7_warband
def test_help_lists_every_command(cli, capsys):
    assert cli.main(["--help"]) == 0
    output = capsys.readouterr().out
    for name in COMMANDS:
        assert name in output
    assert "mordheim-utils.py" in output


@pytest.mark.phase7_warband
def test_unknown_command_is_rejected(cli, capsys):
    assert cli.main(["does-not-exist"]) == 2
    assert "unknown command" in capsys.readouterr().err


@pytest.mark.phase7_warband
def test_combat_lab_launches_the_lab_ui(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["combat-lab"]) == 0
    assert calls == [[sys.executable, "-m", "mordheim_combat_lab", "ui"]]


@pytest.mark.phase7_warband
@pytest.mark.parametrize("name", LAB_COMMANDS)
def test_lab_commands_are_forwarded_to_the_lab_cli(cli, monkeypatch, name):
    calls = _record_run(cli, monkeypatch)
    assert cli.main([name]) == 0
    assert calls == [[sys.executable, "-m", "mordheim_combat_lab", name]]


@pytest.mark.phase7_warband
def test_tests_forwards_pytest_flags_after_double_dash(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["tests", "--scope", "cli", "--", "-q", "-p", "no:cacheprovider"]) == 0
    assert calls == [[sys.executable, "-m", "pytest", "tests/tooling/launcher",
                      "tests/applications/combat_lab/cli", "-q", "-p", "no:cacheprovider"]]


@pytest.mark.phase7_warband
def test_tests_default_scope_is_all(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["tests"]) == 0
    assert calls == [[sys.executable, "-m", "pytest", "tests"]]

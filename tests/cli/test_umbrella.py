import argparse

import pytest

from mordheim_utils.cli import SCOPE_PATHS
from mordheim_utils.cli import build_parser
from mordheim_utils.cli import doctor_command
from mordheim_utils.cli import main

COMMANDS = (
    "combat-lab",
    "warband-manager",
    "benchmark",
    "parity",
    "test-report",
    "verify",
    "audit",
    "validate",
    "tests",
    "combine-kb",
    "build-native",
    "doctor",
)


def test_umbrella_help_lists_every_command(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    for name in COMMANDS:
        assert name in output
    assert "mordheim-utils" in output


def test_bare_invocation_prints_help(capsys):
    assert main([]) == 0
    assert "mordheim-utils" in capsys.readouterr().out


def test_unknown_command_is_rejected(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["does-not-exist"])
    assert exc.value.code == 2
    assert "invalid choice" in capsys.readouterr().err


def test_benchmark_help_shows_the_lab_detailed_arguments(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["benchmark", "--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "--simulation-sizes" in output
    assert "--batch-sizes" in output
    assert "--require-improvement" in output
    assert "--min-improvement" in output


def test_audit_help_shows_the_review_status_filter(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["audit", "--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "--review-status" in output
    assert "needs_ruling" in output


def test_verify_help_shows_the_semantic_options(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["verify", "--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "--require-complete" in output
    assert "--inventory" in output


def test_combine_kb_help_mirrors_the_tool_arguments(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["combine-kb", "--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    assert "-o" in output
    assert "kb_path" in output


def test_tests_help_lists_scopes(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["tests", "--help"])
    assert exc.value.code == 0
    output = capsys.readouterr().out
    for scope in ("verification", "knowledge", "modular", "vectorized", "native"):
        assert scope in output


def test_test_scope_paths_are_non_empty_and_known():
    assert set(SCOPE_PATHS) >= {
        "all", "engines", "modular", "vectorized", "native", "campaign",
        "knowledge", "verification", "construction", "ui", "cli", "architecture",
    }
    for paths in SCOPE_PATHS.values():
        assert paths


def _record_run(monkeypatch):
    calls = []
    import mordheim_utils.cli as cli

    def fake_run(scope, pytest_args):
        cleaned = list(pytest_args)
        if cleaned and cleaned[0] == "--":
            cleaned.pop(0)
        calls.append((scope, cleaned))
        return 0

    monkeypatch.setattr(cli, "_run_pytest", fake_run)
    return calls


def test_tests_forwards_pytest_flags_without_double_dash(monkeypatch):
    calls = _record_run(monkeypatch)
    assert main(["tests", "--scope", "cli", "-q", "-p", "no:cacheprovider"]) == 0
    assert calls == [("cli", ["-q", "-p", "no:cacheprovider"])]


def test_tests_forwards_pytest_flags_after_double_dash(monkeypatch):
    calls = _record_run(monkeypatch)
    assert main(["tests", "--scope", "cli", "--", "-q", "-p", "no:cacheprovider"]) == 0
    assert calls == [("cli", ["-q", "-p", "no:cacheprovider"])]


def test_doctor_reports_environment(capsys):
    assert doctor_command(argparse.Namespace()) == 0
    output = capsys.readouterr().out
    assert "Python:" in output
    assert "optimized combat backends:" in output
    assert "modular reference engine:" in output
    assert "Combat Lab:" in output
    assert "Campaign Manager:" in output
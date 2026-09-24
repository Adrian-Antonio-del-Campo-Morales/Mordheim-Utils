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
    "combine-kb",
    "build-native",
    "doctor",
)

LAB_COMMANDS = ("benchmark", "parity", "coverage-gate", "verify", "calibrate")


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


@pytest.mark.parametrize("exit_code", [0, 1])
def test_check_presentation_preserves_gate_result(cli, monkeypatch, exit_code):
    calls = []
    monkeypatch.setattr(cli, "_run_in", lambda *args: calls.append(args) or exit_code)
    assert cli.main(["check-presentation"]) == exit_code
    assert calls == [(cli.WEB_APP, "npm", "run", "check:presentation")]


def test_check_presentation_help_and_invalid_args_do_not_run(cli, monkeypatch, capsys):
    monkeypatch.setattr(cli, "_run_in", lambda *args: pytest.fail("must not run"))
    assert cli.main(["check-presentation", "--help"]) == 0
    assert "gui-text-audit-deep" in capsys.readouterr().out
    assert cli.main(["check-presentation", "--unknown"]) == 2


def test_combat_lab_launches_the_lab_ui(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["combat-lab"]) == 0
    assert calls == [[sys.executable, "-m", "mordheim_combat_lab", "ui"]]


@pytest.mark.parametrize("name", ("combat-lab", "doctor", "build-native"))
def test_help_is_answered_without_running_anything(cli, monkeypatch, capsys, name):
    """`<command> --help` prints usage; it never launches an app or installs."""
    calls = _record_run(cli, monkeypatch)
    assert cli.main([name, "--help"]) == 0
    assert f"mordheim-utils.py {name}" in capsys.readouterr().out
    assert calls == []


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


def test_report_rules_forwards_to_the_audit_command(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["report", "rules", "--review-status", "needs_ruling",
                     "--output", "outputs/audit/questions"]) == 0
    assert calls == [[
        sys.executable, "-m", "mordheim_combat_lab", "audit",
        "--review-status", "needs_ruling", "--output", "outputs/audit/questions",
    ]]


def test_report_tests_forwards_to_the_test_report_command(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["report", "tests", "--json"]) == 0
    assert calls == [[sys.executable, "-m", "mordheim_combat_lab", "test-report", "--json"]]


def test_report_without_a_kind_prints_its_usage(cli, capsys):
    assert cli.main(["report"]) == 0
    output = capsys.readouterr().out
    assert "report <rules|tests>" in output
    assert "rules" in output and "tests" in output


def test_report_rejects_unknown_kinds(cli, capsys):
    assert cli.main(["report", "nope"]) == 2
    assert "unknown kind" in capsys.readouterr().err


def test_tests_forwards_pytest_flags_without_double_dash(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["tests", "--scope", "cli", "-q", "-p", "no:cacheprovider"]) == 0
    assert calls == [
        [sys.executable, "-m", "pytest", "tests/python/cli", "-q", "-p", "no:cacheprovider"]
    ]


def test_tests_forwards_pytest_flags_after_double_dash(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["tests", "--scope", "cli", "--", "-q", "-p", "no:cacheprovider"]) == 0
    assert calls == [[sys.executable, "-m", "pytest", "tests/python/cli", "-q", "-p", "no:cacheprovider"]]


def test_tests_default_scope_is_all(cli, monkeypatch):
    calls = _record_run(cli, monkeypatch)
    assert cli.main(["tests"]) == 0
    assert calls == [[sys.executable, "-m", "pytest", "tests"]]


def test_tests_rejects_unknown_scope(cli, capsys):
    assert cli.main(["tests", "--scope", "nope"]) == 2
    assert "unknown scope" in capsys.readouterr().err


def test_run_ci_executes_the_ci_validation_gates(cli, monkeypatch):
    calls = []

    def fake_run_in(directory, *argv):
        calls.append((directory, list(argv)))
        return 0

    staged = []
    monkeypatch.setattr(cli, "_run_in", fake_run_in)
    monkeypatch.setattr(cli, "_run_module", lambda *argv: calls.append((cli.REPO_ROOT, [sys.executable, "-m", *argv])) or 0)
    monkeypatch.setattr(cli, "_run", lambda *argv: calls.append((cli.REPO_ROOT, list(argv))) or 0)
    monkeypatch.setattr(cli, "_stage_knowledge_assets", lambda: staged.append(True))

    assert cli.main(["run-ci"]) == 0
    assert staged == [True]
    assert [command for _, command in calls] == [
        [sys.executable, str(cli.KNOWLEDGE_GENERATOR)],
        [sys.executable, str(cli.KNOWLEDGE_GENERATOR), "--check"],
        [sys.executable, "-m", "pytest", "tests/python/web", "tests/python/contracts", "tests/python/campaign",
         "tests/python/architecture", "tests/python/knowledge", "-q"],
        [sys.executable, str(cli.KNOWLEDGE_GENERATOR), "--check"],
        ["npm", "run", "typecheck"],
        ["npm", "test"],
        ["npx", "vitest", "run", "--pool=forks", "--maxWorkers=1",
         "--testTimeout=200000",
         "../../tests/web/features/campaign/knowledge-display-coverage.test.tsx",
         "../../tests/web/features/campaign/ui_i18n.test.ts",
         "../../tests/web/features/campaign/displayText.test.ts",
         "../../tests/web/features/campaign/KnowledgeHint.test.tsx"],
        ["npm", "run", "typecheck"],
        ["npm", "run", "lint"],
        ["npm", "test"],
        ["npm", "run", "build"],
        ["npx", "vitest", "run", "../../tests/web/architecture/boundaries.test.ts"],
    ]


def test_run_ci_stops_after_the_first_failure(cli, monkeypatch):
    monkeypatch.setattr(cli, "_run_in", lambda *_args: 1)
    monkeypatch.setattr(cli, "_stage_knowledge_assets", lambda: pytest.fail("must not stage"))

    assert cli.main(["run-ci"]) == 1


def test_run_in_uses_the_resolved_windows_command(cli, monkeypatch):
    calls = []
    monkeypatch.setattr(cli.shutil, "which", lambda command, path: "C:/Program Files/nodejs/npm.cmd")
    monkeypatch.setattr(cli.subprocess, "call", lambda argv, **kwargs: calls.append((argv, kwargs)) or 0)

    assert cli._run_in(cli.TYPESCRIPT_PACKAGE, "npm", "run", "typecheck") == 0
    assert calls[0][0] == ["C:/Program Files/nodejs/npm.cmd", "run", "typecheck"]


@pytest.mark.parametrize("flag", ("-h", "--help"))
def test_run_ci_help(cli, capsys, flag):
    assert cli.main(["run-ci", flag]) == 0
    assert "usage: python tools/mordheim-utils.py run-ci" in capsys.readouterr().out


def test_test_scope_paths_are_non_empty_and_known(cli):
    assert set(cli.SCOPE_PATHS) >= {
        "all", "engines", "modular", "vectorized", "native", "campaign",
        "knowledge", "verification", "construction", "ui", "cli", "architecture",
    }
    for paths in cli.SCOPE_PATHS.values():
        assert paths
        # Un scope que nombre una ruta que el checkout no tiene falla al colectar
        # con pytest: el mapa, y no quien lo invoca, es el que tiene que estar bien.
        for path in paths:
            assert (cli.REPO_ROOT / path).exists(), path


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
    assert "--deep-modular-simulations" in cli._command_candidates(["benchmark", "--deep-"])
    assert cli._command_candidates(["benchmark", "--backend", "nat"]) == ["native"]
    assert cli._command_candidates(["benchmark", "--backend", ""]) == ["modular", "numpy", "native"]


def test_completion_offers_the_report_kinds_and_their_options(cli):
    assert cli._command_candidates(["report", ""]) == ["rules", "tests"]
    assert cli._command_candidates(["report", "ru"]) == ["rules"]
    assert "--review-status" in cli._command_candidates(["report", "rules", ""])
    assert cli._command_candidates(["report", "tests", "--json"]) == []


def test_completion_covers_tests_scope_values(cli):
    assert cli._command_candidates(["tests", "--scope", "vec"]) == ["vectorized"]
    assert cli._command_candidates(["tests", "--scope", "det"]) == ["deterministic"]
    assert "all" in cli._command_candidates(["tests", "--scope", ""])
    assert cli._command_candidates(["tests", "--scope=ver"]) == ["--scope=verification"]


def test_completion_is_empty_for_unknown_commands(cli):
    assert cli._command_candidates(["does-not-exist", "--x"]) == []
    assert cli._command_candidates(["doctor", "--nope"]) == []

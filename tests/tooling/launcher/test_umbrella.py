import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CLI_SCRIPT = REPO_ROOT / "tools" / "mordheim-utils.py"

MODULAR_MECHANICS = "tests/engines/modular/mechanics"
MODULAR_RUNTIME = "tests/engines/modular/runtime"
EXPLICIT_PYTHON_FILE = "tests/engines/modular/mechanics/test_abdul_eye_pendant.py"
EXPLICIT_NODE_ID = (EXPLICIT_PYTHON_FILE
                    + "::test_printed_kit_compiles_and_worn_ward_uses_four_plus")
EXPLICIT_WEB_FILE = "tests/applications/warband_manager/features/campaign/displayText.test.ts"


@pytest.fixture()
def cli():
    spec = importlib.util.spec_from_file_location("mordheim_utils_launcher", CLI_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _record(cli, monkeypatch, name="_run"):
    calls = []

    def fake(*argv):
        calls.append(list(argv))
        return 0

    monkeypatch.setattr(cli, name, fake)
    return calls


def _record_workspaces(cli, monkeypatch):
    calls = []

    def fake(directory, *args):
        calls.append((directory, args))
        return 0

    monkeypatch.setattr(cli, "_run_in", fake)
    return calls


def test_no_arguments_prints_the_hierarchy(cli, capsys):
    assert cli.main([]) == 0
    output = capsys.readouterr().out
    for line in ("App launchers:", "app combat-lab", "app warband-manager",
                 "Tests:", "tests env", "tests combat-lab", "tests warband-manager",
                 "tests modular", "tests vectorized", "tests native", "tests kb",
                 "Performance:", "performance benchmark", "performance calibrate",
                 "Checks and reports:", "check verify", "check report", "check ci"):
        assert line in output
    assert "usage:" in output


def test_help_flag_matches_the_default_help(cli, capsys):
    assert cli.main(["--help"]) == 0
    assert "usage:" in capsys.readouterr().out


@pytest.mark.parametrize("group", ["app", "tests", "performance", "check"])
def test_group_help_is_available_without_actions(cli, capsys, group):
    assert cli.main([group]) == 0
    assert "usage:" in capsys.readouterr().out


@pytest.mark.parametrize("arguments", [["combat-lab"], ["does-not-exist"]])
def test_unknown_groups_are_rejected(cli, monkeypatch, arguments):
    calls = _record(cli, monkeypatch)
    assert cli.main(arguments) == 2
    assert calls == []


@pytest.mark.parametrize("arguments", [
    ["app", "does-not-exist"],
    ["performance", "does-not-exist"],
    ["check", "does-not-exist"],
    ["tests", "does-not-exist"],
])
def test_unknown_commands_are_rejected(cli, monkeypatch, arguments):
    calls = _record(cli, monkeypatch)
    assert cli.main(arguments) == 2
    assert calls == []


def test_app_combat_lab_opens_the_ui(cli, monkeypatch):
    calls = _record(cli, monkeypatch)
    assert cli.main(["app", "combat-lab"]) == 0
    assert calls == [[sys.executable, "-m", "mordheim_combat_lab", "ui"]]


def test_app_warband_manager_forwards_vite_arguments(cli, monkeypatch):
    calls = _record_workspaces(cli, monkeypatch)
    assert cli.main(["app", "warband-manager", "--port", "5199", "--strictPort"]) == 0
    assert calls == [(cli.WEB_APP, ("npm", "run", "dev", "--", "--port", "5199",
                                    "--strictPort"))]


@pytest.mark.parametrize("name", ["benchmark", "calibrate"])
def test_performance_commands_forward_to_the_lab(cli, monkeypatch, name):
    calls = _record(cli, monkeypatch)
    assert cli.main(["performance", name, "--pairs", "mini"]) == 0
    assert calls == [[sys.executable, "-m", "mordheim_combat_lab", name,
                      "--pairs", "mini"]]


@pytest.mark.parametrize("arguments, expected", [
    (["tests", "combat-lab"], ["tests/applications/combat_lab"]),
    (["tests", "modular"], [MODULAR_MECHANICS, MODULAR_RUNTIME]),
    (["tests", "modular", "mechanics"], [MODULAR_MECHANICS]),
    (["tests", "modular", "mechanics", "runtime"], [MODULAR_MECHANICS, MODULAR_RUNTIME]),
    (["tests", "warband-manager", "python"], ["tests/applications/warband_manager"]),
    (["tests", "vectorized", "mechanics"], ["tests/engines/vectorized/mechanics"]),
    (["tests", "vectorized", "runtime"], ["tests/engines/vectorized/runtime"]),
    (["tests", "native"], ["tests/engines/native"]),
    (["tests", "native", "runtime"], ["tests/engines/native/runtime"]),
    (["tests", "kb"], ["tests/knowledge"]),
    (["tests", "kb", "construction"], ["tests/construction"]),
    (["tests", "kb", "e2e"], ["tests/integration/e2e"]),
    (["tests", "parity"], ["tests/engines/parity/statistical", "tests/tooling/parity"]),
    (["tests", "parity", "statistical"], ["tests/engines/parity/statistical"]),
    (["tests", "parity", "tooling"], ["tests/tooling/parity"]),
    (["tests", "shared"], ["tests/engines/shared"]),
    (["tests", "tooling"], ["tests/tooling/architecture", "tests/tooling/launcher",
                            "tests/tooling/coverage"]),
    (["tests", "tooling", "launcher"], ["tests/tooling/launcher"]),
    (["tests", "tooling", "coverage"], ["tests/tooling/coverage"]),
])
def test_tests_select_the_mapped_pytest_paths(cli, monkeypatch, arguments, expected):
    calls = _record(cli, monkeypatch)
    assert cli.main(arguments) == 0
    assert calls == [[sys.executable, "-m", "pytest", *expected]]


def test_runner_options_are_forwarded_verbatim(cli, monkeypatch):
    calls = _record(cli, monkeypatch)
    arguments = ["-n", "8", "--dist=load", "-q", "--tb=short", "-k", "leadership"]
    assert cli.main(["tests", "modular", "mechanics", *arguments]) == 0
    assert calls == [[sys.executable, "-m", "pytest", MODULAR_MECHANICS, *arguments]]


def test_double_dash_is_not_forwarded(cli, monkeypatch):
    calls = _record(cli, monkeypatch)
    assert cli.main(["tests", "kb", "e2e", "--", "-q"]) == 0
    assert calls == [[sys.executable, "-m", "pytest", "tests/integration/e2e", "-q"]]


def test_an_explicit_file_replaces_the_selection_paths(cli, monkeypatch):
    calls = _record(cli, monkeypatch)
    assert cli.main(["tests", "modular", "mechanics", EXPLICIT_PYTHON_FILE, "-q"]) == 0
    assert calls == [[sys.executable, "-m", "pytest", EXPLICIT_PYTHON_FILE, "-q"]]


def test_an_explicit_node_id_replaces_the_selection_paths(cli, monkeypatch):
    calls = _record(cli, monkeypatch)
    assert cli.main(["tests", "modular", "mechanics", EXPLICIT_NODE_ID, "-q"]) == 0
    assert calls == [[sys.executable, "-m", "pytest", EXPLICIT_NODE_ID, "-q"]]


def test_an_unknown_positional_does_not_launch_pytest(cli, monkeypatch):
    calls = _record(cli, monkeypatch)
    assert cli.main(["tests", "modular", "mechanjcs"]) == 2
    assert calls == []


def test_warband_manager_requires_a_language(cli, monkeypatch, capsys):
    calls = _record(cli, monkeypatch)
    assert cli.main(["tests", "warband-manager"]) == 0
    output = capsys.readouterr().out
    assert "python" in output and "web" in output
    assert calls == []


def test_warband_manager_rejects_options_without_a_language(cli, monkeypatch):
    calls = _record(cli, monkeypatch)
    assert cli.main(["tests", "warband-manager", "-q"]) == 2
    assert calls == []


def test_warband_manager_web_runs_both_vitest_workspaces(cli, monkeypatch):
    calls = _record_workspaces(cli, monkeypatch)
    assert cli.main(["tests", "warband-manager", "web", "--maxWorkers=8"]) == 0
    assert [directory for directory, _ in calls] == [cli.TYPESCRIPT_PACKAGE, cli.WEB_APP]
    assert calls[0][1] == ("npm", "test", "--", "--maxWorkers=8")


def test_tooling_web_selects_the_architecture_project(cli, monkeypatch):
    calls = _record_workspaces(cli, monkeypatch)
    assert cli.main(["tests", "tooling", "web", "--maxWorkers=8"]) == 0
    assert calls[0][1] == ("npm", "test", "--", "--project", "architecture",
                           "--maxWorkers=8")


def test_an_explicit_vitest_file_passes_where_it_does_not_match(cli, monkeypatch):
    calls = _record_workspaces(cli, monkeypatch)
    assert cli.main(["tests", "warband-manager", "web", EXPLICIT_WEB_FILE,
                     "--maxWorkers=8"]) == 0
    expected = ("npm", "test", "--", str(REPO_ROOT / EXPLICIT_WEB_FILE),
                "--maxWorkers=8", "--passWithNoTests")
    assert calls == [(cli.TYPESCRIPT_PACKAGE, expected), (cli.WEB_APP, expected)]


def test_the_knowledge_subsection_is_not_duplicated(cli, monkeypatch):
    calls = _record(cli, monkeypatch)
    assert cli.main(["tests", "kb", "knowledge"]) == 2
    assert calls == []


def test_section_help_keeps_the_bare_selection_serial(cli, capsys):
    assert cli.main(["tests", "modular", "--help"]) == 0
    output = capsys.readouterr().out
    assert "tests modular -q" in output
    assert "tests modular mechanics -n 8 --dist=load -q" in output


def test_subsection_help_has_its_own_selection(cli, capsys):
    assert cli.main(["tests", "modular", "mechanics", "--help"]) == 0
    output = capsys.readouterr().out
    assert "tests modular mechanics [options]" in output
    assert MODULAR_MECHANICS in output
    assert "--collect-only" in output
    assert MODULAR_RUNTIME not in output


def test_web_subsection_help_shows_vitest_examples(cli, capsys):
    assert cli.main(["tests", "warband-manager", "web", "--help"]) == 0
    output = capsys.readouterr().out
    assert "Vitest" in output
    assert "--maxWorkers=8" in output
    assert "--collect-only" not in output


def test_listing_a_web_selection_skips_python_files(cli, monkeypatch, capsys):
    calls = _record(cli, monkeypatch)
    assert cli.main(["tests", "warband-manager", "web", "--list"]) == 0
    output = capsys.readouterr().out
    assert EXPLICIT_WEB_FILE in output
    assert ".py" not in output
    assert calls == []


def test_listing_a_python_selection_skips_web_files(cli, monkeypatch, capsys):
    calls = _record(cli, monkeypatch)
    assert cli.main(["tests", "warband-manager", "python", "--list"]) == 0
    output = capsys.readouterr().out
    assert EXPLICIT_WEB_FILE not in output
    assert ".py" in output
    assert calls == []


def test_listing_diagnostics_reports_no_files(cli, monkeypatch, capsys):
    calls = _record(cli, monkeypatch)
    assert cli.main(["tests", "env", "--list"]) == 0
    assert "no test files" in capsys.readouterr().out
    assert calls == []


def test_listing_a_selection_does_not_import_or_run(cli, monkeypatch, capsys):
    calls = _record(cli, monkeypatch)
    assert cli.main(["tests", "modular", "mechanics", "--list"]) == 0
    output = capsys.readouterr().out
    assert EXPLICIT_PYTHON_FILE in output
    assert calls == []


def test_listing_every_test_file_does_not_import_or_run(cli, monkeypatch, capsys):
    calls = _record(cli, monkeypatch)
    assert cli.main(["tests", "--list"]) == 0
    output = capsys.readouterr().out
    assert EXPLICIT_PYTHON_FILE in output
    assert EXPLICIT_WEB_FILE in output
    assert calls == []


def test_collection_is_forwarded_separately_from_listing(cli, monkeypatch):
    calls = _record(cli, monkeypatch)
    assert cli.main(["tests", "modular", "mechanics", "--collect-only", "-q"]) == 0
    assert calls == [[sys.executable, "-m", "pytest", MODULAR_MECHANICS,
                      "--collect-only", "-q"]]


def test_env_runs_diagnostics_without_a_test_suite(cli, monkeypatch):
    calls = _record(cli, monkeypatch)
    seen = []
    monkeypatch.setattr(cli, "diagnostics_command", lambda: seen.append(True) or 0)
    assert cli.main(["tests", "env"]) == 0
    assert seen == [True]
    assert calls == []


def test_env_rejects_runner_options(cli, monkeypatch):
    monkeypatch.setattr(cli, "diagnostics_command", lambda: 0)
    assert cli.main(["tests", "env", "-q"]) == 2


@pytest.mark.parametrize("arguments, module, forwarded", [
    (["check", "verify", "--json"], "verify", ["--json"]),
    (["check", "parity", "--profile", "quick"], "parity", ["--profile", "quick"]),
    (["check", "coverage", "--json"], "coverage-gate", ["--json"]),
])
def test_check_lab_commands_forward_to_the_lab(cli, monkeypatch, arguments, module,
                                               forwarded):
    calls = _record(cli, monkeypatch)
    assert cli.main(arguments) == 0
    assert calls == [[sys.executable, "-m", "mordheim_combat_lab", module, *forwarded]]


@pytest.mark.parametrize("kind, command", [("rules", "audit"),
                                           ("tests", "test-report")])
def test_check_report_routes_to_the_generator(cli, monkeypatch, kind, command):
    calls = _record(cli, monkeypatch)
    assert cli.main(["check", "report", kind, "--output", "outputs"]) == 0
    assert calls == [[sys.executable, "-m", "mordheim_combat_lab", command,
                      "--output", "outputs"]]


def test_check_report_rejects_unknown_kinds(cli, monkeypatch):
    calls = _record(cli, monkeypatch)
    assert cli.main(["check", "report", "everything"]) == 2
    assert calls == []


def test_check_presentation_runs_the_web_gate(cli, monkeypatch):
    calls = _record_workspaces(cli, monkeypatch)
    assert cli.main(["check", "presentation"]) == 0
    assert calls == [(cli.WEB_APP, ("npm", "run", "check:presentation"))]


def test_check_ci_runs_the_local_gates(cli, monkeypatch):
    seen = []
    monkeypatch.setattr(cli, "run_ci_command", lambda args: seen.append(args) or 0)
    assert cli.main(["check", "ci"]) == 0
    assert seen == [[]]


@pytest.mark.parametrize("arguments", [
    ["tests", "modular", "--help"],
    ["app", "combat-lab", "--help"],
    ["check", "verify", "--help"],
    ["performance", "benchmark", "--help"],
])
def test_each_subsection_has_its_own_help(cli, capsys, arguments):
    assert cli.main(arguments) == 0
    assert "usage:" in capsys.readouterr().out

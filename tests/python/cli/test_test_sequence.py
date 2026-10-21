"""Exercise ordering and failure control with tiny synthetic tests, not engines."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest

pytestmark = pytest.mark.test_infrastructure
ROOT = Path(__file__).resolve().parents[3]
PLUGIN = "tools.verification.test_sequence"
SOURCE = '''\
from pathlib import Path
import pytest

def record(value):
    with Path("trace").open("a") as stream:
        stream.write(value + "\\n")

@pytest.mark.operator
def test_consumer():
    record("operator")

@pytest.mark.compilation
def test_producer():
    record("compilation")
    assert False, "broken producer"
'''


def run_selection(tmp_path, *args, source=SOURCE):
    (tmp_path / "test_subject.py").write_text(source, encoding="utf-8")
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n compilation: producer\n operator: consumer\n"
        " rule_behavior: rule\n", encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(
        [str(ROOT), os.environ.get("PYTHONPATH", "")]))
    # Keep local pytest defaults/plugins from changing the synthetic experiment.
    env.pop("PYTEST_ADDOPTS", None)
    env.pop("PYTEST_PLUGINS", None)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-p", PLUGIN, "-q", *args],
        cwd=tmp_path, env=env, text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)


def test_broken_producer_stops_before_earlier_collected_consumer(tmp_path):
    result = run_selection(tmp_path, "-x")
    assert result.returncode == 1, result.stdout
    assert (tmp_path / "trace").read_text().splitlines() == ["compilation"]
    assert "operator: 1 not-run" in result.stdout


@pytest.mark.parametrize("flags", [(), ("--sequence-keep-going",)])
def test_diagnostic_mode_continues_without_turning_failure_into_success(tmp_path, flags):
    result = run_selection(tmp_path, *flags)
    assert result.returncode == 1, result.stdout
    assert (tmp_path / "trace").read_text().splitlines() == ["compilation", "operator"]


def test_plan_obeys_marker_selection_and_executes_no_test_body(tmp_path):
    result = run_selection(tmp_path, "--step", "3", "--sequence-plan", "-m", "compilation")
    assert result.returncode == 0, result.stdout
    assert "compilation: 1" in result.stdout
    assert "operator: 1" not in result.stdout
    assert not (tmp_path / "trace").exists()


def test_one_phase_does_not_execute_earlier_or_later_categories(tmp_path):
    result = run_selection(tmp_path, "--step", "4", source=SOURCE + '''
@pytest.mark.rule_behavior
def test_rule():
    record("rule")
''')
    assert result.returncode == 0, result.stdout
    assert (tmp_path / "trace").read_text().splitlines() == ["rule"]
    assert "Only step 4" in result.stdout


def test_resume_omits_prerequisites_explicitly(tmp_path):
    result = run_selection(tmp_path, "--sequence-from", "operator")
    assert result.returncode == 0, result.stdout
    assert (tmp_path / "trace").read_text().splitlines() == ["operator"]
    assert "Earlier stages omitted explicitly" in result.stdout


def test_unclassified_test_blocks_execution(tmp_path):
    result = run_selection(tmp_path, source="def test_unclassified():\n    assert False\n")
    assert result.returncode == 4, result.stdout
    assert "exactly one primary category" in result.stdout
    assert not (tmp_path / "trace").exists()


def test_native_compilation_waits_for_selected_oracle_behavior(tmp_path):
    backend = tmp_path / "tests/python/combat/native"
    backend.mkdir(parents=True)
    (backend / "test_backend.py").write_text(
        'from pathlib import Path\nimport pytest\n@pytest.mark.compilation\n'
        'def test_backend():\n    assert Path("trace").read_text() == "rule\\n"\n',
        encoding="utf-8")
    (tmp_path / "test_parameters.py").write_text(
        'from pathlib import Path\nimport pytest\n@pytest.mark.operator\n'
        '@pytest.mark.parametrize("backend", ["native", "modular"])\n'
        'def test_parameter(backend):\n'
        '    with Path("trace").open("a") as stream:\n'
        '        stream.write(backend + "\\n")\n', encoding="utf-8")
    result = run_selection(tmp_path, source=(
        'from pathlib import Path\nimport pytest\n@pytest.mark.rule_behavior\n'
        'def test_rule():\n    Path("trace").write_text("rule\\n")\n'))
    assert result.returncode == 0, result.stdout
    assert result.stdout.index("rule_behavior: 1") < result.stdout.index("optimized/compilation: 1")
    assert (tmp_path / "trace").read_text() == "rule\nnative\n"


def test_launcher_reuses_scope_and_forwards_runner_options(monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("sequence_launcher", ROOT / "tools/mordheim-utils.py")
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    calls = []
    monkeypatch.setattr(cli, "_run", lambda *args: calls.append(args) or 0)
    assert cli.main(["test-sequence", "--scope", "construction", "--sequence-plan", "-q"]) == 0
    assert calls == [(sys.executable, "-m", "pytest", "-p", PLUGIN,
                      "tests/python/construction", "--sequence-plan", "-q")]
    calls.clear()
    assert cli.main(["test-sequence", "--help"]) == 0
    help_text = capsys.readouterr().out
    assert "--scope NAME" in help_text
    assert "--sequence-plan" in help_text
    assert "Python only" in help_text
    assert not calls  # Help must not start pytest, import cases or execute tests.
    assert cli.main(["test-sequence", "--", "--help"]) == 0
    assert calls == [(sys.executable, "-m", "pytest", "-p", PLUGIN, "tests", "--help")]
    calls.clear()
    assert cli.main(["test-sequence", "-step1", "--scope", "knowledge"]) == 0
    assert calls == [(sys.executable, "-m", "pytest", "-p", PLUGIN,
                      "tests/python/knowledge", "tests/specs", "--step=1")]
    calls.clear()
    assert cli.main(["test-sequence", "--steps"]) == 0
    assert calls == [(sys.executable, "-m", PLUGIN, "--steps")]
    calls.clear()
    assert cli.main(["test-sequence", "-step1", "--scope", "knowledge", "--workers=4"]) == 0
    assert calls == [(sys.executable, "-m", PLUGIN, "--workers", "4", "--",
                      "tests/python/knowledge", "tests/specs", "--step=1")]
    calls.clear()
    assert cli.main(["test-sequence", "--workers", "0"]) == 2
    assert not calls

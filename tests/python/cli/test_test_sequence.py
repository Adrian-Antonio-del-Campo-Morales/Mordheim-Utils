"""Exercise ordering and failure control with tiny synthetic tests, not engines."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys

import pytest

pytestmark = pytest.mark.phase0_preflight
ROOT = Path(__file__).resolve().parents[3]
PLUGIN = "tools.verification.test_sequence"


@pytest.mark.parametrize("arguments, expected", [
    (["--steps"], 0),
    (["--scope", "nonexistent"], 2),
])
def test_output_report_preserves_console_and_exit_status(tmp_path, arguments, expected):
    report = tmp_path / "report directory" / "tests.txt"
    report.parent.mkdir()
    report.write_text("previous report", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools/mordheim-utils.py"), "test-sequence",
         *arguments, "--output", str(report)],
        capture_output=True, text=True, encoding="utf-8", timeout=30,
        env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert result.returncode == expected, result.stdout + result.stderr
    assert report.read_text(encoding="utf-8") == result.stdout
    assert result.stdout and "previous report" not in result.stdout


SOURCE = '''\
from pathlib import Path
import pytest

def record(value):
    with Path("trace").open("a") as stream:
        stream.write(value + "\\n")

@pytest.mark.phase4_modular
def test_consumer():
    record("modular")

@pytest.mark.phase3_rules
def test_producer():
    record("rules")
    assert False, "broken producer"
'''


def run_selection(tmp_path, *args, source=SOURCE):
    (tmp_path / "test_subject.py").write_text(source, encoding="utf-8")
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n phase2_construction: construction\n"
        " phase3_rules: rule\n phase4_modular: modular\n"
        " phase5_vectorized: vectorized\n phase6_native: native\n",
        encoding="utf-8")
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
    assert (tmp_path / "trace").read_text().splitlines() == ["rules"]
    assert "phase4_modular: 1 not-run" in result.stdout


@pytest.mark.parametrize("flags", [(), ("--sequence-keep-going",)])
def test_diagnostic_mode_continues_without_turning_failure_into_success(tmp_path, flags):
    result = run_selection(tmp_path, *flags)
    assert result.returncode == 1, result.stdout
    assert (tmp_path / "trace").read_text().splitlines() == ["rules", "modular"]


def test_plan_obeys_marker_selection_and_executes_no_test_body(tmp_path):
    result = run_selection(tmp_path, "--step", "3", "--sequence-plan", "-m", "phase3_rules")
    assert result.returncode == 0, result.stdout
    assert "phase3_rules: 1" in result.stdout
    assert "phase4_modular: 1" not in result.stdout
    assert not (tmp_path / "trace").exists()


def test_one_phase_does_not_execute_earlier_or_later_categories(tmp_path):
    result = run_selection(tmp_path, "--step", "4", source=SOURCE + '''
@pytest.mark.phase2_construction
def test_construction():
    record("construction")
''')
    assert result.returncode == 0, result.stdout
    assert (tmp_path / "trace").read_text().splitlines() == ["modular"]
    assert "Only phase 4" in result.stdout


def test_resume_omits_prerequisites_explicitly(tmp_path):
    result = run_selection(tmp_path, "--sequence-from", "phase4_modular")
    assert result.returncode == 0, result.stdout
    assert (tmp_path / "trace").read_text().splitlines() == ["modular"]
    assert "Earlier phases omitted explicitly" in result.stdout


def test_unclassified_test_blocks_execution(tmp_path):
    result = run_selection(tmp_path, source="def test_unclassified():\n    assert False\n")
    assert result.returncode == 4, result.stdout
    assert "exactly one phase category" in result.stdout
    assert not (tmp_path / "trace").exists()


def test_backend_items_follow_their_own_explicit_phase(tmp_path):
    """A parametrized item is ordered by the backend it actually executes."""
    backend = tmp_path / "tests/python/combat/native"
    backend.mkdir(parents=True)
    (backend / "test_backend.py").write_text(
        'from pathlib import Path\nimport pytest\n@pytest.mark.phase6_native\n'
        'def test_backend():\n    assert Path("trace").read_text().startswith("rules\\n")'
        '\n    assert "numpy" in Path("trace").read_text()\n',
        encoding="utf-8")
    (tmp_path / "test_parameters.py").write_text(
        'from pathlib import Path\nimport pytest\n'
        '@pytest.mark.parametrize("backend", [\n'
        '    pytest.param("numpy", marks=pytest.mark.phase5_vectorized),\n'
        '    pytest.param("native", marks=pytest.mark.phase6_native),\n'
        '])\n'
        'def test_parameter(backend):\n'
        '    with Path("trace").open("a") as stream:\n'
        '        stream.write(backend + "\\n")\n', encoding="utf-8")
    result = run_selection(tmp_path, source=(
        'from pathlib import Path\nimport pytest\n@pytest.mark.phase3_rules\n'
        'def test_rule():\n    Path("trace").write_text("rules\\n")\n'))
    assert result.returncode == 0, result.stdout
    trace = (tmp_path / "trace").read_text().splitlines()
    assert trace[0] == "rules" and "numpy" in trace
    assert result.stdout.index("phase3_rules: 1") < result.stdout.index("phase5_vectorized: 1")
    assert result.stdout.index("phase5_vectorized: 1") < result.stdout.index("phase6_native: 2")


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
    assert cli.main(["test-sequence", "-step0", "--scope", "knowledge", "--workers=4"]) == 0
    assert calls == [(sys.executable, "-m", PLUGIN, "--workers", "4", "--",
                      "tests/python/knowledge", "tests/specs", "--step=0")]
    calls.clear()
    assert cli.main(["test-sequence", "--workers", "0"]) == 2
    assert not calls

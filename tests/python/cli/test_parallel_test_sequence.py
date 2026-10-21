"""Parallel phase barriers and result handling, without production simulations."""
import os
from pathlib import Path

import pytest

from tools.verification import test_sequence as sequence

pytestmark = pytest.mark.test_infrastructure
ROOT = Path(__file__).resolve().parents[3]


@pytest.mark.parametrize("fail", [False, True])
def test_real_workers_finish_before_next_phase_and_preserve_failure(tmp_path, monkeypatch, capfd, fail):
    (tmp_path / "pytest.ini").write_text(
        "[pytest]\nmarkers =\n data_contract: contract\n eligibility: decision\n", encoding="utf-8")
    for own, peer in (("left", "right"), ("right", "left")):
        (tmp_path / f"test_{own}.py").write_text(f'''
import os, time
from pathlib import Path
import pytest

@pytest.mark.data_contract
def test_worker():
    Path("{own}.started").write_text(str(os.getpid()))
    deadline = time.monotonic() + 10
    while not Path("{peer}.started").exists() and time.monotonic() < deadline:
        time.sleep(.02)
    assert Path("{peer}.started").exists(), "the files were not run concurrently"
    assert Path("{peer}.started").read_text() != str(os.getpid())
    Path("{own}.done").write_text("done")
    assert not {fail and own == "right"!r}, "intentional contract failure"
''', encoding="utf-8")
    (tmp_path / "test_consumer.py").write_text('''
from pathlib import Path
import pytest

@pytest.mark.eligibility
def test_next_phase():
    assert Path("left.done").exists() and Path("right.done").exists()
    Path("consumer.done").write_text("done")
''', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join([str(ROOT), os.environ.get("PYTHONPATH", "")]))
    monkeypatch.setenv("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
    monkeypatch.delenv("PYTEST_ADDOPTS", raising=False)
    monkeypatch.delenv("PYTEST_PLUGINS", raising=False)
    # Two actual phases are enough to prove the barrier; no empty-process runs.
    monkeypatch.setattr(sequence, "STEPS", sequence.STEPS[:2])
    assert sequence.run_parallel(2, ["-q"]) == int(fail)
    assert (tmp_path / "consumer.done").exists()
    output = capfd.readouterr().out
    assert "Phase results" in output
    assert "step 2: passed" in output
    assert "2 passed" in output if not fail else "1 failed" in output


@pytest.mark.parametrize("codes,args,expected,calls", [
    ([1, 0, 5], [], 1, 3),
    ([1], ["-x"], 1, 1),
    ([5, 5, 5], [], 5, 3),
    ([4], [], 4, 1),
])
def test_phase_results_continue_or_stop_as_requested(monkeypatch, codes, args, expected, calls):
    invoked = []
    returns = iter(codes)
    monkeypatch.setattr(sequence, "STEPS", sequence.STEPS[:3])
    def run(argv):
        invoked.append(argv)
        return next(returns)
    monkeypatch.setattr(sequence.subprocess, "call", run)
    assert sequence.run_parallel(2, args) == expected
    assert len(invoked) == calls
    assert [argv[-1] for argv in invoked] == [str(n) for n in range(1, calls + 1)]


def test_parallel_plan_is_one_serial_collection_without_xdist_requirement(monkeypatch):
    invoked = []
    monkeypatch.setattr(sequence.importlib.util, "find_spec", lambda name: None)
    monkeypatch.setattr(sequence.subprocess, "call", lambda argv: invoked.append(argv) or 0)
    assert sequence.run_parallel(4, ["--sequence-plan", "--step", "3", "-q"]) == 0
    assert len(invoked) == 1
    assert "-n" not in invoked[0] and "xdist" not in invoked[0]
    assert invoked[0][-2:] == ["--step", "3"]

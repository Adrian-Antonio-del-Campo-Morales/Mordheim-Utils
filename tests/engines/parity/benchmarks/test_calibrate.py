"""external.test_calibration: the machine calibration command.

The sweep is exercised end to end with tiny sizes (mini pair set, two
candidate batches, one worker count) so the suite pays a few seconds, not
the production ~8-10 minutes.  The pairs come from the frozen precompiled
corpus: the sweep never reads the knowledge base or compiles a fighter.
"""
from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from mordheim_combat_lab.application.settings import (
    CALIBRATION_SCHEMA,
    apply_calibration,
    measured_pool_speedups,
)
from mordheim_combat_lab.cli import calibration
from mordheim_combat_lab.cli.scenarios import deep_test_scenarios
from tools.verification.compiled_cases import load_cases

CORPUS = Path(__file__).resolve().parents[2] / "fixtures" / "compiled-cases.json"


@lru_cache(maxsize=1)
def _cases():
    return load_cases(CORPUS)


def _fixture_pairs(pair_set: str):
    """The ``calibration._pairs`` rows, read from the precompiled corpus."""
    cases = _cases()
    return [
        (cases[f"parity/deep/{scenario.id}"].first,
         cases[f"parity/deep/{scenario.id}"].second,
         scenario.maximum_rounds or 50, scenario.id)
        for scenario in deep_test_scenarios(pair_set)
    ]


# Most cases prove the calibration command's flow (sweep, evidence curve,
# installation); the two that only assert the files written or removed carry
# their own persistence marker.


@pytest.fixture(autouse=True)
def _reference_defaults():
    """No measured profile may leak into the rest of the session."""
    apply_calibration(None)
    yield
    apply_calibration(None)


@pytest.fixture(scope="module")
def payload():
    # 40k pooled samples keep every candidate measurable: numpy 40k/2 = 20k
    # over a 10k batch is two batches, so two workers really split the plan.
    return calibration.run_calibration(
        "mini", seed=3, sequential_samples=20_000, pooled_samples=40_000,
        sequential_batches={"native": (5_000, 10_000), "numpy": (10_000,)},
        pooled_batches={"native": (5_000,), "numpy": (10_000,)},
        worker_candidates={"native": (2,), "numpy": (2,)},
        spawn_repetitions=1, log=lambda *_args: None,
        pair_source=_fixture_pairs,
    )


@pytest.mark.phase7_warband
def test_sweep_reports_winners_inside_the_candidates(payload):
    assert payload["schema"] == CALIBRATION_SCHEMA
    assert payload["method"]["pair_sets"]["native"] == "mini"
    assert payload["elapsed_seconds"] >= 0
    assert set(payload["batch_sizes"]) <= {"native", "numpy"}
    for backend in payload["batch_sizes"]:
        assert payload["batch_sizes"][backend] in (5_000, 10_000)
        assert payload["pooled_batch_sizes"][backend] in (5_000, 10_000)
        assert payload["pool_workers"][backend] == 2
        assert payload["spawn_seconds"][backend] > 0
        # Unsupported modular-only duels are disclosed, never measured as if
        # the optimized engines implemented them.
        measured = set(payload["method"]["pair_ids"][backend])
        excluded = payload["method"]["excluded_pairs"][backend]
        requested = {row[3] for row in _fixture_pairs("mini")}
        assert measured
        assert measured.isdisjoint(excluded)
        assert measured | set(excluded) == requested
        assert all(excluded.values())
        for first, second, _, pair_id in _fixture_pairs("mini"):
            if pair_id in measured:
                calibration.require_optimized_support(first, second)
        evidence = payload["evidence"][backend]
        assert evidence["sequential_batch"]["scores"]
        assert evidence["pooled_workers"]["seconds"]
        assert len(evidence["sequential_batch"]["seconds"]["10000"]) == len(
            payload["method"]["pair_ids"][backend])


@pytest.mark.phase7_warband
def test_sweep_derives_a_pool_speedup_curve_from_its_own_evidence(payload):
    curves = measured_pool_speedups(payload)

    assert set(curves) == set(payload["evidence"])
    for backend, points in curves.items():
        assert points, backend
        assert all(segments >= 2 and speedup >= 1.0
                   for segments, speedup in points.items())


@pytest.mark.phase7_warband
def test_installed_profile_is_the_applied_one(payload, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(calibration, "run_calibration", lambda *_args, **_kwargs: payload)
    args = SimpleNamespace(pairs="mini", seed=3, sample_size=20_000,
                           pool_sample_size=20_000, output=None, json=False, reset=False)

    assert calibration.calibration_command(args) == 0

    installed = tmp_path / "Mordheim Combat Lab" / "calibration.json"
    assert json.loads(installed.read_text(encoding="utf-8")) == payload
    output = capsys.readouterr().out
    assert "profile installed at" in output
    assert "applied sections: batch_sizes" in output
    assert "pool_speedups" in output
    assert "measured pool speedup curve" in output
    assert "restart the Combat Lab" in output


# Saved state: the installed profile and the optional report copy are files.
@pytest.mark.phase7_warband
def test_output_flag_writes_a_second_copy(payload, tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(calibration, "run_calibration", lambda *_args, **_kwargs: payload)
    report = tmp_path / "reports" / "calibration.json"
    report.parent.mkdir()
    args = SimpleNamespace(pairs="mini", seed=3, sample_size=20_000,
                           pool_sample_size=20_000, output=str(report), json=False, reset=False)

    assert calibration.calibration_command(args) == 0
    assert json.loads(report.read_text(encoding="utf-8"))["schema"] == CALIBRATION_SCHEMA
    assert (tmp_path / "Mordheim Combat Lab" / "calibration.json").exists()


@pytest.mark.phase7_warband
def test_reset_removes_the_installed_profile(payload, tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(calibration, "run_calibration", lambda *_args, **_kwargs: payload)
    calibration.calibration_command(
        SimpleNamespace(pairs="mini", seed=3, sample_size=20_000, pool_sample_size=20_000,
                        output=None, json=False, reset=False))

    assert calibration.calibration_command(SimpleNamespace(reset=True)) == 0
    assert not (tmp_path / "Mordheim Combat Lab" / "calibration.json").exists()
    assert calibration.calibration_command(SimpleNamespace(reset=True)) == 0

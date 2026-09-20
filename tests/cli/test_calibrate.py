"""external.test_calibration: the machine calibration command.

The sweep is exercised end to end with tiny sizes (mini pair set, two
candidate batches, one worker count) so the suite pays a few seconds, not
the production ~8-10 minutes.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from mordheim_combat_lab.application.settings import (
    CALIBRATION_SCHEMA,
    apply_calibration,
    measured_pool_speedups,
)
from mordheim_combat_lab.cli import calibration


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
    )


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
        evidence = payload["evidence"][backend]
        assert evidence["sequential_batch"]["scores"]
        assert evidence["pooled_workers"]["seconds"]
        assert len(evidence["sequential_batch"]["seconds"]["10000"]) == len(
            payload["method"]["pair_ids"][backend])


def test_sweep_derives_a_pool_speedup_curve_from_its_own_evidence(payload):
    curves = measured_pool_speedups(payload)

    assert set(curves) == set(payload["evidence"])
    for backend, points in curves.items():
        assert points, backend
        assert all(segments >= 2 and speedup >= 1.0
                   for segments, speedup in points.items())


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


def test_reset_removes_the_installed_profile(payload, tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setattr(calibration, "run_calibration", lambda *_args, **_kwargs: payload)
    calibration.calibration_command(
        SimpleNamespace(pairs="mini", seed=3, sample_size=20_000, pool_sample_size=20_000,
                        output=None, json=False, reset=False))

    assert calibration.calibration_command(SimpleNamespace(reset=True)) == 0
    assert not (tmp_path / "Mordheim Combat Lab" / "calibration.json").exists()
    assert calibration.calibration_command(SimpleNamespace(reset=True)) == 0

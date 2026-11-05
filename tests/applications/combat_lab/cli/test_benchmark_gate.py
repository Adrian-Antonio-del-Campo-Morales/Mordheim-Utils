"""Benchmark baseline gate, payload design/provenance and pooled report.

No engine runs here: results are built by hand and the provenance probe is
stubbed, so the checks exercise only the gate's bookkeeping.
"""
from __future__ import annotations

from dataclasses import asdict
import json

import pytest

from mordheim_combat_lab.application import settings
from mordheim_combat_lab.cli import benchmarking
from mordheim_combat_lab.cli.benchmarking import (
    BenchmarkResult,
    benchmark_payload,
    format_parallel_summary,
    gate_against_baseline,
    speedup_payload,
    write_report,
)

PROVENANCE = {
    "cpu_count": 12, "platform": "Linux-x", "machine": "x86_64",
    "python": "3.14.4", "numpy": "2.5.4",
    "engine_digests": {"numpy": "a" * 64, "native": "b" * 64},
    "native_build_sha256": "c" * 64,
    "revision": {"commit": "abc", "dirty": False, "dirty_paths": []},
    "imported_from": {}, "warnings": [],
}


@pytest.fixture(autouse=True)
def _stub_provenance(monkeypatch):
    monkeypatch.setattr(settings, "measurement_provenance",
                        lambda engines, emit=True: json.loads(json.dumps(PROVENANCE)))


def result(scenario, backend, rate):
    return BenchmarkResult(scenario, backend, 1_000, 500, 1, (1_000 / rate,),
                           1_000 / rate, float(rate))


def payload(results, unavailable=(), **overrides):
    options = dict(simulations=1_000, batch_size=500, seed=7, warmups=0, repeats=1,
                   processes=1, backends=("numpy", "native"))
    options.update(overrides)
    return benchmark_payload(results, unavailable, **options)


def roundtrip(document):
    return json.loads(json.dumps(document))


def test_payload_records_design_and_provenance(monkeypatch):
    sequential = payload([result("a", "numpy", 100)])
    assert sequential["configuration"] == {
        "simulations": 1_000, "batch_size": 500, "seed": 7, "warmups": 0,
        "repeats": 1, "processes": 1, "start_method": None,
        "backends": ["native", "numpy"],
    }
    assert sequential["provenance"]["cpu_count"] == 12
    monkeypatch.setattr(benchmarking, "_pool_start_method", lambda: "forkserver")
    pooled = payload([result("a", "numpy", 100)], processes=4)
    assert pooled["configuration"]["processes"] == 4
    assert pooled["configuration"]["start_method"] == "forkserver"
    # Without an explicit list, results + unavailable name the requested backends.
    derived = benchmark_payload(
        [result("a", "numpy", 100)], [{"backend": "native", "reason": "not compiled"}],
        simulations=1_000, batch_size=500, seed=7, warmups=0, repeats=1)
    assert derived["configuration"]["backends"] == ["native", "numpy"]


@pytest.mark.parametrize("field,value", [
    ("processes", 4), ("backends", ("numpy",)), ("seed", 8), ("batch_size", 250),
])
def test_design_differences_are_errors(field, value):
    baseline = roundtrip(payload([result("a", "numpy", 100)]))
    current = payload([result("a", "numpy", 100)], **{field: value})
    with pytest.raises(ValueError, match=field):
        gate_against_baseline(current, baseline, [result("a", "numpy", 100)])


def test_provenance_differences_warn_and_are_recorded_without_failing(capsys):
    baseline = roundtrip(payload([result("a", "numpy", 100), result("a", "native", 100)]))
    baseline["provenance"]["cpu_count"] = 32
    baseline["provenance"]["engine_digests"]["native"] = "d" * 64
    current_results = [result("a", "numpy", 120), result("a", "native", 101)]
    gate = gate_against_baseline(payload(current_results), baseline, current_results)
    assert gate.passed
    (warning,) = gate.provenance_warnings
    assert warning.startswith("PROVENANCE WARNING")
    assert "CPU count differs" in warning and "native engine sources differ" in warning
    assert "PROVENANCE WARNING" in capsys.readouterr().err
    assert roundtrip(asdict(gate))["provenance_warnings"] == [warning]


def test_old_baseline_without_new_fields_warns_and_still_gates():
    current_results = [result("a", "numpy", 120)]
    baseline = {
        "schema": benchmarking.BENCHMARK_SCHEMA,
        "configuration": {"simulations": 1_000, "batch_size": 500, "seed": 7,
                          "warmups": 0, "repeats": 1},
        "results": [asdict(result("a", "numpy", 100))],
    }
    gate = gate_against_baseline(
        payload(current_results, backends=("numpy",)), baseline, current_results)
    assert gate.passed
    unrecorded, unknown = gate.provenance_warnings
    assert "processes, start_method, backends" in unrecorded
    assert "records no provenance" in unknown


def test_baseline_result_without_current_result_fails_the_gate():
    baseline = roundtrip(payload([
        result("a", "numpy", 100), result("a", "native", 100),
        result("b", "native", 100), result("c", "numpy", 100),
        result("a", "modular", 1),
    ]))
    current_results = [result("a", "numpy", 200)]
    unavailable = [
        {"scenario": "a", "backend": "native", "reason": "RuntimeError: boom"},
        {"backend": "native", "reason": "native backend is not compiled"},
    ]
    gate = gate_against_baseline(
        payload(current_results, unavailable), baseline, current_results)
    assert not gate.passed and gate.improved
    # Modular baselines participate like the optimized ones.
    assert [(item.scenario, item.backend, item.reason) for item in gate.missing] == [
        ("a", "modular", "not measured in the current run"),
        ("a", "native", "RuntimeError: boom"),
        ("b", "native", "native backend is not compiled"),
        ("c", "numpy", "not measured in the current run"),
    ]
    assert gate.detail.startswith("4 baseline result(s) have no current measurement")


def test_modular_results_gate_like_the_optimized_ones():
    baseline = roundtrip(payload([result("a", "modular", 100)],
                                 backends=("modular",)))
    improved = [result("a", "modular", 120)]
    gate = gate_against_baseline(
        payload(improved, backends=("modular",)), baseline, improved)
    assert gate.passed and gate.improved
    (comparison,) = gate.comparisons
    assert comparison.backend == "modular" and comparison.status == "IMPROVED"
    regressed = [result("a", "modular", 80)]
    gate = gate_against_baseline(
        payload(regressed, backends=("modular",)), baseline, regressed)
    assert not gate.passed and gate.regressed


def test_markdown_report_lists_missing_results(tmp_path):
    baseline = roundtrip(payload([result("a", "numpy", 100), result("b", "numpy", 100)]))
    current_results = [result("a", "numpy", 200)]
    document = payload(current_results)
    document["comparison"] = asdict(gate_against_baseline(document, baseline, current_results))
    target = tmp_path / "report.md"
    write_report(target, document)
    text = target.read_text(encoding="utf-8")
    assert "## Gate: FAIL" in text
    assert "b/numpy: [MISSING] not measured in the current run" in text


def test_pooled_report_states_only_measured_figures():
    report = speedup_payload([("u1", 3.0), ("u2", 1.0), ("failed", 0.0)],
                             pool_wall=2.0, processes=4)
    assert report["rows"] == [{"unit": "u1", "worker_seconds": 3.0},
                              {"unit": "u2", "worker_seconds": 1.0}]
    assert report["engine_sample_seconds"] == 4.0
    assert report["sample_concurrency"] == 2.0
    assert "speedup" not in report  # it is a concurrency figure, not a speedup
    assert "not a speedup" in format_parallel_summary(report)
    assert speedup_payload([("u1", 0.0)], pool_wall=1.0, processes=2) is None

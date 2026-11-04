"""Run-fault, power, cache and provenance safeguards of the parity tooling.

Every engine call is stubbed: the oracle sampler, the candidate sampler and
the worker pool are replaced, so no modular, NumPy or native duel runs here.
"""
from concurrent.futures.process import BrokenProcessPool
from types import ModuleType, SimpleNamespace
import sys

import numpy as np
import pytest

import mordheim_combat
from mordheim_combat_lab.verification.parity import ParityCase, run_parity
from mordheim_combat_lab.verification.parity import _battery_runner as battery
from mordheim_combat_lab.verification.parity import _runner
from mordheim_combat_lab.verification.parity._report import (
    ParityReport,
    battery_failure_kind,
    battery_report_markdown,
    battery_report_payload,
    parity_report_markdown,
    parity_report_payload,
)
from mordheim_combat_lab.verification.parity._statistical import (
    MAX_DETECTABLE_DIFFERENCE,
    minimum_detectable_difference,
    six_sigma_tolerance,
    underpowered,
)


def observation(winner):
    winner = np.asarray(winner)
    zeros = np.zeros_like(winner)
    return SimpleNamespace(
        winner=winner, resolution_rounds=zeros, rounds=zeros,
        first_wounds=zeros, second_wounds=zeros,
        first_condition=zeros, second_condition=zeros,
    )


@pytest.fixture
def oracle(monkeypatch):
    """Stub the modular sampler; records every executed sample."""
    calls = []

    def reference(case, size, **options):
        calls.append((case.label, size, case.seed))
        return observation([0, 1] * (size // 2))

    monkeypatch.setattr(_runner, "_observed_reference", reference)
    return calls


def candidate_raising(monkeypatch, error):
    def sample(*args, **kwargs):
        raise error
    monkeypatch.setattr(_runner, "_candidate_sample", sample)


def observed(label="case", size=2, **options):
    return ParityCase(label, None, None, simulations=size, **options)


# -- task 4: candidate crashes and missing backends are failures --------------

@pytest.mark.parametrize("error", [TypeError("bad arg"), AttributeError("no attr")])
def test_a_candidate_crash_is_an_own_error(monkeypatch, oracle, error):
    candidate_raising(monkeypatch, error)
    row, = run_parity((observed(),), backends=("numpy",)).rows
    assert row.status == "DIVERGENCE"
    assert row.detail.startswith(f"DIVERGENCE:exception:{type(error).__name__}")
    assert battery_failure_kind(row.status, row.detail) == "error"


def test_a_missing_native_backend_fails_but_a_declined_plan_is_a_dependency(
        monkeypatch, oracle):
    candidate_raising(monkeypatch, _runner._NativeMissing(
        "native extension is not installed"))
    missing, = run_parity((observed(),), backends=("native",)).rows
    assert missing.detail.startswith("NOT_RUN:native-unavailable")
    assert battery_failure_kind(missing.status, missing.detail) == "error"

    candidate_raising(monkeypatch, _runner._NativeUnavailable(
        "native extension does not support this duel plan"))
    declined, = run_parity((observed(),), backends=("native",)).rows
    assert declined.detail.startswith("NOT_RUN:native-plan")
    assert battery_failure_kind(declined.status, declined.detail) == "dependency"


# -- task 5: a stale effect layout is a missing backend -----------------------

def fake_native(monkeypatch, **attributes):
    module = ModuleType("mordheim_combat._combat_native")
    module.__file__ = "/fake/_combat_native.so"
    for name, value in attributes.items():
        setattr(module, name, value)
    monkeypatch.setattr(mordheim_combat, "_combat_native", module, raising=False)
    monkeypatch.setitem(sys.modules, "mordheim_combat._combat_native", module)


def test_native_engine_rejects_a_stale_effect_layout(monkeypatch):
    from mordheim_combat.kernel import EFFECT_VALUE_FIELDS

    entry = dict(CONTEXT_VERSION=1, simulate_batch_observed=lambda *a, **k: None)
    fake_native(monkeypatch, N_EFFECT_FIELDS=len(EFFECT_VALUE_FIELDS) - 1, **entry)
    with pytest.raises(_runner._NativeMissing, match="effect layout is stale"):
        _runner._native_engine()
    fake_native(monkeypatch, N_EFFECT_FIELDS=len(EFFECT_VALUE_FIELDS), **entry)
    assert _runner._native_engine() is sys.modules["mordheim_combat._combat_native"]


# -- task 2: worker pool origin check ------------------------------------------

def test_worker_origin_check_refuses_another_engine_copy():
    expected = _runner._engine_origins(False)
    _runner._check_worker_origins(False, expected)  # same files: accepted
    wrong = {**expected, "mordheim_combat": "/elsewhere/mordheim_combat/__init__.py"}
    with pytest.raises(RuntimeError, match="different engine"):
        _runner._check_worker_origins(False, wrong)


def test_a_broken_pool_fails_the_run_instead_of_reporting_divergence(monkeypatch):
    created = []

    class Pool:
        def __init__(self, **options):
            created.append(options)

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def reference(case, size, **options):
        assert options["executor"] is not None
        raise BrokenProcessPool("a child process terminated abruptly")

    monkeypatch.setattr(_runner, "ProcessPoolExecutor", Pool)
    monkeypatch.setattr(_runner, "resolve_oracle_workers", lambda *args: 2)
    monkeypatch.setattr(_runner, "_observed_reference", reference)
    with pytest.raises(_runner.ParityPoolError, match="different engine"):
        run_parity((observed(),), backends=("numpy",), workers=2)
    options, = created
    assert options["initializer"] is _runner._check_worker_origins
    assert options["initargs"] == (False, _runner._engine_origins(False))


def test_the_cli_reports_a_broken_pool_as_a_failed_run(monkeypatch, capsys):
    from mordheim_combat_lab.cli import commands

    def broken(args):
        raise _runner.ParityPoolError("worker imported a different engine")

    monkeypatch.setattr(commands, "_parity_command", broken)
    assert commands.parity_command(SimpleNamespace()) == 2
    assert "Parity run error" in capsys.readouterr().err


# -- task 8: counts surface refuses context or decisions -----------------------

@pytest.mark.parametrize("extra", [{"context": object()}, {"decisions": object()}])
def test_counts_surface_refuses_context_or_decisions(oracle, extra):
    with pytest.raises(ValueError, match="candidate='observed'"):
        run_parity((observed(**extra),), backends=("numpy",), candidate="counts")
    assert oracle == []


# -- task 9: cache identity and timing -----------------------------------------

def test_cache_key_covers_settings_and_reports_the_original_time(monkeypatch, oracle):
    monkeypatch.setattr(
        _runner, "_candidate_sample",
        lambda *args, **kwargs: observation([1, -1]),
    )
    cache = {}
    first, = run_parity((observed(seed=1),), cache=cache).rows
    again, = run_parity((observed(seed=1),), cache=cache).rows
    assert len(oracle) == 1
    assert first.reference_cached is False and again.reference_cached is True
    assert again.modular_seconds == first.modular_seconds

    run_parity((observed(seed=2),), cache=cache)
    run_parity((observed(seed=1, maximum_rounds=7),), cache=cache)
    run_parity((observed(seed=1, context=SimpleNamespace(terrain="x")),), cache=cache)
    assert len(oracle) == 4
    cached = run_parity((observed(seed=1, context=SimpleNamespace(terrain="x")),),
                        cache=cache)
    assert len(oracle) == 4 and cached.modular_duels == 0


# -- task 3: statistical power --------------------------------------------------

def test_minimum_detectable_difference_is_the_worst_case_tolerance():
    assert minimum_detectable_difference(64) == six_sigma_tolerance(.5, .5, 64)
    assert minimum_detectable_difference(64) > 0.5
    assert MAX_DETECTABLE_DIFFERENCE == 0.05
    assert underpowered(64) and underpowered(7_199) and not underpowered(7_200)


def battery_case(identifier="a"):
    return SimpleNamespace(
        id=identifier, level="quick", variant="B06.1", seed=1,
        maximum_rounds=4, observables=("winner",),
    )


def passing_row(size, label="a"):
    return _runner.ParityRow(
        case=label, backend="numpy", maximum_rounds=4, simulations=size,
        status="PASS", executed=True, compared=True, approved=True,
    )


def test_a_small_passing_sample_is_underpowered_not_approved(monkeypatch):
    monkeypatch.setattr(battery, "required_variants", lambda profile: ("B06.1",))
    small, = battery.battery_results((battery_case(),), (passing_row(64),))
    assert small.status == "UNDERPOWERED" and small.approved is False
    assert small.compared is True and "0.5303" in small.detail
    assert battery_failure_kind(small.status, small.detail) is None

    report = battery.battery_report((small,), (battery_case(),), profile="quick")
    assert report.complete is False and report.accepted is False
    assert report.underpowered == ("a",)
    payload = battery_report_payload(
        report, profile="quick", backend="numpy", catalog_sha256="c",
        inventory_sha256="i", backends=("numpy",),
    )
    assert payload["coverage"]["underpowered"] == 1
    assert payload["coverage"]["approved"] == 0
    assert payload["cases"][0]["minimum_detectable_difference"] == pytest.approx(
        minimum_detectable_difference(64))
    assert payload["power"]["max_detectable_difference"] == MAX_DETECTABLE_DIFFERENCE
    markdown = battery_report_markdown(payload)
    assert "## Statistical power" in markdown and "| 64 | 0.5303 |" in markdown

    large, = battery.battery_results((battery_case(),), (passing_row(8_000),))
    assert large.status == "PASS" and large.approved is True
    assert battery.battery_report(
        (large,), (battery_case(),), profile="quick").complete is True


def run_battery_command(monkeypatch, row, *, require_complete):
    from mordheim_combat_lab.cli import commands
    from mordheim_combat_lab import provenance
    from mordheim_combat_lab.verification.parity import _battery_cases as catalog

    monkeypatch.setattr(catalog, "battery_cases", lambda profile: (battery_case(),))
    monkeypatch.setattr(battery, "required_variants", lambda profile: ("B06.1",))
    monkeypatch.setattr(
        battery, "prepare_cases",
        lambda cases, **options: ((observed("a"),), {}),
    )
    monkeypatch.setattr(
        _runner, "run_parity",
        lambda prepared, **options: _runner.ParityRun(rows=(row,)),
    )
    monkeypatch.setattr(provenance, "run_provenance", lambda root, engines, **k: {
        "revision": {"commit": "abc", "dirty": False}, "imported_from": {},
        "engine_digests": {name: "0" * 64 for name in engines},
        "native_build_sha256": None, "warnings": [],
    })
    args = SimpleNamespace(
        backend="numpy", rows=None, workers=1, output=None, json=False,
        require_complete=require_complete,
    )
    return commands._battery_command(args, "quick")


def test_battery_exit_codes_for_underpowered_and_missing_backends(monkeypatch, capsys):
    assert run_battery_command(monkeypatch, passing_row(64), require_complete=False) == 0
    out = capsys.readouterr().out
    assert "1 case(s) UNDERPOWERED" in out
    assert run_battery_command(monkeypatch, passing_row(64), require_complete=True) == 1
    assert run_battery_command(monkeypatch, passing_row(8_000), require_complete=True) == 0

    missing = _runner.ParityRow(
        case="a", backend="numpy", maximum_rounds=4, simulations=8_000,
        status="NOT_RUN", detail="NOT_RUN:native-unavailable: not installed",
    )
    assert run_battery_command(monkeypatch, missing, require_complete=False) == 1


# -- task 7: deep certificate records backends and fails on missing ones ------

def test_certificate_with_a_missing_requested_backend_is_incomplete():
    report = ParityReport(
        complete=True, obligations=(), verified=(), pending=(), divergences=(),
        exact_checks=("x",),
    )
    backends = {"requested": ["numpy", "native"], "available": ["numpy"],
                "certified": ["numpy"], "missing": ["native"]}
    workers = {"requested": "auto", "environment": None, "resolved": {"matrix:a": 4}}
    payload = parity_report_payload(
        report, backends=backends, oracle_workers=workers,
        provenance={"revision": {"commit": "abc", "dirty": True},
                    "engine_digests": {"modular": "0" * 64},
                    "native_build_sha256": None, "warnings": ["dirty tree"]},
    )
    assert payload["complete"] is False
    assert payload["backends"] == backends and payload["oracle_workers"] == workers
    markdown = parity_report_markdown(payload)
    assert "INCOMPLETE: requested backend(s) unavailable: native" in markdown
    assert "PROVENANCE WARNING:** dirty tree" in markdown

    present = parity_report_payload(report, backends={**backends, "missing": []})
    assert present["complete"] is True

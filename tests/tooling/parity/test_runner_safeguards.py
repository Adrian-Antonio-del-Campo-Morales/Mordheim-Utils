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
from mordheim_combat_lab.verification.parity import _runner
from mordheim_combat_lab.verification.parity._report import (
    ParityReport,
    parity_report_markdown,
    parity_report_payload,
    power_verdict,
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


def test_a_missing_native_backend_fails_but_a_declined_plan_is_a_dependency(
        monkeypatch, oracle):
    candidate_raising(monkeypatch, _runner._NativeMissing(
        "native extension is not installed"))
    missing, = run_parity((observed(),), backends=("native",)).rows
    assert missing.detail.startswith("NOT_RUN:native-unavailable")

    candidate_raising(monkeypatch, _runner._NativeUnavailable(
        "native extension does not support this duel plan"))
    declined, = run_parity((observed(),), backends=("native",)).rows
    assert declined.detail.startswith("NOT_RUN:native-plan")


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


def passing_row(size, label="a"):
    return _runner.ParityRow(
        case=label, backend="numpy", maximum_rounds=4, simulations=size,
        status="PASS", executed=True, compared=True, approved=True,
    )


def test_a_small_passing_sample_is_underpowered_not_approved():
    # Power is a property of the row, applied wherever rows are reported.
    status, approved, detail = power_verdict(passing_row(64))
    assert status == "UNDERPOWERED" and approved is False
    assert "0.5303" in detail and str(MAX_DETECTABLE_DIFFERENCE) in detail

    status, approved, _ = power_verdict(passing_row(8_000))
    assert status == "PASS" and approved is True


def run_parity_command(monkeypatch, row, *, require_complete):
    """``check parity --scenarios basic`` with the sampler answering ``row``."""
    from dataclasses import replace

    from mordheim_combat_lab.cli import commands
    from mordheim_combat_lab.verification import parity

    row = replace(row, case="scenario/basic")
    monkeypatch.setattr(parity, "run_parity",
                        lambda prepared, **options: _runner.ParityRun(rows=(row,)))
    argv = ["parity", "--scenarios", "basic", *(["--require-complete"] if require_complete else [])]
    return commands.parity_command(commands.build_parser().parse_args(argv))


def test_exit_codes_for_underpowered_rows_and_missing_backends(monkeypatch, capsys):
    # A pass too small to detect a 5-point shift is UNDERPOWERED: not a
    # failure, but not complete either.
    assert run_parity_command(monkeypatch, passing_row(64), require_complete=False) == 0
    assert "1 row(s) UNDERPOWERED" in capsys.readouterr().out
    assert run_parity_command(monkeypatch, passing_row(64), require_complete=True) == 1
    assert run_parity_command(monkeypatch, passing_row(8_000), require_complete=True) == 0

    missing = _runner.ParityRow(
        case="a", backend="numpy", maximum_rounds=4, simulations=8_000,
        status="NOT_RUN", detail="NOT_RUN:native-unavailable: not installed",
    )
    assert run_parity_command(monkeypatch, missing, require_complete=False) == 1


# -- task 7: deep certificate records backends and fails on missing ones ------

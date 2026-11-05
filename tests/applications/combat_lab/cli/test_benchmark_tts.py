"""Time-to-solution strategies: parsing, applicability and the modular split.

The parsing and applicability checks run no engine. The execution check runs
the modular oracle at a smoke size through every strategy family and requires
bit-for-bit equal totals, which is what lets the study double as a parity
gate.
"""
from __future__ import annotations

import pytest

from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
from mordheim_combat_lab.cli.benchmarking import parse_tts_strategies
from mordheim_combat_lab.cli.benchmarking import parse_tts_strategy
from mordheim_combat_lab.cli.benchmarking import run_tts_strategy
from mordheim_combat_lab.cli.benchmarking import tts_backend_parity
from mordheim_combat_lab.cli.benchmarking import tts_strategy_applies


def test_strategy_tokens_canonicalize_and_accept_chunk_counts():
    assert parse_tts_strategies(None) == ("sequential", "processes=4", "parallel=4")
    assert parse_tts_strategies("processes=1, parallel=2:8, sequential,parallel=02") == (
        "sequential", "parallel=2:8", "parallel=2")
    assert parse_tts_strategy("parallel=2:8") == ("parallel", 2, 8)
    assert parse_tts_strategy("processes=3") == ("processes", 3, None)
    assert parse_tts_strategy("sequential") == ("sequential", 1, None)


@pytest.mark.parametrize("value", [
    "threads=2", "processes=2:4", "parallel=x", "parallel=4:2", "parallel=2:",
])
def test_invalid_strategy_tokens_are_rejected(value):
    with pytest.raises(ValueError):
        parse_tts_strategies(value)


def test_strategy_applicability_per_engine():
    for backend in ("modular", "numpy", "native"):
        assert tts_strategy_applies("sequential", backend)
        assert tts_strategy_applies("processes=4", backend)
    assert tts_strategy_applies("parallel=4", "modular")
    assert tts_strategy_applies("parallel=4", "numpy")
    assert not tts_strategy_applies("parallel=4", "native")
    assert tts_strategy_applies("parallel=4:16", "modular")
    assert not tts_strategy_applies("parallel=4:16", "numpy")


def test_inapplicable_strategy_is_refused_before_running():
    with pytest.raises(ValueError, match="does not apply"):
        run_tts_strategy("parallel=2", benchmark_scenarios()[:1], simulations=1,
                         batch_size=1, seed=1, backend="native")


def test_modular_strategies_agree_bit_for_bit():
    scenarios = benchmark_scenarios()[:2]
    results = [
        run_tts_strategy(strategy, scenarios, simulations=40, batch_size=20,
                         seed=11, backend="modular")
        for strategy in ("sequential", "processes=2", "parallel=2", "parallel=2:5")
    ]
    assert [item.mode for item in results] == [
        "sequential", "processes-pool", "parallel-pool", "parallel-pool"]
    assert [item.processes for item in results] == [1, 2, 2, 2]
    assert all(len(item.per_scenario_seconds) == 2 for item in results)
    parity = tts_backend_parity(results)
    assert parity["passed"], parity
    assert sum(results[0].totals) == 80

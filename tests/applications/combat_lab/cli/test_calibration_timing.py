"""Calibration timing hygiene: warm pools before timing, record provenance.

Pools, engines and the provenance probe are stubbed: nothing simulates.
"""
from __future__ import annotations

import itertools

from mordheim_combat_lab.cli import calibration


class FakeExecutor:
    """Executor whose warm-up answers come from a scripted pid sequence."""

    def __init__(self, pids, events=None, **_kwargs):
        self.pids = iter(pids)
        self.events = events if events is not None else []
        self.rounds = 0

    def map(self, function, values):
        self.rounds += 1
        self.events.append("warm")
        return [next(self.pids) for _ in values]

    def shutdown(self):
        self.events.append("shutdown")


def test_warm_executor_repeats_until_every_worker_answered():
    executor = FakeExecutor([1, 1, 1, 2, 3, 1, 9, 9, 9])
    assert calibration.warm_executor(executor, 3, pause=0) == 3
    assert executor.rounds == 2


def test_warm_executor_gives_up_after_the_attempt_budget():
    executor = FakeExecutor(itertools.repeat(1))
    assert calibration.warm_executor(executor, 4, attempts=3, pause=0) == 1
    assert executor.rounds == 3


def test_pooled_walls_time_only_after_the_pool_is_warm(monkeypatch):
    events = []
    executors = []

    def make_executor(max_workers):
        executor = FakeExecutor(itertools.count(), events)
        executor.max_workers = max_workers
        executors.append(executor)
        return executor

    monkeypatch.setattr(calibration, "ProcessPoolExecutor", make_executor)
    monkeypatch.setattr(calibration, "simulate_battery",
                        lambda *args, **kwargs: events.append("simulate"))
    pairs = [(object(), object(), 5, "p1"), (object(), object(), 5, "p2")]
    walls = calibration._pooled_walls(pairs, "numpy", 40_000, 10_000, 4, 7)
    assert len(walls) == 2
    (executor,) = executors
    assert executor.max_workers == 4
    first_simulation = events.index("simulate")
    assert "warm" in events[:first_simulation]
    assert "warm" not in events[first_simulation:]
    assert events[-1] == "shutdown"


def test_profile_records_provenance_and_sweeps_workers_at_the_sequential_batch(monkeypatch):
    stamp = {"cpu_count": 3, "engine_digests": {"numpy": "x"}}
    pooled_calls = []
    monkeypatch.setattr(calibration, "measurement_provenance", lambda engines: stamp)
    monkeypatch.setattr(calibration, "available_backends", lambda: ("numpy",))
    monkeypatch.setattr(calibration, "require_optimized_support", lambda *a, **k: None)
    # 100k wins the sequential sweep clearly.
    monkeypatch.setattr(calibration, "_sequential_walls",
                        lambda pairs, backend, samples, batch, seed: (
                            [0.5 if batch == 100_000 else 1.0] * len(pairs)))

    def pooled(pairs, backend, samples, batch, workers, seed):
        pooled_calls.append((samples, batch, workers))
        return [0.5] * len(pairs)

    monkeypatch.setattr(calibration, "_pooled_walls", pooled)
    monkeypatch.setattr(calibration, "measure_spawn", lambda workers, repetitions=3: 0.1)
    payload = calibration.run_calibration(
        "mini", pair_source=lambda name: [(object(), object(), 5, "p1")],
        log=lambda message: None)
    assert payload["provenance"] == stamp
    assert payload["spawn_seconds"] == {"numpy": 0.1}
    assert payload["batch_sizes"] == {"numpy": 100_000}
    assert "pooled_batch_sizes" not in payload
    assert payload["method"]["worker_sweep_batch"] == {"numpy": 100_000}
    # Every worker candidate runs at the sequential winner; the pooled sample
    # (500k by default for numpy) is raised to 10 workers x 100k.
    assert pooled_calls == [(1_000_000, 100_000, count) for count in (4, 6, 8, 10)]
    assert payload["method"]["samples"]["numpy"]["pooled"] == 1_000_000

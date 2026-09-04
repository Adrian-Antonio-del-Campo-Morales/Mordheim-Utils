"""Measure the process-pool modular oracle against the sequential one.

Runs the same independent duel streams through ``simulate_duel_reference``
(one core) and ``simulate_duel_reference_parallel`` (one process per worker)
and reports wall time, speedup and exact equality of the verdict counts.

Usage:
    python tools/measure-parallel-oracle.py [--simulations N] [--workers W]
"""
from __future__ import annotations

import argparse
import platform
import time

from mordheim_combat.modular.duel import simulate_duel_reference
from mordheim_combat.modular.parallel import simulate_duel_reference_parallel
from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
from mordheim_construction.compiler import compile_fighter
import os


def _parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", default="basic",
                        help="scenario id to measure (default: basic)")
    parser.add_argument("--simulations", type=int, default=None,
                        help="target simulations; defaults to a size that runs "
                             "~12 s on the sequential oracle")
    parser.add_argument("--workers", type=int, default=None,
                        help="pool size (default: os.cpu_count())")
    return parser.parse_args()


def _rate(first, second, maximum_rounds: int) -> float:
    start = time.perf_counter()
    simulate_duel_reference(first, second, 2_000, seed=2026,
                            maximum_rounds=maximum_rounds)
    elapsed = time.perf_counter() - start
    return 2_000 / elapsed


def main() -> None:
    args = _parse()
    scenario = next(item for item in benchmark_scenarios() if item.id == args.scenario)
    first, second = compile_fighter(scenario.first), compile_fighter(scenario.second)
    workers = args.workers if args.workers is not None else os.cpu_count() or 1
    rate = _rate(first, second, scenario.maximum_rounds)
    simulations = args.simulations or int(rate * 12)
    print(f"platform: {platform.platform()}")
    print(f"python:   {platform.python_version()}")
    print(f"workers:  {workers} (cpu_count={os.cpu_count()})")
    print(f"scenario: {args.scenario} (max {scenario.maximum_rounds} rounds)")
    print(f"calibrated sequential rate: {rate:,.0f} duels/s -> {simulations:,} duels")
    print(f"{'duels':>10} {'seq (s)':>9} {'par (s)':>9} {'speedup':>8}  exact match")
    for size in (simulations, 4 * simulations):
        sequential_start = time.perf_counter()
        sequential = simulate_duel_reference(
            first, second, size, seed=2026, maximum_rounds=scenario.maximum_rounds,
        )
        sequential_elapsed = time.perf_counter() - sequential_start
        parallel_start = time.perf_counter()
        parallel = simulate_duel_reference_parallel(
            first, second, size, seed=2026, maximum_rounds=scenario.maximum_rounds,
            workers=workers,
        )
        parallel_elapsed = time.perf_counter() - parallel_start
        match = "yes" if parallel == sequential else f"NO {parallel} vs {sequential}"
        print(f"{size:>10,} {sequential_elapsed:>9.2f} {parallel_elapsed:>9.2f} "
              f"{sequential_elapsed / parallel_elapsed:>7.2f}x  {match}")


if __name__ == "__main__":
    main()

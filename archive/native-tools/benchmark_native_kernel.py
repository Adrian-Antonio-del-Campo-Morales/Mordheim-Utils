"""external.benchmark_native_kernel: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

import argparse as argparse
import math as math
from mordheim_combat_lab import engine
import numpy as np
from pathlib import Path
import sys as sys
import time as time


ROOT = Path(__file__).resolve().parents[1]


sys.path.insert(0, str(ROOT / "src"))


base = {
    "WS": 3, "S": 3, "T": 3, "W": 1, "I": 3, "A": 1,
    "skills": [], "main_weapon": "Sword", "off_hand": "None",
    "armor": "No armour",
}


CASES = (
    ("Sword versus mace", {}, {"main_weapon": "Mace"}),
    ("Two weapons", {"off_hand": "Dagger"}, {"off_hand": "Mace"}),
    (
        "Double-handed weapon versus shield",
        {"main_weapon": "Double-handed weapon"},
        {"off_hand": "Shield", "armor": "Light armour"},
    ),
    (
        "Multiple attacks and wounds",
        {"WS": 4, "A": 3, "off_hand": "Axe"},
        {"WS": 4, "W": 2, "T": 4, "armor": "Heavy armour"},
    ),
    (
        "Heavy armour",
        {"main_weapon": "Axe", "armor": "Gromril armour", "off_hand": "Shield"},
        {"main_weapon": "Dagger", "armor": "Gromril armour", "off_hand": "Shield"},
    ),
)


def run_engine(candidate, enemy, total, seed, native):
    previous = engine._simulate_simple_native
    engine._simulate_simple_native = native
    try:
        started = time.perf_counter()
        wins, resolved = engine._simulate_batch(
            candidate,
            np.asarray([enemy]),
            np.zeros(total, dtype=np.int8),
            total,
            seed,
        )
        return wins / resolved, resolved, time.perf_counter() - started
    finally:
        engine._simulate_simple_native = previous


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--simulations", type=int, default=500_000)
    args = parser.parse_args()
    native = engine._simulate_simple_native
    if native is None:
        raise SystemExit("Build the kernel first with build_NATIVE_KERNEL.bat.")

    print(f"Independent runs per engine: {args.simulations:,}")
    worst_z = 0.0
    speedups = []
    for index, (label, candidate_changes, enemy_changes) in enumerate(CASES):
        candidate = engine._make_fighter(base | candidate_changes)
        enemy = engine._make_fighter(base | enemy_changes)
        native_rate, native_resolved, native_time = run_engine(
            candidate, enemy, args.simulations, 1_000 + index, native
        )
        python_rate, python_resolved, python_time = run_engine(
            candidate, enemy, args.simulations, 9_000 + index, None
        )
        standard_error = math.sqrt(
            native_rate * (1 - native_rate) / native_resolved
            + python_rate * (1 - python_rate) / python_resolved
        )
        z_score = (native_rate - python_rate) / standard_error
        speedup = python_time / native_time
        worst_z = max(worst_z, abs(z_score))
        speedups.append(speedup)
        print(
            f"{label:28} Cython {native_rate:8.4%}  NumPy {python_rate:8.4%}  "
            f"Dif. {(native_rate - python_rate) * 100:+.3f} %  "
            f"z {z_score:+.2f}  {speedup:.1f}x"
        )
    print(f"Average speed-up: {sum(speedups) / len(speedups):.1f}x; |z| maximum: {worst_z:.2f}")


if __name__ == "__main__":
    main()

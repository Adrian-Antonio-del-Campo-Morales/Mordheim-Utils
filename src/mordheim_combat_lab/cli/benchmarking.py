"""Maintained end-to-end benchmark suite for combat backends."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
from statistics import median
from time import perf_counter
from typing import Callable

import numpy as np

from mordheim_combat_lab.combat.modular.duel import simulate_duel as simulate_modular_duel
from mordheim_combat_lab.combat.vectorized import simulate_duel
from mordheim_combat_lab.construction.compiler import compile_fighter
from mordheim_combat_lab.domain.models import Characteristics
from mordheim_combat_lab.domain.models import DuelRequest
from mordheim_combat_lab.domain.models import FighterBuild


@dataclass(frozen=True, slots=True)
class BenchmarkScenario:
    id: str
    first: FighterBuild
    second: FighterBuild
    maximum_rounds: int = 50


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    scenario: str
    backend: str
    simulations: int
    batch_size: int
    repeats: int
    samples_seconds: tuple[float, ...]
    median_seconds: float
    simulations_per_second: float


@dataclass(frozen=True, slots=True)
class BenchmarkComparison:
    scenario: str
    backend: str
    baseline_simulations_per_second: float
    current_simulations_per_second: float
    change_ratio: float
    status: str


@dataclass(frozen=True, slots=True)
class BenchmarkGate:
    passed: bool
    improved: bool
    regressed: bool
    comparisons: tuple[BenchmarkComparison, ...]
    detail: str


BENCHMARK_SCHEMA = "mordheim-combat-benchmark/v1"


def benchmark_scenarios() -> tuple[BenchmarkScenario, ...]:
    ordinary = Characteristics(3, 3, 3, 1, 3, 1)
    veteran = Characteristics(4, 4, 4, 2, 4, 2)
    durable = Characteristics(2, 2, 5, 4, 2, 1)
    return (
        BenchmarkScenario(
            "basic",
            FighterBuild("mordheim", ordinary),
            FighterBuild("mordheim", ordinary),
        ),
        BenchmarkScenario(
            "multiattack",
            FighterBuild("mordheim", Characteristics(4, 4, 3, 2, 4, 3),
                         main_weapon_id="weapon.axe", off_hand_id="weapon.dagger"),
            FighterBuild("mordheim", veteran, armour_id="armour.heavy-armour"),
        ),
        BenchmarkScenario(
            "defences",
            FighterBuild("mordheim", veteran, main_weapon_id="weapon.sword",
                         off_hand_id="defence.buckler", armour_id="armour.light-armour"),
            FighterBuild("mordheim", veteran, main_weapon_id="weapon.dwarf-axe",
                         off_hand_id="defence.shield", armour_id="armour.gromril-armour"),
        ),
        BenchmarkScenario(
            "stateful",
            FighterBuild(
                "mordheim", band_id="pit-fighters", profile_id="pit-king",
                special_rule_ids=("band--pit-fighter-skill-force-of-will",),
            ),
            FighterBuild("mordheim", veteran, main_weapon_id="weapon.brazier-iron"),
        ),
        BenchmarkScenario(
            "long",
            FighterBuild("mordheim", durable, armour_id="armour.gromril-armour",
                         off_hand_id="defence.shield"),
            FighterBuild("mordheim", durable, armour_id="armour.gromril-armour",
                         off_hand_id="defence.shield"),
            maximum_rounds=75,
        ),
    )


def run_benchmark(
    scenario: BenchmarkScenario, *, simulations: int, batch_size: int,
    seed: int, backend: str, warmups: int, repeats: int,
    on_progress: Callable[[], None] | None = None,
) -> BenchmarkResult:
    if backend not in {"modular", "numpy", "native"}:
        raise ValueError(f"unknown benchmark backend: {backend}")
    first, second = compile_fighter(scenario.first), compile_fighter(scenario.second)
    request = DuelRequest(
        first, second, simulations, seed=seed, batch_size=batch_size,
        maximum_rounds=scenario.maximum_rounds,
    )
    def execute() -> None:
        if backend == "modular":
            simulate_modular_duel(request)
        else:
            simulate_duel(request, backend=backend)

    for _ in range(warmups):
        execute()
        if on_progress is not None:
            on_progress()
    samples = []
    for _ in range(repeats):
        started = perf_counter()
        execute()
        samples.append(perf_counter() - started)
        if on_progress is not None:
            on_progress()
    middle = median(samples)
    return BenchmarkResult(
        scenario.id, backend, simulations, batch_size, repeats, tuple(samples),
        middle, simulations / middle,
    )


def benchmark_payload(
    results: tuple[BenchmarkResult, ...] | list[BenchmarkResult],
    unavailable: tuple[dict[str, str], ...] | list[dict[str, str]], *,
    simulations: int, batch_size: int, seed: int, warmups: int, repeats: int,
) -> dict[str, object]:
    """Build a durable benchmark artifact suitable for later comparison."""
    return {
        "schema": BENCHMARK_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "platform": platform.platform(),
            "processor": platform.processor(),
        },
        "configuration": {
            "simulations": simulations, "batch_size": batch_size, "seed": seed,
            "warmups": warmups, "repeats": repeats,
        },
        "results": [
            {
                "scenario": item.scenario, "backend": item.backend,
                "simulations": item.simulations, "batch_size": item.batch_size,
                "repeats": item.repeats,
                "samples_seconds": list(item.samples_seconds),
                "median_seconds": item.median_seconds,
                "simulations_per_second": item.simulations_per_second,
            }
            for item in results
        ],
        "unavailable": list(unavailable),
    }


def write_benchmark_payload(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_benchmark_payload(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != BENCHMARK_SCHEMA:
        raise ValueError(f"unsupported benchmark schema: {payload.get('schema')!r}")
    if not isinstance(payload.get("results"), list):
        raise ValueError("benchmark report has no results list")
    return payload


def compare_with_baseline(
    results: tuple[BenchmarkResult, ...] | list[BenchmarkResult],
    baseline: dict[str, object], *, improvement_threshold: float = .10,
    regression_threshold: float = .05,
) -> BenchmarkGate:
    """Apply the agreed optimization gate to NumPy/native comparable results."""
    previous = {
        (str(item["scenario"]), str(item["backend"])): float(item["simulations_per_second"])
        for item in baseline["results"]
    }
    comparisons = []
    for item in results:
        if item.backend == "modular" or (item.scenario, item.backend) not in previous:
            continue
        old = previous[(item.scenario, item.backend)]
        if old <= 0:
            raise ValueError(f"invalid baseline throughput for {item.scenario}/{item.backend}")
        change = item.simulations_per_second / old - 1.0
        status = (
            "IMPROVED" if change >= improvement_threshold else
            "REGRESSED" if change < -regression_threshold else "STABLE"
        )
        comparisons.append(BenchmarkComparison(
            item.scenario, item.backend, old, item.simulations_per_second, change, status,
        ))
    improved = any(item.status == "IMPROVED" for item in comparisons)
    regressed = any(item.status == "REGRESSED" for item in comparisons)
    if not comparisons:
        detail = "no comparable NumPy/native results found in baseline"
    elif regressed:
        detail = "at least one scenario exceeds the allowed regression"
    elif not improved:
        detail = "no scenario reaches the required improvement"
    else:
        detail = "required improvement reached without disallowed regressions"
    return BenchmarkGate(bool(comparisons) and improved and not regressed,
                         improved, regressed, tuple(comparisons), detail)

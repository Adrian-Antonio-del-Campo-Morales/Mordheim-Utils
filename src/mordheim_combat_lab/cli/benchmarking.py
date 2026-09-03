"""Benchmark suite and CLI presenters for the combat backends.

Runs the maintained end-to-end scenarios against the modular, NumPy and
native engines, supports single-configuration runs (with baseline
comparison gates) and size sweeps over simulation counts and batch
sizes, and renders results as console tables, JSON, CSV or Markdown.
"""
from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime, timezone
import csv
import json
from pathlib import Path
import platform
from statistics import median
from time import perf_counter
from typing import Callable
from typing import Iterable

import numpy as np

from mordheim_combat.modular.duel import simulate_duel as simulate_modular_duel
from mordheim_combat.vectorized import simulate_duel
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import DuelRequest
from mordheim_core.models import FighterBuild


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
SWEEP_SCHEMA = "mordheim-combat-benchmark-sweep/v1"

ENGINE_LABELS = {"modular": "Modular", "numpy": "Vectorized", "native": "Native"}


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


def parse_sizes(value: str | None, default: int) -> tuple[int, ...]:
    """Parse a size list such as "1k,10k 100k" into positive integers."""
    if not value or not value.strip():
        return (default,)
    sizes = []
    for token in value.replace(";", ",").replace(" ", ",").split(","):
        token = token.strip().lower()
        if not token:
            continue
        multiplier = 1
        if token.endswith("k"):
            multiplier, token = 1_000, token[:-1]
        elif token.endswith("m"):
            multiplier, token = 1_000_000, token[:-1]
        try:
            parsed = int(token) * multiplier
        except ValueError as error:
            raise ValueError(
                f"invalid size token {token!r}; use plain integers or k/m suffixes"
            ) from error
        if parsed < 1:
            raise ValueError("benchmark sizes must be positive")
        sizes.append(parsed)
    if not sizes:
        raise ValueError("no benchmark sizes provided")
    return tuple(dict.fromkeys(sizes))


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
    """Build a durable single-configuration benchmark artifact."""
    return {
        "schema": BENCHMARK_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": _environment(),
        "configuration": {
            "simulations": simulations, "batch_size": batch_size, "seed": seed,
            "warmups": warmups, "repeats": repeats,
        },
        "results": [asdict(item) for item in results],
        "unavailable": list(unavailable),
    }


def sweep_payload(
    results: tuple[BenchmarkResult, ...] | list[BenchmarkResult],
    unavailable: tuple[dict[str, str], ...] | list[dict[str, str]], *,
    simulation_sizes: tuple[int, ...], batch_sizes: tuple[int, ...],
    seed: int, warmups: int, repeats: int,
) -> dict[str, object]:
    """Build a durable multi-configuration sweep artifact."""
    return {
        "schema": SWEEP_SCHEMA,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "environment": _environment(),
        "configuration": {
            "simulation_sizes": list(simulation_sizes),
            "batch_sizes": list(batch_sizes),
            "seed": seed, "warmups": warmups, "repeats": repeats,
        },
        "results": [asdict(item) for item in results],
        "unavailable": list(unavailable),
    }


def _environment() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "platform": platform.platform(),
        "processor": platform.processor(),
    }


def write_benchmark_payload(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")


def load_benchmark_payload(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != BENCHMARK_SCHEMA:
        raise ValueError(f"unsupported benchmark schema: {payload.get('schema')!r}")
    if not isinstance(payload.get("results"), list):
        raise ValueError("benchmark report has no results list")
    return payload


def write_report(path: Path, payload: dict[str, object]) -> None:
    """Write a benchmark or sweep payload as JSON, CSV or Markdown."""
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = path.suffix.casefold()
    results = payload.get("results", [])
    if suffix == ".csv":
        with path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, delimiter=";")
            writer.writerow([
                "scenario", "engine", "simulations", "batch_size", "repeats",
                "median_seconds", "simulations_per_second",
            ])
            for item in results:
                writer.writerow([
                    item["scenario"], item["backend"], item["simulations"],
                    item["batch_size"], item["repeats"],
                    f"{item['median_seconds']:.6f}",
                    f"{item['simulations_per_second']:.1f}",
                ])
        return
    if suffix in {".md", ".markdown"}:
        path.write_text(
            _markdown_report(payload) + "\n", encoding="utf-8")
        return
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _markdown_report(payload: dict[str, object]) -> str:
    lines = ["# Combat benchmark report", ""]
    configuration = payload.get("configuration", {})
    lines.append(f"- generated: {payload.get('generated_at', '')}")
    environment = payload.get("environment", {})
    lines.append(
        f"- environment: python {environment.get('python')}, "
        f"numpy {environment.get('numpy')}"
    )
    lines.append(f"- configuration: {json.dumps(configuration)}")
    lines.append("")
    if payload.get("comparison") is not None:
        comparison = payload["comparison"]
        lines.append(f"## Gate: {'PASS' if comparison['passed'] else 'FAIL'}")
        lines.append(f"{comparison['detail']}")
        for row in comparison["comparisons"]:
            lines.append(
                f"- {row['scenario']}/{row['backend']}: "
                f"{row['change_ratio']:+.2%} [{row['status']}]"
            )
        lines.append("")
    lines.append("## Results")
    lines.append("")
    lines.append("| scenario | engine | simulations | batch_size | repeats | median (s) | sim/s |")
    lines.append("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
    for item in payload.get("results", []):
        lines.append(
            f"| {item['scenario']} | {ENGINE_LABELS.get(item['backend'], item['backend'])} "
            f"| {item['simulations']:,} | {item['batch_size']:,} | {item['repeats']} "
            f"| {item['median_seconds']:.4f} | {item['simulations_per_second']:,.0f} |"
        )
    return "\n".join(lines)


def compare_with_baseline(
    results: tuple[BenchmarkResult, ...] | list[BenchmarkResult],
    baseline: dict[str, object], *, improvement_threshold: float = .10,
    regression_threshold: float = .05,
) -> BenchmarkGate:
    """Apply the agreed optimization gate to comparable NumPy/native results."""
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


def _render_rows(results, unavailable) -> tuple[list[list[str]], list[str]]:
    """Return (aligned text rows, width hints) for a results table."""
    by_key = {(item.scenario, item.backend, item.simulations, item.batch_size): item
              for item in results}
    rows: list[list[str]] = []
    keys = sorted(by_key)
    for key in keys:
        item = by_key[key]
        rows.append([
            item.scenario,
            ENGINE_LABELS.get(item.backend, item.backend),
            f"{item.simulations:,}", f"{item.batch_size:,}", str(item.repeats),
            f"{item.simulations_per_second:,.0f}",
            f"{item.median_seconds * 1_000:.1f} ms",
        ])
    notes = [f"{row.get('engine', row['backend'])} not available: {row['reason']}"
             for row in unavailable]
    return rows, notes


def print_results_table(
    results: Iterable[BenchmarkResult], unavailable,
    *, simulations: int, batch_size: int, seed: int, repeats: int,
) -> None:
    items = list(results)
    headers = ["Scenario", "Engine", "Simulations", "Batch size", "Repeats",
               "sim/s", "Median"]
    rows, notes = _render_rows(items, unavailable)
    print(
        f"Benchmark: {simulations:,} simulations per scenario and engine "
        f"(batch size {batch_size:,}, seed {seed}, median of {repeats} repeats)."
    )
    _print_ascii_table(headers, rows)
    for note in notes:
        print(note)


def print_sweep_table(
    results: Iterable[BenchmarkResult], unavailable,
    *, simulation_sizes: tuple[int, ...], batch_sizes: tuple[int, ...],
    seed: int, repeats: int,
) -> None:
    items = list(results)
    headers = ["Scenario", "Engine", "Simulations", "Batch size", "Repeats",
               "sim/s", "Median"]
    rows, notes = _render_rows(items, unavailable)
    print(
        "Benchmark sweep: "
        + ", ".join(f"{value:,} simulations" for value in simulation_sizes)
        + "; batch sizes "
        + ", ".join(f"{value:,}" for value in batch_sizes)
        + f" (seed {seed}, median of {repeats} repeats)."
    )
    _print_ascii_table(headers, rows)
    for note in notes:
        print(note)


def _print_ascii_table(headers: list[str], rows: list[list[str]]) -> None:
    widths = [max([len(headers[index])] + [len(row[index]) for row in rows])
              for index in range(len(headers))]
    def line(values: list[str]) -> str:
        return " | ".join(f"{value:<{widths[index]}}" for index, value in enumerate(values))
    print(line(headers))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(line(row))


def print_gate(gate: BenchmarkGate, *, improvement: float, regression: float) -> None:
    print(
        f"Comparison with baseline (required improvement {improvement:g} %, "
        f"maximum regression {regression:g} %):"
    )
    for item in gate.comparisons:
        print(
            f"  {item.scenario}/{item.backend}: {item.change_ratio:+.2%} "
            f"[{item.status}]"
        )
    print(f"Performance gate: {'PASS' if gate.passed else 'FAIL'} - {gate.detail}")


class BenchmarkProgress:
    """Minimal progress bar for already-completed work units."""

    def __init__(self, total: int) -> None:
        self.total = total
        self.completed = 0
        self.rendered = False
        self._render()

    def advance(self) -> None:
        self.completed += 1
        self._render()

    def finish(self) -> None:
        if self.rendered:
            print()

    def _render(self) -> None:
        if not self.total:
            return
        width = 24
        completed = min(self.completed, self.total)
        filled = round(width * completed / self.total)
        percent = completed * 100 // self.total
        print(
            f"\rProgress: [{'#' * filled}{'-' * (width - filled)}] "
            f"{percent:3}% ({completed}/{self.total})",
            end="", flush=True,
        )
        self.rendered = True

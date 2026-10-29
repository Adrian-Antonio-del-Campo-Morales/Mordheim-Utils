"""Excel-friendly reports for statistical comparisons and technical tests."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Callable
from typing import Iterable


from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
from mordheim_combat.vectorized import available_backends
from mordheim_combat_lab.cli.benchmarking import compile_benchmark_fighters
from mordheim_combat_lab.verification.parity import compare_statistical_parity


STATISTICAL_COLUMNS = (
    "test_id", "category", "operation", "rules", "expected",
    "modular_result", "numpy_result", "native_result",
    "modular_status", "numpy_status", "native_status", "passes", "details",
)

TECHNICAL_COLUMNS = (
    "test_id", "file", "class", "test", "markers", "status",
    "duration_seconds", "error", "passes",
)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _excel_cell(value: object) -> object:
    if not isinstance(value, str):
        return value
    # Physical line breaks and control characters make a valid CSV look like
    # broken rows in Excel and in line-oriented viewers.
    value = re.sub(r"[\x00-\x1f\x7f\u2028\u2029]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    # Prevent Excel from interpreting human text as a formula.
    if value.startswith(("=", "+", "-", "@")):
        value = "'" + value
    return value


def write_csv(path: Path, columns: tuple[str, ...], rows: Iterable[dict[str, object]]) -> None:
    """Write a stable semicolon CSV that Excel opens as Unicode."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: _excel_cell(row.get(column, "")) for column in columns})


def statistical_report_rows(*, simulations: int = 100_000, seed: int = 2026,
                            on_progress: Callable[[], None] | None = None,
                            workers: object | None = None,
                            ) -> list[dict[str, object]]:
    """Compare the existing duel scenarios statistically; no semantic YAML runs."""
    native_available = "native" in available_backends()
    rows: list[dict[str, object]] = []
    for scenario in benchmark_scenarios():
        from mordheim_combat.modular.parallel import resolve_oracle_workers
        from mordheim_combat.modular.parallel import run_oracle_sample
        import time

        first, second = compile_benchmark_fighters(scenario)
        oracle_started = time.perf_counter()
        modular_result = run_oracle_sample(
            first, second, simulations, seed=seed,
            maximum_rounds=scenario.maximum_rounds,
            workers=resolve_oracle_workers(
                workers, simulations, scenario.maximum_rounds,
            ),
        )
        oracle_seconds = time.perf_counter() - oracle_started
        numpy_result = compare_statistical_parity(
            scenario.id, first, second, simulations, seed=seed,
            maximum_rounds=scenario.maximum_rounds, backend="numpy",
            modular=modular_result, reference_seconds=oracle_seconds,
        )
        modular = {"rates_w_l_u": numpy_result.modular_rates, "simulations": simulations}
        numpy = {"rates_w_l_u": numpy_result.vectorized_rates, "tolerances": numpy_result.tolerances,
                 "simulations": simulations}
        native = {}
        native_status = "NOT_AVAILABLE"
        native_detail = "native combat backend is not available"
        if native_available:
            try:
                native_result = compare_statistical_parity(
                    scenario.id, first, second, simulations, seed=seed,
                    maximum_rounds=scenario.maximum_rounds, backend="native",
                    modular=modular_result, reference_seconds=oracle_seconds,
                )
            except Exception as error:
                native_status = "FAIL"
                native_detail = str(error)
            else:
                native_status = "PASS" if native_result.passed else "FAIL"
                native = {
                    "rates_w_l_u": native_result.vectorized_rates,
                    "tolerances": native_result.tolerances, "simulations": simulations,
                }
                native_detail = ""
        numpy_passed = numpy_result.passed
        native_passed = not native_available or native_status == "PASS"
        passes = "PASS" if numpy_passed and native_passed else "FAIL"
        if not native_available and numpy_passed:
            passes = "PENDING"
        rows.append({
            "test_id": f"statistical/{scenario.id}", "specification": "statistical",
            "case": scenario.id, "category": "statistical", "operation": "duel",
            "layer": "combat", "source_targets": "", "roles": "aggregate",
            "rules": "",
            "interpretation": "Independent modular and optimized samples satisfy the six-sigma gate.",
            "expected": _json({"minimum_tolerance": 0.0025}), "rng_mode": "statistical",
            "shared_status": "NOT_APPLICABLE", "shared_result": "", "shared_detail": "",
            "modular_status": "PASS", "modular_result": _json(modular), "modular_detail": "",
            "numpy_status": "PASS" if numpy_passed else "FAIL", "numpy_result": _json(numpy), "numpy_detail": "",
            "native_status": native_status, "native_result": _json(native) if native else "",
            "native_detail": native_detail,
            "passes": passes,
            "details": "" if not native_detail else f"native: {native_detail}",
        })
        if on_progress is not None:
            on_progress()
    return rows


def write_statistical_report(output: Path, *,
                          simulations: int = 100_000, seed: int = 2026,
                          on_progress: Callable[[], None] | None = None,
                          workers: object | None = None,
                          ) -> tuple[Path, list[dict[str, object]]]:
    """Compute statistical comparisons and write their CSV; return its path."""
    output = Path(output)
    statistical_path = output / "statistical-parity.csv"
    try:
        statistical_rows = statistical_report_rows(
            simulations=simulations, seed=seed,
            on_progress=on_progress, workers=workers,
        )
    except Exception as error:
        statistical_rows = [{
            "test_id": "report/statistical-generation", "category": "report",
            "operation": "generate", "layer": "infrastructure",
            "modular_status": "ERROR", "modular_detail": str(error), "passes": "FAIL",
        }]
    write_csv(statistical_path, STATISTICAL_COLUMNS, statistical_rows)
    return statistical_path, statistical_rows


def run_technical_tests(path: Path) -> int:
    path = Path(path)
    environment = dict(__import__("os").environ)
    environment["MORDHEIM_TEST_REPORT_CSV"] = str(path.resolve())
    command = [
        sys.executable, "-m", "pytest", "-p",
        "mordheim_combat_lab.verification.pytest_reporter", "-p", "no:cacheprovider", "-q",
    ]
    try:
        exit_code = subprocess.run(command, env=environment, check=False).returncode
    except Exception as error:
        write_csv(path, TECHNICAL_COLUMNS, ({
            "test_id": "pytest/session", "status": "ERROR", "error": str(error), "passes": "FAIL",
        },))
        return 1
    if not path.is_file():
        write_csv(path, TECHNICAL_COLUMNS, ({
            "test_id": "pytest/session", "status": "ERROR",
            "error": "pytest did not create its report", "passes": "FAIL",
        },))
        return 1
    return exit_code


def generate_test_report(output: Path, *, statistical: bool = False,
                         simulations: int = 100_000, seed: int = 2026,
                         on_progress: Callable[[], None] | None = None,
                         workers: object | None = None,
                         ) -> tuple[Path | None, Path, list[dict[str, object]], int]:
    """Technical tests plus optional statistical comparisons; no semantic runner."""
    output = Path(output)
    statistical_path, statistical_rows = None, []
    if statistical:
        statistical_path, statistical_rows = write_statistical_report(
            output, simulations=simulations, seed=seed,
            on_progress=on_progress, workers=workers,
        )
    technical_path = output / "technical-tests.csv"
    technical_exit = run_technical_tests(technical_path)
    return statistical_path, technical_path, statistical_rows, technical_exit

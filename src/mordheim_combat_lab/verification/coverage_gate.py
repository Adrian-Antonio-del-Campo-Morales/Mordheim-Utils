"""Deterministic line-coverage gate for the combat engines.

The semantic-specification corpus and the parity adapters certify the
engines *per rule*, but nothing measures whether every reachable engine line
is exercised by a deterministic test.  This module runs the deterministic
engine suites under ``coverage`` and compares the result against a committed
*budget*: a per-file list of statement lines that must remain exercised.

The gate is deliberately a drift gate rather than a raw percentage gate:

- line numbers shift as the engine evolves, so a percentage baseline would
  fail spuriously on every refactor;
- the budget records which lines were covered on the day it was generated
  (``coverage-gate --update-budget``), and the gate fails when any of them
  stops being exercised.  New engine code is *not* in the budget yet, so a
  change that adds lines must regenerate the budget after adding the
  deterministic tests that cover them — exactly the discipline the parity
  strategy wants (code first, evidence with it, gate green).
"""
from __future__ import annotations

from dataclasses import dataclass
from dataclasses import asdict
import json
import os
import time
from pathlib import Path
from typing import Iterable
from typing import Mapping

ROOT = Path(__file__).resolve().parents[3]

#: Suites that exercise engine behaviour without statistical noise: both
#: drivers' unit suites, the shared phase tests and the parity layer (exact
#: operator checks plus the semantic-specification corpus that replays every
#: rule against the vectorized engine).  Statistical/deep samples are not
#: included: they certify *interaction*, and a flaky sample should never gate
#: coverage.
DEFAULT_SUITES = (
    "tests/combat/modular",
    "tests/combat/vectorized",
    "tests/combat/test_phases.py",
    "tests/verification/test_parity.py",
)

#: Areas of the engine tracked by the gate, keyed by the sub-path under
#: ``src/mordheim_combat`` (or the file name for root-level modules).
AREA_PATHS = {
    "modular": ("modular",),
    "vectorized": ("vectorized",),
    "phases": ("phases.py", "vector_dice.py"),
}

BUDGET_SCHEMA = "mordheim-coverage-budget/v1"


@dataclass(frozen=True, slots=True)
class CoverageFile:
    """Per-file statement coverage for one engine module."""

    module: str  # dotted name, e.g. mordheim_combat.vectorized._driver
    area: str
    statements: int
    covered: tuple[int, ...]
    missing: tuple[int, ...]
    path: str  # repository-relative path

    @property
    def percent(self) -> float:
        return 100.0 * len(self.covered) / self.statements if self.statements else 100.0


@dataclass(frozen=True, slots=True)
class CoverageReport:
    files: tuple[CoverageFile, ...]
    suites: tuple[str, ...]
    seconds: float

    def area_total(self, area: str) -> tuple[int, int]:
        statements = covered = 0
        for item in self.files:
            if item.area == area:
                statements += item.statements
                covered += len(item.covered)
        return covered, statements


@dataclass(frozen=True, slots=True)
class CoverageGateResult:
    passed: bool
    errors: tuple[str, ...]
    report: CoverageReport


def _area_for(relative: str) -> str | None:
    normalized = relative.replace(os.sep, "/")
    for area, markers in AREA_PATHS.items():
        for marker in markers:
            if marker.endswith(".py"):
                if normalized == marker or normalized.endswith(f"/{marker}"):
                    return area
            elif f"/{marker}/" in f"/{normalized}/":
                return area
    return None


def _engine_files(cov) -> list[CoverageFile]:
    files = []
    for absolute in sorted(cov.get_data().measured_files()):
        try:
            relative = os.path.relpath(absolute, ROOT)
        except ValueError:
            continue
        normalized = relative.replace(os.sep, "/")
        if not normalized.startswith("src/mordheim_combat/"):
            continue
        module_relative = normalized[len("src/"):]
        if module_relative.endswith(".py"):
            module_relative = module_relative[:-3]
        module_relative = module_relative.replace("/", ".")
        area = _area_for(relative)
        if area is None:
            continue
        _, statements, executed, missing, _ = cov.analysis2(absolute)
        files.append(CoverageFile(
            module=module_relative, area=area, statements=len(statements),
            covered=tuple(sorted(set(statements) - set(missing))),
            missing=tuple(sorted(missing)),
            path=normalized,
        ))
    return files


def measure_coverage(
    suites: Iterable[str] = DEFAULT_SUITES,
) -> CoverageReport:
    """Run the deterministic suites under coverage and return the engine report.

    Requires the ``coverage`` distribution (dev extra).  Suites are pytest
    paths resolved from the repository root; the run is quiet and never writes
    a ``.coverage`` data file.  Measurement traces the whole process and the
    engine files are filtered afterwards (``coverage`` glob matching is not
    reliable on Windows backslash paths), so only the tracked engine modules
    appear in the report.
    """
    import pytest
    import coverage

    cov = coverage.Coverage(data_file=None)
    suites = tuple(suites)
    started = time.perf_counter()
    cov.start()
    try:
        pytest.main(["-q", "-p", "no:cacheprovider", "--no-header", *suites])
    finally:
        cov.stop()
    files = tuple(sorted(_engine_files(cov), key=lambda item: item.module))
    return CoverageReport(files=files, suites=suites,
                          seconds=time.perf_counter() - started)


def write_budget(path: Path, report: CoverageReport) -> dict[str, object]:
    """Persist the covered-line budget for a measured report."""
    payload: dict[str, object] = {
        "schema": BUDGET_SCHEMA,
        "suites": report.suites,
        "areas": {
            area: {
                entry.module: sorted(entry.covered)
                for entry in report.files if entry.area == area
            }
            for area in AREA_PATHS
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return payload


def load_budget(path: Path) -> dict[str, object]:
    if not path.is_file():
        raise FileNotFoundError(
            f"no coverage budget at {path}; run `coverage-gate --update-budget` "
            "after the deterministic suites pass"
        )
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != BUDGET_SCHEMA:
        raise ValueError(
            f"unsupported coverage budget schema: {payload.get('schema')!r}"
        )
    return payload


def evaluate(
    report: CoverageReport,
    budget: Mapping[str, object] | None = None,
    *,
    minimum_percent: Mapping[str, float] | None = None,
) -> CoverageGateResult:
    """Evaluate the drift gate against a budget and optional per-area floors.

    Every budgeted line that the fresh run no longer covers is an error (the
    line became dead code, or its deterministic test lost the path — both
    need a decision, not silence).  ``minimum_percent`` (area name -> percent)
    adds a floor so a new area cannot start empty.
    """
    errors: list[str] = []
    by_module = {entry.module: entry for entry in report.files}
    if budget is not None:
        areas = budget.get("areas") or {}
        assert isinstance(areas, dict)
        for area, modules in areas.items():
            assert isinstance(modules, dict)
            for module, lines in modules.items():
                current = by_module.get(module)
                covered = set(current.covered) if current is not None else set()
                lost = sorted(set(int(line) for line in lines) - covered)
                if lost:
                    errors.append(
                        f"{module}: {len(lost)} budgeted line(s) lost: "
                        + ", ".join(str(line) for line in lost[:10])
                        + (" ..." if len(lost) > 10 else "")
                    )
    totals: dict[str, tuple[int, int]] = {}
    for area in AREA_PATHS:
        totals[area] = report.area_total(area)
    for area, floor in (minimum_percent or {}).items():
        covered, statements = totals.get(area, (0, 0))
        percent = 100.0 * covered / statements if statements else 0.0
        if percent < floor:
            errors.append(
                f"{area}: {percent:.2f}% covered ({covered}/{statements} "
                f"statements), below the {floor:.2f}% floor"
            )
    return CoverageGateResult(
        passed=not errors, errors=tuple(errors), report=report,
    )


def report_payload(
    result: CoverageGateResult,
    *,
    minimum_percent: Mapping[str, float] | None = None,
    budget_path: str | None = None,
) -> dict[str, object]:
    report = result.report
    return {
        "schema": "mordheim-combat-coverage/v1",
        "passed": result.passed,
        "errors": result.errors,
        "suites": report.suites,
        "seconds": report.seconds,
        "budget": budget_path,
        "minimum_percent": dict(minimum_percent or {}),
        "areas": {
            area: {"covered": covered, "statements": statements,
                   "percent": round(100.0 * covered / statements, 2)
                   if statements else 100.0}
            for area, (covered, statements) in {
                area: report.area_total(area) for area in AREA_PATHS
            }.items()
        },
        "files": tuple(asdict(item) for item in report.files),
    }

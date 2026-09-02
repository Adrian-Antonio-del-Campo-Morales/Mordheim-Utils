"""Excel-friendly human reports for semantic parity and technical tests."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable


from mordheim_combat_lab.cli.benchmarking import benchmark_scenarios
from mordheim_combat.vectorized import available_backends
from mordheim_construction.compiler import compile_fighter
from mordheim_combat_lab.verification.parity import CONSTRUCTION_SPEC_OPERATIONS
from mordheim_combat_lab.verification.parity import compare_statistical_parity
from mordheim_combat_lab.verification.parity import verify_specification_parity
from mordheim_combat_lab.verification.scenarios import check_case
from mordheim_combat_lab.verification.specifications import load_fixtures
from mordheim_knowledge.loader import knowledge_root


SEMANTIC_COLUMNS = (
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


def _expected(case: dict) -> dict[str, object]:
    result: dict[str, object] = {}
    for key in ("expect", "expect_contains", "distribution", "reject"):
        if key in case:
            result[key] = case[key]
    return result


def _overall(*statuses: str) -> str:
    if any(status in {"FAIL", "DIVERGENCE", "ERROR"} for status in statuses):
        return "FAIL"
    if statuses and all(status == "OUT_OF_SCOPE" for status in statuses):
        return "OUT_OF_SCOPE"
    if any(status in {"PENDING_ADAPTER", "PENDING_SEMANTIC", "NOT_AVAILABLE"} for status in statuses):
        return "PENDING"
    return "PASS"


def semantic_report_rows(*, statistical: bool = False, simulations: int = 100_000,
                         seed: int = 2026) -> list[dict[str, object]]:
    root = knowledge_root()
    parity = verify_specification_parity(root)
    indexed = {(item.specification, item.case): item for item in parity.cases}
    native_available = "native" in available_backends()
    rows: list[dict[str, object]] = []
    for specification in load_fixtures():
        sources = " | ".join(str(source["target"]) for source in specification.get("sources", ()))
        for case in specification.get("cases", ()):
            item = indexed[(str(specification["id"]), str(case["id"]))]
            construction = item.operation in CONSTRUCTION_SPEC_OPERATIONS
            base = {
                "test_id": f"{item.specification}/{item.case}",
                "specification": item.specification,
                "case": item.case,
                "category": specification.get("category", ""),
                "operation": item.operation,
                "layer": "construction" if construction else "combat",
                "source_targets": sources,
                "rules": sources,
                "roles": " | ".join(str(role) for role in case.get("roles", ())),
                "interpretation": specification.get("interpretation", ""),
                "expected": _json(_expected(case)),
                "rng_mode": "distribution" if "distribution" in case else "fixed" if case.get("rolls") else "deterministic",
                "shared_status": "NOT_APPLICABLE", "shared_result": "", "shared_detail": "",
                "modular_status": "", "modular_result": "", "modular_detail": "",
                "numpy_status": "", "numpy_result": "", "numpy_detail": "",
                "native_status": "", "native_result": "", "native_detail": "",
                "details": "",
            }
            if item.status == "OUT_OF_SCOPE":
                for engine in ("shared", "modular", "numpy", "native"):
                    base[f"{engine}_status"] = "OUT_OF_SCOPE"
                base["passes"] = "OUT_OF_SCOPE"
                base["details"] = "Rule excluded by the declared runtime scope."
                rows.append(base)
                continue
            if item.adapter == "semantic-pending":
                base["modular_status"] = base["numpy_status"] = base["native_status"] = "PENDING_SEMANTIC"
                base["modular_detail"] = item.detail
                base["passes"] = "PENDING"
                base["details"] = item.detail
                rows.append(base)
                continue
            try:
                observed = check_case(case, root)
            except Exception as error:
                base["modular_status"] = "FAIL"
                base["modular_detail"] = str(error)
                observed = None
            else:
                base["modular_status"] = "PASS_SHARED" if construction else "PASS"
                base["modular_result"] = _json(observed)
            if construction:
                base["shared_status"] = "PASS" if observed is not None else "FAIL"
                base["shared_result"] = base["modular_result"]
                for engine in ("numpy", "native"):
                    base[f"{engine}_status"] = "PASS_SHARED" if observed is not None else "FAIL"
                    base[f"{engine}_result"] = base["modular_result"]
            else:
                base["numpy_status"] = item.status
                base["numpy_detail"] = item.detail
                if item.status == "PASS":
                    base["numpy_result"] = base["modular_result"]
                base["native_status"] = "PENDING_ADAPTER" if native_available else "NOT_AVAILABLE"
                if not native_available:
                    base["native_detail"] = "native combat backend is not available"
            base["passes"] = _overall(
                str(base["shared_status"]), str(base["modular_status"]),
                str(base["numpy_status"]), str(base["native_status"]),
            )
            details = tuple(
                f"{engine}: {base[f'{engine}_detail']}"
                for engine in ("shared", "modular", "numpy", "native")
                if base.get(f"{engine}_detail")
            )
            base["details"] = " | ".join(details)
            rows.append(base)

    if statistical:
        for scenario in benchmark_scenarios():
            result = compare_statistical_parity(
                scenario.id, compile_fighter(scenario.first), compile_fighter(scenario.second),
                simulations, seed=seed, maximum_rounds=scenario.maximum_rounds,
            )
            modular = {"rates_w_l_u": result.modular_rates, "simulations": simulations}
            numpy = {"rates_w_l_u": result.vectorized_rates, "tolerances": result.tolerances,
                     "simulations": simulations}
            native_status = "PENDING_ADAPTER" if native_available else "NOT_AVAILABLE"
            rows.append({
                "test_id": f"statistical/{scenario.id}", "specification": "statistical",
                "case": scenario.id, "category": "statistical", "operation": "duel",
                "layer": "combat", "source_targets": "", "roles": "aggregate",
                "rules": "",
                "interpretation": "Independent modular and optimized samples satisfy the six-sigma gate.",
                "expected": _json({"minimum_tolerance": 0.0025}), "rng_mode": "statistical",
                "shared_status": "NOT_APPLICABLE", "shared_result": "", "shared_detail": "",
                "modular_status": "PASS", "modular_result": _json(modular), "modular_detail": "",
                "numpy_status": "PASS" if result.passed else "FAIL", "numpy_result": _json(numpy), "numpy_detail": "",
                "native_status": native_status, "native_result": "",
                "native_detail": "" if native_available else "native combat backend is not available",
                "passes": "PENDING" if result.passed else "FAIL",
                "details": "" if native_available else "native: native combat backend is not available",
            })
    return rows


def run_technical_tests(path: Path) -> int:
    environment = dict(__import__("os").environ)
    environment["MORDHEIM_TEST_REPORT_CSV"] = str(path.resolve())
    command = [
        sys.executable, "-m", "pytest", "-p",
        "mordheim_combat_lab.verification.pytest_reporter", "-p", "no:cacheprovider", "-q",
    ]
    try:
        return subprocess.run(command, env=environment, check=False).returncode
    except Exception as error:
        write_csv(path, TECHNICAL_COLUMNS, ({
            "test_id": "pytest/session", "status": "ERROR", "error": str(error), "passes": "FAIL",
        },))
        return 1


def generate_test_report(output: Path, *, statistical: bool = False,
                         simulations: int = 100_000, seed: int = 2026) -> tuple[Path, Path, list[dict[str, object]], int]:
    output = Path(output)
    semantic_path = output / "semantic-parity.csv"
    technical_path = output / "technical-tests.csv"
    try:
        semantic_rows = semantic_report_rows(
            statistical=statistical, simulations=simulations, seed=seed,
        )
    except Exception as error:
        semantic_rows = [{
            "test_id": "report/semantic-generation", "category": "report",
            "operation": "generate", "layer": "infrastructure",
            "modular_status": "ERROR", "modular_detail": str(error), "passes": "FAIL",
        }]
    write_csv(semantic_path, SEMANTIC_COLUMNS, semantic_rows)
    technical_exit = run_technical_tests(technical_path)
    if not technical_path.is_file():
        write_csv(technical_path, TECHNICAL_COLUMNS, ({
            "test_id": "pytest/session", "status": "ERROR",
            "error": "pytest did not create its report", "passes": "FAIL",
        },))
        technical_exit = 1
    return semantic_path, technical_path, semantic_rows, technical_exit

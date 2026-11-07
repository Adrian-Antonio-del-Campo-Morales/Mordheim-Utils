"""Excel-friendly report of the technical test run."""
from __future__ import annotations

import csv
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Iterable




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


_CHECKOUT = Path(__file__).resolve().parents[4]
_PACKAGE_ROOTS = (
    "packages/python/combat-engine", "packages/python/roster-construction",
    "packages/python/core", "packages/python/knowledge", "apps/combat-lab", ".",
)


def _checkout_root() -> Path | None:
    if (_CHECKOUT / "pyproject.toml").is_file() and (_CHECKOUT / "tests").is_dir():
        return _CHECKOUT
    return None


def run_technical_tests(path: Path) -> int:
    """Run the repository's pytest suite and write its technical CSV to ``path``.

    From a source checkout the child runs in that checkout with its package
    roots first on ``PYTHONPATH``: the reporter plugin is imported before
    pytest's ``pythonpath`` setting applies, so it would otherwise resolve
    through whatever editable install the interpreter has.  A CSV left at
    ``path`` by an earlier run is removed first; a CSV that this run did not
    write is reported as missing, never reused.
    """
    import os
    import time

    path = Path(path)
    environment = dict(os.environ)
    environment["MORDHEIM_TEST_REPORT_CSV"] = str(path.resolve())
    checkout = _checkout_root()
    if checkout is not None:
        existing = environment.get("PYTHONPATH")
        environment["PYTHONPATH"] = os.pathsep.join(
            [*(str(checkout / root) for root in _PACKAGE_ROOTS), *([existing] if existing else [])]
        )
    command = [
        sys.executable, "-m", "pytest", "-p",
        "mordheim_combat_lab.verification.pytest_reporter", "-p", "no:cacheprovider", "-q",
    ]
    started = time.time()
    try:
        path.unlink()
        removed = True
    except FileNotFoundError:
        removed = True
    except OSError:  # cannot remove it: only a newer file counts as this run's
        removed = False
    try:
        exit_code = subprocess.run(
            command, env=environment, check=False,
            cwd=None if checkout is None else str(checkout),
        ).returncode
    except Exception as error:
        write_csv(path, TECHNICAL_COLUMNS, ({
            "test_id": "pytest/session", "status": "ERROR", "error": str(error), "passes": "FAIL",
        },))
        return 1
    produced = path.is_file() and (removed or path.stat().st_mtime > started)
    if not produced:
        write_csv(path, TECHNICAL_COLUMNS, ({
            "test_id": "pytest/session", "status": "ERROR",
            "error": f"pytest did not create its report (exit status {exit_code})",
            "passes": "FAIL",
        },))
        return exit_code or 1
    return exit_code


def generate_test_report(output: Path) -> tuple[Path, int]:
    """Run the technical tests; return the CSV path and pytest's exit status."""
    technical_path = Path(output) / "technical-tests.csv"
    return technical_path, run_technical_tests(technical_path)

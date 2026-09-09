"""Naming helpers for generated reports."""

from datetime import datetime
from pathlib import Path


def execution_stamp() -> str:
    """Return a filesystem-safe local execution timestamp."""
    return datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")


def timestamped_report_path(directory: Path, stem: str, suffix: str) -> Path:
    """Build a unique report path for runs that did not choose one explicitly."""
    return Path(directory) / f"{stem}-{execution_stamp()}{suffix}"

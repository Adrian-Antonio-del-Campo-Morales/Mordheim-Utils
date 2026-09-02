"""Localización de recursos; nunca depende del directorio de trabajo."""
from pathlib import Path
import sys


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").is_file():
            return parent
    raise FileNotFoundError("No se encontró el proyecto; indica una ruta explícita de recursos.")

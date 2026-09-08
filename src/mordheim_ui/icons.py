from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path


_CACHE: dict[tuple[int, str, int], tk.PhotoImage] = {}
_DISPLAY_SCALE = 2.0
_MAX_DISPLAY_SIZE = 42


def _icons_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "sources" / "icons"
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "sources" / "icons"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("sources/icons")


def ui_icon(widget: tk.Misc, name: str, size: int = 20) -> tk.PhotoImage:
    """Load one PNG, enlarged to fill its allotted control without crowding it."""
    key = (id(widget.tk), name, size)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    source = tk.PhotoImage(master=widget, file=str(_icons_root() / f"{name}.png"))
    target = min(_MAX_DISPLAY_SIZE, int(size * _DISPLAY_SCALE))
    factor = max(1, max(source.width(), source.height()) // target)
    image = source.subsample(factor, factor)
    _CACHE[key] = image
    return image

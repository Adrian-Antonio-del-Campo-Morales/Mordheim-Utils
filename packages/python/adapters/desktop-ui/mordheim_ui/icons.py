from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk


_CACHE: dict[tuple[int, str, int], ImageTk.PhotoImage] = {}
_DISPLAY_SCALE = 2.35
_MAX_DISPLAY_SIZE = 48


def _icons_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "sources" / "icons"
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "sources" / "icons"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("sources/icons")


def _render_icon(path: Path, target: int) -> Image.Image:
    """Crop transparent padding and centre the artwork in an exact square."""
    source = Image.open(path).convert("RGBA")
    bounds = source.getchannel("A").getbbox()
    if bounds:
        source = source.crop(bounds)
    source.thumbnail((target, target), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (target, target), (0, 0, 0, 0))
    canvas.alpha_composite(source, ((target - source.width) // 2, (target - source.height) // 2))
    return canvas


def ui_icon(widget: tk.Misc, name: str, size: int = 20) -> ImageTk.PhotoImage:
    """Load one icon with maximum, consistent visual size and alignment."""
    key = (id(widget.tk), name, size)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached
    target = min(_MAX_DISPLAY_SIZE, int(size * _DISPLAY_SCALE))
    image = ImageTk.PhotoImage(_render_icon(_icons_root() / f"{name}.png", target), master=widget)
    _CACHE[key] = image
    return image

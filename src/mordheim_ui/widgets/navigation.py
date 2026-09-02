from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from mordheim_ui.theme import COLORS


class StepProgress(tk.Frame):
    def __init__(self, master: tk.Misc, steps: list[str], active_index: int, completed: set[int] | None = None, on_select: Callable[[int], None] | None = None, **kwargs) -> None:
        super().__init__(master, bg=COLORS["panel_deep"], **kwargs)
        completed = completed or set()
        for index, label in enumerate(steps):
            if index:
                tk.Frame(self, bg=COLORS["border_soft"], height=1, width=18).pack(side="left", padx=2)
            state = "✓" if index in completed else str(index + 1)
            fg = COLORS["success"] if index in completed else (COLORS["accent"] if index == active_index else COLORS["muted"])
            style = "Mini.TButton"
            text = f"{state}  {label.upper()}"
            btn = ttk.Button(self, text=text, style=style, command=(lambda i=index: on_select(i)) if on_select else None)
            btn.pack(side="left", padx=2, pady=5)
            # Tiny semantic underline, clearer than relying on ttk state colors.
            if index == active_index:
                marker = tk.Frame(self, bg=COLORS["accent"], width=2, height=22)
                marker.pack(side="left", padx=(0, 2), pady=8)

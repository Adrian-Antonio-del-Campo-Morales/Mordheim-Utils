from __future__ import annotations

import tkinter as tk

from mordheim_ui.theme import COLORS


class BeforeAfterMetric(tk.Frame):
    def __init__(self, master: tk.Misc, title: str, before: str, after: str | None = None, delta: str | None = None, **kwargs) -> None:
        super().__init__(master, bg=COLORS["panel"], **kwargs)
        tk.Label(self, text=title.upper(), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
        value = before if after is None else f"{before}  →  {after}"
        tk.Label(self, text=value, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 12)).pack(anchor="w", pady=(4, 0))
        if delta:
            positive = not delta.startswith("-")
            tk.Label(self, text=delta, bg=COLORS["panel"], fg=COLORS["success"] if positive else COLORS["danger"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(2, 0))


class MetricStrip(tk.Frame):
    def __init__(self, master: tk.Misc, metrics: list[tuple[str, str, str | None, str | None]], **kwargs) -> None:
        super().__init__(master, bg=COLORS["panel"], **kwargs)
        for index, (title, before, after, delta) in enumerate(metrics):
            if index:
                tk.Frame(self, bg=COLORS["border_soft"], width=1).grid(row=0, column=index * 2 - 1, sticky="ns", pady=8)
            box = BeforeAfterMetric(self, title, before, after, delta)
            box.grid(row=0, column=index * 2, sticky="nsew", padx=14, pady=8)
            self.columnconfigure(index * 2, weight=1)

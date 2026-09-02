from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from collections.abc import Callable, Iterable

from mordheim_ui.theme import COLORS


class PageHeader(tk.Frame):
    """Compact page heading with optional supporting text and primary action."""

    def __init__(
        self,
        master: tk.Misc,
        title: str,
        subtitle: str | None = None,
        *,
        action_text: str | None = None,
        action: Callable[[], None] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        text = tk.Frame(self, bg=COLORS["bg"])
        text.pack(side="left", fill="x", expand=True)
        tk.Label(text, text=title, bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 16)).pack(anchor="w")
        if subtitle:
            tk.Label(
                text,
                text=subtitle,
                bg=COLORS["bg"],
                fg=COLORS["muted"],
                font=("Segoe UI", 9),
            ).pack(anchor="w", pady=(3, 0))
        if action_text and action:
            ttk.Button(self, text=action_text, style="Accent.TButton", command=action).pack(side="right", padx=(12, 0))


class SegmentedTabs(tk.Frame):
    """Small, low-noise secondary navigation for sibling views."""

    def __init__(
        self,
        master: tk.Misc,
        items: Iterable[tuple[str, str]],
        active: str,
        on_select: Callable[[str], None],
        **kwargs,
    ) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        for key, label in items:
            selected = key == active
            button = tk.Button(
                self,
                text=label,
                command=lambda value=key: on_select(value),
                bg=COLORS["panel_deep"] if selected else COLORS["bg"],
                fg=COLORS["accent"] if selected else COLORS["muted"],
                activebackground=COLORS["panel_soft"],
                activeforeground=COLORS["text"],
                relief="flat",
                bd=0,
                highlightthickness=0,
                padx=14,
                pady=8,
                font=("Segoe UI Semibold", 8),
                cursor="hand2",
            )
            button.pack(side="left", padx=(0, 2))


class SummaryStrip(tk.Frame):
    """Small persistent summary. Avoids turning every view into a dashboard."""

    def __init__(self, master: tk.Misc, items: Iterable[tuple[str, str]], **kwargs) -> None:
        super().__init__(master, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["border_soft"], **kwargs)
        for index, (label, value) in enumerate(items):
            if index:
                tk.Frame(self, bg=COLORS["border_soft"], width=1).pack(side="left", fill="y", pady=9)
            cell = tk.Frame(self, bg=COLORS["panel"], padx=16, pady=8)
            cell.pack(side="left", fill="x", expand=True)
            tk.Label(cell, text=label.upper(), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 7)).pack(anchor="w")
            tk.Label(cell, text=value, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 11)).pack(anchor="w", pady=(2, 0))


class InlineNotice(tk.Frame):
    def __init__(
        self,
        master: tk.Misc,
        text: str,
        *,
        action_text: str | None = None,
        action: Callable[[], None] | None = None,
        tone: str = "accent",
        **kwargs,
    ) -> None:
        super().__init__(master, bg=COLORS["panel_deep"], highlightthickness=1, highlightbackground=COLORS["border_soft"], **kwargs)
        fg = COLORS.get(tone, COLORS["accent"])
        tk.Label(self, text=text, bg=COLORS["panel_deep"], fg=fg, font=("Segoe UI Semibold", 8), padx=12).pack(side="left", pady=8)
        if action_text and action:
            ttk.Button(self, text=action_text, style="Mini.TButton", command=action).pack(side="right", padx=8, pady=5)

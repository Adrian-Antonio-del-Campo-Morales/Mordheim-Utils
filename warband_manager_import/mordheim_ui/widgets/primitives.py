from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from mordheim_ui.theme import COLORS


class BorderedFrame(tk.Frame):
    def __init__(self, master: tk.Misc, *, background: str | None = None, padding: int = 1, **kwargs) -> None:
        super().__init__(master, bg=COLORS["border"], bd=0, highlightthickness=0, **kwargs)
        self.body = tk.Frame(self, bg=background or COLORS["panel"], bd=0, highlightthickness=0)
        self.body.pack(fill="both", expand=True, padx=padding, pady=padding)


class ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Misc, *, background: str | None = None, **kwargs) -> None:
        super().__init__(master, style="App.TFrame", **kwargs)
        bg = background or COLORS["bg"]
        self.canvas = tk.Canvas(self, background=bg, highlightthickness=0, bd=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self.window_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.inner.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self.window_id, width=e.width))
        self.canvas.bind("<Enter>", lambda _e: self._bind_mousewheel())
        self.canvas.bind("<Leave>", lambda _e: self._unbind_mousewheel())

    def _bind_mousewheel(self) -> None:
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda _e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda _e: self.canvas.yview_scroll(1, "units"))

    def _unbind_mousewheel(self) -> None:
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event: tk.Event) -> None:
        self.canvas.yview_scroll(int(-event.delta / 120), "units")


class SectionBox(BorderedFrame):
    def __init__(self, master: tk.Misc, title: str, *, action_text: str | None = None, action: Callable[[], None] | None = None, **kwargs) -> None:
        super().__init__(master, background=COLORS["panel"], padding=1, **kwargs)
        header = tk.Frame(self.body, bg=COLORS["panel_deep"], height=35)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text=title.upper(), bg=COLORS["panel_deep"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8), padx=10).pack(side="left", fill="y")
        if action_text and action:
            ttk.Button(header, text=action_text, style="Mini.TButton", command=action).pack(side="right", padx=6, pady=5)
        self.content = tk.Frame(self.body, bg=COLORS["panel"])
        self.content.pack(fill="both", expand=True)


class Divider(tk.Frame):
    def __init__(self, master: tk.Misc, **kwargs) -> None:
        super().__init__(master, bg=COLORS["border_soft"], height=1, **kwargs)


class EmptyState(tk.Frame):
    def __init__(self, master: tk.Misc, title: str, detail: str, **kwargs) -> None:
        super().__init__(master, bg=COLORS["panel"], **kwargs)
        tk.Label(self, text=title, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 13)).pack(pady=(36, 6))
        tk.Label(self, text=detail, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack()

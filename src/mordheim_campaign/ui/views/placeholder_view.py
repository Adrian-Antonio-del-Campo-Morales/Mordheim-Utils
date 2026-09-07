from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, PageHeader
from mordheim_ui.i18n import tr


class SettingsView(tk.Frame):
    def __init__(self, master: tk.Misc, controller, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.columnconfigure(0, weight=1)
        PageHeader(self, tr('Settings'), tr('Campaign preferences, ruleset selection and presentation options.')).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        box = BorderedFrame(self, background=COLORS["panel"], padding=1)
        box.grid(row=1, column=0, sticky="ew")
        body = box.body
        body.configure(padx=18, pady=18)
        rows = ((tr('Language'), tr('English')), (tr('Ruleset'), tr('Mordheim core + enabled sources')), (tr('Enabled sources'), tr('Core / Official')), (tr('Appearance'), tr('Dark')))
        for label, value in rows:
            row = tk.Frame(body, bg=COLORS["panel"], pady=7)
            row.pack(fill="x")
            tk.Label(row, text=label.upper(), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left")
            tk.Label(row, text=value, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(side="right")

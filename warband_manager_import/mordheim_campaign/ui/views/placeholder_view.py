from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, PageHeader


class RulesView(tk.Frame):
    def __init__(self, master: tk.Misc, controller, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        PageHeader(self, "Rules", "Search and browse the Mordheim knowledge base without campaign-management clutter.").grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search = ttk.Entry(self)
        search.insert(0, "Search rules, skills, equipment, scenarios…")
        search.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        box = BorderedFrame(self, background=COLORS["panel"], padding=1)
        box.grid(row=2, column=0, sticky="nsew")
        body = box.body
        body.configure(padx=18, pady=18)
        tk.Label(body, text="BROWSE", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 10))
        for text in ("Warbands", "Skills", "Equipment", "Special Rules", "Scenarios", "Campaign Rules"):
            ttk.Button(body, text=f"{text}  ›", style="Mini.TButton").pack(anchor="w", fill="x", pady=3)


class SettingsView(tk.Frame):
    def __init__(self, master: tk.Misc, controller, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.columnconfigure(0, weight=1)
        PageHeader(self, "Settings", "Campaign preferences, ruleset selection and presentation options.").grid(row=0, column=0, sticky="ew", pady=(0, 10))
        box = BorderedFrame(self, background=COLORS["panel"], padding=1)
        box.grid(row=1, column=0, sticky="ew")
        body = box.body
        body.configure(padx=18, pady=18)
        rows = (("Language", "English"), ("Ruleset", "Mordheim core + enabled sources"), ("Enabled sources", "Core / Official"), ("Appearance", "Dark"))
        for label, value in rows:
            row = tk.Frame(body, bg=COLORS["panel"], pady=7)
            row.pack(fill="x")
            tk.Label(row, text=label.upper(), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left")
            tk.Label(row, text=value, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(side="right")

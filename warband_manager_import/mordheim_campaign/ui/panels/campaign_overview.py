from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import SectionBox, Divider


class CampaignOverviewPanel(SectionBox):
    def __init__(self, master: tk.Misc, controller: AppController, **kwargs) -> None:
        super().__init__(master, "Campaign overview", **kwargs)
        self.controller = controller
        c = controller.state.campaign

        hero = tk.Frame(self.content, bg=COLORS["panel"], padx=14, pady=14)
        hero.pack(fill="x")
        emblem = tk.Canvas(hero, width=64, height=88, bg=COLORS["panel_deep"], bd=0, highlightthickness=1, highlightbackground=COLORS["border"])
        emblem.pack(side="left", padx=(0, 12))
        emblem.create_oval(18, 10, 46, 38, outline=COLORS["accent"], width=2)
        emblem.create_line(32, 38, 32, 72, fill=COLORS["accent"], width=2)
        emblem.create_line(15, 52, 49, 52, fill=COLORS["accent"], width=2)
        text = tk.Frame(hero, bg=COLORS["panel"])
        text.pack(side="left", fill="both", expand=True)
        tk.Label(text, text=c.warband_name, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 13), wraplength=150, justify="left").pack(anchor="w")
        tk.Label(text, text=c.warband_type, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 10))
        tk.Label(text, text=f"Started {c.started}", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
        tk.Label(text, text=f"Current battle  #{c.current_battle}", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", pady=(3, 0))

        Divider(self.content).pack(fill="x")
        metrics = [
            ("Gold crowns", f"{c.gold} gc", "◉"),
            ("Wyrdstone shards", str(c.wyrdstone), "◇"),
            ("Warband rating", str(c.rating), "✥"),
            ("Models", f"{c.models} / {c.max_models}", "♙"),
            ("Heroes", f"{c.heroes} / {c.max_heroes}", "♜"),
            ("Henchmen", str(c.henchmen), "♟"),
            ("Experience", str(c.experience), "★"),
        ]
        for label, value, icon in metrics:
            row = tk.Frame(self.content, bg=COLORS["panel"], padx=13, pady=9)
            row.pack(fill="x")
            tk.Label(row, text=icon, bg=COLORS["panel"], fg=COLORS["accent"], font=("Georgia", 15), width=3).pack(side="left")
            info = tk.Frame(row, bg=COLORS["panel"])
            info.pack(side="left", fill="x", expand=True)
            tk.Label(info, text=label.upper(), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 7)).pack(anchor="w")
            tk.Label(info, text=value, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 11)).pack(anchor="w", pady=(2, 0))
            Divider(self.content).pack(fill="x")

        ttk.Button(self.content, text="VIEW CAMPAIGN  ›", command=lambda: controller.navigate("campaign")).pack(fill="x", padx=12, pady=12)

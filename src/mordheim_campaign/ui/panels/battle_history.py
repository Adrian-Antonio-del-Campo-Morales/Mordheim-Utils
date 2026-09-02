from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import SectionBox, Divider


class BattleHistoryPanel(SectionBox):
    def __init__(self, master: tk.Misc, controller: AppController, *, compact: bool = False, **kwargs) -> None:
        super().__init__(master, "Battle history", **kwargs)
        self.controller = controller
        battles = controller.state.campaign.battles
        shown = battles[:6] if compact else battles
        for battle in shown:
            row = tk.Frame(self.content, bg=COLORS["panel"], padx=11, pady=9, cursor="hand2")
            row.pack(fill="x")
            top = tk.Frame(row, bg=COLORS["panel"])
            top.pack(fill="x")
            tk.Label(top, text=f"#{battle.number}", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(side="left")
            tk.Label(top, text=battle.date, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left", padx=8)
            result_color = COLORS["success"] if battle.result.lower() == "victory" else COLORS["danger"]
            tk.Label(top, text=battle.result, bg=COLORS["panel"], fg=result_color, font=("Georgia", 10)).pack(side="right")
            tk.Label(row, text=f"{battle.scenario} vs. {battle.opponent}", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(5, 3))
            stats = f"◉ {battle.gold_delta:+d}    ◇ +{battle.wyrdstone}    ★ +{battle.xp_delta}    ☠ {battle.casualties}    ↑ {battle.advances}"
            tk.Label(row, text=stats, bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI", 8), anchor="w").pack(fill="x")
            for widget in (row, top):
                widget.bind("<Button-1>", lambda _e, n=battle.number: controller.select_battle(n))
            Divider(self.content).pack(fill="x")
        ttk.Button(self.content, text="VIEW BATTLE DETAILS  ›", command=lambda: controller.navigate("campaign")).pack(fill="x", padx=12, pady=12)

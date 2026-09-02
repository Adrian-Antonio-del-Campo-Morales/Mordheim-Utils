from __future__ import annotations

import tkinter as tk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, MetricStrip


class WarbandStatusPanel(BorderedFrame):
    def __init__(self, master: tk.Misc, controller: AppController, **kwargs) -> None:
        super().__init__(master, background=COLORS["panel"], padding=1, **kwargs)
        c = controller.state.campaign
        header = tk.Frame(self.body, bg=COLORS["panel_deep"], height=34)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="WARBAND STATUS", bg=COLORS["panel_deep"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8), padx=10).pack(side="left", fill="y")
        last = c.battles[0]
        color = COLORS["success"] if last.result.lower() == "victory" else COLORS["danger"]
        tk.Label(header, text=f"LAST BATTLE: {last.result.upper()}  ·  {last.scenario} vs. {last.opponent}", bg=COLORS["panel_deep"], fg=color, font=("Segoe UI Semibold", 8), padx=10).pack(side="right", fill="y")
        metrics = [
            ("Gold crowns", str(c.gold_before), str(c.gold), f"+{c.gold - c.gold_before}"),
            ("Wyrdstone", str(c.wyrdstone_before), str(c.wyrdstone), f"+{c.wyrdstone - c.wyrdstone_before}"),
            ("Warband rating", str(c.rating_before), str(c.rating), f"+{c.rating - c.rating_before}"),
            ("Models", str(c.models_before), str(c.models), str(c.models - c.models_before)),
            ("Experience", str(c.experience_before), str(c.experience), f"+{c.experience - c.experience_before}"),
        ]
        MetricStrip(self.body, metrics).pack(fill="x")

from __future__ import annotations

import tkinter as tk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, SummaryStrip


class CampaignStatistics(tk.Frame):
    def __init__(self, master: tk.Misc, controller: AppController, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        c = controller.state.campaign
        committed = [b for b in c.battles if b.number <= c.current_state_number]
        tk.Label(self, text="CAMPAIGN STATISTICS", bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 16)).pack(anchor="w", pady=(2, 4))
        tk.Label(self, text="Aggregates live outside the sequence; the Timeline remains the default way to understand what happened and when.", bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 10))
        SummaryStrip(self, [("Battles", str(len(committed))), ("Victories", str(sum(1 for b in committed if b.result.lower() == "victory"))), ("Current rating", str(c.current_state.rating)), ("Current models", str(c.current_state.models))]).pack(fill="x", pady=(0, 10))
        box = BorderedFrame(self, background=COLORS["panel"], padding=1); box.pack(fill="x")
        body = box.body; body.configure(padx=18, pady=16)
        tk.Label(body, text="RATING PROGRESSION", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(body, text="  →  ".join(str(state.rating) for state in c.states), bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 11), wraplength=900, justify="left").pack(anchor="w", pady=(10, 0))

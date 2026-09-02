from __future__ import annotations

import tkinter as tk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, SegmentedTabs, SummaryStrip


class BattleMoment(tk.Frame):
    """One table battle: facts only, separated from post-battle consequences."""

    def __init__(self, master: tk.Misc, controller: AppController, number: int, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        battle = controller.state.campaign.battle(number)
        self.columnconfigure(0, weight=1); self.rowconfigure(3, weight=1)

        top = tk.Frame(self, bg=COLORS["bg"]); top.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        tk.Label(top, text=f"BATTLE #{battle.number}", bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 16)).pack(side="left")
        result_color = COLORS["success"] if battle.result.lower() == "victory" else COLORS["danger"]
        tk.Label(top, text=battle.result.upper(), bg=COLORS["bg"], fg=result_color, font=("Segoe UI Semibold", 9)).pack(side="left", padx=10)
        tk.Label(self, text=f"{battle.scenario} · vs. {battle.opponent} · {battle.date}", bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=(0, 8))

        nav = tk.Frame(self, bg=COLORS["bg"]); nav.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        SegmentedTabs(nav, (("overview", "OVERVIEW"), ("participants", "PARTICIPANTS"), ("notes", "NOTES")), controller.state.battle_section, controller.set_battle_section).pack(side="left")
        if battle.number <= controller.state.campaign.current_state_number:
            tk.Button(nav, text="RESULTING STATE ›", command=lambda: controller.select_state(battle.number), bg=COLORS["panel_soft"], fg=COLORS["text"], relief="flat", padx=9, pady=5).pack(side="right")
        tk.Button(nav, text="POST-BATTLE", command=lambda: controller.select_post_battle(battle.number), bg=COLORS["panel_soft"], fg=COLORS["text"], relief="flat", padx=9, pady=5).pack(side="right", padx=(0, 6))

        section = controller.state.battle_section
        content = self._participants(battle) if section == "participants" else self._notes(battle) if section == "notes" else self._overview(battle)
        content.grid(row=3, column=0, sticky="nsew")

    def _overview(self, battle) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"]); frame.columnconfigure(0, weight=1)
        SummaryStrip(frame, [("Warband rating", str(battle.rating_before)), ("Opponent rating", str(battle.opponent_rating or "—")), ("Models deployed", str(battle.models_before)), ("Result", battle.result)]).pack(fill="x", pady=(0, 10))
        box = BorderedFrame(frame, background=COLORS["panel"], padding=1); box.pack(fill="x")
        body = box.body; body.configure(padx=18, pady=16)
        tk.Label(body, text="WHAT HAPPENED ON THE TABLE", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(body, text="Battle records contain table facts only. Injury rolls, experience, exploration and trading belong to the Post-Battle node that follows this battle.", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9), wraplength=820, justify="left").pack(anchor="w", pady=(8, 12))
        tk.Label(body, text=f"Out of Action / casualties recorded: {battle.casualties}", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(anchor="w", pady=2)
        return frame

    def _participants(self, battle) -> BorderedFrame:
        box = BorderedFrame(self, background=COLORS["panel"], padding=1); body = box.body; body.configure(padx=18, pady=16)
        tk.Label(body, text="PARTICIPANTS", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 8))
        for warrior in self.controller.state.campaign.warriors:
            row = tk.Frame(body, bg=COLORS["panel"], pady=5); row.pack(fill="x")
            tk.Label(row, text=warrior.name, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(side="left")
            status = "Out of Action" if warrior.id == "marta" and battle.number in (7, 8) else "Participated"
            tk.Label(row, text=status, bg=COLORS["panel"], fg=COLORS["danger"] if status == "Out of Action" else COLORS["muted"], font=("Segoe UI", 8)).pack(side="right")
        return box

    def _notes(self, battle) -> BorderedFrame:
        box = BorderedFrame(self, background=COLORS["panel"], padding=1); body = box.body; body.configure(padx=18, pady=16)
        tk.Label(body, text="BATTLE NOTES", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(body, text=battle.notes or "No notes were recorded for this battle.", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9), wraplength=820, justify="left").pack(anchor="w", pady=(10, 0))
        return box

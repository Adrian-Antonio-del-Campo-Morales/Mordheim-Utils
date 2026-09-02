from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.ui.panels import InventoryWorkspace, WarriorCard
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, ScrollableFrame, SegmentedTabs, SummaryStrip


class WarbandStateMoment(tk.Frame):
    """Read or edit one immutable/active warband state from the timeline."""

    def __init__(self, master: tk.Misc, controller: AppController, number: int, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        self.number = number
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        c = controller.state.campaign
        state = c.state(number)
        current = number == c.current_state_number

        top = tk.Frame(self, bg=COLORS["bg"])
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        title = "CURRENT WARBAND" if current else ("INITIAL WARBAND" if number == 0 else f"WARBAND STATE #{number}")
        tk.Label(top, text=title, bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 16)).pack(side="left")
        if not current:
            tk.Label(top, text="HISTORICAL · READ ONLY", bg=COLORS["panel_deep"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7), padx=8, pady=4).pack(side="left", padx=10)
        else:
            ttk.Button(top, text="EDIT WARBAND", command=self._placeholder).pack(side="right")

        subtitle = "Campaign starting point" if number == 0 else f"After Battle #{number} · {state.date}"
        tk.Label(self, text=subtitle, bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=(0, 8))

        nav = tk.Frame(self, bg=COLORS["bg"])
        nav.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        SegmentedTabs(
            nav,
            (("overview", "OVERVIEW"), ("warriors", "WARRIORS"), ("inventory", "INVENTORY")),
            controller.state.state_section,
            controller.set_state_section,
        ).pack(side="left")
        if not current:
            if number > 0:
                ttk.Button(nav, text="‹ PREVIOUS STATE", style="Mini.TButton", command=lambda: controller.select_state(number - 1)).pack(side="right")
            if number < c.current_state_number:
                ttk.Button(nav, text="NEXT STATE ›", style="Mini.TButton", command=lambda: controller.select_state(number + 1)).pack(side="right", padx=(0, 6))

        if controller.state.state_section == "warriors":
            content = self._warriors(read_only=not current)
        elif controller.state.state_section == "inventory":
            content = InventoryWorkspace(self, controller, show_summary=False, read_only=not current)
        else:
            content = self._overview(state, current)
        content.grid(row=3, column=0, sticky="nsew")

    def _overview(self, state, current: bool) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"])
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)
        SummaryStrip(
            frame,
            [("Rating", str(state.rating)), ("Models", f"{state.models}/{state.max_models}"), ("Treasury", f"{state.gold} gc"), ("Wyrdstone", str(state.wyrdstone))],
        ).grid(row=0, column=0, sticky="ew", pady=(0, 10))

        body = tk.Frame(frame, bg=COLORS["bg"])
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)

        composition = BorderedFrame(body, background=COLORS["panel"], padding=1)
        composition.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        cb = composition.body; cb.configure(padx=18, pady=16)
        tk.Label(cb, text="WARBAND AT THIS POINT", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        for label, value in (("Heroes", str(state.heroes)), ("Henchmen", str(state.henchmen)), ("Total experience", str(state.experience))):
            row = tk.Frame(cb, bg=COLORS["panel"], pady=7); row.pack(fill="x")
            tk.Label(row, text=label, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(side="left")
            tk.Label(row, text=value, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 11)).pack(side="right")

        context = BorderedFrame(body, background=COLORS["panel"], padding=1)
        context.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        xb = context.body; xb.configure(padx=18, pady=16)
        if current:
            pending = self.controller.state.campaign.pending_post_battle
            tk.Label(xb, text="CAMPAIGN POSITION", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
            if pending:
                battle = self.controller.state.campaign.battle(pending.battle_number)
                tk.Label(xb, text=f"Battle #{battle.number} is complete", bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 12)).pack(anchor="w", pady=(10, 3))
                tk.Label(xb, text=f"{battle.scenario} vs. {battle.opponent} · {battle.result}", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w")
                tk.Label(xb, text=f"Post-battle is at step {pending.active_step + 1}/7. State #{pending.battle_number} does not exist yet.", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9), wraplength=430, justify="left").pack(anchor="w", pady=(8, 12))
                tk.Label(xb, text="Select the Post-Battle #8 node in the timeline, or use the Resume action above.", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8), wraplength=430, justify="left").pack(anchor="w")
            else:
                tk.Label(xb, text="No pending actions.", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 12))
                ttk.Button(xb, text="+ NEW BATTLE", style="Accent.TButton", command=self._placeholder).pack(anchor="w")
        else:
            tk.Label(xb, text="THIS STATE IN THE TIMELINE", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
            text = "This is the immutable starting point from which the campaign begins." if state.number == 0 else f"This snapshot was created when Post-Battle #{state.number} was committed. Open the adjacent transition nodes to see why the warband changed."
            tk.Label(xb, text=text, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9), wraplength=430, justify="left").pack(anchor="w", pady=(10, 12))
            if state.number > 0:
                ttk.Button(xb, text=f"VIEW POST-BATTLE #{state.number}", command=lambda: self.controller.select_post_battle(state.number)).pack(anchor="w")
        return frame

    def _warriors(self, read_only: bool) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"])
        frame.columnconfigure(0, weight=1); frame.rowconfigure(0, weight=1)
        scroll = ScrollableFrame(frame, background=COLORS["bg"]); scroll.grid(row=0, column=0, sticky="nsew")
        for warrior in self.controller.state.campaign.warriors:
            WarriorCard(scroll.inner, warrior, on_edit=(None if read_only else self._placeholder)).pack(fill="x", pady=(0, 7))
        return frame

    def _placeholder(self) -> None:
        messagebox.showinfo("Prototype", "This control is intentionally visual-only in the timeline-first prototype.", parent=self)

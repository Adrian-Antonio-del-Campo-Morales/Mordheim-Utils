from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, Divider, ExperienceTrack, PageHeader, StepProgress, SummaryStrip


STEPS = ["Battle", "Injuries", "Experience", "Advances", "Exploration", "Trading", "Review"]


class PostBattleView(tk.Frame):
    """A single-task wizard: only the current post-battle decision is visible."""

    def __init__(self, master: tk.Misc, controller: AppController, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        PageHeader(
            self,
            f"Post-Battle · Battle #{controller.state.campaign.current_battle}",
            "Resolve the battle in order. The current roster remains unchanged until Review is confirmed.",
            action_text="SAVE & CLOSE",
            action=self._placeholder,
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))

        StepProgress(
            self,
            STEPS,
            controller.state.post_battle_step,
            controller.state.post_battle_completed,
            controller.set_post_battle_step,
        ).grid(row=1, column=0, sticky="w", pady=(0, 8))

        step = controller.state.post_battle_step
        status_text = f"{step + 1} of {len(STEPS)} · {STEPS[step]}"
        tk.Label(self, text=status_text.upper(), bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8)).grid(row=2, column=0, sticky="w", pady=(0, 6))

        container = tk.Frame(self, bg=COLORS["bg"])
        container.grid(row=3, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, minsize=980, weight=0)
        container.columnconfigure(2, weight=1)
        container.rowconfigure(0, weight=1)
        self._step_panel(container).grid(row=0, column=1, sticky="nsew")

        self._actions().grid(row=4, column=0, sticky="ew", pady=(8, 0))

    def _step_panel(self, parent: tk.Misc) -> BorderedFrame:
        box = BorderedFrame(parent, background=COLORS["panel"], padding=1)
        body = box.body
        body.configure(padx=18, pady=16)
        handlers = (
            self._battle_step,
            self._injuries_step,
            self._experience_step,
            self._advances_step,
            self._exploration_step,
            self._trading_step,
            self._review_step,
        )
        handlers[self.controller.state.post_battle_step](body)
        return box

    def _actions(self) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"])
        step = self.controller.state.post_battle_step
        if step > 0:
            ttk.Button(frame, text="‹ BACK", command=lambda: self.controller.set_post_battle_step(step - 1)).pack(side="left")
        if step < len(STEPS) - 1:
            ttk.Button(frame, text="CONTINUE ›", style="Accent.TButton", command=lambda: self.controller.set_post_battle_step(step + 1)).pack(side="right")
        else:
            ttk.Button(frame, text="FINISH POST-BATTLE", style="Accent.TButton", command=self._placeholder).pack(side="right")
        return frame

    def _title(self, parent: tk.Misc, title: str, detail: str) -> None:
        tk.Label(parent, text=title, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 15)).pack(anchor="w")
        tk.Label(parent, text=detail, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9), wraplength=880, justify="left").pack(anchor="w", pady=(4, 16))

    def _battle_step(self, parent: tk.Misc) -> None:
        self._title(parent, "Battle result", "Record what happened on the table. The application will derive rule effects later; this screen only captures facts.")
        form = tk.Frame(parent, bg=COLORS["panel"])
        form.pack(fill="x")
        fields = (("Scenario", "Skirmish"), ("Opponent", "Possessed"), ("Result", "Victory"))
        for row, (label, value) in enumerate(fields):
            tk.Label(form, text=label.upper(), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).grid(row=row, column=0, sticky="w", pady=7)
            entry = ttk.Entry(form, width=42)
            entry.insert(0, value)
            entry.grid(row=row, column=1, sticky="ew", padx=(14, 0), pady=7)
        form.columnconfigure(1, weight=1)
        Divider(parent).pack(fill="x", pady=16)
        tk.Label(parent, text="OUT OF ACTION", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 6))
        for warrior in self.controller.state.campaign.warriors:
            row = tk.Frame(parent, bg=COLORS["panel"], pady=4)
            row.pack(fill="x")
            tk.Checkbutton(row, bg=COLORS["panel"], activebackground=COLORS["panel"], selectcolor=COLORS["entry"]).pack(side="left")
            tk.Label(row, text=warrior.name, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(side="left", padx=4)

    def _injuries_step(self, parent: tk.Misc) -> None:
        self._title(parent, "Injuries", "Only warriors that require an injury roll are shown here.")
        self._result_card(parent, "Sister Superior Marta", "Hero · Out of Action", "D66  24", "LEG WOUND", "M -1")
        self._result_card(parent, "Novices", "Henchmen · 1 member Out of Action", "D6  1", "DEAD", "Group size 3 → 2")

    def _experience_step(self, parent: tk.Misc) -> None:
        self._title(parent, "Experience", "Review the reasons for each award. Manual adjustment stays available for unusual campaign rules.")
        for warrior in self.controller.state.campaign.warriors[:4]:
            card = tk.Frame(parent, bg=COLORS["panel_alt"], padx=12, pady=10)
            card.pack(fill="x", pady=(0, 7))
            top = tk.Frame(card, bg=COLORS["panel_alt"])
            top.pack(fill="x")
            tk.Label(top, text=warrior.name, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Georgia", 11)).pack(side="left")
            before = warrior.previous_experience if warrior.previous_experience is not None else warrior.experience
            tk.Label(top, text=f"XP {before} → {warrior.experience}", bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(side="right")
            reasons = "Survived +1   ·   Scenario / objectives +1   ·   Enemy OoA +1" if warrior.id == "matriarch" else "Survived +1   ·   Scenario / objectives +1"
            tk.Label(card, text=reasons, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(5, 5))
            ExperienceTrack(card, warrior.experience, previous_experience=before, track_type="hero").pack(fill="x")

    def _advances_step(self, parent: tk.Misc) -> None:
        self._title(parent, "Advances", "Only models that crossed an advancement threshold need attention.")
        self._choice_card(parent, "Mother Superior", "Advancement roll: 7", "Choose a new skill", ["Combat", "Academic", "Strength", "Special"])
        self._choice_card(parent, "Sigmarite Sisters", "Advancement roll: 6", "Choose a characteristic", ["+1 WS", "+1 BS"])

    def _exploration_step(self, parent: tk.Misc) -> None:
        self._title(parent, "Exploration", "Roll in the app or enter physical dice; both workflows should be equally comfortable.")
        info = tk.Frame(parent, bg=COLORS["panel_alt"], padx=14, pady=14)
        info.pack(fill="x")
        tk.Label(info, text="ELIGIBLE HEROES   4", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        dice = tk.Frame(info, bg=COLORS["panel_alt"])
        dice.pack(anchor="w", pady=14)
        for value in (3, 3, 5, 6):
            tk.Label(dice, text=str(value), width=3, bg=COLORS["panel_deep"], fg=COLORS["accent"], relief="solid", bd=1, font=("Georgia", 16), padx=8, pady=8).pack(side="left", padx=(0, 8))
        tk.Label(info, text="4 wyrdstone found   ·   Special result: Double 3", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(anchor="w")
        ttk.Button(info, text="ROLL / ENTER DICE", command=self._placeholder).pack(anchor="w", pady=(12, 0))

    def _trading_step(self, parent: tk.Misc) -> None:
        self._title(parent, "Trading", "This is a transaction step, not a second inventory manager. Purchases go to the stash unless assigned later.")
        SummaryStrip(parent, [("Treasury", "72 gc"), ("Wyrdstone", "4 shards"), ("Purchases", "27 gc"), ("After trading", "45 gc")]).pack(fill="x", pady=(0, 14))
        tabs = tk.Frame(parent, bg=COLORS["panel"])
        tabs.pack(fill="x", pady=(0, 10))
        for index, label in enumerate(("BUY", "SELL", "RECRUIT")):
            tk.Label(tabs, text=label, bg=COLORS["panel_deep"] if index == 0 else COLORS["panel"], fg=COLORS["accent"] if index == 0 else COLORS["muted"], padx=14, pady=7, font=("Segoe UI Semibold", 8)).pack(side="left")
        market = tk.Frame(parent, bg=COLORS["panel_alt"], padx=12, pady=10)
        market.pack(fill="x")
        for name, price in (("Sigmarite Warhammer", 15), ("Light Armour", 20), ("Hammer", 3), ("Sword", 10)):
            row = tk.Frame(market, bg=COLORS["panel_alt"], pady=5)
            row.pack(fill="x")
            tk.Label(row, text=name, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(side="left")
            ttk.Button(row, text=f"BUY · {price} gc", style="Mini.TButton", command=self._placeholder).pack(side="right")

    def _review_step(self, parent: tk.Misc) -> None:
        self._title(parent, "Review", "A concise diff of the campaign state. Nothing is committed until the player confirms it.")
        SummaryStrip(parent, [("Rating", "174 → 183"), ("Models", "9 → 8"), ("Treasury", "34 → 72 gc"), ("Wyrdstone", "1 → 4")]).pack(fill="x", pady=(0, 14))
        sections = [
            ("CASUALTIES", ["Novice Greta — Dead", "Sister Superior Marta — Leg Wound (M -1)"]),
            ("EXPERIENCE", ["Mother Superior 20 → 23", "Sister Superior Anna 17 → 19", "Novices 3 → 4"]),
            ("ADVANCES", ["Mother Superior — +1 WS", "Sigmarite Sisters — +1 A"]),
            ("ECONOMY", ["4 wyrdstone", "Treasury 34 → 72 gc"]),
        ]
        for title, lines in sections:
            tk.Label(parent, text=title, bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(7, 3))
            for line in lines:
                tk.Label(parent, text=f"• {line}", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(anchor="w", padx=(8, 0), pady=1)

    def _result_card(self, parent: tk.Misc, name: str, subtitle: str, roll: str, result: str, effect: str) -> None:
        card = tk.Frame(parent, bg=COLORS["panel_alt"], padx=12, pady=10)
        card.pack(fill="x", pady=(0, 8))
        top = tk.Frame(card, bg=COLORS["panel_alt"])
        top.pack(fill="x")
        tk.Label(top, text=name, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Georgia", 11)).pack(side="left")
        tk.Label(top, text=roll, bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(side="right")
        tk.Label(card, text=subtitle, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 7))
        tk.Label(card, text=f"{result}  ·  {effect}", bg=COLORS["panel_alt"], fg=COLORS["danger"], font=("Segoe UI Semibold", 9)).pack(anchor="w")

    def _choice_card(self, parent: tk.Misc, name: str, roll: str, result: str, choices: list[str]) -> None:
        card = tk.Frame(parent, bg=COLORS["panel_alt"], padx=12, pady=11)
        card.pack(fill="x", pady=(0, 8))
        tk.Label(card, text=name, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Georgia", 11)).pack(anchor="w")
        tk.Label(card, text=f"{roll}  →  {result}", bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(3, 9))
        row = tk.Frame(card, bg=COLORS["panel_alt"])
        row.pack(fill="x")
        for choice in choices:
            ttk.Button(row, text=choice, style="Mini.TButton", command=self._placeholder).pack(side="left", padx=(0, 6))

    def _placeholder(self) -> None:
        messagebox.showinfo("Prototype", "The GUI flow is implemented; campaign rules/actions are intentionally placeholders for now.", parent=self)

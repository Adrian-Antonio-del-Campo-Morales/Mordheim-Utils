from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.state import STAT_KEYS, WarriorVM
from mordheim_campaign.ui.dialogs import AddWarriorDialog
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, ExperienceTrack, ScrollableFrame, SegmentedTabs, SummaryStrip


class InitialWarbandDraftMoment(tk.Frame):
    """Construction workspace for the campaign's State #0.

    The dense roster-sheet language is kept because construction is the one
    task where characteristics, equipment, rules and XP genuinely belong in
    the same visual context. Editing controls live behind explicit actions.
    """

    def __init__(self, master: tk.Misc, controller: AppController, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        self.campaign = controller.state.campaign
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        self._build_heading().grid(row=0, column=0, sticky="ew", pady=(0, 8))
        SummaryStrip(
            self,
            [
                ("Gold Crowns", f"{self.campaign.draft_treasury} gc"),
                ("Warband Rating", str(self.campaign.draft_rating)),
                ("Models", f"{self.campaign.draft_model_count}/{self.campaign.maximum_models}"),
                ("Heroes", f"{self.campaign.draft_hero_count}/{self.campaign.hero_limit}"),
            ],
        ).grid(row=1, column=0, sticky="ew", pady=(0, 8))
        self._build_roster_toolbar().grid(row=2, column=0, sticky="ew", pady=(0, 8))
        self._build_roster().grid(row=3, column=0, sticky="nsew")
        self._build_footer().grid(row=4, column=0, sticky="ew", pady=(8, 0))

    def _build_heading(self) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"])
        text = tk.Frame(frame, bg=COLORS["bg"])
        text.pack(side="left", fill="x", expand=True)
        line = tk.Frame(text, bg=COLORS["bg"])
        line.pack(anchor="w")
        tk.Label(line, text="INITIAL WARBAND", bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 16)).pack(side="left")
        tk.Label(line, text="DRAFT", bg=COLORS["panel_deep"], fg=COLORS["accent"], font=("Segoe UI Semibold", 7), padx=8, pady=4).pack(side="left", padx=(10, 0))
        tk.Label(text, text="Build the warband that will become the campaign's immutable starting state.", bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 0))

        identity = tk.Frame(frame, bg=COLORS["bg"])
        identity.pack(side="right", padx=(14, 0))
        tk.Label(identity, text=self.campaign.warband_type.upper(), bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8)).pack(anchor="e")
        tk.Label(identity, text=self.campaign.warband_name, bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 11)).pack(anchor="e", pady=(2, 0))
        return frame

    def _build_roster_toolbar(self) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"])
        tab = self.controller.state.draft_warrior_tab
        hero_count = self.campaign.draft_hero_count
        hench_count = self.campaign.draft_henchman_count
        SegmentedTabs(
            frame,
            (("hero", f"HEROES  {hero_count}/{self.campaign.hero_limit}"), ("henchman", f"HENCHMEN  {hench_count}")),
            tab,
            self.controller.set_draft_warrior_tab,
        ).pack(side="left")
        action = "+ ADD HERO" if tab == "hero" else "+ ADD HENCHMAN GROUP"
        ttk.Button(frame, text=action, style="Accent.TButton", command=self._open_add_warrior).pack(side="right")
        return frame

    def _open_add_warrior(self) -> None:
        AddWarriorDialog(self, self.controller, kind=self.controller.state.draft_warrior_tab)

    def _build_roster(self) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"])
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        scroll = ScrollableFrame(frame, background=COLORS["bg"])
        scroll.grid(row=0, column=0, sticky="nsew")
        kind = self.controller.state.draft_warrior_tab
        warriors = [w for w in self.campaign.warriors if w.kind == kind]
        if not warriors:
            empty = BorderedFrame(scroll.inner, background=COLORS["panel"], padding=1)
            empty.pack(fill="x")
            body = empty.body
            body.configure(height=230)
            body.pack_propagate(False)
            label = "No heroes yet" if kind == "hero" else "No henchman groups yet"
            tk.Label(body, text=label, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 13)).pack(pady=(58, 6))
            tk.Label(body, text="Pick a canonical profile from the warband roster to begin.", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack()
            ttk.Button(
                body,
                text=("+ ADD FIRST HERO" if kind == "hero" else "+ ADD FIRST GROUP"),
                style="Accent.TButton",
                command=self._open_add_warrior,
            ).pack(pady=(12, 0))
            return frame
        for warrior in warriors:
            DraftWarriorCard(scroll.inner, warrior, on_edit=self._placeholder, on_more=self._warrior_menu(warrior)).pack(fill="x", pady=(0, 8))
        return frame

    def _build_footer(self) -> tk.Frame:
        outer = BorderedFrame(self, background=COLORS["panel_deep"], padding=1)
        body = outer.body
        body.configure(padx=14, pady=11)

        metrics = tk.Frame(body, bg=COLORS["panel_deep"])
        metrics.pack(side="left", fill="y")
        values = (
            ("MODELS", f"{self.campaign.draft_model_count}/{self.campaign.maximum_models}"),
            ("RECRUITMENT", f"{self.campaign.draft_recruitment_cost} gc"),
            ("EQUIPMENT", f"{self.campaign.draft_equipment_cost} gc"),
            ("TREASURY", f"{self.campaign.draft_treasury} gc"),
        )
        for index, (label, value) in enumerate(values):
            if index:
                tk.Frame(metrics, bg=COLORS["border_soft"], width=1).pack(side="left", fill="y", padx=12)
            cell = tk.Frame(metrics, bg=COLORS["panel_deep"])
            cell.pack(side="left")
            tk.Label(cell, text=value, bg=COLORS["panel_deep"], fg=COLORS["text"], font=("Georgia", 11)).pack(anchor="w")
            tk.Label(cell, text=label, bg=COLORS["panel_deep"], fg=COLORS["muted_dark"], font=("Segoe UI Semibold", 7)).pack(anchor="w", pady=(2, 0))

        actions = tk.Frame(body, bg=COLORS["panel_deep"])
        actions.pack(side="right", fill="y")
        checks = tk.Frame(actions, bg=COLORS["panel_deep"])
        checks.pack(side="left", padx=(0, 18))
        conditions = (
            (self.campaign.draft_hero_count >= 1, "Leader / hero present"),
            (self.campaign.draft_model_count >= self.campaign.minimum_models, f"Minimum {self.campaign.minimum_models} models reached"),
            (self.campaign.draft_treasury >= 0, "Within starting treasury"),
        )
        for ok, text in conditions:
            tk.Label(checks, text=("✓ " if ok else "! ") + text, bg=COLORS["panel_deep"], fg=COLORS["success"] if ok else COLORS["danger"], font=("Segoe UI Semibold", 8), anchor="w").pack(anchor="w", pady=1)

        start = ttk.Button(actions, text="START CAMPAIGN", style="Accent.TButton", command=self.controller.commit_initial_warband)
        start.pack(side="left", pady=2)
        if not self.campaign.draft_is_legal:
            start.state(["disabled"])
        return outer

    def _warrior_menu(self, warrior: WarriorVM):
        """Menu contextual de fila: tamaño de grupo y eliminación del borrador."""

        def popup() -> None:
            menu = tk.Menu(
                self,
                tearoff=False,
                bg=COLORS["panel"],
                fg=COLORS["text"],
                activebackground=COLORS["panel_soft"],
                activeforeground=COLORS["text"],
            )
            if warrior.kind == "henchman":
                menu.add_command(label="+ 1 member", command=lambda: self._adjust_group(warrior, 1))
                menu.add_command(label="− 1 member", command=lambda: self._adjust_group(warrior, -1))
                menu.add_separator()
            menu.add_command(label="Remove from draft", command=lambda: self._remove_warrior(warrior))
            try:
                menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
            finally:
                menu.grab_release()

        return popup

    def _adjust_group(self, warrior: WarriorVM, delta: int) -> None:
        ok, message = self.controller.adjust_draft_group(warrior.id, delta)
        if not ok:
            messagebox.showerror("Cannot resize group", message, parent=self)

    def _remove_warrior(self, warrior: WarriorVM) -> None:
        ok, message = self.controller.remove_draft_warrior(warrior.id)
        if not ok:
            messagebox.showerror("Cannot remove warrior", message, parent=self)

    def _placeholder(self) -> None:
        messagebox.showinfo("Prototype", "Per-warrior equipment and skill editing arrives with the campaign rules engine.", parent=self)


class DraftWarriorCard(tk.Frame):
    def __init__(self, master: tk.Misc, warrior: WarriorVM, *, on_edit, on_more, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.warrior = warrior
        border = BorderedFrame(self, background=COLORS["panel_alt"], padding=1)
        border.pack(fill="x")
        card = border.body

        header = tk.Frame(card, bg=COLORS["panel_alt"], padx=13, pady=8)
        header.pack(fill="x")
        identity = tk.Frame(header, bg=COLORS["panel_alt"])
        identity.pack(side="left", fill="x", expand=True)
        tk.Label(identity, text=warrior.name.upper(), bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Georgia", 11)).pack(anchor="w")
        sub = warrior.profile_name
        if warrior.kind == "henchman":
            sub += f"  ·  {warrior.quantity} member{'s' if warrior.quantity != 1 else ''}"
        tk.Label(identity, text=sub, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))

        tools = tk.Frame(header, bg=COLORS["panel_alt"])
        tools.pack(side="right")
        total = warrior.cost * warrior.quantity + warrior.equipment_cost * warrior.quantity
        tk.Label(tools, text=f"{total} gc", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Georgia", 10)).pack(side="left", padx=(0, 12))
        ttk.Button(tools, text="EDIT", style="Mini.TButton", command=on_edit).pack(side="left")
        ttk.Button(tools, text="…", style="Mini.TButton", command=on_more, width=3).pack(side="left", padx=(5, 0))

        tk.Frame(card, bg=COLORS["border_soft"], height=1).pack(fill="x")
        body = tk.Frame(card, bg=COLORS["panel"], height=174)
        body.pack(fill="x")
        body.pack_propagate(False)
        body.columnconfigure(0, weight=36, uniform="draft-card")
        body.columnconfigure(1, weight=28, uniform="draft-card")
        body.columnconfigure(2, weight=36, uniform="draft-card")
        body.rowconfigure(0, weight=1)

        self._stats(body).grid(row=0, column=0, sticky="nsew")
        self._equipment(body).grid(row=0, column=1, sticky="nsew", padx=(1, 1))
        self._skills(body).grid(row=0, column=2, sticky="nsew")

        tk.Frame(card, bg=COLORS["border_soft"], height=1).pack(fill="x")
        xp = tk.Frame(card, bg=COLORS["panel"], padx=12, pady=6)
        xp.pack(fill="x")
        info = tk.Frame(xp, bg=COLORS["panel"], width=90)
        info.pack(side="left")
        tk.Label(info, text="EXPERIENCE", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).pack(anchor="w")
        tk.Label(info, text=str(warrior.experience), bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 10)).pack(anchor="w", pady=(1, 0))
        ExperienceTrack(xp, warrior.experience, track_type="hero" if warrior.kind == "hero" else "henchman").pack(side="left", fill="x", expand=True, padx=(10, 0))

    def _section(self, master: tk.Misc, title: str) -> tuple[tk.Frame, tk.Frame]:
        outer = tk.Frame(master, bg=COLORS["panel"])
        head = tk.Frame(outer, bg=COLORS["panel_deep"], height=28)
        head.pack(fill="x")
        head.pack_propagate(False)
        tk.Label(head, text=title, bg=COLORS["panel_deep"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7), padx=9).pack(side="left", fill="y")
        content = tk.Frame(outer, bg=COLORS["panel"], padx=9, pady=8)
        content.pack(fill="both", expand=True)
        return outer, content

    def _stats(self, master: tk.Misc) -> tk.Frame:
        outer, content = self._section(master, "CHARACTERISTICS")
        grid = tk.Frame(content, bg=COLORS["panel"])
        grid.pack(fill="x", pady=(4, 0))
        for col, key in enumerate(STAT_KEYS):
            grid.columnconfigure(col, weight=1, uniform="stats")
            tk.Label(grid, text=key, bg=COLORS["black"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7), pady=4).grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 1, 0))
            tk.Label(grid, text=str(self.warrior.stats.get(key, "-")), bg=COLORS["panel_soft"], fg=COLORS["text"], font=("Georgia", 9), pady=7).grid(row=1, column=col, sticky="ew", padx=(0 if col == 0 else 1, 0), pady=(1, 0))
        mods = [(key, value) for key, value in self.warrior.stat_modifiers.items() if value]
        text = "Modifiers: none" if not mods else "Modifiers: " + "  ·  ".join(f"{k} {v:+d}" for k, v in mods)
        tk.Label(content, text=text, bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(anchor="w", pady=(10, 0))
        return outer

    def _equipment(self, master: tk.Misc) -> tk.Frame:
        outer, content = self._section(master, "EQUIPMENT")
        lines = self.warrior.equipment or ["None"]
        for line in lines[:5]:
            tk.Label(content, text=line, bg=COLORS["panel"], fg=COLORS["muted"] if line == "None" else COLORS["text"], font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=2)
        return outer

    def _skills(self, master: tk.Misc) -> tk.Frame:
        outer, content = self._section(master, "SKILLS / RULES")
        lines = self.warrior.skills or ["None"]
        for line in lines[:4]:
            tk.Label(content, text=line, bg=COLORS["panel"], fg=COLORS["muted"] if line == "None" else COLORS["text"], font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=2)
        if self.warrior.skill_access:
            tk.Label(content, text="SKILL ACCESS", bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI Semibold", 7)).pack(anchor="w", pady=(8, 3))
            tk.Label(content, text="  ·  ".join(self.warrior.skill_access), bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI", 8), anchor="w", wraplength=320, justify="left").pack(fill="x")
        return outer

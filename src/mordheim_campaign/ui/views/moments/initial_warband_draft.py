from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_ui import themed_dialogs as messagebox
from mordheim_ui import themed_dialogs as simpledialog

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.state import STAT_KEYS, WarriorVM
from mordheim_campaign.ui.equipment_display import equipment_quantity_suffix
from mordheim_campaign.ui.dialogs import AddWarriorDialog, HireSwordDialog
from mordheim_campaign.ui.panels import InventoryWorkspace
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, ExperienceTrack, ScrollableFrame, SegmentedTabs
from mordheim_ui.i18n import tr
from mordheim_ui.icons import ui_icon


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

        self._build_summary_bar().grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self._build_heading().grid(row=1, column=0, sticky="ew", pady=(0, 6))
        self._build_roster_toolbar().grid(row=2, column=0, sticky="ew", pady=(0, 6))
        self._build_roster().grid(row=3, column=0, sticky="nsew")

    def _build_heading(self) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"])
        text = tk.Frame(frame, bg=COLORS["bg"])
        text.pack(side="left", fill="x", expand=True)
        line = tk.Frame(text, bg=COLORS["bg"])
        line.pack(anchor="w")
        tk.Label(line, text=tr('INITIAL WARBAND'), bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 14)).pack(side="left")
        tk.Label(line, text=tr('DRAFT'), bg=COLORS["panel_deep"], fg=COLORS["accent"], font=("Segoe UI Semibold", 7), padx=6, pady=2).pack(side="left", padx=(8, 0))
        tk.Label(text, text=tr("Build the warband that will become the campaign's immutable starting state."), bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))

        identity = tk.Frame(frame, bg=COLORS["bg"])
        identity.pack(side="right", padx=(14, 0))
        tk.Label(identity, text=self.campaign.warband_type.upper(), bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8)).pack(anchor="e")
        tk.Label(identity, text=self.campaign.warband_name, bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 11)).pack(anchor="e", pady=(2, 0))
        return frame

    def _build_roster_toolbar(self) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"])
        tab = self.controller.state.draft_warrior_tab
        SegmentedTabs(
            frame,
            (
                ("hero", tr('HEROES')),
                ("henchman", tr('HENCHMEN')),
                ("hireling", tr('HIRED SWORDS')),
                ("inventory", tr('INVENTORY')),
            ),
            tab,
            self.controller.set_draft_warrior_tab,
            prominent=True,
        ).pack(side="left")
        if tab == "hireling":
            ttk.Button(frame, text=tr('HIRE SWORD'), image=ui_icon(self, "campaign_warband_recruit", 20), compound="left", style="Accent.TButton", command=lambda: HireSwordDialog(self, self.controller)).pack(side="right")
        elif tab != "inventory":
            action = tr('ADD HERO') if tab == "hero" else tr('ADD HENCHMEN GROUP')
            icon = "campaign_warband_add_hero" if tab == "hero" else "campaign_warband_add_henchmen"
            ttk.Button(frame, text=action, image=ui_icon(self, icon, 20), compound="left", style="Accent.TButton", command=self._open_add_warrior).pack(side="right")
        return frame

    def _open_add_warrior(self) -> None:
        AddWarriorDialog(self, self.controller, kind=self.controller.state.draft_warrior_tab)

    def _build_roster(self) -> tk.Frame:
        if self.controller.state.draft_warrior_tab == "inventory":
            return InventoryWorkspace(self, self.controller, show_summary=False)
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
            label = tr('No heroes yet') if kind == "hero" else (tr('No Hired Swords yet') if kind == "hireling" else tr('No henchman groups yet'))
            tk.Label(body, text=label, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 13)).pack(pady=(58, 6))
            tk.Label(body, text=tr('Pick a canonical profile from the warband roster to begin.'), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack()
            if kind == "hireling":
                ttk.Button(body, text=tr('HIRE SWORD'), image=ui_icon(self, "campaign_warband_recruit", 20), compound="left", style="Accent.TButton", command=lambda: HireSwordDialog(self, self.controller)).pack(pady=(12, 0))
            else:
                ttk.Button(
                    body,
                    text=(tr('ADD FIRST HERO') if kind == "hero" else tr('ADD FIRST GROUP')),
                    image=ui_icon(self, "campaign_warband_add_hero" if kind == "hero" else "campaign_warband_add_henchmen", 20),
                    compound="left",
                    style="Accent.TButton",
                    command=self._open_add_warrior,
                ).pack(pady=(12, 0))
            return frame
        for warrior in warriors:
            DraftWarriorCard(
                scroll.inner,
                warrior,
                on_more=self._warrior_menu(warrior),
            ).pack(fill="x", pady=(0, 8))
        return frame

    def _build_summary_bar(self) -> tk.Frame:
        outer = BorderedFrame(self, background=COLORS["panel_deep"], padding=1)
        body = outer.body
        body.configure(padx=10, pady=7)

        metrics = tk.Frame(body, bg=COLORS["panel_deep"])
        metrics.pack(fill="x")
        values = (
            (tr('TREASURY'), f"{self.campaign.draft_treasury} gc"),
            (tr('RECRUITMENT'), f"{self.campaign.draft_recruitment_cost} gc"),
            (tr('EQUIPMENT'), f"{self.campaign.draft_equipment_cost} gc"),
            (tr('RATING'), str(self.campaign.draft_rating)),
            (tr('MODELS'), f"{self.campaign.draft_warband_member_count}/{self.campaign.effective_maximum_models}"),
            (tr('HEROES'), f"{self.campaign.draft_hero_count}/{self.campaign.hero_limit}"),
        )
        for index, (label, value) in enumerate(values):
            if index:
                tk.Frame(metrics, bg=COLORS["border_soft"], width=1).pack(side="left", fill="y", padx=8)
            cell = tk.Frame(metrics, bg=COLORS["panel_deep"])
            cell.pack(side="left")
            tk.Label(cell, text=value, bg=COLORS["panel_deep"], fg=COLORS["text"], font=("Georgia", 10)).pack(anchor="w")
            tk.Label(cell, text=label, bg=COLORS["panel_deep"], fg=COLORS["muted_dark"], font=("Segoe UI Semibold", 6)).pack(anchor="w", pady=(1, 0))

        actions = tk.Frame(body, bg=COLORS["panel_deep"])
        actions.pack(fill="x", pady=(6, 0))
        checks = tk.Frame(actions, bg=COLORS["panel_deep"])
        checks.pack(side="left")
        conditions = (
            (self.campaign.draft_hero_count >= 1, tr('Leader / hero present')),
            (self.campaign.draft_warband_member_count >= self.campaign.minimum_models, tr('Minimum {} models reached').format(self.campaign.minimum_models)),
            (self.campaign.draft_treasury >= 0, tr('Within starting treasury')),
        )
        for index, (ok, text) in enumerate(conditions):
            tk.Label(
                checks,
                text=("✓ " if ok else "! ") + text,
                bg=COLORS["panel_deep"],
                fg=COLORS["success"] if ok else COLORS["danger"],
                font=("Segoe UI Semibold", 7),
            ).pack(side="left", padx=(0 if index == 0 else 12, 0))

        return outer

    def _warrior_menu(self, warrior: WarriorVM):
        """Row context menu: group size and draft removal."""

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
                menu.add_command(label=tr('+ 1 member'), command=lambda: self._adjust_group(warrior, 1))
                menu.add_command(label=tr('− 1 member'), command=lambda: self._adjust_group(warrior, -1))
                menu.add_separator()
            menu.add_command(label=tr('Rename…'), command=lambda: self._rename_warrior(warrior))
            if warrior.kind != "hireling":
                menu.add_command(label=tr('Edit skills…'), command=lambda: self._edit_skills(warrior))
            menu.add_command(label=tr('Remove from draft'), command=lambda: self._remove_warrior(warrior))
            try:
                menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
            finally:
                menu.grab_release()

        return popup

    def _edit_skills(self, warrior) -> None:
        from mordheim_campaign.ui.dialogs.manual_management import ManualSkillsDialog
        ManualSkillsDialog(self, self.controller, warrior)

    def _adjust_group(self, warrior: WarriorVM, delta: int) -> None:
        ok, message = self.controller.perform_undoable(
            tr('Resize henchman group'), lambda: self.controller.adjust_draft_group(warrior.id, delta))
        if not ok:
            messagebox.showerror(tr('Cannot resize group'), message, parent=self)

    def _remove_warrior(self, warrior: WarriorVM) -> None:
        ok, message = self.controller.perform_undoable(
            tr('Dismiss warrior'), lambda: self.controller.remove_draft_warrior(warrior.id))
        if not ok:
            messagebox.showerror(tr('Cannot remove warrior'), message, parent=self)

    def _rename_warrior(self, warrior: WarriorVM) -> None:
        name = simpledialog.askstring(tr('Rename'), tr('New name'), initialvalue=warrior.name, parent=self)
        if name is None:
            return
        ok, message = self.controller.perform_undoable(
            tr('Rename warrior'), lambda: self.controller.rename_draft_warrior(warrior.id, name))
        if not ok:
            messagebox.showerror(tr('Cannot rename'), message, parent=self)

class DraftWarriorCard(tk.Frame):
    def __init__(self, master: tk.Misc, warrior: WarriorVM, *, on_more, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.warrior = warrior
        border = BorderedFrame(self, background=COLORS["panel_alt"], padding=1)
        border.pack(fill="x")
        card = border.body

        body = tk.Frame(card, bg=COLORS["panel"], height=184)
        body.pack(fill="x")
        body.pack_propagate(False)
        body.columnconfigure(0, weight=36, uniform="draft-card")
        body.columnconfigure(1, weight=28, uniform="draft-card")
        body.columnconfigure(2, weight=36, uniform="draft-card")
        body.rowconfigure(0, weight=1)

        self._identity_stats(body, on_more).grid(row=0, column=0, sticky="nsew")
        self._equipment(body).grid(row=0, column=1, sticky="nsew", padx=(1, 1))
        self._skills(body).grid(row=0, column=2, sticky="nsew")

        tk.Frame(card, bg=COLORS["border_soft"], height=1).pack(fill="x")
        footer = tk.Frame(card, bg=COLORS["panel"], padx=12, pady=6)
        footer.pack(fill="x")
        footer.columnconfigure(0, weight=36, uniform="draft-footer")
        footer.columnconfigure(2, weight=64, uniform="draft-footer")

        access = tk.Frame(footer, bg=COLORS["panel"])
        access.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        tk.Label(access, text=tr('SKILL ACCESS'), bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI Semibold", 7)).pack(side="left", padx=(0, 10))
        tk.Label(
            access, text="  ·  ".join(warrior.skill_access) if warrior.skill_access else "—",
            bg=COLORS["panel"], fg=COLORS["accent"] if warrior.skill_access else COLORS["muted_dark"],
            font=("Segoe UI", 8), anchor="w", wraplength=360, justify="left",
        ).pack(side="left", fill="x", expand=True)

        info = tk.Frame(footer, bg=COLORS["panel"], width=78)
        info.grid(row=0, column=1, sticky="ns", padx=(0, 10))
        info.grid_propagate(False)
        tk.Label(info, text=tr('EXPERIENCE'), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).pack(anchor="w")
        tk.Label(info, text=str(warrior.experience), bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 10)).pack(anchor="w", pady=(1, 0))
        ExperienceTrack(footer, warrior.experience, track_type="hero" if warrior.kind == "hero" else "henchman").grid(row=0, column=2, sticky="ew")

    def _section(self, master: tk.Misc, title: str) -> tuple[tk.Frame, tk.Frame]:
        outer = tk.Frame(master, bg=COLORS["panel"])
        head = tk.Frame(outer, bg=COLORS["panel_deep"], height=28)
        head.pack(fill="x")
        head.pack_propagate(False)
        tk.Label(head, text=title, bg=COLORS["panel_deep"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7), padx=9).pack(side="left", fill="y")
        content = tk.Frame(outer, bg=COLORS["panel"], padx=9, pady=8)
        content.pack(fill="both", expand=True)
        return outer, content

    def _identity_stats(self, master: tk.Misc, on_more) -> tk.Frame:
        outer = tk.Frame(master, bg=COLORS["panel"])
        header = tk.Frame(outer, bg=COLORS["panel_alt"], padx=13, pady=8)
        header.pack(fill="x")
        identity = tk.Frame(header, bg=COLORS["panel_alt"])
        identity.pack(side="left", fill="x", expand=True)
        tk.Label(identity, text=self.warrior.name.upper(), bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Georgia", 11)).pack(anchor="w")
        sub = self.warrior.profile_name
        if self.warrior.kind == "henchman":
            sub += f"  ·  {self.warrior.quantity} member{'s' if self.warrior.quantity != 1 else ''}"
        tk.Label(identity, text=sub, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))
        tools = tk.Frame(header, bg=COLORS["panel_alt"])
        tools.pack(side="right")
        total = self.warrior.cost * self.warrior.quantity + sum(item.total_cost for item in self.warrior.equipment)
        tk.Label(tools, text=f"{total} gc", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Georgia", 10)).pack(side="left", padx=(0, 12))
        ttk.Button(tools, text="…", style="Mini.TButton", command=on_more, width=3).pack(side="left")

        content = tk.Frame(outer, bg=COLORS["panel"], padx=9, pady=12)
        content.pack(fill="both", expand=True)
        grid = tk.Frame(content, bg=COLORS["panel"])
        grid.pack(fill="x")
        for col, key in enumerate(STAT_KEYS):
            grid.columnconfigure(col, weight=1, uniform="stats")
            tk.Label(grid, text=key, bg=COLORS["black"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7), pady=4).grid(row=0, column=col, sticky="ew", padx=(0 if col == 0 else 1, 0))
            tk.Label(grid, text=str(self.warrior.stats.get(key, "-")), bg=COLORS["panel_soft"], fg=COLORS["text"], font=("Georgia", 9), pady=7).grid(row=1, column=col, sticky="ew", padx=(0 if col == 0 else 1, 0), pady=(1, 0))
        return outer

    def _equipment(self, master: tk.Misc) -> tk.Frame:
        outer, content = self._section(master, tr('EQUIPMENT'))
        lines = [f"{item.name}{equipment_quantity_suffix(self.warrior, item)}" for item in self.warrior.equipment] or ["None"]
        for line in lines[:7]:
            tk.Label(content, text=line, bg=COLORS["panel"], fg=COLORS["muted"] if line == "None" else COLORS["text"], font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=2)
        return outer

    def _skills(self, master: tk.Misc) -> tk.Frame:
        outer, content = self._section(master, tr('SKILLS / RULES'))
        lines = self.warrior.skills or ["None"]
        for line in lines[:7]:
            tk.Label(content, text=line, bg=COLORS["panel"], fg=COLORS["muted"] if line == "None" else COLORS["text"], font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=2)
        return outer

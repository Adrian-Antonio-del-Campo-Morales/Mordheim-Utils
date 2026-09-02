from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.ui.panels import InventoryWorkspace, WarriorCard
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import PageHeader, ScrollableFrame, SegmentedTabs


class RosterView(tk.Frame):
    """Current-state workspace: warriors or inventory, never campaign history."""

    def __init__(self, master: tk.Misc, controller: AppController, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        PageHeader(
            self,
            "Roster",
            "Current warband state. Manage warriors and the equipment the band owns.",
        ).grid(row=0, column=0, sticky="ew", pady=(0, 8))

        nav = tk.Frame(self, bg=COLORS["bg"])
        nav.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        SegmentedTabs(
            nav,
            (("warriors", "WARRIORS"), ("inventory", "INVENTORY")),
            controller.state.roster_section,
            controller.set_roster_section,
        ).pack(side="left")
        if controller.state.roster_section == "warriors":
            ttk.Button(nav, text="EDIT ROSTER", command=self._placeholder).pack(side="right")

        if controller.state.roster_section == "inventory":
            InventoryWorkspace(self, controller).grid(row=2, column=0, sticky="nsew")
        else:
            self._build_warriors().grid(row=2, column=0, sticky="nsew")

    def _build_warriors(self) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"])
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        scroll = ScrollableFrame(frame, background=COLORS["bg"])
        scroll.grid(row=0, column=0, sticky="nsew")

        warriors = self.controller.state.campaign.warriors
        groups = (
            ("HEROES", [w for w in warriors if w.kind == "hero"]),
            ("HENCHMEN", [w for w in warriors if w.kind == "henchman"]),
        )
        for section_index, (title, entries) in enumerate(groups):
            header = tk.Frame(scroll.inner, bg=COLORS["bg"])
            header.pack(fill="x", pady=((0 if section_index == 0 else 13), 7))
            count = sum(w.quantity for w in entries)
            tk.Label(header, text=f"{title}  ({count})", bg=COLORS["bg"], fg=COLORS["text"], font=("Segoe UI Semibold", 10)).pack(side="left")
            ttk.Button(
                header,
                text="+ ADD HERO" if title == "HEROES" else "+ ADD HENCHMAN GROUP",
                style="Mini.TButton",
                command=self._placeholder,
            ).pack(side="right")
            for warrior in entries:
                WarriorCard(scroll.inner, warrior, on_edit=self._placeholder).pack(fill="x", pady=(0, 7))
        return frame

    def _placeholder(self) -> None:
        messagebox.showinfo("Prototype", "This control is intentionally visual-only in the GUI prototype.", parent=self)

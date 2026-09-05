from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, ScrollableFrame, SegmentedTabs, SummaryStrip


def _placeholder(parent: tk.Misc) -> None:
    messagebox.showinfo("Prototype", "This control is visual-only in the interface prototype.", parent=parent)


class InventoryWorkspace(tk.Frame):
    """Focused inventory workspace.

    Resources are summarized, not given a permanent side panel. Assignment is a
    detail action, not another simultaneously visible column. The user chooses
    either an item-centric or warrior-centric representation of the same stock.
    """

    def __init__(self, master: tk.Misc, controller: AppController, *, show_summary: bool = True, read_only: bool = False, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        self.read_only = read_only
        c = controller.state.campaign
        base_row = 0
        if show_summary:
            SummaryStrip(
                self,
                [
                    ("Gold crowns", f"{c.current_state.gold} gc"),
                    ("Wyrdstone", f"{c.current_state.wyrdstone} shards"),
                    ("Inventory", f"{sum(i.owned for i in c.inventory)} items"),
                    ("In stash", f"{sum(i.stash for i in c.inventory)} items"),
                ],
            ).grid(row=0, column=0, sticky="ew", pady=(0, 10))
            base_row = 1
        self.rowconfigure(base_row + 2, weight=1)
        self.columnconfigure(0, weight=1)

        toolbar = tk.Frame(self, bg=COLORS["bg"])
        toolbar.grid(row=base_row, column=0, sticky="ew", pady=(0, 8))
        SegmentedTabs(
            toolbar,
            (("item", "BY ITEM"), ("warrior", "BY WARRIOR")),
            controller.state.inventory_mode,
            controller.set_inventory_mode,
        ).pack(side="left")
        if not read_only:
            ttk.Button(toolbar, text="+ ADD ITEM", command=lambda: _placeholder(self)).pack(side="right")
            ttk.Button(toolbar, text="MANAGE RESOURCES", command=lambda: _placeholder(self)).pack(side="right", padx=(0, 7))

        filters = tk.Frame(self, bg=COLORS["bg"])
        filters.grid(row=base_row + 1, column=0, sticky="ew", pady=(0, 8))
        search = ttk.Entry(filters)
        search.insert(0, "Search inventory…")
        search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        for index, label in enumerate(("ALL", "WEAPONS", "ARMOUR", "MISC", "CONSUMABLES")):
            tk.Label(
                filters,
                text=label,
                bg=COLORS["panel_deep"] if index == 0 else COLORS["bg"],
                fg=COLORS["accent"] if index == 0 else COLORS["muted"],
                padx=9,
                pady=6,
                font=("Segoe UI Semibold", 7),
            ).pack(side="left", padx=(0, 2))

        if controller.state.inventory_mode == "item":
            self._build_by_item().grid(row=base_row + 2, column=0, sticky="nsew")
        else:
            self._build_by_warrior().grid(row=base_row + 2, column=0, sticky="nsew")

    def _build_by_item(self) -> BorderedFrame:
        box = BorderedFrame(self, background=COLORS["panel"], padding=1)
        table = box.body
        table.rowconfigure(1, weight=1)
        table.columnconfigure(0, weight=1)

        head = tk.Frame(table, bg=COLORS["panel_deep"], height=36)
        head.grid(row=0, column=0, sticky="ew")
        head.pack_propagate(False)
        widths = (5, 2, 1, 1, 1, 1)
        cols = ("ITEM", "TYPE", "OWNED", "EQUIPPED", "STASH", "")
        for index, (label, weight) in enumerate(zip(cols, widths)):
            head.columnconfigure(index, weight=weight)
            tk.Label(
                head,
                text=label,
                bg=COLORS["panel_deep"],
                fg=COLORS["muted"],
                font=("Segoe UI Semibold", 7),
                anchor="w" if index < 2 else "center",
                padx=10,
            ).grid(row=0, column=index, sticky="nsew")

        scroll = ScrollableFrame(table, background=COLORS["panel"])
        scroll.grid(row=1, column=0, sticky="nsew")
        for item in self.controller.state.campaign.inventory:
            row = tk.Frame(scroll.inner, bg=COLORS["panel"], height=44, cursor="hand2")
            row.pack(fill="x")
            row.pack_propagate(False)
            for index, weight in enumerate(widths):
                row.columnconfigure(index, weight=weight)
            values = (item.name, item.category, str(item.owned), str(item.equipped), str(item.stash), "•••")
            for index, value in enumerate(values):
                fg = COLORS["text"] if index == 0 else COLORS["muted"]
                tk.Label(
                    row,
                    text=value,
                    bg=COLORS["panel"],
                    fg=fg,
                    font=("Segoe UI", 9 if index == 0 else 8),
                    anchor="w" if index < 2 else "center",
                    padx=10,
                ).grid(row=0, column=index, sticky="nsew")
            for widget in row.winfo_children():
                widget.bind("<Button-1>", lambda _e, name=item.name: self._show_item(name))
            tk.Frame(scroll.inner, bg=COLORS["border_soft"], height=1).pack(fill="x")
        return box

    def _build_by_warrior(self) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"])
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        scroll = ScrollableFrame(frame, background=COLORS["bg"])
        scroll.grid(row=0, column=0, sticky="nsew")
        for warrior in self.controller.state.campaign.warriors:
            card = BorderedFrame(scroll.inner, background=COLORS["panel"], padding=1)
            card.pack(fill="x", pady=(0, 7))
            body = card.body
            body.configure(padx=14, pady=11)
            top = tk.Frame(body, bg=COLORS["panel"])
            top.pack(fill="x")
            tk.Label(top, text=warrior.name, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 11)).pack(side="left")
            tk.Label(top, text=f"{len(warrior.equipment)} items", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left", padx=10)
            ttk.Button(top, text="MANAGE", style="Mini.TButton", command=self._open_editor).pack(side="right")
            tk.Label(
                body,
                text="   •   ".join(warrior.equipment) if warrior.equipment else "No equipment",
                bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8), anchor="w", justify="left",
            ).pack(fill="x", pady=(7, 0))

        stash = BorderedFrame(scroll.inner, background=COLORS["panel"], padding=1)
        stash.pack(fill="x", pady=(4, 0))
        body = stash.body
        body.configure(padx=14, pady=11)
        tk.Label(body, text="STASH", bg=COLORS["panel"], fg=COLORS["accent"], font=("Georgia", 11)).pack(anchor="w")
        stash_items = [f"{item.name} ×{item.stash}" for item in self.controller.state.campaign.inventory if item.stash]
        tk.Label(body, text="   •   ".join(stash_items), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8), anchor="w", justify="left").pack(fill="x", pady=(7, 0))
        return frame

    def _open_editor(self) -> None:
        from mordheim_campaign.ui.dialogs.equipment_editor import EquipmentEditorDialog

        EquipmentEditorDialog(self.winfo_toplevel(), self.controller)

    def _show_item(self, name: str) -> None:
        item = next((entry for entry in self.controller.state.campaign.inventory if entry.name == name), None)
        if item is None:
            return
        assigned = []
        for warrior in self.controller.state.campaign.warriors:
            if name in warrior.equipment:
                assigned.append(warrior.name)
        detail = (
            f"{item.name}\n\nOwned: {item.owned}\nEquipped: {item.equipped}\nStash: {item.stash}\n\n"
            + ("Assigned to:\n• " + "\n• ".join(assigned) if assigned else "No current assignments")
            + "\n\nAssignment and selling actions will be wired later."
        )
        messagebox.showinfo("Inventory item", detail, parent=self)


# Compatibility exports for older imports while the prototype evolves.
ResourcesPanel = InventoryWorkspace
InventoryListPanel = InventoryWorkspace
AssignmentsPanel = InventoryWorkspace

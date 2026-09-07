from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.i18n import tr
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, ScrollableFrame, SummaryStrip


class InventoryWorkspace(tk.Frame):
    """Single equipment board: roster on the left, stash on the right."""

    def __init__(self, master: tk.Misc, controller: AppController, *, show_summary: bool = True, read_only: bool = False, purchase_mode: str | None = None, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        self.read_only = read_only
        self.purchase_mode = purchase_mode
        self._drag = None
        self._drag_badge: tk.Toplevel | None = None
        campaign = controller.state.campaign
        row = 0
        if show_summary:
            SummaryStrip(self, [
                (tr('Gold crowns'), f"{campaign.current_state.gold} gc"),
                ("Wyrdstone", tr('{} shards').format(campaign.current_state.wyrdstone)),
                (tr('Inventory'), tr('{} items').format(sum(item.owned for item in campaign.inventory))),
                (tr('In stash'), tr('{} items').format(sum(item.stash for item in campaign.inventory))),
            ]).grid(row=0, column=0, sticky="ew", pady=(0, 7))
            row = 1

        self.columnconfigure(0, weight=1)
        self.rowconfigure(row + 1, weight=1)
        toolbar = tk.Frame(self, bg=COLORS["bg"])
        toolbar.grid(row=row, column=0, sticky="ew", pady=(0, 6))
        tk.Label(toolbar, text=tr('Drag items between warriors and stash.'), bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left")
        if (campaign.is_draft or purchase_mode == "post_battle") and not read_only:
            ttk.Button(toolbar, text=tr('BUY AND SELL'), style="Accent.TButton", command=self._open_stash).pack(side="right")

        board = tk.Frame(self, bg=COLORS["bg"])
        board.grid(row=row + 1, column=0, sticky="nsew")
        board.columnconfigure(0, weight=3)
        board.columnconfigure(1, weight=2)
        board.rowconfigure(0, weight=1)
        self._build_roster(board).grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._build_stash(board).grid(row=0, column=1, sticky="nsew", padx=(6, 0))

    def _build_roster(self, parent: tk.Misc) -> BorderedFrame:
        outer = BorderedFrame(parent, background=COLORS["panel"], padding=1)
        body = outer.body
        body.configure(padx=8, pady=8)
        tk.Label(body, text=tr('WARBAND EQUIPMENT'), bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 5))
        scroll = ScrollableFrame(body, background=COLORS["panel"])
        scroll.pack(fill="both", expand=True)
        for warrior in self.controller.state.campaign.warriors:
            card = tk.Frame(scroll.inner, bg=COLORS["panel_alt"], padx=8, pady=6)
            card.pack(fill="x", pady=(0, 5))
            if warrior.kind != "hireling":
                card._equipment_drop_warrior_id = warrior.id
            label = warrior.name + (f"  ×{warrior.quantity}" if warrior.quantity > 1 else "")
            tk.Label(card, text=label, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", pady=(0, 3))
            if not warrior.equipment:
                tk.Label(card, text=tr('No equipment'), bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
            for equipment in warrior.equipment:
                locked = not equipment.transferable
                item = tk.Frame(card, bg=COLORS["panel_alt"], cursor="arrow" if locked else "hand2")
                item.pack(fill="x", pady=1)
                suffix = f" ×{equipment.quantity}" if equipment.quantity > 1 else ""
                if equipment.acquisition == "starting_grant":
                    note = tr(' · free starting equipment')
                elif equipment.acquisition == "hireling_grant":
                    note = tr(' · Hired Sword equipment')
                else:
                    note = ""
                icon = "🔒" if locked else "≡"
                rarity = next((row.rarity for row in self.controller.state.campaign.inventory if row.id == equipment.item_id), None)
                rare_note = f"  ·  {rarity}" if rarity else ""
                tk.Label(item, text=f"{icon}  {equipment.name}{suffix}{note}{rare_note}", bg=COLORS["panel_alt"], fg=COLORS["muted"] if locked else COLORS["text"], font=("Segoe UI", 8), anchor="w").pack(fill="x")
                if not self.read_only and not locked:
                    self._make_draggable(item, ("warrior", equipment.item_id, warrior.id), equipment.name)
        return outer

    def _build_stash(self, parent: tk.Misc) -> BorderedFrame:
        outer = BorderedFrame(parent, background=COLORS["panel"], padding=1)
        body = outer.body
        body.configure(padx=8, pady=8)
        body._equipment_drop_stash = True
        tk.Label(body, text=tr('STASH'), bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 5))
        scroll = ScrollableFrame(body, background=COLORS["panel"])
        scroll.pack(fill="both", expand=True)
        scroll._equipment_drop_stash = True
        scroll.inner._equipment_drop_stash = True
        rows = [item for item in self.controller.state.campaign.inventory if item.stash > 0]
        if not rows:
            tk.Label(scroll.inner, text=tr('The stash is empty.'), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
        for inventory in rows:
            item = tk.Frame(scroll.inner, bg=COLORS["panel_alt"], padx=7, pady=5, cursor="hand2")
            item.pack(fill="x", pady=(0, 4))
            item._equipment_drop_stash = True
            rare_note = f"  ·  {inventory.rarity}" if inventory.rarity else ""
            tk.Label(item, text=f"≡  {inventory.name} ×{inventory.stash}{rare_note}", bg=COLORS["panel_alt"], fg=COLORS["accent"] if inventory.rarity else COLORS["text"], font=("Segoe UI", 8), anchor="w").pack(fill="x")
            if not self.read_only:
                self._make_draggable(item, ("stash", inventory.id, None), inventory.name)
        return outer

    def _make_draggable(self, widget: tk.Misc, payload, label: str) -> None:
        for target in [widget, *widget.winfo_children()]:
            target.configure(cursor="hand2")
            target.bind("<ButtonPress-1>", lambda event, p=payload, text=label: self._drag_start(event, p, text))
            target.bind("<B1-Motion>", self._drag_move)
            target.bind("<ButtonRelease-1>", self._drag_end)

    def _drag_start(self, event, payload, label: str) -> None:
        self._drag = payload
        badge = tk.Toplevel(self)
        badge.overrideredirect(True)
        badge.attributes("-topmost", True)
        tk.Label(badge, text=label, bg=COLORS["accent"], fg=COLORS["black"], padx=7, pady=4, font=("Segoe UI Semibold", 8)).pack()
        self._drag_badge = badge
        self._drag_move(event)

    def _drag_move(self, event) -> None:
        if self._drag_badge is not None:
            self._drag_badge.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")

    def _drag_end(self, event) -> None:
        payload = self._drag
        self._drag = None
        if self._drag_badge is not None:
            self._drag_badge.destroy()
            self._drag_badge = None
        target = self.winfo_containing(event.x_root, event.y_root)
        warrior_id = None
        stash = False
        while target is not None:
            warrior_id = getattr(target, "_equipment_drop_warrior_id", warrior_id)
            stash = stash or bool(getattr(target, "_equipment_drop_stash", False))
            if target is self:
                break
            target = target.master
        if payload is None:
            return
        source, item_id, source_warrior = payload
        if source == "stash" and warrior_id:
            self._apply(self.controller.assign_stash_item, item_id, warrior_id)
        elif source == "warrior" and warrior_id and warrior_id != source_warrior:
            self._finish(self.controller.transfer_equipped_item(item_id, source_warrior, warrior_id))
        elif source == "warrior" and stash:
            self._apply(self.controller.return_equipped_item, item_id, source_warrior)

    def _apply(self, action, item_id: str, warrior_id: str) -> None:
        self._finish(action(item_id, warrior_id))

    def _finish(self, result) -> None:
        ok, message = result
        if not ok:
            messagebox.showerror(tr('Cannot move item'), message, parent=self)
            return
        self.controller.notify()

    def _open_stash(self) -> None:
        from mordheim_campaign.ui.dialogs.draft_stash import DraftStashDialog

        DraftStashDialog(self, self.controller, mode=self.purchase_mode or "draft")


ResourcesPanel = InventoryWorkspace
InventoryListPanel = InventoryWorkspace
AssignmentsPanel = InventoryWorkspace

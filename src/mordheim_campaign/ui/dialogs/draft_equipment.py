from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.i18n import tr
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, ScrollableFrame


class DraftEquipmentDialog(tk.Toplevel):
    """Buy and remove one warrior row's creation equipment."""

    def __init__(self, parent: tk.Misc, controller: AppController, warrior_id: str) -> None:
        super().__init__(parent)
        self.controller = controller
        self.warrior_id = warrior_id
        self.warrior = next(row for row in controller.state.campaign.warriors if row.id == warrior_id)
        self.offers = controller.draft_equipment_offers(warrior_id)
        self.configure(bg=COLORS["bg"])
        self.title(tr('Equipment') + f" · {self.warrior.name}")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        outer = BorderedFrame(self, background=COLORS["panel"], padding=1)
        outer.pack(fill="both", expand=True, padx=12, pady=12)
        body = outer.body
        body.configure(padx=12, pady=10)

        head = tk.Frame(body, bg=COLORS["panel"])
        head.pack(fill="x", pady=(0, 8))
        tk.Label(head, text=self.warrior.name.upper(), bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 13)).pack(side="left")
        self.treasury_var = tk.StringVar()
        tk.Label(head, textvariable=self.treasury_var, bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(side="right")

        columns = tk.Frame(body, bg=COLORS["panel"])
        columns.pack(fill="both", expand=True)
        self._build_available(columns).grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self._build_owned(columns).grid(row=0, column=1, sticky="nsew", padx=(6, 0))

        foot = tk.Frame(body, bg=COLORS["panel"])
        foot.pack(fill="x", pady=(8, 0))
        self.status_var = tk.StringVar()
        tk.Label(foot, textvariable=self.status_var, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left")
        ttk.Button(foot, text=tr('Done'), command=self._close).pack(side="right")

        self._refresh()
        self.protocol("WM_DELETE_WINDOW", self._close)
        self.bind("<Escape>", lambda _e: self._close())
        self.after_idle(self._center)

    def _panel(self, parent: tk.Misc, title: str) -> tuple[tk.Frame, tk.Frame]:
        outer = BorderedFrame(parent, background=COLORS["panel_alt"], padding=1)
        body = outer.body
        body.configure(width=300, height=300, padx=8, pady=8)
        body.pack_propagate(False)
        tk.Label(body, text=title, bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 5))
        scroll = ScrollableFrame(body, background=COLORS["panel_alt"], height=260)
        scroll.pack(fill="both", expand=True)
        return outer, scroll.inner

    def _build_available(self, parent: tk.Misc) -> tk.Frame:
        outer, rows = self._panel(parent, tr('AVAILABLE TO BUY'))
        self.available_rows = rows
        return outer

    def _build_owned(self, parent: tk.Misc) -> tk.Frame:
        outer, rows = self._panel(parent, tr('PURCHASED EQUIPMENT'))
        self.owned_rows = rows
        return outer

    def _refresh(self) -> None:
        for parent in (self.available_rows, self.owned_rows):
            for child in parent.winfo_children():
                child.destroy()
        campaign = self.controller.state.campaign
        self.treasury_var.set(tr('{} gc remaining').format(campaign.draft_treasury))
        multiplier = self.warrior.quantity

        for offer in self.offers:
            row = tk.Frame(self.available_rows, bg=COLORS["panel_alt"])
            row.pack(fill="x", pady=1)
            total = offer.cost * multiplier if offer.cost is not None else None
            label = f"{offer.name}  ·  {total} gc" if total is not None else f"{offer.name}  ·  —"
            tk.Label(row, text=label, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8), anchor="w").pack(side="left", fill="x", expand=True)
            button = ttk.Button(row, text=tr('BUY'), style="Mini.TButton", width=6, command=lambda item=offer.item_id: self._run(self.controller.buy_draft_equipment, item))
            button.pack(side="right")
            if total is None or total > campaign.draft_treasury:
                button.state(["disabled"])

        purchased = [item for item in self.warrior.equipment if item.acquisition == "purchase"]
        if not purchased:
            tk.Label(self.owned_rows, text=tr('No purchased equipment'), bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
        for item in purchased:
            row = tk.Frame(self.owned_rows, bg=COLORS["panel_alt"])
            row.pack(fill="x", pady=1)
            sets = max(1, item.quantity // self.warrior.quantity)
            label = item.name if sets == 1 else f"{item.name} ×{sets}"
            tk.Label(row, text=label, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8), anchor="w").pack(side="left", fill="x", expand=True)
            ttk.Button(row, text=tr('SELL'), style="Mini.TButton", width=8, command=lambda item_id=item.item_id: self._run(self.controller.remove_draft_equipment, item_id)).pack(side="right")

    def _run(self, action, item_id: str) -> None:
        ok, message = action(self.warrior_id, item_id)
        self.status_var.set(("✓ " if ok else "! ") + message)
        self._refresh()

    def _close(self) -> None:
        self.destroy()
        self.controller.notify()

    def _center(self) -> None:
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - self.winfo_width()) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - self.winfo_height()) // 2)
        self.geometry(f"+{x}+{y}")

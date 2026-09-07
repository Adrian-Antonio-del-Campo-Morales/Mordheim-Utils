from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.i18n import tr
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, ScrollableFrame


class DraftStashDialog(tk.Toplevel):
    """Buy creation items without assigning them to a warrior."""

    def __init__(self, parent: tk.Misc, controller: AppController, *, mode: str = "draft") -> None:
        super().__init__(parent)
        self.controller = controller
        self.mode = mode
        self.offers = controller.draft_stash_offers() if mode == "draft" else controller.post_battle_content().common_items()
        self.rare_ids = {offer.item_id for offer in controller.post_battle_content().rare_items()} if mode == "post_battle" else set()
        categories = list(dict.fromkeys(offer.category for offer in self.offers))
        self.expanded_categories = {categories[0]} if categories else set()
        self.configure(bg=COLORS["bg"])
        self.title(tr('Buy and Sell'))
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        outer = BorderedFrame(self, background=COLORS["panel"], padding=1)
        outer.pack(fill="both", expand=True, padx=12, pady=12)
        body = outer.body
        body.configure(padx=12, pady=10)

        head = tk.Frame(body, bg=COLORS["panel"])
        head.pack(fill="x", pady=(0, 7))
        tk.Label(head, text=tr('BUY AND SELL'), bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 13)).pack(side="left")
        self.treasury_var = tk.StringVar()
        tk.Label(head, textvariable=self.treasury_var, bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(side="right")

        columns = tk.Frame(body, bg=COLORS["panel"])
        columns.pack(fill="both", expand=True)
        available, self.available_rows = self._panel(columns, tr('AVAILABLE ITEMS'))
        available.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        stash, self.stash_rows = self._panel(columns, tr('CURRENT STASH'))
        stash.grid(row=0, column=1, sticky="nsew", padx=(6, 0))

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
        body.configure(width=310, height=320, padx=8, pady=8)
        body.pack_propagate(False)
        tk.Label(body, text=title, bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 5))
        scroll = ScrollableFrame(body, background=COLORS["panel_alt"], height=275)
        scroll.pack(fill="both", expand=True)
        return outer, scroll.inner

    def _refresh(self) -> None:
        for parent in (self.available_rows, self.stash_rows):
            for child in parent.winfo_children():
                child.destroy()
        campaign = self.controller.state.campaign
        treasury = campaign.draft_treasury if self.mode == "draft" else self.controller.post_battle_engine().projected_gold()
        self.treasury_var.set(tr('{} gc remaining').format(treasury))
        grouped = {}
        for offer in self.offers:
            grouped.setdefault(offer.category, []).append(offer)
        for category, offers in grouped.items():
            expanded = category in self.expanded_categories
            header = tk.Button(
                self.available_rows,
                text=f"{'−' if expanded else '+'}  {self._category_label(category)}  ({len(offers)})",
                command=lambda value=category: self._toggle_category(value),
                bg=COLORS["panel_deep"], fg=COLORS["accent"] if expanded else COLORS["text"],
                activebackground=COLORS["panel_soft"], activeforeground=COLORS["text"],
                relief="flat", bd=0, highlightthickness=0, anchor="w", padx=7, pady=5,
                font=("Segoe UI Semibold", 8), cursor="hand2",
            )
            header.pack(fill="x", pady=(0, 2))
            if not expanded:
                continue
            for offer in offers:
                row = tk.Frame(self.available_rows, bg=COLORS["panel_alt"])
                row.pack(fill="x", pady=1, padx=(7, 0))
                tk.Label(row, text=f"{offer.name}  ·  {offer.price_label}", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8), anchor="w").pack(side="left", fill="x", expand=True)
                button = ttk.Button(row, text=tr('BUY'), style="Mini.TButton", width=6, command=lambda value=offer: self._buy(value))
                button.pack(side="right")
                if offer.price_gc is None or offer.price_gc > treasury:
                    button.state(["disabled"])
        if not campaign.inventory:
            tk.Label(self.stash_rows, text=tr('The stash is empty.'), bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
        for item in campaign.inventory:
            if item.stash < 1:
                continue
            row = tk.Frame(self.stash_rows, bg=COLORS["panel_alt"])
            row.pack(fill="x", pady=1)
            rarity = item.rarity or (tr('RARE ITEM') if item.id in self.rare_ids else "")
            suffix = f"  ·  {rarity}" if rarity else ""
            tk.Label(row, text=f"{item.name} ×{item.stash}{suffix}", bg=COLORS["panel_alt"], fg=COLORS["accent"] if rarity else COLORS["text"], font=("Segoe UI", 8), anchor="w").pack(side="left", fill="x", expand=True)
            ttk.Button(row, text=tr('SELL'), style="Mini.TButton", width=8, command=lambda item_id=item.id: self._sell(item_id)).pack(side="right")

    @staticmethod
    def _category_label(category: str) -> str:
        labels = {
            "close-combat-weapon": tr('CLOSE COMBAT WEAPONS'),
            "ranged-weapon": tr('RANGED WEAPONS'),
            "armour": tr('ARMOUR'),
            "shield-or-defence": tr('SHIELDS AND DEFENCES'),
            "combat-equipment": tr('MISCELLANEOUS EQUIPMENT'),
            "material-or-upgrade": tr('MATERIALS AND UPGRADES'),
            "trollheim-equipment": tr('TROLLHEIM EQUIPMENT'),
            "out-of-scope": tr('OTHER ITEMS'),
        }
        return labels.get(category, category.replace("-", " ").upper())

    def _toggle_category(self, category: str) -> None:
        if category in self.expanded_categories:
            self.expanded_categories.remove(category)
        else:
            self.expanded_categories.add(category)
        self._refresh()

    def _run(self, action, item_id: str) -> None:
        ok, message = action(item_id, 1)
        self.status_var.set(("✓ " if ok else "! ") + message)
        self._refresh()

    def _buy(self, offer) -> None:
        if self.mode == "draft":
            self._run(self.controller.buy_draft_stash_item, offer.item_id)
            return
        result = self.controller.post_battle_engine().buy_item(
            offer.item_id, 1, offer.price_gc, category=offer.category, rarity=offer.rarity,
        )
        self.status_var.set(("✓ " if result[0] else "! ") + result[1])
        self._refresh()

    def _sell(self, item_id: str) -> None:
        action = self.controller.remove_draft_stash_item if self.mode == "draft" else self.controller.post_battle_engine().sell_item
        self._run(action, item_id)

    def _close(self) -> None:
        self.destroy()
        self.controller.notify()

    def _center(self) -> None:
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - self.winfo_width()) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - self.winfo_height()) // 2)
        self.geometry(f"+{x}+{y}")

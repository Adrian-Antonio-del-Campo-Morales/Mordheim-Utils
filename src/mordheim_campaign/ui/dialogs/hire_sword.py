from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_ui import themed_dialogs as messagebox

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.ui.components import ask_dice
from mordheim_ui.i18n import tr
from mordheim_ui.theme import COLORS
from mordheim_ui.windowing import center_on_application
from mordheim_ui.icons import ui_icon
from mordheim_ui.widgets import BorderedFrame


class HireSwordDialog(tk.Toplevel):
    """Hire one eligible Hired Sword during initial warband creation."""

    def __init__(self, parent: tk.Misc, controller: AppController) -> None:
        super().__init__(parent)
        self.controller = controller
        self.offers = controller.draft_hired_swords()
        self.configure(bg=COLORS["bg"])
        self.title(tr('Hire Hired Sword'))
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        outer = BorderedFrame(self, background=COLORS["panel"], padding=1)
        outer.pack(fill="both", expand=True, padx=12, pady=12)
        body = outer.body
        body.configure(padx=12, pady=10)
        heading = tk.Frame(body, bg=COLORS["panel"])
        heading.pack(fill="x")
        tk.Label(heading, image=ui_icon(self, "campaign_warband_recruit", 31), bg=COLORS["panel"]).pack(side="left", padx=(0, 8))
        tk.Label(heading, text=tr('HIRE HIRED SWORD'), bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 14)).pack(side="left")
        tk.Label(body, text=tr('{} gc available').format(controller.state.campaign.draft_treasury), bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(2, 7))

        picker = tk.Frame(body, bg=COLORS["panel"])
        picker.pack(fill="both", expand=True)
        self.table = ttk.Treeview(
            picker, columns=("name", "fee", "upkeep", "availability"), show="headings",
            height=min(14, max(7, len(self.offers))), selectmode="browse",
        )
        self.table.heading("name", text=tr('HIRED SWORD'), anchor="w")
        self.table.heading("fee", text=tr('HIRE FEE'), anchor="e")
        self.table.heading("upkeep", text=tr('UPKEEP'), anchor="e")
        self.table.heading("availability", text=tr('AVAILABILITY'), anchor="e")
        self.table.column("name", width=300, minwidth=220, anchor="w", stretch=True)
        self.table.column("fee", width=105, minwidth=80, anchor="e", stretch=False)
        self.table.column("upkeep", width=105, minwidth=80, anchor="e", stretch=False)
        self.table.column("availability", width=125, minwidth=95, anchor="e", stretch=False)
        scrollbar = ttk.Scrollbar(picker, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=scrollbar.set)
        self.table.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        for index, offer in enumerate(self.offers):
            self.table.insert("", "end", iid=str(index), values=(
                offer.name,
                offer.fee_label or "—",
                offer.upkeep_label or "—",
                offer.availability_label,
            ))
        if self.offers:
            self.table.selection_set("0")
            self.table.see("0")
        self.table.bind("<<TreeviewSelect>>", self._update_detail)
        self.table.bind("<Double-Button-1>", lambda _event: self._hire())

        self.detail_var = tk.StringVar()
        tk.Label(body, textvariable=self.detail_var, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8), wraplength=560, justify="left").pack(anchor="w", pady=(7, 0))
        actions = tk.Frame(body, bg=COLORS["panel"])
        actions.pack(fill="x", pady=(9, 0))
        ttk.Button(actions, text=tr('Cancel'), command=self.destroy).pack(side="right", padx=(0, 6))
        self.hire_button = ttk.Button(actions, text=tr('HIRE'), style="Accent.TButton", command=self._hire)
        self.hire_button.pack(side="right")
        if not self.offers:
            self.hire_button.state(["disabled"])
        self._update_detail()
        self.bind("<Escape>", lambda _e: self.destroy())
        self.after_idle(self._center)

    def _selected(self):
        selection = self.table.selection()
        return self.offers[int(selection[0])] if selection else None

    def _update_detail(self, _event=None) -> None:
        offer = self._selected()
        if offer is None:
            self.detail_var.set(tr('No Hired Swords are available to this warband.'))
            return
        parts = [offer.availability_label]
        if offer.eligibility_note:
            parts.append(offer.eligibility_note)
        self.detail_var.set(" · ".join(parts))
        if (offer.fee_gc is None and not offer.fee_resources) or offer.eligibility == "variant":
            self.hire_button.state(["disabled"])
        else:
            self.hire_button.state(["!disabled"])

    def _hire(self) -> None:
        offer = self._selected()
        if offer is None:
            return
        roll = None
        if offer.eligibility == "conditional":
            dice = ask_dice(self, title=tr('Acceptance roll'), dice_count=1)
            if not dice:
                return
            roll = dice[0]
        fee_roll = None
        if offer.fee_dice is not None:
            dice = ask_dice(self, title=tr('Hiring fee'), dice_count=offer.fee_dice[0],
                            dice_sides=offer.fee_dice[1])
            if not dice:
                return
            fee_roll = sum(dice)
        ok, message = self.controller.perform_undoable(
            tr('Hire Hired Sword'),
            lambda: self.controller.hire_draft_hired_sword(offer.profile_id, roll, fee_roll))
        if not ok:
            messagebox.showerror(tr('Cannot hire Hired Sword'), message, parent=self)
            return
        self.destroy()
        self.controller.notify()

    def _center(self) -> None:
        center_on_application(self)

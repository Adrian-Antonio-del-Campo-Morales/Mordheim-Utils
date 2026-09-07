from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.i18n import tr
from mordheim_ui.theme import COLORS
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
        tk.Label(body, text=tr('HIRE HIRED SWORD'), bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 14)).pack(anchor="w")
        tk.Label(body, text=tr('{} gc available').format(controller.state.campaign.draft_treasury), bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(2, 7))

        self.listbox = tk.Listbox(
            body, width=72, height=13, bg=COLORS["entry"], fg=COLORS["text"],
            selectbackground=COLORS["accent"], selectforeground=COLORS["black"],
            bd=0, highlightthickness=1, highlightbackground=COLORS["border_soft"],
            font=("Segoe UI", 8), activestyle="none", exportselection=False,
        )
        self.listbox.pack(fill="x")
        for offer in self.offers:
            fee = offer.fee_label or "—"
            upkeep = tr(' · upkeep {}').format(offer.upkeep_label) if offer.upkeep_label else ""
            marker = " *" if offer.eligibility != "eligible" else ""
            self.listbox.insert("end", f"{offer.name}{marker}  ·  {fee}{upkeep}")
        if self.offers:
            self.listbox.selection_set(0)
        self.listbox.bind("<<ListboxSelect>>", self._update_detail)

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
        selection = self.listbox.curselection()
        return self.offers[selection[0]] if selection else None

    def _update_detail(self, _event=None) -> None:
        offer = self._selected()
        if offer is None:
            self.detail_var.set(tr('No Hired Swords are available to this warband.'))
            return
        parts = [offer.availability_label]
        if offer.eligibility_note:
            parts.append(offer.eligibility_note)
        self.detail_var.set(" · ".join(parts))
        if offer.fee_gc is None or offer.eligibility == "variant":
            self.hire_button.state(["disabled"])
        else:
            self.hire_button.state(["!disabled"])

    def _hire(self) -> None:
        offer = self._selected()
        if offer is None:
            return
        roll = None
        if offer.eligibility == "conditional":
            roll = simpledialog.askinteger(tr('Acceptance roll'), tr('Enter D6 result'), parent=self, minvalue=1, maxvalue=6)
            if roll is None:
                return
        ok, message = self.controller.hire_draft_hired_sword(offer.profile_id, roll)
        if not ok:
            messagebox.showerror(tr('Cannot hire Hired Sword'), message, parent=self)
            return
        self.destroy()
        self.controller.notify()

    def _center(self) -> None:
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - self.winfo_width()) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - self.winfo_height()) // 2)
        self.geometry(f"+{x}+{y}")

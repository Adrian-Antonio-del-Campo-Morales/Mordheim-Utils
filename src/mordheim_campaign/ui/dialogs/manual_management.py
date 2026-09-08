from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_ui import themed_dialogs as messagebox
from mordheim_ui.i18n import tr
from mordheim_ui.theme import COLORS
from mordheim_ui.windowing import center_on_application
from mordheim_ui.widgets import BorderedFrame


class ResourceCorrectionDialog(tk.Toplevel):
    def __init__(self, parent, controller) -> None:
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=COLORS["bg"]); self.title(tr("Manage resources")); self.resizable(False, False)
        self.transient(parent.winfo_toplevel()); self.grab_set()
        body = BorderedFrame(self, background=COLORS["panel"], padding=1).body
        body.master.pack(fill="both", expand=True, padx=14, pady=14); body.configure(padx=16, pady=14)
        tk.Label(body, text=tr("MANAGE RESOURCES"), bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 13)).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        self.resource = tk.StringVar(value="gold_crowns")
        choices = [("gold_crowns", tr("Gold crowns")), ("wyrdstone_fragments", tr("Wyrdstone")),
                   ("treasures", tr("Treasures")), ("campaign_points", tr("Campaign points"))]
        menu = ttk.OptionMenu(body, self.resource, self.resource.get(), *[key for key, _ in choices])
        menu.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.amount = tk.IntVar(value=0)
        ttk.Spinbox(body, from_=-9999, to=9999, textvariable=self.amount, width=9).grid(row=1, column=1, sticky="e")
        self.reason = tk.StringVar()
        ttk.Entry(body, textvariable=self.reason, width=48).grid(row=2, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        tk.Label(body, text=tr("Reason for correction"), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).grid(row=3, column=0, columnspan=2, sticky="w")
        ttk.Button(body, text=tr("APPLY"), style="Accent.TButton", command=self._apply).grid(row=4, column=1, sticky="e", pady=(12, 0))
        self.after_idle(lambda: center_on_application(self))

    def _apply(self) -> None:
        ok, message = self.controller.perform_undoable(
            tr('Correct resources'),
            lambda: self.controller.adjust_resource(self.resource.get(), self.amount.get(), self.reason.get()))
        if not ok:
            messagebox.showerror(tr("Cannot apply correction"), message, parent=self); return
        self.destroy(); self.controller.notify()


class AddInventoryItemDialog(tk.Toplevel):
    def __init__(self, parent, controller) -> None:
        super().__init__(parent)
        self.controller = controller
        offers = (*controller.post_battle_content().common_items(), *controller.post_battle_content().rare_items())
        self.offers = sorted({row.item_id: row for row in offers}.values(), key=lambda row: row.name.casefold())
        self.configure(bg=COLORS["bg"]); self.title(tr("Add item")); self.resizable(False, False)
        self.transient(parent.winfo_toplevel()); self.grab_set()
        outer = BorderedFrame(self, background=COLORS["panel"], padding=1); outer.pack(padx=14, pady=14)
        body = outer.body; body.configure(padx=14, pady=12)
        tk.Label(body, text=tr("ADD ITEM FROM KB"), bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 13)).pack(anchor="w", pady=(0, 8))
        self.listbox = tk.Listbox(body, width=62, height=14, bg=COLORS["entry"], fg=COLORS["text"],
                                  selectbackground=COLORS["accent"], selectforeground=COLORS["black"], bd=0,
                                  highlightthickness=1, highlightbackground=COLORS["border_soft"])
        self.listbox.pack(fill="both", expand=True)
        for offer in self.offers:
            self.listbox.insert("end", f"{offer.name}  ·  {offer.category}")
        if self.offers: self.listbox.selection_set(0)
        row = tk.Frame(body, bg=COLORS["panel"]); row.pack(fill="x", pady=(8, 0))
        self.quantity = tk.IntVar(value=1); ttk.Spinbox(row, from_=1, to=99, width=5, textvariable=self.quantity).pack(side="left")
        self.reason = tk.StringVar(); ttk.Entry(row, textvariable=self.reason, width=42).pack(side="left", fill="x", expand=True, padx=8)
        ttk.Button(row, text=tr("ADD"), style="Accent.TButton", command=self._apply).pack(side="right")
        tk.Label(body, text=tr("Quantity · reason for correction"), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
        self.after_idle(lambda: center_on_application(self))

    def _apply(self) -> None:
        selected = self.listbox.curselection()
        if not selected: return
        ok, message = self.controller.perform_undoable(
            tr('Correct inventory'), lambda: self.controller.manually_add_item(
                self.offers[selected[0]].item_id, self.quantity.get(), self.reason.get()))
        if not ok:
            messagebox.showerror(tr("Cannot add item"), message, parent=self); return
        self.destroy(); self.controller.notify()


class ManualSkillsDialog(tk.Toplevel):
    def __init__(self, parent, controller, warrior) -> None:
        super().__init__(parent)
        self.controller, self.warrior = controller, warrior
        self.entries = sorted(controller.port.skills(), key=lambda row: str(row.get("name") or "").casefold())
        self.configure(bg=COLORS["bg"]); self.title(tr("Edit skills")); self.resizable(False, False)
        self.transient(parent.winfo_toplevel()); self.grab_set()
        outer = BorderedFrame(self, background=COLORS["panel"], padding=1); outer.pack(padx=14, pady=14)
        body = outer.body; body.configure(padx=14, pady=12)
        tk.Label(body, text=tr("EDIT SKILLS — {}").format(warrior.name), bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 13)).pack(anchor="w", pady=(0, 8))
        self.listbox = tk.Listbox(body, width=62, height=16, bg=COLORS["entry"], fg=COLORS["text"],
                                  selectbackground=COLORS["accent"], selectforeground=COLORS["black"], bd=0,
                                  highlightthickness=1, highlightbackground=COLORS["border_soft"])
        self.listbox.pack(fill="both", expand=True); self._refresh()
        self.reason = tk.StringVar()
        ttk.Entry(body, textvariable=self.reason, width=62).pack(fill="x", pady=(8, 0))
        tk.Label(body, text=tr("Reason for correction"), bg=COLORS["panel"], fg=COLORS["muted"],
                 font=("Segoe UI", 8)).pack(anchor="w")
        buttons = tk.Frame(body, bg=COLORS["panel"]); buttons.pack(fill="x", pady=(9, 0))
        ttk.Button(buttons, text=tr("REMOVE"), command=lambda: self._set(False)).pack(side="right", padx=(6, 0))
        ttk.Button(buttons, text=tr("ADD"), style="Accent.TButton", command=lambda: self._set(True)).pack(side="right")
        self.after_idle(lambda: center_on_application(self))

    def _refresh(self) -> None:
        self.listbox.delete(0, "end")
        for row in self.entries:
            name = str(row.get("name") or "")
            mark = "✓ " if name in self.warrior.skills else "  "
            self.listbox.insert("end", f"{mark}[{self.controller.port.skill_table_label(row)}] {name}")

    def _set(self, present: bool) -> None:
        selected = self.listbox.curselection()
        if not selected: return
        name = str(self.entries[selected[0]].get("name") or "")
        ok, message = self.controller.perform_undoable(
            tr('Correct skills'),
            lambda: self.controller.set_manual_skill(self.warrior.id, name, present, self.reason.get()))
        if not ok:
            messagebox.showerror(tr("Cannot edit skill"), message, parent=self); return
        self._refresh()

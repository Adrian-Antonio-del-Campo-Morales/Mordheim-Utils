from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.knowledge_port import WarbandProfile
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame


class AddWarriorDialog(tk.Toplevel):
    """Pick a canonical profile of the warband and add it to the draft.

    The dialog shows only profiles the KB allows for this band (roster order,
    per-profile limits, no random-characteristic profiles yet). Quantity
    applies to henchmen/animal groups; heroes are added one at a time.
    """

    def __init__(self, parent: tk.Misc, controller: AppController, *, kind: str) -> None:
        super().__init__(parent)
        self.controller = controller
        self.kind = kind
        self.profiles = controller.addable_profiles(kind)
        self.configure(bg=COLORS["bg"])
        self.title("Add Hero" if kind == "hero" else "Add Henchmen Group")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        outer = BorderedFrame(self, background=COLORS["panel"], padding=1)
        outer.pack(fill="both", expand=True, padx=18, pady=18)
        body = outer.body
        body.configure(padx=20, pady=18)

        heading = "ADD HERO" if kind == "hero" else "ADD HENCHMEN GROUP"
        subtitle = "Choose a canonical profile from the warband roster." if kind == "hero" else (
            "Choose a group profile; the whole group shares one profile card."
        )
        tk.Label(body, text=heading, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 15)).pack(anchor="w")
        tk.Label(body, text=subtitle, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 12))

        self._build_picker(body)
        self._build_detail(body)
        if kind == "henchman":
            self._build_quantity(body)
        self._build_actions(body)

        self.bind("<Return>", lambda _e: self._add())
        self.bind("<Escape>", lambda _e: self.destroy())
        self.after_idle(self._center)

    def _build_picker(self, body: tk.Frame) -> None:
        frame = tk.Frame(body, bg=COLORS["panel"])
        frame.pack(fill="x")
        self.listbox = tk.Listbox(
            frame,
            height=8,
            bg=COLORS["entry"],
            fg=COLORS["text"],
            selectbackground=COLORS["accent"],
            selectforeground=COLORS["black"],
            highlightthickness=1,
            highlightbackground=COLORS["border_soft"],
            bd=0,
            font=("Segoe UI", 9),
            activestyle="none",
        )
        self.listbox.pack(fill="x")
        for profile in self.profiles:
            self.listbox.insert("end", f"{profile.name}  ·  {profile.cost} gc  ·  XP {profile.experience}")
        if not self.profiles:
            self.listbox.insert("end", "(no profiles available)")
            self.listbox.configure(state="disabled")
        if self.profiles:
            self.listbox.selection_set(0)
        self.listbox.bind("<<ListboxSelect>>", lambda _e: self._update_detail())

    def _current_profile(self) -> WarbandProfile | None:
        if not self.profiles:
            return None
        index = self.listbox.curselection()
        return self.profiles[index[0]] if index else None

    def _build_detail(self, body: tk.Frame) -> None:
        self.detail_var = tk.StringVar()
        tk.Label(
            body,
            textvariable=self.detail_var,
            bg=COLORS["panel"],
            fg=COLORS["muted"],
            font=("Segoe UI", 8),
            justify="left",
            wraplength=360,
        ).pack(anchor="w", pady=(9, 0))

    def _build_quantity(self, body: tk.Frame) -> None:
        self.quantity_var = tk.IntVar(value=1)
        row = tk.Frame(body, bg=COLORS["panel"])
        row.pack(fill="x", pady=(10, 0))
        tk.Label(row, text="MODELS IN GROUP", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8)).pack(side="left")
        self.quantity_box = ttk.Spinbox(row, from_=1, to=99, width=6, textvariable=self.quantity_var)
        self.quantity_box.pack(side="left", padx=(10, 0))
        self.quantity_hint = tk.StringVar()
        tk.Label(row, textvariable=self.quantity_hint, bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(side="left", padx=(10, 0))

    def _build_actions(self, body: tk.Frame) -> None:
        actions = tk.Frame(body, bg=COLORS["panel"])
        actions.pack(fill="x", pady=(16, 0))
        ttk.Button(actions, text="Cancel", command=self.destroy).pack(side="right", padx=(0, 6))
        label = "ADD TO DRAFT" if self.profiles else "CLOSE"
        ttk.Button(actions, text=label, style="Accent.TButton", command=self._add).pack(side="right")

    def _quantity_limits(self, profile: WarbandProfile) -> int:
        """Cantidad máxima para una fila nueva según límites del roster."""
        campaign = self.controller.state.campaign
        taken, member_max = self.controller.profile_allowance(profile)
        capacity = campaign.maximum_models - campaign.draft_model_count
        limits = [capacity]
        if member_max is not None:
            limits.append(member_max - taken)
        if profile.group_maximum is not None:
            limits.append(profile.group_maximum)
        return max(1, min(limits))

    def _update_detail(self, _event=None) -> None:
        profile = self._current_profile()
        if profile is None:
            self.detail_var.set("")
            return
        taken, member_max = self.controller.profile_allowance(profile)
        allowance = "no roster limit" if member_max is None else f"{member_max - taken} remaining"
        lines = [
            "  ·  ".join(f"{key} {value}" for key, value in profile.characteristics.items()),
            f"Cost {profile.cost} gc per model  ·  Starting XP {profile.experience}  ·  {allowance}",
        ]
        if profile.skill_tables:
            lines.append("Skill access: " + ", ".join(profile.skill_tables))
        if profile.inherent_rules:
            lines.append("Rules: " + ", ".join(profile.inherent_rules))
        self.detail_var.set("\n".join(lines))
        if self.kind == "henchman":
            high = self._quantity_limits(profile)
            self.quantity_box.configure(to=max(1, high))
            if self.quantity_var.get() > high or self.quantity_var.get() < 1:
                self.quantity_var.set(1)
            self.quantity_hint.set(f"at most {high} models")

    def _add(self) -> None:
        profile = self._current_profile()
        if profile is None:
            self.destroy()
            return
        quantity = 1 if self.kind == "hero" else int(self.quantity_var.get())
        ok, message = self.controller.add_draft_warriors(profile.profile_id, quantity)
        if not ok:
            messagebox.showerror("Cannot add warrior", message, parent=self)
            return
        self.destroy()

    def _center(self) -> None:
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - self.winfo_width()) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - self.winfo_height()) // 2)
        self.geometry(f"+{x}+{y}")

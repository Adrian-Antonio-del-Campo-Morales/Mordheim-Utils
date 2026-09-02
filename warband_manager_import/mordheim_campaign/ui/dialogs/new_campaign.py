from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame


class NewCampaignDialog(tk.Toplevel):
    """Small campaign creation dialog.

    It deliberately asks only for the identity of the campaign and warband.
    Rulesets, KB validation and persistence are intentionally outside this GUI
    prototype and can be added later without enlarging the onboarding flow.
    """

    WARBANDS = ("Sisters of Sigmar", "Mercenaries", "Witch Hunters")

    def __init__(self, parent: tk.Misc, controller: AppController) -> None:
        super().__init__(parent)
        self.controller = controller
        self.configure(bg=COLORS["bg"])
        self.title("Create Campaign")
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.grab_set()

        outer = BorderedFrame(self, background=COLORS["panel"], padding=1)
        outer.pack(fill="both", expand=True, padx=18, pady=18)
        body = outer.body
        body.configure(padx=20, pady=18)

        tk.Label(body, text="CREATE CAMPAIGN", bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 15)).grid(row=0, column=0, columnspan=2, sticky="w")
        tk.Label(body, text="Start with the minimum information. The initial warband is built next.", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9)).grid(row=1, column=0, columnspan=2, sticky="w", pady=(4, 18))

        tk.Label(body, text="CAMPAIGN NAME", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8)).grid(row=2, column=0, sticky="w")
        self.name_var = tk.StringVar(value="New Mordheim Campaign")
        ttk.Entry(body, textvariable=self.name_var, width=38).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 14))

        tk.Label(body, text="WARBAND", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8)).grid(row=4, column=0, sticky="w")
        self.warband_var = tk.StringVar(value=self.WARBANDS[0])
        ttk.Combobox(body, textvariable=self.warband_var, values=self.WARBANDS, state="readonly", width=35).grid(row=5, column=0, columnspan=2, sticky="ew", pady=(5, 6))
        tk.Label(body, text="Warband options are visual prototype data for now.", bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 8)).grid(row=6, column=0, columnspan=2, sticky="w")

        actions = tk.Frame(body, bg=COLORS["panel"])
        actions.grid(row=7, column=0, columnspan=2, sticky="e", pady=(22, 0))
        ttk.Button(actions, text="Cancel", command=self.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="CREATE", style="Accent.TButton", command=self._create).pack(side="left")
        body.columnconfigure(0, weight=1)

        self.bind("<Return>", lambda _e: self._create())
        self.bind("<Escape>", lambda _e: self.destroy())
        self.after_idle(self._center)

    def _center(self) -> None:
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - self.winfo_width()) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - self.winfo_height()) // 2)
        self.geometry(f"+{x}+{y}")

    def _create(self) -> None:
        name = self.name_var.get().strip() or "New Mordheim Campaign"
        self.controller.new_campaign(name, self.warband_var.get())
        self.destroy()

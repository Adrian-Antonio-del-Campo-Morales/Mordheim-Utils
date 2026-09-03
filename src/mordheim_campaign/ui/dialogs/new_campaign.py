from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame


class NewCampaignDialog(tk.Toplevel):
    """Small campaign creation dialog.

    It deliberately asks only for the identity of the campaign and warband. The
    warband list comes from the canonical KB through ``KnowledgePort``; rules,
    KB validation and the initial roster are resolved after creation without
    enlarging the onboarding flow.
    """

    DEFAULT_BAND_ID = "sisters-of-sigmar"

    def __init__(self, parent: tk.Misc, controller: AppController) -> None:
        super().__init__(parent)
        self.controller = controller
        self.options = controller.warband_options()
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
        labels = [option.label for option in self.options]
        self._selected = next(
            (index for index, option in enumerate(self.options) if option.band_id == self.DEFAULT_BAND_ID and option.collection == "mordheim"),
            0,
        )
        self.warband_var = tk.StringVar(value=labels[self._selected])
        self.warband_box = ttk.Combobox(body, textvariable=self.warband_var, values=labels, state="readonly", width=35)
        self.warband_box.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(5, 6))
        self.warband_box.bind("<<ComboboxSelected>>", self._on_warband_change)
        self.caption_var = tk.StringVar()
        tk.Label(body, textvariable=self.caption_var, bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 8), justify="left", wraplength=330).grid(row=6, column=0, columnspan=2, sticky="w")
        self._update_caption()

        actions = tk.Frame(body, bg=COLORS["panel"])
        actions.grid(row=7, column=0, columnspan=2, sticky="e", pady=(22, 0))
        ttk.Button(actions, text="Cancel", command=self.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="CREATE", style="Accent.TButton", command=self._create).pack(side="left")
        body.columnconfigure(0, weight=1)

        self.bind("<Return>", lambda _e: self._create())
        self.bind("<Escape>", lambda _e: self.destroy())
        self.after_idle(self._center)

    def _current_option(self):
        label = self.warband_var.get()
        return next((option for option in self.options if option.label == label), self.options[self._selected])

    def _update_caption(self) -> None:
        option = self._current_option()
        source = f" · {option.source_label}" if option.collection != "mordheim" else ""
        self.caption_var.set(
            f"{option.minimum_models}–{option.maximum_models} models · {option.starting_gold} gc starting{source} · {option.publication}"
        )

    def _on_warband_change(self, _event=None) -> None:
        self._update_caption()

    def _center(self) -> None:
        self.update_idletasks()
        parent = self.master.winfo_toplevel()
        x = parent.winfo_rootx() + max(0, (parent.winfo_width() - self.winfo_width()) // 2)
        y = parent.winfo_rooty() + max(0, (parent.winfo_height() - self.winfo_height()) // 2)
        self.geometry(f"+{x}+{y}")

    def _create(self) -> None:
        name = self.name_var.get().strip() or "New Mordheim Campaign"
        option = self._current_option()
        self.controller.new_campaign(name, option.band_id)
        self.destroy()

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.ui.panels import CampaignTimeline
from mordheim_campaign.ui.views.moments import BattleEntryMoment, BattleMoment, InitialWarbandDraftMoment, PostBattleMoment, WarbandStateMoment
from mordheim_ui.theme import COLORS
from mordheim_ui.i18n import tr


class CampaignView(tk.Frame):
    """Campaign-first workspace: timeline at left, selected moment at right."""

    def __init__(self, master: tk.Misc, controller: AppController, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        self.columnconfigure(0, weight=1)
        c = controller.state.campaign
        variants = self.controller.variant_options()
        content_row = 0
        if variants:
            compact = tk.Frame(self, bg=COLORS["bg"])
            compact.grid(row=0, column=0, sticky="ew", pady=(0, 5))
            self._variant_selector(compact, c)
            content_row = 1
        self.rowconfigure(content_row, weight=1)
        self._timeline().grid(row=content_row, column=0, sticky="nsew")

    def _variant_selector(self, frame: tk.Misc, c) -> None:
        variants = self.controller.variant_options()
        if variants:
            vbox = tk.Frame(frame, bg=COLORS["bg"])
            vbox.pack(side="right")
            tk.Label(vbox, text=tr('MERCENARY VARIANT'), bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).pack(side="left", padx=(0, 6))
            labels = [label for _, label in variants]
            current = next((label for identifier, label in variants if identifier == c.mercenary_variant), None)
            variant_var = tk.StringVar(value=current or "—")
            box = ttk.Combobox(vbox, textvariable=variant_var, values=("—", *labels), state="readonly", width=11)
            box.pack(side="left")
            box.bind("<<ComboboxSelected>>", lambda _e: self.controller.perform_undoable(
                tr('Change mercenary variant'), lambda: self.controller.set_mercenary_variant(
                    None if variant_var.get() == "—" else next(
                        identifier for identifier, label in variants if label == variant_var.get())
                )))

    def _timeline(self) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"])
        frame.columnconfigure(0, minsize=265, weight=0)
        frame.columnconfigure(1, weight=1)
        frame.rowconfigure(0, weight=1)
        CampaignTimeline(frame, self.controller, width=275).grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        detail = tk.Frame(frame, bg=COLORS["bg"])
        detail.grid(row=0, column=1, sticky="nsew")
        detail.columnconfigure(0, weight=1)
        detail.rowconfigure(0, weight=1)

        node = self.controller.state.selected_moment
        kind, number_text = node.split(":", 1)
        number = int(number_text)
        if kind == "draft":
            widget = InitialWarbandDraftMoment(detail, self.controller)
        elif kind == "state":
            widget = WarbandStateMoment(detail, self.controller, number)
        elif kind == "battle":
            widget = BattleMoment(detail, self.controller, number)
        elif kind == "new-battle":
            widget = BattleEntryMoment(detail, self.controller, number)
        else:
            widget = PostBattleMoment(detail, self.controller, number)
        widget.grid(row=0, column=0, sticky="nsew")
        return frame

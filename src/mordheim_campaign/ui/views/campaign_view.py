from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.ui.dialogs import NewCampaignDialog
from mordheim_campaign.ui.panels import CampaignTimeline
from mordheim_campaign.ui.views.campaign_statistics import CampaignStatistics
from mordheim_campaign.ui.views.moments import BattleMoment, InitialWarbandDraftMoment, PostBattleMoment, WarbandStateMoment
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import SegmentedTabs
from mordheim_ui.i18n import tr


class CampaignView(tk.Frame):
    """Campaign-first workspace: timeline at left, selected moment at right."""

    def __init__(self, master: tk.Misc, controller: AppController, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        c = controller.state.campaign
        self._header(c).grid(row=0, column=0, sticky="ew", pady=(0, 8))

        mode_bar = tk.Frame(self, bg=COLORS["bg"])
        mode_bar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        modes = (("timeline", tr('TIMELINE')),) if c.is_draft else (("timeline", tr('TIMELINE')), ("statistics", tr('STATISTICS')))
        SegmentedTabs(mode_bar, modes, "timeline" if c.is_draft else controller.state.campaign_mode, controller.set_campaign_mode).pack(side="left")

        if not c.is_draft and controller.state.campaign_mode == "statistics":
            CampaignStatistics(self, controller).grid(row=2, column=0, sticky="nsew")
        else:
            self._timeline().grid(row=2, column=0, sticky="nsew")

    def _header(self, c) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"])
        text = tk.Frame(frame, bg=COLORS["bg"])
        text.pack(side="left", fill="x", expand=True)

        selector = tk.Menubutton(
            text,
            text=f"{c.campaign_name}  ▾",
            bg=COLORS["bg"],
            fg=COLORS["text"],
            activebackground=COLORS["panel_deep"],
            activeforeground=COLORS["text"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Georgia", 17),
            cursor="hand2",
            padx=0,
            pady=0,
        )
        selector.pack(anchor="w")
        menu = tk.Menu(selector, tearoff=False, bg=COLORS["panel"], fg=COLORS["text"], activebackground=COLORS["panel_soft"], activeforeground=COLORS["text"])
        menu.add_command(label=f"✓  {c.campaign_name}", state="disabled")
        menu.add_separator()
        menu.add_command(label=tr('New Campaign…'), command=self._new_campaign)
        menu.add_command(label=tr('Open creation example'), command=self.controller.open_creation_example)
        menu.add_command(label=tr('Open campaign example'), command=self.controller.open_campaign_example)
        menu.add_separator()
        menu.add_command(label=tr('Manage Campaigns…'), command=self._placeholder)
        selector.configure(menu=menu)

        phase = tr('Initial warband draft') if c.is_draft else tr('{}  ·  {}  ·  started {}').format(c.warband_name, c.warband_type, c.started)
        tk.Label(text, text=phase, bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(anchor="w", pady=(3, 0))

        compact = tk.Frame(frame, bg=COLORS["bg"])
        compact.pack(side="right", padx=(12, 0))
        variants = self.controller.variant_options()
        if variants:
            vbox = tk.Frame(compact, bg=COLORS["bg"])
            vbox.pack(side="left", padx=(0, 12))
            tk.Label(vbox, text=tr('MERCENARY VARIANT'), bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).pack(anchor="w")
            labels = [label for _, label in variants]
            current = next((label for identifier, label in variants if identifier == c.mercenary_variant), None)
            variant_var = tk.StringVar(value=current or "—")
            box = ttk.Combobox(vbox, textvariable=variant_var, values=("—", *labels), state="readonly", width=11)
            box.pack(anchor="w", pady=(2, 0))
            box.bind("<<ComboboxSelected>>", lambda _e: self.controller.set_mercenary_variant(
                None if variant_var.get() == "—" else next(identifier for identifier, label in variants if label == variant_var.get())
            ))
        if c.is_draft:
            tk.Label(
                compact,
                text=tr('DRAFT  ·  {} gc  ·  Rating {}  ·  {}/{} models').format(c.draft_treasury, c.draft_rating, c.draft_model_count, c.maximum_models),
                bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8),
            ).pack(side="left", padx=(0, 12))
            start = ttk.Button(compact, text=tr('START CAMPAIGN'), style="Accent.TButton", command=self.controller.commit_initial_warband)
            start.pack(side="left")
            if not c.draft_is_legal:
                start.state(["disabled"])
        else:
            current = c.current_state
            tk.Label(
                compact,
                text=tr('CURRENT  ·  Rating {}  ·  {}/{} models  ·  {} gc').format(current.rating, current.models, current.max_models, current.gold),
                bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8),
            ).pack(side="left", padx=(0, 12))
            pending = c.pending_post_battle
            if pending:
                ttk.Button(compact, text=tr('RESUME POST-BATTLE #{}').format(pending.battle_number), style="Accent.TButton", command=self.controller.resume_pending_post_battle).pack(side="left")
            else:
                ttk.Button(compact, text=tr('+ NEW BATTLE'), style="Accent.TButton", command=self._new_battle).pack(side="left")
        return frame

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
        else:
            widget = PostBattleMoment(detail, self.controller, number)
        widget.grid(row=0, column=0, sticky="nsew")
        return frame

    def _new_campaign(self) -> None:
        NewCampaignDialog(self, self.controller)

    def _new_battle(self) -> None:
        from mordheim_campaign.ui.dialogs.record_battle import RecordBattleDialog

        RecordBattleDialog(self, self.controller)

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.ui.dialogs import NewCampaignDialog
from mordheim_campaign.ui.file_actions import (
    export_warband_pdf,
    load_campaign_file,
    save_current_campaign,
)
from mordheim_campaign.ui.views import CampaignView, RulesView, SettingsView
from mordheim_ui.theme import COLORS
from mordheim_ui.i18n import tr
from mordheim_ui.icons import ui_icon


VIEWS = {
    "campaign": CampaignView,
    "rules": RulesView,
    "settings": SettingsView,
}

NAV = [
    ("campaign", 'CAMPAIGN', "campaign_navigation_campaign"),
    ("rules", 'RULES', "campaign_file_rules"),
    ("settings", 'SETTINGS', "campaign_file_settings"),
]


class AppShell(tk.Frame):
    """Small application chrome around a campaign-centric workspace.

    Roster, inventory, battle history and post-battle are no longer global
    destinations. They are contextual views of a moment selected in Campaign.
    """

    def __init__(self, master: tk.Misc, controller: AppController, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        self.nav_buttons: dict[str, ttk.Button] = {}
        self.action_buttons: list[tuple[ttk.Button, str]] = []
        self.pack(fill="both", expand=True)
        self._build_header()
        self.winfo_toplevel().bind_all("<Control-z>", self._undo_shortcut)
        self.content = tk.Frame(self, bg=COLORS["bg"], padx=12, pady=10)
        self.content.pack(fill="both", expand=True)
        controller.subscribe(self.render)
        controller.subscribe_undo(self._refresh_undo)
        self.render()

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=COLORS["bg"], height=62)
        header.pack(fill="x")
        header.pack_propagate(False)

        title = tk.Frame(header, bg=COLORS["bg"], padx=15)
        title.pack(side="left", fill="y")
        self.title_var = tk.StringVar(value=tr('MORDHEIM CAMPAIGN MANAGER'))
        self.subtitle_var = tk.StringVar(value=tr('A WARBAND THROUGH TIME'))
        tk.Label(title, textvariable=self.title_var, bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 14)).pack(anchor="w", pady=(9, 0))
        tk.Label(title, textvariable=self.subtitle_var, bg=COLORS["bg"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(2, 0))

        nav = tk.Frame(header, bg=COLORS["bg"])
        nav.pack(side="left", fill="y", padx=(22, 0))
        for key, label, icon in NAV:
            btn = ttk.Button(
                nav, text=tr(label), image=ui_icon(self, icon, 19), compound="left",
                style="Nav.TButton", command=lambda k=key: self.controller.navigate(k),
            )
            btn.pack(side="left", fill="y", padx=1)
            self.nav_buttons[key] = btn

        actions = tk.Frame(header, bg=COLORS["bg"], padx=12)
        actions.pack(side="right", fill="y")
        handlers = (
            ('New Campaign', "campaign_navigation_initial_warband", lambda: NewCampaignDialog(self, self.controller)),
            ('Campaigns', "campaign_navigation_campaign", self._open_library),
            ("Load", "campaign_file_load", lambda: load_campaign_file(self, self.controller)),
            ("Save", "campaign_file_save", lambda: save_current_campaign(self, self.controller)),
            ('Export PDF', "campaign_file_export", lambda: export_warband_pdf(self, self.controller)),
        )
        for text, icon, handler in handlers:
            button = ttk.Button(
                actions, text=tr(text), image=ui_icon(self, icon, 17), compound="left",
                style="Ghost.TButton", command=handler,
            )
            button.pack(side="left", pady=13, padx=2)
            self.action_buttons.append((button, text))

        self.undo_button = ttk.Button(
            actions, text=tr('Undo'), image=ui_icon(self, "campaign_dice_undo", 17), compound="left",
            style="Ghost.TButton", command=self.controller.undo,
        )
        self.undo_button.pack(side="left", pady=13, padx=2, before=self.action_buttons[-1][0])

        tk.Frame(self, bg=COLORS["border_soft"], height=1).pack(fill="x")

    def _open_library(self) -> None:
        from mordheim_campaign.ui.dialogs.campaign_library import CampaignLibraryDialog
        CampaignLibraryDialog(self, self.controller)

    def render(self) -> None:
        self.title_var.set(tr('MORDHEIM CAMPAIGN MANAGER'))
        self.subtitle_var.set(tr('A WARBAND THROUGH TIME'))
        labels = {key: label for key, label, _icon in NAV}
        for key, button in self.nav_buttons.items():
            button.configure(text=tr(labels[key]))
            button.configure(style="NavActive.TButton" if key == self.controller.state.active_view else "Nav.TButton")
        for button, label in self.action_buttons:
            button.configure(text=tr(label))
        self._refresh_undo()
        for child in self.content.winfo_children():
            child.destroy()
        view_type = VIEWS.get(self.controller.state.active_view, CampaignView)
        view_type(self.content, self.controller).pack(fill="both", expand=True)

    def _undo_shortcut(self, _event=None):
        if self.controller.can_undo:
            self.controller.undo()
        return "break"

    def _refresh_undo(self) -> None:
        self.undo_button.configure(
            text=tr(self.controller.undo_label),
            state="normal" if self.controller.can_undo else "disabled",
        )

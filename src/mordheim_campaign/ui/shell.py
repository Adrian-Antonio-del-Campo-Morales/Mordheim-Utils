from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.ui.file_actions import export_campaign_markdown, load_campaign_file, save_current_campaign
from mordheim_campaign.ui.views import CampaignView, RulesView, SettingsView
from mordheim_ui.theme import COLORS


VIEWS = {
    "campaign": CampaignView,
    "rules": RulesView,
    "settings": SettingsView,
}

NAV = [
    ("campaign", "CAMPAIGN"),
    ("rules", "RULES"),
    ("settings", "SETTINGS"),
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
        self.pack(fill="both", expand=True)
        self._build_header()
        self.content = tk.Frame(self, bg=COLORS["bg"], padx=12, pady=10)
        self.content.pack(fill="both", expand=True)
        controller.subscribe(self.render)
        self.render()

    def _build_header(self) -> None:
        header = tk.Frame(self, bg=COLORS["bg"], height=62)
        header.pack(fill="x")
        header.pack_propagate(False)

        title = tk.Frame(header, bg=COLORS["bg"], padx=15)
        title.pack(side="left", fill="y")
        tk.Label(title, text="MORDHEIM CAMPAIGN MANAGER", bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 14)).pack(anchor="w", pady=(9, 0))
        tk.Label(title, text="A WARBAND THROUGH TIME", bg=COLORS["bg"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(2, 0))

        nav = tk.Frame(header, bg=COLORS["bg"])
        nav.pack(side="left", fill="y", padx=(22, 0))
        for key, label in NAV:
            btn = ttk.Button(nav, text=label, style="Nav.TButton", command=lambda k=key: self.controller.navigate(k))
            btn.pack(side="left", fill="y", padx=1)
            self.nav_buttons[key] = btn

        actions = tk.Frame(header, bg=COLORS["bg"], padx=12)
        actions.pack(side="right", fill="y")
        handlers = {
            "Load": lambda: load_campaign_file(self, self.controller),
            "Save": lambda: save_current_campaign(self, self.controller),
            "Export": lambda: export_campaign_markdown(self, self.controller),
        }
        for text, handler in handlers.items():
            ttk.Button(actions, text=text, style="Ghost.TButton", command=handler).pack(side="left", pady=13, padx=2)

        tk.Frame(self, bg=COLORS["border_soft"], height=1).pack(fill="x")

    def render(self) -> None:
        for key, button in self.nav_buttons.items():
            button.configure(style="NavActive.TButton" if key == self.controller.state.active_view else "Nav.TButton")
        for child in self.content.winfo_children():
            child.destroy()
        view_type = VIEWS.get(self.controller.state.active_view, CampaignView)
        view_type(self.content, self.controller).pack(fill="both", expand=True)

from __future__ import annotations

import tkinter as tk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.ui.shell import AppShell
from mordheim_ui.theme import COLORS, configure_theme


class CampaignManagerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        configure_theme(self)
        self.configure(bg=COLORS["bg"])
        self.title("Mordheim Campaign Manager — GUI Prototype")
        self.geometry("1560x900")
        self.minsize(1280, 760)
        self.controller = AppController()
        AppShell(self, self.controller)


def main() -> int:
    app = CampaignManagerApp()
    app.mainloop()
    return 0

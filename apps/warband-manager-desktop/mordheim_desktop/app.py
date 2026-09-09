from __future__ import annotations

"""Desktop composition root (Tkinter): wires the campaign application layer
with the `mordheim_ui` adapter. Lives in `apps/warband-manager-desktop` per
the target architecture; the campaign packages stay UI-agnostic."""

import tkinter as tk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.ui.shell import AppShell
from mordheim_knowledge.i18n import set_locale as set_kb_locale
from mordheim_ui.i18n import set_locale as set_ui_locale
from mordheim_ui.theme import COLORS, configure_theme


class CampaignManagerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        # Display locale of KB names and interface strings (MORDHEIM_LOCALE).
        set_kb_locale()
        set_ui_locale()
        configure_theme(self)
        self.configure(bg=COLORS["bg"])
        self.title("Mordheim Campaign Manager — GUI Prototype")
        self.geometry("1560x900")
        self.minsize(1280, 760)
        self.controller = AppController()
        # Desktop locale wiring: the application layer fans locale switches
        # out to registered callbacks instead of importing the singletons, so
        # the same controller works in the web adapter.
        self.controller.subscribe_locale(set_ui_locale)
        self.controller.subscribe_locale(set_kb_locale)
        AppShell(self, self.controller)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _close(self) -> None:
        from mordheim_campaign.ui.file_actions import confirm_discard_changes
        if confirm_discard_changes(self, self.controller):
            self.destroy()


def main() -> int:
    app = CampaignManagerApp()
    app.mainloop()
    return 0

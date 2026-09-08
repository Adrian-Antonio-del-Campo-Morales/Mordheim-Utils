from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, ttk

from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, PageHeader
from mordheim_ui.i18n import tr


class SettingsView(tk.Frame):
    def __init__(self, master: tk.Misc, controller, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.columnconfigure(0, weight=1)
        PageHeader(self, tr('Settings'), tr('Campaign preferences, ruleset selection and presentation options.')).grid(row=0, column=0, sticky="ew", pady=(0, 10))
        box = BorderedFrame(self, background=COLORS["panel"], padding=1)
        box.grid(row=1, column=0, sticky="ew")
        body = box.body
        body.configure(padx=18, pady=18)
        language = tk.Frame(body, bg=COLORS["panel"], pady=7); language.pack(fill="x")
        tk.Label(language, text=tr('Language').upper(), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left")
        from mordheim_ui.i18n import current_locale
        locale = tk.StringVar(value="Español" if current_locale() == "es" else "English")
        ttk.OptionMenu(language, locale, locale.get(), "English", "Español",
                       command=lambda value: self._set_locale(controller, value)).pack(side="right")
        folder = tk.Frame(body, bg=COLORS["panel"], pady=7); folder.pack(fill="x")
        tk.Label(folder, text=tr('Campaign folder').upper(), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left")
        self.folder_var = tk.StringVar(value=str(controller.campaign_library_path))
        ttk.Button(folder, textvariable=self.folder_var, command=lambda: self._folder(controller)).pack(side="right")

    def _set_locale(self, controller, value: str) -> None:
        from mordheim_knowledge.i18n import set_locale as set_kb_locale
        from mordheim_ui.i18n import set_locale as set_ui_locale
        locale = "es" if value == "Español" else "en"
        set_ui_locale(locale); set_kb_locale(locale); controller.notify()

    def _folder(self, controller) -> None:
        from pathlib import Path
        selected = filedialog.askdirectory(parent=self, initialdir=controller.campaign_library_path)
        if selected:
            controller.campaign_library_path = Path(selected); self.folder_var.set(selected)

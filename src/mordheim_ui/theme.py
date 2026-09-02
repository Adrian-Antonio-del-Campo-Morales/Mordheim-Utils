from __future__ import annotations

import tkinter as tk
from tkinter import ttk


# Based on the palette of the existing prototype, expanded with semantic tokens.
COLORS = {
    "bg": "#11151a",
    "panel": "#191e24",
    "panel_alt": "#1e242b",
    "panel_soft": "#242b34",
    "panel_deep": "#14191f",
    "border": "#39424d",
    "border_soft": "#2e3741",
    "text": "#eef1f4",
    "muted": "#aab5c5",
    "muted_dark": "#75808e",
    "accent": "#bf8b3f",
    "accent_hover": "#d39d4d",
    "accent_dark": "#8d642d",
    "danger": "#c95b55",
    "danger_dark": "#4d2828",
    "success": "#82b36a",
    "success_dark": "#263b28",
    "info": "#7fa2c2",
    "entry": "#20262e",
    "black": "#0d1014",
    "white": "#ffffff",
}


def configure_theme(root: tk.Misc) -> ttk.Style:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.option_add("*Font", ("Segoe UI", 9))
    root.option_add("*tearOff", False)

    style.configure("App.TFrame", background=COLORS["bg"])
    style.configure("Panel.TFrame", background=COLORS["panel"])
    style.configure("PanelAlt.TFrame", background=COLORS["panel_alt"])
    style.configure("PanelDeep.TFrame", background=COLORS["panel_deep"])
    style.configure("Card.TFrame", background=COLORS["panel_alt"])

    style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
    style.configure("AppTitle.TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Georgia", 16))
    style.configure("AppSubtitle.TLabel", background=COLORS["bg"], foreground=COLORS["accent"], font=("Segoe UI Semibold", 9))
    style.configure("Title.TLabel", background=COLORS["bg"], foreground=COLORS["text"], font=("Segoe UI Semibold", 14))
    style.configure("Section.TLabel", background=COLORS["panel"], foreground=COLORS["text"], font=("Segoe UI Semibold", 10))
    style.configure("SectionAlt.TLabel", background=COLORS["panel_alt"], foreground=COLORS["text"], font=("Segoe UI Semibold", 10))
    style.configure("CardTitle.TLabel", background=COLORS["panel_alt"], foreground=COLORS["text"], font=("Georgia", 11, "bold"))
    style.configure("CardText.TLabel", background=COLORS["panel_alt"], foreground=COLORS["text"])
    style.configure("CardMuted.TLabel", background=COLORS["panel_alt"], foreground=COLORS["muted"])
    style.configure("Muted.TLabel", background=COLORS["bg"], foreground=COLORS["muted"])
    style.configure("PanelMuted.TLabel", background=COLORS["panel"], foreground=COLORS["muted"])
    style.configure("PanelText.TLabel", background=COLORS["panel"], foreground=COLORS["text"])
    style.configure("MetricName.TLabel", background=COLORS["panel"], foreground=COLORS["muted"], font=("Segoe UI", 8))
    style.configure("MetricValue.TLabel", background=COLORS["panel"], foreground=COLORS["text"], font=("Segoe UI Semibold", 12))
    style.configure("AccentText.TLabel", background=COLORS["panel"], foreground=COLORS["accent"], font=("Segoe UI Semibold", 9))
    style.configure("Success.TLabel", background=COLORS["panel"], foreground=COLORS["success"], font=("Segoe UI Semibold", 10))
    style.configure("DangerText.TLabel", background=COLORS["panel"], foreground=COLORS["danger"], font=("Segoe UI Semibold", 10))

    style.configure(
        "TButton",
        background=COLORS["panel_soft"], foreground=COLORS["text"],
        bordercolor=COLORS["border"], lightcolor=COLORS["panel_soft"], darkcolor=COLORS["panel_soft"],
        padding=(12, 7), relief="flat",
    )
    style.map("TButton", background=[("active", "#2b333d"), ("pressed", "#303944")])

    style.configure(
        "Accent.TButton",
        background=COLORS["accent"], foreground=COLORS["black"], bordercolor=COLORS["accent_dark"],
        lightcolor=COLORS["accent"], darkcolor=COLORS["accent"], padding=(14, 8), font=("Segoe UI Semibold", 9),
    )
    style.map("Accent.TButton", background=[("active", COLORS["accent_hover"]), ("pressed", COLORS["accent_dark"])])

    style.configure(
        "Ghost.TButton",
        background=COLORS["bg"], foreground=COLORS["muted"], bordercolor=COLORS["bg"],
        lightcolor=COLORS["bg"], darkcolor=COLORS["bg"], padding=(10, 7),
    )
    style.map("Ghost.TButton", background=[("active", COLORS["panel_soft"])], foreground=[("active", COLORS["text"])])

    style.configure(
        "Nav.TButton",
        background=COLORS["bg"], foreground=COLORS["muted"], bordercolor=COLORS["bg"],
        lightcolor=COLORS["bg"], darkcolor=COLORS["bg"], padding=(14, 15), font=("Segoe UI Semibold", 9),
    )
    style.map("Nav.TButton", background=[("active", COLORS["panel_deep"])], foreground=[("active", COLORS["text"])])

    style.configure(
        "NavActive.TButton",
        background=COLORS["panel_deep"], foreground=COLORS["text"], bordercolor=COLORS["accent"],
        lightcolor=COLORS["panel_deep"], darkcolor=COLORS["panel_deep"], padding=(14, 15), font=("Segoe UI Semibold", 9),
    )

    style.configure(
        "Mini.TButton",
        background=COLORS["panel_soft"], foreground=COLORS["text"], bordercolor=COLORS["border"],
        lightcolor=COLORS["panel_soft"], darkcolor=COLORS["panel_soft"], padding=(8, 4), font=("Segoe UI", 8),
    )

    style.configure(
        "Danger.TButton",
        background=COLORS["panel_soft"], foreground="#e5aaa7", bordercolor=COLORS["border"], padding=(10, 5),
    )
    style.map("Danger.TButton", background=[("active", COLORS["danger_dark"])])

    style.configure("TEntry", fieldbackground=COLORS["entry"], foreground=COLORS["text"], bordercolor=COLORS["border"], insertcolor=COLORS["text"], padding=7)
    style.map("TEntry", bordercolor=[("focus", COLORS["accent"])])
    style.configure("TCombobox", fieldbackground=COLORS["entry"], background=COLORS["entry"], foreground=COLORS["text"], bordercolor=COLORS["border"], arrowcolor=COLORS["muted"], padding=6)
    style.map("TCombobox", fieldbackground=[("readonly", COLORS["entry"])], foreground=[("readonly", COLORS["text"])], bordercolor=[("focus", COLORS["accent"])])
    style.configure("TSpinbox", fieldbackground=COLORS["entry"], foreground=COLORS["text"], bordercolor=COLORS["border"], arrowcolor=COLORS["muted"], padding=5)

    style.configure("TNotebook", background=COLORS["bg"], borderwidth=0, tabmargins=(0, 0, 0, 0))
    style.configure("TNotebook.Tab", background=COLORS["panel"], foreground=COLORS["muted"], bordercolor=COLORS["border"], padding=(18, 9), font=("Segoe UI Semibold", 9))
    style.map("TNotebook.Tab", background=[("selected", COLORS["panel_alt"]), ("active", COLORS["panel_soft"])], foreground=[("selected", COLORS["accent"]), ("active", COLORS["text"])])

    style.configure("Vertical.TScrollbar", background=COLORS["panel_soft"], troughcolor=COLORS["bg"], arrowcolor=COLORS["muted"])
    return style

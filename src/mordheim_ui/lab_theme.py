"""ui.theme: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from tkinter import ttk


COLORS = {
    "bg": "#17191D",
    "surface": "#202329",
    "surface_alt": "#272B32",
    "surface_hover": "#30353D",
    "border": "#383D46",
    "border_light": "#454B56",
    "text": "#EEEDE8",
    "text_muted": "#A6ABB3",
    "text_disabled": "#686D75",
    "accent": "#B68A4A",
    "accent_hover": "#C99A55",
    "accent_pressed": "#9F743B",
    "danger": "#B94A48",
    "danger_hover": "#CC5754",
    "success": "#4E9668",
    "warning": "#C69A4B",
    "selection": "#343B45",
}


def apply_theme(root) -> None:
    """Apply the previous UI's ``clam`` styles to the new widget tree."""
    style = ttk.Style(root)
    style.theme_use("clam")
    root.configure(background=COLORS["bg"])
    default_font = ("Segoe UI", 10)
    root.option_add("*Font", default_font)
    # Pop-up menus are classic Tk widgets, not ttk widgets.  Configure them
    # through the option database so Collections, Import and Equipment share
    # the dark workbook surface on every platform.
    root.option_add("*Menu.Font", default_font)
    root.option_add("*Menu.background", COLORS["surface_alt"])
    root.option_add("*Menu.foreground", COLORS["text"])
    root.option_add("*Menu.activeBackground", COLORS["accent"])
    root.option_add("*Menu.activeForeground", "#111111")
    root.option_add("*Menu.selectColor", COLORS["accent"])
    root.option_add("*Menu.borderWidth", 0)
    root.option_add("*Menu.relief", "flat")
    root.option_add("*TCombobox*Listbox.background", COLORS["surface_alt"])
    root.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", COLORS["accent"])
    root.option_add("*TCombobox*Listbox.selectForeground", "#111111")
    root.option_add("*TCombobox*Listbox.highlightThickness", 0)
    root.option_add("*TCombobox*Listbox.font", default_font)
    style.configure(".", background=COLORS["bg"], foreground=COLORS["text"], fieldbackground=COLORS["surface"], bordercolor=COLORS["border"], font=default_font)
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Card.TFrame", background=COLORS["surface"])
    # Attribute cells were visually distinct cards in the workbook UI.  Keep
    # the border on the frame itself so the grouping survives all platform
    # themes, including Windows' clam fallback.
    style.configure("Stat.TFrame", background=COLORS["surface"], bordercolor=COLORS["border"], borderwidth=1, relief="solid")
    style.configure("TLabel", background=COLORS["bg"], foreground=COLORS["text"])
    style.configure("Muted.TLabel", foreground=COLORS["text_muted"])
    style.configure("Title.TLabel", font=("Segoe UI Semibold", 18))
    style.configure("Heading.TLabel", font=("Segoe UI Semibold", 15))
    style.configure("Section.TLabel", font=("Segoe UI Semibold", 11))
    style.configure("Card.TLabel", background=COLORS["surface"], foreground=COLORS["text"])
    style.configure("Card.Muted.TLabel", background=COLORS["surface"], foreground=COLORS["text_muted"])
    style.configure("TButton", padding=(12, 7), background=COLORS["surface_alt"], foreground=COLORS["text"], bordercolor=COLORS["border"], relief="flat")
    style.map("TButton", background=[("pressed", COLORS["surface_hover"]), ("active", COLORS["surface_hover"]), ("disabled", COLORS["surface"])], foreground=[("disabled", COLORS["text_disabled"])])
    style.configure("Stat.TButton", padding=(5, 9), background=COLORS["surface_alt"], foreground=COLORS["text"], bordercolor=COLORS["border"], width=2, font=("Segoe UI Semibold", 14))
    style.map("Stat.TButton", background=[("pressed", COLORS["accent_pressed"]), ("active", COLORS["surface_hover"])])
    style.configure("Stat.TEntry", fieldbackground=COLORS["bg"], foreground=COLORS["text"], bordercolor=COLORS["border"], justify="center", padding=(3, 2))
    style.configure("StatValue.TEntry", fieldbackground=COLORS["bg"], foreground=COLORS["text"], bordercolor=COLORS["accent"], justify="center", padding=(8, 8), font=("Segoe UI Semibold", 24))
    style.configure("Accent.TButton", background=COLORS["accent"], foreground="#111111", bordercolor=COLORS["accent"], font=("Segoe UI Semibold", 10), padding=(16, 8))
    style.map("Accent.TButton", background=[("pressed", COLORS["accent_pressed"]), ("active", COLORS["accent_hover"]), ("disabled", COLORS["surface_alt"])])
    style.configure("TCombobox", fieldbackground=COLORS["surface_alt"], background=COLORS["surface_alt"], foreground=COLORS["text"], arrowcolor=COLORS["text_muted"], bordercolor=COLORS["border"], padding=(6, 5))
    style.map("TCombobox", fieldbackground=[("readonly", COLORS["surface_alt"]), ("disabled", COLORS["surface"])], foreground=[("disabled", COLORS["text_disabled"])], bordercolor=[("focus", COLORS["accent"])])
    style.configure("TMenubutton", padding=(10, 6), background=COLORS["surface_alt"], foreground=COLORS["text"], bordercolor=COLORS["border"], relief="flat")
    style.map("TMenubutton", background=[("pressed", COLORS["surface_hover"]), ("active", COLORS["surface_hover"]), ("disabled", COLORS["surface"])], foreground=[("disabled", COLORS["text_disabled"])])
    style.configure("Card.TMenubutton", padding=(7, 5), background=COLORS["surface_alt"], foreground=COLORS["text"], bordercolor=COLORS["border"], relief="flat")
    style.map("Card.TMenubutton", background=[("pressed", COLORS["surface_hover"]), ("active", COLORS["surface_hover"])])
    style.configure("TSpinbox", fieldbackground=COLORS["surface_alt"], foreground=COLORS["text"], arrowcolor=COLORS["text_muted"], bordercolor=COLORS["border"], padding=(5, 5))
    style.configure("TNotebook", background=COLORS["bg"], borderwidth=0, tabmargins=(12, 6, 12, 0))
    style.configure("TNotebook.Tab", background=COLORS["bg"], foreground=COLORS["text_muted"], padding=(15, 9), font=("Segoe UI Semibold", 8))
    style.map("TNotebook.Tab", background=[("selected", COLORS["surface"]), ("active", COLORS["surface_alt"])], foreground=[("selected", COLORS["accent"]), ("active", COLORS["text"])])
    style.configure("TLabelframe", background=COLORS["surface"], bordercolor=COLORS["border"], borderwidth=1, relief="solid")
    style.configure("TLabelframe.Label", background=COLORS["surface"], foreground=COLORS["text"], font=("Segoe UI Semibold", 10))
    style.configure("Treeview", background=COLORS["surface"], fieldbackground=COLORS["surface"], foreground=COLORS["text"], rowheight=30)
    style.map("Treeview", background=[("selected", COLORS["selection"])], foreground=[("selected", COLORS["text"])])
    style.configure("Treeview.Heading", background=COLORS["surface_alt"], foreground=COLORS["text_muted"], font=("Segoe UI Semibold", 9), padding=(6, 8))
    style.configure("Horizontal.TProgressbar", background=COLORS["accent"], troughcolor=COLORS["surface_alt"], bordercolor=COLORS["surface_alt"], borderwidth=0, thickness=7)

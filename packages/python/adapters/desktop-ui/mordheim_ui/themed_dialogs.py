from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_ui.theme import COLORS
from mordheim_ui.windowing import center_on_application
from mordheim_ui.icons import ui_icon


def _dialog(title: str, message: str, parent=None, *, danger: bool = False):
    owner = parent.winfo_toplevel() if parent is not None else tk._get_default_root()
    window = tk.Toplevel(owner)
    window.title(title)
    window.configure(bg=COLORS["bg"])
    window.transient(owner)
    window.grab_set()
    window.resizable(False, False)
    body = tk.Frame(window, bg=COLORS["panel"], padx=20, pady=18)
    body.pack(fill="both", expand=True, padx=1, pady=1)
    tk.Label(body, text=title.upper(), bg=COLORS["panel"], fg=COLORS["danger"] if danger else COLORS["accent"],
             font=("Segoe UI Semibold", 8)).pack(anchor="w")
    message_row = tk.Frame(body, bg=COLORS["panel"])
    message_row.pack(fill="x", pady=(8, 14))
    tk.Label(
        message_row,
        image=ui_icon(window, "campaign_dice_error" if danger else "campaign_dice_confirm", 42),
        bg=COLORS["panel"],
    ).pack(side="left", padx=(0, 14))
    tk.Label(message_row, text=message, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9),
             wraplength=430, justify="left").pack(side="left", fill="x", expand=True)
    actions = tk.Frame(body, bg=COLORS["panel"])
    actions.pack(fill="x")
    window.after_idle(lambda: center_on_application(window))
    return window, body, actions


def showerror(title: str, message: str, *, parent=None, **_kwargs):
    window, _body, actions = _dialog(title, message, parent, danger=True)
    ttk.Button(actions, text="OK", style="Accent.TButton", command=window.destroy).pack(side="right")
    window.bind("<Return>", lambda _e: window.destroy())
    window.bind("<Escape>", lambda _e: window.destroy())
    window.wait_window()
    return "ok"


def askyesno(title: str, message: str, *, parent=None, **_kwargs) -> bool:
    window, _body, actions = _dialog(title, message, parent)
    result = [False]
    ttk.Button(actions, text="CANCEL", command=window.destroy).pack(side="right", padx=(6, 0))
    ttk.Button(actions, text="CONFIRM", style="Accent.TButton",
               command=lambda: (result.__setitem__(0, True), window.destroy())).pack(side="right")
    window.bind("<Escape>", lambda _e: window.destroy())
    window.wait_window()
    return result[0]


def _ask_value(title: str, prompt: str, *, parent=None, initialvalue=None, integer: bool = False,
               minvalue=None, maxvalue=None):
    window, body, actions = _dialog(title, prompt, parent)
    variable = tk.IntVar(value=initialvalue if initialvalue is not None else minvalue or 1) if integer else tk.StringVar(value=initialvalue or "")
    field = (ttk.Spinbox(body, textvariable=variable, from_=minvalue if minvalue is not None else -999999,
                         to=maxvalue if maxvalue is not None else 999999, width=12)
             if integer else ttk.Entry(body, textvariable=variable, width=42))
    field.pack(fill="x", before=actions, pady=(0, 14))
    result = []

    def confirm() -> None:
        try:
            value = int(variable.get()) if integer else str(variable.get())
        except (TypeError, ValueError, tk.TclError):
            return
        if minvalue is not None and value < minvalue or maxvalue is not None and value > maxvalue:
            return
        result.append(value)
        window.destroy()

    ttk.Button(actions, text="CANCEL", command=window.destroy).pack(side="right", padx=(6, 0))
    ttk.Button(actions, text="OK", style="Accent.TButton", command=confirm).pack(side="right")
    window.bind("<Return>", lambda _e: confirm())
    window.bind("<Escape>", lambda _e: window.destroy())
    field.focus_set()
    if not integer:
        field.selection_range(0, "end")
    window.wait_window()
    return result[0] if result else None


def askstring(title: str, prompt: str, *, parent=None, initialvalue=None, **_kwargs):
    return _ask_value(title, prompt, parent=parent, initialvalue=initialvalue)


def askinteger(title: str, prompt: str, *, parent=None, initialvalue=None, minvalue=None, maxvalue=None, **_kwargs):
    return _ask_value(title, prompt, parent=parent, initialvalue=initialvalue, integer=True, minvalue=minvalue, maxvalue=maxvalue)

"""Application startup and fatal-error handling."""

import os
import sys
import tkinter as tk
import traceback
from multiprocessing import freeze_support
from tkinter import messagebox

from .ui import CombatLabApp


def _show_fatal_startup_error(exc):
    error_text = "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "Mordheim Combat Lab - Startup error",
            "Mordheim Combat Lab could not start.\n\n" + error_text,
        )
        root.destroy()
    except Exception:
        try:
            base = (
                os.path.dirname(sys.executable)
                if getattr(sys, "frozen", False)
                else os.getcwd()
            )
            with open(
                os.path.join(base, "MordheimCombatLab_startup_error.txt"),
                "w",
                encoding="utf-8",
            ) as error_file:
                error_file.write(error_text)
        except Exception:
            pass


def _configure_frozen_runtime():
    if getattr(sys, "frozen", False):
        try:
            os.chdir(os.path.dirname(sys.executable))
        except Exception:
            pass


def main():
    try:
        freeze_support()
        _configure_frozen_runtime()
        app = CombatLabApp()
        app.mainloop()
    except Exception as exc:
        _show_fatal_startup_error(exc)
        return 1
    return 0

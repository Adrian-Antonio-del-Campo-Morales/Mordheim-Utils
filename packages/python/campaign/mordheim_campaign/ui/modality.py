"""Restore the previous modal editor when a nested dialog closes."""
import tkinter as tk


def make_modal(window, owner):
    previous = window.grab_current()
    window.transient(owner.winfo_toplevel())
    window.grab_set()

    def restore(event):
        if event.widget is not window or previous is None:
            return
        try:
            if previous.winfo_exists() and window.grab_current() in (None, window):
                previous.grab_set()
        except tk.TclError:
            pass  # The whole application may be closing.

    window.bind('<Destroy>', restore, add='+')

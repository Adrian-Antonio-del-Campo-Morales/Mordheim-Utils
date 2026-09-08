from __future__ import annotations

import tkinter as tk


def center_on_application(window: tk.Toplevel) -> None:
    """Place a completed dialog at the centre of the application window."""
    application = window._root()
    application.update_idletasks()
    window.update_idletasks()

    # Requested dimensions are stable before the window manager maps the
    # dialog. winfo_width/height can still report 1 here on Windows, placing
    # the dialog noticeably down and right of the real centre.
    width = max(window.winfo_reqwidth(), window.winfo_width())
    height = max(window.winfo_reqheight(), window.winfo_height())
    x = application.winfo_rootx() + (application.winfo_width() - width) // 2
    y = application.winfo_rooty() + (application.winfo_height() - height) // 2

    window.geometry(f"{width}x{height}{x:+d}{y:+d}")

"""ui.widgets.feedback: responsibility extracted without altering the rules."""
from __future__ import annotations

from mordheim_ui.lab_theme import COLORS
import tkinter as tk


TOOLTIP_DELAY_MS = 400


class _TooltipManager:
    """One delayed, reusable tooltip window for an application toplevel."""

    def __init__(self, root):
        self.root = root
        self._after_id = None
        self._after_source = None
        self._source = None
        self._text = ""
        self._position = (0, 0)
        self._window = None
        self._label = None

    def schedule(self, source, text, x: int, y: int) -> None:
        """Show ``text`` after a short hover delay, replacing any pending tip."""
        content = text() if callable(text) else text
        self.hide()
        if not content:
            return
        self._source, self._text, self._position = source, str(content), (x, y)
        self._after_id = source.after(TOOLTIP_DELAY_MS, self._show)
        self._after_source = source

    def hide(self, source=None) -> None:
        """Cancel a pending tooltip and hide the reusable window."""
        if source is not None and source is not self._source:
            return
        if self._after_id is not None:
            try:
                # ``after`` callbacks are registered on their originating
                # widget.  Cancelling through the root leaves that widget's
                # Tcl command registered and makes Tk try to delete it again
                # during shutdown.
                self._after_source.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None
            self._after_source = None
        if self._window is not None:
            try:
                self._window.withdraw()
            except tk.TclError:
                self._window = None
                self._label = None
        self._source = None

    def _show(self) -> None:
        self._after_id = None
        self._after_source = None
        if self._source is None:
            return
        try:
            if self._window is None or not self._window.winfo_exists():
                self._window = tk.Toplevel(self.root)
                self._window.wm_overrideredirect(True)
                self._label = tk.Label(
                    self._window,
                    justify=tk.LEFT,
                    background=COLORS["surface_alt"],
                    foreground=COLORS["text"],
                    relief=tk.SOLID,
                    borderwidth=1,
                    font=("Segoe UI", 9),
                    wraplength=420,
                )
                self._label.pack(ipadx=5, ipady=3)
            self._label.configure(text=self._text)
            x, y = self._position
            self._window.wm_geometry(f"+{x}+{y}")
            self._window.deiconify()
            self._window.lift()
        except tk.TclError:
            self._window = None
            self._label = None

    def destroy(self) -> None:
        """Release pending callbacks and the reusable window before root teardown."""
        self.hide()
        if self._window is not None:
            try:
                self._window.destroy()
            except tk.TclError:
                pass
        self._window = None
        self._label = None


def tooltip_manager(widget) -> _TooltipManager:
    """Return the single tooltip manager owned by ``widget``'s toplevel."""
    root = widget.winfo_toplevel()
    manager = getattr(root, "_combat_lab_tooltip_manager", None)
    if manager is None:
        manager = _TooltipManager(root)
        setattr(root, "_combat_lab_tooltip_manager", manager)
    return manager


def destroy_tooltips(root) -> None:
    """Tear down the root's shared tooltip before Tk destroys its children."""
    manager = getattr(root, "_combat_lab_tooltip_manager", None)
    if manager is not None:
        manager.destroy()


class ToolTip:
    """Attach the shared delayed tooltip manager to an ordinary Tk widget."""

    def __init__(self, widget, text):
        self.widget, self.text = widget, text
        widget.bind("<Enter>", self.show_tip, add="+")
        widget.bind("<Leave>", self.hide_tip, add="+")

    def show_tip(self, _event=None):
        tooltip_manager(self.widget).schedule(
            self.widget,
            self.text,
            self.widget.winfo_rootx() + 20,
            self.widget.winfo_rooty() + 20,
        )

    def hide_tip(self, _event=None):
        tooltip_manager(self.widget).hide(self.widget)

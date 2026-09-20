"""ui: Anchored popover with a scrollable checkbutton list.

Replaces ``tk.Menu`` pickers that outgrow the screen: fixed height,
scrollbar, menu-like dismissal (Escape, outside click) and a stacking order
forced above the application window. The window is positioned before it maps
and never uses the withdraw/deiconify dance, which is unreliable on Windows
for ``overrideredirect`` windows.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_ui.lab_theme import COLORS


class ChecklistPopover:
    """Small anchored window whose scrollable body the caller populates.

    Dismissal is menu-like: Escape, clicking the anchor again, or clicking
    anywhere outside the popover. Outside clicks are detected with a
    root-level binding rather than a global grab, which is unreliable on
    Windows.
    """

    def __init__(self, anchor, *, height: int = 280, min_width: int = 300):
        self.anchor = anchor
        self.height = height
        self.min_width = min_width
        self._window: tk.Toplevel | None = None
        self._root_bindings: tuple[tuple[str, str], ...] = ()
        self._anchor_unmap_funcid = ""
        #: Frames the caller fills in ``open``; ``None`` while closed.
        self.actions_frame: ttk.Frame | None = None
        self.scroll_frame: ttk.Frame | None = None

    @property
    def is_open(self) -> bool:
        return self._window is not None and bool(self._window.winfo_exists())

    def open(self, populate) -> None:
        """Build, position and map the popover.

        ``populate(actions, scroll_frame)`` fills the always-visible action
        row and the scrollable checklist body. The geometry is fixed before
        the window maps: mapping an ``overrideredirect`` window at the
        default position and moving it afterwards is the Windows failure
        mode that leaves the popover invisible behind the main window.
        """
        self.close()
        window = tk.Toplevel(self.anchor)
        window.overrideredirect(True)
        # Classic Tk widgets default to white; paint them with the workbook
        # surface so no unpainted strip ever flashes while the window maps.
        window.configure(background=COLORS["bg"])
        body = ttk.Frame(window, padding=(6, 4))
        body.pack(fill="both", expand=True)
        self.actions_frame = ttk.Frame(body)
        self.actions_frame.pack(fill="x")
        holder = ttk.Frame(body)
        holder.pack(fill="both", expand=True, pady=(4, 0))
        canvas = tk.Canvas(holder, height=self.height, width=120,
                           highlightthickness=0, background=COLORS["bg"])
        # Pack the scrollbar BEFORE the canvas: a canvas without an explicit
        # width requests ~10cm, and packed first it consumes the whole popover,
        # squeezing the scrollbar down to 0px (never mapped, never visible).
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview,
                                  style="Popover.Vertical.TScrollbar")
        scrollbar.pack(side="right", fill="y")
        self.scroll_frame = ttk.Frame(canvas, padding=(0, 2))
        self.scroll_frame.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        inner = canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        # Stretch the checklist to the full popover width: the frame's natural
        # width is its widest row, and the leftover canvas area would otherwise
        # show as an unpainted white strip on the right/bottom.
        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(inner, width=event.width),
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        # Wheel scrolling follows the pointer, as listbox menus do.
        for widget in (canvas, self.scroll_frame):
            widget.bind("<Enter>", lambda _e: canvas.bind_all("<MouseWheel>", lambda ev: canvas.yview_scroll(-1 * (ev.delta // 120), "units")))
            widget.bind("<Leave>", lambda _e: canvas.unbind_all("<MouseWheel>"))
        populate(self.actions_frame, self.scroll_frame)
        # Position BEFORE the first map: on Windows the position component of
        # ``wm geometry`` is ignored once an overrideredirect window is
        # mapped, so any intermediate ``update`` would pin it at (0, 0).
        x = self.anchor.winfo_rootx()
        y = self.anchor.winfo_rooty() + self.anchor.winfo_height() + 2
        width = max(self.anchor.winfo_width(), self.min_width)
        window.geometry(f"{width}x{self.height + 40}+{x}+{y}")
        window.lift()
        window.attributes("-topmost", True)
        window.bind("<Escape>", lambda _e: self.close())
        root = self.anchor.winfo_toplevel()
        self._root_bindings = (
            ("<Button-1>", root.bind("<Button-1>", self._on_root_click, add="+")),
            ("<Escape>", root.bind("<Escape>", lambda _e: self.close(), add="+")),
            ("<Configure>", root.bind("<Configure>", self._on_root_configure, add="+")),
        )
        # A tab switch, minimize or re-layout unmaps the anchor button.
        self._anchor_unmap_funcid = self.anchor.bind("<Unmap>", lambda _e: self.close(), add="+")
        self._window = window

    def _on_root_configure(self, event) -> None:
        """Close when the main window is resized or moved."""
        if not self.is_open:
            return
        try:
            if event.widget is self.anchor.winfo_toplevel():
                self.close()
        except tk.TclError:
            pass

    def _on_root_click(self, event) -> None:
        if not self.is_open:
            return
        anchor = self.anchor
        ax, ay = anchor.winfo_rootx(), anchor.winfo_rooty()
        if ax <= event.x_root < ax + anchor.winfo_width() and ay <= event.y_root < ay + anchor.winfo_height():
            return  # inside the anchor: its toggle command closes the popover
        window = self._window
        x0, y0 = window.winfo_rootx(), window.winfo_rooty()
        inside = (
            x0 <= event.x_root < x0 + window.winfo_width()
            and y0 <= event.y_root < y0 + window.winfo_height()
        )
        if not inside:
            self.close()

    def close(self) -> None:
        if self.is_open:
            try:
                self._window.unbind_all("<MouseWheel>")
                root = self.anchor.winfo_toplevel()
                for sequence, funcid in self._root_bindings:
                    root.unbind(sequence, funcid)
                self.anchor.unbind("<Unmap>", self._anchor_unmap_funcid)
            except tk.TclError:
                pass
            self._window.destroy()
        self._window = None
        self._root_bindings = ()
        self._anchor_unmap_funcid = ""
        self.actions_frame = None
        self.scroll_frame = None

"""external.test_checklist_popover: shared popover widget behaviour."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from mordheim_combat_lab.ui.widgets.checklist_popover import ChecklistPopover
from mordheim_ui.lab_theme import COLORS


@pytest.fixture(scope="module")
def root():
    try:
        instance = tk.Tk()
    except tk.TclError:  # headless environment
        pytest.skip("Tk display is not available")
    instance.geometry("+100+100")
    yield instance
    instance.destroy()


@pytest.fixture()
def anchor(root):
    anchor = ttk.Button(root, text="Picker")
    anchor.pack(padx=40, pady=40)
    root.update_idletasks()
    yield anchor
    anchor.destroy()


def _popover_rows(popover):
    return [
        child for child in popover.scroll_frame.winfo_children()
        if isinstance(child, ttk.Checkbutton)
    ]


def test_popover_maps_visible_and_above_the_anchor(root, anchor):
    popover = ChecklistPopover(anchor, height=200, min_width=260)
    popover.open(lambda actions, body: ttk.Checkbutton(body, text="Alpha").pack())

    try:
        assert popover.is_open
        # The Windows failure mode was a mapped-but-invisible window: assert
        # it is actually rendered, stacked above the app and on screen.
        assert root.state() != "withdrawn"
        assert popover._window.winfo_ismapped()
        assert int(popover._window.winfo_viewable()) == 1
        assert int(popover._window.winfo_rootx()) > 0
        assert int(popover._window.winfo_rooty()) > 0
        assert popover._window.winfo_rooty() >= anchor.winfo_rooty()
    finally:
        popover.close()
    assert not popover.is_open


def test_popover_dismisses_on_escape_and_outside_click(root, anchor):
    popover = ChecklistPopover(anchor)
    popover.open(lambda actions, body: ttk.Checkbutton(body, text="Alpha").pack())

    # Real users press Escape while focus rests in the main window (the
    # anchor button just received their click), so the root-level binding is
    # the dismissal path that matters.
    root.focus_set()
    root.update()
    root.event_generate("<Escape>")
    root.update()
    assert not popover.is_open

    popover.open(lambda actions, body: ttk.Checkbutton(body, text="Beta").pack())
    root.event_generate("<Button-1>", x=1, y=1)  # far from anchor and popover
    root.update()
    assert not popover.is_open, "an outside click must dismiss the popover"

    # Clicks on the anchor are left to the anchor's own toggle command.
    popover.open(lambda actions, body: ttk.Checkbutton(body, text="Gamma").pack())
    ax = anchor.winfo_rootx() + anchor.winfo_width() // 2 - root.winfo_rootx()
    ay = anchor.winfo_rooty() + anchor.winfo_height() // 2 - root.winfo_rooty()
    root.event_generate("<Button-1>", x=ax, y=ay)
    root.update()
    assert popover.is_open


def test_popover_repopulates_on_every_open(root, anchor):
    popover = ChecklistPopover(anchor)
    for label in ("One", "Two"):
        popover.open(lambda actions, body, label=label: ttk.Checkbutton(body, text=label).pack())
        assert [row.cget("text") for row in _popover_rows(popover)] == [label]
    popover.close()


def test_popover_shows_a_visible_scrollbar(root, anchor):
    """Regression: the canvas was packed first and its ~10cm width request
    squeezed the scrollbar to 0px (never mapped, never visible)."""
    popover = ChecklistPopover(anchor, height=280, min_width=300)
    def populate(actions, body):
        for index in range(17):
            ttk.Checkbutton(body, text=f"Skill {index}").pack(fill="x", pady=1)
    popover.open(populate)
    try:
        found = None
        stack = [popover._window]
        while stack:
            widget = stack.pop()
            if isinstance(widget, ttk.Scrollbar):
                found = widget
                break
            stack.extend(widget.winfo_children())
        assert found is not None, "the popover body has no scrollbar"
        root.update()
        assert found.winfo_ismapped(), "the scrollbar is not mapped"
        assert found.winfo_width() >= 10, "the scrollbar is squeezed to invisibility"
    finally:
        popover.close()


def _popover_canvas(popover):
    stack = [popover._window]
    while stack:
        widget = stack.pop()
        if isinstance(widget, tk.Canvas):
            return widget
        stack.extend(widget.winfo_children())
    raise AssertionError("the popover body has no canvas")


def test_popover_body_matches_the_dark_theme(root, anchor):
    """Regression: the classic Tk canvas painted a white strip wherever the
    checklist frame (natural width of its widest row) did not cover it."""
    popover = ChecklistPopover(anchor, height=200, min_width=300)
    popover.open(lambda actions, body: ttk.Checkbutton(body, text="Alpha").pack())
    try:
        canvas = _popover_canvas(popover)
        assert canvas.cget("background") == COLORS["bg"]
        assert popover._window.cget("background") == COLORS["bg"]
        root.update()
        # The inner frame stretches to the canvas width: no unpainted strip.
        assert popover.scroll_frame.winfo_width() == canvas.winfo_width()
    finally:
        popover.close()


def test_popover_closes_when_the_main_window_resizes_or_moves(root, anchor):
    popover = ChecklistPopover(anchor)
    popover.open(lambda actions, body: ttk.Checkbutton(body, text="Alpha").pack())
    root.geometry("640x520+100+100")  # resize
    root.update()
    assert not popover.is_open, "resizing the main window must dismiss the popover"

    popover.open(lambda actions, body: ttk.Checkbutton(body, text="Beta").pack())
    root.geometry("+150+130")  # move without resizing
    root.update()
    assert not popover.is_open, "moving the main window must dismiss the popover"


def test_combobox_popdown_shell_matches_the_dark_theme(root):
    """Regression: the popdown shell is a classic Tk toplevel and painted a
    white frame around the dark listbox (class ComboboxPopdown)."""
    import tkinter as tk
    from mordheim_ui.lab_theme import apply_theme

    apply_theme(root)
    combo = ttk.Combobox(root, values=("Alpha", "Beta"), state="readonly")
    combo.pack()
    root.update()
    popdown = str(root.tk.call("ttk::combobox::PopdownWindow", combo))
    try:
        assert root.tk.call(popdown, "cget", "-background") == COLORS["surface_alt"]
    finally:
        combo.destroy()  # the popdown is a child window of the combobox


def test_popover_closes_when_a_tab_switch_hides_the_anchor(root):
    notebook = ttk.Notebook(root)
    page1, page2 = ttk.Frame(notebook), ttk.Frame(notebook)
    notebook.add(page1, text="One")
    notebook.add(page2, text="Two")
    notebook.pack()
    tab_anchor = ttk.Button(page1, text="Picker")
    tab_anchor.pack(padx=20, pady=20)
    root.update()
    popover = ChecklistPopover(tab_anchor)
    try:
        popover.open(lambda actions, body: ttk.Checkbutton(body, text="Alpha").pack())
        assert popover.is_open
        notebook.select(page2)
        root.update()
        assert not popover.is_open, "a tab switch must dismiss the popover"
    finally:
        notebook.destroy()


def test_popover_rebuilds_with_fresh_variables(root, anchor):
    """Stale BooleanVars from a previous open must not leak into the checklist."""
    popover = ChecklistPopover(anchor)
    variables: list[tk.BooleanVar] = []

    def populate(actions, body):
        variable = tk.BooleanVar(value=True)
        variables.append(variable)
        ttk.Checkbutton(body, text="Alpha", variable=variable).pack()

    popover.open(populate)
    popover.close()
    variables[0].set(False)  # mutate after close: must not affect the next open
    popover.open(populate)
    assert variables[1].get() is True
    popover.close()

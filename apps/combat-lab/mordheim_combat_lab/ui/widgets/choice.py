"""ui: Translatable choice widgets decoupling data ids from display labels.

The workbook stores KB item ids (``weapon.fist``, ``material.normal``…)
internally while the comboboxes render localized labels. ``ChoiceVar`` holds
the current *value*; ``ChoiceBox`` is the readonly combobox bound to it.
"""
from __future__ import annotations

from mordheim_ui.i18n import tr

import tkinter as tk
from tkinter import ttk


class ChoiceVar:
    """Holds a data value and mirrors its localized label into ``variable``.

    An option may carry a *reason*: the shared eligibility module refused it in
    the current context. Incompatible options stay visible and disabled with
    that reason instead of disappearing, and the current selection is never
    changed silently — it stays until the user picks another value or clears it.
    """

    #: Suffix appended to the disabled label so the motive is visible inline.
    REASON_SEPARATOR = " — "

    def __init__(self, value=None, master=None):
        self.value = value
        self.variable = tk.StringVar(master=master, value="")
        self._options: dict[str | None, str] = {}
        self._reasons: dict[str | None, str] = {}
        self._boxes: list["ChoiceBox"] = []

    def subscribe(self, box: "ChoiceBox"):
        """Register a combobox so option changes keep its dropdown in sync."""
        self._boxes.append(box)
        box._sync_values()

    def set_options(self, options: dict[str | None, str], reasons: dict[str | None, str] | None = None):
        """Replace the choices. ``options`` maps data value → label key.

        ``reasons`` maps a data value → the shared decision's motive; those
        entries are disabled in the dropdown. The current value is retained
        even when it is refused, so an invalid existing selection remains
        visible and removable.
        """
        self._options = dict(options)
        self._reasons = {key: value for key, value in (reasons or {}).items() if value}
        self.variable.set(self.display_label(self.value) if self._has(self.value) else "")
        for box in self._boxes:
            box._sync_values()

    def display_label(self, value) -> str:
        """Localized label of one value, with its refusal motive when disabled."""
        label = tr(self._options.get(value, ""))
        reason = self._reasons.get(value, "").strip()
        return f"{label}{self.REASON_SEPARATOR}{reason}" if reason else label

    def option_labels(self) -> tuple[str, ...]:
        return tuple(self.display_label(value) for value in self._options)

    def reason(self, value=None) -> str:
        """Refusal motive of one value, or of the current selection."""
        return self._reasons.get(self.value if value is None else value, "")

    def set(self, value):
        self.value = value
        if self._has(value):
            self.variable.set(self.display_label(value))

    def get(self):
        return self.value

    def label(self):
        return self.variable.get()

    def set_by_label(self, label):
        for value in self._options:
            if self.display_label(value) == label or tr(self._options[value]) == label:
                self.set(value)
                return

    def set_by_value(self, value, default=None):
        if self._has(value):
            self.set(value)
        elif default is not None and self._has(default):
            self.set(default)

    def _has(self, value):
        return value in self._options


class ChoiceBox(ttk.Combobox):
    """Readonly combobox whose values are localized labels of data ids."""

    def __init__(self, master, choice: ChoiceVar, on_change=None, **kwargs):
        super().__init__(master, textvariable=choice.variable, state="readonly", **kwargs)
        self._choice = choice
        self._on_change = on_change
        self.bind("<<ComboboxSelected>>", self._selected)
        choice.subscribe(self)

    def _sync_values(self):
        """Mirror the ChoiceVar options into the dropdown list.

        The combobox only shows what ``values`` contains; a change that
        updates just the displayed variable leaves an empty dropdown. A
        refused option keeps its place and its motive in the label.
        """
        try:
            self.configure(values=self._choice.option_labels())
        except tk.TclError:
            pass  # widget already destroyed during a UI rebuild

    def refresh_labels(self):
        """Re-render option labels and the current selection (locale change)."""
        self._sync_values()
        if self._choice.value is not None and self._choice._has(self._choice.value):
            self._choice.set(self._choice.value)

    def _selected(self, _event=None):
        self._choice.set_by_label(self.get())
        if self._on_change:
            self._on_change()


__all__ = ["ChoiceVar", "ChoiceBox"]

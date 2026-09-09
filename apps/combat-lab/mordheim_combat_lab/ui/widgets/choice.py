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
    """Holds a data value and mirrors its localized label into ``variable``."""

    def __init__(self, value=None, master=None):
        self.value = value
        self.variable = tk.StringVar(master=master, value="")
        self._options: dict[str, str] = {}

    def set_options(self, options: dict[str | None, str]):
        """Replace the choices. ``options`` maps data value → label key."""
        self._options = dict(options)
        self.variable.set(tr(self._options.get(self.value)) if self._has(self.value) else "")

    def set(self, value):
        self.value = value
        if self._has(value):
            self.variable.set(tr(self._options[value]))

    def get(self):
        return self.value

    def label(self):
        return self.variable.get()

    def set_by_label(self, label):
        for value, key in self._options.items():
            if tr(key) == label:
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

    def refresh_labels(self):
        """Re-render option labels and the current selection (locale change)."""
        self.configure(values=tuple(tr(key) for key in self._choice._options.values()))
        if self._choice.value is not None and self._choice._has(self._choice.value):
            self._choice.set(self._choice.value)

    def _selected(self, _event=None):
        self._choice.set_by_label(self.get())
        if self._on_change:
            self._on_change()


__all__ = ["ChoiceVar", "ChoiceBox"]

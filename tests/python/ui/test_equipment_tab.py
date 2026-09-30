"""Equipment analysis page construction regressions."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from mordheim_combat_lab.ui.tabs.equipment import EquipmentAnalysisTab


def test_equipment_tab_displays_controls_and_results_table():
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk display is not available")
    root.withdraw()
    try:
        notebook = ttk.Notebook(root)
        page = ttk.Frame(notebook)
        notebook.add(page, text="Equipment")
        tab = EquipmentAnalysisTab(
            page, None, None, None, None, tk.IntVar(root, value=100),
        )
        tab.pack(fill="both", expand=True)
        notebook.select(page)
        root.update_idletasks()

        assert tab.workers.get() == -1
        assert tab.maximum_changed_slots.get() == 1
        assert tab.run_button.cget("text") == "Compare equipment"
        assert tab.tree.winfo_exists()
        assert tab.tree.heading("optimal", "text") == "Best Result"
        assert tab.winfo_manager() == "pack"
    finally:
        root.destroy()

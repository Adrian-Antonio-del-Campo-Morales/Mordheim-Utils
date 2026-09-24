"""external.test_weapons_tab: Weapons tab behaviour tests."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from mordheim_combat_lab.application.analyses import compare_builds  # noqa: F401  (import surface check)
from mordheim_combat_lab.application.catalogue import CombatCatalogue, ProfileChoice
from mordheim_combat_lab.application.settings import DuelExecutionSettings
from mordheim_combat_lab.ui.tabs.weapons import WeaponAnalysisTab
from mordheim_core.models import Characteristics, FighterBuild


@pytest.fixture(scope="module")
def root():
    try:
        instance = tk.Tk()
    except tk.TclError:  # headless environment
        pytest.skip("Tk display is not available")
    instance.withdraw()
    yield instance
    instance.destroy()


class _StubCandidateEditor:
    """Duck-typed stand-in for FighterEditor around a fixed profile."""

    def __init__(self, catalogue, choice):
        self.catalogue = catalogue
        self.choice = choice
        self.off_hand = tk.StringVar(value="")

    def build(self):
        if self.choice is None:  # free selection
            return FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1))
        return FighterBuild(
            "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
            collection=self.choice.collection,
            band_id=self.choice.band_id,
            profile_id=self.choice.profile_id,
        )

    def main_weapon_options(self):
        return self.catalogue.weapons(self.choice)


def _make_tab(root, catalogue, editor, simulations_value=2_000):
    simulations = tk.IntVar(value=simulations_value)
    settings = DuelExecutionSettings(simulations_value, 0, simulations_value, 2)
    return WeaponAnalysisTab(
        root, catalogue, editor, editor, lambda: settings, simulations,
    )


def _run_and_wait(root, tab):
    import time
    tab.run()
    deadline = time.time() + 30.0
    while tab._running and time.time() < deadline:
        root.update()
        time.sleep(0.02)
    assert not tab._running, "the analysis thread did not finish"


def test_weapons_tab_requires_a_selection(root):
    catalogue = CombatCatalogue()
    editor = _StubCandidateEditor(catalogue, None)
    editor.choice = None  # free selection
    tab = _make_tab(root, catalogue, editor)
    tab._open_weapon_popover(); tab._close_weapon_popover()
    for variable in tab._weapon_selection.values():
        variable.set(False)

    tab.run()

    assert not tab._running
    assert tab.status.get() == "Select at least one weapon to compare."


def test_weapons_tab_popover_lists_legal_weapons_and_counts(root):
    catalogue = CombatCatalogue()
    choice = ProfileChoice("mordheim", "sisters-of-sigmar", "sister-superior", "Sister Superior")
    editor = _StubCandidateEditor(catalogue, choice)
    tab = _make_tab(root, catalogue, editor)

    tab._open_weapon_popover()
    checkbuttons = [
        child for child in tab._popover.scroll_frame.winfo_children()
        if isinstance(child, ttk.Checkbutton)
    ]
    labels = {child.cget("text") for child in checkbuttons}
    expected = {name for _item_id, name in editor.main_weapon_options()}
    assert expected <= labels
    assert tab._available_count == len(expected)
    tab._close_weapon_popover()
    assert f"({len(expected)} / {len(expected)})" in tab.weapons_button.cget("text")


def test_weapons_tab_runs_selected_weapons(root):
    catalogue = CombatCatalogue()
    choice = ProfileChoice("mordheim", "sisters-of-sigmar", "sister-superior", "Sister Superior")
    editor = _StubCandidateEditor(catalogue, choice)
    tab = _make_tab(root, catalogue, editor)
    tab._open_weapon_popover(); tab._close_weapon_popover()
    # Keep only two weapons selected.
    keep = {"weapon.mace", "weapon.sigmarite-hammer"}
    for item_id, variable in tab._weapon_selection.items():
        variable.set(item_id in keep)
    tab._selection_changed()

    _run_and_wait(root, tab)

    rows = tab.tree.get_children()
    assert 0 < len(rows) <= 2
    for row in rows:
        assert tab.tree.set(row, "main") in {"Mace", "Sigmarite Hammer"}
        assert tab.tree.set(row, "optimal"), "missing win-rate cell"


def test_weapons_tab_passes_workers_to_the_battery_service(root):
    catalogue = CombatCatalogue()
    choice = ProfileChoice("mordheim", "sisters-of-sigmar", "sister-superior", "Sister Superior")
    editor = _StubCandidateEditor(catalogue, choice)
    tab = _make_tab(root, catalogue, editor)
    tab._open_weapon_popover(); tab._close_weapon_popover()
    for item_id, variable in tab._weapon_selection.items():
        variable.set(item_id == "weapon.mace")
    tab._selection_changed()
    assert tab.workers.get() == -1  # default: automatic battery policy
    tab.workers.set(2)

    _run_and_wait(root, tab)

    rows = tab.tree.get_children()
    assert len(rows) == 1
    assert tab.tree.set(rows[0], "main") == "Mace"


def test_weapons_tab_never_fails_with_an_empty_error(root):
    catalogue = CombatCatalogue()
    editor = _StubCandidateEditor(catalogue, None)
    editor.choice = None
    tab = _make_tab(root, catalogue, editor)
    tab._open_weapon_popover(); tab._close_weapon_popover()
    # A fist-only candidate triggers the historical empty-key crash path.
    tab._weapon_selection.clear()
    tab._weapon_selection["weapon.fist"] = tk.BooleanVar(value=True)
    tab._selection_changed()

    _run_and_wait(root, tab)

    status = tab.status.get()
    assert not status.endswith("None"), status

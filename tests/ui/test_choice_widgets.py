"""external.test_choice_widgets: Choice widget dropdown-sync tests."""
from __future__ import annotations

import tkinter as tk

import pytest

from mordheim_combat_lab.ui.widgets.choice import ChoiceBox
from mordheim_combat_lab.ui.widgets.choice import ChoiceVar


@pytest.fixture(scope="module")
def root():
    try:
        instance = tk.Tk()
    except tk.TclError:  # headless environment
        pytest.skip("Tk display is not available")
    instance.withdraw()
    yield instance
    instance.destroy()


def test_choicebox_dropdown_stays_in_sync_with_set_options(root):
    var = ChoiceVar("weapon.mace")
    box = ChoiceBox(root, var)

    var.set_options({"weapon.mace": "Mace", "weapon.flail": "Flail"})

    assert box.cget("values") == ("Mace", "Flail")
    assert var.variable.get() == "Mace"
    assert box.get() == "Mace"


def test_choicebox_dropdown_clears_the_label_when_the_value_is_not_an_option(root):
    var = ChoiceVar("weapon.fist")
    box = ChoiceBox(root, var)

    var.set_options({"weapon.mace": "Mace"})

    assert box.cget("values") == ("Mace",)
    assert var.variable.get() == ""

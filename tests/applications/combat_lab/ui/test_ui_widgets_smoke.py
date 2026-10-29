"""Small UI and application smoke tests consolidated by surface."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_combat_lab.application.motta import motta_score
from mordheim_combat_lab.application.settings import DuelExecutionSettings
from mordheim_combat_lab.persistence.workbooks import CombatLabWorkbookError
from mordheim_combat_lab.persistence.workbooks import load_ui_workbook
from mordheim_combat_lab.persistence.workbooks import save_workbook
from mordheim_combat_lab.ui.app import _preference_int
from mordheim_combat_lab.ui.tabs.equipment import EquipmentAnalysisTab
from mordheim_combat_lab.ui.widgets.choice import ChoiceBox
from mordheim_combat_lab.ui.widgets.choice import ChoiceVar
from mordheim_construction.compiler import compile_fighter
from mordheim_core.models import Characteristics
from mordheim_core.models import DuelResult
from mordheim_core.models import FighterBuild


# Reading a stored preference falls back when the value is absent or out of range.
# The visible value is what this helper feeds; no storage write is exercised.
def test_preference_int_uses_default_for_invalid_or_out_of_range_values():
    assert _preference_int({"count": "20"}, "count", 10, 1) == 20
    assert _preference_int({"count": "bad"}, "count", 10, 1) == 10
    assert _preference_int({"count": 0}, "count", 10, 1) == 10


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


def test_free_selection_build_compiles_with_runtime_equipment():
    catalogue = CombatCatalogue()
    sword = next(item_id for item_id, name in catalogue.weapons(None) if name == "Sword")
    shield = next(item_id for item_id, name in catalogue.off_hand_options(None) if name == "Shield")

    fighter = compile_fighter(
        FighterBuild(
            "mordheim",
            Characteristics(4, 3, 3, 1, 4, 1),
            main_weapon_id=sword,
            off_hand_id=shield,
        )
    )

    assert fighter.fighter_id == "custom:custom"


def test_free_selection_build_compiles_with_an_implemented_warband_skill():
    fighter = compile_fighter(FighterBuild(
        "mordheim",
        Characteristics(4, 3, 3, 1, 4, 1),
        special_rule_ids=("band--pit-fighter-skill-arms-master",),
    ))

    assert fighter.fighter_id == "custom:custom"


def test_workbook_round_trip_preserves_stable_build_ids_and_result(tmp_path):
    candidate = FighterBuild(
        "mordheim", collection="mordheim", band_id="mercenaries", profile_id="mercenary-captain",
        main_weapon_id="weapon.sword", off_hand_id="defence.shield", defence_ids=("defence.helmet",),
        skill_ids=("skill.mighty-blow",),
        trait_overrides={"causes_fear": True},
    )
    enemy = FighterBuild("mordheim", Characteristics(3, 3, 3, 1, 3, 1, leadership=7), main_weapon_id="weapon.mace")
    settings = DuelExecutionSettings(5_000, 123, 500, 30)
    result = DuelResult(2_500, 2_400, 100, 5_000)
    path = tmp_path / "duel.xlsx"

    save_workbook(path, candidate, enemy, settings, result)
    restored_candidate, restored_enemy, restored_settings, restored_result = load_ui_workbook(path)

    assert restored_candidate == candidate
    assert restored_enemy == enemy
    assert restored_settings == settings
    assert restored_result == result


def test_workbook_rejects_unknown_or_corrupt_files(tmp_path):
    path = tmp_path / "not-a-workbook.xlsx"
    path.write_text("not an Excel file", encoding="utf-8")

    with pytest.raises(CombatLabWorkbookError):
        load_ui_workbook(path)


def test_motta_uses_the_legacy_cost_regularisation():
    assert motta_score(1.0, 10.0) == 50.73997463001903


def test_motta_requires_a_known_cost():
    assert motta_score(2.0, None) is None

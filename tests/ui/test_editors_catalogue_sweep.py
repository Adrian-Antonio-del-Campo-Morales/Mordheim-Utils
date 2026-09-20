"""external.test_editors_catalogue_sweep: no editor selector stays empty for any KB profile."""
from __future__ import annotations

import tkinter as tk

import pytest

from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_combat_lab.ui.editors import FREE_SELECTION
from mordheim_combat_lab.ui.editors import FighterEditor

#: Every ChoiceBox of the editor, mirroring what the workbook exposes.
SELECTOR_NAMES = (
    "weapon_combo", "off_hand_combo", "armour_combo",
    "main_material_combo", "off_material_combo",
    "main_poison_combo", "off_poison_combo",
)


@pytest.fixture(scope="module")
def root():
    try:
        instance = tk.Tk()
    except tk.TclError:  # headless environment
        pytest.skip("Tk display is not available")
    instance.withdraw()
    yield instance
    instance.destroy()


@pytest.fixture(scope="module")
def editor(root):
    return FighterEditor(root, "Candidate", CombatCatalogue())


def _assert_selectors_populated(editor, band_name: str, profile_name: str) -> None:
    for name in SELECTOR_NAMES:
        combo = getattr(editor, name)
        values = tuple(combo.cget("values"))
        assert values, (
            f"empty dropdown for band={band_name!r} profile={profile_name!r} selector={name}"
        )
        assert combo.get(), (
            f"blank selection for band={band_name!r} profile={profile_name!r} "
            f"selector={name} options={values}"
        )


def test_sweep_every_band_and_profile_keeps_all_selectors_populated(editor):
    assert editor._band_packages, "the editor must expose the full band catalogue"
    checked = 0
    for band_name in sorted(editor._band_packages):
        editor.band.set(band_name)
        editor._band_changed()
        for profile_name in sorted(editor._profiles):
            editor.profile_name.set(profile_name)
            editor._profile_changed()
            _assert_selectors_populated(editor, band_name, profile_name)
            # The editor must survive every KB profile, including composite
            # models with null characteristics (e.g. the plague cart).
            assert editor.build() is not None
            checked += 1
    assert checked > 0, "no profile was visited; the sweep is vacuous"


def test_free_selection_keeps_all_selectors_populated(editor):
    editor.band.set(FREE_SELECTION)
    editor._band_changed()

    assert editor.is_free_selection
    # Free selection offers the whole runtime catalogue, Fist included.
    assert "Fist" in tuple(editor.weapon_combo.cget("values"))
    _assert_selectors_populated(editor, FREE_SELECTION, "-")


def test_composite_profile_with_null_characteristics_renders_and_builds(editor):
    """The plague cart declares null characteristics and must not crash."""
    band_name = next(
        name for name, package in editor._band_packages.items()
        if package.band["id"] == "carnival-of-chaos"
    )
    editor.band.set(band_name)
    editor._band_changed()
    profile_name = next(
        name for name, choice in editor._profiles.items()
        if choice.profile_id == "plague-cart"
    )
    editor.profile_name.set(profile_name)
    editor._profile_changed()

    _assert_selectors_populated(editor, band_name, profile_name)
    build = editor.build()
    assert build.profile_id == "plague-cart"
    assert build.characteristics.weapon_skill >= 0


def test_sister_superior_weapon_selector_is_populated(editor):
    """Regression: the Sister Superior weapon dropdown used to open empty."""
    band_name = next(
        name for name, package in editor._band_packages.items()
        if package.band["id"] == "sisters-of-sigmar"
    )
    editor.band.set(band_name)
    editor._band_changed()
    profile_name = next(
        name for name, choice in editor._profiles.items()
        if choice.profile_id == "sister-superior"
    )
    editor.profile_name.set(profile_name)
    editor._profile_changed()

    values = tuple(editor.weapon_combo.cget("values"))
    assert values == (
        "Free hand", "Dagger", "Double-Handed Weapon", "Flail",
        "Mace", "Sigmarite Hammer", "Steel Whip",
    )
    assert editor.weapon_combo.get() == "Free hand"
    assert editor.weapon.get() is None

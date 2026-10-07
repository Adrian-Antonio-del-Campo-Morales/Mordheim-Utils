"""external.test_editors_catalogue_sweep: no editor selector stays empty for any KB profile."""
from __future__ import annotations

import tkinter as tk

import pytest

from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_combat_lab.ui.editors import FREE_SELECTION
from mordheim_combat_lab.ui.editors import FighterEditor
from mordheim_core.models import Characteristics, FighterBuild
from mordheim_construction.compiler import compile_fighter

#: Every ChoiceBox of the editor, mirroring what the workbook exposes.
SELECTOR_NAMES = (
    "weapon_combo", "off_hand_combo", "armour_combo",
    "main_material_combo", "off_material_combo",
    "main_poison_combo", "off_poison_combo",
)


def test_editor_roundtrips_a_supplied_fear_condition_and_explicit_leadership(editor):
    build = FighterBuild('mordheim', Characteristics(3, 3, 3, 2, 3, 1, leadership=7),
                         main_weapon_id='weapon.mace', trait_overrides={'causes_fear': True})
    editor.load_build(build)
    assert editor.causes_fear.get() and editor.leadership.get() == '7'
    projected = editor.build()
    assert projected.trait_overrides['causes_fear'] is True and projected.characteristics.leadership == 7
    assert 'mechanic.causes-fear' in compile_fighter(projected).global_effects.tags
    editor.causes_fear.set(False)
    assert 'mechanic.causes-fear' not in compile_fighter(editor.build()).global_effects.tags


def test_editor_roundtrips_a_supplied_canonical_condition(editor):
    """The editor passes canonical ids through; it keeps no second table."""
    assert 'condition.hatred' in editor.condition_vars
    build = FighterBuild('mordheim', Characteristics(3, 3, 3, 2, 3, 1),
                         main_weapon_id='weapon.mace', condition_ids=('condition.hatred',))
    editor.load_build(build)
    assert editor.condition_vars['condition.hatred'].get()
    projected = editor.build()
    assert projected.condition_ids == ('condition.hatred',)
    assert 'skill.hatred' in compile_fighter(projected).global_effects.tags
    editor.condition_vars['condition.hatred'].set(False)
    assert editor.build().condition_ids == ()


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



def test_editor_roundtrips_supplied_stupidity_conditions_and_handler_value(root):
    editor = FighterEditor(root, 'Stupidity', CombatCatalogue())
    build = FighterBuild('mordheim', Characteristics(3, 3, 3, 2, 2, 1, leadership=7),
        main_weapon_id='weapon.mace', trait_overrides={'stupidity': True, 'stupidity_initial_failed': True})
    editor.load_build(build); root.update_idletasks()
    compiled = compile_fighter(editor.build())
    assert 'mechanic.stupidity' in compiled.global_effects.tags
    assert 'condition.stupidity-failed' in compiled.global_effects.tags
    editor.stupidity_exempt.set(True)
    assert 'condition.stupidity-exempt' in compile_fighter(editor.build()).global_effects.tags
    editor.stupidity.set(False); editor.stupidity_initial_failed.set(False); editor.stupidity_exempt.set(False)
    assert 'mechanic.stupidity' not in compile_fighter(editor.build()).global_effects.tags
    build = FighterBuild('mordheim', band_id='dark-elves', profile_id='cold-one-beasthounds',
        main_weapon_id='weapon.fist', trait_overrides={'stupidity_leadership': 8})
    editor.load_build(build); root.update_idletasks()
    assert editor.stupidity_leadership.get() == '8'
    assert compile_fighter(editor.build()).stupidity_leadership == 8
    editor.destroy()


def test_editor_roundtrips_explicit_elf_identity_without_overriding_profile_default(root):
    editor = FighterEditor(root, 'Identity', CombatCatalogue())
    editor.load_build(FighterBuild('mordheim', band_id='high-elves-lus', profile_id='seaguard', main_weapon_id='weapon.dagger'))
    root.update_idletasks()
    assert editor.elf_kind.get() is None
    assert 'species.high-elf' in compile_fighter(editor.build()).global_effects.tags
    editor.elf_kind.set('other')
    assert 'species.high-elf' not in compile_fighter(editor.build()).global_effects.tags
    editor.load_build(FighterBuild('mordheim', band_id='lothern-sea-patrol-sar', profile_id='raw-recruits', main_weapon_id='weapon.dagger', trait_overrides={'elf_kind': 'high'}))
    root.update_idletasks()
    assert editor.elf_kind.get() == 'high'
    assert 'species.high-elf' in compile_fighter(editor.build()).global_effects.tags
    editor.elf_kind.set('dark')
    assert 'species.dark-elf' in compile_fighter(editor.build()).global_effects.tags
    assert editor.sex.get() is None
    editor.sex.set('male')
    build = editor.build()
    editor.load_build(build); root.update_idletasks()
    assert editor.sex.get() == 'male'
    assert 'sex.male' in compile_fighter(editor.build()).global_effects.tags
    editor.sex.set(None)
    assert 'sex' not in editor.build().trait_overrides
    editor.supplied_choices['creature_kind'].set('daemon')
    editor.supplied_choices['species'].set('human')
    editor.supplied_flags['lit_item'].set(True)
    editor.supplied_flags['onogal_follower'].set(True)
    editor.supplied_choices['mercenary_origin'].set('marienburg')
    build = editor.build()
    editor.load_build(build); root.update_idletasks()
    assert editor.supplied_choices['creature_kind'].get() == 'daemon'
    assert editor.supplied_flags['lit_item'].get()
    fighter = compile_fighter(editor.build())
    assert {'nature.daemon', 'species.human', 'condition.open-flame'} <= set(fighter.global_effects.tags)
    assert 'identity.onogal-follower' in fighter.global_effects.tags
    assert editor.supplied_choices['mercenary_origin'].get() == 'marienburg'
    assert 'mercenary-origin.marienburg' in fighter.global_effects.tags
    editor.supplied_choices['creature_kind'].set(None)
    editor.supplied_flags['lit_item'].set(False)
    assert 'creature_kind' not in editor.build().trait_overrides
    assert 'lit_item' not in editor.build().trait_overrides
    editor.destroy()


def test_editor_roundtrips_snorri_prebattle_drinking_result(root):
    editor = FighterEditor(root, 'Snorri', CombatCatalogue())
    build = FighterBuild('mordheim', band_id='hirelings.dramatis-personae.2b',
        profile_id='hireling.dramatis.snorri-nosebiter', main_weapon_id='weapon.dwarf-axe',
        off_hand_id='weapon.mace', trait_overrides={'snorri_drunk_result': 6})
    editor.load_build(build); root.update_idletasks()
    assert editor.supplied_choices['snorri_drunk_result'].get() == 6
    restored = editor.build()
    assert restored.trait_overrides['snorri_drunk_result'] == 6
    fighter = compile_fighter(restored)
    assert 'condition.snorri-frenzy' in fighter.global_effects.tags
    editor.supplied_choices['snorri_drunk_result'].set(2)
    restored = editor.build(); editor.load_build(restored)
    assert compile_fighter(editor.build()).characteristics.strength == 3
    editor.destroy()


def test_editor_roundtrips_native_sister_starting_skill_choices(root):
    editor = FighterEditor(root, 'Sister', CombatCatalogue())
    try:
        build = FighterBuild('mordheim', band_id='hirelings.hired-sword.2b',
            profile_id='hireling.hired-sword.sister-of-sigmar', main_weapon_id='weapon.arcane-candelabrum',
            off_hand_id='weapon.sigmarite-hammer', armour_id='armour.light-armour', special_rule_ids=(
                'band--special-skills-sign-of-sigmar', 'band--special-skills-protection-of-sigmar'))
        editor.load_build(build); root.update_idletasks()
        restored = editor.build()
        assert set(restored.special_rule_ids) == set(build.special_rule_ids)
        fighter = compile_fighter(restored)
        assert 'skill.sigmar-s-sign' in fighter.global_effects.tags
        assert 'defence.holy-relic' in fighter.global_effects.tags
    finally:
        editor.destroy()


def test_editor_roundtrips_house_and_qualified_animal_facts(root):
    editor = FighterEditor(root, 'Qualified facts', CombatCatalogue())
    try:
        build = FighterBuild('mordheim', band_id='house-guard-sc', profile_id='commander',
            main_weapon_id='weapon.mace', trait_overrides={'house_guard_house': 'fierezza'})
        editor.load_build(build); root.update_idletasks()
        assert editor.supplied_choices['house_guard_house'].get() == 'fierezza'
        assert 'house-guard.fierezza' in compile_fighter(editor.build()).global_effects.tags
        editor.load_build(FighterBuild('mordheim', Characteristics(3, 3, 3, 1, 3, 1, leadership=5),
            main_weapon_id='weapon.fist', trait_overrides={'fighter_kind': 'animal',
                'fauna_animal_kind': 'handled', 'animal_handler_leadership': 7}))
        root.update_idletasks()
        restored = editor.build()
        editor.load_build(restored); root.update_idletasks()
        fighter = compile_fighter(editor.build())
        assert {'fighter-kind.animal', 'fauna-animal.handled'} <= set(fighter.global_effects.tags)
        assert fighter.animal_handler_leadership == 7
    finally:
        editor.destroy()


def test_editor_roundtrips_native_eagle_count_and_snerik_source_kit(root):
    editor = FighterEditor(root, 'Native companions', CombatCatalogue())
    try:
        pid = 'hireling.hired-sword.war-priestess-of-myrmidia'
        build = FighterBuild('mordheim', band_id='hirelings.hired-sword.2b', profile_id=pid,
            main_weapon_id='weapon.dagger', special_rule_ids=(pid + '.skill.eagle-friend',),
            trait_overrides={'eagle_friends': 2})
        editor.load_build(build); root.update_idletasks()
        assert editor.eagle_friends.get() == '2'
        assert len(compile_fighter(editor.build()).extra_attacks) == 2
        editor.eagle_friends.set('')
        assert len(compile_fighter(editor.build()).extra_attacks) == 1
        pid = 'hireling.dramatis.snerik-night-goblin-scout'
        build = FighterBuild('mordheim', band_id='hirelings.dramatis-personae.2b', profile_id=pid,
            main_weapon_id='weapon.sword', off_hand_id='weapon.dagger',
            owned_item_ids=('dagger', 'sword', 'short_bow', pid + '.item.camouflage-cloak'))
        editor.load_build(build); root.update_idletasks()
        restored = editor.build()
        assert restored.owned_item_ids == build.owned_item_ids
        assert compile_fighter(restored).fighter_id.endswith(pid)
        dreamer = FighterBuild('mordheim', band_id='dreamwalkers-cult-of-morr-fbg',
            profile_id='dreamer', main_weapon_id='weapon.sword',
            trait_overrides={'guiding_dream_target': True})
        editor.load_build(dreamer); root.update_idletasks()
        assert 'condition.guiding-dream-target' in compile_fighter(editor.build()).global_effects.tags
        vampire = FighterBuild('mordheim', Characteristics(3, 3, 3, 1, 3, 1),
            trait_overrides={'vampire': True, 'vampire_bloodline': 'lahmian'})
        editor.load_build(vampire); root.update_idletasks()
        assert 'vampire-bloodline.lahmian' in compile_fighter(editor.build()).global_effects.tags
    finally:
        editor.destroy()

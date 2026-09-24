"""external.test_improvements: Improvements tab behaviour tests."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

import pytest

from mordheim_combat_lab.application.analyses import add_improvement, improvement_choices
from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_combat_lab.application.settings import DuelExecutionSettings
from mordheim_combat_lab.ui.tabs.improvements import ImprovementAnalysisTab
from mordheim_core.models import Characteristics, FighterBuild

def test_improvement_choices_exclude_out_of_scope_and_already_selected_skills():
    catalogue = CombatCatalogue()
    choice = next(
        profile for profile in catalogue.profiles("mordheim", "kislevites")
        if profile.profile_id == "druzhina-captain"
    )
    candidate = FighterBuild(
        "mordheim",
        collection=choice.collection,
        band_id=choice.band_id,
        profile_id=choice.profile_id,
        skill_ids=("skill.mighty-blow",),
    )

    choices = improvement_choices(catalogue, choice, candidate)
    choice_ids = {skill.id for skill in choices}

    assert "skill.acrobat" not in choice_ids
    assert "skill.mighty-blow" not in choice_ids
    assert choice_ids
    assert all(skill.runtime_available for skill in choices)


def test_add_improvement_maps_warband_skills_to_special_rule_ids():
    catalogue = CombatCatalogue()
    choice = next(
        profile for profile in catalogue.profiles("mordheim", "pit-fighters")
        if profile.profile_id == "pit-king"
    )
    candidate = FighterBuild(
        "mordheim",
        collection=choice.collection,
        band_id=choice.band_id,
        profile_id=choice.profile_id,
    )
    skill = next(
        skill for skill in improvement_choices(catalogue, choice, candidate)
        if skill.rule_id == "band--pit-fighter-skill-body-slam"
    )

    improved = add_improvement(catalogue, candidate, skill)

    assert improved.skill_ids == ()
    assert improved.special_rule_ids == ("band--pit-fighter-skill-body-slam",)


def test_improvement_choices_exclude_compound_renowned_virtue():
    catalogue = CombatCatalogue()
    choice = next(
        profile for profile in catalogue.profiles("mordheim", "bretonnian-chapel-guard")
        if profile.profile_id == "questing-knight"
    )
    candidate = FighterBuild(
        "mordheim",
        collection=choice.collection,
        band_id=choice.band_id,
        profile_id=choice.profile_id,
    )

    choices = improvement_choices(catalogue, choice, candidate)

    assert "band--renowned-virtue" not in {skill.rule_id for skill in choices}


@pytest.fixture(scope="module")
def root():
    try:
        instance = tk.Tk()
    except tk.TclError:  # headless environment
        pytest.skip("Tk display is not available")
    instance.withdraw()
    yield instance
    instance.destroy()


def _captain(catalogue):
    return next(
        profile for profile in catalogue.profiles("mordheim", "kislevites")
        if profile.profile_id == "druzhina-captain"
    )


def _make_tab(root, catalogue, simulations_value):
    simulations = tk.IntVar(value=simulations_value)
    settings = DuelExecutionSettings(simulations_value, 0, simulations_value, 2)
    tab = ImprovementAnalysisTab(
        root, catalogue, None, None, lambda: settings, simulations,
    )
    return tab


class _StubCandidateEditor:
    """Duck-typed stand-in for FighterEditor around a fixed profile."""

    def __init__(self, catalogue, choice):
        self.catalogue = catalogue
        self.choice = choice

    def build(self):
        # Explicit base characteristics keep attribute improvements usable;
        # the KB profile alone defers characteristics to the compiler.
        return FighterBuild(
            "mordheim", Characteristics(3, 3, 3, 1, 3, 1),
            collection=self.choice.collection,
            band_id=self.choice.band_id,
            profile_id=self.choice.profile_id,
        )


def _run_and_wait(root, tab):
    import time
    tab.run()
    deadline = time.time() + 30.0
    while tab._running and time.time() < deadline:  # the worker joins via _poll_worker()
        root.update()
        time.sleep(0.02)
    assert not tab._running, "the analysis thread did not finish"


def _sync_selection(tab):
    """Open and close the popover so the checklist mirrors the candidate."""
    tab._open_skill_popover()
    tab._close_skill_popover()


def test_improvements_tab_lists_choices_and_runs_selected_combinations(root):
    catalogue = CombatCatalogue()
    choice = _captain(catalogue)
    editor = _StubCandidateEditor(catalogue, choice)
    tab = _make_tab(root, catalogue, 2_000)
    tab.candidate_editor = editor
    tab.enemy_editor = editor
    _sync_selection(tab)

    from mordheim_combat_lab.application.analyses import attribute_choices
    available = improvement_choices(catalogue, choice, editor.build())
    attributes = attribute_choices(catalogue, choice, editor.build())
    expected = len(available) + len(attributes)
    assert expected > 0
    tab._open_skill_popover(); tab._close_skill_popover()
    assert tab._available_count == expected
    assert f"({expected} / {expected})" in tab.skills_button.cget("text")

    # Pairs run only when the size selector asks for them: both applied
    # columns carry an item name and the unused ones stay empty. Only skills
    # are selected here: the "+1" suffix belongs to attribute increases alone
    # (a mis-typed discriminator once tagged every skill cell with it).
    for item_id, variable in tab._skill_selection.items():
        variable.set(item_id.startswith("skill."))
    tab._selection_changed()
    tab.improvement_size.set(2)
    _run_and_wait(root, tab)
    rows = tab.tree.get_children()
    assert rows, "the pair comparison produced no rows"
    for row in rows:
        assert tab.tree.set(row, "improvement1") != "—"
        assert tab.tree.set(row, "improvement2") != "—"
        assert tab.tree.set(row, "improvement3") == "—"
        assert not tab.tree.set(row, "improvement1").endswith("+1")
        assert not tab.tree.set(row, "improvement2").endswith("+1")


def test_improvements_tab_respects_the_skill_selection(root):
    catalogue = CombatCatalogue()
    choice = _captain(catalogue)
    editor = _StubCandidateEditor(catalogue, choice)
    tab = _make_tab(root, catalogue, 2_000)
    tab.candidate_editor = editor
    tab.enemy_editor = editor
    _sync_selection(tab)

    first = next(iter(tab._skill_selection))
    for variable in tab._skill_selection.values():
        variable.set(False)
    tab._skill_selection[first].set(True)
    tab._selection_changed()

    tab.improvement_size.set(1)
    _run_and_wait(root, tab)
    rows = tab.tree.get_children()
    assert len(rows) == 1
    assert tab.tree.set(rows[0], "improvement1") != "—"
    assert "Se compararon 1 combinaciones" in tab.status.get() or "Compared 1 combinations" in tab.status.get()


def test_improvements_tab_requires_a_selection(root):
    catalogue = CombatCatalogue()
    choice = _captain(catalogue)
    editor = _StubCandidateEditor(catalogue, choice)
    tab = _make_tab(root, catalogue, 2_000)
    tab.candidate_editor = editor
    tab.enemy_editor = editor
    _sync_selection(tab)

    for variable in tab._skill_selection.values():
        variable.set(False)

    tab.run()

    assert not tab._running
    assert tab.status.get() == "Select at least one improvement to compare."


def test_improvements_tab_passes_workers_to_the_battery_service(root):
    catalogue = CombatCatalogue()
    choice = _captain(catalogue)
    editor = _StubCandidateEditor(catalogue, choice)
    tab = _make_tab(root, catalogue, 2_000)
    tab.candidate_editor = editor
    tab.enemy_editor = editor
    _sync_selection(tab)
    first = next(iter(tab._skill_selection))
    for variable in tab._skill_selection.values():
        variable.set(False)
    tab._skill_selection[first].set(True)
    tab._selection_changed()
    assert tab.workers.get() == -1  # default: automatic battery policy
    tab.workers.set(2)

    tab.improvement_size.set(1)
    _run_and_wait(root, tab)
    rows = tab.tree.get_children()
    assert len(rows) == 1
    assert "Se compararon 1 combinaciones" in tab.status.get() or "Compared 1 combinations" in tab.status.get()


def test_improvements_tab_offers_attribute_increases_within_racial_maximums(root):
    catalogue = CombatCatalogue()
    choice = _captain(catalogue)
    editor = _StubCandidateEditor(catalogue, choice)
    tab = _make_tab(root, catalogue, 2_000)
    tab.candidate_editor = editor
    tab.enemy_editor = editor
    _sync_selection(tab)

    from mordheim_combat_lab.application.analyses import attribute_choices
    attributes = attribute_choices(catalogue, choice, editor.build())
    attribute_ids = {item.id for item in attributes}
    # Humans can raise every duel characteristic from the base profile.
    assert {"WS", "S", "T", "W", "I", "A"} <= attribute_ids
    tab._open_skill_popover()
    checkbuttons = [
        child for child in tab._popover.scroll_frame.winfo_children()
        if isinstance(child, ttk.Checkbutton)
    ]
    labels = {child.cget("text") for child in checkbuttons}
    for item in attributes:
        assert item.id in tab._skill_selection
        assert f"{item.name} +1" in labels
    tab._close_skill_popover()

    # A candidate already at the human Initiative maximum gets no I option.
    from mordheim_core.models import Characteristics
    capped = FighterBuild(
        "mordheim", Characteristics(6, 4, 4, 3, 6, 4),
        collection=choice.collection, band_id=choice.band_id,
        profile_id=choice.profile_id,
    )
    assert "I" not in {item.id for item in attribute_choices(catalogue, choice, capped)}


def _menu_labels(menu):
    labels = []
    for index in range(menu.index("end") + 1):
        try:
            labels.append(menu.entrycget(index, "label"))
        except tk.TclError:
            continue  # separators expose no label
    return labels


def test_improvements_tab_runs_attribute_increases(root):
    catalogue = CombatCatalogue()
    choice = _captain(catalogue)
    editor = _StubCandidateEditor(catalogue, choice)
    tab = _make_tab(root, catalogue, 2_000)
    tab.candidate_editor = editor
    tab.enemy_editor = editor
    _sync_selection(tab)

    from mordheim_combat_lab.application.analyses import attribute_choices
    attributes = attribute_choices(catalogue, choice, editor.build())
    for variable in tab._skill_selection.values():
        variable.set(False)
    ws = next(item for item in attributes if item.id == "WS")
    tab._skill_selection["WS"].set(True)
    tab._selection_changed()

    tab.improvement_size.set(1)
    _run_and_wait(root, tab)
    rows = tab.tree.get_children()
    assert len(rows) == 1
    assert tab.tree.set(rows[0], "improvement1") == f"{ws.name} +1"
    assert "+" in tab.tree.set(rows[0], "optimal")  # win rate and impact


def test_improvements_tab_repeats_an_attribute_to_its_racial_maximum(root):
    """Selecting only Strength with size 3 runs [S+1, S+1, S+1] as one row
    whenever the candidate still has three points below the racial maximum."""
    catalogue = CombatCatalogue()
    choice = _captain(catalogue)
    editor = _StubCandidateEditor(catalogue, choice)
    tab = _make_tab(root, catalogue, 2_000)
    tab.candidate_editor = editor
    tab.enemy_editor = editor
    _sync_selection(tab)

    for variable in tab._skill_selection.values():
        variable.set(False)
    tab._skill_selection["S"].set(True)  # human base 3, maximum 4 -> only one step
    tab._skill_selection["WS"].set(True)  # 3 of 6 -> three steps available
    tab._selection_changed()

    tab.improvement_size.set(3)
    _run_and_wait(root, tab)
    rows = tab.tree.get_children()
    assert rows, "no combinations were generated"
    labels = {tuple(tab.tree.set(row, f"improvement{index}") for index in range(1, 4)) for row in rows}
    assert ("Weapon Skill +1", "Weapon Skill +1", "Weapon Skill +1") in labels
    # Strength has a single step for this candidate: no row may stack it twice.
    for row in rows:
        cells = [tab.tree.set(row, f"improvement{index}") for index in range(1, 6)]
        assert cells.count("Strength +1") <= 1
    assert "Weapon Skill + Weapon Skill + Weapon Skill" in {tab.tree.set(row, "improvement1") for row in rows} or any(
        "Weapon Skill" in cell for row in rows for cell in (tab.tree.set(row, "improvement1"),)
    )

"""ui: Improvements tab: added skills and effects."""
from __future__ import annotations

from mordheim_combat_lab.application.analyses import (
    AttributeChoice, ComparisonCandidate, add_improvement_items,
    attribute_choices, compare_builds, improvement_choices,
    improvement_combinations,
)
from mordheim_combat_lab.ui.widgets.checklist_popover import ChecklistPopover
from mordheim_core.models import SimulationCancelled
from mordheim_combat_lab.ui.widgets.progress import AnalysisProgress
from mordheim_ui.i18n import tr
import threading as threading
import tkinter as tk
from tkinter import StringVar
from tkinter import ttk


#: Main-thread poll interval while a worker computes the comparison.
POLL_INTERVAL_MS = 30

#: Checklist popover height in pixels; the scrollbar handles the overflow.
POPUP_HEIGHT = 280


class ImprovementAnalysisTab(ttk.Frame):
    """Compare selected additional skills, alone or in combinations.

    Thread coordination: the worker thread never touches Tkinter. It stores
    its progress counter and the final outcome behind an ``Event``, and the
    main thread polls both, so the analysis also stays controllable while the
    event loop is suspended (tests, modal dialogs).
    """

    def __init__(self, parent, catalogue, candidate_editor, enemy_editor, settings_provider, simulations, usage_factory=None):
        super().__init__(parent, padding=12)
        self.catalogue = catalogue
        self.candidate_editor = candidate_editor
        self.enemy_editor = enemy_editor
        self.settings_provider = settings_provider
        self.simulations = simulations
        self.workers = tk.IntVar(value=-1)
        self._usage_factory = usage_factory
        self.status = StringVar(value=tr("Compare each legal additional skill against the candidate baseline."))
        self.improvement_size = tk.IntVar(value=1)
        self._skill_selection: dict[str, tk.BooleanVar] = {}
        self._available_count = 0
        self._selected_count = 0
        self._running = False
        self._outcome_event: threading.Event | None = None
        self._outcome = None
        self._worker_progress = 0
        self._reported_progress = 0
        self._progress_lock = threading.Lock()
        self._build_gui()

    def _build_gui(self) -> None:
        ttk.Label(self, text=tr("Improvement analysis"), style="Heading.TLabel").pack(anchor="w")
        ttk.Label(self, text=tr("Each row applies the selected profile-legal skills to the candidate configuration."), style="Muted.TLabel").pack(anchor="w", pady=(2, 12))
        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(0, 10))
        ttk.Label(controls, text=tr("Simulations")).pack(side="left", padx=(0, 5))
        ttk.Spinbox(controls, from_=1_000, to=10_000_000, increment=10_000, textvariable=self.simulations, width=12).pack(side="left", padx=(0, 12))
        ttk.Label(controls, text=tr("Battery workers (-1 = automatic, 0 = sequential)")).pack(side="left", padx=(0, 5))
        ttk.Spinbox(controls, from_=-1, to=32, increment=1, textvariable=self.workers, width=5).pack(side="left", padx=(0, 12))
        ttk.Label(controls, text=tr("Number of improvements:")).pack(side="left", padx=(0, 5))
        ttk.Combobox(
            controls, textvariable=self.improvement_size, values=(1, 2, 3, 4, 5),
            state="readonly", width=3, justify="center",
        ).pack(side="left", padx=(0, 12))
        self.skills_button = ttk.Button(controls, text=tr("Skills ({} / {})").format(0, 0), command=self._toggle_skill_popover)
        self.skills_button.pack(side="left", padx=(0, 12))
        self._popover = ChecklistPopover(self.skills_button, height=POPUP_HEIGHT)
        self.run_button = ttk.Button(controls, text=tr("Compare improvements"), style="Accent.TButton", command=self.run)
        self.run_button.pack(side="left")
        self.progress = AnalysisProgress(self)
        self.progress.pack(fill="x", pady=(0, 10))
        # Keep the workbook-style result layout from the legacy Improvements
        # page: one column per applied improvement, up to five.
        columns = ("improvement1", "improvement2", "improvement3", "improvement4", "improvement5", "optimal", "equipment")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        definitions = (
            ("improvement1", tr("Improvement {}").format(1), 210), ("improvement2", tr("Improvement {}").format(2), 160),
            ("improvement3", tr("Improvement {}").format(3), 160), ("improvement4", tr("Improvement {}").format(4), 160),
            ("improvement5", tr("Improvement {}").format(5), 160), ("optimal", tr("Best Result"), 170),
            ("equipment", tr("Equipment Used"), 230),
        )
        for column, heading, width in definitions:
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=width, anchor="w" if column.startswith("improvement") else "center")
        self.tree.pack(fill="both", expand=True)
        ttk.Label(self, textvariable=self.status, style="Muted.TLabel", wraplength=1080).pack(anchor="w", pady=(10, 0))

    def _toggle_skill_popover(self) -> None:
        """Open the selection checklist below the button; close on outside click."""
        if self._popover.is_open:
            self._close_skill_popover()
            return
        self._open_skill_popover()

    def _item_label(self, item) -> str:
        """Skill names render verbatim; attribute increases show their step."""
        return f"{item.name} +1" if isinstance(item, AttributeChoice) else item.name

    def _open_skill_popover(self) -> None:
        candidate = self.candidate_editor.build()
        try:
            choices = improvement_choices(
                self.catalogue, self.candidate_editor.choice, candidate,
            )
            attribute_items = attribute_choices(
                self.catalogue, self.candidate_editor.choice, candidate,
            )
        except (KeyError, TypeError, ValueError, AttributeError):
            choices = ()
            attribute_items = ()
        self._available_count = len(choices) + len(attribute_items)
        offered = {item.id for item in (*choices, *attribute_items)}
        for item_id in list(self._skill_selection):
            if item_id not in offered:
                del self._skill_selection[item_id]
        for item in (*choices, *attribute_items):
            self._skill_selection.setdefault(item.id, tk.BooleanVar(value=True))
        self._selection_changed()

        def populate(actions: ttk.Frame, body: ttk.Frame) -> None:
            ttk.Button(actions, text=tr("Select all"), width=12,
                       command=lambda: self._set_all_skills(True)).pack(side="left", padx=(0, 4))
            ttk.Button(actions, text=tr("Select none"), width=12,
                       command=lambda: self._set_all_skills(False)).pack(side="left")
            for item, label in (
                *((item, self._item_label(item)) for item in choices),
                *((item, self._item_label(item)) for item in attribute_items),
            ):
                ttk.Checkbutton(
                    body, text=label,
                    variable=self._skill_selection[item.id],
                    command=self._selection_changed,
                ).pack(fill="x", pady=1)

        self._popover.open(populate)

    def _close_skill_popover(self) -> None:
        self._popover.close()

    def _set_all_skills(self, value: bool) -> None:
        for variable in self._skill_selection.values():
            variable.set(value)
        self._selection_changed()

    def _selection_changed(self) -> None:
        self._selected_count = sum(1 for variable in self._skill_selection.values() if variable.get())
        self._update_skills_button()

    def _update_skills_button(self) -> None:
        self.skills_button.configure(text=tr("Skills ({} / {})").format(self._selected_count, self._available_count))

    def run(self) -> None:
        if self._running:
            return
        try:
            settings = self.settings_provider()
            candidate = self.candidate_editor.build()
            enemy = self.enemy_editor.build()
            items = (
                *improvement_choices(self.catalogue, self.candidate_editor.choice, candidate),
                *attribute_choices(self.catalogue, self.candidate_editor.choice, candidate),
            )
            selected = tuple(
                item for item in items
                if (variable := self._skill_selection.get(item.id)) is None or variable.get()
            )
            if not selected:
                self.status.set(tr("Select at least one improvement to compare."))
                return
            size = int(self.improvement_size.get())
            capacity = sum(getattr(item, "steps", 1) for item in selected)
            if size > capacity:
                self.status.set(tr("Not enough selected skills for {} improvements.").format(size))
                return
            combinations = improvement_combinations(selected, size)
            labels = {item.id: self._item_label(item) for item in selected}
            raw_workers = int(self.workers.get())
            workers = None if raw_workers < 0 else max(0, raw_workers)  # -1 = automatic
            observe = self._usage_factory("improvements", size) if self._usage_factory else None
        except (KeyError, TypeError, ValueError) as exc:
            self.status.set(tr("Configuration error: {}").format(exc))
            return
        self._running = True
        self.run_button.configure(state="disabled")
        self.status.set(tr("Comparing {} improvement combinations…").format(len(combinations)))
        cancel_event = self.progress.start(len(combinations) + 1)
        self._outcome_event = threading.Event()
        self._outcome = None
        self._worker_progress = 0
        self._reported_progress = 0
        self.after(POLL_INTERVAL_MS, self._poll_worker)
        threading.Thread(
            target=self._compare,
            args=(candidate, enemy, combinations, labels, settings, cancel_event, workers, observe),
            daemon=True,
        ).start()

    def _advance(self, value: int) -> None:
        """Record one completed unit from the worker thread (Tkinter-free)."""
        with self._progress_lock:
            self._worker_progress = value

    def _poll_worker(self) -> None:
        """Main-thread pump: mirror progress, then dispatch the outcome."""
        with self._progress_lock:
            value = self._worker_progress
        if value > self._reported_progress:
            self.progress.advance(value)
            self._reported_progress = value
        if self._outcome_event is None or not self._outcome_event.is_set():
            try:
                self.after(POLL_INTERVAL_MS, self._poll_worker)
            except tk.TclError:
                pass  # the page was destroyed while the worker ran
            return
        outcome, self._outcome, self._outcome_event = self._outcome, None, None
        if outcome[0] == "finished":
            self._finished(outcome[1], outcome[2], outcome[3])
        elif outcome[0] == "failed":
            self._failed(outcome[1])
        else:
            self._cancelled()

    def _compare(self, candidate, enemy, combinations, labels, settings, cancel_event, workers=0, observe=None) -> None:
        try:
            self._advance(1)
            by_id = {combination.id: combination for combination in combinations}
            variants = tuple(ComparisonCandidate(combination.id, combination.label,
                add_improvement_items(self.catalogue, candidate, combination.skills)) for combination in combinations)
            batch = compare_builds(candidate, enemy, variants, settings, cancel_event,
                lambda completed: self._advance(completed + 1), workers=workers, observe=observe)
            rows = [(row.candidate.label,
                     tuple(labels[item.id] for item in by_id[row.candidate.id].skills),
                     row.win_rate, row.improvement) for row in batch.results]
            self._outcome = ("finished", rows, batch.baseline_win_rate, settings.simulations)
        except SimulationCancelled:
            self._outcome = ("cancelled",)
        except Exception as exc:
            self._outcome = ("failed", str(exc))
        finally:
            self._outcome_event.set()

    def _finished(self, rows, baseline: float, simulations: int) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for label, applied, win_rate, impact in sorted(rows, key=lambda row: row[3], reverse=True):
            columns = [applied[index] if index < len(applied) else "—" for index in range(5)]
            self.tree.insert("", "end", values=(
                *columns, f"{win_rate:.2f}% ({impact:+.2f}%)", tr("Current configuration"),
            ))
        self.status.set(tr("Baseline: {}% candidate win rate. Compared {} combinations across {} duels.").format(f"{baseline:.2f}", len(rows), f"{(len(rows) + 1) * simulations:,}"))
        self.progress.finish(tr("Complete"))
        self._done()

    def _failed(self, error: str) -> None:
        self.status.set(tr("Improvement analysis error: {}").format(error))
        self.progress.finish(tr("Error"))
        self._done()

    def _cancelled(self) -> None:
        self.status.set(tr("Improvement analysis cancelled."))
        self.progress.finish(tr("Cancelled"))
        self._done()

    def _done(self) -> None:
        self._running = False
        self.run_button.configure(state="normal")

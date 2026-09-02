"""ui.tabs.improvements: responsabilidad extraída sin alterar las reglas."""
from __future__ import annotations

from mordheim_combat_lab.application.analyses import (
    ComparisonCandidate, add_improvement, compare_builds, improvement_choices,
)
from mordheim_combat_lab.domain.models import SimulationCancelled
from mordheim_combat_lab.ui.widgets.progress import AnalysisProgress
import threading as threading
from tkinter import StringVar
from tkinter import ttk


class ImprovementAnalysisTab(ttk.Frame):
    """Compare each selectable additional skill against the current build."""

    def __init__(self, parent, catalogue, candidate_editor, enemy_editor, settings_provider, simulations):
        super().__init__(parent, padding=12)
        self.catalogue = catalogue
        self.candidate_editor = candidate_editor
        self.enemy_editor = enemy_editor
        self.settings_provider = settings_provider
        self.simulations = simulations
        self.status = StringVar(value="Compare each legal additional skill against the candidate baseline.")
        self._running = False
        self._build_gui()

    def _build_gui(self) -> None:
        ttk.Label(self, text="Improvement analysis", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(self, text="Each result adds one currently unselected, profile-legal skill to the candidate configuration.", style="Muted.TLabel").pack(anchor="w", pady=(2, 12))
        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(0, 10))
        ttk.Label(controls, text="Simulations").pack(side="left", padx=(0, 5))
        ttk.Spinbox(controls, from_=1_000, to=10_000_000, increment=10_000, textvariable=self.simulations, width=12).pack(side="left", padx=(0, 12))
        self.run_button = ttk.Button(controls, text="Compare improvements", style="Accent.TButton", command=self.run)
        self.run_button.pack(side="left")
        self.progress = AnalysisProgress(self)
        self.progress.pack(fill="x", pady=(0, 10))
        # Keep the workbook-style result layout from the legacy Improvements
        # page.  The current runtime evaluates one added skill at a time, so
        # only the first improvement column is populated.
        columns = ("improvement1", "improvement2", "improvement3", "improvement4", "improvement5", "optimal", "equipment")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        definitions = (
            ("improvement1", "Improvement 1", 210), ("improvement2", "Improvement 2", 160),
            ("improvement3", "Improvement 3", 160), ("improvement4", "Improvement 4", 160),
            ("improvement5", "Improvement 5", 160), ("optimal", "Best Result", 170),
            ("equipment", "Equipment Used", 230),
        )
        for column, heading, width in definitions:
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=width, anchor="w" if column.startswith("improvement") else "center")
        self.tree.pack(fill="both", expand=True)
        ttk.Label(self, textvariable=self.status, style="Muted.TLabel", wraplength=1080).pack(anchor="w", pady=(10, 0))

    def run(self) -> None:
        if self._running:
            return
        try:
            settings = self.settings_provider()
            candidate = self.candidate_editor.build()
            enemy = self.enemy_editor.build()
            skills = improvement_choices(
                self.catalogue, self.candidate_editor.choice, candidate,
            )
        except (KeyError, TypeError, ValueError) as exc:
            self.status.set(f"Configuration error: {exc}")
            return
        self._running = True
        self.run_button.configure(state="disabled")
        self.status.set(f"Comparing {len(skills)} additional skills…")
        cancel_event = self.progress.start(len(skills) + 1)
        threading.Thread(target=self._compare, args=(candidate, enemy, skills, settings, cancel_event), daemon=True).start()

    def _compare(self, candidate, enemy, skills, settings, cancel_event) -> None:
        try:
            self.after(0, self.progress.advance, 1)
            variants = tuple(ComparisonCandidate(skill.id, skill.name,
                add_improvement(self.catalogue, candidate, skill)) for skill in skills)
            batch = compare_builds(candidate, enemy, variants, settings, cancel_event,
                lambda completed: self.after(0, self.progress.advance, completed + 1))
            rows = [(row.candidate.label, row.win_rate, row.improvement,
                     row.enemy_win_rate, row.unresolved_rate) for row in batch.results]
        except SimulationCancelled:
            self.after(0, self._cancelled)
        except Exception as exc:
            self.after(0, self._failed, str(exc))
        else:
            self.after(0, self._finished, rows, batch.baseline_win_rate, settings.simulations)

    def _finished(self, rows, baseline: float, simulations: int) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for skill, candidate, impact, _enemy, _unresolved in sorted(rows, key=lambda row: row[2], reverse=True):
            self.tree.insert("", "end", values=(
                skill, "—", "—", "—", "—",
                f"{candidate:.2f}% ({impact:+.2f}%)", "Current configuration",
            ))
        self.status.set(f"Baseline: {baseline:.2f}% candidate win rate. Compared {len(rows)} skills across {(len(rows) + 1) * simulations:,} duels.")
        self.progress.finish("Complete")
        self._done()

    def _failed(self, error: str) -> None:
        self.status.set(f"Improvement analysis error: {error}")
        self.progress.finish("Error")
        self._done()

    def _cancelled(self) -> None:
        self.status.set("Improvement analysis cancelled.")
        self.progress.finish("Cancelled")
        self._done()

    def _done(self) -> None:
        self._running = False
        self.run_button.configure(state="normal")

"""ui: Weapons tab: weapon catalogue and pairing."""
from __future__ import annotations

from dataclasses import replace
from mordheim_combat_lab.application.motta import motta_score
from mordheim_combat_lab.application.analyses import ComparisonCandidate, compare_builds
from mordheim_core.models import SimulationCancelled
from mordheim_combat_lab.ui.widgets.checklist_popover import ChecklistPopover
from mordheim_combat_lab.ui.widgets.progress import AnalysisProgress
from mordheim_ui.i18n import tr
import threading as threading
import tkinter as tk
from tkinter import StringVar
from tkinter import ttk


#: Main-thread poll interval while a worker computes the comparison.
POLL_INTERVAL_MS = 30

#: Checklist popover height in pixels; the scrollbar handles the overflow.
POPUP_HEIGHT = 240


class WeaponAnalysisTab(ttk.Frame):
    """Compare the selected legal candidate weapons against the enemy."""

    def __init__(self, parent, catalogue, candidate_editor, enemy_editor, settings_provider, simulations, usage_factory=None):
        super().__init__(parent, padding=12)
        self.catalogue = catalogue
        self.candidate_editor = candidate_editor
        self.enemy_editor = enemy_editor
        self.settings_provider = settings_provider
        self.simulations = simulations
        self.workers = tk.IntVar(value=-1)
        self._usage_factory = usage_factory
        self.status = StringVar(value=tr("Configure the duel, then compare the candidate's legal weapons."))
        self._weapon_selection: dict[str, tk.BooleanVar] = {}
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
        ttk.Label(self, text=tr("Weapon analysis"), style="Heading.TLabel").pack(anchor="w")
        ttk.Label(self, text=tr("Each selected main weapon is simulated against the current enemy configuration."), style="Muted.TLabel").pack(anchor="w", pady=(2, 12))
        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(0, 10))
        ttk.Label(controls, text=tr("Simulations")).pack(side="left", padx=(0, 5))
        ttk.Spinbox(controls, from_=1_000, to=10_000_000, increment=10_000, textvariable=self.simulations, width=12).pack(side="left", padx=(0, 12))
        ttk.Label(controls, text=tr("Battery workers (-1 = automatic, 0 = sequential)")).pack(side="left", padx=(0, 5))
        ttk.Spinbox(controls, from_=-1, to=32, increment=1, textvariable=self.workers, width=5).pack(side="left", padx=(0, 12))
        self.weapons_button = ttk.Button(controls, text=tr("Weapons ({} / {})").format(0, 0), command=self._toggle_weapon_popover)
        self.weapons_button.pack(side="left", padx=(0, 12))
        self._popover = ChecklistPopover(self.weapons_button, height=POPUP_HEIGHT)
        self.run_button = ttk.Button(controls, text=tr("Compare weapons"), style="Accent.TButton", command=self.run)
        self.run_button.pack(side="left")
        self.progress = AnalysisProgress(self)
        self.progress.pack(fill="x", pady=(0, 10))
        columns = ("main", "off", "single", "shield", "dual", "two_hand", "optimal", "motta", "cost", "equipment")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        definitions = (
            ("main", tr("Main Weapon"), 230), ("off", tr("Off-Hand Weapon"), 210),
            ("single", tr("Free Hand"), 155), ("shield", tr("Shield"), 155),
            ("dual", tr("Two Weapons"), 155), ("two_hand", tr("Two Hands"), 155),
            ("optimal", tr("Best Result"), 175), ("motta", tr("MOTTA Score"), 130),
            ("cost", tr("Cost"), 130), ("equipment", tr("Equipment Used"), 220),
        )
        for column, heading, width in definitions:
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=width, anchor="w" if column in {"main", "off"} else "center")
        self.tree.pack(fill="both", expand=True)
        ttk.Label(self, textvariable=self.status, style="Muted.TLabel", wraplength=1080).pack(anchor="w", pady=(10, 0))

    # ------------------------------------------------------- weapon picker

    def _weapon_options(self):
        """Legal main weapons of the current candidate, editor options first."""
        return self.candidate_editor.main_weapon_options()

    def _toggle_weapon_popover(self) -> None:
        if self._popover.is_open:
            self._close_weapon_popover()
            return
        self._open_weapon_popover()

    def _open_weapon_popover(self) -> None:
        offered = {item_id: name for item_id, name in self._weapon_options()}
        for item_id in list(self._weapon_selection):
            if item_id not in offered:
                del self._weapon_selection[item_id]
        for item_id in offered:
            self._weapon_selection.setdefault(item_id, tk.BooleanVar(value=True))
        self._available_count = len(offered)
        self._selection_changed()

        def populate(actions: ttk.Frame, body: ttk.Frame) -> None:
            ttk.Button(actions, text=tr("Select all"), width=12,
                       command=lambda: self._set_all_weapons(True)).pack(side="left", padx=(0, 4))
            ttk.Button(actions, text=tr("Select none"), width=12,
                       command=lambda: self._set_all_weapons(False)).pack(side="left")
            for item_id, name in offered.items():
                ttk.Checkbutton(
                    body, text=name,
                    variable=self._weapon_selection[item_id],
                    command=self._selection_changed,
                ).pack(fill="x", pady=1)

        self._popover.open(populate)

    def _close_weapon_popover(self) -> None:
        self._popover.close()

    def _set_all_weapons(self, value: bool) -> None:
        for variable in self._weapon_selection.values():
            variable.set(value)
        self._selection_changed()

    def _selection_changed(self) -> None:
        self._selected_count = sum(1 for variable in self._weapon_selection.values() if variable.get())
        self.weapons_button.configure(text=tr("Weapons ({} / {})").format(self._selected_count, self._available_count))

    # ------------------------------------------------------------ analysis

    def run(self) -> None:
        if self._running:
            return
        try:
            settings = self.settings_provider()
            candidate = self.candidate_editor.build()
            enemy = self.enemy_editor.build()
            options = self._weapon_options()
            selected = tuple(
                (item_id, name) for item_id, name in options
                if (variable := self._weapon_selection.get(item_id)) is None or variable.get()
            )
            if not selected:
                self.status.set(tr("Select at least one weapon to compare."))
                return
            raw_workers = int(self.workers.get())
            workers = None if raw_workers < 0 else max(0, raw_workers)  # -1 = automatic
            observe = self._usage_factory("weapons", len(selected)) if self._usage_factory else None
        except (KeyError, TypeError, ValueError) as exc:
            self.status.set(tr("Configuration error: {}").format(exc))
            return
        self._running = True
        self.run_button.configure(state="disabled")
        self.status.set(tr("Comparing {} weapons with {} duels each…").format(len(selected), f"{settings.simulations:,}"))
        cancel_event = self.progress.start(len(selected))
        self._outcome_event = threading.Event()
        self._outcome = None
        self._worker_progress = 0
        self._reported_progress = 0
        self.after(POLL_INTERVAL_MS, self._poll_worker)
        threading.Thread(
            target=self._compare,
            args=(candidate, enemy, selected, settings, cancel_event, workers, observe),
            daemon=True,
        ).start()

    def _advance(self, value: int) -> None:
        with self._progress_lock:
            self._worker_progress = value

    def _poll_worker(self) -> None:
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
            self._finished(outcome[1], outcome[2])
        elif outcome[0] == "failed":
            self._failed(outcome[1])
        else:
            self._cancelled()

    def _compare(self, candidate, enemy, options, settings, cancel_event, workers=0, observe=None) -> None:
        try:
            by_id = {weapon_id: name for weapon_id, name in options}
            variants = []
            for weapon_id, name in options:
                off_hand = candidate.off_hand_id
                if self.catalogue.mechanic(weapon_id).get("hands") == 2:
                    off_hand = None
                variants.append(ComparisonCandidate(weapon_id, name,
                    replace(candidate, main_weapon_id=weapon_id, off_hand_id=off_hand)))
            batch = compare_builds(candidate, enemy, variants, settings, cancel_event,
                lambda completed: self._advance(completed), workers=workers, observe=observe)
            rows = [(row.candidate.id, row.candidate.label, row.win_rate, row.improvement) for row in batch.results]
            self._outcome = ("finished", rows, settings.simulations)
        except SimulationCancelled:
            self._outcome = ("cancelled",)
        except Exception as exc:  # surface the real failure text, never "None"
            self._outcome = ("failed", f"{type(exc).__name__}: {exc}")
        finally:
            self._outcome_event.set()

    def _finished(self, rows, simulations: int) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        configured_candidate = self.candidate_editor.build()
        off_hand_id = self.candidate_editor.off_hand.get()
        off_hand_label = self.candidate_editor.catalogue.localized_name(off_hand_id, "Free hand") if off_hand_id else tr("Free hand")
        for weapon_id, name, win_rate, impact in sorted(rows, key=lambda row: row[3], reverse=True):
            if weapon_id and self.catalogue.mechanic(weapon_id).get("hands") == 2:
                mode = "two_hand"
                displayed_off_hand = "—"
            elif off_hand_id is None:
                mode, displayed_off_hand = "single", "—"
            elif weapon_id and off_hand_id and off_hand_id.startswith("weapon."):
                mode, displayed_off_hand = "dual", off_hand_label
            else:
                mode, displayed_off_hand = "shield", off_hand_label
            mode_cells = ["", "", "", ""]
            mode_cells[("single", "shield", "dual", "two_hand").index(mode)] = f"{win_rate:.2f}% ({impact:+.2f}%)"
            cost = 0.0 if weapon_id == configured_candidate.main_weapon_id else self.catalogue.cost(weapon_id, self.candidate_editor.choice)
            motta = motta_score(impact, cost)
            cost_display = f"{cost:g} gc" if cost is not None else "—"
            self.tree.insert("", "end", values=(
                name, displayed_off_hand, *mode_cells,
                f"{win_rate:.2f}% ({impact:+.2f}%)", f"{motta:.2f}" if motta is not None else "—", cost_display, "Current configuration",
            ))
        self.status.set(tr("Compared {} weapons across {} duels.").format(len(rows), f"{len(rows) * simulations:,}"))
        self.progress.finish(tr("Complete"))
        self._done()

    def _failed(self, error: str) -> None:
        self.status.set(tr("Weapon analysis error: {}").format(error))
        self.progress.finish(tr("Error"))
        self._done()

    def _cancelled(self) -> None:
        self.status.set(tr("Weapon analysis cancelled."))
        self.progress.finish(tr("Cancelled"))
        self._done()

    def _done(self) -> None:
        self._running = False
        self.run_button.configure(state="normal")

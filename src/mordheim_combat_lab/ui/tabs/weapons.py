"""ui.tabs.weapons: responsibility extracted without altering the rules."""
from __future__ import annotations

from dataclasses import replace
from mordheim_combat_lab.application.motta import motta_score
from mordheim_combat_lab.application.analyses import ComparisonCandidate, compare_builds
from mordheim_core.models import SimulationCancelled
from mordheim_combat_lab.ui.widgets.progress import AnalysisProgress
import threading as threading
from tkinter import StringVar
from tkinter import ttk


class WeaponAnalysisTab(ttk.Frame):
    """Compare every legal candidate weapon against the configured enemy."""

    def __init__(self, parent, catalogue, candidate_editor, enemy_editor, settings_provider, simulations):
        super().__init__(parent, padding=12)
        self.catalogue = catalogue
        self.candidate_editor = candidate_editor
        self.enemy_editor = enemy_editor
        self.settings_provider = settings_provider
        self.simulations = simulations
        self.status = StringVar(value="Configure the duel, then compare the candidate's legal weapons.")
        self._running = False
        self._build_gui()

    def _build_gui(self) -> None:
        ttk.Label(self, text="Weapon analysis", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(self, text="Each legal main weapon is simulated against the current enemy configuration.", style="Muted.TLabel").pack(anchor="w", pady=(2, 12))
        controls = ttk.Frame(self)
        controls.pack(fill="x", pady=(0, 10))
        ttk.Label(controls, text="Simulations").pack(side="left", padx=(0, 5))
        ttk.Spinbox(controls, from_=1_000, to=10_000_000, increment=10_000, textvariable=self.simulations, width=12).pack(side="left", padx=(0, 12))
        self.run_button = ttk.Button(controls, text="Compare weapons", style="Accent.TButton", command=self.run)
        self.run_button.pack(side="left")
        self.progress = AnalysisProgress(self)
        self.progress.pack(fill="x", pady=(0, 10))
        columns = ("main", "off", "single", "shield", "dual", "two_hand", "optimal", "motta", "cost", "equipment")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        definitions = (
            ("main", "Main Weapon", 230), ("off", "Off-Hand Weapon", 210),
            ("single", "Free Hand", 155), ("shield", "Shield", 155),
            ("dual", "Two Weapons", 155), ("two_hand", "Two Hands", 155),
            ("optimal", "Best Result", 175), ("motta", "MOTTA Score", 130),
            ("cost", "Cost", 130), ("equipment", "Equipment Used", 220),
        )
        for column, heading, width in definitions:
            self.tree.heading(column, text=heading)
            self.tree.column(column, width=width, anchor="w" if column in {"main", "off"} else "center")
        self.tree.pack(fill="both", expand=True)
        ttk.Label(self, textvariable=self.status, style="Muted.TLabel", wraplength=1080).pack(anchor="w", pady=(10, 0))

    def run(self) -> None:
        if self._running:
            return
        try:
            settings = self.settings_provider()
            candidate = self.candidate_editor.build()
            enemy = self.enemy_editor.build()
            options = self.candidate_editor.main_weapon_options()
            if not options:
                raise ValueError("At least one legal weapon is required.")
        except (KeyError, TypeError, ValueError) as exc:
            self.status.set(f"Configuration error: {exc}")
            return
        self._running = True
        self.run_button.configure(state="disabled")
        self.status.set(f"Comparing {len(options)} weapons with {settings.simulations:,} duels each…")
        cancel_event = self.progress.start(len(options))
        threading.Thread(target=self._compare, args=(candidate, enemy, options, settings, cancel_event), daemon=True).start()

    def _compare(self, candidate, enemy, options, settings, cancel_event) -> None:
        try:
            variants = []
            for weapon_id, name in options:
                off_hand = candidate.off_hand_id
                if self.catalogue.mechanic(weapon_id).get("hands") == 2:
                    off_hand = None
                variants.append(ComparisonCandidate(weapon_id, name,
                    replace(candidate, main_weapon_id=weapon_id, off_hand_id=off_hand)))
            batch = compare_builds(candidate, enemy, variants, settings, cancel_event,
                lambda completed: self.after(0, self.progress.advance, completed))
            rows = [(row.candidate.label, row.win_rate, row.improvement) for row in batch.results]
        except SimulationCancelled:
            self.after(0, self._cancelled)
        except Exception as exc:
            self.after(0, self._failed, str(exc))
        else:
            self.after(0, self._finished, rows, settings.simulations)

    def _finished(self, rows, simulations: int) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        configured_candidate = self.candidate_editor.build()
        off_hand = self.candidate_editor.off_hand_name.get() or "Free hand"
        for name, candidate, impact in sorted(rows, key=lambda row: row[1], reverse=True):
            weapon_id = next((item_id for item_id, item_name in self.candidate_editor.main_weapon_options() if item_name == name), "")
            if self.catalogue.mechanic(weapon_id).get("hands") == 2:
                mode = "two_hand"
                displayed_off_hand = "—"
            elif off_hand == "Free hand":
                mode, displayed_off_hand = "single", "—"
            elif weapon_id and self.candidate_editor._active_off_hands.get(off_hand, "").startswith("weapon."):
                mode, displayed_off_hand = "dual", off_hand
            else:
                mode, displayed_off_hand = "shield", off_hand
            mode_cells = ["", "", "", ""]
            mode_cells[("single", "shield", "dual", "two_hand").index(mode)] = f"{candidate:.2f}% ({impact:+.2f}%)"
            cost = 0.0 if weapon_id == configured_candidate.main_weapon_id else self.catalogue.cost(weapon_id, self.candidate_editor.choice)
            motta = motta_score(impact, cost)
            cost_display = f"{cost:g} gc" if cost is not None else "—"
            self.tree.insert("", "end", values=(
                name, displayed_off_hand, *mode_cells,
                f"{candidate:.2f}% ({impact:+.2f}%)", f"{motta:.2f}" if motta is not None else "—", cost_display, "Current configuration",
            ))
        self.status.set(f"Compared {len(rows)} weapons across {len(rows) * simulations:,} duels.")
        self.progress.finish("Complete")
        self._done()

    def _failed(self, error: str) -> None:
        self.status.set(f"Weapon analysis error: {error}")
        self.progress.finish("Error")
        self._done()

    def _cancelled(self) -> None:
        self.status.set("Weapon analysis cancelled.")
        self.progress.finish("Cancelled")
        self._done()

    def _done(self) -> None:
        self._running = False
        self.run_button.configure(state="normal")

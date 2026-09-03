"""ui.app: responsibility extracted without altering the rules."""
from __future__ import annotations

from mordheim_combat_lab.application.catalogue import CombatCatalogue
from mordheim_combat_lab.application.settings import DuelExecutionSettings
from mordheim_combat_lab.persistence.preferences import load_preferences
from mordheim_combat_lab.persistence.preferences import save_preferences
from mordheim_combat_lab.persistence.workbooks import CombatLabWorkbookError
from mordheim_combat_lab.persistence.workbooks import load_ui_workbook
from mordheim_combat_lab.persistence.workbooks import save_workbook
from mordheim_combat_lab.ui.editors import FighterEditor
from mordheim_combat_lab.ui.tabs.equipment import EquipmentAnalysisTab
from mordheim_combat_lab.ui.tabs.improvements import ImprovementAnalysisTab
from mordheim_combat_lab.ui.tabs.weapons import WeaponAnalysisTab
from mordheim_ui.lab_theme import apply_theme
from mordheim_combat_lab.ui.widgets.feedback import destroy_tooltips
import os as os
import time as time
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk


WINDOW_MOVE_THROTTLE_MS = 12 if os.name == "nt" else 0


def _preference_int(preferences: dict, key: str, default: int, minimum: int = 0) -> int:
    """Read a bounded integer preference without making startup fragile."""
    try:
        value = int(preferences.get(key, default))
    except (TypeError, ValueError):
        return default
    return value if value >= minimum else default


class CombatLabApp(tk.Tk):
    """KB-driven application shell with the legacy workbook layout.

    The original application deliberately separated configuring the candidate,
    configuring enemies and reviewing each analysis.  Keeping that information
    architecture is important: a "Duel" page with two anonymous cards made
    the new runtime feel like a different product.  The widgets below are new
    views over :class:`FighterBuild`, not adapters for ``legacy_ui``.
    """

    def __init__(self):
        super().__init__()
        apply_theme(self)
        self.title("Mordheim Combat Lab")
        self.minsize(900, 700)
        self._preferences = load_preferences()
        self.geometry(str(self._preferences.get("window_geometry") or "1180x800"))
        self.catalogue = CombatCatalogue()
        self.collection_categories = {
            category: tk.BooleanVar(value=True)
            for category in ("core", "1a", "1b", "1c", "trollheim")
        }
        self.simulations = tk.IntVar(value=_preference_int(self._preferences, "simulations", 100_000, 1))
        self.seed = tk.IntVar(value=_preference_int(self._preferences, "seed", 0))
        self.batch_size = tk.IntVar(value=_preference_int(self._preferences, "batch_size", 100_000, 1))
        self.maximum_rounds = tk.IntVar(value=_preference_int(self._preferences, "maximum_rounds", 50, 1))
        self.analysis_simulations = {
            tab: tk.IntVar(value=self.simulations.get())
            for tab in ("improvements", "weapons", "equipment")
        }
        self.status = tk.StringVar(value="Configure the candidate and enemy, then use an analysis tab.")
        self._last_result = None
        self.enemy_editor = None
        self._build_gui()
        self._restore_geometry()
        self._initialize_window_move_throttle()
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build_gui(self) -> None:
        header = ttk.Frame(self, padding=(20, 14, 20, 10))
        header.pack(fill="x")
        branding = ttk.Frame(header)
        branding.pack(side="left")
        ttk.Label(branding, text="Mordheim Combat Lab", style="Title.TLabel").pack(anchor="w")
        ttk.Label(branding, text="Simulation Workbook", style="Muted.TLabel").pack(anchor="w")
        actions = ttk.Frame(header)
        actions.pack(side="right")
        self.collections_button = ttk.Menubutton(actions, text="Collections ▾")
        collections_menu = tk.Menu(self.collections_button, tearoff=False)
        for category, label in (("core", "Mordheim Core"), ("1a", "1A"), ("1b", "1B"), ("1c", "1C"), ("trollheim", "Trollheim")):
            collections_menu.add_checkbutton(label=label, variable=self.collection_categories[category], command=self._collections_changed)
        self.collections_button.configure(menu=collections_menu)
        self.collections_button.pack(side="left", padx=(0, 10))
        import_button = ttk.Menubutton(actions, text="Import ▾")
        import_menu = tk.Menu(import_button, tearoff=False)
        import_menu.add_command(label="Load candidate", command=lambda: self._load_workbook("candidate"))
        import_menu.add_command(label="Load enemy", command=lambda: self._load_workbook("enemy"))
        import_button.configure(menu=import_menu)
        import_button.pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Load", command=self._load_workbook).pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Save", style="Accent.TButton", command=self._save_workbook).pack(side="left")
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True)
        candidate_tab = ttk.Frame(self.notebook, padding=12)
        enemy_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(candidate_tab, text="Candidate")
        self.notebook.add(enemy_tab, text="Enemy")
        self._build_candidate_tab(candidate_tab)
        self._enemy_tab = enemy_tab
        self.notebook.bind("<<NotebookTabChanged>>", self._build_enemy_tab_on_selection, add="+")
        self._lazy_analysis_tabs = {}
        for tab_type, tab_key, title in (
            (ImprovementAnalysisTab, "improvements", "Improvements"),
            (WeaponAnalysisTab, "weapons", "Weapons"),
            (EquipmentAnalysisTab, "equipment", "Equipment"),
        ):
            tab = ttk.Frame(self.notebook)
            self.notebook.add(tab, text=title)
            self._lazy_analysis_tabs[str(tab)] = (tab, tab_type, tab_key)
        self.notebook.bind("<<NotebookTabChanged>>", self._build_selected_analysis_tab, add="+")
        rules_tab = ttk.Frame(self.notebook, padding=20)
        self.notebook.add(rules_tab, text="House Rules")
        self._build_rules_tab(rules_tab)

    def _build_selected_analysis_tab(self, _event=None) -> None:
        """Build an analysis page only when the user first opens it."""
        tab_id = str(self.notebook.select())
        specification = self._lazy_analysis_tabs.pop(tab_id, None)
        if specification is None:
            return

        enemy_editor = self._ensure_enemy_editor()
        tab, tab_type, tab_key = specification
        view = tab_type(
            tab,
            self.catalogue,
            self.candidate_editor,
            enemy_editor,
            self._analysis_settings(tab_key),
            self.analysis_simulations[tab_key],
        )
        view.pack(fill="both", expand=True)

    def _build_candidate_tab(self, parent) -> None:
        ttk.Label(parent, text="Candidate", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(parent, text="Choose a warrior and their legal combat configuration.", style="Muted.TLabel").pack(anchor="w", pady=(2, 12))
        self.candidate_editor = FighterEditor(parent, "Candidate", self.catalogue, self._editor_changed)
        self.candidate_editor.pack(fill="x")

    def _build_enemy_tab_on_selection(self, _event=None) -> None:
        """Build the Enemy editor the first time its page is selected."""
        if str(self.notebook.select()) == str(self._enemy_tab):
            self._ensure_enemy_editor()

    def _ensure_enemy_editor(self) -> FighterEditor:
        """Return the Enemy editor, constructing its deferred page if needed."""
        if self.enemy_editor is not None:
            return self.enemy_editor

        ttk.Label(self._enemy_tab, text="Enemy", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(self._enemy_tab, text="Configure the opposing warrior used by every simulation and analysis.", style="Muted.TLabel").pack(anchor="w", pady=(2, 12))
        self.enemy_editor = FighterEditor(self._enemy_tab, "Enemy", self.catalogue, self._editor_changed)
        self.enemy_editor.pack(fill="x")
        return self.enemy_editor

    def _collections_changed(self) -> None:
        """Filter both editor warband lists by the selected KB source grades."""
        categories = {category for category, variable in self.collection_categories.items() if variable.get()}
        self.candidate_editor.set_categories(categories)
        if self.enemy_editor is not None:
            self.enemy_editor.set_categories(categories)

    def _build_rules_tab(self, parent) -> None:
        ttk.Label(parent, text="House Rules", style="Heading.TLabel").pack(anchor="w")
        ttk.Label(
            parent,
            text=("The executable rules are selected by the knowledge base. "
                  "This version deliberately does not restore the legacy checkboxes: "
                  "they altered the retired engine and could silently produce a duel "
                  "that the new runtime cannot represent."),
            style="Muted.TLabel", wraplength=820, justify="left",
        ).pack(anchor="w", pady=(8, 16))
        ttk.Label(parent, text="Active runtime", style="Section.TLabel").pack(anchor="w")
        ttk.Label(parent, text="Mordheim close combat · KB-backed legal equipment · deterministic seed support", style="Muted.TLabel").pack(anchor="w", pady=(4, 0))

    def _restore_geometry(self) -> None:
        """Use the former centred-window behaviour unless a size was saved."""
        if self._preferences.get("window_geometry"):
            return
        width = min(1280, max(900, self.winfo_screenwidth() - 100))
        height = min(1050, max(700, self.winfo_screenheight() - 30))
        self.geometry(f"{width}x{height}+{max(0, (self.winfo_screenwidth() - width) // 2)}+{max(0, (self.winfo_screenheight() - height) // 2)}")

    def _initialize_window_move_throttle(self) -> None:
        """Throttle pure window movement on Windows to coalesce Configure events."""
        if WINDOW_MOVE_THROTTLE_MS <= 0:
            return

        self._window_move_throttle_geometry = None
        self.bind("<Configure>", self._throttle_window_move, add="+")

    def _throttle_window_move(self, event) -> None:
        """Delay only pure top-level movement; resizing is never throttled."""
        if event.widget is not self:
            return

        geometry = (int(event.x), int(event.y), int(event.width), int(event.height))
        previous = self._window_move_throttle_geometry
        self._window_move_throttle_geometry = geometry

        if previous is None:
            return

        moved = geometry[:2] != previous[:2]
        resized = geometry[2:] != previous[2:]
        if moved and not resized:
            time.sleep(WINDOW_MOVE_THROTTLE_MS / 1000.0)

    def _editor_changed(self) -> None:
        self.status.set("Ready for an analysis with the selected fighters.")

    def execution_settings(self) -> DuelExecutionSettings:
        """Snapshot the execution controls for one simulation or analysis run."""
        return DuelExecutionSettings(int(self.simulations.get()), int(self.seed.get()), int(self.batch_size.get()), int(self.maximum_rounds.get()))

    def _analysis_settings(self, tab: str):
        """Return the independent simulation count configured on one analysis tab."""
        def provider() -> DuelExecutionSettings:
            simulations = int(self.analysis_simulations[tab].get())
            # The workbook retains the most recently used analysis settings.
            self.simulations.set(simulations)
            return DuelExecutionSettings(simulations, int(self.seed.get()), int(self.batch_size.get()), int(self.maximum_rounds.get()))
        return provider

    def _save_workbook(self) -> None:
        try:
            candidate = self.candidate_editor.build()
            enemy = self._ensure_enemy_editor().build()
            settings = self.execution_settings()
        except (KeyError, TypeError, ValueError) as exc:
            self.status.set(f"Configuration error: {exc}")
            return
        path = filedialog.asksaveasfilename(
            parent=self, title="Save Mordheim Combat Lab workbook", defaultextension=".xlsx",
            filetypes=(("Excel workbook", "*.xlsx"),),
        )
        if not path:
            return
        try:
            save_workbook(path, candidate, enemy, settings, self._last_result)
        except OSError as exc:
            self.status.set(f"Workbook save error: {exc}")
        else:
            self.status.set(f"Saved workbook: {path}")

    def _load_workbook(self, target: str = "both") -> None:
        path = filedialog.askopenfilename(parent=self, title="Load Mordheim Combat Lab workbook", filetypes=(("Excel workbook", "*.xlsx"),))
        if not path:
            return
        try:
            candidate, enemy, settings, result = load_ui_workbook(path)
            if target in {"both", "candidate"}:
                self.candidate_editor.load_build(candidate)
            if target in {"both", "enemy"}:
                self._ensure_enemy_editor().load_build(enemy)
            if target == "both":
                self.simulations.set(settings.simulations)
                for variable in self.analysis_simulations.values():
                    variable.set(settings.simulations)
                self.seed.set(settings.seed)
                self.batch_size.set(settings.batch_size)
                self.maximum_rounds.set(settings.maximum_rounds)
        except (CombatLabWorkbookError, KeyError, TypeError, ValueError) as exc:
            self.status.set(f"Workbook load error: {exc}")
            return
        self._last_result = result if target == "both" else self._last_result
        description = {"both": "workbook", "candidate": "candidate", "enemy": "enemy"}[target]
        self.status.set(f"Loaded {description}: {path}")

    def _close(self) -> None:
        save_preferences({
            "window_geometry": self.geometry(),
            "simulations": self.simulations.get(),
            "seed": self.seed.get(),
            "batch_size": self.batch_size.get(),
            "maximum_rounds": self.maximum_rounds.get(),
        })
        destroy_tooltips(self)
        self.destroy()


def main() -> int:
    app = CombatLabApp()
    app.mainloop()
    return 0


__all__ = ["CombatLabApp", "main"]

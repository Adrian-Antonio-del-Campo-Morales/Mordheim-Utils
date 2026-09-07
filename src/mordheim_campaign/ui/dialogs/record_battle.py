from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.ui.components import PostBattleSequence
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, ScrollableFrame
from mordheim_ui.i18n import tr


class BattleEntryMoment(tk.Frame):
    """Main-workspace sequence for recording a played battle.

    The scenario picker lists the KB scenario catalogue (1v1 entries first);
    the opponent is free text; result is Victory / Defeat / Draw. Derived
    numbers (rating, models) snapshot automatically from the current state —
    only what the player knows at the table is asked.
    """

    def __init__(self, parent: tk.Misc, controller: AppController, number: int, **kwargs) -> None:
        super().__init__(parent, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        self.number = number
        self._ooa_vars: dict[str, tk.BooleanVar] = {}

        outer = BorderedFrame(self, background=COLORS["panel"], padding=1)
        outer.pack(fill="both", expand=True)
        body = outer.body
        body.configure(padx=20, pady=18, width=620, height=570)

        tk.Label(body, text=tr('BATTLE #{} · RESULTS').format(number), bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 15)).pack(anchor="w")
        tk.Label(
            body,
            text=tr('Record the table facts of a played battle. The post-battle sequence that follows applies injuries, experience, exploration and trading.'),
            bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9), wraplength=580, justify="left",
        ).pack(anchor="w", pady=(4, 10))

        self._scenarios = controller.scenario_options()
        self._build_step_bar(body)
        self.pages = tk.Frame(body, bg=COLORS["panel"])
        self.pages.pack(fill="both", expand=True)
        self.scenario_page = tk.Frame(self.pages, bg=COLORS["panel"])
        self.results_page = tk.Frame(self.pages, bg=COLORS["panel"])

        self._build_scenario(self.scenario_page)
        self._build_opponent(self.scenario_page)

        scroll = ScrollableFrame(self.results_page, background=COLORS["panel"], height=405)
        scroll.pack(fill="both", expand=True)
        results = scroll.inner
        results.configure(padx=2, pady=2)
        self._build_selected_scenario(results)
        self._build_result(results)
        self._build_scenario_results(results)
        self._build_counters(results)
        self._build_casualties(results)
        self._casualties_hint = tk.Label(results, text="", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8))
        self._casualties_hint.pack(anchor="w", pady=(0, 8))
        self._build_notes(results)
        self._build_actions(body)
        self._update_hint()
        self._show_step(0)
        # TODO: Persist a pending battle-entry draft in application state so
        # partially entered scenario answers survive navigating to another
        # timeline row. Currently they live only in this rendered GUI moment.

    # ----------------------------------------------------------------- rows

    def _build_step_bar(self, body: tk.Frame) -> None:
        self.sequence_host = tk.Frame(body, bg=COLORS["panel"])
        self.sequence_host.pack(fill="x", pady=(0, 12))

    def _row(self, body: tk.Frame, label: str) -> tk.Frame:
        row = tk.Frame(body, bg=COLORS["panel"])
        row.pack(fill="x", pady=(0, 8))
        tk.Label(row, text=label, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8), width=16, anchor="w").pack(side="left")
        return row

    def _build_scenario(self, body: tk.Frame) -> None:
        row = self._row(body, tr('SCENARIO'))
        # 1v1 scenarios first, then multiplayer, keeping catalogue order inside each group.
        ordered = sorted(self._scenarios, key=lambda entry: (entry[2] != "1v1",))
        labels = [f"{name}  ·  {mode}" for _sid, name, mode in ordered]
        self._scenario_ids = [scenario_id for scenario_id, _name, _mode in ordered]
        self._scenario_names = {scenario_id: name for scenario_id, name, _mode in self._scenarios}
        self.scenario_box = ttk.Combobox(row, state="readonly", values=labels, width=34)
        self.scenario_box.pack(side="left")
        self.scenario_box.set(labels[0] if labels else tr('(no scenarios)'))
        # TODO: Replace this flat form with a scenario-driven battle sequence.
        # The KB must expose each objective, condition, recipient, amount/die and
        # resulting XP/resource award structurally before the GUI can generate
        # reliable scenario-specific fields and calculate rewards automatically.

    def _build_opponent(self, body: tk.Frame) -> None:
        row = self._row(body, tr('OPPONENT'))
        self.opponent_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.opponent_var, width=28).pack(side="left")
        rating_row = tk.Frame(body, bg=COLORS["panel"])
        rating_row.pack(fill="x", pady=(0, 8))
        tk.Label(rating_row, text=tr('OPPONENT RATING'), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8), width=16, anchor="w").pack(side="left")
        self.rating_var = tk.StringVar()
        ttk.Entry(rating_row, textvariable=self.rating_var, width=8).pack(side="left")
        tk.Label(rating_row, text=tr('(optional)'), bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(side="left", padx=(6, 0))

    def _build_result(self, body: tk.Frame) -> None:
        row = self._row(body, tr('RESULT'))
        self.result_var = tk.StringVar(value=tr('Victory'))
        for value in (tr('Victory'), tr('Defeat'), tr('Draw')):
            ttk.Radiobutton(row, text=value, value=value, variable=self.result_var).pack(side="left", padx=(0, 10))

    def _build_selected_scenario(self, body: tk.Frame) -> None:
        self.selected_scenario_var = tk.StringVar()
        tk.Label(body, textvariable=self.selected_scenario_var, bg=COLORS["panel"], fg=COLORS["accent"], font=("Georgia", 12)).pack(anchor="w", pady=(0, 10))

    def _build_scenario_results(self, body: tk.Frame) -> None:
        outer = BorderedFrame(body, background=COLORS["panel_alt"], padding=1)
        outer.pack(fill="x", pady=(0, 10))
        panel = outer.body
        panel.configure(padx=12, pady=10)
        tk.Label(panel, text=tr('SCENARIO-SPECIFIC RESULTS'), bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(
            panel,
            text=tr('Objectives, casualties caused and scenario rewards will appear here when their rules are available as structured data.'),
            bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8), wraplength=540, justify="left",
        ).pack(anchor="w", pady=(5, 0))
        # TODO: Generate controls from structured scenario result fields and
        # persist their answers with the battle. Current scenario progression
        # entries do not consistently encode condition, recipient, amount/die
        # and resulting XP/resources in machine-readable fields.

    def _build_counters(self, body: tk.Frame) -> None:
        row = self._row(body, tr('EXPERIENCE ADJUSTMENT'))
        self.xp_var = tk.IntVar(value=1)
        ttk.Spinbox(row, from_=0, to=99, width=5, textvariable=self.xp_var).pack(side="left")
        tk.Label(row, text=tr('temporary manual value until scenario rewards are calculated automatically'), bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7), wraplength=400, justify="left").pack(side="left", padx=(8, 0))
        # TODO: Replace xp_delta with per-warrior awards calculated from the
        # selected scenario, result, objectives and enemy Out of Action events.

    def _build_casualties(self, body: tk.Frame) -> None:
        """Checklist of warriors recorded Out of Action (drives Recovery)."""
        self._row(body, tr('OUT OF ACTION'))
        warriors = self.controller.state.campaign.warriors
        box = tk.Frame(body, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["border_soft"])
        box.pack(fill="x", pady=(0, 8))
        inner = tk.Frame(box, bg=COLORS["panel"], padx=10, pady=8)
        inner.pack(fill="x")
        for warrior in warriors:
            label = warrior.name + (f"  ·  ×{warrior.quantity}" if warrior.quantity > 1 else "")
            var = tk.BooleanVar(value=False)
            self._ooa_vars[warrior.id] = var
            ttk.Checkbutton(
                inner, text=label, variable=var,
                command=self._update_hint,
            ).pack(anchor="w", pady=1)
        tk.Label(
            body,
            text=tr("Marked warriors roll on the serious-injury charts in Recovery (post-battle step 1). Henchman groups: ticking marks the whole group's survival roll."),
            bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7), wraplength=430, justify="left",
        ).pack(anchor="w")

    def _build_notes(self, body: tk.Frame) -> None:
        row = self._row(body, tr('NOTES'))
        self.notes_text = tk.Text(
            row, width=48, height=6, wrap="word",
            bg=COLORS["panel_alt"], fg=COLORS["text"],
            insertbackground=COLORS["text"], relief="flat", bd=0,
            highlightthickness=1, highlightbackground=COLORS["border_soft"],
            highlightcolor=COLORS["accent"], padx=7, pady=6,
            font=("Segoe UI", 9),
        )
        self.notes_text.pack(side="left", fill="x", expand=True)

    def _build_actions(self, body: tk.Frame) -> None:
        actions = tk.Frame(body, bg=COLORS["panel"])
        actions.pack(fill="x", pady=(10, 0))
        self.back_button = ttk.Button(actions, text=tr('‹ BACK'), command=lambda: self._show_step(0))
        self.back_button.pack(side="left")
        self.record_button = ttk.Button(actions, text=tr('RECORD & RESOLVE'), style="Accent.TButton", command=self._record)
        self.record_button.pack(side="right")
        self.next_button = ttk.Button(actions, text=tr('CONTINUE ›'), style="Accent.TButton", command=lambda: self._show_step(1))
        self.next_button.pack(side="right")

    # --------------------------------------------------------------- actions

    def _show_step(self, step: int) -> None:
        self.scenario_page.pack_forget()
        self.results_page.pack_forget()
        (self.scenario_page if step == 0 else self.results_page).pack(fill="both", expand=True)
        if step == 1:
            index = max(0, self.scenario_box.current())
            scenario_id = self._scenario_ids[index] if self._scenario_ids else ""
            self.selected_scenario_var.set(self._scenario_names.get(scenario_id, scenario_id))
        for child in self.sequence_host.winfo_children():
            child.destroy()
        PostBattleSequence(
            self.sequence_host,
            ("Scenario", "Results"),
            (("Battle setup", (0,)), ("Battle outcome", (1,))),
            step,
            set(range(step)),
            lambda index: self._show_step(index),
        ).pack(fill="x")
        if step == 0:
            self.back_button.pack_forget()
            self.record_button.pack_forget()
            self.next_button.pack(side="right")
        else:
            self.next_button.pack_forget()
            self.back_button.pack(side="left")
            self.record_button.pack(side="right")

    def _update_hint(self) -> None:
        count = len(self._out_of_action_ids())
        self._casualties_hint.configure(text=tr('{} warrior(s) recorded Out of Action').format(count))

    def _out_of_action_ids(self) -> list[str]:
        return [warrior_id for warrior_id, var in self._ooa_vars.items() if var.get()]

    def _record(self) -> None:
        index = max(0, self.scenario_box.current())
        scenario_id = self._scenario_ids[index] if self._scenario_ids else ""
        scenario_name = self._scenario_names.get(scenario_id, scenario_id)
        rating_text = self.rating_var.get().strip()
        try:
            opponent_rating = int(rating_text) if rating_text else None
        except ValueError:
            opponent_rating = None
        ok, message = self.controller.record_battle(
            scenario_id=scenario_id,
            scenario_name=scenario_name,
            opponent=self.opponent_var.get(),
            result=self.result_var.get(),
            xp_delta=max(0, int(self.xp_var.get())),
            casualties=len(self._out_of_action_ids()),
            opponent_rating=opponent_rating,
            notes=self.notes_text.get("1.0", "end-1c").strip(),
            out_of_action_ids=self._out_of_action_ids(),
        )
        if not ok:
            from tkinter import messagebox

            messagebox.showerror(tr('Cannot record battle'), message, parent=self)
            return

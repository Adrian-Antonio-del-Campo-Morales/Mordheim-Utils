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
        self._ooa_vars: dict[str, tuple[tk.Variable, int]] = {}
        # Partially entered answers survive navigating to another timeline
        # row: they persist on AppState.pending_battle_draft and clear when
        # the battle is recorded.
        self._draft = controller.state.pending_battle_draft

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
        self._build_manual_xp(results)
        self._build_casualties(results)
        self._casualties_hint = tk.Label(results, text="", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8))
        self._casualties_hint.pack(anchor="w", pady=(0, 8))
        self._build_notes(results)
        self._build_actions(body)
        self._update_hint()
        self._show_step(0)
        self._restore_draft()
        self._watch_draft()

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
        # Award rows are generated from the KB scenario plan (scenario_rewards);
        # objectives that remain prose-only in the KB stay manual entries.

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
        """Controls generated from the KB scenario award plan (structured data)."""
        outer = BorderedFrame(body, background=COLORS["panel_alt"], padding=1)
        outer.pack(fill="x", pady=(0, 10))
        panel = outer.body
        panel.configure(padx=12, pady=10)
        tk.Label(panel, text=tr('SCENARIO-SPECIFIC RESULTS'), bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        self._plan_host = tk.Frame(panel, bg=COLORS["panel_alt"])
        self._plan_host.pack(fill="x", pady=(5, 0))
        self.scenario_box.bind("<<ComboboxSelected>>", lambda _e: self._rebuild_plan_panel(), add=True)
        self._rebuild_plan_panel()

    def _rebuild_plan_panel(self) -> None:
        """List the scenario's award rows; prose-only rows become editable entries."""
        for child in self._plan_host.winfo_children():
            child.destroy()
        self._manual_award_vars = []
        rewards = self.controller.scenario_rewards()
        index = max(0, self.scenario_box.current())
        scenario_id = self._scenario_ids[index] if self._scenario_ids else ""
        rows = rewards.plan(scenario_id)
        if not rows:
            tk.Label(
                self._plan_host,
                text=tr('This scenario declares no structured awards.'),
                bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8), wraplength=540, justify="left",
            ).pack(anchor="w")
            return
        for plan_row in rows:
            line = tk.Frame(self._plan_host, bg=COLORS["panel_alt"])
            line.pack(fill="x", pady=1)
            trigger = plan_row.trigger or tr('manual')
            recipient = plan_row.recipient.replace("_", " ")
            tk.Label(
                line, text=f"{plan_row.label}  ·  {trigger}  ·  {recipient}",
                bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8),
            ).pack(side="left")
            if plan_row.manual:
                tk.Label(line, text=tr('XP'), bg=COLORS["panel_alt"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(side="right", padx=(0, 3))
                var = tk.IntVar(value=max(0, plan_row.amount))
                self._manual_award_vars.append({"award_id": plan_row.award_id, "label": plan_row.label, "var": var})
                ttk.Spinbox(line, from_=0, to=99, width=4, textvariable=var).pack(side="right")

    def _build_counters(self, body: tk.Frame) -> None:
        row = self._row(body, tr('ENEMY OUT OF ACTION'))
        self.enemy_ooa_var = tk.IntVar(value=0)
        ttk.Spinbox(row, from_=0, to=99, width=5, textvariable=self.enemy_ooa_var, command=self._recompute_awards).pack(side="left")
        tk.Label(row, text=tr('drives the per-enemy experience award'), bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(side="left", padx=(8, 0))

        self._awards_box = tk.Frame(body, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["border_soft"])
        self._awards_box.pack(fill="x", pady=(0, 8))
        self._xp_vars: dict[str, tk.IntVar] = {}
        inner = tk.Frame(self._awards_box, bg=COLORS["panel"], padx=10, pady=8)
        inner.pack(fill="x")
        tk.Label(inner, text=tr('PER-WARRIOR EXPERIENCE'), bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(
            inner,
            text=tr('Computed from the scenario award plan (survival, winning leader, per-enemy). Adjust any total before recording.'),
            bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7), wraplength=430, justify="left",
        ).pack(anchor="w", pady=(0, 5))
        self._awards_host = tk.Frame(inner, bg=COLORS["panel"])
        self._awards_host.pack(fill="x")
        self._recompute_awards()

    def _recompute_awards(self) -> None:
        """Rebuild the per-warrior XP editor from the scenario award plan."""
        rewards = self.controller.scenario_rewards()
        index = max(0, self.scenario_box.current())
        scenario_id = self._scenario_ids[index] if self._scenario_ids else ""
        rows = self.controller.state.campaign.warriors
        try:
            enemy = max(0, int(self.enemy_ooa_var.get()))
        except (TypeError, ValueError, tk.TclError):
            enemy = 0
        computed = rewards.compute_for(scenario_id, rows, result=self.result_var.get(), enemy_out_of_action=enemy)
        overrides = {wid: var.get() for wid, var in self._xp_vars.items()}
        for child in self._awards_host.winfo_children():
            child.destroy()
        self._xp_vars = {}
        if not rows:
            tk.Label(self._awards_host, text=tr('No warriors recorded.'), bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
            return
        if not rewards.plan(scenario_id):
            tk.Label(
                self._awards_host,
                text=tr('This scenario declares no structured awards; grant experience manually below or in post-battle.'),
                bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7), wraplength=430, justify="left",
            ).pack(anchor="w")
        for warrior in rows:
            row = tk.Frame(self._awards_host, bg=COLORS["panel"])
            row.pack(fill="x", pady=1)
            label = warrior.name + (f"  ·  ×{warrior.quantity}" if warrior.quantity > 1 else "")
            tk.Label(row, text=label, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 8)).pack(side="left")
            var = tk.IntVar(value=int(overrides.get(warrior.id, computed.get(warrior.id, 0))))
            self._xp_vars[warrior.id] = var
            ttk.Spinbox(row, from_=0, to=99, width=4, textvariable=var).pack(side="right")
            tk.Label(row, text=tr('XP'), bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(side="right", padx=(0, 3))

    def _build_manual_xp(self, body: tk.Frame) -> None:
        row = self._row(body, tr('EXPERIENCE ADJUSTMENT'))
        self.xp_var = tk.IntVar(value=1)
        ttk.Spinbox(row, from_=0, to=99, width=5, textvariable=self.xp_var).pack(side="left")
        tk.Label(row, text=tr('manual per-warrior value for scenarios without a structured award plan'), bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7), wraplength=400, justify="left").pack(side="left", padx=(8, 0))

    def _build_casualties(self, body: tk.Frame) -> None:
        """Checklist of warriors recorded Out of Action (drives Recovery)."""
        self._row(body, tr('OUT OF ACTION'))
        warriors = self.controller.state.campaign.warriors
        box = tk.Frame(body, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["border_soft"])
        box.pack(fill="x", pady=(0, 8))
        inner = tk.Frame(box, bg=COLORS["panel"], padx=10, pady=8)
        inner.pack(fill="x")
        for warrior in warriors:
            row = tk.Frame(inner, bg=COLORS["panel"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=warrior.name, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 8)).pack(side="left")
            if warrior.kind == "henchman" and warrior.quantity > 1:
                var = tk.IntVar(value=0)
                self._ooa_vars[warrior.id] = (var, warrior.quantity)
                tk.Label(row, text=tr('of {} models').format(warrior.quantity), bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(side="right", padx=(5, 0))
                ttk.Spinbox(row, from_=0, to=warrior.quantity, width=4, textvariable=var, command=self._update_hint).pack(side="right")
                var.trace_add("write", lambda *_args: self._update_hint())
            else:
                var = tk.BooleanVar(value=False)
                self._ooa_vars[warrior.id] = (var, 1)
                ttk.Checkbutton(row, text=tr('OUT OF ACTION'), variable=var, command=self._update_hint).pack(side="right")
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

    # ------------------------------------------------------------- draft state

    def _restore_draft(self) -> None:
        """Re-apply the persisted battle-entry draft to the form controls."""
        draft = self._draft
        if not draft:
            return
        if draft.get("scenario_id") in self._scenario_ids and self.scenario_box.current() < 0:
            index = self._scenario_ids.index(draft["scenario_id"])
            ordered = sorted(self._scenarios, key=lambda entry: (entry[2] != "1v1",))
            labels = [f"{name}  ·  {mode}" for _sid, name, _mode in ordered]
            self.scenario_box.set(labels[index])
        for variable, key in (
            (self.opponent_var, "opponent"),
            (self.rating_var, "opponent_rating"),
            (self.result_var, "result"),
            (self.notes_text, "notes"),
        ):
            value = draft.get(key)
            if value is None:
                continue
            if variable is self.notes_text:
                variable.delete("1.0", "end")
                variable.insert("1.0", str(value))
            else:
                variable.set(str(value))
        if draft.get("xp") is not None:
            try:
                self.xp_var.set(int(draft["xp"]))
            except (TypeError, ValueError):
                pass
        if draft.get("enemy_ooa") is not None:
            try:
                self.enemy_ooa_var.set(int(draft["enemy_ooa"]))
            except (TypeError, ValueError, tk.TclError):
                pass
        for warrior_id, value in (draft.get("xp_awards") or {}).items():
            var = self._xp_vars.get(warrior_id)
            if var is not None:
                try:
                    var.set(int(value))
                except (TypeError, ValueError, tk.TclError):
                    pass
        for warrior_id, (var, maximum) in self._ooa_vars.items():
            saved = draft.get("ooa", {}).get(warrior_id)
            if saved is None:
                continue
            try:
                var.set(max(0, min(maximum, int(saved))) if isinstance(var, tk.IntVar) else bool(int(saved)))
            except (TypeError, ValueError, tk.TclError):
                pass
        self._update_hint()

    def _watch_draft(self) -> None:
        """Persist every form change into the application-state draft."""
        self.scenario_box.bind("<<ComboboxSelected>>", lambda _e: (self._recompute_awards(), self._save_draft()), add=True)
        for variable in (self.opponent_var, self.rating_var, self.result_var):
            variable.trace_add("write", lambda *_a: (self._recompute_awards(), self._save_draft()))
        self.xp_var.trace_add("write", lambda *_a: self._save_draft())
        for var, _maximum in self._ooa_vars.values():
            var.trace_add("write", lambda *_a: self._save_draft())
        self.notes_text.bind("<<Modified>>", self._notes_modified)

    def _notes_modified(self, _event) -> None:
        self.notes_text.edit_modified(False)
        self._save_draft()

    def _save_draft(self) -> None:
        draft = {
            "battle_number": self.number,
            "scenario_id": self._scenario_ids[max(0, self.scenario_box.current())] if self.scenario_box.current() >= 0 else "",
            "opponent": self.opponent_var.get(),
            "opponent_rating": self.rating_var.get(),
            "result": self.result_var.get(),
            "xp": self.xp_var.get(),
            "notes": self.notes_text.get("1.0", "end-1c"),
            "ooa": {warrior_id: var.get() for warrior_id, (var, _maximum) in self._ooa_vars.items()},
            "enemy_ooa": self.enemy_ooa_var.get(),
            "xp_awards": {warrior_id: var.get() for warrior_id, var in self._xp_vars.items()},
        }
        self.controller.state.pending_battle_draft.clear()
        self.controller.state.pending_battle_draft.update(draft)

    def _out_of_action_ids(self) -> list[str]:
        result = []
        for warrior_id, (var, maximum) in self._ooa_vars.items():
            try:
                count = int(var.get())
            except (TypeError, ValueError, tk.TclError):
                count = 0
            result.extend([warrior_id] * max(0, min(maximum, count)))
        return result

    def _per_group_casualties(self) -> dict[str, int]:
        """Explicit Out-of-Action counts per warrior/group."""
        result: dict[str, int] = {}
        for warrior_id, (var, maximum) in self._ooa_vars.items():
            try:
                count = int(var.get())
            except (TypeError, ValueError, tk.TclError):
                count = 0
            count = max(0, min(maximum, count))
            if count:
                result[warrior_id] = result.get(warrior_id, 0) + count
        return result

    def _record(self) -> None:
        index = max(0, self.scenario_box.current())
        scenario_id = self._scenario_ids[index] if self._scenario_ids else ""
        scenario_name = self._scenario_names.get(scenario_id, scenario_id)
        rating_text = self.rating_var.get().strip()
        try:
            opponent_rating = int(rating_text) if rating_text else None
        except ValueError:
            opponent_rating = None
        plan = self.controller.scenario_rewards().plan(scenario_id)
        xp_awards = {
            warrior_id: max(0, int(var.get()))
            for warrior_id, var in self._xp_vars.items()
            if max(0, int(var.get())) > 0
        }
        if not plan and not xp_awards:
            base = max(0, int(self.xp_var.get()))
            xp_awards = {warrior.id: base for warrior in self.controller.state.campaign.warriors if base > 0}
        try:
            enemy_ooa = max(0, int(self.enemy_ooa_var.get()))
        except (TypeError, ValueError, tk.TclError):
            enemy_ooa = 0
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
            per_group_casualties=self._per_group_casualties(),
            xp_awards=xp_awards,
            scenario_results={
                "enemy_out_of_action": enemy_ooa,
                "scenario_id": scenario_id,
                "manual_awards": [
                    {"award_id": entry["award_id"], "label": entry["label"], "amount": max(0, int(entry["var"].get()))}
                    for entry in getattr(self, "_manual_award_vars", ())
                    if max(0, int(entry["var"].get())) > 0
                ],
            },
        )
        if not ok:
            from tkinter import messagebox

            messagebox.showerror(tr('Cannot record battle'), message, parent=self)
            return
        self.controller.state.pending_battle_draft.clear()

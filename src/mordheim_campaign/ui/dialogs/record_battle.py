from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from mordheim_campaign.ui.input_validation import IntegerVar, numeric_action, numeric_preview

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.ui.components import DiceResolutionCard, PostBattleSequence, ask_dice
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, ScrollableFrame
from mordheim_ui.i18n import tr, tr_message
from mordheim_ui.windowing import center_on_application


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
        self._enemy_ooa_vars: dict[str, tk.IntVar] = {}
        self._objective_vars: list[dict] = []
        self._additional_reward_rows: list[dict] = []
        self._extra_items: dict[str, tk.IntVar] = {}
        self._xp_unlocked = False
        self._xp_overrides: dict[str, int] = {}
        # Partially entered answers survive navigating to another timeline
        # row: they persist on AppState.pending_battle_draft and clear when
        # the battle is recorded.
        self._draft = controller.state.pending_battle_draft

        outer = BorderedFrame(self, background=COLORS["panel"], padding=1)
        outer.pack(fill="both", expand=True)
        body = outer.body
        body.configure(padx=20, pady=18, width=620, height=570)

        pending_checks = controller.pending_battle_start_checks()
        if pending_checks:
            self._build_prebattle_checks(body, pending_checks)
            return
        available, unavailable = controller.battle_availability()
        self._battle_warriors = available
        self._unavailable_warriors = [warrior for warrior, _reason, _temporary in unavailable]
        self._unavailable_reasons = {warrior.id: reason for warrior, reason, _temporary in unavailable}

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
        self._build_unavailable(results)
        self._build_manual_xp(results)
        self._build_casualties(results)
        self._casualties_hint = tk.Label(results, text="", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI Semibold", 8))
        self._casualties_hint.pack(anchor="w", pady=(0, 8))
        self._build_extra_rewards(results)
        self._build_notes(results)
        self._build_actions(body)
        self._update_hint()
        self._show_step(0)
        self._restore_draft()
        self._watch_draft()

    def _build_prebattle_checks(self, body: tk.Frame, pending_checks: list[tuple[object, dict]]) -> None:
        tk.Label(body, text=tr('BATTLE #{} · PRE-BATTLE CHECKS').format(self.number), bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 15)).pack(anchor="w")
        tk.Label(
            body,
            text=tr('Resolve lasting injuries before recording the battle. Failed warriors will be excluded automatically.'),
            bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9), wraplength=620, justify="left",
        ).pack(anchor="w", pady=(4, 12))
        for warrior, check in pending_checks:
            dice = check.get("dice") or {}
            count, sides = int(dice.get("count") or 1), int(dice.get("sides") or 6)
            DiceResolutionCard(
                body,
                title=f"{warrior.name} · {tr('Old Battle Wound')}",
                subtitle=tr('On a roll of 1, this warrior must miss the battle.'),
                notation=f"{count if count != 1 else ''}D{sides}", dice_count=count, dice_sides=sides,
                demo_dice=(3,) * count, combine="sum", outcome_actions=(),
                on_resolved=lambda values, w=warrior, c=check: self._store_battle_start_check(w, c, values),
            ).pack(fill="x", pady=(0, 8))

    def _store_battle_start_check(self, warrior, check: dict, dice: list[int]) -> tuple[str, str, str]:
        roll = sum(dice)
        ok, message = self.controller.perform_undoable(
            tr('Pre-battle injury check'), lambda: self.controller.resolve_battle_start_check(
                warrior.id, str(check.get("check_id") or ""), roll))
        if ok:
            self.after_idle(self.controller.notify)
        return (tr('Check resolved') if ok else tr('Invalid result'), message, "accent" if ok else "danger")

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
        opponents = sorted({option.name for option in self.controller.warband_options()}, key=str.casefold)
        ttk.Combobox(row, textvariable=self.opponent_var, values=opponents, width=31).pack(side="left")
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
        """Render automatic awards and player decisions as compact structured rows."""
        for child in self._plan_host.winfo_children():
            child.destroy()
        self._objective_vars = []
        self._additional_reward_rows = []
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
        for plan_row in rows:
            line = tk.Frame(self._plan_host, bg=COLORS["panel_alt"])
            line.pack(fill="x", pady=2)
            line.columnconfigure(0, weight=1)
            tk.Label(
                line, text=plan_row.label,
                bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8),
                wraplength=390, justify="left", anchor="w",
            ).grid(row=0, column=0, sticky="ew")
            if plan_row.manual:
                candidates = list(self._battle_warriors)
                if "hero" in plan_row.label.casefold() and "henchman" not in plan_row.label.casefold():
                    candidates = [warrior for warrior in candidates if warrior.kind == "hero"]
                amount_var = IntegerVar(value=max(0, plan_row.amount))
                if plan_row.selection in {"multiple", "distributed"}:
                    selections = {}
                    checklist = tk.Frame(line, bg=COLORS["panel_alt"])
                    checklist.grid(row=0, column=1, sticky="e", padx=(10, 0))
                    for warrior in candidates:
                        if plan_row.selection == "multiple":
                            selected = tk.BooleanVar(value=False)
                            selections[warrior.id] = selected
                            ttk.Checkbutton(
                                checklist, text=warrior.name, variable=selected,
                                command=lambda: (self._recompute_awards(), self._save_draft()),
                            ).pack(anchor="w")
                        else:
                            allocated = IntegerVar(value=0)
                            selections[warrior.id] = allocated
                            allocation = tk.Frame(checklist, bg=COLORS["panel_alt"])
                            allocation.pack(fill="x", anchor="e")
                            tk.Label(allocation, text=warrior.name, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8)).pack(side="left")
                            ttk.Spinbox(allocation, from_=0, to=99, width=4, textvariable=allocated, command=lambda: (self._recompute_awards(), self._save_draft())).pack(side="right", padx=(6, 0))
                    self._objective_vars.append({
                        "award_id": plan_row.award_id, "label": plan_row.label,
                        "amount": amount_var, "selections": selections,
                        "selection": plan_row.selection,
                    })
                else:
                    labels = [tr('Not achieved')] + [warrior.name for warrior in candidates]
                    var = tk.StringVar(value=labels[0])
                    self._objective_vars.append({
                        "award_id": plan_row.award_id, "label": plan_row.label,
                        "amount": amount_var, "var": var,
                        "hero_ids": [""] + [warrior.id for warrior in candidates], "labels": labels,
                    })
                    box = ttk.Combobox(line, state="readonly", values=labels, textvariable=var, width=24)
                    box.grid(row=0, column=1, sticky="e", padx=(10, 0))
                    box.bind("<<ComboboxSelected>>", lambda _e: (self._recompute_awards(), self._save_draft()), add=True)
                if plan_row.amount_dice:
                    ttk.Spinbox(line, from_=0, to=99, width=4, textvariable=amount_var, command=self._recompute_awards).grid(row=0, column=2, padx=(4, 0))
            else:
                tk.Label(
                    line, text=tr('Automatic'), bg=COLORS["panel_alt"], fg=COLORS["success"],
                    font=("Segoe UI Semibold", 7),
                ).grid(row=0, column=1, sticky="e", padx=(10, 0))
        self._build_additional_rewards(self._plan_host, scenario_id)
        self._sync_manual_xp_visibility(bool(rows))

    def _build_additional_rewards(self, body: tk.Frame, scenario_id: str) -> None:
        rewards = self.controller.scenario_rewards().additional(scenario_id)
        if not rewards:
            return
        tk.Frame(body, bg=COLORS["border_soft"], height=1).pack(fill="x", pady=(8, 7))
        tk.Label(body, text=tr('ADDITIONAL REWARDS'), bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        for reward in rewards:
            rule = str(reward.get("rule") or "")
            tk.Label(body, text=rule, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 7), wraplength=535, justify="left").pack(anchor="w", pady=(5, 2))
            if reward.get("kind") == "resource":
                variable = IntegerVar(value=0)
                self._additional_reward_rows.append({"spec": reward, "quantity": variable})
                line = tk.Frame(body, bg=COLORS["panel_alt"]); line.pack(fill="x")
                unit = tr('GC AWARDED') if reward.get("resource") == "gold_crowns" else tr('SHARDS AWARDED')
                tk.Label(line, text=unit, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI Semibold", 7)).pack(side="left")
                ttk.Spinbox(line, from_=0, to=9999, width=6, textvariable=variable, command=self._save_draft).pack(side="right")
            elif reward.get("kind") == "exploration":
                self._additional_reward_rows.append({"spec": reward})
                text = tr('+{} exploration die · reroll all dice').format(reward.get("extra_dice", 0))
                tk.Label(body, text=text, bg=COLORS["panel_alt"], fg=COLORS["success"], font=("Segoe UI Semibold", 7)).pack(anchor="w")
            else:
                for content in reward.get("contents") or ():
                    line = tk.Frame(body, bg=COLORS["panel_alt"]); line.pack(fill="x", pady=1)
                    line.columnconfigure(0, weight=1)
                    obtained = tk.BooleanVar(value=False)
                    quantity = IntegerVar(value=0)
                    status = tk.StringVar(value=tr('Not resolved'))
                    reward_row = {"spec": reward, "content": content, "obtained": obtained, "quantity": quantity, "status": status}
                    self._additional_reward_rows.append(reward_row)
                    tk.Label(line, text=f"{content.get('label')}  ·  {content.get('roll')}", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8), anchor="w").grid(row=0, column=0, sticky="ew")
                    tk.Label(line, textvariable=status, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 7)).grid(row=0, column=1, padx=(8, 4))
                    ttk.Button(line, text=tr('RESOLVE'), style="Mini.TButton", command=lambda r=reward_row: self._resolve_reward_roll(r)).grid(row=0, column=2)

    def _resolve_reward_roll(self, row: dict) -> None:
        content = row["content"]
        availability = content.get("availability") or {}
        available = True
        details = []
        if availability.get("dice"):
            dice = availability["dice"]
            values = self._roll_or_enter(int(dice.get("count") or 1), int(dice.get("sides") or 6), content.get("label"))
            if values is None:
                return
            total = sum(values) * int(dice.get("multiplier") or 1) + int(dice.get("modifier") or 0)
            details.append(str(total))
            if availability.get("target") is not None:
                available = total >= int(availability["target"])
            if content.get("when"):
                when = content["when"]
                available = int(when.get("min") or 0) <= total <= int(when.get("max") or total)
        if not available:
            row["obtained"].set(False); row["quantity"].set(0)
            row["status"].set(tr('Failed ({})').format(', '.join(details)))
            self._save_draft()
            return
        quantity = 1
        if content.get("quantity_dice"):
            dice = content["quantity_dice"]
            values = self._roll_or_enter(int(dice.get("count") or 1), int(dice.get("sides") or 6), content.get("label"))
            if values is None:
                return
            quantity = sum(values) * int(dice.get("multiplier") or 1) + int(dice.get("modifier") or 0)
            details.append(str(quantity))
        row["obtained"].set(True); row["quantity"].set(max(0, quantity))
        roll_text = f" · {tr('roll')}: {' → '.join(details)}" if details else ""
        row["status"].set(tr('Obtained: {}').format(quantity) + roll_text)
        self._save_draft()

    def _roll_or_enter(self, count: int, sides: int, title: str) -> list[int] | None:
        return ask_dice(self, title=str(title), dice_count=count, dice_sides=sides)

    def _build_extra_rewards(self, body: tk.Frame) -> None:
        """Optional campaign/house-rule rewards, independent of the scenario KB."""
        outer = BorderedFrame(body, background=COLORS["panel_alt"], padding=1)
        outer.pack(fill="x", pady=(0, 10))
        panel = outer.body; panel.configure(padx=12, pady=10)
        tk.Label(panel, text=tr('EXTRA REWARDS'), bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(panel, text=tr('Optional rewards granted by house rules or the campaign organiser.'), bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 7)).pack(anchor="w", pady=(1, 7))
        resources = tk.Frame(panel, bg=COLORS["panel_alt"]); resources.pack(fill="x")
        self._extra_gold_var = IntegerVar(value=0); self._extra_wyrdstone_var = IntegerVar(value=0)
        for column, (label, variable) in enumerate(((tr('GOLD CROWNS'), self._extra_gold_var), (tr('WYRDSTONE'), self._extra_wyrdstone_var))):
            tk.Label(resources, text=label, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).grid(row=0, column=column * 2, sticky="w", padx=(0 if column == 0 else 18, 5))
            ttk.Spinbox(resources, from_=0, to=9999, width=6, textvariable=variable, command=self._save_draft).grid(row=0, column=column * 2 + 1)
            variable.trace_add("write", lambda *_a: self._save_draft())

        options = self.controller.port.item_options()
        self._extra_item_ids = [item_id for item_id, _name in options]
        labels = [name for _item_id, name in options]
        picker = tk.Frame(panel, bg=COLORS["panel_alt"]); picker.pack(fill="x", pady=(8, 3))
        self._extra_item_box = ttk.Combobox(picker, state="readonly", values=labels, width=42)
        self._extra_item_box.pack(side="left", fill="x", expand=True)
        if labels: self._extra_item_box.current(0)
        self._extra_item_quantity = IntegerVar(value=1)
        ttk.Spinbox(picker, from_=1, to=99, width=4, textvariable=self._extra_item_quantity).pack(side="left", padx=5)
        ttk.Button(picker, text=tr('ADD'), style="Mini.TButton", command=self._add_extra_item).pack(side="left")
        self._extra_items_host = tk.Frame(panel, bg=COLORS["panel_alt"]); self._extra_items_host.pack(fill="x")

    def _add_extra_item(self) -> None:
        index = self._extra_item_box.current()
        if index < 0 or index >= len(self._extra_item_ids):
            return
        item_id = self._extra_item_ids[index]
        quantity = max(1, int(self._extra_item_quantity.get()))
        variable = self._extra_items.get(item_id)
        if variable is None:
            self._extra_items[item_id] = IntegerVar(value=quantity)
        else:
            variable.set(variable.get() + quantity)
        self._refresh_extra_items(); self._save_draft()

    def _refresh_extra_items(self) -> None:
        for child in self._extra_items_host.winfo_children(): child.destroy()
        for item_id, variable in self._extra_items.items():
            row = tk.Frame(self._extra_items_host, bg=COLORS["panel_alt"]); row.pack(fill="x", pady=1)
            tk.Label(row, text=self.controller.port.item_name(item_id) or item_id, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8)).pack(side="left")
            ttk.Button(row, text=tr('REMOVE'), style="Mini.TButton", command=lambda key=item_id: self._remove_extra_item(key)).pack(side="right", padx=(5, 0))
            ttk.Spinbox(row, from_=1, to=99, width=4, textvariable=variable, command=self._save_draft).pack(side="right")

    def _remove_extra_item(self, item_id: str) -> None:
        self._extra_items.pop(item_id, None); self._refresh_extra_items(); self._save_draft()

    def _build_counters(self, body: tk.Frame) -> None:
        self._awards_box = tk.Frame(body, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["border_soft"])
        self._awards_box.pack(fill="x", pady=(0, 8))
        self._xp_vars: dict[str, tk.IntVar] = {}
        inner = tk.Frame(self._awards_box, bg=COLORS["panel"], padx=10, pady=8)
        inner.pack(fill="x")
        heading = tk.Frame(inner, bg=COLORS["panel"])
        heading.pack(fill="x")
        tk.Label(heading, text=tr('PER-WARRIOR EXPERIENCE'), bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(side="left")
        self._xp_lock_button = ttk.Button(heading, style="Mini.TButton", command=self._toggle_xp_lock)
        self._xp_lock_button.pack(side="right")
        self._refresh_xp_lock_button()
        tk.Label(inner, text=tr('Automatic awards plus each warrior’s scenario actions.'), bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(anchor="w", pady=(0, 5))
        self._awards_host = tk.Frame(inner, bg=COLORS["panel"])
        self._awards_host.pack(fill="x")
        self._recompute_awards()

    @numeric_preview
    def _recompute_awards(self) -> None:
        """Rebuild the per-warrior XP editor from the scenario award plan."""
        rewards = self.controller.scenario_rewards()
        index = max(0, self.scenario_box.current())
        scenario_id = self._scenario_ids[index] if self._scenario_ids else ""
        rows = self._battle_warriors
        enemy_counts = {}
        for warrior_id, variable in self._enemy_ooa_vars.items():
            try:
                enemy_counts[warrior_id] = max(0, int(variable.get()))
            except (TypeError, ValueError, tk.TclError):
                return
        computed = rewards.compute_for(scenario_id, rows, result=self.result_var.get(), enemy_out_of_action=enemy_counts)
        for objective in self._objective_vars:
            if "selections" in objective:
                for warrior_id, variable in objective["selections"].items():
                    if objective["selection"] == "distributed":
                        award = max(0, int(variable.get()))
                    else:
                        award = max(0, int(objective["amount"].get())) if variable.get() else 0
                    if award:
                        computed[warrior_id] = computed.get(warrior_id, 0) + award
                continue
            try:
                selected = objective["hero_ids"][objective["labels"].index(objective["var"].get())]
            except (ValueError, IndexError):
                selected = ""
            if selected:
                computed[selected] = computed.get(selected, 0) + max(0, int(objective["amount"].get()))
        previous_enemy = enemy_counts
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
        per_enemy = any(row.trigger == "enemy_put_out_of_action" and not row.manual for row in rewards.plan(scenario_id))
        self._enemy_ooa_vars = {}
        for warrior in rows:
            row = tk.Frame(self._awards_host, bg=COLORS["panel"])
            row.pack(fill="x", pady=2)
            row.columnconfigure(0, weight=1)
            label = warrior.name + (f"  ·  ×{warrior.quantity}" if warrior.quantity > 1 else "")
            tk.Label(row, text=label, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 8), anchor="w").grid(row=0, column=0, sticky="ew")
            if per_enemy and warrior.kind == "hero":
                tk.Label(row, text=tr('ENEMY OOA'), bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).grid(row=0, column=1, padx=(8, 3))
                enemy_var = IntegerVar(value=previous_enemy.get(warrior.id, 0))
                self._enemy_ooa_vars[warrior.id] = enemy_var
                ttk.Spinbox(row, from_=0, to=99, width=4, textvariable=enemy_var, command=self._recompute_awards).grid(row=0, column=2)
                enemy_var.trace_add("write", lambda *_a: (self._recompute_awards(), self._save_draft()))
            value = self._xp_overrides.get(warrior.id, int(computed.get(warrior.id, 0)))
            var = IntegerVar(value=value)
            self._xp_vars[warrior.id] = var
            tk.Label(row, text=tr('XP'), bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).grid(row=0, column=3, padx=(12, 3))
            spin = ttk.Spinbox(row, from_=0, to=99, width=4, textvariable=var, state="normal" if self._xp_unlocked else "disabled")
            spin.grid(row=0, column=4)
            var.trace_add("write", lambda *_a, wid=warrior.id, value=var: self._set_xp_override(wid, value))

    def _set_xp_override(self, warrior_id: str, variable: tk.IntVar) -> None:
        if not self._xp_unlocked:
            return
        try:
            self._xp_overrides[warrior_id] = max(0, int(variable.get()))
        except (TypeError, ValueError, tk.TclError):
            return
        self._save_draft()

    def _toggle_xp_lock(self) -> None:
        self._xp_unlocked = not self._xp_unlocked
        if not self._xp_unlocked:
            self._xp_overrides.clear()
        self._refresh_xp_lock_button()
        self._recompute_awards()
        self._save_draft()

    def _refresh_xp_lock_button(self) -> None:
        if not hasattr(self, "_xp_lock_button"):
            return
        text = f"🔓 {tr('EDIT')}" if self._xp_unlocked else f"🔒 {tr('LOCKED')}"
        self._xp_lock_button.configure(text=text)

    def _build_manual_xp(self, body: tk.Frame) -> None:
        row = self._row(body, tr('EXPERIENCE ADJUSTMENT'))
        self._manual_xp_row = row
        self.xp_var = IntegerVar(value=1)
        ttk.Spinbox(row, from_=0, to=99, width=5, textvariable=self.xp_var).pack(side="left")
        tk.Label(row, text=tr('manual per-warrior value for scenarios without a structured award plan'), bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7), wraplength=400, justify="left").pack(side="left", padx=(8, 0))
        scenario_id = self._scenario_ids[max(0, self.scenario_box.current())] if self._scenario_ids else ""
        self._sync_manual_xp_visibility(bool(self.controller.scenario_rewards().plan(scenario_id)))

    def _sync_manual_xp_visibility(self, has_plan: bool) -> None:
        row = getattr(self, "_manual_xp_row", None)
        if row is None:
            return
        if has_plan:
            row.pack_forget()
        elif not row.winfo_manager():
            row.pack(fill="x", pady=(0, 8), before=self._awards_box)

    def _build_casualties(self, body: tk.Frame) -> None:
        """Checklist of warriors recorded Out of Action (drives Recovery)."""
        self._row(body, tr('OUT OF ACTION'))
        warriors = self._battle_warriors
        box = tk.Frame(body, bg=COLORS["panel"], highlightthickness=1, highlightbackground=COLORS["border_soft"])
        box.pack(fill="x", pady=(0, 8))
        inner = tk.Frame(box, bg=COLORS["panel"], padx=10, pady=8)
        inner.pack(fill="x")
        for warrior in warriors:
            row = tk.Frame(inner, bg=COLORS["panel"])
            row.pack(fill="x", pady=1)
            tk.Label(row, text=warrior.name, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 8)).pack(side="left")
            if warrior.kind == "henchman" and warrior.quantity > 1:
                var = IntegerVar(value=0)
                self._ooa_vars[warrior.id] = (var, warrior.quantity)
                tk.Label(row, text=tr('of {} models').format(warrior.quantity), bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(side="right", padx=(5, 0))
                ttk.Spinbox(row, from_=0, to=warrior.quantity, width=4, textvariable=var, command=self._update_hint).pack(side="right")
                var.trace_add("write", lambda *_args: self._update_hint())
            else:
                var = tk.BooleanVar(value=False)
                self._ooa_vars[warrior.id] = (var, 1)
                ttk.Checkbutton(row, text=tr('OUT OF ACTION'), variable=var, command=self._update_hint, style="Panel.TCheckbutton").pack(side="right")
        tk.Label(
            body,
            text=tr("Marked warriors roll on the serious-injury charts in Recovery (post-battle step 1). For Henchman groups, choose exactly how many members went Out of Action."),
            bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7), wraplength=430, justify="left",
        ).pack(anchor="w")

    def _build_unavailable(self, body: tk.Frame) -> None:
        if not self._unavailable_warriors:
            return
        self._row(body, tr('UNAVAILABLE'))
        box = tk.Frame(body, bg=COLORS["panel_alt"], padx=10, pady=7)
        box.pack(fill="x", pady=(0, 8))
        for warrior in self._unavailable_warriors:
            remaining = warrior.games_to_miss
            reason = self._unavailable_reasons.get(warrior.id) or warrior.absence_reason or tr('Injury')
            text = tr('{} · did not participate · {} · {} battle(s) remaining before this battle').format(
                warrior.name, reason, remaining,
            )
            tk.Label(box, text=text, bg=COLORS["panel_alt"], fg=COLORS["danger"], font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=1)

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
            icons=("campaign_battle_add_battle", "campaign_battle_current"),
        ).pack(fill="x")
        if step == 0:
            self.back_button.pack_forget()
            self.record_button.pack_forget()
            self.next_button.pack(side="right")
        else:
            self.next_button.pack_forget()
            self.back_button.pack(side="left")
            self.record_button.pack(side="right")

    @numeric_preview
    def _update_hint(self) -> None:
        count = len(self._out_of_action_ids())
        self._casualties_hint.configure(text=tr('{} warrior(s) recorded Out of Action').format(count))

    # ------------------------------------------------------------- draft state

    def _restore_draft(self) -> None:
        """Re-apply the persisted battle-entry draft to the form controls."""
        draft = self._draft
        if not draft:
            return
        self._xp_unlocked = bool(draft.get("xp_manual_unlocked", False))
        self._xp_overrides = {
            warrior_id: max(0, int(value))
            for warrior_id, value in (draft.get("xp_overrides") or {}).items()
        }
        self._refresh_xp_lock_button()
        if draft.get("scenario_id") in self._scenario_ids:
            index = self._scenario_ids.index(draft["scenario_id"])
            self.scenario_box.current(index)
            self._rebuild_plan_panel()
            self._recompute_awards()
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
        for warrior_id, value in (draft.get("enemy_ooa_by_warrior") or {}).items():
            variable = self._enemy_ooa_vars.get(warrior_id)
            if variable is not None:
                variable.set(max(0, int(value)))
        for objective in self._objective_vars:
            saved_objective = (draft.get("scenario_objectives") or {}).get(objective["award_id"], {})
            if "selections" in objective:
                saved_recipients = saved_objective.get("recipients") or {}
                for warrior_id, variable in objective["selections"].items():
                    if objective["selection"] == "distributed":
                        variable.set(max(0, int(saved_recipients.get(warrior_id) or 0)))
                    else:
                        variable.set(warrior_id in saved_recipients)
                if saved_objective.get("amount") is not None:
                    objective["amount"].set(max(0, int(saved_objective["amount"])))
                continue
            selected_id = str(saved_objective.get("recipient") or "")
            if selected_id in objective["hero_ids"]:
                objective["var"].set(objective["labels"][objective["hero_ids"].index(selected_id)])
            if saved_objective.get("amount") is not None:
                objective["amount"].set(max(0, int(saved_objective["amount"])))
        saved_rewards = draft.get("additional_rewards") or {}
        for row in self._additional_reward_rows:
            key = str((row.get("content") or row["spec"]).get("id") or "")
            saved = saved_rewards.get(key) or {}
            if row.get("quantity") is not None and "quantity" in saved:
                row["quantity"].set(saved["quantity"])
            if row.get("obtained") is not None and "obtained" in saved:
                row["obtained"].set(saved["obtained"])
                if row.get("status") is not None:
                    row["status"].set(tr('Obtained: {}').format(saved.get("quantity", 0)) if saved["obtained"] else tr('Not obtained'))
        house = draft.get("extra_rewards") or {}
        self._extra_gold_var.set(max(0, int(house.get("gold_crowns") or 0)))
        self._extra_wyrdstone_var.set(max(0, int(house.get("wyrdstone_fragments") or 0)))
        self._extra_items.clear()
        for item_id, quantity in (house.get("items") or {}).items():
            if self.controller.port.item_name(item_id) and int(quantity) > 0:
                self._extra_items[item_id] = IntegerVar(value=int(quantity))
        self._refresh_extra_items()
        self._recompute_awards()
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

    @numeric_preview
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
            "enemy_ooa_by_warrior": {warrior_id: var.get() for warrior_id, var in self._enemy_ooa_vars.items()},
            "xp_awards": {warrior_id: var.get() for warrior_id, var in self._xp_vars.items()},
            "xp_manual_unlocked": self._xp_unlocked,
            "xp_overrides": dict(self._xp_overrides),
            "scenario_objectives": self._scenario_objective_results(),
            "additional_rewards": self._additional_rewards_draft(),
            "extra_rewards": self._extra_rewards_draft(),
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

    def _scenario_objective_results(self) -> dict[str, dict]:
        result = {}
        for objective in self._objective_vars:
            if "selections" in objective:
                if objective["selection"] == "distributed":
                    recipients = {
                        warrior_id: max(0, int(variable.get()))
                        for warrior_id, variable in objective["selections"].items()
                        if max(0, int(variable.get())) > 0
                    }
                else:
                    recipients = {
                        warrior_id: max(0, int(objective["amount"].get()))
                        for warrior_id, variable in objective["selections"].items()
                        if variable.get()
                    }
                result[objective["award_id"]] = {
                    "recipients": recipients,
                    "amount": max(0, int(objective["amount"].get())),
                }
                continue
            try:
                index = objective["labels"].index(objective["var"].get())
                result[objective["award_id"]] = {
                    "recipient": objective["hero_ids"][index],
                    "amount": max(0, int(objective["amount"].get())),
                }
            except (ValueError, IndexError):
                result[objective["award_id"]] = {"recipient": "", "amount": 0}
        return result

    def _additional_rewards_draft(self) -> dict[str, dict]:
        result = {}
        for row in self._additional_reward_rows:
            key = str((row.get("content") or row["spec"]).get("id") or "")
            result[key] = {
                "quantity": int(row["quantity"].get()) if row.get("quantity") is not None else 0,
                "obtained": bool(row["obtained"].get()) if row.get("obtained") is not None else True,
            }
        return result

    def _additional_rewards_result(self) -> list[dict]:
        result = []
        for row in self._additional_reward_rows:
            spec = row["spec"]
            if spec.get("kind") == "exploration":
                result.append({"kind": "exploration", "extra_dice": int(spec.get("extra_dice") or 0), "reroll_all": bool(spec.get("reroll_all"))})
                continue
            obtained = bool(row["obtained"].get()) if row.get("obtained") is not None else True
            quantity = max(0, int(row["quantity"].get())) if row.get("quantity") is not None else 0
            if not obtained or quantity <= 0:
                continue
            grant = (row.get("content") or {}).get("grant") or {}
            if spec.get("kind") == "resource":
                result.append({"kind": "resource", "resource": spec["resource"], "quantity": quantity})
            elif grant.get("kind") == "resource":
                result.append({"kind": "resource", "resource": grant["resource"], "quantity": quantity})
            elif grant.get("kind") == "item":
                result.append({"kind": "item", "item_id": grant["item_id"], "label": (row.get("content") or {}).get("label"), "quantity": quantity})
            else:
                result.append({
                    "kind": "special", "special_id": grant.get("special_id"),
                    "label": (row.get("content") or {}).get("label"), "quantity": quantity,
                    "rule": spec.get("rule") or (row.get("content") or {}).get("label"),
                })
        return result

    def _extra_rewards_draft(self) -> dict:
        return {
            "gold_crowns": max(0, int(self._extra_gold_var.get())),
            "wyrdstone_fragments": max(0, int(self._extra_wyrdstone_var.get())),
            "items": {item_id: max(0, int(variable.get())) for item_id, variable in self._extra_items.items()},
        }

    def _extra_rewards_result(self) -> list[dict]:
        draft = self._extra_rewards_draft()
        result = []
        for resource in ("gold_crowns", "wyrdstone_fragments"):
            if draft[resource]:
                result.append({"kind": "resource", "resource": resource, "quantity": draft[resource], "source": "house_rule"})
        result.extend(
            {"kind": "item", "item_id": item_id, "label": self.controller.port.item_name(item_id), "quantity": quantity, "source": "house_rule"}
            for item_id, quantity in draft["items"].items() if quantity > 0
        )
        return result

    @numeric_action
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
            xp_awards = {warrior.id: base for warrior in self._battle_warriors if base > 0}
        enemy_ooa = {
            warrior_id: max(0, int(variable.get()))
            for warrior_id, variable in self._enemy_ooa_vars.items()
        }
        objectives = self._scenario_objective_results()
        official_rewards = self._additional_rewards_result()
        extra_rewards = self._extra_rewards_result()
        ok, message = self.controller.perform_undoable(tr('Record battle'), lambda: self.controller.record_battle(
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
                "scenario_id": scenario_id,
                "enemy_out_of_action_by_warrior": enemy_ooa,
                "objectives": objectives,
                "additional_rewards": official_rewards + extra_rewards,
                "extra_rewards": extra_rewards,
            },
        ))
        if not ok:
            from mordheim_ui import themed_dialogs as messagebox

            messagebox.showerror(tr('Cannot record battle'), tr_message(message), parent=self)
            return
        self.controller.state.pending_battle_draft.clear()

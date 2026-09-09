from __future__ import annotations

import tkinter as tk

from mordheim_campaign.application.controller import AppController
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, SegmentedTabs, SummaryStrip
from mordheim_ui.i18n import tr


class BattleMoment(tk.Frame):
    """One table battle: facts only, separated from post-battle consequences."""

    def __init__(self, master: tk.Misc, controller: AppController, number: int, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        battle = controller.state.campaign.battle(number)
        self.columnconfigure(0, weight=1); self.rowconfigure(3, weight=1)

        top = tk.Frame(self, bg=COLORS["bg"]); top.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        tk.Label(top, text=tr('BATTLE #{}').format(battle.number), bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 16)).pack(side="left")
        result_color = COLORS["success"] if battle.result.lower() == "victory" else COLORS["danger"]
        tk.Label(top, text=battle.result.upper(), bg=COLORS["bg"], fg=result_color, font=("Segoe UI Semibold", 9)).pack(side="left", padx=10)
        tk.Label(self, text=tr('{} · vs. {} · {}').format(battle.scenario, battle.opponent, battle.date), bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 9)).grid(row=1, column=0, sticky="w", pady=(0, 8))

        nav = tk.Frame(self, bg=COLORS["bg"]); nav.grid(row=2, column=0, sticky="ew", pady=(0, 8))
        SegmentedTabs(nav, (("overview", tr('OVERVIEW')), ("participants", tr('PARTICIPANTS')), ("notes", tr('NOTES'))), controller.state.battle_section, controller.set_battle_section).pack(side="left")

        section = controller.state.battle_section
        content = self._participants(battle) if section == "participants" else self._notes(battle) if section == "notes" else self._overview(battle)
        content.grid(row=3, column=0, sticky="nsew")

    def _overview(self, battle) -> tk.Frame:
        frame = tk.Frame(self, bg=COLORS["bg"]); frame.columnconfigure(0, weight=1)
        SummaryStrip(frame, [(tr('Warband rating'), str(battle.rating_before)), (tr('Opponent rating'), str(battle.opponent_rating or "—")), (tr('Models deployed'), str(battle.models_before)), (tr('Result'), battle.result)]).pack(fill="x", pady=(0, 10))
        self._summary_card(
            frame, tr('BATTLE'),
            tr('{} faced {} in {} and recorded a {}.').format(
                self.controller.state.campaign.warband_name, battle.opponent, battle.scenario, battle.result.lower(),
            ),
            [
                tr('{} models were deployed with a warband rating of {}.').format(battle.models_before, battle.rating_before),
                tr('The opposing warband rating was {}.').format(battle.opponent_rating or tr('not recorded')),
            ],
        )
        roster = {warrior.id: warrior.name for warrior in self.controller.state.campaign.warriors}
        recorded = list(battle.out_of_action_ids or ())
        names = [roster.get(warrior_id, tr('Warrior no longer in the current roster')) for warrior_id in recorded]
        casualty_lines = [tr('{} Out of Action result(s) were recorded.').format(battle.casualties)]
        if names:
            casualty_lines.append(tr('Affected: {}.').format(' · '.join(names)))
        elif battle.casualties:
            casualty_lines.append(tr('The individual warriors were not recorded for this battle.'))
        self._summary_card(
            frame, tr('CASUALTIES'),
            tr('These are the facts recorded at the end of the battle; lasting consequences belong to Post-Battle.'),
            casualty_lines,
        )
        self._summary_card(
            frame, tr('RECORDED CONSEQUENCES'),
            tr('The battle record handed the following totals to its Post-Battle sequence.'),
            [
                tr('{} experience award').format(f"+{battle.xp_delta}"),
                tr('{} wyrdstone shard(s) recorded').format(battle.wyrdstone),
                tr('{} advance(s) recorded').format(battle.advances),
                tr('Roster size: {} → {} models').format(battle.models_before, battle.models_after),
                tr('Warband rating: {} → {}').format(battle.rating_before, battle.rating_after),
            ],
        )
        if battle.scenario_results:
            lines = self._scenario_result_lines(battle)
            self._summary_card(
                frame, tr('SCENARIO OBJECTIVES'),
                tr('Structured scenario answers recorded with this battle.'),
                lines,
            )
        return frame

    def _scenario_result_lines(self, battle) -> list[str]:
        names = {str(row.get("id")): str(row.get("name")) for row in battle.participants}
        results = battle.scenario_results or {}
        lines = []
        for warrior_id, count in (results.get("enemy_out_of_action_by_warrior") or {}).items():
            if int(count or 0):
                lines.append(tr('{} put {} enemy model(s) Out of Action.').format(names.get(warrior_id, warrior_id), count))
        for objective in (results.get("objectives") or {}).values():
            recipient = str((objective or {}).get("recipient") or "")
            amount = int((objective or {}).get("amount") or 0)
            if recipient and amount:
                lines.append(tr('{} received +{} XP for a scenario objective.').format(names.get(recipient, recipient), amount))
        for reward in results.get("additional_rewards") or ():
            quantity = int(reward.get("quantity") or 0)
            if reward.get("kind") == "exploration":
                lines.append(tr('Scenario exploration rule applied.'))
            elif reward.get("resource") == "gold_crowns":
                lines.append(tr('{} gc awarded.').format(quantity))
            elif reward.get("resource") == "wyrdstone_fragments":
                lines.append(tr('{} wyrdstone shard(s) awarded.').format(quantity))
            elif reward.get("kind") in {"item", "special"}:
                lines.append(tr('{} × {} added to the stash.').format(quantity, reward.get("label") or reward.get("item_id") or reward.get("special_id")))
        return lines or [tr('No additional reward was recorded.')]

    def _summary_card(self, parent, title: str, intro: str, lines: list[str]) -> None:
        box = BorderedFrame(parent, background=COLORS["panel"], padding=1)
        box.pack(fill="x", pady=(0, 7))
        body = box.body
        body.configure(padx=14, pady=11)
        tk.Label(body, text=title, bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(body, text=intro, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8), wraplength=850, justify="left").pack(anchor="w", pady=(4, 5))
        for line in lines:
            tk.Label(body, text=f"• {line}", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 8), wraplength=830, justify="left").pack(anchor="w", pady=1)

    def _participants(self, battle) -> BorderedFrame:
        box = BorderedFrame(self, background=COLORS["panel"], padding=1); body = box.body; body.configure(padx=18, pady=16)
        tk.Label(body, text=tr('PARTICIPANTS'), bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 8))
        tk.Label(
            body,
            text=tr('{} models deployed · {} Out of Action. Which warriors went Out of Action is resolved in Recovery (post-battle step 1).').format(battle.models_before, battle.casualties),
            bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8), wraplength=760, justify="left",
        ).pack(anchor="w", pady=(0, 8))
        for warrior in self._participant_rows(battle):
            row = tk.Frame(body, bg=COLORS["panel"], pady=5); row.pack(fill="x")
            label = warrior["name"] + (f"  ·  ×{warrior['quantity']}" if warrior["quantity"] > 1 else "")
            tk.Label(row, text=label, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(side="left")
            status = tr('Participated')
            tone = COLORS["muted"]
            if warrior["ooa"]:
                status = tr('Out of Action')
                tone = COLORS["danger"]
            elif warrior["condition"]:
                status = warrior["condition"]
                tone = COLORS["danger"]
            tk.Label(row, text=status, bg=COLORS["panel"], fg=tone, font=("Segoe UI", 8)).pack(side="right")
        for warrior in battle.absentees:
            row = tk.Frame(body, bg=COLORS["panel"], pady=5); row.pack(fill="x")
            label = str(warrior.get("name") or warrior.get("id"))
            if int(warrior.get("quantity") or 1) > 1:
                label += f"  ·  ×{int(warrior['quantity'])}"
            tk.Label(row, text=label, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9)).pack(side="left")
            reason = str(warrior.get("reason") or tr('Injury'))
            tk.Label(row, text=tr('Did not participate · {}').format(reason), bg=COLORS["panel"], fg=COLORS["danger"], font=("Segoe UI", 8)).pack(side="right")
        return box

    def _participant_rows(self, battle) -> list[dict]:
        """Battle-time participant snapshot, falling back to the live roster."""
        if battle.participants:
            ooa_counts = battle.per_group_casualties or {}
            rows = [
                {
                    "name": str(row.get("name") or row.get("id")),
                    "quantity": int(row.get("quantity") or 1),
                    "condition": str(row.get("condition") or ""),
                    "ooa": ooa_counts.get(str(row.get("id")), 0) > 0 or str(row.get("id")) in (battle.out_of_action_ids or []),
                }
                for row in battle.participants
            ]
            if ooa_counts or battle.out_of_action_ids is not None:
                return rows
            return rows
        ooa = set(battle.out_of_action_ids or ())
        return [
            {"name": warrior.name, "quantity": warrior.quantity, "condition": warrior.condition or "", "ooa": warrior.id in ooa}
            for warrior in self.controller.state.campaign.warriors
        ]

    def _notes(self, battle) -> BorderedFrame:
        box = BorderedFrame(self, background=COLORS["panel"], padding=1); body = box.body; body.configure(padx=18, pady=16)
        tk.Label(body, text=tr('BATTLE NOTES'), bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        tk.Label(body, text=battle.notes or tr('No notes were recorded for this battle.'), bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9), wraplength=820, justify="left").pack(anchor="w", pady=(10, 0))
        return box

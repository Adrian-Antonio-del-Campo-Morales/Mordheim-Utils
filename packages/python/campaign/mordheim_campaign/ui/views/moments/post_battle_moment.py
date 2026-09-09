from __future__ import annotations

from dataclasses import replace
import tkinter as tk
from tkinter import ttk

from mordheim_ui import themed_dialogs as messagebox
from mordheim_ui import themed_dialogs as simpledialog

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.domain.models import POST_BATTLE_GROUPS, POST_BATTLE_STEPS
from mordheim_campaign.ui.components import DiceResolutionCard, PostBattleSequence, ask_dice
from mordheim_campaign.ui.panels import InventoryWorkspace
from mordheim_campaign.ui.views.moments.initial_warband_draft import DraftWarriorCard
from mordheim_ui.i18n import tr, tr_message
from mordheim_ui.theme import COLORS
from mordheim_ui.windowing import center_on_application
from mordheim_ui.widgets import BorderedFrame, ExperienceTrack, ScrollableFrame, SegmentedTabs, SummaryStrip


def _injury_card(dice: list[int], resolver, *, hero: bool) -> tuple[str, str, str]:
    """Live KB resolution for an injury card's roll."""
    outcome = (resolver.resolve_hero_serious_injury(10 * dice[0] + dice[1]) if hero
               else resolver.resolve_henchman_serious_injury(dice[0]))
    detail = _injury_detail(outcome)
    tone = "danger" if outcome.result in ("Dead", "Removed", "Multiple Injuries") else "accent"
    return tr(outcome.result), detail, tone


def _injury_detail(outcome) -> str:
    parts = [tr_message(part) for part in outcome.effects]
    if outcome.note:
        parts.append(tr_message(outcome.note))
    if outcome.follow_up:
        parts.append(tr_message(outcome.follow_up))
    return "  •  ".join(parts) or tr('No lasting effect.')


def _injury_history(outcome, roll: int) -> str:
    return tr("{} ({}) — {}").format(tr(outcome.result), roll, _injury_detail(outcome))


def _injury_store(dice: list[int], resolver, *, hero: bool, holder: dict) -> tuple[str, str, str]:
    holder["dice"] = list(dice)
    return _injury_card(dice, resolver, hero=hero)


def _exploration_card(dice: list[int], resolver) -> tuple[str, str, str]:
    """Live KB resolution of an exploration roll."""
    resolved = resolver.resolve_exploration(tuple(dice))
    detail = tr('Total {} → {} wyrdstone shard(s)').format(resolved.total, resolved.shards)
    if resolved.matching_dice_note:
        detail += f" · {tr_message(resolved.matching_dice_note)}"
    return tr('Exploration resolved · {} shard(s)').format(resolved.shards), detail, "accent"


def _exploration_store(dice: list[int], resolver, holder: dict) -> tuple[str, str, str]:
    holder["dice"] = list(dice)
    return _exploration_card(dice, resolver)


def _rarity_card(dice: list[int], resolver, item_id: str, name: str, holder: dict) -> tuple[str, str, str]:
    """Live KB rarity-test resolution for a rare-item search."""
    search = resolver.resolve_rarity_search(item_id, sum(dice), modifiers=int(holder.get("modifiers") or 0))
    holder["dice"] = list(dice)
    holder["success"] = search.success
    title = "Available" if search.success else tr('Not found')
    tone = "success" if search.success else "neutral"
    return title, f"{name}: {tr_message(search.note)}", tone


class PostBattleMoment(tk.Frame):
    """Resolve one battle-to-state transition as eight sequential user actions.

    The Battle itself remains a separate timeline node. The UI condenses source
    steps 6 and 7 into one Searches action and derives warband rating
    automatically, so the player sees four balanced chapters of two actions.
    Final Review is an application confirmation, not a ninth rules step.

    Every step now reads the live campaign and applies its outcome through
    :class:`PostBattleEngine`; COMMIT STATE appends the next immutable State.
    The one remaining display-only area is the per-warrior advancement editor
    (skills/characteristics), which arrives with the equipment/skill work.
    """

    def __init__(self, master: tk.Misc, controller: AppController, number: int, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        self.number = number
        self._scroll: ScrollableFrame | None = None
        self._scroll_pos = 0.0
        self._scroll_y = 0.0
        self._status_text = ""
        self._sell_var: tk.IntVar | None = None
        self._search_assignments: dict[str, tk.StringVar] = {}
        self._recruitment_tab = "hero"
        post = controller.state.campaign.post_battle(number)
        # Step-local working data (unresolved dice, form values) live in the
        # persisted PostBattleVM, so navigating away or a save/load cannot
        # discard them. The holders below are views onto that state.
        state = post.step_state
        self._pending_injury_rolls = state.setdefault("injuries", {})
        self._pending_exploration = state.setdefault("exploration", {})
        self._pending_veterans = state.setdefault("veterans", {})
        self._sell_state = state.setdefault("sell", {})
        self._post = post
        if post.complete:
            self._build_completed(post)
        else:
            self._build_pending(post)

    # ------------------------------------------------------------- scaffolding

    def _rebuild(self) -> None:
        """Rebuilds the current step in place, preserving scroll position."""
        if self._scroll is not None:
            self._scroll_pos = self._scroll.canvas.yview()[0]
            self._scroll_y = max(0.0, float(self._scroll.canvas.canvasy(0)))
        post = self.controller.state.campaign.post_battle(self.number)
        for child in self.winfo_children():
            child.destroy()
        if post.complete:
            self._build_completed(post)
        else:
            self._build_pending(post)
        if self._scroll is not None:
            scroll = self._scroll
            offset = self._scroll_y

            def restore_scroll() -> None:
                scroll.canvas.update_idletasks()
                bounds = scroll.canvas.bbox("all")
                if bounds is None:
                    return
                content_height = max(1, bounds[3] - bounds[1])
                scroll.canvas.yview_moveto(min(1.0, offset / content_height))

            # Scrollregion is updated by the inner frame's <Configure> event;
            # wait one additional idle cycle before restoring the viewport.
            scroll.canvas.after_idle(lambda: scroll.canvas.after_idle(restore_scroll))

    def _run(self, action) -> None:
        """Runs one engine action; reports and rebuilds on success."""
        ok, message = self.controller.perform_undoable("", action)
        self._status_text = ("✓ " if ok else "⚠ ") + message
        if ok:
            self._rebuild()

    def _engine(self):
        return self.controller.post_battle_engine()

    def _status_line(self, parent) -> None:
        if not self._status_text:
            return
        tone = COLORS["success"] if self._status_text.startswith("✓") else COLORS["danger"]
        tk.Label(
            parent, text=self._status_text, bg=COLORS["panel"], fg=tone,
            font=("Segoe UI Semibold", 8), wraplength=980, justify="left",
        ).pack(anchor="w", pady=(0, 9))

    def _build_completed(self, post) -> None:
        battle = self.controller.state.campaign.battle(post.battle_number)
        campaign = self.controller.state.campaign
        tk.Label(self, text=tr('POST-BATTLE #{}').format(post.battle_number), bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 16)).pack(anchor="w")
        tk.Label(
            self,
            text=tr('Complete · transformed State #{} into State #{}').format(post.battle_number - 1, post.battle_number),
            bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(3, 10))
        SummaryStrip(
            self,
            [
                (tr('Experience'), f"+{battle.xp_delta}"),
                (tr('Casualties'), str(battle.casualties)),
                (tr('Advances'), str(battle.advances)),
                ("Wyrdstone", f"+{battle.wyrdstone}"),
                (tr('Gold'), f"{battle.gold_delta:+d} gc"),
                (tr('Rating'), f"{battle.rating_before} → {battle.rating_after}"),
            ],
        ).pack(fill="x", pady=(0, 10))

        box = BorderedFrame(self, background=COLORS["panel"], padding=1)
        box.pack(fill="both", expand=True)
        scroll = ScrollableFrame(box.body, background=COLORS["panel"])
        scroll.pack(fill="both", expand=True)
        body = scroll.inner
        body.configure(padx=14, pady=12)

        affected = len(battle.out_of_action_ids or ())
        advances = [str(row.get("applied_label") or tr('Unresolved advance')) for row in post.pending_advances]
        injury_lines = [
            str(result)
            for holder in (post.step_state.get("injuries") or {}).values()
            for result in holder.get("history") or ()
        ]
        exploration = post.step_state.get("exploration") or {}
        exploration_lines = []
        if exploration.get("dice"):
            exploration_lines.append(tr('Dice: {}').format(' · '.join(map(str, exploration["dice"]))))
        exploration_lines.extend(
            str(entry.get("message") or "") for entry in post.event_log
            if int(entry.get("step") or -1) == 2 and entry.get("message")
        )
        veterans = post.step_state.get("veterans") or {}
        veteran_lines = ([tr('Dice: {}').format(' · '.join(map(str, veterans["dice"]))) ]
                         if veterans.get("dice") else [])
        search_lines = []
        for search in post.searches.values():
            dice = search.get("dice") or []
            search_lines.append(
                f"{search.get('hero_name') or search.get('hero_id')}: "
                f"{search.get('label') or search.get('target_id')}"
                + (f" · {tr('Dice')}: {' · '.join(map(str, dice))}" if dice else "")
            )
        recruitment_lines = [
            str(entry.get("message") or "") for entry in post.event_log
            if int(entry.get("step") or -1) == 6 and entry.get("message")
        ]
        equipment_lines = [
            str(entry.get("message") or "") for entry in post.event_log
            if int(entry.get("step") or -1) == 7 and entry.get("message")
        ]
        self._history_step(body, "01", tr('INJURIES'), tr('{} warrior result(s) were marked Out of Action.').format(affected or battle.casualties), [
            tr('Serious-injury rolls were completed before the new roster state was created.'),
            *(injury_lines or [tr('No detailed injury rolls were recorded.')]),
        ])
        self._history_step(body, "02", tr('EXPERIENCE'), tr('The recorded battle award was +{} XP.').format(battle.xp_delta),
                           advances or [tr('No advances were recorded in this sequence.')])
        self._history_step(body, "03", tr('EXPLORATION'), tr('{} wyrdstone shard(s) were added by exploration.').format(post.wyrdstone_delta),
                           exploration_lines or [tr('No detailed exploration result was recorded.')])
        sale = tr('{} shard(s) were sold.').format(post.wyrdstone_sold) if post.sale_resolved else tr('No wyrdstone sale was recorded.')
        self._history_step(body, "04", tr('SELL WYRDSTONE'), sale, [tr('Sale income is included in the final treasury change.')])
        self._history_step(body, "05", tr('VETERAN EXPERIENCE'), tr('{} Veteran XP remained after recruitment.').format(post.veteran_pool),
                           veteran_lines or [tr('No veteran roll was recorded.')])
        self._history_step(body, "06", tr('RARE ITEMS & DRAMATIS'), tr('Searches assigned during this sequence were completed.'),
                           search_lines or [tr('No searches were recorded.')])
        self._history_step(body, "07", tr('RECRUITMENT'), tr('The final roster contains {} models.').format(battle.models_after),
                           recruitment_lines or [tr('No recruitment changes were recorded.')])
        self._history_step(body, "08", tr('EQUIPMENT'), tr('Purchases, sales and assignments produced the final inventory.'),
                           equipment_lines or [tr('No equipment transactions were recorded.')])
        try:
            before = campaign.state(post.battle_number - 1)
            after = campaign.state(post.battle_number)
        except StopIteration:
            before = after = None
        if before is not None and after is not None:
            self._history_step(body, "✓", tr('FINAL STATE'), tr('The sequence created State #{}.').format(after.number), [
                tr('Models: {} → {}').format(before.models, after.models),
                tr('Treasury: {} → {} gc').format(before.gold, after.gold),
                tr('Wyrdstone: {} → {}').format(before.wyrdstone, after.wyrdstone),
                tr('Rating: {} → {}').format(before.rating, after.rating),
            ])
        if post.event_log:
            for index, entry in enumerate(post.event_log):
                step = int(entry.get("step") or 0)
                title = tr(POST_BATTLE_STEPS[step]) if 0 <= step < len(POST_BATTLE_STEPS) else f"#{step}"
                self._history_step(
                    body, f"{index + 1:02d}", title, str(entry.get("message") or ""),
                    [f"{key}: {value}" for key, value in (entry.get("ids") or {}).items()],
                )
        else:
            self._history_step(body, "?", tr('EVENT LOG'), tr('This sequence was completed before the event log existed; aggregate totals above summarise it.'), [])

    def _history_step(self, parent, number: str, title: str, summary: str, lines: list[str]) -> None:
        card = tk.Frame(parent, bg=COLORS["panel_alt"], highlightthickness=1, highlightbackground=COLORS["border_soft"], padx=11, pady=9)
        card.pack(fill="x", pady=(0, 6))
        head = tk.Frame(card, bg=COLORS["panel_alt"])
        head.pack(fill="x")
        tk.Label(head, text=number, bg=COLORS["panel_deep"], fg=COLORS["accent"], font=("Segoe UI Semibold", 7), padx=7, pady=3).pack(side="left")
        tk.Label(head, text=title, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI Semibold", 8)).pack(side="left", padx=(8, 0))
        tk.Label(card, text=summary, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8), wraplength=900, justify="left").pack(anchor="w", pady=(6, 3))
        for line in lines:
            tk.Label(card, text=f"• {line}", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8), wraplength=880, justify="left").pack(anchor="w", padx=(8, 0), pady=1)

    def _build_pending(self, post) -> None:
        battle = self.controller.state.campaign.battle(post.battle_number)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        top = tk.Frame(self, bg=COLORS["bg"])
        top.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        title = tk.Frame(top, bg=COLORS["bg"])
        title.pack(side="left", fill="x", expand=True)
        tk.Label(title, text=tr('POST-BATTLE #{}').format(post.battle_number), bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 16)).pack(side="left")
        tk.Label(title, text=tr('IN PROGRESS'), bg=COLORS["panel_deep"], fg=COLORS["accent"], font=("Segoe UI Semibold", 7), padx=8, pady=4).pack(side="left", padx=10)
        ttk.Button(top, text=tr('SAVE & CLOSE'), command=self._save_and_close).pack(side="right")

        intro = (
            f"Resolve Battle #{post.battle_number} in order. The eight actions below create the next warband state; "
            "rating is recalculated automatically and Final Review only confirms the resulting changes."
        )
        tk.Label(self, text=intro, bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 9), wraplength=1080, justify="left").grid(row=1, column=0, sticky="w", pady=(0, 9))

        PostBattleSequence(
            self,
            POST_BATTLE_STEPS,
            POST_BATTLE_GROUPS,
            post.active_step,
            post.completed_steps,
            self.controller.set_post_battle_step,
            review_active=post.review_open,
        ).grid(row=2, column=0, sticky="ew", pady=(0, 9))

        context = tk.Frame(self, bg=COLORS["bg"])
        context.grid(row=3, column=0, sticky="ew", pady=(0, 6))
        if post.review_open:
            tk.Label(context, text=tr("FINAL REVIEW  ·  ALL 8 ACTIONS COMPLETE"), bg=COLORS["bg"], fg=COLORS["success"], font=("Segoe UI Semibold", 8)).pack(side="left")
            tk.Label(context, text=tr("Next: Commit new warband state"), bg=COLORS["bg"], fg=COLORS["muted_dark"], font=("Segoe UI", 8)).pack(side="right")
        else:
            tk.Label(context, text=tr("CURRENT PHASE  ·  {}").format(tr(POST_BATTLE_STEPS[post.active_step]).upper()), bg=COLORS["bg"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(side="left")
            if post.active_step + 1 < len(POST_BATTLE_STEPS):
                tk.Label(context, text=tr("Next: {}").format(tr(POST_BATTLE_STEPS[post.active_step + 1])), bg=COLORS["bg"], fg=COLORS["muted_dark"], font=("Segoe UI", 8)).pack(side="right")
            else:
                tk.Label(context, text=tr("Next: Final Review"), bg=COLORS["bg"], fg=COLORS["muted_dark"], font=("Segoe UI", 8)).pack(side="right")

        box = BorderedFrame(self, background=COLORS["panel"], padding=1)
        box.grid(row=4, column=0, sticky="nsew")
        scroll = ScrollableFrame(box.body, background=COLORS["panel"])
        scroll.pack(fill="both", expand=True)
        self._scroll = scroll
        body = scroll.inner
        body.configure(padx=18, pady=16)

        if post.review_open:
            self._review(body, battle)
        else:
            handlers = (
                self._injuries,
                self._experience,
                self._exploration,
                self._sell_wyrdstone,
                self._veterans,
                self._rare_and_dramatis,
                self._recruitment,
                self._equipment,
            )
            handlers[post.active_step](body, battle)
            self._follow_ups(body, post)

        actions = tk.Frame(self, bg=COLORS["bg"])
        actions.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        if post.review_open:
            ttk.Button(actions, text=f"‹  {tr('Equipment').upper()}", command=lambda: self.controller.set_post_battle_step(len(POST_BATTLE_STEPS) - 1)).pack(side="left")
            ttk.Button(actions, text=tr('COMMIT STATE #{}').format(post.battle_number), style="Accent.TButton", command=self._commit).pack(side="right")
            return

        if post.active_step > 0:
            ttk.Button(actions, text=f"‹  {tr(POST_BATTLE_STEPS[post.active_step - 1]).upper()}", command=lambda: self.controller.set_post_battle_step(post.active_step - 1)).pack(side="left")

        if post.active_step < len(POST_BATTLE_STEPS) - 1:
            ttk.Button(
                actions,
                text=tr("CONTINUE TO {}  ›").format(tr(POST_BATTLE_STEPS[post.active_step + 1]).upper()),
                style="Accent.TButton",
                command=self._advance_step,
            ).pack(side="right")
        elif post.active_step in post.completed_steps:
            ttk.Button(actions, text=tr('FINAL REVIEW  ›'), style="Accent.TButton", command=self.controller.open_post_battle_review).pack(side="right")
        else:
            ttk.Button(actions, text=tr('CONTINUE TO FINAL REVIEW  ›'), style="Accent.TButton", command=self._advance_step).pack(side="right")

    def _advance_step(self) -> None:
        post = self.controller.state.campaign.pending_post_battle
        if post is None:
            return
        if post.active_step in post.completed_steps:
            self.controller.advance_post_battle_step()
            return
        description = tr(POST_BATTLE_STEPS[post.active_step])
        self.controller.perform_undoable(description, self._advance_step_impl)
        self._rebuild()

    def _advance_step_impl(self) -> None:
        post = self.controller.state.campaign.pending_post_battle
        if post is None:
            return
        engine = self._engine()
        battle = self.controller.state.campaign.battle(post.battle_number)
        if post.active_step == 0:
            if not post.step_state.get("injuries_applied"):
                marked = self._out_of_action_warriors(battle)
                rolls = [self._pending_injury_rolls.get(f"{warrior.id}:{index}") for index, warrior in self._numbered_warriors(marked)]
                if any(not holder or not holder.get("complete") for holder in rolls):
                    messagebox.showerror(tr('Incomplete step'), tr('Resolve every injury roll before continuing.'), parent=self)
                    return False, tr('Resolve every injury roll before continuing.')
                resolver = self.controller.post_battle_resolver()
                for warrior, holder in zip(marked, rolls):
                    kind = "hero" if warrior.kind == "hero" else "henchman"
                    for result in holder.get("finals") or ():
                        if result.get("mode") == "subtable":
                            outcome = resolver.resolve_injury_subtable(kind, str(result.get("parent") or ""), int(result["roll"]))
                        else:
                            outcome = (resolver.resolve_hero_serious_injury(int(result["roll"])) if warrior.kind == "hero"
                                       else resolver.resolve_henchman_serious_injury(int(result["roll"])))
                        if outcome is None:
                            messagebox.showerror(tr('Cannot apply result'), tr('A stored injury result can no longer be resolved from the KB.'), parent=self)
                            return False, tr('A stored injury result can no longer be resolved from the KB.')
                        if result.get("effect_roll") is not None:
                            effects = []
                            for effect in outcome.effects_raw:
                                effect = dict(effect)
                                if effect.get("type") == "warrior.miss_games" and isinstance(effect.get("games"), dict) and effect["games"].get("kind") == "dice":
                                    effect["games"] = {"kind": "fixed", "value": int(result["effect_roll"])}
                                effects.append(effect)
                            outcome = replace(outcome, effects_raw=tuple(effects))
                        ok, message = engine.apply_serious_injury(warrior.id, outcome)
                        if not ok:
                            messagebox.showerror(tr('Cannot apply result'), tr_message(message), parent=self)
                            return False, message
                ok, message = engine.apply_battle_experience()
                if not ok:
                    messagebox.showerror(tr('Cannot apply result'), tr_message(message), parent=self)
                    return False, message
                post.step_state["injuries_applied"] = True
        elif post.active_step == 1:
            unresolved = [row for row in post.pending_advances if not row.get("committed")]
            if unresolved:
                names = []
                for row in unresolved:
                    label = str(row.get("warrior_name") or row.get("warrior_id") or tr('Unknown warrior'))
                    threshold = row.get("threshold")
                    names.append(f"{label} ({threshold} XP)" if threshold is not None else label)
                messagebox.showerror(
                    tr('Incomplete step'),
                    tr('Resolve and apply every earned advance before continuing to Exploration. Pending: {}').format(' · '.join(names)),
                    parent=self,
                )
                return False, tr('Resolve and apply every earned advance before continuing to Exploration.')
        elif post.active_step == 2:
            dice = self._pending_exploration.get("dice")
            if dice is None:
                messagebox.showerror(tr('Incomplete step'), tr('Resolve the exploration roll before continuing.'), parent=self)
                return False, tr('Resolve the exploration roll before continuing.')
            if not self._pending_exploration.get("applied"):
                messagebox.showerror(
                    tr('Incomplete step'),
                    tr('Finish the pending Exploration discard or re-roll decision before continuing.'),
                    parent=self,
                )
                return False, tr('Finish the pending Exploration decision before continuing.')
        elif post.active_step == 3 and not post.sale_resolved:
            quantity = max(0, int(self._sell_var.get())) if self._sell_var is not None else 0
            ok, message = engine.sell_wyrdstone(quantity)
            if not ok:
                messagebox.showerror(tr('Cannot apply result'), tr_message(message), parent=self)
                return False, message
        elif post.active_step == 4:
            dice = self._pending_veterans.get("dice")
            if not dice:
                messagebox.showerror(tr('Incomplete step'), tr('Resolve the veteran roll before continuing.'), parent=self)
                return False, tr('Resolve the veteran roll before continuing.')
            engine.apply_veteran_pool(sum(dice))
        elif post.active_step == 5:
            assigned = [hero_id for hero_id, variable in self._search_assignments.items() if variable.get() != tr('No search')]
            if any(not post.searches.get(hero_id, {}).get("dice") for hero_id in assigned):
                messagebox.showerror(tr('Incomplete step'), tr('Resolve every assigned search before continuing.'), parent=self)
                return False, tr('Resolve every assigned search before continuing.')
        elif post.active_step == 7 and post.equipment_obligations:
            message = tr('Equip every newly recruited Henchman with the required matching equipment before continuing.')
            messagebox.showerror(tr('Incomplete step'), tr_message(message), parent=self)
            return False, message
        open_follow_ups = post.unacknowledged_follow_ups(post.active_step)
        if open_follow_ups:
            messagebox.showerror(
                tr('Incomplete step'),
                tr('Resolve or acknowledge every follow-up before continuing: {}').format(
                    ' · '.join(str(row.get("description") or row.get("id")) for row in open_follow_ups)
                ),
                parent=self,
            )
            # Keep applied injuries and their decisions; remain on Recovery.
            return post.active_step == 0 and bool(post.step_state.get("injuries_applied")), tr('Resolve or acknowledge every follow-up before continuing.')
        self.controller.advance_post_battle_step()
        return True, tr('Step completed')

    @staticmethod
    def _numbered_warriors(warriors) -> list[tuple[int, object]]:
        seen: dict[str, int] = {}
        result = []
        for warrior in warriors:
            seen[warrior.id] = seen.get(warrior.id, 0) + 1
            result.append((seen[warrior.id], warrior))
        return result

    def _commit(self) -> None:
        ok, message = self.controller.commit_post_battle()
        if not ok:
            self._status_text = "⚠ " + message
            self._rebuild()

    # ------------------------------------------------------------- step views

    def _title(self, parent: tk.Misc, title: str, detail: str) -> None:
        tk.Label(parent, text=title, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 14)).pack(anchor="w")
        tk.Label(parent, text=detail, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9), wraplength=980, justify="left").pack(anchor="w", pady=(4, 12))
        self._status_line(parent)

    def _section(self, parent: tk.Misc, title: str, subtitle: str = "") -> tk.Frame:
        frame = tk.Frame(parent, bg=COLORS["panel_alt"], highlightthickness=1, highlightbackground=COLORS["border_soft"], padx=13, pady=11)
        frame.pack(fill="x", pady=(0, 9))
        tk.Label(frame, text=title, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Georgia", 11)).pack(anchor="w")
        if subtitle:
            tk.Label(frame, text=subtitle, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8), wraplength=900, justify="left").pack(anchor="w", pady=(3, 8))
        return frame

    def _kb_provenance(self, index: int) -> str:
        """KB provenance line (sequence step ids + resolved catalogue files)."""
        sources = self.controller.post_battle_content().action_sources()
        source = sources[index]
        step_ids = " + ".join(source.kb_step_ids)
        files = ", ".join(source.resolved_catalogues)
        return tr('KB source: {} — resolves {}').format(step_ids, files)

    # 01 · injuries ---------------------------------------------------------

    def _out_of_action_warriors(self, battle) -> list:
        """Warriors recorded Out of Action for this battle.

        Falls back to every warrior when the battle predates per-warrior
        recording (``out_of_action_ids`` is ``None``).
        """
        warriors = self.controller.state.campaign.warriors
        if battle.out_of_action_ids is None:
            return list(warriors)
        by_id = {warrior.id: warrior for warrior in warriors}
        return [by_id[warrior_id] for warrior_id in battle.out_of_action_ids if warrior_id in by_id]

    def _injuries(self, parent: tk.Misc, battle) -> None:
        resolver = self.controller.post_battle_resolver()
        marked = self._out_of_action_warriors(battle)
        recorded = battle.out_of_action_ids is not None
        scope = (
            tr('{} warrior(s) were recorded Out of Action in the battle record').format(len(marked))
            if recorded else tr('No per-warrior record exists for this battle; every warrior is offered')
        )
        self._title(parent, tr('01 · Injuries'), tr('{}. Resolve each against the KB serious-injury charts: each roll starts unresolved; resolving then applying it mutates the roster. {}').format(scope, self._kb_provenance(0)))
        if not marked:
            tk.Label(parent, text=tr('No warrior was recorded Out of Action: proceed to Experience.'), bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
            return
        totals = {warrior.id: sum(1 for row in marked if row.id == warrior.id) for warrior in marked}
        seen: dict[str, int] = {}
        for warrior in marked:
            seen[warrior.id] = seen.get(warrior.id, 0) + 1
            casualty_number = seen[warrior.id]
            injury_key = f"{warrior.id}:{casualty_number}"
            hero = warrior.kind == "hero"
            holder = self._pending_injury_rolls.setdefault(injury_key, {})
            subtitle = (tr('Hero · Out of Action · D66 serious injury roll')
                        if hero else tr('Henchmen casualty {} of {} · D6 survival roll').format(casualty_number, totals[warrior.id]))
            row = self._section(parent, warrior.name, subtitle)
            for result in holder.get("history") or ():
                tk.Label(row, text=tr('Result: {}').format(result), bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI Semibold", 8), wraplength=850, justify="left").pack(anchor="w", pady=(0, 4))
            followup = holder.get("followup") or {}
            if not holder.get("initial_resolved"):
                self._injury_dice(row, resolver, hero, holder, title=tr('Serious injury roll'), mode="initial")
            elif followup.get("type") == "repeat_count":
                self._injury_dice(row, resolver, hero, holder, title=tr('Roll number of additional injuries'), mode="repeat_count", dice_count=1, notation="D6")
            elif followup.get("type") == "repeat_results":
                self._injury_dice(
                    row, resolver, hero, holder,
                    title=tr('Additional serious injury · {} remaining').format(followup.get("remaining", 0)),
                    mode="repeat_result", dice_count=2, notation="D66",
                )
            elif followup.get("type") == "subtable":
                self._injury_dice(row, resolver, hero, holder, title=tr('Follow-up roll'), mode="subtable", dice_count=1, notation="D6")
            elif followup.get("type") == "effect_dice":
                sides = int(followup.get("sides") or 6)
                count = int(followup.get("count") or 1)
                self._injury_dice(row, resolver, hero, holder, title=tr('Roll required by this result'), mode="effect_dice", dice_count=count, notation=f"{count if count > 1 else ''}D{sides}", dice_sides=sides)

    def _injury_dice(self, parent, resolver, hero: bool, holder: dict, *, title: str, mode: str, dice_count: int | None = None, notation: str | None = None, dice_sides: int = 6) -> None:
        count = dice_count or (2 if hero else 1)
        DiceResolutionCard(
            parent, title=title, subtitle=tr('Roll in app or enter physical dice'),
            notation=notation or ("D66" if hero else "D6"), dice_count=count,
            dice_sides=dice_sides,
            demo_dice=(2, 4) if count == 2 else (3,), combine="d66" if count == 2 else "sum",
            on_resolved=lambda dice: self.controller.perform_undoable(
                tr('Injury roll'), lambda: self._store_injury_roll(resolver, hero, holder, mode, dice)),
            outcome_actions=(),
        ).pack(fill="x", pady=(5, 0))

    def _store_injury_roll(self, resolver, hero: bool, holder: dict, mode: str, dice: list[int]) -> tuple[str, str, str]:
        kind = "hero" if hero else "henchman"
        roll = 10 * dice[0] + dice[1] if len(dice) > 1 else dice[0]
        followup = holder.get("followup") or {}
        if mode == "effect_dice":
            holder.setdefault("history", []).append(tr('{}: {}').format(followup.get("label") or 'Additional roll', roll))
            holder.setdefault("finals", []).append({**dict(followup.get("final") or {}), "effect_roll": roll})
            remaining = max(0, int(followup.get("resume_repeat") or 0))
            holder["followup"] = {
                "type": "repeat_results", "result_id": followup.get("repeat_parent"), "remaining": remaining,
            } if remaining else {}
            holder["complete"] = remaining == 0
            self.after_idle(self._rebuild)
            return tr('Result recorded'), str(roll), "accent"
        if mode == "repeat_count":
            holder["followup"] = {**followup, "type": "repeat_results", "remaining": dice[0]}
            holder.setdefault("history", []).append(tr('Multiple Injuries: {} additional result(s)').format(dice[0]))
            self.after_idle(self._rebuild)
            return tr('Additional injuries'), tr('{} D66 roll(s) required.').format(dice[0]), "danger"
        if mode == "subtable":
            outcome = resolver.resolve_injury_subtable(kind, str(followup.get("result_id") or ""), roll)
            if outcome is None:
                return tr('Invalid result'), tr('This subtable result could not be resolved from the KB.'), "danger"
            holder.setdefault("finals", []).append({"mode": "subtable", "parent": followup["result_id"], "roll": roll})
            holder.setdefault("history", []).append(_injury_history(outcome, roll))
            remaining = max(0, int(followup.get("resume_repeat") or 0))
            holder["followup"] = {
                "type": "repeat_results",
                "result_id": followup.get("repeat_parent"),
                "remaining": remaining,
            } if remaining else {}
            holder["complete"] = remaining == 0
            self.after_idle(self._rebuild)
            return tr(outcome.result), _injury_detail(outcome), "accent"
        if mode == "repeat_result":
            outcome = resolver.resolve_repeat_reroll(kind, str(followup.get("result_id") or ""), roll)
            if outcome is None:
                holder.setdefault("history", []).append(tr('Rolled {}: excluded result — roll again').format(roll))
                self.after_idle(self._rebuild)
                return tr('Roll again'), tr('This result is excluded from Multiple Injuries.'), "danger"
            holder.setdefault("history", []).append(_injury_history(outcome, roll))
            remaining = max(0, int(followup.get("remaining") or 1) - 1)
            if outcome.follow_up:
                holder["followup"] = {
                    "type": "subtable",
                    "result_id": outcome.result_id,
                    "resume_repeat": remaining,
                    "repeat_parent": followup.get("result_id"),
                }
                holder["complete"] = False
            else:
                final = {"mode": "base", "roll": roll}
                effect_dice = self._injury_effect_dice(outcome)
                if effect_dice:
                    holder["followup"] = {
                        "type": "effect_dice", "final": final,
                        "resume_repeat": remaining, "repeat_parent": followup.get("result_id"), **effect_dice,
                    }
                    holder["complete"] = False
                else:
                    holder.setdefault("finals", []).append(final)
                    holder["followup"] = {**followup, "remaining": remaining} if remaining else {}
                    holder["complete"] = remaining == 0
            self.after_idle(self._rebuild)
            return tr(outcome.result), _injury_detail(outcome), "accent"

        outcome = resolver.resolve_hero_serious_injury(roll) if hero else resolver.resolve_henchman_serious_injury(roll)
        holder["dice"] = list(dice)
        holder["initial_resolved"] = True
        holder.setdefault("history", []).append(_injury_history(outcome, roll))
        if outcome.follow_up:
            repeated = bool(resolver.repeat_reroll_exclusions(kind, outcome.result_id))
            holder["followup"] = {"type": "repeat_count" if repeated else "subtable", "result_id": outcome.result_id}
            holder["complete"] = False
        else:
            final = {"mode": "base", "roll": roll}
            effect_dice = self._injury_effect_dice(outcome)
            if effect_dice:
                holder["followup"] = {"type": "effect_dice", "final": final, **effect_dice}
                holder["complete"] = False
            else:
                holder.setdefault("finals", []).append(final)
                holder["complete"] = True
        self.after_idle(self._rebuild)
        return _injury_card(dice, resolver, hero=hero)

    @staticmethod
    def _injury_effect_dice(outcome) -> dict | None:
        for effect in outcome.effects_raw:
            value = effect.get("games") if effect.get("type") == "warrior.miss_games" else None
            if isinstance(value, dict) and value.get("kind") == "dice":
                dice = value.get("dice") or {}
                return {"count": int(dice.get("count") or 1), "sides": int(dice.get("sides") or 6), "label": "Games missed"}
        return None

    # 02 · experience -------------------------------------------------------

    def _experience(self, parent: tk.Misc, battle) -> None:
        engine = self._engine()
        self._title(parent, tr('02 · Experience'), tr('Allocate the experience Battle #{} granted (+{} XP). Crossed thresholds earn advance rolls resolved against the KB advancement tables; stat increases and skill/spell picks are committed here. {}').format(battle.number, battle.xp_delta, self._kb_provenance(1)))
        for warrior in self.controller.state.campaign.warriors:
            card = tk.Frame(parent, bg=COLORS["panel_alt"], padx=12, pady=10)
            card.pack(fill="x", pady=(0, 7))
            top = tk.Frame(card, bg=COLORS["panel_alt"])
            top.pack(fill="x")
            tk.Label(top, text=warrior.name, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Georgia", 11)).pack(side="left")
            label = warrior.profile_name
            if warrior.quantity > 1:
                label += f"  ·  ×{warrior.quantity}"
            tk.Label(top, text=label, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left", padx=(8, 0))
            tk.Label(top, text=tr('XP {}').format(warrior.experience), bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(side="right", padx=(0, 10))
            tk.Label(card, text=tr('Battle result award: +{} XP').format(battle.xp_delta), bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(5, 5))
            ExperienceTrack(card, warrior.experience, track_type="hero" if warrior.kind == "hero" else "henchman").pack(fill="x")

        tk.Label(parent, text=tr('ADVANCE ROLLS EARNED THIS SEQUENCE'), bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(7, 6))
        pending = engine.post.pending_advances if engine.post is not None else []
        if not pending:
            tk.Label(
                parent,
                text=tr('No warrior has crossed an experience threshold yet. Grant XP above; a threshold earns a 2D6 advance roll on the KB table (heroes: 20/40/65/90… · henchmen: 8/16/25/35…).'),
                bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8), wraplength=900, justify="left",
            ).pack(anchor="w")
            return
        counts: dict[str, int] = {}
        for row in pending:
            if not row.get("committed"):
                warrior_id = str(row.get("warrior_id"))
                counts[warrior_id] = counts.get(warrior_id, 0) + 1
        multiple = [f"{row.name}: {counts[row.id]}" for row in self.controller.state.campaign.warriors if counts.get(row.id, 0) > 1]
        if multiple:
            tk.Label(
                parent, text=tr('Multiple advances earned · {}').format(' · '.join(multiple)),
                bg=COLORS["panel_deep"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8), padx=10, pady=6,
            ).pack(fill="x", pady=(0, 7))
        for row in list(pending):
            self._advance_card(parent, engine, row)

    def _advance_card(self, parent: tk.Misc, engine, row: dict) -> None:
        warrior_id = str(row.get("warrior_id"))
        warrior = next((w for w in engine.campaign.warriors if w.id == warrior_id), None)
        if warrior is None:
            return
        is_hero = str(row.get("table") or "hero") == "hero"
        kind_label = tr('Hero') if is_hero else f"Henchmen group (all {warrior.quantity} members gain it)"
        threshold = row.get("threshold")
        committed = bool(row.get("committed"))
        roll_total = row.get("roll_total")
        if row.get("promotion_immediate"):
            subtitle = tr("New Hero · The Lad's Got Talent · immediate 2D6 Hero advance")
        else:
            subtitle = tr('{} · crossed the {} XP threshold · 2D6 on the KB {} table').format(kind_label, threshold, 'hero' if is_hero else 'henchman')
        if committed:
            subtitle += tr(' · COMMITTED: {}').format(row.get('applied_label') or 'applied')
        elif roll_total is not None:
            subtitle += tr(' · rolled {}').format(roll_total)

        card = tk.Frame(parent, bg=COLORS["panel_alt"], highlightthickness=1, highlightbackground=COLORS["border_soft"], padx=12, pady=10)
        card.pack(fill="x", pady=(0, 7))
        top = tk.Frame(card, bg=COLORS["panel_alt"])
        top.pack(fill="x")
        tk.Label(top, text=warrior.name, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Georgia", 11)).pack(side="left")
        tk.Label(top, text="ADVANCE", bg=COLORS["panel_deep"], fg=COLORS["success" if committed else "accent"], font=("Segoe UI Semibold", 7), padx=7, pady=3).pack(side="right")
        tk.Label(card, text=subtitle, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(3, 0))
        for previous in row.get("roll_history") or ():
            tk.Label(card, text=tr('Previous result: {}').format(previous), bg=COLORS["panel_alt"], fg=COLORS["danger"], font=("Segoe UI", 8), wraplength=850, justify="left").pack(anchor="w", pady=(3, 0))

        if committed:
            return
        if row.get("promotion_setup_pending"):
            tk.Label(
                card, text=tr('Choose exactly two Hero skill lists. These define future skill advances; they do not grant skills now.'),
                bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8),
            ).pack(anchor="w", pady=(7, 5))
            ttk.Button(
                card, text=tr('CHOOSE 2 SKILL LISTS…'), style="Accent.TButton",
                command=lambda w=warrior_id: self._choose_promotion_tables(w),
            ).pack(anchor="w")
            return
        if roll_total is None:
            holder: dict = {}
            DiceResolutionCard(
                card, title=tr('Advance roll'), subtitle=tr('Roll in app or enter physical dice'),
                notation="2D6", dice_count=2, demo_dice=(4, 3), combine="sum",
                outcome_title=tr('Pending advance'), outcome_detail=tr('The result will be applied automatically when possible.'),
                on_resolved=lambda dice, _e=engine, _w=warrior_id, _t=threshold, _x=holder: self.controller.perform_undoable(
                    tr('Advance roll'), lambda: self._advance_roll_result(_e, _w, _t, _x, dice)),
                outcome_actions=((tr('RESOLVE ADVANCE'), lambda: self._resolve_advance(engine, warrior_id, threshold, holder), "Accent.TButton"),),
            ).pack(fill="x", pady=(8, 0))
            return
        outcome, _row = engine._pending_outcome(warrior_id, threshold)
        if outcome is None:
            return
        tk.Label(card, text=f"{outcome.title} · {outcome.detail}", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(anchor="w", pady=(6, 4))
        actions = tk.Frame(card, bg=COLORS["panel_alt"])
        actions.pack(fill="x")
        for option in outcome.options:
            if option.kind == "characteristic_increase" and len(outcome.options) > 1:
                for key in warrior.stats:
                    if f"+{option.amount} {key}" == option.label:
                        ttk.Button(actions, text=f"+1 {key}", style="Mini.TButton",
                                   command=lambda w=warrior_id, t=threshold, k=key: self._commit_advance(w, threshold=t, option_kind="characteristic_increase", characteristic=k)).pack(side="left", padx=(0, 6))
                        break
            elif option.kind == "choose_skill":
                ttk.Button(actions, text=tr('CHOOSE SKILL…'), style="Accent.TButton",
                           command=lambda w=warrior_id, t=threshold: self._open_skill_dialog(w, want_spells=False, threshold=t)).pack(side="left", padx=(0, 6))
            elif option.kind == "generate_spell":
                ttk.Button(actions, text=tr('GENERATE SPELL…'), style="Accent.TButton",
                           command=lambda w=warrior_id, t=threshold: self._open_skill_dialog(w, want_spells=True, threshold=t)).pack(side="left", padx=(0, 6))
            elif option.kind == "promote_henchman":
                ttk.Button(actions, text=tr("THE LAD'S GOT TALENT…"), style="Accent.TButton",
                           command=lambda w=warrior_id, t=threshold: self._promote_member(w, threshold=t)).pack(side="left", padx=(0, 6))
            elif option.kind == "external_resolution":
                ttk.Button(actions, text=tr('CONFIRM TABLE-SIDE RESOLUTION'), style="Accent.TButton",
                           command=lambda w=warrior_id, t=threshold: self._commit_advance(
                               w, threshold=t, option_kind="external_resolution"
                           )).pack(side="left", padx=(0, 6))
        if not outcome.options:
            tk.Label(
                actions,
                text=tr('This result requires an effect or reroll outside the application. Reopen the advance and roll again once the roster is correct.'),
                bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8),
                wraplength=850, justify="left",
            ).pack(anchor="w")
            ttk.Button(actions, text=tr('REOPEN ADVANCE FOR REROLL'), style="Accent.TButton",
                       command=lambda w=warrior_id, t=threshold: self._reroll_unsupported(w, t)).pack(side="left", pady=(4, 0))
    def _advance_roll_result(self, engine, warrior_id: str, threshold: int, holder: dict, dice: list[int]) -> tuple[str, str, str]:
        """Persist a known roll immediately and continue only with real choices."""
        holder["dice"] = list(dice)
        total = sum(dice)
        ok, message = engine.resolve_pending_advance(warrior_id, total, threshold=threshold)
        self._status_text = ("✓ " if ok else "⚠ ") + message
        if not ok:
            self.after_idle(self._rebuild)
            return tr('Advance needs attention'), message, "danger"
        outcome, row = engine._pending_outcome(warrior_id, threshold)
        if outcome is not None and not outcome.final:
            self.after_idle(lambda: self._complete_advance_subroll(engine, warrior_id, threshold, total))
            return outcome.title, outcome.detail, "accent"
        if row is not None and row.get("committed"):
            self.after_idle(self._rebuild)
            return tr('Advance applied'), str(row.get("applied_label") or message), "success"
        options = tuple(outcome.options) if outcome is not None else ()
        if len(options) == 1 and options[0].kind == "choose_skill":
            self.after_idle(lambda: self._open_skill_dialog(warrior_id, want_spells=False, threshold=threshold))
            return tr('Choose a skill'), tr('Select one of the skills available to this Hero.'), "accent"
        self.after_idle(self._rebuild)
        return outcome.title if outcome else tr('Advance resolved'), outcome.detail if outcome else message, "accent"

    def _complete_advance_subroll(self, engine, warrior_id: str, threshold: int, total: int) -> None:
        subroll = self._ask_subroll(total)
        if subroll is None:
            self._rebuild()
            return
        self._run(lambda: engine.resolve_pending_advance(warrior_id, total, subroll=subroll, threshold=threshold))

    def _resolve_advance(self, engine, warrior_id: str, threshold: int, holder: dict) -> None:
        dice = holder.get("dice")
        if dice is None:
            return
        total = sum(dice)
        ok, message = self.controller.perform_undoable(
            tr('Resolve advance'),
            lambda: engine.resolve_pending_advance(warrior_id, total, threshold=threshold))
        self._status_text = ("✓ " if ok else "⚠ ") + message
        if not ok:
            self._rebuild()
            return
        outcome, row = engine._pending_outcome(warrior_id, threshold)
        if outcome is not None and not outcome.final:
            self._complete_advance_subroll(engine, warrior_id, threshold, total)
        elif row is not None and row.get("committed"):
            self._rebuild()
        elif outcome is not None and len(outcome.options) == 1 and outcome.options[0].kind == "choose_skill":
            self._open_skill_dialog(warrior_id, want_spells=False, threshold=threshold)
        else:
            self._rebuild()

    def _ask_subroll(self, total: int) -> int | None:
        dice = ask_dice(self, title=tr('The advance row {} needs a D6 sub-roll.').format(total), dice_count=1)
        return dice[0] if dice else None

    def _commit_advance(self, warrior_id: str, *, threshold: int | None = None, option_kind: str, characteristic: str | None = None) -> None:
        engine = self._engine()
        ok, message = self.controller.perform_undoable(
            tr('Apply advance'), lambda: engine.commit_pending_advance(
                warrior_id, option_kind=option_kind, characteristic=characteristic, threshold=threshold,
            ))
        self._status_text = ("✓ " if ok else "⚠ ") + message
        self._rebuild()

    def _choose_promotion_tables(self, warrior_id: str) -> None:
        engine = self._engine()
        tables = list(engine.promotion_hero_tables(warrior_id))
        dialog = tk.Toplevel(self)
        dialog.title(tr('Hero skill lists'))
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        tk.Label(dialog, text=tr('Choose exactly two skill lists available to Heroes in this warband.'),
                 bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 10)).pack(padx=18, pady=(14, 7))
        choices = tk.Listbox(dialog, selectmode="multiple", exportselection=False, height=min(9, len(tables)), width=34,
                             bg=COLORS["entry"], fg=COLORS["text"], selectbackground=COLORS["accent"], bd=0)
        choices.pack(fill="x", padx=18)
        for table in tables:
            choices.insert("end", table)
        status = tk.StringVar()
        tk.Label(dialog, textvariable=status, bg=COLORS["panel"], fg=COLORS["danger"], font=("Segoe UI", 8)).pack(padx=18, pady=5)

        def confirm() -> None:
            selected = [tables[index] for index in choices.curselection()]
            ok, message = self.controller.perform_undoable(
                tr('Choose Hero skill lists'), lambda: engine.set_promotion_skill_tables(warrior_id, selected))
            if not ok:
                status.set(message)
                return
            self._status_text = "✓ " + message
            dialog.destroy()
            self._rebuild()

        ttk.Button(dialog, text=tr('CONFIRM LISTS'), style="Accent.TButton", command=confirm).pack(pady=(2, 14))
        dialog.bind("<Escape>", lambda _e: dialog.destroy())
        dialog.after_idle(lambda: center_on_application(dialog))

    def _reroll_advance(self, warrior_id: str, threshold: int, outcome) -> None:
        reason = tr('Rolled {}: {} — this result cannot be applied and must be rerolled.').format(outcome.roll, outcome.title)
        self._run(lambda: self._engine().reset_pending_advance_for_reroll(warrior_id, threshold=threshold, reason=reason))

    def _reroll_unsupported(self, warrior_id: str, threshold: int | None) -> None:
        """Structured action for advancement results the app cannot auto-apply."""
        reason = tr('Result resolved at the table; the advance reopens for a new roll.')
        self._run(lambda: self._engine().reset_pending_advance_for_reroll(warrior_id, threshold=threshold, reason=reason))

    def _promote_member(self, warrior, *, threshold: int | None = None) -> None:
        """Ask for the promoted member's name, then split the group (Lad's Got Talent)."""
        dialog = tk.Toplevel(self)
        dialog.title(tr("The Lad's Got Talent"))
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        tk.Label(
            dialog,
            text=tr('Name the member of {} who becomes a Hero.').format(warrior.name),
            bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 10),
        ).pack(padx=18, pady=(14, 6))
        var = tk.StringVar(value=tr('{} Champion').format(warrior.profile_name))
        entry = ttk.Entry(dialog, textvariable=var, width=32)
        entry.pack(padx=18, pady=4)
        entry.selection_range(0, "end")
        entry.focus_set()
        result: list[str] = []

        def _confirm() -> None:
            result.append(var.get().strip() or tr('{} Champion').format(warrior.profile_name))
            dialog.destroy()

        ttk.Button(dialog, text=tr('PROMOTE'), style="Accent.TButton", command=_confirm).pack(pady=(6, 14))
        dialog.bind("<Return>", lambda _e: _confirm())
        dialog.bind("<Escape>", lambda _e: dialog.destroy())
        dialog.after_idle(lambda: center_on_application(dialog))
        dialog.wait_window()
        if not result:
            return
        ok, message = self.controller.perform_undoable(
            tr("The Lad's Got Talent"),
            lambda: self._engine().promote_henchman(warrior.id, member_name=result[0], threshold=threshold))
        self._status_text = ("✓ " if ok else "⚠ ") + message
        self._rebuild()

    def _open_skill_dialog(self, warrior_id: str, *, want_spells: bool, promotion: bool = False, threshold: int | None = None) -> None:
        from mordheim_campaign.ui.dialogs.skill_choice import SkillChoiceDialog

        dialog = SkillChoiceDialog(
            self, self.controller, warrior_id,
            want_spells=want_spells, promotion=promotion, threshold=threshold,
        )
        self.wait_window(dialog)
        engine = self._engine()
        row = engine.post.pending_advance_for(warrior_id, threshold) if engine.post is not None else None
        if row is not None and row.get("committed"):
            self._status_text = "✓ " + str(row.get("applied_label") or tr('Advance committed'))
        self._rebuild()

    # 03 · exploration ------------------------------------------------------

    def _exploration(self, parent: tk.Misc, battle) -> None:
        resolver = self.controller.post_battle_resolver()
        engine = self._engine()
        self._title(parent, tr('03 · Exploration'), tr('Roll once for each eligible Hero, plus one die when the warband won. Shards come from the KB shard chart; matching dice open the KB special-result table. {}').format(self._kb_provenance(2)))
        surviving = engine.eligible_exploration_heroes(battle)
        won = battle.result == "Victory"
        scenario_rule = (engine.post.step_state.get("scenario_exploration") or {}) if engine.post is not None else {}
        extra_dice = max(0, int(scenario_rule.get("extra_dice") or 0))
        campaign_rules = [str(rule.get("text") or "") for rule in engine.campaign.special_rules]
        straggler_rule = next((text for text in campaign_rules if "extra die" in text and "discard" in text), "")
        persistent_reroll = any("re-roll one die" in text for text in campaign_rules)
        if straggler_rule:
            extra_dice += 1
        dice_count = resolver.exploration_dice(surviving_heroes=surviving, warband_won=won) + extra_dice
        demo = ((3, 3, 5, 6) + (1,) * 6)[:dice_count]
        holder = self._pending_exploration
        reroll_note = tr(' · the scenario allows one complete reroll') if scenario_rule.get("reroll_all") else ""
        dice = holder.get("dice")
        if dice is None and dice_count == 0:
            self.controller.perform_undoable(tr('Exploration roll'), lambda: self._apply_exploration_roll([], resolver, holder))
            return
        if dice is None:
            DiceResolutionCard(
                parent, title=tr('Exploration Dice'), subtitle=tr('Eligible Heroes: {} · {}D6 from the KB allocation').format(surviving, dice_count) + reroll_note,
                notation=f"{dice_count}D6", dice_count=dice_count, demo_dice=demo, combine="list",
                outcome_title="Exploration resolved", outcome_detail=tr('Resolve the roll to reveal the shard total.'),
                on_resolved=lambda values, _r=resolver, _x=holder: self.controller.perform_undoable(
                    tr('Exploration roll'), lambda: self._apply_exploration_roll(values, _r, _x)),
                outcome_actions=(),
            ).pack(fill="x")
            return

        if not holder.get("applied") and straggler_rule and not holder.get("discarded"):
            self._exploration_discard_choice(parent, holder, straggler_rule)
            return
        if not holder.get("applied") and scenario_rule.get("reroll_all") and not holder.get("scenario_reroll_decided"):
            self._exploration_full_reroll_choice(parent, holder, resolver)
            return
        if not holder.get("applied") and persistent_reroll and not holder.get("reroll_decided"):
            self._exploration_reroll_choice(parent, holder, resolver)
            return
        if not holder.get("applied"):
            self._commit_exploration_dice(holder, resolver)
            return

        resolved = resolver.resolve_exploration(tuple(dice))
        SummaryStrip(parent, [
            (tr('Dice total'), str(resolved.total)),
            (tr('Wyrdstone from roll'), f"+{resolved.shards}"),
            (tr('In hoard'), str(engine.projected_shards())),
        ]).pack(fill="x", pady=(0, 12))
        event = resolver.exploration_followup_row(tuple(dice))
        if event is None:
            card = self._section(parent, tr('EXPLORATION EVENT'), tr('No matching-dice event was obtained.'))
            tk.Label(card, text=tr('No special event.'), bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
            return
        self._exploration_event(parent, event)

    def _apply_exploration_roll(self, dice: list[int], resolver, holder: dict) -> tuple[str, str, str]:
        holder["dice"] = list(dice)
        campaign_rules = [str(rule.get("text") or "") for rule in self._engine().campaign.special_rules]
        scenario_rule = (self._engine().post.step_state.get("scenario_exploration") or {}) if self._engine().post else {}
        needs_choice = (
            any("extra die" in text and "discard" in text for text in campaign_rules)
            or any("re-roll one die" in text for text in campaign_rules)
            or bool(scenario_rule.get("reroll_all"))
        )
        if needs_choice:
            self.after_idle(self._rebuild)
        if not holder.get("applied") and not needs_choice:
            ok, message = self._engine().apply_exploration(tuple(dice))
            if ok:
                holder["applied"] = True
                self._status_text = "✓ " + message
                self.after_idle(self._rebuild)
            else:
                self._status_text = "⚠ " + message
        return _exploration_card(dice, resolver)

    def _commit_exploration_dice(self, holder: dict, resolver) -> None:
        dice = list(holder.get("dice") or ())
        ok, message = self._engine().apply_exploration(tuple(dice))
        if ok:
            holder["applied"] = True
            if holder.get("discarded"):
                campaign = self._engine().campaign
                campaign.special_rules[:] = [rule for rule in campaign.special_rules
                    if not ("extra die" in str(rule.get("text") or "") and "discard" in str(rule.get("text") or ""))]
        self._status_text = ("✓ " if ok else "⚠ ") + message
        self.after_idle(self._rebuild)

    def _exploration_discard_choice(self, parent: tk.Misc, holder: dict, _rule: str) -> None:
        card = self._section(parent, tr('STRAGGLER BONUS'), tr('Choose one die to discard before resolving Exploration.'))
        dice = list(holder.get("dice") or ())
        selected = tk.IntVar(value=0)
        for index, value in enumerate(dice):
            ttk.Radiobutton(card, text=f"D{index + 1}: {value}", variable=selected, value=index).pack(side="left", padx=(0, 8))
        ttk.Button(card, text=tr('DISCARD'), style="Accent.TButton", command=lambda: self._discard_exploration_die(
            holder, selected.get()
        )).pack(side="left")

    def _discard_exploration_die(self, holder: dict, index: int) -> None:
        def discard() -> None:
            dice = list(holder.get("dice") or ())
            if 0 <= index < len(dice):
                dice.pop(index)
            holder["dice"], holder["discarded"] = dice, True
        self.controller.perform_undoable(tr('Discard Exploration die'), discard)
        self._rebuild()

    def _exploration_reroll_choice(self, parent: tk.Misc, holder: dict, resolver) -> None:
        card = self._section(parent, tr('CATACOMBS RE-ROLL'), tr('You may re-roll one Exploration die.'))
        dice = list(holder.get("dice") or ())
        selected = tk.IntVar(value=0)
        picks = tk.Frame(card, bg=COLORS["panel_alt"]); picks.pack(fill="x", pady=(0, 4))
        for index, value in enumerate(dice):
            ttk.Radiobutton(picks, text=f"D{index + 1}: {value}", variable=selected, value=index).pack(side="left", padx=(0, 8))
        # A compact die card keeps Roll in app / Enter manually consistent.
        DiceResolutionCard(card, title=tr('Replacement die'), subtitle=tr('Roll in app or enter physical dice'),
            notation="D6", dice_count=1, demo_dice=(3,), combine="sum",
            on_resolved=lambda values: self.controller.perform_undoable(
                tr('Exploration re-roll'), lambda: self._replace_exploration_die(holder, selected.get(), values[0], resolver)),
            outcome_actions=()).pack(fill="x", pady=(5, 0))
        ttk.Button(card, text=tr('KEEP ORIGINAL ROLL'), style="Mini.TButton",
                   command=lambda: (self.controller.perform_undoable(
                       tr('Keep Exploration roll'), lambda: holder.update(reroll_decided=True)), self._rebuild())).pack(anchor="e", pady=(5, 0))

    def _exploration_full_reroll_choice(self, parent: tk.Misc, holder: dict, resolver) -> None:
        dice = list(holder.get("dice") or ())
        card = self._section(parent, tr('SCENARIO RE-ROLL'), tr('The scenario permits one complete Exploration re-roll.'))
        DiceResolutionCard(
            card, title=tr('Re-roll all Exploration dice'), subtitle=tr('Roll in app or enter physical dice'),
            notation=f"{len(dice)}D6", dice_count=len(dice), demo_dice=tuple(1 for _ in dice), combine="list",
            on_resolved=lambda values: self.controller.perform_undoable(
                tr('Exploration re-roll'), lambda: self._replace_full_exploration_roll(holder, values, resolver)),
            outcome_actions=(),
        ).pack(fill="x")
        ttk.Button(card, text=tr('KEEP ORIGINAL ROLL'), style="Mini.TButton",
                   command=lambda: (self.controller.perform_undoable(
                       tr('Keep Exploration roll'), lambda: holder.update(scenario_reroll_decided=True)), self._rebuild())).pack(anchor="e", pady=(5, 0))

    def _replace_full_exploration_roll(self, holder: dict, values: list[int], resolver) -> tuple[str, str, str]:
        holder["dice"] = list(values)
        holder["scenario_reroll_decided"] = True
        self.after_idle(self._rebuild)
        return _exploration_card(list(values), resolver)

    def _replace_exploration_die(self, holder: dict, index: int, value: int, resolver) -> tuple[str, str, str]:
        dice = list(holder.get("dice") or ())
        if dice:
            dice[max(0, min(index, len(dice) - 1))] = int(value)
        holder["dice"], holder["reroll_decided"] = dice, True
        self.after_idle(self._rebuild)
        return _exploration_card(dice, resolver)

    def _exploration_event(self, parent: tk.Misc, event: dict) -> None:
        pattern = str(event.get("dice_pattern") or "").replace(",", " · ")
        card = self._section(parent, tr('EXPLORATION EVENT'), f"{pattern}  ·  {event.get('outcome')}")
        rewards = self._exploration_reward_labels(event.get("follow_up") or {})
        if rewards:
            tk.Label(card, text=tr('Possible effects and rewards'), bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 3))
            for reward in rewards:
                tk.Label(card, text=f"• {reward}", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8), wraplength=760, justify="left").pack(anchor="w", padx=(7, 0))

        engine = self._engine()
        pending = engine.exploration_followup_pending()
        row = engine._exploration_followup_row()
        for message in (row or {}).get("messages") or ():
            tk.Label(card, text=f"✓ {message}", bg=COLORS["panel_alt"], fg=COLORS["success"], font=("Segoe UI", 8)).pack(anchor="w", pady=1)
        if row is None:
            completed = [entry for entry in (engine.post.event_log if engine.post else ()) if entry.get("step") == 2 and entry.get("action") == "exploration_followup"]
            if completed:
                tk.Label(card, text=str(completed[-1].get("message") or ""), bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8), wraplength=760, justify="left").pack(anchor="w", pady=(6, 0))
            tk.Label(card, text=tr('Event resolved.'), bg=COLORS["panel_alt"], fg=COLORS["success"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(6, 0))
            return
        if (pending or {}).get("kind") == "choose_hero":
            self._exploration_hero_choice(card, row)
        elif (pending or {}).get("kind") == "choose_option":
            self._exploration_option_choice(card, pending)
        elif (pending or {}).get("kind") == "choose_warriors":
            self._exploration_warrior_choice(card, pending)
        else:
            count = int((pending or {}).get("dice_count") or 1)
            sides = int((pending or {}).get("dice_sides") or 6)
            DiceResolutionCard(
                card,
                title=self._exploration_prompt(pending),
                subtitle=tr('Roll in app or enter physical dice'),
                notation=f"{count if count > 1 else ''}D{sides}",
                dice_count=count,
                dice_sides=sides,
                demo_dice=(1,) * count,
                combine="sum",
                on_resolved=lambda dice: self.controller.perform_undoable(
                    tr('Exploration event roll'), lambda: self._apply_exploration_event_roll(dice)),
                outcome_actions=(),
            ).pack(fill="x", pady=(8, 0))

    def _exploration_hero_choice(self, card: tk.Misc, row: dict) -> None:
        heroes = [warrior for warrior in self.controller.state.campaign.warriors if warrior.kind == "hero"]
        action = tk.Frame(card, bg=COLORS["panel_alt"]); action.pack(fill="x", pady=(8, 0))
        tk.Label(action, text=tr('Choose a Hero'), bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI Semibold", 8)).pack(side="left")
        labels = [hero.name for hero in heroes]
        selected = tk.StringVar(value=labels[0] if labels else "")
        ttk.Combobox(action, state="readonly", values=labels, textvariable=selected, width=25).pack(side="left", padx=8)
        ttk.Button(
            action, text=tr('CONFIRM'), style="Accent.TButton",
            command=lambda: self._apply_exploration_hero(heroes[labels.index(selected.get())].id) if selected.get() in labels else None,
        ).pack(side="left")

    def _apply_exploration_hero(self, hero_id: str) -> None:
        self._run(lambda: self._engine().advance_exploration_followup(hero_id=hero_id))

    def _exploration_option_choice(self, card: tk.Misc, pending: dict) -> None:
        action = tk.Frame(card, bg=COLORS["panel_alt"]); action.pack(fill="x", pady=(8, 0))
        tk.Label(action, text=str(pending.get("label") or tr('Choose an outcome')), bg=COLORS["panel_alt"],
                 fg=COLORS["text"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 4))
        buttons = tk.Frame(action, bg=COLORS["panel_alt"]); buttons.pack(fill="x")
        for option in pending.get("options") or ():
            ttk.Button(buttons, text=str(option.get("label") or option.get("id")), style="Accent.TButton",
                       command=lambda oid=str(option.get("id")): self._run(
                           lambda: self._engine().advance_exploration_followup(option_id=oid)
                       )).pack(side="left", padx=(0, 6))

    def _exploration_warrior_choice(self, card: tk.Misc, pending: dict) -> None:
        action = tk.Frame(card, bg=COLORS["panel_alt"]); action.pack(fill="x", pady=(8, 0))
        maximum = int(pending.get("maximum") or 1)
        tk.Label(action, text=f"{pending.get('label') or tr('Choose warriors')} · {tr('maximum')} {maximum}",
                 bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        choices = []
        for option in pending.get("options") or ():
            variable = tk.BooleanVar(value=False); choices.append((str(option.get("id")), variable))
            ttk.Checkbutton(action, text=str(option.get("label")), variable=variable).pack(anchor="w", pady=1)
        ttk.Button(action, text=tr('CONFIRM'), style="Accent.TButton", command=lambda: self._run(
            lambda: self._engine().advance_exploration_followup(
                warrior_ids=[warrior_id for warrior_id, variable in choices if variable.get()]
            ))).pack(anchor="e", pady=(5, 0))

    def _apply_exploration_event_roll(self, dice: list[int]) -> tuple[str, str, str]:
        ok, message = self._engine().advance_exploration_followup(roll=sum(dice))
        self._status_text = ("✓ " if ok else "⚠ ") + message
        if ok:
            self.after_idle(self._rebuild)
        return (tr('Result recorded') if ok else tr('Cannot apply result'), message, "success" if ok else "danger")

    def _exploration_prompt(self, pending: dict | None) -> str:
        label = str((pending or {}).get("label") or "")
        replacements = {
            "gold_crowns roll": tr('Gold crowns roll'),
            "wyrdstone_fragments roll": tr('Wyrdstone roll'),
            "follow-up roll": tr('Event result roll'),
            "toughness test": tr('Toughness test'),
            "leadership test": tr('Leadership test'),
        }
        if label in replacements:
            return replacements[label]
        if label.endswith(" quantity roll"):
            item_id = label.removesuffix(" quantity roll")
            return tr('{} quantity roll').format(self.controller.port.item_name(item_id) or item_id.replace("_", " ").title())
        return label.replace("_", " ").strip().title() or tr('Event result roll')

    def _exploration_reward_labels(self, node) -> list[str]:
        labels: list[str] = []
        if isinstance(node, list):
            for child in node:
                labels.extend(self._exploration_reward_labels(child))
            return list(dict.fromkeys(labels))
        if not isinstance(node, dict):
            return labels
        for resource, amount in (node.get("resources") or {}).items():
            resource_name = {
                "gold_crowns": tr('Gold crowns'),
                "wyrdstone_fragments": tr('Wyrdstone shards'),
                "experience": tr('Experience'),
            }.get(resource, resource.replace("_", " ").title())
            labels.append(f"{resource_name}: {self._reward_amount_label(amount)}")
        for item in node.get("items") or ():
            item_id = str(item.get("item_id") or "")
            labels.append(f"{self.controller.port.item_name(item_id) or item_id}: {self._reward_amount_label(item.get('quantity'))}")
        if node.get("note"):
            labels.append(tr_message(str(node["note"])))
        for value in node.values():
            if isinstance(value, (dict, list)):
                labels.extend(self._exploration_reward_labels(value))
        return list(dict.fromkeys(labels))

    @staticmethod
    def _reward_amount_label(amount) -> str:
        if not isinstance(amount, dict):
            return str(amount)
        if amount.get("kind") == "fixed":
            return str(amount.get("value") or 0)
        dice = amount.get("dice") or {}
        return f"{dice.get('count', 1)}D{dice.get('sides', 6)}"

    # 04 · sell wyrdstone ---------------------------------------------------

    def _sell_wyrdstone(self, parent: tk.Misc, _battle) -> None:
        engine = self._engine()
        resolver = self.controller.post_battle_resolver()
        post = engine.post
        self._title(parent, tr('04 · Sell Wyrdstone'), tr('Choose how many shards to sell. This action can only be performed once in the post-battle sequence; the sale value comes from the KB pricing table (warband size × shards sold). {}').format(self._kb_provenance(3)))
        if post is None:
            return
        available = engine.projected_shards()
        if post.sale_resolved:
            SummaryStrip(parent, [(tr('Sale resolved'), tr('once per sequence')), (tr('Shards sold'), str(post.wyrdstone_sold)), (tr('Shards remaining'), str(available))]).pack(fill="x", pady=(0, 12))
            return
        SummaryStrip(parent, [(tr('In hoard'), str(available)), (tr('Sell now'), tr('choose below')), (tr('Income'), tr('KB pricing table'))]).pack(fill="x", pady=(0, 12))
        card = self._section(parent, tr('Choose quantity to sell'), tr('The table value is calculated from the current warband size and the fragments sold.'))
        row = tk.Frame(card, bg=COLORS["panel_alt"])
        row.pack(fill="x")
        tk.Label(row, text=tr('Wyrdstone shards'), bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(side="left")
        self._sell_var = tk.IntVar(value=int(self._sell_state.get("quantity", min(1, available))))
        ttk.Spinbox(row, from_=0, to=available, width=5, textvariable=self._sell_var).pack(side="left", padx=12)
        value_var = tk.StringVar()
        tk.Label(row, textvariable=value_var, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(side="left", padx=(4, 12))
        def update_value(*_args) -> None:
            try:
                quantity = max(0, min(available, int(self._sell_var.get())))
            except (ValueError, tk.TclError):
                quantity = 0
            value_var.set(f"{resolver.wyrdstone_sale_value(quantity, engine.projected_warband_members())} gc")
            self._sell_state["quantity"] = quantity
        self._sell_var.trace_add("write", update_value)
        update_value()
        tk.Label(card, text=tr('Selling zero shards is allowed: it closes the once-per-sequence action.'), bg=COLORS["panel_alt"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(anchor="w", pady=(9, 0))

    # 05 · veterans ---------------------------------------------------------

    def _veterans(self, parent: tk.Misc, _battle) -> None:
        engine = self._engine()
        self._title(parent, tr('05 · Available Veterans'), tr('Determine the post-battle experience pool available for hiring experienced recruits. You are not committing to hire anyone yet. {}').format(self._kb_provenance(4)))
        post = engine.post
        holder = self._pending_veterans
        pool = post.veteran_pool if post is not None else 0
        DiceResolutionCard(
            parent, title=tr('Veteran Experience Pool'), subtitle=tr('Availability check before recruitment · current pool {} XP').format(pool),
            notation="2D6", dice_count=2, demo_dice=(4, 3), combine="sum",
            outcome_title=tr('Pool rolled'), outcome_detail=tr('This pool is used later in Recruitment'),
            on_resolved=lambda dice, _x=holder: self.controller.perform_undoable(
                tr('Veteran experience roll'),
                lambda: (_x.update(dice=list(dice)), tr('{} XP available').format(sum(dice)), tr('Veteran pool of {} XP').format(sum(dice)), "accent")[1:]),
            outcome_actions=(),
        ).pack(fill="x")

    # 06 · rare items & dramatis --------------------------------------------

    def _rare_and_dramatis(self, parent: tk.Misc, _battle) -> None:
        content = self.controller.post_battle_content()
        resolver = self.controller.post_battle_resolver()
        rare = list(content.rare_items())
        dramatis = list(content.dramatis_personae())
        heroes = [warrior for warrior in self.controller.state.campaign.warriors if warrior.kind == "hero"]
        self._title(
            parent,
            tr('06 · Rare Items & Dramatis'),
            tr('Assign each available Hero to one rare item or Dramatis search. A Hero can perform at most one search in this sequence. {}').format(self._kb_provenance(5)),
        )
        section = self._section(
            parent, tr('HERO SEARCH ASSIGNMENTS'),
            tr('{} Heroes available · {} rare items · {} Dramatis Personae').format(len(heroes), len(rare), len(dramatis)),
        )
        post = self._post
        no_search = tr('No search')
        targets = {no_search: ("none", None)}
        identity_label: dict[str, str] = {}
        for offer in rare:
            label = f"{tr('RARE ITEM')} · {offer.name} · {tr('Rare')} {offer.rarity}"
            targets[label] = ("rare", offer)
            identity_label[f"rare:{offer.item_id}"] = label
        for offer in dramatis:
            marker = " *" if offer.eligibility != "eligible" else ""
            label = f"DRAMATIS · {offer.name}{marker}"
            targets[label] = ("dramatis", offer)
            identity_label[f"dramatis:{offer.profile_id}"] = label
        if not heroes:
            tk.Label(section, text=tr('No Heroes are currently available to search.'), bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
            return
        for hero in heroes:
            card = tk.Frame(section, bg=COLORS["panel_alt"], pady=5)
            card.pack(fill="x")
            row = tk.Frame(card, bg=COLORS["panel_alt"])
            row.pack(fill="x")
            tk.Label(row, text=hero.name, width=24, anchor="w", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI Semibold", 8)).pack(side="left")
            variable = self._search_assignments.setdefault(hero.id, tk.StringVar(value=no_search))
            record = post.searches.get(hero.id) or {}
            if record.get("target_id") and variable.get() == no_search:
                variable.set(identity_label.get(str(record["target_id"]), no_search))
            picker = ttk.Combobox(row, state="readonly", textvariable=variable, values=list(targets), width=55)
            picker.pack(side="left", fill="x", expand=True)
            result_host = tk.Frame(card, bg=COLORS["panel_alt"])
            result_host.pack(fill="x")
            picker.bind("<<ComboboxSelected>>", lambda _event, h=hero, v=variable, host=result_host: self._select_hero_search(h, v, host, targets, resolver))
            if variable.get() != no_search:
                self._render_hero_search(hero, variable, result_host, targets, resolver, reset=False)

    def _render_hero_search(self, hero, variable, host, targets, resolver, *, reset: bool = True) -> None:
        for child in host.winfo_children():
            child.destroy()
        kind, offer = targets.get(variable.get(), ("none", None))
        holder = self._post.searches.setdefault(hero.id, {})
        if reset:
            holder.clear()
            if kind == "rare":
                jewel_bonus = 1 if any("+1 to rolls for locating rare items" in rule for rule in hero.special_rules) else 0
                holder.update(kind="rare", target_id=f"rare:{offer.item_id}", item_id=offer.item_id,
                              label=variable.get(), modifiers=jewel_bonus, hero_id=hero.id)
            elif kind == "dramatis":
                holder.update(kind="dramatis", target_id=f"dramatis:{offer.profile_id}", profile_id=offer.profile_id, label=variable.get(), modifiers=0, hero_id=hero.id)
        if kind == "none":
            return
        if holder.get("dice"):
            status = tr('Consumed') if holder.get("used") else (tr('Available') if holder.get("success") else tr('Not found'))
            tk.Label(host, text=f"{offer.name} · {status}", bg=COLORS["panel_alt"],
                     fg=COLORS["success"] if holder.get("success") else COLORS["muted"],
                     font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(7, 0))
            if holder.get("success") and not holder.get("used"):
                command = (lambda o=offer, h=holder: self._buy_rare_offer(o, h)) if kind == "rare" else (
                    lambda o=offer, h=holder: self._hire_dramatis(o, h))
                ttk.Button(host, text=tr('BUY') if kind == "rare" else tr('HIRE'),
                           style="Accent.TButton", command=command).pack(anchor="e", pady=(5, 0))
            return
        if kind == "rare":
            DiceResolutionCard(
                host, title=offer.name, subtitle=tr('{} searches for a Rare {} item').format(hero.name, offer.rarity),
                notation="2D6", dice_count=2, demo_dice=(5, 4), combine="sum",
                outcome_title=tr('Rare item search'), outcome_detail=tr('Resolve the roll to test the selected item.'),
                on_resolved=lambda dice, o=offer, h=holder: self.controller.perform_undoable(
                    tr('Rare item search roll'), lambda: _rarity_card(dice, resolver, o.item_id, o.name, h)),
                outcome_actions=(("BUY", lambda o=offer, h=holder: self._buy_rare_offer(o, h), "Accent.TButton"),),
            ).pack(fill="x", pady=(7, 0))

        else:
            DiceResolutionCard(
                host, title=offer.name, subtitle=tr('{} searches for this Dramatis Persona').format(hero.name),
                notation="D6", dice_count=1, demo_dice=(3,), combine="sum",
                outcome_title=tr('Dramatis search'), outcome_detail=tr('Resolve the roll to locate the character. For conditional entries the acceptance roll reuses the same die.'),
                on_resolved=lambda dice, h=holder: self.controller.perform_undoable(
                    tr('Dramatis search roll'),
                    lambda: (h.update(dice=list(dice), success=True), tr('Located'), tr('Character found · hiring remains optional'), "success")[1:]),
                outcome_actions=(("HIRE", lambda o=offer, h=holder: self._hire_dramatis(o, h), "Accent.TButton"),),
            ).pack(fill="x", pady=(7, 0))

    def _select_hero_search(self, hero, variable, host, targets, resolver) -> None:
        """Store a search target as a proper undoable campaign action."""
        selected = variable.get()

        def change() -> tuple[bool, str]:
            kind, offer = targets.get(selected, ("none", None))
            holder = self._post.searches.setdefault(hero.id, {})
            holder.clear()
            if kind == "rare":
                jewel_bonus = 1 if any("+1 to rolls for locating rare items" in rule for rule in hero.special_rules) else 0
                holder.update(kind="rare", target_id=f"rare:{offer.item_id}", item_id=offer.item_id,
                              label=selected, modifiers=jewel_bonus, hero_id=hero.id)
            elif kind == "dramatis":
                holder.update(kind="dramatis", target_id=f"dramatis:{offer.profile_id}", profile_id=offer.profile_id,
                              label=selected, modifiers=0, hero_id=hero.id)
            return True, f"{hero.name}: {selected}"

        self.controller.perform_undoable(tr('Choose search target'), change)
        self._render_hero_search(hero, variable, host, targets, resolver, reset=False)

    def _buy_rare_offer(self, offer, holder: dict) -> None:
        if holder.get("used"):
            self._status_text = tr('⚠ This successful search has already been used.')
            return
        if not holder.get("success"):
            self._status_text = tr('⚠ The rarity test failed; the item is not available to buy.')
            return
        engine = self._engine()
        if offer.price_dice is not None:
            from mordheim_campaign.ui.dialogs.variable_price import VariablePriceDialog

            VariablePriceDialog(
                self, offer=offer,
                buy=lambda price: self.controller.perform_undoable(
                    tr('Buy rare item'), lambda: self._consume_rare_purchase(holder, lambda: engine.buy_item(
                        offer.item_id, 1, price, category=offer.category, rarity=offer.rarity,
                    ))),
            )
            return
        if offer.price_upgrade_multiplier is not None:
            from mordheim_campaign.ui.dialogs.variable_price import UpgradePriceDialog

            UpgradePriceDialog(
                self, offer=offer, campaign=self.controller.state.campaign,
                weapon_hands=self.controller.port.weapon_hands,
                buy=lambda price, target: self.controller.perform_undoable(
                    tr('Upgrade weapon'), lambda: self._consume_rare_purchase(
                        holder, lambda: engine.buy_weapon_upgrade(offer, target.id, price))),
            )
            return
        self._run(lambda: self._consume_rare_purchase(holder, lambda: engine.buy_item(
            offer.item_id, 1, offer.price_gc, category=offer.category, rarity=offer.rarity,
        )))

    @staticmethod
    def _consume_rare_purchase(holder: dict, purchase) -> tuple[bool, str]:
        if holder.get("used"):
            return False, "This successful search has already been used."
        result = purchase()
        if result[0]:
            holder["used"] = True
        return result

    def _hire_dramatis(self, offer, holder: dict) -> None:
        if holder.get("used"):
            self._status_text = tr('⚠ This successful search has already been used.')
            return
        dice = holder.get("dice")
        acceptance = int(dice[0]) if (offer.eligibility == "conditional" and dice) else None
        self._run(lambda: self._consume_rare_purchase(
            holder, lambda: self._engine().hire_hireling(offer, acceptance_roll=acceptance)))

    # 07 · recruitment ------------------------------------------------------

    def _recruitment(self, parent: tk.Misc, _battle) -> None:
        engine = self._engine()
        campaign = self.controller.state.campaign
        self._title(
            parent,
            tr('07 · Recruitment'),
            tr('Hire or dismiss warriors and Hired Swords. Equipment purchases and assignments are handled in the next step. {}').format(self._kb_provenance(6)),
        )
        post = engine.post
        SummaryStrip(parent, [
            (tr('Treasury'), f"{engine.projected_gold()} gc"),
            ("Veteran pool", f"{post.veteran_pool if post else 0} XP"),
            (tr('Models'), f"{engine.projected_warband_members()}/{engine.effective_maximum_models()}"),
        ]).pack(fill="x", pady=(0, 12))

        toolbar = tk.Frame(parent, bg=COLORS["bg"])
        toolbar.pack(fill="x", pady=(0, 8))
        SegmentedTabs(
            toolbar,
            (
                ("hero", tr('HEROES')),
                ("henchman", tr('HENCHMEN')),
                ("hireling", tr('HIRED SWORDS')),
            ),
            self._recruitment_tab,
            self._set_recruitment_tab,
            prominent=True,
        ).pack(side="left")
        action = tr('+ HIRE SWORD') if self._recruitment_tab == "hireling" else (
            tr('+ ADD HERO') if self._recruitment_tab == "hero" else tr('+ ADD HENCHMAN GROUP')
        )
        ttk.Button(toolbar, text=action, style="Accent.TButton", command=self._open_recruitment_menu).pack(side="right")

        current = [row for row in campaign.warriors if row.kind == self._recruitment_tab]
        if not current:
            empty = self._section(parent, tr('CURRENT ROSTER'), tr('No recruits of this type are currently in the warband.'))
            ttk.Button(empty, text=action, style="Accent.TButton", command=self._open_recruitment_menu).pack(anchor="w")
        else:
            for warrior in current:
                DraftWarriorCard(parent, warrior, on_more=self._recruitment_warrior_menu(warrior)).pack(fill="x", pady=(0, 8))

        if self._recruitment_tab == "henchman":
            pending = []
            for warrior in current:
                for item in warrior.equipment:
                    missing = warrior.quantity - item.quantity if item.per_model and item.transferable else 0
                    if missing > 0:
                        pending.append(f"{warrior.name}: {missing}× {item.name}")
            if pending:
                warning = self._section(
                    parent, tr('EQUIPMENT PENDING'),
                    tr('These requirements will be purchased or assigned during the Equipment step.'),
                )
                tk.Label(warning, text="\n".join(pending), bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8), justify="left").pack(anchor="w")

    def _set_recruitment_tab(self, tab: str) -> None:
        self._recruitment_tab = tab
        self._rebuild()

    def _available_recruitment_profiles(self):
        engine = self._engine()
        return [profile for profile, allowed, _reason in engine.recruitment_eligibility(self._recruitment_tab) if allowed]

    def _open_recruitment_menu(self) -> None:
        menu = tk.Menu(self, tearoff=False, bg=COLORS["panel"], fg=COLORS["text"], activebackground=COLORS["panel_soft"], activeforeground=COLORS["text"])
        if self._recruitment_tab == "hireling":
            offers = [row for row in self.controller.post_battle_content().hired_swords() if row.eligibility == "eligible"]
            for offer in offers:
                if offer.fee_dice is not None:
                    menu.add_command(
                        label=f"{offer.name}  ·  {offer.fee_label}",
                        command=lambda o=offer: self._open_hireling_fee(o),
                    )
                else:
                    menu.add_command(label=f"{offer.name}  ·  {offer.fee_label}", command=lambda o=offer: self._run(lambda: self._engine().hire_hireling(o)))
        else:
            for profile in self._available_recruitment_profiles():
                menu.add_command(label=f"{profile.name}  ·  {profile.cost} gc", command=lambda p=profile: self._recruit_profile(p))
        if menu.index("end") is None:
            menu.add_command(label=tr('No recruits available'), state="disabled")
        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    def _open_hireling_fee(self, offer) -> None:
        """Variable hiring fee: roll the declared dice, then hire."""
        from mordheim_campaign.ui.dialogs.variable_price import HirelingFeeDialog

        HirelingFeeDialog(
            self, offer=offer,
            hire=lambda fee_roll: self._engine().hire_hireling(offer, fee_roll=fee_roll),
        )

    def _recruitment_warrior_menu(self, warrior):
        def popup() -> None:
            menu = tk.Menu(self, tearoff=False, bg=COLORS["panel"], fg=COLORS["text"], activebackground=COLORS["panel_soft"], activeforeground=COLORS["text"])
            if warrior.kind != "hireling":
                menu.add_command(label=tr('Edit skills…'), command=lambda: self._edit_manual_skills(warrior))
                menu.add_separator()
            if warrior.kind == "henchman":
                menu.add_command(label=tr('+ 1 member'), command=lambda: self._confirm_group_recruit(warrior))
                menu.add_command(label=tr('Dismiss 1 member'), command=lambda: self._confirm_dismiss(warrior, one_member=True))
                menu.add_separator()
            menu.add_command(label=tr('Dismiss warrior / group'), command=lambda: self._confirm_dismiss(warrior))
            try:
                menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
            finally:
                menu.grab_release()
        return popup

    def _edit_manual_skills(self, warrior) -> None:
        from mordheim_campaign.ui.dialogs.manual_management import ManualSkillsDialog
        ManualSkillsDialog(self, self.controller, warrior)

    def _confirm_group_recruit(self, warrior) -> None:
        ok, result = self._engine().group_recruitment_quote(warrior.id)
        if not ok:
            messagebox.showerror(tr('Cannot recruit'), str(result), parent=self)
            return
        reqs = result["requirements"]
        lines = [tr('Recruit: {} gc').format(result["recruit_cost"]), tr('Veteran Experience: {} XP').format(result["required_xp"])]
        if result.get("experience_gc"):
            lines.append(tr('Experience cost: {} gc').format(result["experience_gc"]))
        if reqs:
            lines.append("")
            lines.append(tr('Equipment required in the next step:'))
            for row in reqs:
                source = tr('from stash') if row["in_stash"] else tr('{} gc to buy').format(row["unit_cost"])
                lines.append(f"• 1× {row['name']} · {source}")
            lines.append(tr('Estimated equipment purchases: {} gc').format(result["equipment_cost"]))
        if messagebox.askyesno(tr('Add group member'), "\n".join(lines), parent=self):
            self._run(lambda: self._engine().add_member_to_group(warrior.id))

    def _confirm_dismiss(self, warrior, *, one_member: bool = False) -> None:
        label = tr('one member of {}').format(warrior.name) if one_member and warrior.quantity > 1 else warrior.name
        detail = tr('Dismiss {}? Transferable equipment will return to the stash; restricted starting equipment leaves with the recruit.').format(label)
        if messagebox.askyesno(tr('Confirm dismissal'), detail, parent=self):
            self._run(lambda: self._engine().dismiss_warrior(warrior.id, one_member=one_member))

    def _recruit_profile(self, profile) -> None:
        base = profile.name if profile.kind == "hero" else f"{profile.name} Group"
        name = simpledialog.askstring(tr('Name warrior or group'), tr('Name'), initialvalue=base, parent=self)
        if name is None:
            return
        self._run(lambda: self._engine().recruit_band_profile(profile.profile_id, 1, name))

    # 08 · equipment --------------------------------------------------------

    def _equipment(self, parent: tk.Misc, _battle) -> None:
        engine = self._engine()
        campaign = self.controller.state.campaign
        self._title(
            parent,
            tr('08 · Equipment'),
            tr('Buy and sell equipment, then drag items between the stash and warriors. Rare items found earlier remain available and are highlighted. {}').format(self._kb_provenance(7)),
        )
        owned = sum(item.owned for item in campaign.inventory)
        equipped = sum(item.equipped for item in campaign.inventory)
        available = sum(item.stash for item in campaign.inventory)
        rare = sum(item.stash for item in campaign.inventory if item.rarity)
        SummaryStrip(parent, [
            (tr('Treasury'), f"{engine.projected_gold()} gc"),
            (tr('Owned'), str(owned)),
            (tr('Equipped'), str(equipped)),
            (tr('In stash'), str(available)),
            (tr('Rare finds'), str(rare)),
        ]).pack(fill="x", pady=(0, 8))
        obligations = [row for row in (engine.post.equipment_obligations if engine.post else [])]
        if obligations:
            box = self._section(
                parent, tr('EQUIPMENT OBLIGATIONS'),
                tr('Members recruited this sequence still need this equipment.'),
            )
            for row in obligations:
                tk.Label(
                    box,
                    text=tr('{}: {}× {}').format(row.get("item_name") or row.get("item_id"), row.get("quantity"), tr('pending')),
                    bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8),
                ).pack(anchor="w")
        InventoryWorkspace(parent, self.controller, show_summary=False, purchase_mode="post_battle").pack(fill="both", expand=True)

    def _follow_ups(self, parent: tk.Misc, post) -> None:
        """Pending follow-up actions of the active step, with acknowledgement."""
        pending = post.follow_ups_for_step(post.active_step)
        if post.active_step == 2:
            pending = [row for row in pending if row.get("type") != "exploration_followup"]
        if not pending:
            return
        section = self._section(parent, tr('PENDING FOLLOW-UPS'), tr('Resolve every required effect before continuing.'))
        for row in pending:
            row_frame = tk.Frame(section, bg=COLORS["panel_alt"])
            row_frame.pack(fill="x", pady=2)
            done = post.is_acknowledged(post.active_step, str(row.get("id")))
            marker = "✓ " if done else "• "
            tk.Label(
                row_frame, text=marker + str(row.get("description") or row.get("id")),
                bg=COLORS["panel_alt"], fg=COLORS["muted"] if done else COLORS["text"],
                font=("Segoe UI", 8), wraplength=760, justify="left",
            ).pack(side="left", fill="x", expand=True)
            if not done:
                if row.get("type") == "injury_followup":
                    ttk.Button(
                        row_frame, text=tr('RESOLVE…'), style="Accent.TButton",
                        command=lambda r=row: self._resolve_injury_followup(r),
                    ).pack(side="right", padx=(0, 6))
                elif row.get("type") == "encounter" and row.get("encounter_id") == "campaign.encounter.sold-to-the-pits":
                    ttk.Button(
                        row_frame, text=tr('WON'), style="Accent.TButton",
                        command=lambda r=row: self._resolve_sold_to_pits(r, won=True),
                    ).pack(side="right", padx=(0, 6))
                    ttk.Button(
                        row_frame, text=tr('LOST'), style="Mini.TButton",
                        command=lambda r=row: self._resolve_sold_to_pits(r, won=False),
                    ).pack(side="right", padx=(0, 6))
                elif row.get("type") == "prisoner":
                    ttk.Button(
                        row_frame, text=tr('LOST'), style="Mini.TButton",
                        command=lambda r=row: self._resolve_captured(r, "lost"),
                    ).pack(side="right", padx=(0, 6))
                    ttk.Button(
                        row_frame, text=tr('EXCHANGED'), style="Mini.TButton",
                        command=lambda r=row: self._resolve_captured(r, "exchange"),
                    ).pack(side="right", padx=(0, 6))
                    ttk.Button(
                        row_frame, text=tr('RANSOM…'), style="Accent.TButton",
                        command=lambda r=row: self._resolve_captured(r, "ransom"),
                    ).pack(side="right", padx=(0, 6))
                elif row.get("type") == "relationship":
                    ttk.Button(
                        row_frame, text=tr('SET TARGET…'), style="Accent.TButton",
                        command=lambda r=row: self._resolve_hatred_target(r),
                    ).pack(side="right", padx=(0, 6))
                elif row.get("type") == "eye_injury":
                    ttk.Button(row_frame, text=tr('RIGHT EYE'), style="Mini.TButton", command=lambda r=row: self._resolve_eye(r, "right")).pack(side="right", padx=(0, 6))
                    ttk.Button(row_frame, text=tr('LEFT EYE'), style="Accent.TButton", command=lambda r=row: self._resolve_eye(r, "left")).pack(side="right", padx=(0, 6))
                elif row.get("type") == "hireling_upkeep":
                    ttk.Button(row_frame, text=tr('DISMISS'), style="Mini.TButton",
                               command=lambda r=row: self._run(lambda: self._engine().resolve_hireling_upkeep(str(r.get("id")), pay=False))).pack(side="right", padx=(0, 6))
                    ttk.Button(row_frame, text=tr('PAY UPKEEP'), style="Accent.TButton",
                               command=lambda r=row: self._run(lambda: self._engine().resolve_hireling_upkeep(str(r.get("id")), pay=True))).pack(side="right", padx=(0, 6))
                elif row.get("type") == "scenario_spell_reward":
                    ttk.Button(row_frame, text=tr('CHOOSE HERO AND SPELLS…'), style="Accent.TButton",
                               command=lambda r=row: self._resolve_tome_of_magic(r)).pack(side="right", padx=(0, 6))
                elif row.get("type") == "scenario_encampment":
                    ttk.Button(row_frame, text=tr('OCCUPY'), style="Accent.TButton",
                               command=lambda r=row: self._run(lambda: self._engine().resolve_scenario_encampment(str(r.get("id")), "occupy"))).pack(side="right", padx=(0, 6))
                    ttk.Button(row_frame, text=tr('DESTROY'), style="Mini.TButton",
                               command=lambda r=row: self._run(lambda: self._engine().resolve_scenario_encampment(str(r.get("id")), "destroy"))).pack(side="right", padx=(0, 6))
                elif row.get("type") == "exploration_followup":
                    ttk.Button(
                        row_frame, text=tr('RESOLVE…'), style="Accent.TButton",
                        command=lambda r=row: self._resolve_exploration_followup(r),
                    ).pack(side="right", padx=(0, 6))
                interactive = {"prisoner", "relationship", "eye_injury", "hireling_upkeep", "injury_followup", "exploration_followup", "scenario_spell_reward", "scenario_encampment"}
                if row.get("type") not in interactive and not (row.get("type") == "encounter" and row.get("encounter_id") == "campaign.encounter.sold-to-the-pits"):
                    ttk.Button(
                        row_frame, text=tr('RESOLVED AT THE TABLE'), style="Mini.TButton",
                        command=lambda r=row: self._acknowledge_follow_up(r),
                    ).pack(side="right")

    def _resolve_injury_followup(self, row) -> None:
        """Ask the subtable/repeat die and apply the follow-up outcome."""
        engine = self._engine()
        count = int(row.get("dice_count") or 1)
        sides = int(row.get("dice_sides") or 6)
        roll = self._ask_roll(count, sides, str(row.get("description") or "follow-up"))
        if roll is None:
            return
        self._run(lambda: engine.resolve_injury_followup(str(row.get("id")), roll))

    def _ask_roll(self, count: int, sides: int, title: str) -> int | None:
        dice = ask_dice(self, title=title, dice_count=count, dice_sides=sides)
        return sum(dice) if dice else None

    def _resolve_sold_to_pits(self, row: dict, *, won: bool) -> None:
        roll = None
        if not won:
            dice = ask_dice(
                self,
                title=tr('Serious injury after losing in the pits'),
                dice_count=2,
                dice_sides=6,
            )
            if not dice:
                return
            roll = 10 * dice[0] + dice[1]
        self._run(lambda: self._engine().resolve_sold_to_pits(str(row.get("id")), won=won, injury_roll=roll))

    def _resolve_captured(self, row: dict, resolution: str) -> None:
        ransom = 0
        disposition = "other"
        if resolution == "ransom":
            value = simpledialog.askinteger(
                tr('Ransom'), tr('Gold crowns paid to the captor:'), parent=self,
                initialvalue=0, minvalue=0,
            )
            if value is None:
                return
            ransom = value
        elif resolution == "lost":
            disposition = self._choose_capture_disposition()
            if not disposition:
                return
        self._run(lambda: self._engine().resolve_captured(
            str(row.get("id")), resolution=resolution, ransom=ransom, disposition=disposition,
        ))

    def _choose_capture_disposition(self) -> str:
        dialog = tk.Toplevel(self)
        dialog.configure(bg=COLORS["bg"]); dialog.title(tr('Captured warrior'))
        dialog.transient(self.winfo_toplevel()); dialog.grab_set(); dialog.resizable(False, False)
        panel = tk.Frame(dialog, bg=COLORS["panel"], padx=16, pady=14); panel.pack(padx=1, pady=1)
        tk.Label(panel, text=tr('WHAT HAPPENED TO THE CAPTURED WARRIOR?'), bg=COLORS["panel"],
                 fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 9))
        result = []
        choices = (
            ("enslaved", tr('SOLD INTO SLAVERY')), ("executed", tr('EXECUTED')),
            ("zombie", tr('RAISED AS A ZOMBIE')), ("sacrificed", tr('SACRIFICED')),
            ("other", tr('OTHER PERMANENT LOSS')),
        )
        for value, label in choices:
            ttk.Button(panel, text=label, command=lambda choice=value: (result.append(choice), dialog.destroy())).pack(fill="x", pady=2)
        ttk.Button(panel, text=tr('CANCEL'), command=dialog.destroy).pack(fill="x", pady=(8, 0))
        dialog.bind("<Escape>", lambda _e: dialog.destroy())
        dialog.after_idle(lambda: center_on_application(dialog)); dialog.wait_window()
        return result[0] if result else ""

    def _resolve_hatred_target(self, row: dict) -> None:
        selector = str(row.get("target_selector") or "").replace("_", " ")
        target = simpledialog.askstring(
            tr('Bitter Enmity'),
            tr('Enter the specific hated target required by this result ({}):').format(selector),
            parent=self,
        )
        if target is None:
            return
        self._run(lambda: self._engine().resolve_hatred_target(str(row.get("id")), target))

    def _resolve_eye(self, row: dict, eye: str) -> None:
        self._run(lambda: self._engine().resolve_lost_eye(str(row.get("id")), eye))

    def _resolve_tome_of_magic(self, row: dict) -> None:
        engine = self._engine()
        heroes = [warrior for warrior in engine.campaign.warriors if warrior.kind == "hero"]
        if not heroes:
            return
        dialog = tk.Toplevel(self); dialog.configure(bg=COLORS["panel"])
        dialog.title(tr('Tome of Magic')); dialog.transient(self.winfo_toplevel()); dialog.grab_set()
        tk.Label(dialog, text=tr('Choose a Hero and exactly two spells.'), bg=COLORS["panel"], fg=COLORS["text"],
                 font=("Segoe UI Semibold", 9)).pack(anchor="w", padx=16, pady=(14, 7))
        hero_var = tk.StringVar(value=heroes[0].name)
        hero_box = ttk.Combobox(dialog, state="readonly", values=[hero.name for hero in heroes],
                                textvariable=hero_var, width=42)
        hero_box.pack(fill="x", padx=16)
        spells = tk.Listbox(dialog, selectmode="multiple", exportselection=False, width=58, height=12,
                            bg=COLORS["entry"], fg=COLORS["text"], selectbackground=COLORS["accent"],
                            selectforeground=COLORS["black"], bd=0)
        spells.pack(fill="both", expand=True, padx=16, pady=8)
        option_rows = []

        def refresh(_event=None) -> None:
            nonlocal option_rows
            hero = heroes[[value.name for value in heroes].index(hero_var.get())]
            option_rows = list(engine.scenario_spell_options(hero.id))
            spells.delete(0, "end")
            for option in option_rows:
                known = str(option.get("name") or "") in hero.skills
                spells.insert("end", f"{'✓ ' if known else ''}{option.get('name')}  ·  {str(option.get('lore_id')).replace('lore.', '').replace('-', ' ').title()}")
                if known: spells.itemconfig("end", fg=COLORS["muted"])

        def confirm() -> None:
            hero = heroes[[value.name for value in heroes].index(hero_var.get())]
            ids = [str(option_rows[index].get("id") or "") for index in spells.curselection()]
            ok, message = self.controller.perform_undoable(
                tr('Assign scenario spell reward'),
                lambda: engine.resolve_scenario_spell_reward(str(row.get("id")), hero.id, ids))
            if not ok:
                messagebox.showerror(tr('Cannot apply result'), tr_message(message), parent=dialog); return
            dialog.destroy(); self._status_text = "✓ " + message; self._rebuild()

        hero_box.bind("<<ComboboxSelected>>", refresh); refresh()
        ttk.Button(dialog, text=tr('CONFIRM'), style="Accent.TButton", command=confirm).pack(anchor="e", padx=16, pady=(0, 14))
        dialog.after_idle(lambda: center_on_application(dialog))

    def _resolve_exploration_followup(self, row) -> None:
        """Interactive resolution of the KB exploration special result."""
        engine = self._engine()
        pending = engine.exploration_followup_pending()
        while pending is not None:
            if pending.get("kind") == "choose_hero":
                hero_id = self._choose_hero(pending.get("label") or tr('Choose a Hero'))
                if hero_id is None:
                    return
                ok, message = self.controller.perform_undoable(
                    tr('Resolve Exploration event'),
                    lambda: engine.advance_exploration_followup(hero_id=hero_id))
            else:
                count = int(pending.get("dice_count") or 1)
                sides = int(pending.get("dice_sides") or 6)
                roll = self._ask_roll(count, sides, str(pending.get("label") or tr('Follow-up roll')))
                if roll is None:
                    return
                ok, message = self.controller.perform_undoable(
                    tr('Exploration event roll'),
                    lambda: engine.advance_exploration_followup(roll=roll))
            if not ok:
                messagebox.showerror(tr('Cannot apply result'), tr_message(message), parent=self)
                return
            pending = engine.exploration_followup_pending()
        self._status_text = "✓ " + tr('Exploration follow-up resolved.')
        self._rebuild()

    def _choose_hero(self, title: str) -> str | None:
        heroes = [w for w in self.controller.state.campaign.warriors if w.kind == "hero"]
        if not heroes:
            return None
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        tk.Label(dialog, text=title, bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 10)).pack(padx=18, pady=(14, 6))
        var = tk.StringVar(value=heroes[0].id)
        for hero in heroes:
            ttk.Radiobutton(dialog, text=hero.name, value=hero.id, variable=var).pack(anchor="w", padx=18)
        result: list[str] = []

        def _ok() -> None:
            result.append(var.get())
            dialog.destroy()

        ttk.Button(dialog, text=tr('OK'), style="Accent.TButton", command=_ok).pack(pady=(6, 12))
        dialog.after_idle(lambda: center_on_application(dialog))
        dialog.wait_window()
        return result[0] if result else None

    def _acknowledge_follow_up(self, row) -> None:
        self._post.acknowledge(self._post.active_step, str(row.get("id")))
        self._rebuild()

    # ------------------------------------------------------------- final review

    def _review(self, parent: tk.Misc, battle) -> None:
        engine = self._engine()
        projections = engine.projections()
        base = engine._base_state()
        self._title(parent, tr('Final Review'), tr('All eight player actions are complete. This confirmation creates State #{}; warband rating is calculated automatically from the final roster. {}').format(battle.number, self._kb_provenance(0)))
        SummaryStrip(parent, [
            (tr('Rating'), f"{base.rating if base else '—'} → {projections['rating']}"),
            (tr('Models'), f"{base.models if base else '—'} → {projections['models']}"),
            (tr('Treasury'), f"{base.gold if base else '—'} → {projections['gold']} gc"),
            ("Wyrdstone", f"{base.wyrdstone if base else '—'} → {projections['shards']}"),
        ]).pack(fill="x", pady=(0, 12))
        for title, lines in (
            (tr('RECOVERY'), [tr('Injuries applied'), tr('Experience total {} XP').format(projections['experience'])]),
            (tr('EXPLORATION & INCOME'), ["Exploration resolved", tr('Wyrdstone sale resolved once')]),
            (tr('SEARCHES'), [tr('Veteran pool: {} XP').format(engine.post.veteran_pool if engine.post else 0), tr('Rare items and Dramatis searches resolved')]),
            (tr('WARBAND'), [tr('Recruitment complete'), tr('Equipment reallocated'), "Rating recalculated automatically"]),
        ):
            tk.Label(parent, text=title, bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(6, 3))
            for line in lines:
                tk.Label(parent, text=f"• {line}", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(anchor="w", padx=(8, 0), pady=1)

    def _save_and_close(self) -> None:
        """Saves the campaign (with the pending post-battle) and returns to the current state."""
        from mordheim_campaign.ui.file_actions import save_current_campaign

        if save_current_campaign(self, self.controller) is not None:
            self.controller.go_to_current_state()

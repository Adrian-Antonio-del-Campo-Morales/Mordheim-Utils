from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.state import POST_BATTLE_GROUPS, POST_BATTLE_STEPS
from mordheim_campaign.ui.components import DiceResolutionCard, PostBattleSequence
from mordheim_ui.i18n import tr
from mordheim_ui.theme import COLORS
from mordheim_ui.widgets import BorderedFrame, ExperienceTrack, ScrollableFrame, SummaryStrip


def _injury_card(dice: list[int], resolver, *, hero: bool) -> tuple[str, str, str]:
    """Live KB resolution for an injury card's roll."""
    outcome = (resolver.resolve_hero_serious_injury(10 * dice[0] + dice[1]) if hero
               else resolver.resolve_henchman_serious_injury(dice[0]))
    parts = list(outcome.effects)
    if outcome.follow_up:
        parts.append(outcome.follow_up)
    detail = " · ".join(parts) or "No lasting effect."
    tone = "danger" if outcome.result in ("Dead", "Removed", "Multiple Injuries") else "accent"
    return outcome.result, detail, tone


def _injury_store(dice: list[int], resolver, *, hero: bool, holder: dict) -> tuple[str, str, str]:
    holder["dice"] = list(dice)
    return _injury_card(dice, resolver, hero=hero)


def _exploration_card(dice: list[int], resolver) -> tuple[str, str, str]:
    """Live KB resolution of an exploration roll."""
    resolved = resolver.resolve_exploration(tuple(dice))
    detail = f"Total {resolved.total} → {resolved.shards} wyrdstone shard(s)"
    if resolved.matching_dice_note:
        detail += f" · {resolved.matching_dice_note}"
    return f"Exploration resolved · {resolved.shards} shard(s)", detail, "accent"


def _exploration_store(dice: list[int], resolver, holder: dict) -> tuple[str, str, str]:
    holder["dice"] = list(dice)
    return _exploration_card(dice, resolver)


def _rarity_card(dice: list[int], resolver, item_id: str, name: str, holder: dict) -> tuple[str, str, str]:
    """Live KB rarity-test resolution for a rare-item search."""
    search = resolver.resolve_rarity_search(item_id, sum(dice))
    holder["dice"] = list(dice)
    holder["success"] = search.success
    title = "Available" if search.success else "Not found"
    tone = "success" if search.success else "neutral"
    return title, f"{name}: {search.note}", tone


def _selected_index(labels: list[str], picker) -> int:
    try:
        return max(0, labels.index(picker.get()))
    except ValueError:
        return 0


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
        self._status_text = ""
        self._applied_injuries: set[str] = set()
        post = controller.state.campaign.post_battle(number)
        if post.complete:
            self._build_completed(post)
        else:
            self._build_pending(post)

    # ------------------------------------------------------------- scaffolding

    def _rebuild(self) -> None:
        """Rebuilds the current step in place, preserving scroll position."""
        if self._scroll is not None:
            self._scroll_pos = self._scroll.canvas.yview()[0]
        post = self.controller.state.campaign.post_battle(self.number)
        for child in self.winfo_children():
            child.destroy()
        if post.complete:
            self._build_completed(post)
        else:
            self._build_pending(post)
        if self._scroll is not None:
            self._scroll.canvas.after_idle(lambda: self._scroll.canvas.yview_moveto(self._scroll_pos))

    def _run(self, action) -> None:
        """Runs one engine action; reports and rebuilds on success."""
        ok, message = action()
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
        tk.Label(self, text=f"POST-BATTLE #{post.battle_number}", bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 16)).pack(anchor="w")
        tk.Label(
            self,
            text=f"Complete · transformed State #{post.battle_number - 1} into State #{post.battle_number}",
            bg=COLORS["bg"], fg=COLORS["muted"], font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(3, 10))
        SummaryStrip(
            self,
            [
                ("Experience", f"+{battle.xp_delta}"),
                ("Casualties", str(battle.casualties)),
                ("Advances", str(battle.advances)),
                ("Wyrdstone", f"+{battle.wyrdstone}"),
                ("Gold", f"{battle.gold_delta:+d} gc"),
                ("Rating", f"{battle.rating_before} → {battle.rating_after}"),
            ],
        ).pack(fill="x", pady=(0, 10))

        box = BorderedFrame(self, background=COLORS["panel"], padding=1)
        box.pack(fill="x")
        body = box.body
        body.configure(padx=18, pady=16)
        tk.Label(body, text="THE TRANSITION", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w")
        for line in (
            "Recovery resolved injuries, experience and resulting advances.",
            f"Exploration yielded {battle.wyrdstone} wyrdstone shard(s) before income decisions.",
            "Veterans, rare items and Dramatis searches were resolved.",
            "Recruitment and equipment reallocation produced the final warband.",
            f"Warband rating was recalculated automatically: {battle.rating_before} → {battle.rating_after}.",
        ):
            tk.Label(body, text=f"• {line}", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(anchor="w", pady=3)
        actions = tk.Frame(body, bg=COLORS["panel"])
        actions.pack(fill="x", pady=(16, 0))
        ttk.Button(actions, text=f"‹ STATE #{post.battle_number - 1}", command=lambda: self.controller.select_state(post.battle_number - 1)).pack(side="left")
        ttk.Button(actions, text=f"STATE #{post.battle_number} ›", style="Accent.TButton", command=lambda: self.controller.select_state(post.battle_number)).pack(side="right")

    def _build_pending(self, post) -> None:
        battle = self.controller.state.campaign.battle(post.battle_number)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        top = tk.Frame(self, bg=COLORS["bg"])
        top.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        title = tk.Frame(top, bg=COLORS["bg"])
        title.pack(side="left", fill="x", expand=True)
        tk.Label(title, text=f"POST-BATTLE #{post.battle_number}", bg=COLORS["bg"], fg=COLORS["text"], font=("Georgia", 16)).pack(side="left")
        tk.Label(title, text="IN PROGRESS", bg=COLORS["panel_deep"], fg=COLORS["accent"], font=("Segoe UI Semibold", 7), padx=8, pady=4).pack(side="left", padx=10)
        ttk.Button(top, text="SAVE & CLOSE", command=self._save_and_close).pack(side="right")
        ttk.Button(top, text=f"VIEW BATTLE #{post.battle_number}", style="Ghost.TButton", command=lambda: self.controller.select_battle(post.battle_number)).pack(side="right", padx=(0, 5))

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

        actions = tk.Frame(self, bg=COLORS["bg"])
        actions.grid(row=5, column=0, sticky="ew", pady=(8, 0))
        if post.review_open:
            ttk.Button(actions, text=f"‹  {tr('Equipment').upper()}", command=lambda: self.controller.set_post_battle_step(len(POST_BATTLE_STEPS) - 1)).pack(side="left")
            ttk.Button(actions, text=f"COMMIT STATE #{post.battle_number}", style="Accent.TButton", command=self._commit).pack(side="right")
            return

        if post.active_step > 0:
            ttk.Button(actions, text=f"‹  {tr(POST_BATTLE_STEPS[post.active_step - 1]).upper()}", command=lambda: self.controller.set_post_battle_step(post.active_step - 1)).pack(side="left")

        if post.active_step < len(POST_BATTLE_STEPS) - 1:
            ttk.Button(
                actions,
                text=tr("CONTINUE TO {}  ›").format(tr(POST_BATTLE_STEPS[post.active_step + 1]).upper()),
                style="Accent.TButton",
                command=self.controller.advance_post_battle_step,
            ).pack(side="right")
        elif post.active_step in post.completed_steps:
            ttk.Button(actions, text="FINAL REVIEW  ›", style="Accent.TButton", command=self.controller.open_post_battle_review).pack(side="right")
        else:
            ttk.Button(actions, text="CONTINUE TO FINAL REVIEW  ›", style="Accent.TButton", command=self.controller.advance_post_battle_step).pack(side="right")

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
        return f"KB source: {step_ids} — resolves {files}"

    # 01 · injuries ---------------------------------------------------------

    def _out_of_action_warriors(self, battle) -> list:
        """Warriors recorded Out of Action for this battle.

        Falls back to every warrior when the battle predates per-warrior
        recording (``out_of_action_ids`` is ``None``).
        """
        warriors = self.controller.state.campaign.warriors
        if battle.out_of_action_ids is None:
            return list(warriors)
        recorded = set(battle.out_of_action_ids)
        return [warrior for warrior in warriors if warrior.id in recorded] or list(warriors)

    def _injuries(self, parent: tk.Misc, battle) -> None:
        resolver = self.controller.post_battle_resolver()
        marked = self._out_of_action_warriors(battle)
        recorded = battle.out_of_action_ids is not None
        scope = (
            f"{len(marked)} warrior(s) were recorded Out of Action in the battle record"
            if recorded else "No per-warrior record exists for this battle; every warrior is offered"
        )
        self._title(parent, "01 · Injuries", f"{scope}. Resolve each against the KB serious-injury charts: each roll starts unresolved; resolving then applying it mutates the roster. {self._kb_provenance(0)}")
        if not marked:
            tk.Label(parent, text="No warrior was recorded Out of Action: proceed to Experience.", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")
            return
        for warrior in marked:
            hero = warrior.kind == "hero"
            applied = warrior.id in self._applied_injuries
            holder: dict = {}
            subtitle = ("Hero · Out of Action · D66 serious injury roll"
                        if hero else f"Henchmen group · {warrior.quantity} member{'s' if warrior.quantity != 1 else ''} · D6 survival roll")
            if applied:
                subtitle += " · APPLIED"
            DiceResolutionCard(
                parent,
                title=warrior.name, subtitle=subtitle,
                notation="D66" if hero else "D6",
                dice_count=2 if hero else 1,
                demo_dice=(2, 4) if hero else (1,),
                combine="d66" if hero else "sum",
                on_resolved=lambda dice, _r=resolver, _h=hero, _x=holder: _injury_store(dice, _r, hero=_h, holder=_x),
                outcome_actions=(() if applied else (("APPLY TO ROSTER", lambda w=warrior, _x=holder: self._apply_injury(w, _x), "Accent.TButton"),)),
            ).pack(fill="x", pady=(0, 9))

    def _apply_injury(self, warrior, holder: dict) -> None:
        dice = holder.get("dice")
        if not dice:
            return
        resolver = self.controller.post_battle_resolver()
        outcome = (resolver.resolve_hero_serious_injury(10 * dice[0] + dice[1]) if warrior.kind == "hero"
                   else resolver.resolve_henchman_serious_injury(dice[0]))
        self._applied_injuries.add(warrior.id)
        self._run(lambda: self._engine().apply_serious_injury(warrior.id, outcome))

    # 02 · experience -------------------------------------------------------

    def _experience(self, parent: tk.Misc, battle) -> None:
        engine = self._engine()
        self._title(parent, "02 · Experience", f"Allocate the experience Battle #{battle.number} granted (+{battle.xp_delta} XP). Crossed thresholds earn advance rolls resolved against the KB advancement tables; stat increases and skill/spell picks are committed here. {self._kb_provenance(1)}")
        engine.sync_pending_advances()
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
            tk.Label(top, text=f"XP {warrior.experience}", bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(side="right", padx=(0, 10))
            ttk.Button(top, text="+1 XP", style="Mini.TButton", command=lambda w=warrior: self._run(lambda: self._engine().add_xp(w.id, 1))).pack(side="right")
            tk.Label(card, text="Survived +1   ·   Scenario / objectives +1", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(5, 5))
            ExperienceTrack(card, warrior.experience, track_type="hero" if warrior.kind == "hero" else "henchman").pack(fill="x")

        tk.Label(parent, text="ADVANCE ROLLS EARNED THIS SEQUENCE", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(7, 6))
        pending = engine.post.pending_advances if engine.post is not None else []
        if not pending:
            tk.Label(
                parent,
                text="No warrior has crossed an experience threshold yet. Grant XP above; a threshold earns a 2D6 advance roll on the KB table (heroes: 20/40/65/90… · henchmen: 8/16/25/35…).",
                bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8), wraplength=900, justify="left",
            ).pack(anchor="w")
            return
        for row in list(pending):
            self._advance_card(parent, engine, row)

    def _advance_card(self, parent: tk.Misc, engine, row: dict) -> None:
        warrior_id = str(row.get("warrior_id"))
        warrior = next((w for w in engine.campaign.warriors if w.id == warrior_id), None)
        if warrior is None:
            return
        is_hero = str(row.get("table") or "hero") == "hero"
        kind_label = "Hero" if is_hero else f"Henchmen group (all {warrior.quantity} members gain it)"
        threshold = row.get("threshold")
        committed = bool(row.get("committed"))
        roll_total = row.get("roll_total")
        subtitle = f"{kind_label} · crossed the {threshold} XP threshold · 2D6 on the KB {'hero' if is_hero else 'henchman'} table"
        if committed:
            subtitle += f" · COMMITTED: {row.get('applied_label') or 'applied'}"
        elif roll_total is not None:
            subtitle += f" · rolled {roll_total}"

        card = tk.Frame(parent, bg=COLORS["panel_alt"], highlightthickness=1, highlightbackground=COLORS["border_soft"], padx=12, pady=10)
        card.pack(fill="x", pady=(0, 7))
        top = tk.Frame(card, bg=COLORS["panel_alt"])
        top.pack(fill="x")
        tk.Label(top, text=warrior.name, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Georgia", 11)).pack(side="left")
        tk.Label(top, text="ADVANCE", bg=COLORS["panel_deep"], fg=COLORS["success" if committed else "accent"], font=("Segoe UI Semibold", 7), padx=7, pady=3).pack(side="right")
        tk.Label(card, text=subtitle, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(3, 0))

        if committed:
            return
        if roll_total is None:
            holder: dict = {}
            DiceResolutionCard(
                card, title="Advance roll", subtitle="Roll in app or enter physical dice",
                notation="2D6", dice_count=2, demo_dice=(4, 3), combine="sum",
                outcome_title="Pending pick", outcome_detail="Resolved; choose the advance below.",
                on_resolved=lambda dice, _e=engine, _w=warrior_id, _x=holder: _x.update(dice=list(dice))
                or ("Advance resolved", "Choose the resulting advance.", "accent"),
                outcome_actions=(("RESOLVE ROLL", lambda: self._resolve_advance(_e, _w, _x), "Accent.TButton"),),
            ).pack(fill="x", pady=(8, 0))
            return
        outcome, _row = engine._pending_outcome(warrior_id)
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
                                   command=lambda w=warrior_id, k=key: self._commit_advance(w, option_kind="characteristic_increase", characteristic=k)).pack(side="left", padx=(0, 6))
                        break
            elif option.kind == "choose_skill":
                ttk.Button(actions, text="CHOOSE SKILL…", style="Accent.TButton",
                           command=lambda w=warrior_id: self._open_skill_dialog(w, want_spells=False)).pack(side="left", padx=(0, 6))
            elif option.kind == "generate_spell":
                ttk.Button(actions, text="GENERATE SPELL…", style="Accent.TButton",
                           command=lambda w=warrior_id: self._open_skill_dialog(w, want_spells=True)).pack(side="left", padx=(0, 6))
            elif option.kind == "promote_henchman":
                if warrior.quantity < 2:
                    tk.Label(actions, text="A group of one cannot split into a hero; reroll this advance instead.", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left")
                else:
                    ttk.Button(actions, text="THE LAD'S GOT TALENT…", style="Accent.TButton",
                               command=lambda w=warrior_id: self._promote_member(w)).pack(side="left", padx=(0, 6))
        budget = engine.promotion_pick_budget(warrior_id)
        if budget and budget < 2:
            ttk.Button(actions, text=f"PICK PROMOTION SKILL ({budget} LEFT)…", style="Accent.TButton",
                       command=lambda w=warrior_id: self._open_skill_dialog(w, want_spells=False, promotion=True)).pack(side="left", padx=(0, 6))

    def _resolve_advance(self, engine, warrior_id: str, holder: dict) -> None:
        dice = holder.get("dice")
        if not dice:
            return
        total = sum(dice)
        outcome, _row = engine._pending_outcome(warrior_id)
        subroll = None
        if outcome is not None and not outcome.final:
            # Characteristic tables need a D6 sub-roll after an 8 or 9.
            subroll = self._ask_subroll(total)
            if subroll is None:
                return
        self._run(lambda: engine.resolve_pending_advance(warrior_id, total, subroll=subroll))

    def _ask_subroll(self, total: int) -> int | None:
        dialog = tk.Toplevel(self)
        dialog.title("D6 sub-roll")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        tk.Label(dialog, text=f"The advance row {total} needs a D6 sub-roll.", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 10)).pack(padx=18, pady=(14, 6))
        var = tk.IntVar(value=3)
        ttk.Spinbox(dialog, from_=1, to=6, width=5, textvariable=var).pack(pady=4)
        result: list[int] = []
        ttk.Button(dialog, text="OK", style="Accent.TButton", command=lambda: (result.append(int(var.get())), dialog.destroy())).pack(pady=(4, 12))
        dialog.wait_window()
        return result[0] if result else None

    def _commit_advance(self, warrior_id: str, *, option_kind: str, characteristic: str | None = None) -> None:
        engine = self._engine()
        ok, message = engine.commit_pending_advance(
            warrior_id, option_kind=option_kind, characteristic=characteristic,
        )
        self._status_text = ("✓ " if ok else "⚠ ") + message
        self._rebuild()

    def _promote_member(self, warrior) -> None:
        """Ask for the promoted member's name, then split the group (Lad's Got Talent)."""
        dialog = tk.Toplevel(self)
        dialog.title("The Lad's Got Talent")
        dialog.transient(self.winfo_toplevel())
        dialog.grab_set()
        tk.Label(
            dialog,
            text=f"Name the member of {warrior.name} who becomes a Hero.",
            bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 10),
        ).pack(padx=18, pady=(14, 6))
        var = tk.StringVar(value=f"{warrior.profile_name} Champion")
        entry = ttk.Entry(dialog, textvariable=var, width=32)
        entry.pack(padx=18, pady=4)
        entry.selection_range(0, "end")
        entry.focus_set()
        result: list[str] = []

        def _confirm() -> None:
            result.append(var.get().strip() or f"{warrior.profile_name} Champion")
            dialog.destroy()

        ttk.Button(dialog, text="PROMOTE", style="Accent.TButton", command=_confirm).pack(pady=(6, 14))
        dialog.bind("<Return>", lambda _e: _confirm())
        dialog.bind("<Escape>", lambda _e: dialog.destroy())
        dialog.wait_window()
        if not result:
            return
        ok, message = self._engine().promote_henchman(warrior.id, member_name=result[0])
        self._status_text = ("✓ " if ok else "⚠ ") + message
        self._rebuild()

    def _open_skill_dialog(self, warrior_id: str, *, want_spells: bool, promotion: bool = False) -> None:
        from mordheim_campaign.ui.dialogs.skill_choice import SkillChoiceDialog

        dialog = SkillChoiceDialog(self, self._engine(), warrior_id, want_spells=want_spells, promotion=promotion)
        self.wait_window(dialog)
        engine = self._engine()
        row = engine.post.pending_advance_for(warrior_id) if engine.post is not None else None
        if row is not None and row.get("committed"):
            self._status_text = "✓ " + str(row.get("applied_label") or "Advance committed")
        self._rebuild()

    # 03 · exploration ------------------------------------------------------

    def _exploration(self, parent: tk.Misc, battle) -> None:
        resolver = self.controller.post_battle_resolver()
        engine = self._engine()
        self._title(parent, "03 · Exploration", f"Roll once for each eligible Hero, plus one die when the warband won. Shards come from the KB shard chart; matching dice open the KB special-result table. {self._kb_provenance(2)}")
        if engine.post is not None and engine.post.wyrdstone_delta:
            SummaryStrip(parent, [("Shards found", f"+{engine.post.wyrdstone_delta}"), ("In hoard", f"{engine.projected_shards()}")]).pack(fill="x", pady=(0, 12))
            return
        surviving = max(0, engine.projected_heroes() - battle.casualties)
        won = battle.result == "Victory"
        dice_count = resolver.exploration_dice(surviving_heroes=surviving, warband_won=won)
        demo = ((3, 3, 5, 6) + (1,) * 6)[:dice_count]
        holder: dict = {}
        DiceResolutionCard(
            parent, title="Exploration Dice", subtitle=f"Eligible Heroes: {surviving} · {dice_count}D6 from the KB allocation",
            notation=f"{dice_count}D6", dice_count=dice_count, demo_dice=demo, combine="list",
            outcome_title="Exploration resolved", outcome_detail="Resolve the roll to reveal the shard total.",
            on_resolved=lambda dice, _r=resolver, _x=holder: _exploration_store(dice, _r, holder=_x),
            outcome_actions=(("ADD SHARDS TO HOARD", lambda: self._apply_exploration(holder), "Accent.TButton"),),
        ).pack(fill="x")

    def _apply_exploration(self, holder: dict) -> None:
        dice = holder.get("dice")
        if dice:
            self._run(lambda: self._engine().apply_exploration(tuple(dice)))

    # 04 · sell wyrdstone ---------------------------------------------------

    def _sell_wyrdstone(self, parent: tk.Misc, _battle) -> None:
        engine = self._engine()
        resolver = self.controller.post_battle_resolver()
        post = engine.post
        self._title(parent, "04 · Sell Wyrdstone", f"Choose how many shards to sell. This action can only be performed once in the post-battle sequence; the sale value comes from the KB pricing table (warband size × shards sold). {self._kb_provenance(3)}")
        if post is None:
            return
        available = engine.projected_shards()
        if post.sale_resolved:
            SummaryStrip(parent, [("Sale resolved", "once per sequence"), ("Shards sold", str(post.wyrdstone_sold)), ("Shards remaining", str(available))]).pack(fill="x", pady=(0, 12))
            return
        SummaryStrip(parent, [("In hoard", str(available)), ("Sell now", "choose below"), ("Income", "KB pricing table")]).pack(fill="x", pady=(0, 12))
        card = self._section(parent, "Choose quantity to sell", "The table value is calculated from the current warband size and the fragments sold.")
        row = tk.Frame(card, bg=COLORS["panel_alt"])
        row.pack(fill="x")
        tk.Label(row, text="Wyrdstone shards", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(side="left")
        sell_var = tk.IntVar(value=min(1, available))
        ttk.Spinbox(row, from_=0, to=available, width=5, textvariable=sell_var).pack(side="left", padx=12)
        value_var = tk.StringVar(value="—")
        tk.Label(row, textvariable=value_var, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI Semibold", 9)).pack(side="left", padx=(4, 12))
        ttk.Button(row, text="CALCULATE SALE", command=lambda: value_var.set(
            f"{resolver.wyrdstone_sale_value(max(0, sell_var.get()), engine.projected_models())} gc")).pack(side="left")
        ttk.Button(row, text="SELL", style="Accent.TButton", command=lambda: self._run(
            lambda: engine.sell_wyrdstone(max(0, sell_var.get())))).pack(side="right")
        tk.Label(card, text="Selling zero shards is allowed: it closes the once-per-sequence action.", bg=COLORS["panel_alt"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(anchor="w", pady=(9, 0))

    # 05 · veterans ---------------------------------------------------------

    def _veterans(self, parent: tk.Misc, _battle) -> None:
        engine = self._engine()
        self._title(parent, "05 · Available Veterans", f"Determine the post-battle experience pool available for hiring experienced recruits. You are not committing to hire anyone yet. {self._kb_provenance(4)}")
        post = engine.post
        holder: dict = {}
        pool = post.veteran_pool if post is not None else 0
        DiceResolutionCard(
            parent, title="Veteran Experience Pool", subtitle=f"Availability check before recruitment · current pool {pool} XP",
            notation="2D6", dice_count=2, demo_dice=(4, 3), combine="sum",
            outcome_title="Pool rolled", outcome_detail="This pool is used later in Recruitment",
            on_resolved=lambda dice, _x=holder: (_x.update(dice=list(dice)), f"{sum(dice)} XP available", f"Veteran pool of {sum(dice)} XP", "accent")[1:],
            outcome_actions=(("SET VETERAN POOL", lambda: self._apply_veterans(holder), "Accent.TButton"),),
        ).pack(fill="x")

    def _apply_veterans(self, holder: dict) -> None:
        dice = holder.get("dice")
        if dice:
            self._run(lambda: self._engine().apply_veteran_pool(sum(dice)))

    # 06 · rare items & dramatis --------------------------------------------

    def _rare_and_dramatis(self, parent: tk.Misc, _battle) -> None:
        content = self.controller.post_battle_content()
        resolver = self.controller.post_battle_resolver()
        rare = content.rare_items()
        dramatis = content.dramatis_personae()
        self._title(
            parent,
            "06 · Rare Items & Dramatis",
            f"One UI phase contains the two consecutive searches: first rare items, then Dramatis Personae. Eligible Heroes are a limited search resource. Offers come from the KB Trading Post and hiring catalogue. {self._kb_provenance(5)}",
        )

        tk.Label(parent, text="A · RARE ITEMS", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 6))
        rare_section = self._section(
            parent, "Choose a rare item",
            f"{len(rare)} rare Trading Post items are available to this warband. Assign an eligible Hero to search for one specific item; successful purchases go to the stash.",
        )
        if rare:
            controls = tk.Frame(rare_section, bg=COLORS["panel_alt"])
            controls.pack(fill="x")
            item_labels = [f"{entry.name} · Rare {entry.rarity} · {entry.price_label}" for entry in rare[:12]]
            picker = ttk.Combobox(controls, state="readonly", values=item_labels, width=42)
            picker.pack(side="left")
            picker.set(item_labels[0])

            holder: dict = {}
            DiceResolutionCard(
                parent, title="Rare item availability search", subtitle="A successful search reveals a contextual Buy action · resolves the 2D6 rarity test against the KB availability of the selected item",
                notation="2D6", dice_count=2, demo_dice=(5, 4), combine="sum",
                outcome_title="Rare item search", outcome_detail="Resolve the roll to test the selected item.",
                on_resolved=lambda dice, _r=resolver, _h=holder: _rarity_card(
                    dice, _r, rare[_selected_index(item_labels, picker)].item_id,
                    rare[_selected_index(item_labels, picker)].name, holder),
                outcome_actions=(("BUY", lambda: self._buy_selected_rare(rare, item_labels, picker, holder), "Accent.TButton"),),
            ).pack(fill="x", pady=(10, 4))
            tk.Label(
                rare_section,
                text=f"{len(rare)} rare entries in the KB trading post (showing {min(len(rare), 12)}).",
                bg=COLORS["panel_alt"], fg=COLORS["muted_dark"], font=("Segoe UI", 7),
            ).pack(anchor="w", pady=(4, 0))
        else:
            tk.Label(
                rare_section, text="No rare items from the Trading Post are available to this warband.",
                bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8),
            ).pack(anchor="w")

        divider = tk.Frame(parent, bg=COLORS["border_soft"], height=1)
        divider.pack(fill="x", pady=(0, 11))
        tk.Label(parent, text="B · DRAMATIS PERSONAE", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(0, 6))
        dramatis_section = self._section(
            parent, "Choose a special character",
            "Heroes assigned to this search are not available to look for rare items in the same sequence. Entries marked * depend on roster/variant conditions evaluated by the application.",
        )
        if dramatis:
            eligibility_notes = [
                f"{offer.name}: {offer.eligibility_note}" for offer in dramatis
                if offer.eligibility != "eligible"
            ]
            if eligibility_notes:
                tk.Label(
                    dramatis_section,
                    text="\n".join(f"• {line}" for line in eligibility_notes[:4]),
                    bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 7), justify="left",
                    wraplength=860,
                ).pack(anchor="w", pady=(0, 6))
            labels = [
                (f"{offer.name}{' *' if offer.eligibility != 'eligible' else ''}"
                 + (f" · {offer.fee_label}" if offer.fee_label else ""))
                for offer in dramatis[:12]
            ]
            picker = ttk.Combobox(dramatis_section, state="readonly", values=labels, width=40)
            picker.pack(anchor="w")
            picker.set(labels[0])

            def _selected_offer():
                try:
                    index = max(0, labels.index(picker.get()))
                except ValueError:
                    index = 0
                return dramatis[index]

            holder: dict = {}
            DiceResolutionCard(
                parent, title="Dramatis Personae search", subtitle="One D6 per searcher · a result under the Hero's Initiative locates the character",
                notation="D6", dice_count=1, demo_dice=(3,), combine="sum",
                outcome_title="Dramatis search", outcome_detail="Resolve the roll to locate the character. For conditional entries the acceptance roll reuses the same die.",
                on_resolved=lambda dice, _x=holder: (_x.update(dice=list(dice), success=True), "Located", "Character found · hiring remains optional", "success")[1:],
                outcome_actions=(("HIRE", lambda: self._hire_dramatis(_selected_offer(), holder), "Accent.TButton"),),
            ).pack(fill="x", pady=(10, 0))
        else:
            tk.Label(
                dramatis_section, text="No Dramatis Personae are currently searchable by this warband.",
                bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8),
            ).pack(anchor="w")

    def _buy_selected_rare(self, rare, item_labels: list[str], picker, holder: dict) -> None:
        if not holder.get("success"):
            self._status_text = "⚠ The rarity test failed; the item is not available to buy."
            self._rebuild()
            return
        offer = rare[_selected_index(item_labels, picker)]
        if offer.price_gc is None:
            self._status_text = "⚠ This item has no flat price; purchases are not supported yet."
            self._rebuild()
            return
        self._run(lambda: self._engine().buy_item(offer.item_id, 1, offer.price_gc))

    def _hire_dramatis(self, offer, holder: dict) -> None:
        dice = holder.get("dice")
        acceptance = int(dice[0]) if (offer.eligibility == "conditional" and dice) else None
        self._run(lambda: self._engine().hire_hireling(offer, acceptance_roll=acceptance))

    # 07 · recruitment ------------------------------------------------------

    def _recruitment(self, parent: tk.Misc, _battle) -> None:
        content = self.controller.post_battle_content()
        engine = self._engine()
        campaign = self.controller.state.campaign
        hired = content.hired_swords()
        common = content.common_items()
        self._title(
            parent,
            "07 · Recruitment",
            f"Hire new warriors or Hired Swords and buy common items. This is the warband-building stage; rare-item searches are already closed. {self._kb_provenance(6)}",
        )
        post = engine.post
        SummaryStrip(parent, [
            ("Treasury", f"{engine.projected_gold()} gc"),
            ("Veteran pool", f"{post.veteran_pool if post else 0} XP"),
            ("Models", f"{engine.projected_models()}/{campaign.maximum_models}"),
        ]).pack(fill="x", pady=(0, 12))

        warriors = [
            profile for profile in self.controller.port.profiles(campaign.collection, campaign.band_id, kind="henchman")
            if profile.kind == "henchman"
        ]
        recruit_section = self._section(parent, "WARRIORS", "Recruit new members or add to the roster (KB profiles, model and treasury limits enforced).")
        for profile in warriors[:14]:
            row = tk.Frame(recruit_section, bg=COLORS["panel_alt"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{profile.name}  ·  {profile.cost} gc", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8)).pack(side="left")
            ttk.Button(row, text="RECRUIT", style="Mini.TButton", command=lambda p=profile: self._run(
                lambda: engine.recruit_band_profile(p.profile_id, 1))).pack(side="right")

        hired_section = self._section(parent, "HIRED SWORDS", "Hire available mercenaries and account for upkeep where applicable. * = acceptance roll or Mercenary-variant condition.")
        if hired:
            for offer in hired[:14]:
                row = tk.Frame(hired_section, bg=COLORS["panel_alt"])
                row.pack(fill="x", pady=2)
                marker = " *" if offer.eligibility != "eligible" else ""
                label = f"{offer.name}{marker}  ·  {offer.availability_label.lower()}"
                if offer.fee_label:
                    label += f"  ·  Hire {offer.fee_label}"
                if offer.upkeep_label:
                    label += f" · Upkeep {offer.upkeep_label}"
                tk.Label(row, text=label, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8)).pack(side="left")
                if offer.fee_gc is not None and offer.eligibility == "eligible":
                    ttk.Button(row, text="HIRE", style="Mini.TButton", command=lambda o=offer: self._run(
                        lambda: engine.hire_hireling(o, acceptance_roll=None))).pack(side="right")
        else:
            tk.Label(hired_section, text="No Hired Swords are available to this warband.", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w")

        common_section = self._section(parent, "COMMON ITEMS", "Common equipment can be purchased without a rarity search (KB Trading Post).")
        for offer in common[:14]:
            if offer.price_gc is None:
                continue
            row = tk.Frame(common_section, bg=COLORS["panel_alt"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=f"{offer.name}  ·  {offer.price_label}", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8)).pack(side="left")
            ttk.Button(row, text="BUY", style="Mini.TButton", command=lambda o=offer: self._run(
                lambda: engine.buy_item(o.item_id, 1, o.price_gc))).pack(side="right")

    # 08 · equipment --------------------------------------------------------

    def _equipment(self, parent: tk.Misc, _battle) -> None:
        content = self.controller.post_battle_content()
        engine = self._engine()
        campaign = self.controller.state.campaign
        common = content.common_items()
        self._title(
            parent,
            "08 · Equipment",
            f"Buy common equipment, then manage the complete band inventory from the stash. Items found or purchased earlier appear here before the next warband state is committed. {self._kb_provenance(7)}",
        )
        purchase = self._section(parent, "BUY EQUIPMENT", "Common items can be bought here. Rare finds from Searches have already been resolved and, if purchased, are waiting in the stash below.")
        purchase_head = tk.Frame(purchase, bg=COLORS["panel_alt"])
        purchase_head.pack(fill="x", pady=(0, 9))
        tk.Label(purchase_head, text="TREASURY", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).pack(side="left")
        tk.Label(purchase_head, text=f"{engine.projected_gold()} gc", bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Georgia", 17)).pack(side="left", padx=(8, 20))
        tk.Label(purchase_head, text="Purchases are added to the stash", bg=COLORS["panel_alt"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(side="left")

        offers = [offer for offer in common if offer.price_gc is not None][:14]
        if offers:
            chooser = tk.Frame(purchase, bg=COLORS["panel_alt"])
            chooser.pack(fill="x")
            tk.Label(chooser, text="ITEM", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).grid(row=0, column=0, sticky="w")
            tk.Label(chooser, text="QTY", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).grid(row=0, column=1, sticky="w", padx=(8, 0))
            item_labels = [f"{offer.name} · {offer.price_label}" for offer in offers]
            item = ttk.Combobox(chooser, state="readonly", values=item_labels, width=40)
            item.grid(row=1, column=0, sticky="ew", pady=(3, 0))
            item.set(item_labels[0])
            qty = tk.IntVar(value=1)
            ttk.Spinbox(chooser, from_=1, to=10, width=5, textvariable=qty).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(3, 0))

            def _selected_offer():
                try:
                    return offers[max(0, item_labels.index(item.get()))]
                except ValueError:
                    return offers[0]

            ttk.Button(chooser, text="BUY & ADD TO STASH", style="Accent.TButton", command=lambda: self._run(
                lambda: engine.buy_item(_selected_offer().item_id, max(1, qty.get()), _selected_offer().price_gc))).grid(row=1, column=2, sticky="e", pady=(3, 0))
            chooser.columnconfigure(0, weight=1)

        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True, pady=(5, 0))

        stash_tab = tk.Frame(notebook, bg=COLORS["panel"], padx=10, pady=10)
        warrior_tab = tk.Frame(notebook, bg=COLORS["panel"], padx=10, pady=10)
        notebook.add(stash_tab, text="STASH")
        notebook.add(warrior_tab, text="BY WARRIOR")

        stash_top = tk.Frame(stash_tab, bg=COLORS["panel"])
        stash_top.pack(fill="x", pady=(0, 7))
        owned = sum(item.owned for item in campaign.inventory)
        equipped = sum(item.equipped for item in campaign.inventory)
        available = sum(item.stash for item in campaign.inventory)
        tk.Label(stash_top, text="BAND INVENTORY", bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 11)).pack(side="left")
        tk.Label(stash_top, text=f"Owned {owned}  ·  Equipped {equipped}  ·  Available {available}", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="right")

        stash_table = tk.Frame(stash_tab, bg=COLORS["border_soft"], padx=1, pady=1)
        stash_table.pack(fill="x")
        hdr = tk.Frame(stash_table, bg=COLORS["panel_deep"], padx=9, pady=6)
        hdr.pack(fill="x")
        for text, width in (("ITEM", 24), ("OWNED", 8), ("CURRENTLY EQUIPPED", 40), ("STASH", 8)):
            tk.Label(hdr, text=text, width=width, anchor="w", bg=COLORS["panel_deep"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).pack(side="left")

        if campaign.inventory:
            for row in campaign.inventory:
                item_row = tk.Frame(stash_table, bg=COLORS["panel_alt"], padx=9, pady=5)
                item_row.pack(fill="x", pady=(1, 0))
                tk.Label(item_row, text=row.name, width=24, anchor="w", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8)).pack(side="left")
                tk.Label(item_row, text=str(row.owned), width=8, anchor="w", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left")
                tk.Label(item_row, text=f"{row.equipped} equipped", width=26, anchor="w", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left")
                tk.Label(item_row, text=str(row.stash), width=8, anchor="w", bg=COLORS["panel_alt"], fg=COLORS["accent"] if row.stash else COLORS["muted_dark"], font=("Segoe UI Semibold", 8)).pack(side="left")
                if row.stash > 0:
                    ttk.Button(item_row, text="SELL", style="Mini.TButton", command=lambda r=row: self._run(lambda: engine.sell_item(r.id, 1))).pack(side="right", padx=(5, 0))
                    ttk.Button(item_row, text="ASSIGN", style="Mini.TButton", command=lambda r=row: self._assign_menu(r)).pack(side="right", padx=(5, 0))
        else:
            tk.Label(stash_table, text="The stash is empty.", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8), padx=9, pady=6).pack(anchor="w")

        tk.Label(
            stash_tab,
            text="Assign moves an available copy from the stash to a warrior. Sell uses half the stored value.",
            bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7),
        ).pack(anchor="w", pady=(7, 0))

        tk.Label(warrior_tab, text="EQUIPMENT BY WARRIOR", bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 11)).pack(anchor="w", pady=(0, 7))
        for warrior in campaign.warriors:
            row = tk.Frame(warrior_tab, bg=COLORS["panel_alt"], padx=10, pady=7)
            row.pack(fill="x", pady=(0, 3))
            left = tk.Frame(row, bg=COLORS["panel_alt"])
            left.pack(side="left", fill="x", expand=True)
            label = warrior.name + (f"  ×{warrior.quantity}" if warrior.quantity > 1 else "")
            tk.Label(left, text=label, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Georgia", 9)).pack(anchor="w")
            current = ", ".join(warrior.equipment) or "—"
            tk.Label(left, text=current, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))

    def _assign_menu(self, item_row) -> None:
        engine = self._engine()
        menu = tk.Menu(self, tearoff=False, bg=COLORS["panel"], fg=COLORS["text"], activebackground=COLORS["panel_soft"], activeforeground=COLORS["text"])
        for warrior in self.controller.state.campaign.warriors:
            menu.add_command(
                label=warrior.name + (f"  ×{warrior.quantity}" if warrior.quantity > 1 else ""),
                command=lambda w=warrior: self._run(lambda: engine.assign_item(item_row.id, w.id)),
            )
        try:
            menu.tk_popup(self.winfo_pointerx(), self.winfo_pointery())
        finally:
            menu.grab_release()

    # ------------------------------------------------------------- final review

    def _review(self, parent: tk.Misc, battle) -> None:
        engine = self._engine()
        projections = engine.projections()
        base = engine._base_state()
        self._title(parent, "Final Review", f"All eight player actions are complete. This confirmation creates State #{battle.number}; warband rating is calculated automatically from the final roster. {self._kb_provenance(0)}")
        SummaryStrip(parent, [
            ("Rating", f"{base.rating if base else '—'} → {projections['rating']}"),
            ("Models", f"{base.models if base else '—'} → {projections['models']}"),
            ("Treasury", f"{base.gold if base else '—'} → {projections['gold']} gc"),
            ("Wyrdstone", f"{base.wyrdstone if base else '—'} → {projections['shards']}"),
        ]).pack(fill="x", pady=(0, 12))
        for title, lines in (
            ("RECOVERY", ["Injuries applied", f"Experience total {projections['experience']} XP"]),
            ("EXPLORATION & INCOME", ["Exploration resolved", "Wyrdstone sale resolved once"]),
            ("SEARCHES", [f"Veteran pool: {engine.post.veteran_pool if engine.post else 0} XP", "Rare items and Dramatis searches resolved"]),
            ("WARBAND", ["Recruitment complete", "Equipment reallocated", "Rating recalculated automatically"]),
        ):
            tk.Label(parent, text=title, bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(6, 3))
            for line in lines:
                tk.Label(parent, text=f"• {line}", bg=COLORS["panel"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(anchor="w", padx=(8, 0), pady=1)

    def _save_and_close(self) -> None:
        """Saves the campaign (with the pending post-battle) and returns to the current state."""
        from mordheim_campaign.ui.file_actions import save_current_campaign

        save_current_campaign(self, self.controller)
        self.controller.go_to_current_state()
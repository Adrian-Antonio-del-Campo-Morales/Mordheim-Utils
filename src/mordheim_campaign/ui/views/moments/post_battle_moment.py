from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from mordheim_campaign.application.controller import AppController
from mordheim_campaign.application.state import POST_BATTLE_GROUPS, POST_BATTLE_STEPS
from mordheim_campaign.ui.components import DiceResolutionCard, PostBattleSequence
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


def _exploration_card(dice: list[int], resolver) -> tuple[str, str, str]:
    """Live KB resolution of an exploration roll."""
    resolved = resolver.resolve_exploration(tuple(dice))
    detail = f"Total {resolved.total} → {resolved.shards} wyrdstone shard(s)"
    if resolved.matching_dice_note:
        detail += f" · {resolved.matching_dice_note}"
    return f"Exploration resolved · {resolved.shards} shard(s)", detail, "accent"


def _rarity_card(dice: list[int], resolver, item_id: str, name: str) -> tuple[str, str, str]:
    """Live KB rarity-test resolution for a rare-item search."""
    search = resolver.resolve_rarity_search(item_id, sum(dice))
    title = "Available" if search.success else "Not found"
    tone = "success" if search.success else "neutral"
    return title, f"{name}: {search.note}", tone


class PostBattleMoment(tk.Frame):
    """Resolve one battle-to-state transition as eight sequential user actions.

    The Battle itself remains a separate timeline node. The UI condenses source
    steps 6 and 7 into one Searches action and derives warband rating
    automatically, so the player sees four balanced chapters of two actions.
    Final Review is an application confirmation, not a ninth rules step.
    """

    def __init__(self, master: tk.Misc, controller: AppController, number: int, **kwargs) -> None:
        super().__init__(master, bg=COLORS["bg"], **kwargs)
        self.controller = controller
        self.number = number
        post = controller.state.campaign.post_battle(number)
        if post.complete:
            self._build_completed(post)
        else:
            self._build_pending(post)

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
            tk.Label(context, text="FINAL REVIEW  ·  ALL 8 ACTIONS COMPLETE", bg=COLORS["bg"], fg=COLORS["success"], font=("Segoe UI Semibold", 8)).pack(side="left")
            tk.Label(context, text="Next: Commit new warband state", bg=COLORS["bg"], fg=COLORS["muted_dark"], font=("Segoe UI", 8)).pack(side="right")
        else:
            tk.Label(context, text=f"CURRENT PHASE  ·  {POST_BATTLE_STEPS[post.active_step].upper()}", bg=COLORS["bg"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(side="left")
            if post.active_step + 1 < len(POST_BATTLE_STEPS):
                tk.Label(context, text=f"Next: {POST_BATTLE_STEPS[post.active_step + 1]}", bg=COLORS["bg"], fg=COLORS["muted_dark"], font=("Segoe UI", 8)).pack(side="right")
            else:
                tk.Label(context, text="Next: Final Review", bg=COLORS["bg"], fg=COLORS["muted_dark"], font=("Segoe UI", 8)).pack(side="right")

        box = BorderedFrame(self, background=COLORS["panel"], padding=1)
        box.grid(row=4, column=0, sticky="nsew")
        scroll = ScrollableFrame(box.body, background=COLORS["panel"])
        scroll.pack(fill="both", expand=True)
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
            ttk.Button(actions, text="‹  EQUIPMENT", command=lambda: self.controller.set_post_battle_step(len(POST_BATTLE_STEPS) - 1)).pack(side="left")
            ttk.Button(actions, text=f"COMMIT STATE #{post.battle_number}", style="Accent.TButton", command=self._placeholder).pack(side="right")
            return

        if post.active_step > 0:
            ttk.Button(actions, text=f"‹  {POST_BATTLE_STEPS[post.active_step - 1].upper()}", command=lambda: self.controller.set_post_battle_step(post.active_step - 1)).pack(side="left")

        if post.active_step < len(POST_BATTLE_STEPS) - 1:
            ttk.Button(
                actions,
                text=f"CONTINUE TO {POST_BATTLE_STEPS[post.active_step + 1].upper()}  ›",
                style="Accent.TButton",
                command=self.controller.advance_post_battle_step,
            ).pack(side="right")
        elif post.active_step in post.completed_steps:
            ttk.Button(actions, text="FINAL REVIEW  ›", style="Accent.TButton", command=self.controller.open_post_battle_review).pack(side="right")
        else:
            ttk.Button(actions, text="CONTINUE TO FINAL REVIEW  ›", style="Accent.TButton", command=self.controller.advance_post_battle_step).pack(side="right")

    def _title(self, parent: tk.Misc, title: str, detail: str) -> None:
        tk.Label(parent, text=title, bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 14)).pack(anchor="w")
        tk.Label(parent, text=detail, bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 9), wraplength=980, justify="left").pack(anchor="w", pady=(4, 14))

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

    def _injuries(self, parent: tk.Misc, _battle) -> None:
        resolver = self.controller.post_battle_resolver()
        self._title(parent, "01 · Injuries", f"Resolve warriors that went Out of Action against the KB serious-injury charts. Every required roll starts unresolved so physical dice and in-app dice are equally supported. {self._kb_provenance(0)}")
        hero = resolver.resolve_hero_serious_injury(24)  # demo preview: D66 = 2 & 4
        hero_detail = " · ".join(part for part in (hero.effects + ((hero.follow_up,) if hero.follow_up else ()))) or "No lasting effect."
        DiceResolutionCard(
            parent, title="Sister Superior Marta", subtitle=f"Hero · Out of Action · Serious Injury roll required · resolved from the KB hero D66 table",
            notation="D66", dice_count=2, demo_dice=(2, 4), combine="d66",
            outcome_title=hero.result, outcome_detail=hero_detail, outcome_tone="danger",
            on_resolved=lambda dice, _r=resolver: _injury_card(dice, _r, hero=True),
        ).pack(fill="x", pady=(0, 9))
        henchman = resolver.resolve_henchman_serious_injury(1)
        DiceResolutionCard(
            parent, title="Novices", subtitle="Henchmen · 1 member Out of Action · survival roll required · resolved from the KB henchman D6 table",
            notation="D6", dice_count=1, demo_dice=(1,), combine="sum",
            outcome_title=henchman.result, outcome_detail=" · ".join(henchman.effects) or "No lasting effect.",
            outcome_tone="danger" if henchman.result == "Removed" else "neutral",
            on_resolved=lambda dice, _r=resolver: _injury_card(dice, _r, hero=False),
        ).pack(fill="x", pady=(0, 8))

    def _experience(self, parent: tk.Misc, _battle) -> None:
        self._title(parent, "02 · Experience", f"Allocate experience first. Any advancement created by the new XP is then resolved here before moving on to Exploration. {self._kb_provenance(1)}")
        for warrior, before, after in (
            (self.controller.state.campaign.warriors[0], 23, 26),
            (self.controller.state.campaign.warriors[1], 19, 21),
        ):
            card = tk.Frame(parent, bg=COLORS["panel_alt"], padx=12, pady=10)
            card.pack(fill="x", pady=(0, 7))
            top = tk.Frame(card, bg=COLORS["panel_alt"])
            top.pack(fill="x")
            tk.Label(top, text=warrior.name, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Georgia", 11)).pack(side="left")
            tk.Label(top, text=f"XP {before} → {after}", bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(side="right")
            tk.Label(card, text="Survived +1   ·   Scenario / objectives +1", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(5, 5))
            ExperienceTrack(card, after, previous_experience=before, track_type="hero").pack(fill="x")

        tk.Label(parent, text="ADVANCEMENTS TRIGGERED BY THIS XP", bg=COLORS["panel"], fg=COLORS["accent"], font=("Segoe UI Semibold", 8)).pack(anchor="w", pady=(7, 6))
        DiceResolutionCard(
            parent, title="Mother Superior", subtitle="Crossed an advancement threshold · Hero Advancement roll",
            notation="2D6", dice_count=2, demo_dice=(3, 4), combine="sum",
            outcome_title="New Skill", outcome_detail="Choose one legal skill list",
            choices=("Combat", "Academic", "Strength", "Special"),
        ).pack(fill="x", pady=(0, 9))
        DiceResolutionCard(
            parent, title="Sigmarite Sisters", subtitle="Henchman group crossed an advancement threshold",
            notation="2D6", dice_count=2, demo_dice=(2, 4), combine="sum",
            outcome_title="Characteristic", outcome_detail="Choose one legal result",
            choices=("+1 WS", "+1 BS"),
        ).pack(fill="x", pady=(0, 8))

    def _exploration(self, parent: tk.Misc, _battle) -> None:
        resolver = self.controller.post_battle_resolver()
        self._title(parent, "03 · Exploration", f"Roll once for each eligible Hero, plus one die when the warband won. Shards come from the KB shard chart; matching dice open the KB special-result table. {self._kb_provenance(2)}")
        dice_count = resolver.exploration_dice(surviving_heroes=4, warband_won=False)
        resolved = resolver.resolve_exploration((3, 3, 5, 6))
        detail = f"Total {resolved.total} → {resolved.shards} wyrdstone shard(s)"
        if resolved.matching_dice_note:
            detail += f" · {resolved.matching_dice_note}"
        DiceResolutionCard(
            parent, title="Exploration Dice", subtitle=f"Eligible Heroes: 4 · {dice_count}D6 from the KB allocation",
            notation=f"{dice_count}D6", dice_count=dice_count, demo_dice=(3, 3, 5, 6), combine="list",
            outcome_title=f"Exploration resolved · {resolved.shards} shard(s)", outcome_detail=detail,
            on_resolved=lambda dice, _r=resolver: _exploration_card(dice, _r),
        ).pack(fill="x")

    def _sell_wyrdstone(self, parent: tk.Misc, _battle) -> None:
        self._title(parent, "04 · Sell Wyrdstone", f"Choose how many shards to sell. This action can only be performed once in the post-battle sequence; the sale value is derived automatically. {self._kb_provenance(3)}")
        SummaryStrip(parent, [("In stash", "4 shards"), ("Sell now", "3 shards"), ("Keep", "1 shard"), ("Income", "Auto")]).pack(fill="x", pady=(0, 12))
        card = self._section(parent, "Choose quantity to sell", "The prototype keeps the calculation out of the player's workload.")
        row = tk.Frame(card, bg=COLORS["panel_alt"])
        row.pack(fill="x")
        tk.Label(row, text="Wyrdstone shards", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 9)).pack(side="left")
        sell_var = tk.IntVar(value=3)
        ttk.Spinbox(row, from_=0, to=4, width=5, textvariable=sell_var).pack(side="left", padx=12)
        ttk.Button(row, text="CALCULATE SALE", style="Accent.TButton", command=self._placeholder).pack(side="right")
        tk.Label(card, text="Sale value will use the current warband size and campaign rules automatically.", bg=COLORS["panel_alt"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(anchor="w", pady=(9, 0))

    def _veterans(self, parent: tk.Misc, _battle) -> None:
        self._title(parent, "05 · Available Veterans", f"Determine the post-battle experience pool available for hiring experienced recruits. You are not committing to hire anyone yet. {self._kb_provenance(4)}")
        DiceResolutionCard(
            parent, title="Veteran Experience Pool", subtitle="Availability check before recruitment",
            notation="2D6", dice_count=2, demo_dice=(4, 3), combine="sum",
            outcome_title="7 XP available", outcome_detail="This pool can be used later in Recruitment",
        ).pack(fill="x")

    def _rare_and_dramatis(self, parent: tk.Misc, _battle) -> None:
        content = self.controller.post_battle_content()
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
            ttk.Combobox(controls, state="readonly", values=item_labels, width=42).pack(side="left")
            ttk.Button(controls, text="ADD SEARCH", style="Mini.TButton", command=self._placeholder).pack(side="left", padx=8)
            tk.Label(
                rare_section,
                text=f"Showing {min(len(rare), 12)} of {len(rare)} available entries from the KB trading post.",
                bg=COLORS["panel_alt"], fg=COLORS["muted_dark"], font=("Segoe UI", 7),
            ).pack(anchor="w", pady=(8, 0))
            resolver = self.controller.post_battle_resolver()
            search = resolver.resolve_rarity_search(rare[0].item_id, 9)  # demo preview: 2D6 = 5 & 4
            search_title = "Available" if search.success else "Not found"
            search_tone = "success" if search.success else "neutral"
            DiceResolutionCard(
                parent, title=f"Rare item availability search · {rare[0].name}",
                subtitle=("A successful search reveals a contextual Buy action. "
                          "Test resolved from the KB rarity rules against the offered item."),
                notation="2D6", dice_count=2, demo_dice=(5, 4), combine="sum",
                outcome_title=search_title, outcome_detail=search.note, outcome_tone=search_tone,
                on_resolved=lambda dice, _r=resolver, _id=rare[0].item_id, _n=rare[0].name: _rarity_card(dice, _r, _id, _n),
            ).pack(fill="x", pady=(10, 12))
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
            controls = tk.Frame(dramatis_section, bg=COLORS["panel_alt"])
            controls.pack(fill="x")
            labels = []
            for offer in dramatis[:12]:
                marker = " *" if offer.eligibility != "eligible" else ""
                label = f"{offer.name}{marker}"
                if offer.fee_label:
                    label += f" · {offer.fee_label}"
                labels.append(label)
            ttk.Combobox(controls, state="readonly", values=labels, width=40).pack(side="left")
            ttk.Button(controls, text="ASSIGN SEARCHERS", style="Mini.TButton", command=self._placeholder).pack(side="left", padx=8)
            DiceResolutionCard(
                parent, title="Dramatis Personae search", subtitle="One D6 per searcher · a result under the Hero's Initiative locates the character",
                notation="D6", dice_count=1, demo_dice=(3,), combine="sum",
                outcome_title="Located", outcome_detail="Character found · hiring remains optional",
                outcome_actions=(("HIRE", self._placeholder, "Accent.TButton"),),
            ).pack(fill="x", pady=(10, 0))
        else:
            tk.Label(
                dramatis_section, text="No Dramatis Personae are currently searchable by this warband.",
                bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8),
            ).pack(anchor="w")

    def _recruitment(self, parent: tk.Misc, _battle) -> None:
        content = self.controller.post_battle_content()
        hired = content.hired_swords()
        common = content.common_items()
        self._title(
            parent,
            "07 · Recruitment",
            f"Hire new warriors or Hired Swords and buy common items. This is the warband-building stage; rare-item searches are already closed. {self._kb_provenance(6)}",
        )
        SummaryStrip(parent, [("Treasury", "72 gc"), ("Veteran pool", "7 XP"), ("New hires", "0"), ("Common purchases", "0 gc")]).pack(fill="x", pady=(0, 12))

        warriors = [
            profile for profile in self.controller.port.profiles(
                self.controller.state.campaign.collection, self.controller.state.campaign.band_id, kind="henchman"
            )
            if profile.kind == "henchman"
        ]
        warrior_rows = tuple((profile.name, f"{profile.cost} gc") for profile in warriors)
        common_rows = tuple((f"{offer.name} · {offer.price_label}", offer.price_label) for offer in common[:14])
        for heading, detail, rows, limit_note in (
            ("WARRIORS", "Recruit new members or add to eligible Henchman groups (KB roster).", warrior_rows, f"{len(warriors)} recruit profiles"),
            ("HIRED SWORDS", "Hire available mercenaries and account for upkeep where applicable. * = acceptance roll or Mercenary-variant condition.", tuple(
                (f"{offer.name}{' *' if offer.eligibility != 'eligible' else ''} · {offer.availability_label.lower()}",
                 f"Hire {offer.fee_label or '—'} · Upkeep {offer.upkeep_label or '—'}")
                for offer in hired[:14]
            ), f"{len(hired)} available Hired Swords"),
            ("COMMON ITEMS", "Common equipment can be purchased without a rarity search (KB Trading Post).", common_rows, f"{len(common)} common items available"),
        ):
            if not rows:
                continue
            section = self._section(parent, heading, f"{detail} ({limit_note})")
            for name, cost in rows:
                row = tk.Frame(section, bg=COLORS["panel_alt"])
                row.pack(fill="x", pady=2)
                tk.Label(row, text=name, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8)).pack(side="left")
                ttk.Button(row, text=cost, style="Mini.TButton", command=self._placeholder).pack(side="right")

    def _equipment(self, parent: tk.Misc, _battle) -> None:
        # Purchase area: money is intentionally visible at the point where the
        # player spends it, rather than repeated across unrelated phases.
        content = self.controller.post_battle_content()
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
        tk.Label(purchase_head, text="72 gc", bg=COLORS["panel_alt"], fg=COLORS["accent"], font=("Georgia", 17)).pack(side="left", padx=(8, 20))
        tk.Label(purchase_head, text="Purchases are added to the stash", bg=COLORS["panel_alt"], fg=COLORS["muted_dark"], font=("Segoe UI", 7)).pack(side="left")

        chooser = tk.Frame(purchase, bg=COLORS["panel_alt"])
        chooser.pack(fill="x")
        tk.Label(chooser, text="ITEM", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).grid(row=0, column=0, sticky="w")
        tk.Label(chooser, text="QTY", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).grid(row=0, column=1, sticky="w", padx=(8, 0))
        tk.Label(chooser, text="COST", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).grid(row=0, column=2, sticky="w", padx=(8, 0))
        item_labels = [f"{offer.name} · {offer.price_label}" for offer in common[:14]]
        item = ttk.Combobox(chooser, state="readonly", values=item_labels, width=40)
        item.grid(row=1, column=0, sticky="ew", pady=(3, 0))
        if common:
            item.set(item_labels[0])
        qty = tk.IntVar(value=1)
        ttk.Spinbox(chooser, from_=1, to=10, width=5, textvariable=qty).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(3, 0))
        cost_var = tk.StringVar(value=common[0].price_label if common else "—")
        tk.Label(chooser, textvariable=cost_var, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI Semibold", 9)).grid(row=1, column=2, sticky="w", padx=(8, 14), pady=(3, 0))
        ttk.Button(chooser, text="BUY & ADD TO STASH", style="Accent.TButton", command=self._placeholder).grid(row=1, column=3, sticky="e", pady=(3, 0))
        chooser.columnconfigure(0, weight=1)
        if common:
            def update_cost(_event=None) -> None:
                selection = item.get()
                match = next((offer for offer in common if f"{offer.name} · {offer.price_label}" == selection), None)
                cost_var.set(match.price_label if match else "—")
            item.bind("<<ComboboxSelected>>", update_cost)
        tk.Label(
            purchase,
            text=f"{len(common)} common items are available to this warband (KB Trading Post); showing {min(len(common), 14)}. The list and the price update from the KB when the warband changes.",
            bg=COLORS["panel_alt"], fg=COLORS["muted_dark"], font=("Segoe UI", 7), wraplength=900, justify="left",
        ).pack(anchor="w", pady=(8, 0))

        # Lower workspace: one inventory list is the source of truth. It shows
        # ownership, current holders and unassigned stock, with contextual
        # assignment/sale actions instead of separate competing panels.
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True, pady=(5, 0))

        stash_tab = tk.Frame(notebook, bg=COLORS["panel"], padx=10, pady=10)
        warrior_tab = tk.Frame(notebook, bg=COLORS["panel"], padx=10, pady=10)
        notebook.add(stash_tab, text="STASH")
        notebook.add(warrior_tab, text="BY WARRIOR")

        stash_top = tk.Frame(stash_tab, bg=COLORS["panel"])
        stash_top.pack(fill="x", pady=(0, 7))
        tk.Label(stash_top, text="BAND INVENTORY", bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 11)).pack(side="left")
        tk.Label(stash_top, text="Owned 24  ·  Equipped 18  ·  Available 6", bg=COLORS["panel"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="right")

        stash_table = tk.Frame(stash_tab, bg=COLORS["border_soft"], padx=1, pady=1)
        stash_table.pack(fill="x")
        hdr = tk.Frame(stash_table, bg=COLORS["panel_deep"], padx=9, pady=6)
        hdr.pack(fill="x")
        for text, width in (("ITEM", 24), ("OWNED", 8), ("CURRENTLY EQUIPPED", 40), ("STASH", 8)):
            tk.Label(hdr, text=text, width=width, anchor="w", bg=COLORS["panel_deep"], fg=COLORS["muted"], font=("Segoe UI Semibold", 7)).pack(side="left")

        inventory_rows = (
            ("Sigmarite Warhammer", "1", "Mother Superior", "0"),
            ("Hammer", "5", "Sigmarite Sisters ×4", "1"),
            ("Sword", "3", "Sister Anna · Sister Veriet", "1"),
            ("Crossbow", "2", "Sister Marta", "1"),
            ("Light Armour", "4", "Mother Superior · Anna · Marta", "1"),
            ("Holy Relic", "1", "—", "1"),
            ("Rope & Hook", "2", "Sister Veriet", "1"),
        )
        for name, owned, equipped, available in inventory_rows:
            row = tk.Frame(stash_table, bg=COLORS["panel_alt"], padx=9, pady=5)
            row.pack(fill="x", pady=(1, 0))
            tk.Label(row, text=name, width=24, anchor="w", bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Segoe UI", 8)).pack(side="left")
            tk.Label(row, text=owned, width=8, anchor="w", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left")
            tk.Label(row, text=equipped, width=40, anchor="w", bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(side="left")
            tk.Label(row, text=available, width=8, anchor="w", bg=COLORS["panel_alt"], fg=COLORS["accent"] if available != "0" else COLORS["muted_dark"], font=("Segoe UI Semibold", 8)).pack(side="left")
            ttk.Button(row, text="ASSIGN", style="Mini.TButton", command=self._placeholder).pack(side="right", padx=(5, 0))
            ttk.Button(row, text="SELL", style="Mini.TButton", command=self._placeholder).pack(side="right", padx=(5, 0))

        tk.Label(
            stash_tab,
            text="Assign moves an available copy from the stash to an eligible warrior. Sell uses the campaign's current sale rules automatically.",
            bg=COLORS["panel"], fg=COLORS["muted_dark"], font=("Segoe UI", 7),
        ).pack(anchor="w", pady=(7, 0))

        tk.Label(warrior_tab, text="EQUIPMENT BY WARRIOR", bg=COLORS["panel"], fg=COLORS["text"], font=("Georgia", 11)).pack(anchor="w", pady=(0, 7))
        for warrior, current in (
            ("Mother Superior", "Sigmarite Warhammer · Light Armour · Rosary"),
            ("Sister Anna", "Sword · Shield · Light Armour"),
            ("Sister Marta", "Crossbow · Dagger · Light Armour"),
            ("Sister Veriet", "Sword · Rope & Hook"),
        ):
            row = tk.Frame(warrior_tab, bg=COLORS["panel_alt"], padx=10, pady=7)
            row.pack(fill="x", pady=(0, 3))
            left = tk.Frame(row, bg=COLORS["panel_alt"])
            left.pack(side="left", fill="x", expand=True)
            tk.Label(left, text=warrior, bg=COLORS["panel_alt"], fg=COLORS["text"], font=("Georgia", 9)).pack(anchor="w")
            tk.Label(left, text=current, bg=COLORS["panel_alt"], fg=COLORS["muted"], font=("Segoe UI", 8)).pack(anchor="w", pady=(2, 0))
            ttk.Button(row, text="MANAGE", style="Mini.TButton", command=self._placeholder).pack(side="right")

    def _review(self, parent: tk.Misc, battle) -> None:
        self._title(parent, "Final Review", f"All eight player actions are complete. This confirmation creates State #{battle.number}; warband rating is calculated automatically from the final roster.")
        SummaryStrip(parent, [("Rating", "183 → 194"), ("Models", "8 → 7"), ("Treasury", "72 → 91 gc"), ("Wyrdstone", "4 → 6")]).pack(fill="x", pady=(0, 12))
        for title, lines in (
            ("RECOVERY", ["Novice removed", "Mother Superior 23 → 26 XP", "2 advances resolved"]),
            ("EXPLORATION & INCOME", ["Exploration resolved", "+2 wyrdstone after sale decisions"]),
            ("SEARCHES", ["Veteran pool: 7 XP", "1 rare item found", "Dramatis search completed"]),
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

    def _placeholder(self) -> None:
        messagebox.showinfo("Prototype", "This control is intentionally visual-only in the interface prototype.", parent=self)

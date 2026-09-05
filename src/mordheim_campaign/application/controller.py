from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path

from mordheim_campaign.application.knowledge_port import KnowledgePort, WarbandProfile
from .state import AppState, BattleVM, PostBattleVM, WarbandStateVM, make_draft_state, make_example_state, warrior_vm


_ROMAN = ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))

#: Mercenary variants (Reikland/Middenheim/Marienburg/Ostermark) selectable by
#: variant-capable warbands, as (stable id, label).
VARIANT_CHOICES = (
    ("reikland", "Reikland"),
    ("middenheim", "Middenheim"),
    ("marienburg", "Marienburg"),
    ("ostermark", "Ostermark"),
)


def _roman(number: int) -> str:
    result = []
    for value, numeral in _ROMAN:
        while number >= value:
            result.append(numeral)
            number -= value
    return "".join(result)


class AppController:
    """Thin UI controller for the timeline-first campaign manager.

    The campaign timeline owns navigation between immutable states and the
    transitions that produce them. Band and profile data come from the KB
    through :class:`KnowledgePort`; Tk widgets never read YAML or the loaders.
    """

    def __init__(self, state: AppState | None = None, *, port: KnowledgePort | None = None) -> None:
        self.port = port or KnowledgePort()
        self.state = state if state is not None else make_draft_state(self.port, "sisters-of-sigmar")
        self.persist_path: Path | None = None
        self._listeners: list[Callable[[], None]] = []
        self._resolver = None

    def subscribe(self, listener: Callable[[], None]) -> None:
        self._listeners.append(listener)

    def notify(self) -> None:
        for listener in list(self._listeners):
            listener()

    def replace_state(self, state: AppState) -> None:
        self.state = state
        self.notify()

    def navigate(self, view: str) -> None:
        self.state.active_view = view
        self.notify()

    def set_campaign_mode(self, mode: str) -> None:
        self.state.campaign_mode = mode
        self.state.active_view = "campaign"
        self.notify()

    def select_moment(self, node_id: str) -> None:
        self.state.selected_moment = node_id
        self.state.active_view = "campaign"
        self.state.campaign_mode = "timeline"
        self.notify()

    def select_draft(self) -> None:
        self.select_moment("draft:0")

    def select_state(self, number: int) -> None:
        self.select_moment(f"state:{number}")

    def select_battle(self, number: int) -> None:
        self.select_moment(f"battle:{number}")

    def select_post_battle(self, number: int) -> None:
        self.select_moment(f"post:{number}")

    def set_state_section(self, section: str) -> None:
        self.state.state_section = section
        self.notify()

    def set_battle_section(self, section: str) -> None:
        self.state.battle_section = section
        self.notify()

    def set_inventory_mode(self, mode: str) -> None:
        self.state.inventory_mode = mode
        self.notify()

    def set_draft_warrior_tab(self, tab: str) -> None:
        self.state.draft_warrior_tab = tab
        self.state.selected_moment = "draft:0"
        self.notify()

    def set_post_battle_step(self, index: int) -> None:
        pending = self.state.campaign.pending_post_battle
        if pending is None:
            return
        # Completed steps may be revisited, but future steps are reached only
        # through the sequential Continue action. Final Review is outside the
        # eight rules-facing actions, so selecting a step closes Review.
        accessible = set(pending.completed_steps) | {pending.active_step}
        if index not in accessible:
            return
        pending.active_step = index
        pending.review_open = False
        self.state.selected_moment = pending.node_id
        self.state.active_view = "campaign"
        self.state.campaign_mode = "timeline"
        self.notify()

    def advance_post_battle_step(self) -> None:
        pending = self.state.campaign.pending_post_battle
        if pending is None:
            return
        from .state import POST_BATTLE_STEPS

        current = pending.active_step
        pending.completed_steps.add(current)
        if current >= len(POST_BATTLE_STEPS) - 1:
            # Rating is derived automatically. Once Equipment is complete the
            # eight-step sequence is done and the app opens a confirmation diff.
            pending.review_open = True
        else:
            pending.active_step = current + 1
            pending.review_open = False
        self.state.selected_moment = pending.node_id
        self.state.active_view = "campaign"
        self.state.campaign_mode = "timeline"
        self.notify()

    def open_post_battle_review(self) -> None:
        pending = self.state.campaign.pending_post_battle
        if pending is None:
            return
        from .state import POST_BATTLE_STEPS

        if len(pending.completed_steps) < len(POST_BATTLE_STEPS):
            return
        pending.review_open = True
        self.state.selected_moment = pending.node_id
        self.notify()

    def resume_pending_post_battle(self) -> None:
        pending = self.state.campaign.pending_post_battle
        if pending is not None:
            self.select_post_battle(pending.battle_number)

    # --------------------------------------------------------------- battles

    def scenario_options(self):
        """(id, name, player_mode) triples of the KB scenario catalogue."""
        return self.port.scenario_options()

    # ------------------------------------------------- equipment moves (any time)

    def assign_stash_item(self, item_id: str, warrior_id: str) -> tuple[bool, str]:
        """Assign one stash copy to a warrior (legal outside post-battle too)."""
        from mordheim_campaign.application.post_battle_engine import PostBattleEngine

        engine = PostBattleEngine(self.port, self.state.campaign, self.state.campaign.pending_post_battle)
        return engine.move_stash_to_warrior(item_id, warrior_id)

    def return_equipped_item(self, item_id: str, warrior_id: str) -> tuple[bool, str]:
        """Return one equipped copy to the stash (legal outside post-battle too)."""
        from mordheim_campaign.application.post_battle_engine import PostBattleEngine

        engine = PostBattleEngine(self.port, self.state.campaign, self.state.campaign.pending_post_battle)
        return engine.return_warrior_to_stash(item_id, warrior_id)

    def record_battle(
        self,
        *,
        scenario_id: str,
        scenario_name: str,
        opponent: str,
        result: str,
        xp_delta: int,
        casualties: int,
        gold_delta: int = 0,
        wyrdstone: int = 0,
        opponent_rating: int | None = None,
        notes: str = "",
        out_of_action_ids: list[str] | None = None,
    ) -> tuple[bool, str]:
        """Record a played battle and open its pending post-battle.

        Table facts only: the scenario comes from the KB catalogue and the
        derived numbers (rating, models) snapshot the warband *before* the
        post-battle mutations. The resulting ``PostBattleVM`` is the node the
        eight-step sequence then transforms into the next immutable state.
        """
        campaign = self.state.campaign
        if campaign.is_draft:
            return False, "Commit the initial warband before recording battles."
        if campaign.pending_post_battle is not None:
            return False, (
                f"Post-Battle #{campaign.pending_post_battle.battle_number} is still pending; "
                "commit it before recording the next battle."
            )
        known = {scenario_id for scenario_id, _name, _mode in self.port.scenario_options()}
        if scenario_id not in known:
            return False, f"Unknown scenario: {scenario_id}"
        result = result.strip().casefold().capitalize()
        if result not in ("Victory", "Defeat", "Draw"):
            return False, "Result must be Victory, Defeat or Draw."
        number = campaign.next_battle_number
        base = campaign.current_state
        battle = BattleVM(
            number=number,
            date=date.today().strftime("%d %b %Y"),
            scenario=scenario_name or scenario_id,
            opponent=opponent.strip() or "Unknown opponent",
            result=result,
            gold_delta=int(gold_delta),
            wyrdstone=max(0, int(wyrdstone)),
            xp_delta=max(0, int(xp_delta)),
            casualties=max(0, int(casualties)),
            advances=0,
            rating_before=base.rating,
            rating_after=base.rating,
            models_before=base.models,
            models_after=base.models,
            notes=notes.strip(),
            opponent_rating=opponent_rating,
            out_of_action_ids=list(out_of_action_ids) if out_of_action_ids else None,
        )
        if battle.out_of_action_ids is not None:
            battle.casualties = len(battle.out_of_action_ids)
        campaign.battles.append(battle)
        campaign.post_battles.append(PostBattleVM(battle_number=number, complete=False))
        self.select_battle(number)
        return True, f"Battle #{number} recorded · {battle.scenario} vs. {battle.opponent} ({result})."

    def latest_battle_number(self) -> int | None:
        """Number of the most recent battle (the one a dialog may extend)."""
        battles = self.state.campaign.battles
        return battles[-1].number if battles else None

    def go_to_current_state(self) -> None:
        if self.state.campaign.is_draft:
            self.select_draft()
        else:
            self.select_state(self.state.campaign.current_state_number)

    # ------------------------------------------------------------- campaigns

    def warband_options(self):
        """Canonical selectable warbands (read-only DTOs)."""
        return self.port.options()

    # ------------------------------------------------------- mercenary variant

    def variant_options(self):
        """(variant id, label) pairs when the warband may pick a variant."""
        from mordheim_campaign.application.hire_eligibility import VARIANT_CAPABLE_BANDS

        if self._campaign().band_id not in VARIANT_CAPABLE_BANDS:
            return ()
        return VARIANT_CHOICES

    def set_mercenary_variant(self, variant: str | None) -> None:
        """Stores the warband's Mercenary variant (``None`` clears it)."""
        variant = variant.strip().casefold() if variant else None
        if variant is not None and variant not in {identifier for identifier, _ in VARIANT_CHOICES}:
            return
        self._campaign().mercenary_variant = variant
        self.notify()

    def new_campaign(self, campaign_name: str, band_id: str) -> None:
        self.persist_path = None
        self.replace_state(make_draft_state(self.port, band_id, campaign_name=campaign_name))

    def open_creation_example(self) -> None:
        self.persist_path = None
        self.replace_state(make_draft_state(self.port, "sisters-of-sigmar", campaign_name="The Sisters of Morr"))

    def open_campaign_example(self) -> None:
        self.persist_path = None
        self.replace_state(make_example_state(self.port))

    def commit_initial_warband(self) -> None:
        campaign = self.state.campaign
        if not campaign.is_draft or not campaign.draft_is_legal:
            return
        campaign.is_draft = False
        campaign.started = date.today().strftime("%d %b %Y")
        campaign.current_state_number = 0
        campaign.states = [
            WarbandStateVM(
                number=0,
                date=campaign.started,
                gold=campaign.draft_treasury,
                wyrdstone=0,
                rating=campaign.draft_rating,
                models=campaign.draft_model_count,
                max_models=campaign.maximum_models,
                heroes=campaign.draft_hero_count,
                henchmen=campaign.draft_henchman_count,
                experience=campaign.draft_experience,
                label="Initial Warband",
            )
        ]
        self.state.selected_moment = "state:0"
        self.state.state_section = "overview"
        self.notify()

    # ------------------------------------------------------- draft roster edits

    def _campaign(self):
        return self.state.campaign

    def post_battle_resolver(self):
        """KB-backed post-battle dice resolution (cached per controller)."""
        from mordheim_campaign.application.post_battle_resolution import PostBattleResolver

        if self._resolver is None:
            self._resolver = PostBattleResolver(self.port)
        return self._resolver

    def post_battle_engine(self):
        """Write side of the pending post-battle, bound to the live campaign.

        Returns an engine whose post may be None when no sequence is pending;
        engine actions guard on that.
        """
        from mordheim_campaign.application.post_battle_engine import PostBattleEngine

        campaign = self._campaign()
        return PostBattleEngine(self.port, campaign, campaign.pending_post_battle)

    def commit_post_battle(self) -> tuple[bool, str]:
        """Commits the pending post-battle and navigates to its new State."""
        engine = self.post_battle_engine()
        ok, message = engine.commit()
        if ok:
            self.select_state(engine.post.battle_number)
            return True, message
        self.notify()
        return False, message

    def post_battle_content(self):
        """KB-fed offers and provenance for the pending post-battle screens."""
        from mordheim_campaign.application.post_battle_catalogue import PostBattleCatalogue

        campaign = self._campaign()
        return PostBattleCatalogue(
            self.port,
            campaign.collection,
            campaign.band_id,
            ruleset=campaign.ruleset,
            member_profile_ids=frozenset(
                row.profile_id for row in campaign.warriors if row.profile_id
            ),
            # Employed Hired Swords/Dramatis are roster members whose canonical
            # profile ids live under ``hireling.*``; the mutual-exclusion rules
            # (Highwayman/Roadwarden, Shadow Warrior, …) read them from here.
            hired_sword_profile_ids=frozenset(
                row.profile_id for row in campaign.warriors
                if row.profile_id and row.profile_id.startswith("hireling.")
            ),
            variant=campaign.mercenary_variant,
        )

    def addable_profiles(self, kind: str) -> tuple[WarbandProfile, ...]:
        """Profiles that can still be added to the draft (within the roster)."""
        campaign = self._campaign()
        if not campaign.is_draft or not campaign.band_id:
            return ()
        candidates = self.port.profiles(campaign.collection, campaign.band_id, kind=kind)
        result = []
        for profile in candidates:
            if profile.random_characteristics:
                continue
            _, maximum = self.profile_allowance(profile)
            if maximum is not None and maximum <= 0:
                continue
            result.append(profile)
        return tuple(result)

    def profile_allowance(self, profile: WarbandProfile) -> tuple[int, int | None]:
        """(models already taken, member cap) for a draft profile."""
        campaign = self._campaign()
        taken = sum(row.quantity for row in campaign.warriors if row.profile_id == profile.profile_id)
        return taken, profile.member_maximum

    def add_draft_warriors(self, profile_id: str, quantity: int = 1) -> tuple[bool, str]:
        """Add a warrior or group to the draft, validating canonical limits."""
        campaign = self._campaign()
        if not campaign.is_draft:
            return False, "Only the initial warband draft can be edited."
        try:
            profile = next(
                p for p in self.port.profiles(campaign.collection, campaign.band_id) if p.profile_id == profile_id
            )
        except StopIteration:
            return False, f"Unknown profile: {profile_id}"
        quantity = max(1, int(quantity))
        if profile.kind == "henchman" and profile.group_maximum is not None and quantity > profile.group_maximum:
            return False, f"Groups of {profile.name} hold at most {profile.group_maximum} models."
        taken, maximum = self.profile_allowance(profile)
        if maximum is not None and taken + quantity > maximum:
            remaining = maximum - taken
            return False, f"Roster limit for {profile.name} reached ({remaining} remaining)."
        cost = profile.cost * quantity
        if cost > campaign.draft_treasury:
            return False, f"Not enough gold: {profile.name} costs {cost} gc, treasury is {campaign.draft_treasury} gc."
        if campaign.draft_model_count + quantity > campaign.maximum_models:
            return False, f"Cannot exceed {campaign.maximum_models} models."
        if profile.kind == "hero" and campaign.draft_hero_count + quantity > campaign.hero_limit:
            return False, f"Cannot exceed {campaign.hero_limit} heroes."
        occurrences = sum(1 for row in campaign.warriors if row.profile_id == profile_id)
        row_id = f"{profile_id}#{occurrences + 1}"
        name = profile.name
        if profile.kind == "hero":
            name = self._unique_hero_name(profile.name)
        campaign.warriors.append(warrior_vm(profile, row_id=row_id, name=name, quantity=quantity))
        self.notify()
        return True, f"{name}{f' ×{quantity}' if quantity > 1 else ''} added to the draft."

    def adjust_draft_group(self, warrior_id: str, delta: int) -> tuple[bool, str]:
        """Resizes a henchman row keeping the limits in force."""
        campaign = self._campaign()
        row = next((w for w in campaign.warriors if w.id == warrior_id), None)
        if row is None or not campaign.is_draft:
            return False, "Only the initial warband draft can be edited."
        if row.kind == "hero":
            return False, "Heroes are individuals; add or remove them instead."
        profile = next(
            (p for p in self.port.profiles(campaign.collection, campaign.band_id) if p.profile_id == row.profile_id),
            None,
        )
        if profile is None:
            return False, "Profile is no longer available in the knowledge base."
        new_quantity = row.quantity + int(delta)
        if new_quantity < 1:
            return False, "A henchman group keeps at least one member."
        if profile.group_maximum is not None and new_quantity > profile.group_maximum:
            return False, f"Groups of {profile.name} hold at most {profile.group_maximum} models."
        added = new_quantity - row.quantity
        if added > 0:
            taken, maximum = self.profile_allowance(profile)
            if maximum is not None and taken + added > maximum:
                return False, f"Roster limit for {profile.name} reached."
            if added * profile.cost > campaign.draft_treasury:
                return False, "Not enough gold for the added members."
            if campaign.draft_model_count + added > campaign.maximum_models:
                return False, f"Cannot exceed {campaign.maximum_models} models."
        row.quantity = new_quantity
        self.notify()
        return True, f"{row.name} now has {new_quantity} member{'s' if new_quantity != 1 else ''}."

    def remove_draft_warrior(self, warrior_id: str) -> tuple[bool, str]:
        """Removes a draft row; legality is re-evaluated instantly."""
        campaign = self._campaign()
        if not campaign.is_draft:
            return False, "Only the initial warband draft can be edited."
        row = next((w for w in campaign.warriors if w.id == warrior_id), None)
        if row is None:
            return False, "Warrior not found in the draft."
        campaign.warriors.remove(row)
        self.notify()
        return True, f"{row.name} removed from the draft."

    def _unique_hero_name(self, base: str) -> str:
        taken = {row.name for row in self._campaign().warriors if row.kind == "hero"}
        if base not in taken:
            return base
        index = 2
        while f"{base} {_roman(index)}" in taken:
            index += 1
        return f"{base} {_roman(index)}"

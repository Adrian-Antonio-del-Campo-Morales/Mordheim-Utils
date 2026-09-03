from __future__ import annotations

from collections.abc import Callable
from datetime import date
from pathlib import Path

from mordheim_campaign.application.knowledge_port import KnowledgePort, WarbandProfile
from .state import AppState, WarbandStateVM, make_draft_state, make_example_state, warrior_vm


_ROMAN = ((10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"))


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

    def go_to_current_state(self) -> None:
        if self.state.campaign.is_draft:
            self.select_draft()
        else:
            self.select_state(self.state.campaign.current_state_number)

    # ------------------------------------------------------------- campaigns

    def warband_options(self):
        """Bandas canónicas seleccionables (DTOs de solo lectura)."""
        return self.port.options()

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

    def addable_profiles(self, kind: str) -> tuple[WarbandProfile, ...]:
        """Perfiles que aún pueden añadirse al borrador (sin exceder el roster)."""
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
        """(modelos actuales, tope de miembro) para un perfil del borrador."""
        campaign = self._campaign()
        taken = sum(row.quantity for row in campaign.warriors if row.profile_id == profile.profile_id)
        return taken, profile.member_maximum

    def add_draft_warriors(self, profile_id: str, quantity: int = 1) -> tuple[bool, str]:
        """Añade un guerrero o grupo al borrador validando límites canónicos."""
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
        """Cambia el tamaño de una fila de secuaces manteniendo los límites."""
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
        """Elimina una fila del borrador; la legalidad se revalúa al instante."""
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

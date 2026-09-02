from __future__ import annotations

from collections.abc import Callable
from datetime import date

from .state import AppState, WarbandStateVM, make_creation_demo_state, make_demo_state


class AppController:
    """Thin UI controller for the interface-first prototype.

    The campaign timeline owns navigation between immutable states and the
    transitions that produce them. Real use cases can replace these mutations
    later without making Tk widgets know about the KB or persistence.
    """

    def __init__(self, state: AppState) -> None:
        self.state = state
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

    def new_campaign(self, campaign_name: str, warband_type: str) -> None:
        self.replace_state(make_creation_demo_state(campaign_name=campaign_name, warband_type=warband_type, empty=True))

    def open_creation_example(self) -> None:
        self.replace_state(make_creation_demo_state())

    def open_campaign_example(self) -> None:
        self.replace_state(make_demo_state())

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

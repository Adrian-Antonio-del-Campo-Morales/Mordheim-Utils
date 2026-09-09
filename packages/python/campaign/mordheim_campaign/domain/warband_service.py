"""campaign.domain.warband_service: committing the initial warband.

Turns a legal draft into State #0: freezes the construction limits, folds the
fixed equipment into the inventory and appends the first immutable timeline
state with its roster/inventory snapshot. Pure over the campaign model; the
KB entered when the draft was built.
"""
from __future__ import annotations

import copy
from datetime import date

from mordheim_campaign.domain.models import CampaignVM, InventoryItemVM, WarbandStateVM


def commit_initial_warband(campaign: CampaignVM) -> tuple[bool, str]:
    """Commit the draft as State #0.

    Mutates ``campaign`` in place (draft → active). Returns ``(False, '')``
    when the draft is not legal or already committed.
    """
    if not campaign.is_draft or not campaign.draft_is_legal:
        return False, ""
    for warrior in campaign.warriors:
        for equipment in warrior.equipment:
            if not equipment.transferable or equipment.acquisition in {"purchase", "stash_assignment"}:
                continue
            row = next((item for item in campaign.inventory if item.id == equipment.item_id), None)
            if row is None:
                row = InventoryItemVM(equipment.item_id, equipment.name, "Equipment", 0, 0, 0, equipment.unit_cost)
                campaign.inventory.append(row)
            row.owned += equipment.quantity
            row.equipped += equipment.quantity
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
            max_models=campaign.effective_maximum_models,
            heroes=campaign.draft_hero_count,
            henchmen=campaign.draft_henchman_count,
            experience=campaign.draft_experience,
            label="Initial Warband",
            roster=copy.deepcopy(campaign.warriors),
            inventory=copy.deepcopy(campaign.inventory),
        )
    ]
    return True, f"State #0 committed: {campaign.states[0].models} models · rating {campaign.states[0].rating}."

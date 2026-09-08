"""application.state: compatibility facade over the campaign domain models.

The state model moved to :mod:`mordheim_campaign.domain.models` (web
migration Phase 2); every public name is re-exported unchanged so existing
imports keep working. New code should import from the domain directly:

    from mordheim_campaign.domain.models import CampaignVM
"""
from mordheim_campaign.domain.models import (
    POST_BATTLE_GROUPS,
    POST_BATTLE_STEPS,
    STAT_KEYS,
    AppState,
    BattleVM,
    CampaignVM,
    EquipmentEntryVM,
    InventoryItemVM,
    PostBattleVM,
    WarbandStateVM,
    WarriorVM,
    unique_warrior_name,
)
from mordheim_campaign.domain.builders import make_draft_state, make_example_state, warrior_vm

__all__ = [
    "POST_BATTLE_GROUPS",
    "POST_BATTLE_STEPS",
    "STAT_KEYS",
    "AppState",
    "BattleVM",
    "CampaignVM",
    "EquipmentEntryVM",
    "InventoryItemVM",
    "PostBattleVM",
    "WarbandStateVM",
    "WarriorVM",
    "make_draft_state",
    "make_example_state",
    "unique_warrior_name",
    "warrior_vm",
]

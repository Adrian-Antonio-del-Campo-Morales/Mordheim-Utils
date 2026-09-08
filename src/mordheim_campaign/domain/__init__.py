"""campaign.domain: pure campaign domain of the Warband Manager.

Models and use-case services of the campaign, independent of any UI toolkit,
locale singletons, the filesystem and the Knowledge Base loaders:

- ``models``            — the campaign state model (``AppState``, ``CampaignVM`,
  ``WarriorVM``, ``BattleVM``, ``PostBattleVM``, ``WarbandStateVM``,
  ``InventoryItemVM``, ``EquipmentEntryVM``) and the derived draft/timeline
  projections;
- ``builders``          — construction of a draft/example state from a
  :class:`~mordheim_campaign.application.knowledge_port.KnowledgePort`;
- ``battle_service``    — recording a battle and the pre-battle availability
  rules;
- ``warband_service``   — committing the initial warband (draft → State #0);
- ``timeline_service``  — post-battle step navigation rules.

Layer rule (executable in ``tests/architecture/test_boundaries.py``): the
domain imports neither Tkinter/React, nor ``mordheim_ui``, nor locale
singletons, nor ``pathlib``.
"""
from .models import (
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
from .builders import make_draft_state, make_example_state, warrior_vm

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

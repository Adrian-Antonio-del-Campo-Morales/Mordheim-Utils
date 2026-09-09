from __future__ import annotations

from mordheim_campaign.domain.models import EquipmentEntryVM, WarriorVM


def displayed_equipment_quantity(warrior: WarriorVM, item: EquipmentEntryVM) -> int:
    """Return copies per model, not the group's aggregate inventory count."""
    quantity = item.quantity
    group_size = warrior.quantity
    if (
        warrior.kind == "henchman"
        and group_size > 1
        and item.per_model
        and quantity % group_size == 0
    ):
        return quantity // group_size
    return quantity


def equipment_quantity_suffix(warrior: WarriorVM, item: EquipmentEntryVM) -> str:
    quantity = displayed_equipment_quantity(warrior, item)
    return f" ×{quantity}" if quantity > 1 else ""

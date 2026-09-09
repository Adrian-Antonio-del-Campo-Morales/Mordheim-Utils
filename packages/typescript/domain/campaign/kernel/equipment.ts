/**
 * P3.5: equipment assignment between stash and warriors — the basis for the
 * P6.3 block, implementing the frozen `assignEquipment` use case.
 *
 * Conservation rule: `owned = equipped + stash` per inventory row; moving
 * equipment to a warrior increments `equipped` (and the warrior's entry),
 * moving back increments `stash`. Quantities must be available; transferable
 * equipment only (non-transferable rows are fixed to their owner).
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { IdString } from "../index";
import type {
  Campaign,
  CampaignDocument,
  EquipmentEntry,
  InventoryItem,
  UseCaseResult,
  Warrior,
} from "./usecases";
import { rejected } from "./rejections";
import { findInventoryItem, findWarrior, withCampaign } from "./document";

export interface AssignEquipmentInput {
  readonly warrior_id: IdString;
  readonly item_id: IdString;
  readonly quantity: number;
  readonly direction: "equip" | "stash";
}

/** Applies the inventory-side delta of an assignment; null when stock is short. */
function moveInventory(
  inventory: readonly InventoryItem[],
  itemId: IdString,
  quantity: number,
  field: "equipped" | "stash",
): InventoryItem[] | null {
  const next: InventoryItem[] = [];
  for (const item of inventory) {
    if (item.id !== itemId) {
      next.push(item);
      continue;
    }
    const available = field === "equipped" ? item.stash : item.equipped;
    if (available < quantity) return null;
    next.push(
      field === "equipped"
        ? { ...item, stash: item.stash - quantity, equipped: item.equipped + quantity }
        : { ...item, equipped: item.equipped - quantity, stash: item.stash + quantity },
    );
  }
  return next;
}

/**
 * Assign equipment between the stash and a warrior. Rejects unknown
 * warriors/items, non-positive quantities, unavailable stock and
 * non-transferable rows.
 */
export function assignEquipment(
  document: CampaignDocument,
  input: AssignEquipmentInput,
): UseCaseResult {
  if (!Number.isInteger(input.quantity) || input.quantity <= 0) {
    return rejected("invalid_input", "Assignment quantity must be a positive integer.");
  }
  const warrior = findWarrior(document, input.warrior_id);
  if (!warrior) {
    return rejected("not_found", `Unknown warrior id: ${input.warrior_id}.`);
  }
  const item = findInventoryItem(document, input.item_id);
  if (!item) {
    return rejected("not_found", `Unknown inventory item id: ${input.item_id}.`);
  }
  if (item.owned !== item.equipped + item.stash) {
    return rejected(
      "conflict",
      `Inventory row "${item.id}" is inconsistent (owned ${item.owned} ≠ equipped ${item.equipped} + stash ${item.stash}).`,
    );
  }

  if (input.direction === "equip") {
    if (item.stash < input.quantity) {
      return rejected(
        "limit_violated",
        `Only ${item.stash} of "${item.id}" in the stash; cannot equip ${input.quantity}.`,
      );
    }
    const existingEntry = warrior.equipment.find((e) => e.item_id === input.item_id);
    const updated: EquipmentEntry = existingEntry
      ? { ...existingEntry, quantity: (existingEntry.quantity ?? 1) + input.quantity, acquisition: "stash_assignment" as const }
      : {
          item_id: input.item_id,
          name: item.name,
          quantity: input.quantity,
          acquisition: "stash_assignment" as const,
          ...(item.value !== undefined ? { unit_cost: item.value } : {}),
        };
    const entries: EquipmentEntry[] = existingEntry
      ? warrior.equipment.map((e) => (e === existingEntry ? updated : e))
      : [...warrior.equipment, updated];
    const inventory = moveInventory(document.campaign.inventory, input.item_id, input.quantity, "equipped");
    if (inventory === null) {
      return rejected("limit_violated", `Not enough "${item.id}" in the stash.`);
    }
    const nextWarriors: Warrior[] = document.campaign.warriors.map((w) =>
      w.id === input.warrior_id ? { ...w, equipment: entries } : w,
    );
    const campaign: Campaign = { ...document.campaign, warriors: nextWarriors, inventory };
    return { ok: true, state: withCampaign(document, campaign) };
  }

  // direction === "stash": take equipped units back from the warrior.
  const equippedEntry = warrior.equipment.find(
    (e) => e.item_id === input.item_id && e.acquisition !== "fixed",
  );
  if (!equippedEntry || equippedEntry.quantity < input.quantity) {
    return rejected(
      "limit_violated",
      `${warrior.name} does not carry ${input.quantity} of "${item.id}" to return.`,
    );
  }
  const inventory = moveInventory(document.campaign.inventory, input.item_id, input.quantity, "stash");
  if (inventory === null) {
    return rejected("limit_violated", `Not enough "${item.id}" equipped to return.`);
  }
  const nextWarriors: Warrior[] = document.campaign.warriors.map((w) =>
    w.id === input.warrior_id
      ? {
          ...w,
          equipment: w.equipment
            .map((e) =>
              e === equippedEntry ? { ...e, quantity: e.quantity - input.quantity } : e,
            )
            .filter((e) => e.quantity > 0),
        }
      : w,
  );
  const campaign: Campaign = { ...document.campaign, warriors: nextWarriors, inventory };
  return { ok: true, state: withCampaign(document, campaign) };
}

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

import type { IdString, KnowledgeReader } from "../index";
import type {
  Campaign,
  CampaignDocument,
  EquipmentEntry,
  InventoryItem,
  UseCaseResult,
  Warrior,
} from "./usecases";
import { rejected } from "./rejections";
import { findInventoryItem, findWarrior, treasury, withCampaign } from "./document";

export interface DraftEquipmentPurchaseInput {
  readonly warrior_id: IdString;
  readonly item_id: IdString;
  /** Required only for a KB offer whose creation price is dice-resolved. */
  readonly unit_price?: number;
}

export interface DraftEquipmentRemovalInput {
  readonly warrior_id: IdString;
  readonly item_id: IdString;
  readonly unit_price?: number;
}

export interface DraftStashPurchaseInput {
  readonly item_id: IdString;
  readonly quantity: number;
  readonly unit_price?: number;
}

export interface DraftStashRemovalInput {
  readonly item_id: IdString;
  readonly quantity: number;
}

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
  // Withdrawals validate the warrior's own entry first: a fixed (profile)
  // entry is not transferable even when the inventory has no matching row.
  if (input.direction === "stash") {
    const targetEntry = warrior.equipment.find((e) => e.item_id === input.item_id);
    if (targetEntry && targetEntry.acquisition === "fixed") {
      return rejected(
        "limit_violated",
        `"${input.item_id}" is fixed equipment of ${warrior.name} and cannot be moved.`,
      );
    }
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
    // A draft can carry a purchased copy and a later stash-assigned copy of
    // same item. Keep acquisition provenance separate; never rewrite fixed
    // or paid equipment into a stash assignment.
    const existingEntry = warrior.equipment.find(
      (e) => e.item_id === input.item_id && e.acquisition === "stash_assignment",
    );
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
  // (Fixed entries were already rejected above; the entry must exist and
  // cover the requested quantity.)
  const equippedEntry = warrior.equipment.find(
    (e) => e.item_id === input.item_id && e.acquisition !== "fixed",
  );
  if (!equippedEntry || (equippedEntry.quantity ?? 1) < input.quantity) {
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

/**
 * Purchase one permitted item for every model in a draft row.  This is the
 * immutable counterpart of desktop `Controller.buy_draft_equipment`: the
 * profile's equipment list is the authority, and its listed cost wins over
 * the generic catalogue value.
 */
export function buyDraftEquipment(
  document: CampaignDocument,
  input: DraftEquipmentPurchaseInput,
  knowledge: KnowledgeReader,
): UseCaseResult {
  if (!document.campaign.configuration.is_draft) {
    return rejected("not_permitted_when_committed", "Only draft warriors can buy creation equipment.");
  }
  const warrior = findWarrior(document, input.warrior_id);
  if (!warrior || warrior.kind === "hireling" || !warrior.profile_id) {
    return rejected("not_found", "Draft warrior is not eligible for creation equipment.");
  }
  const profile = knowledge.queryKnowledge({ id: { kind: "profile_id", value: warrior.profile_id } });
  if (!profile.ok || (typeof profile.record.data["band_id"] === "string" && profile.record.data["band_id"] !== document.campaign.identity.band_id)) {
    return rejected("not_found", `Unknown profile id: ${warrior.profile_id}.`);
  }
  const access = Array.isArray(profile.record.data["equipment_access"])
    ? profile.record.data["equipment_access"] as Readonly<Record<string, unknown>>[]
    : [];
  const offer = access.find((row) => row["item_id"] === input.item_id);
  if (!offer) {
    return rejected("not_available", "This warrior cannot buy that item.");
  }
  const listedPrice = offer["cost"];
  const price = typeof listedPrice === "number" ? listedPrice : input.unit_price;
  if (!Number.isInteger(price) || price < 0) {
    return rejected("invalid_input", "Resolve a valid creation price before buying this item.");
  }
  const item = knowledge.queryKnowledge({ id: { kind: "item_id", value: input.item_id } });
  if (!item.ok) return rejected("not_found", `Unknown item id: ${input.item_id}.`);
  const quantity = warrior.quantity ?? 1;
  const total = price * quantity;
  if (total > treasury(document.campaign)) {
    return rejected("limit_violated", `Not enough gold: ${total} gc needed, ${treasury(document.campaign)} gc available.`);
  }
  const name = item.record.names["en"] ?? input.item_id;
  const existing = warrior.equipment.find((entry) => entry.item_id === input.item_id && entry.acquisition === "purchase" && entry.unit_cost === price);
  const equipment: EquipmentEntry[] = existing
    ? warrior.equipment.map((entry) => entry === existing ? { ...entry, quantity: entry.quantity + quantity } : entry)
    : [...warrior.equipment, { item_id: input.item_id, name, quantity, acquisition: "purchase", unit_cost: price, per_model: true }];
  const existingInventory = findInventoryItem(document, input.item_id);
  const inventory: InventoryItem[] = existingInventory
    ? document.campaign.inventory.map((entry) => entry.id === input.item_id ? { ...entry, owned: entry.owned + quantity, equipped: entry.equipped + quantity } : entry)
    : [...document.campaign.inventory, { id: input.item_id, name, category: String(item.record.data["kind"] ?? "Equipment"), owned: quantity, equipped: quantity, stash: 0, value: price }];
  const campaign: Campaign = {
    ...document.campaign,
    warriors: document.campaign.warriors.map((entry) => entry.id === warrior.id ? { ...entry, equipment } : entry),
    inventory,
  };
  return { ok: true, state: withCampaign(document, campaign) };
}

/** Refund a purchased draft loadout, returning its exact recorded price. */
export function removeDraftEquipment(
  document: CampaignDocument,
  input: DraftEquipmentRemovalInput,
): UseCaseResult {
  if (!document.campaign.configuration.is_draft) {
    return rejected("not_permitted_when_committed", "Only a draft can remove creation equipment.");
  }
  const warrior = findWarrior(document, input.warrior_id);
  const purchase = warrior?.equipment.find((entry) => entry.item_id === input.item_id && entry.acquisition === "purchase" && (input.unit_price === undefined || entry.unit_cost === input.unit_price));
  if (!warrior || !purchase) return rejected("not_found", "Purchased item not found on this draft warrior.");
  const stock = findInventoryItem(document, input.item_id);
  if (!stock || stock.owned < purchase.quantity || stock.equipped < purchase.quantity) {
    return rejected("conflict", "Draft inventory does not contain the purchased loadout.");
  }
  const inventory = document.campaign.inventory
    .map((entry) => entry.id === input.item_id ? { ...entry, owned: entry.owned - purchase.quantity, equipped: entry.equipped - purchase.quantity } : entry)
    .filter((entry) => entry.owned > 0);
  const campaign: Campaign = {
    ...document.campaign,
    warriors: document.campaign.warriors.map((entry) => entry.id === warrior.id ? { ...entry, equipment: entry.equipment.filter((item) => item !== purchase) } : entry),
    inventory,
  };
  return { ok: true, state: withCampaign(document, campaign) };
}

/** Buy unassigned creation equipment from this warband's canonical lists. */
export function buyDraftStashItem(
  document: CampaignDocument,
  input: DraftStashPurchaseInput,
  knowledge: KnowledgeReader,
): UseCaseResult {
  if (!document.campaign.configuration.is_draft) return rejected("not_permitted_when_committed", "Draft stash is only available during initial creation.");
  if (!Number.isInteger(input.quantity) || input.quantity <= 0) return rejected("invalid_input", "Purchase quantity must be a positive integer.");
  const band = knowledge.queryKnowledge({ id: { kind: "band_id", value: document.campaign.identity.band_id } });
  if (!band.ok) return rejected("not_found", `Unknown warband id: ${document.campaign.identity.band_id}.`);
  const access = Array.isArray(band.record.data["equipment_access"]) ? band.record.data["equipment_access"] as Readonly<Record<string, unknown>>[] : [];
  const offer = access.filter((row) => row["item_id"] === input.item_id).sort((left, right) => Number(left["cost"] ?? Infinity) - Number(right["cost"] ?? Infinity))[0];
  if (!offer) return rejected("not_available", "This warband cannot buy that item during creation.");
  const price = typeof offer["cost"] === "number" ? offer["cost"] : input.unit_price;
  if (!Number.isInteger(price) || price < 0) return rejected("invalid_input", "Resolve a valid creation price before buying this item.");
  const total = price * input.quantity;
  if (total > treasury(document.campaign)) return rejected("limit_violated", `Not enough gold: ${total} gc needed, ${treasury(document.campaign)} gc available.`);
  const item = knowledge.queryKnowledge({ id: { kind: "item_id", value: input.item_id } });
  if (!item.ok) return rejected("not_found", `Unknown item id: ${input.item_id}.`);
  const name = item.record.names["en"] ?? input.item_id;
  const existing = findInventoryItem(document, input.item_id);
  const inventory: InventoryItem[] = existing
    ? document.campaign.inventory.map((entry) => entry.id === input.item_id ? { ...entry, owned: entry.owned + input.quantity, stash: entry.stash + input.quantity, value: price } : entry)
    : [...document.campaign.inventory, { id: input.item_id, name, category: String(item.record.data["kind"] ?? "Equipment"), owned: input.quantity, equipped: 0, stash: input.quantity, value: price }];
  return { ok: true, state: withCampaign(document, { ...document.campaign, inventory }) };
}

/** Refund unassigned draft stash copies at their recorded acquisition price. */
export function removeDraftStashItem(document: CampaignDocument, input: DraftStashRemovalInput): UseCaseResult {
  if (!document.campaign.configuration.is_draft) return rejected("not_permitted_when_committed", "Draft stash is only available during initial creation.");
  if (!Number.isInteger(input.quantity) || input.quantity <= 0) return rejected("invalid_input", "Removal quantity must be a positive integer.");
  const item = findInventoryItem(document, input.item_id);
  if (!item) return rejected("not_found", `Unknown inventory item id: ${input.item_id}.`);
  if (item.stash < input.quantity) return rejected("limit_violated", `Only ${item.stash} unassigned copy/copies are available.`);
  const inventory = document.campaign.inventory
    .map((entry) => entry.id === input.item_id ? { ...entry, owned: entry.owned - input.quantity, stash: entry.stash - input.quantity } : entry)
    .filter((entry) => entry.owned > 0);
  return { ok: true, state: withCampaign(document, { ...document.campaign, inventory }) };
}

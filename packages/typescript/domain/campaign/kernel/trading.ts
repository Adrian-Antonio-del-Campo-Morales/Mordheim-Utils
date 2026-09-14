/**
 * Campaign hirelings, exploration and trading: the application-facing
 * kernel pieces the feature block needs beyond the P3.5 base.
 *
 * Trading rule (ported from the desktop `Controller.buy_draft_stash_item`,
 * phase-agnostic): a purchase moves gold into inventory as a stash row —
 * `owned` and `stash` rise together, `value` records the unit price actually
 * paid. Gold is *implicit* (Python `treasury` = starting gold − recruitment
 * − equipment), so a purchase only has to keep the valuation honest.
 * A sale reverses it: stock leaves `owned`/`stash`, and the sale price is
 * recorded as a battle-less income entry in the timeline's manual log —
 * the desktop books campaign income the same non-destructive way.
 *
 * Availability and band restrictions are the application layer's job (the
 * eligibility rules live in `application/features/hirelings/`); this module
 * enforces the inventory-side invariants only.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { IdString, OpenPayload } from "../index";
import type {
  Campaign,
  CampaignDocument,
  InventoryItem,
  UseCaseResult,
} from "./usecases";
import { rejected } from "./rejections";
import { findInventoryItem, treasury, withCampaign } from "./document";

export interface BuyTradingItemInput {
  readonly item_id: IdString;
  /** Stable KB id of the trading-post offer (for display and provenance). */
  readonly offer_id?: IdString;
  /** Volatile display name of the item (never used for identity). */
  readonly name: string;
  readonly category?: string;
  /** Unit price in gold crowns actually agreed (already dice-resolved). */
  readonly unit_price: number;
  readonly quantity: number;
}

export interface SellStashItemInput {
  readonly item_id: IdString;
  readonly quantity: number;
  /** Sale price per unit in gold crowns (dice-resolved by the caller). */
  readonly unit_price: number;
}

/** Appends (or grows) a stash row; returns null when the price is unusable. */
function stashRowFor(
  inventory: readonly InventoryItem[],
  input: BuyTradingItemInput,
): InventoryItem[] | null {
  if (!Number.isInteger(input.unit_price) || input.unit_price < 0) return null;
  const existing = inventory.find((item) => item.id === input.item_id);
  if (existing) {
    return inventory.map((item) =>
      item.id === input.item_id
        ? { ...item, owned: item.owned + input.quantity, stash: item.stash + input.quantity }
        : item,
    );
  }
  return [
    ...inventory,
    {
      id: input.item_id,
      name: input.name,
      category: input.category ?? "Trading Post",
      owned: input.quantity,
      equipped: 0,
      stash: input.quantity,
      value: input.unit_price,
    },
  ];
}

/**
 * Buys an item into the stash. Rejects non-positive quantities, unusable
 * prices and a resulting negative treasury; everything else is inventory
 * bookkeeping the caller can trust.
 */
export function buyTradingItem(
  document: CampaignDocument,
  input: BuyTradingItemInput,
): UseCaseResult {
  if (!Number.isInteger(input.quantity) || input.quantity <= 0) {
    return rejected("invalid_input", "Purchase quantity must be a positive integer.");
  }
  if (!Number.isInteger(input.unit_price) || input.unit_price < 0) {
    return rejected("invalid_input", `Invalid price: ${input.unit_price}.`);
  }
  const campaign = document.campaign;
  if (campaign.configuration.is_draft) {
    return rejected("not_permitted_in_draft", "Buy through the draft equipment panel; trading opens after the warband is committed.");
  }
  const total = input.unit_price * input.quantity;
  const available = treasury(campaign);
  if (total > available) {
    return rejected(
      "limit_violated",
      `Not enough gold: ${total} gc needed, ${available} gc available.`,
    );
  }
  const inventory = stashRowFor(campaign.inventory, input);
  if (!inventory) {
    return rejected("invalid_input", `Invalid price: ${input.unit_price}.`);
  }
  const campaign_next: Campaign = { ...campaign, inventory };
  return { ok: true, state: withCampaign(document, campaign_next) };
}

/**
 * Sells from the stash. Stock conservation holds (`owned = equipped + stash`
 * stays true per row; rows vanishing at zero owned are removed, mirroring
 * the desktop). The sale is booked in `manual_log` as an open payload —
 * income resolution itself is an exploration/post-battle matter, never
 * invented here.
 */
export function sellStashItem(
  document: CampaignDocument,
  input: SellStashItemInput,
): UseCaseResult {
  if (!Number.isInteger(input.quantity) || input.quantity <= 0) {
    return rejected("invalid_input", "Sale quantity must be a positive integer.");
  }
  if (!Number.isInteger(input.unit_price) || input.unit_price < 0) {
    return rejected("invalid_input", `Invalid price: ${input.unit_price}.`);
  }
  const campaign = document.campaign;
  const row = findInventoryItem(document, input.item_id);
  if (!row) {
    return rejected("not_found", `Unknown inventory item: ${input.item_id}.`);
  }
  if (row.stash < input.quantity) {
    return rejected(
      "limit_violated",
      `Only ${row.stash} in stash for "${input.item_id}" — cannot sell ${input.quantity}.`,
    );
  }
  const owned = row.owned - input.quantity;
  const inventory: InventoryItem[] = campaign.inventory
    .map((item) =>
      item.id === input.item_id
        ? { ...item, owned: owned, stash: item.stash - input.quantity }
        : item,
    )
    .filter((item) => item.owned > 0);
  const entry: OpenPayload = {
    type: "stash_sale",
    item_id: input.item_id,
    quantity: input.quantity,
    unit_price: input.unit_price,
    total: input.unit_price * input.quantity,
  };
  const campaign_next: Campaign = {
    ...campaign,
    inventory,
    manual_log: [...campaign.manual_log, entry],
  };
  return { ok: true, state: withCampaign(document, campaign_next) };
}

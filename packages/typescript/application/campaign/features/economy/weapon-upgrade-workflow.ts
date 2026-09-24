/**
 * Post-battle weapon upgrades — the TS counterpart of desktop
 * `PostBattleEngine.buy_weapon_upgrade`, pinning the engine-side guards the
 * desktop matrix asserts (forged-price rejection, duplicate-upgrade
 * rejection, stash availability).
 *
 * A weapon upgrade consumes one stashed base weapon and replaces it with the
 * upgraded record at `expected = base value × offer multiplier`, charging the
 * pending post-battle's gold delta.
 *
 * Purity: no React, no DOM, no filesystem. The KB is read through the
 * injected `KnowledgeReader` only.
 *
 */

import type { CampaignDocument, KnowledgeReader } from "../../../../domain/campaign/index";
import { withCampaign } from "../../../../domain/campaign/kernel/document";

interface CatalogueReader extends KnowledgeReader {
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
  list?(kind: string): readonly Readonly<Record<string, unknown>>[];
}

export interface WeaponUpgradeInput {
  /** Upgrade offer id (e.g. "gromril_weapon"). */
  readonly item_id: string;
  /** Inventory row id of the stashed base weapon (e.g. "axe"). */
  readonly target_id: string;
  /** Agreed price in gc; must equal `target.value × multiplier`. */
  readonly unit_price: number;
}

export type WeaponUpgradeResult =
  | { readonly ok: true; readonly document: CampaignDocument }
  | { readonly ok: false; readonly message: string };

function titleCase(value: string): string {
  return value.replace(/[-_]+/g, " ").replace(/\b\w/g, (letter) => letter.toLocaleUpperCase());
}

export function buyWeaponUpgrade(
  document: CampaignDocument,
  reader: CatalogueReader,
  input: WeaponUpgradeInput,
): WeaponUpgradeResult {
  const post = document.campaign.post_battles.find((row) => !row.complete);
  if (!post) {
    return { ok: false, message: "Weapon upgrades are only available during post-battle." };
  }
  const target = document.campaign.inventory.find((row) => row.id === input.target_id);
  if (!target || target.stash < 1) {
    return { ok: false, message: "The selected base weapon is not available in the stash." };
  }
  const offers = Array.isArray(reader.campaignSection?.("trading-post").items)
    ? reader.campaignSection("trading-post").items as Readonly<Record<string, unknown>>[]
    : [];
  const offer = offers.find((row) => row.item_id === input.item_id);
  const price = offer?.price && typeof offer.price === "object"
    ? offer.price as Readonly<Record<string, unknown>>
    : {};
  const multiplier = price.multiplier;
  if (!offer || typeof multiplier !== "number") {
    return { ok: false, message: "This weapon upgrade is not available to the warband in this phase." };
  }
  // Warband availability restrictions (desktop catalogue: warband_only /
  // warband_forbidden / condition rows).
  const groups = new Set(
    (reader.list?.("warband_group") ?? [])
      .filter((row) => Array.isArray(row.band_ids) && (row.band_ids as unknown[]).map(String).includes(document.campaign.identity.band_id))
      .map((row) => String(row.id ?? "")),
  );
  for (const restriction of Array.isArray(offer.restrictions) ? offer.restrictions as Readonly<Record<string, unknown>>[] : []) {
    const bandIds = (restriction.band_ids ?? []) as unknown[];
    const groupIds = (restriction.groups ?? []) as unknown[];
    const matches = bandIds.map(String).includes(document.campaign.identity.band_id)
      || groupIds.map(String).some((id) => groups.has(id));
    if (restriction.type === "warband_only" && !matches) {
      return { ok: false, message: "This weapon upgrade is not available to this warband." };
    }
    if (restriction.type === "warband_forbidden" && matches) {
      return { ok: false, message: "This weapon upgrade is forbidden to this warband." };
    }
    if (restriction.type === "condition") {
      return { ok: false, message: String(restriction.note ?? "This weapon upgrade cannot be purchased here.") };
    }
  }

  const baseId = target.base_item_id ?? target.id;
  const base = reader.queryKnowledge({ id: { kind: "item_id", value: baseId } });
  const kind = base.ok ? String(base.record.data.kind ?? "") : "";
  if (kind !== "close-combat-weapon" && kind !== "ranged-weapon") {
    return { ok: false, message: "Only weapons can receive this upgrade." };
  }
  const offerKnown = reader.queryKnowledge({ id: { kind: "item_id", value: input.item_id } });
  const offerName = offerKnown.ok
    ? String(offerKnown.record.names.en ?? offerKnown.record.names.es ?? "") || titleCase(input.item_id)
    : titleCase(input.item_id);
  if (target.id.startsWith(`${input.item_id}:`) || (target.special_rules ?? []).includes(offerName)) {
    return { ok: false, message: `${target.name} already has the ${offerName} upgrade.` };
  }
  const expected = Math.floor((target.value ?? 0) * multiplier);
  if (!Number.isInteger(input.unit_price) || input.unit_price <= 0 || input.unit_price !== expected) {
    return { ok: false, message: `Invalid upgrade price: expected ${expected} gc.` };
  }
  const snapshot = document.campaign.states.find((row) => row.number === document.campaign.current_state_number)
    ?? document.campaign.states.at(-1);
  const available = (snapshot?.gold ?? 0) + (post.gold_delta ?? 0);
  if (input.unit_price > available) {
    return { ok: false, message: `Not enough gold: ${input.unit_price} gc needed, ${available} gc available.` };
  }

  // Consume one stashed base copy; rows vanishing at zero owned are removed.
  let inventory = document.campaign.inventory
    .map((row) => row.id === target.id
      ? { ...row, owned: row.owned - 1, stash: row.stash - 1 }
      : row)
    .filter((row) => row.owned > 0);
  const upgradedId = `${input.item_id}:${target.id}`;
  const upgradedName = `${offerName} ${target.name}`;
  const existing = inventory.find((row) => row.id === upgradedId);
  inventory = existing
    ? inventory.map((row) => row.id === upgradedId ? { ...row, owned: row.owned + 1, stash: row.stash + 1 } : row)
    : [
        ...inventory,
        {
          id: upgradedId,
          name: upgradedName,
          category: target.category,
          owned: 1,
          equipped: 0,
          stash: 1,
          value: (target.value ?? 0) + input.unit_price,
          ...(offer.rarity !== undefined && offer.rarity !== null ? { rarity: `Rare ${String(offer.rarity)}` } : {}),
          special_rules: [...(target.special_rules ?? []), offerName],
          base_item_id: baseId,
        },
      ];
  const changed = {
    ...post,
    gold_delta: (post.gold_delta ?? 0) - input.unit_price,
    event_log: [
      ...(post.event_log ?? []),
      {
        step: 7,
        type: "upgrade_weapon",
        item_id: input.item_id,
        base_item_id: baseId,
        gold: input.unit_price,
        description: `${target.name} upgraded to ${upgradedName} for ${input.unit_price} gc.`,
      },
    ],
  };
  const campaign = {
    ...document.campaign,
    inventory,
    post_battles: document.campaign.post_battles.map((row) => row === post ? changed : row),
  };
  return { ok: true, document: withCampaign(document, campaign) };
}

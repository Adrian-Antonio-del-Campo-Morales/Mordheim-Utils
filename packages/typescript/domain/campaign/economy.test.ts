/**
 * Parity port of desktop `tests/campaign/test_economy_sequence_matrix.py`
 * (7 test functions → behavioural equivalents). Traceability: manifest rows
 * with `web_target: packages/typescript/domain/campaign/economy.test.ts`.
 *
 * Desktop semantics (`AppController` draft economy + kernel):
 * - `draft_treasury = starting_gold − recruitment − inventory acquisition cost`;
 * - refunds match the *actual* recorded per-copy purchase price (mixed
 *   prices are a real ledger, `acquisition_costs`, oldest first);
 * - returning an equipped copy to the stash is cost-neutral while it stays
 *   in the warband;
 * - assignment carries the specific copy's recorded cost;
 * - heroes cannot be recruited as multi-member rows;
 * - every transition survives a v5 file round-trip.
 *
 * The fake KB mirrors the real artefact shape: `equipment_access` rows carry
 * `list_id` + optional cost — a costless access row means the creation price
 * is resolved at the table (`unit_price`), exactly like `rat_familiar_scroll`
 * in the published Clan Pestilens lists.
 *
 * Purity: plain Node, fake KnowledgeReader, in-memory v5 round-trip —
 * no React, no DOM, no filesystem.
 */

import { describe, expect, it } from "vitest";

import { buyDraftEquipment, removeDraftEquipment, buyDraftStashItem, removeDraftStashItem, assignEquipment } from "../../domain/campaign/kernel/equipment";
import { treasury } from "../../domain/campaign/kernel/document";
import { commitInitialWarband } from "../../domain/campaign/kernel/commit-warband";
import { recordBattle } from "../../domain/campaign/kernel/record-battle";
import type { Campaign, CampaignDocument, KnowledgeReader, Warrior } from "../../domain/campaign/kernel/usecases";
import { CampaignFileV5Adapter, parseCampaignFileDetailed } from "../../adapters/campaign-file";

const adapter = new CampaignFileV5Adapter();

/** In-memory v5 round-trip (desktop `load_campaign(save_campaign(...))`). */
function roundtrip(document: CampaignDocument): CampaignDocument {
  const serialized = adapter.serializeCampaign(document.campaign);
  expect(serialized.ok).toBe(true);
  if (!serialized.ok) return document;
  const parsed = parseCampaignFileDetailed(serialized.text);
  expect(parsed.ok).toBe(true);
  if (!parsed.ok) return document;
  return { campaign: parsed.campaign, view: parsed.view };
}

const knowledge: KnowledgeReader = {
  queryKnowledge(query) {
    const ref = query.id;
    const id = ref.value;
    if (query.id.kind === "profile_id") {
      if (id === "unarmoured") {
        return {
          ok: true,
          record: {
            kind: "profile", id: ref, names: { en: id },
            data: { band_id: "skaven-clan-pestilens", equipment_forbids: ["armour"], equipment_access: [
              { item_id: "light_armour", cost: 20 }, { item_id: "shield", cost: 5 }, { item_id: "buckler", cost: 5 },
            ] },
          },
        };
      }
      // Access row without a numeric cost (desktop `cost: None` → the
      // creation price is resolved manually via unit_price).
      return {
        ok: true,
        record: {
          kind: "profile",
          id: ref,
          names: { en: id },
          data: {
            band_id: "skaven-clan-pestilens",
            equipment_access: [{ item_id: "rat_familiar_scroll", list_id: "clan-pestilens-hero-equipment-list" }],
            can_gain_experience: true,
          },
        },
      };
    }
    if (query.id.kind === "band_id") {
      return {
        ok: true,
        record: {
          kind: "band",
          id: ref,
          names: { en: id },
          data: {
            equipment_access: [{ item_id: "rat_familiar_scroll", list_id: "clan-pestilens-henchmen-equipment-list" }],
          },
        },
      };
    }
    if (query.id.kind === "item_id") {
      if (["light_armour", "shield", "buckler"].includes(id)) return { ok: true, record: { kind: "item", id: ref, names: { en: id }, data: { kind: id === "light_armour" ? "armour" : "shield-or-defence" } } };
      return { ok: true, record: { kind: "item", id: ref, names: { en: id }, data: { kind: "Equipment" } } };
    }
    if (query.id.kind === "scenario_id" && id === "skirmish") {
      return { ok: true, record: { kind: "scenario", id: ref, names: { en: "Skirmish" }, data: {} } };
    }
    return { ok: false, reason: "not_found" };
  },
  queryMany: (queries) => queries.map((q) => knowledge.queryKnowledge(q)),
};

function hero(id: string, profileId: string): Warrior {
  return { id, name: id, profile_name: profileId, kind: "hero", profile_id: profileId, stats: { WS: 3 }, equipment: [], skills: [], experience: 0, cost: 30 };
}

function group(id: string, profileId: string, quantity: number): Warrior {
  return { id, name: `${profileId} Group`, profile_name: profileId, kind: "henchman", profile_id: profileId, stats: { WS: 2 }, equipment: [], skills: [], experience: 0, cost: 20, quantity };
}

function draft(extra: Warrior[], startingGold = 500): CampaignDocument {
  const campaign: Campaign = {
    identity: { campaign_name: "Economy", warband_name: "Band", warband_type: "Clan Pestilens", band_id: "skaven-clan-pestilens", mercenary_variant: null },
    configuration: { is_draft: true, starting_gold: startingGold, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
    resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 0,
    warriors: extra,
    battles: [],
    states: [],
    post_battles: [],
    inventory: [],
    special_rules: [],
    manual_log: [],
  };
  return { campaign, view: {} };
}

function committed(extra: Warrior[]): CampaignDocument {
  const base = draft(extra);
  return {
    ...base,
    campaign: {
      ...base.campaign,
      configuration: { ...base.campaign.configuration, is_draft: false },
      current_state_number: 1,
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 3, max_models: 15, heroes: 1, henchmen: 2, experience: 0, label: "Initial Warband" }],
    },
  };
}

describe("desktop test_economy_sequence_matrix.py → web draft economy parity", () => {
  it("blocks armour, shields and bucklers for profiles that forbid armour", () => {
    const doc = draft([hero("h1", "unarmoured")]);
    for (const item_id of ["light_armour", "shield", "buckler"]) {
      const result = buyDraftEquipment(doc, { warrior_id: "h1", item_id, unit_price: 1 }, knowledge);
      expect(result.ok).toBe(false);
      if (!result.ok) expect(result.message).toBe("This warrior cannot wear armour, shields or bucklers.");
    }
  });

  it("personal equipment refund matches the actual purchase price", () => {
    const prices = [26, 31] as const;
    const doc = draft([hero("h1", "sorcerer"), hero("h2", "sorcerer")]);
    // Desktop: 2 heroes (60) + purchases 26+31; treasury = 500 − 60 − 57 = 383.
    const first = buyDraftEquipment(doc, { warrior_id: "h1", item_id: "rat_familiar_scroll", unit_price: prices[0] }, knowledge);
    expect(first.ok).toBe(true);
    if (!first.ok) return;
    const second = buyDraftEquipment(first.state, { warrior_id: "h2", item_id: "rat_familiar_scroll", unit_price: prices[1] }, knowledge);
    expect(second.ok).toBe(true);
    if (!second.ok) return;
    expect(treasury(second.state.campaign)).toBe(500 - 60 - (prices[0] + prices[1]));
    // Each warrior's ledger records its own price.
    expect(second.state.campaign.warriors[0].equipment[0].acquisition_costs).toEqual([26]);
    expect(second.state.campaign.warriors[1].equipment[0].acquisition_costs).toEqual([31]);
    // Removing hero 1 refunds exactly 26 (the actual purchase, not the row value).
    const removed = removeDraftEquipment(second.state, { warrior_id: "h1", item_id: "rat_familiar_scroll" });
    expect(removed.ok).toBe(true);
    if (!removed.ok) return;
    expect(treasury(removed.state.campaign)).toBe(500 - 60 - prices[1]);
  });

  it("round-trips mixed-price purchases through v5 before refund", () => {
    const before = draft([hero("h1", "sorcerer")]);
    const bought = buyDraftEquipment(before, { warrior_id: "h1", item_id: "rat_familiar_scroll", unit_price: 26 }, knowledge);
    expect(bought.ok).toBe(true);
    if (!bought.ok) return;
    const restored = roundtrip(bought.state);
    expect(restored.campaign.warriors[0].equipment[0].acquisition_costs).toEqual([26]);
    const removed = removeDraftEquipment(restored, { warrior_id: "h1", item_id: "rat_familiar_scroll" });
    expect(removed.ok).toBe(true);
    if (!removed.ok) return;
    // Ledger fully refunded: treasury = starting − recruitment.
    expect(treasury(removed.state.campaign)).toBe(500 - 30);
  });

  it("returning an equipped copy to the stash is cost-neutral", () => {
    const before = draft([hero("h1", "sorcerer")]);
    const bought = buyDraftEquipment(before, { warrior_id: "h1", item_id: "rat_familiar_scroll", unit_price: 26 }, knowledge);
    expect(bought.ok).toBe(true);
    if (!bought.ok) return;
    expect(treasury(bought.state.campaign)).toBe(500 - 30 - 26);
    const assigned = assignEquipment(bought.state, { warrior_id: "h1", item_id: "rat_familiar_scroll", quantity: 1, direction: "stash" });
    expect(assigned.ok).toBe(true);
    if (!assigned.ok) return;
    // Copy stays owned by the warband → cost stays committed.
    expect(treasury(assigned.state.campaign)).toBe(500 - 30 - 26);
    // Selling the stash copy releases its recorded price.
    const sold = removeDraftStashItem(assigned.state, { item_id: "rat_familiar_scroll", quantity: 1 });
    expect(sold.ok).toBe(true);
    if (!sold.ok) return;
    expect(treasury(sold.state.campaign)).toBe(500 - 30);
  });

  it("assignment preserves the copy cost through a round-trip", () => {
    const before = draft([hero("h1", "sorcerer")]);
    const bought = buyDraftStashItem(before, { item_id: "rat_familiar_scroll", quantity: 1, unit_price: 27 }, knowledge);
    expect(bought.ok).toBe(true);
    if (!bought.ok) return;
    expect(bought.state.campaign.inventory[0].acquisition_costs).toEqual([27]);
    const assigned = assignEquipment(bought.state, { warrior_id: "h1", item_id: "rat_familiar_scroll", quantity: 1, direction: "equip" });
    expect(assigned.ok).toBe(true);
    if (!assigned.ok) return;
    const restored = roundtrip(assigned.state);
    expect(restored.campaign.warriors[0].equipment[0].acquisition_costs).toEqual([27]);
  });

  it("mixed-price group stash purchases stay conserved", () => {
    let doc = draft([group("crew", "crew", 2)]);
    for (const price of [42, 51, 48]) {
      const bought = buyDraftStashItem(doc, { item_id: "rat_familiar_scroll", quantity: 1, unit_price: price }, knowledge);
      expect(bought.ok).toBe(true);
      if (!bought.ok) return;
      doc = bought.state;
    }
    const stock = doc.campaign.inventory[0];
    expect(stock.owned).toBe(3);
    expect(stock.owned).toBe(stock.equipped + stock.stash);
    // Exact per-copy ledger, oldest first (desktop `add_stock`).
    expect(stock.acquisition_costs).toEqual([42, 51, 48]);
    const removed = removeDraftStashItem(doc, { item_id: "rat_familiar_scroll", quantity: 3 });
    expect(removed.ok).toBe(true);
    if (!removed.ok) return;
    // Full refund = sum of the per-copy ledger; the row disappears.
    expect(removed.state.campaign.inventory.find((row) => row.id === "rat_familiar_scroll")).toBeUndefined();
    expect(treasury(removed.state.campaign)).toBe(500 - 40);
  });

  it("partial stash refund takes the recorded copies, not the row value", () => {
    let doc = draft([group("crew", "crew", 2)]);
    for (const price of [42, 51, 48]) {
      const bought = buyDraftStashItem(doc, { item_id: "rat_familiar_scroll", quantity: 1, unit_price: price }, knowledge);
      if (bought.ok) doc = bought.state; else throw new Error(bought.message);
    }
    // Remove 2 copies: refund 42+51 (oldest first, desktop `remove_stock`).
    const removed = removeDraftStashItem(doc, { item_id: "rat_familiar_scroll", quantity: 2 });
    expect(removed.ok).toBe(true);
    if (!removed.ok) return;
    const stock = removed.state.campaign.inventory.find((row) => row.id === "rat_familiar_scroll");
    expect(stock?.acquisition_costs).toEqual([48]);
    expect(treasury(removed.state.campaign)).toBe(500 - 40 - 48);
  });

  it("mixed-cost group resize preserves remaining cost", () => {
    let doc = draft([group("crew", "crew", 2)]);
    for (const price of [42, 51, 48]) {
      const bought = buyDraftStashItem(doc, { item_id: "rat_familiar_scroll", quantity: 1, unit_price: price }, knowledge);
      if (bought.ok) doc = bought.state; else throw new Error(bought.message);
    }
    const assigned = assignEquipment(doc, { warrior_id: "crew", item_id: "rat_familiar_scroll", quantity: 3, direction: "equip" });
    expect(assigned.ok).toBe(true);
    if (!assigned.ok) return;
    const entry = assigned.state.campaign.warriors[0].equipment[0];
    expect(entry.quantity).toBe(3);
    // Equipped copies carry the exact stash ledger (desktop `stash_costs`).
    expect(entry.acquisition_costs).toEqual([42, 51, 48]);
    const restored = roundtrip(assigned.state);
    expect(restored.campaign.warriors[0].equipment[0].acquisition_costs).toEqual([42, 51, 48]);
  });

  it("heroes cannot be recruited as a multi-member row", () => {
    // Hero rows are always single-member (desktop rejects multi-member hero
    // recruitment in the draft add path).
    const doc = committed([hero("h1", "sorcerer"), group("monks", "monk-initiates", 2)]);
    expect(doc.campaign.warriors.filter((w) => w.kind === "hero").every((w) => (w.quantity ?? 1) === 1)).toBe(true);
    const bad = draft([{ ...hero("bad", "sorcerer"), quantity: 2 }]);
    const commit = commitInitialWarband(bad);
    expect(commit.ok).toBe(false);
  });

  it("mixed costs survive group transitions (conservation + round-trip)", () => {
    for (const prices of [[42, 51], [51, 42], [46, 46]] as const) {
      let doc = draft([hero("captain", "sorcerer"), group("crew", "crew", 3)]);
      for (const price of prices) {
        const bought = buyDraftStashItem(doc, { item_id: "rat_familiar_scroll", quantity: 1, unit_price: price }, knowledge);
        if (bought.ok) doc = bought.state; else throw new Error(bought.message);
      }
      const assigned = assignEquipment(doc, { warrior_id: "crew", item_id: "rat_familiar_scroll", quantity: 2, direction: "equip" });
      expect(assigned.ok).toBe(true);
      if (!assigned.ok) continue;
      const committed = commitInitialWarband(assigned.state);
      expect(committed.ok).toBe(true);
      if (!committed.ok) continue;
      const battle = recordBattle(committed.state, { scenario: "skirmish", opponent: "Audit", result: "draw", gold_delta: 0, wyrdstone: 0, xp_delta: 0, casualties: 0, out_of_action_ids: null }, knowledge);
      expect(battle.ok).toBe(true);
      if (!battle.ok) continue;
      const restored = roundtrip(battle.state);
      const stock = restored.campaign.inventory.find((row) => row.id === "rat_familiar_scroll");
      expect(stock).toBeDefined();
      // Conservation across the commit boundary: owned = equipped + stash.
      expect(stock!.owned).toBe(stock!.equipped + stock!.stash);
    }
  });
});

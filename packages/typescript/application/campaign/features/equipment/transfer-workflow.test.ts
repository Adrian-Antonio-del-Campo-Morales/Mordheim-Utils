/**
 * Parity port of the desktop `transfer_equipped_item` behaviour in
 * `controller.py` (no dedicated desktop test — ported from the implementation).
 * Exercised against the web `transferEquippedItem` seam in
 * `transfer-workflow.ts` — no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument } from "../../../../domain/campaign/index";

import { transferEquippedItem } from "./transfer-workflow";

function makeDoc(): CampaignDocument {
  const doc: unknown = {
    view: { selected_moment: "post:1" },
    campaign: {
      identity: { campaign_name: "Transfer", warband_name: "Test", warband_type: "Middenheim", band_id: "middenheim", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "hero-1", name: "Sigrid", profile_name: "Captain", kind: "hero", stats: { M: 4, WS: 4 }, equipment: [{ item_id: "sword", name: "Sword", quantity: 1, acquisition: "stash_assignment", transferable: true }], skills: [], experience: 10, cost: 65 },
        { id: "hero-2", name: "Ursula", profile_name: "Captain", kind: "hero", stats: { M: 4, WS: 4 }, equipment: [], skills: [], experience: 10, cost: 65 },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0 }],
      post_battles: [],
      inventory: [{ id: "sword", name: "Sword", category: "weapon", owned: 1, equipped: 1, stash: 0, value: 10 }], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

describe("transferEquippedItem (desktop transfer_equipped_item)", () => {
  it("moves one loadout set from the source to the target warrior", () => {
    const result = transferEquippedItem(makeDoc(), { item_id: "sword", source_id: "hero-1", target_id: "hero-2" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const warriors = result.document.campaign.warriors;
    const source = warriors.find((w) => w.id === "hero-1");
    const target = warriors.find((w) => w.id === "hero-2");
    expect(source?.equipment.find((e) => e.item_id === "sword")).toBeUndefined();
    expect(target?.equipment.find((e) => e.item_id === "sword")?.quantity).toBe(1);
    const item = result.document.campaign.inventory.find((row) => row.id === "sword");
    expect(item?.owned).toBe(1);
    expect(item?.equipped).toBe(1);
    expect(item?.stash).toBe(0);
  });

  it("rejects transferring to the same warrior", () => {
    const result = transferEquippedItem(makeDoc(), { item_id: "sword", source_id: "hero-1", target_id: "hero-1" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("same warrior");
  });

  it("rejects when the source does not carry the transferable item", () => {
    const result = transferEquippedItem(makeDoc(), { item_id: "dagger", source_id: "hero-1", target_id: "hero-2" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("not available");
  });

  it("requires a complete transferable set on the source", () => {
    const doc = makeDoc();
    (doc.campaign.warriors[0] as any).equipment = [
      { item_id: "sword", name: "Sword", quantity: 1, acquisition: "stash_assignment", transferable: true, per_model: true },
    ];
    (doc.campaign.warriors[0] as unknown as { quantity: number }).quantity = 2;
    (doc.campaign.warriors[0] as unknown as { kind: string }).kind = "henchman";
    const result = transferEquippedItem(doc, { item_id: "sword", source_id: "hero-1", target_id: "hero-2" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("complete transferable set");
  });

  it("rejects when the stash plus released copies cannot cover the target's group", () => {
    const doc = makeDoc();
    // Target is a 3-model henchman group needing 3 copies; only 1 can be released.
    (doc.campaign.warriors[1] as unknown as { kind: string; quantity: number }).kind = "henchman";
    (doc.campaign.warriors[1] as unknown as { quantity: number }).quantity = 3;
    const result = transferEquippedItem(doc, { item_id: "sword", source_id: "hero-1", target_id: "hero-2" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("only 1 are available");
  });

  it("releases and assigns per-model quantities for henchman groups", () => {
    const doc = makeDoc();
    (doc.campaign.warriors[0] as unknown as { kind: string; quantity: number }).kind = "henchman";
    (doc.campaign.warriors[0] as unknown as { quantity: number }).quantity = 3;
    (doc.campaign.warriors[0] as unknown as { equipment: unknown[] }).equipment = [
      { item_id: "sword", name: "Sword", quantity: 3, acquisition: "stash_assignment", transferable: true, per_model: true },
    ];
    (doc.campaign.inventory[0] as { owned: number; equipped: number; stash: number }).owned = 3;
    (doc.campaign.inventory[0] as { equipped: number }).equipped = 3;
    const result = transferEquippedItem(doc, { item_id: "sword", source_id: "hero-1", target_id: "hero-2" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const warriors = result.document.campaign.warriors;
    expect(warriors.find((w) => w.id === "hero-1")?.equipment.find((e) => e.item_id === "sword")).toBeUndefined();
    expect(warriors.find((w) => w.id === "hero-2")?.equipment.find((e) => e.item_id === "sword")?.quantity).toBe(1);
  });
});
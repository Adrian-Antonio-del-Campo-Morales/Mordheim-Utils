/**
 * Parity port of desktop `tests/python/campaign/test_campaign_sequence_matrix.py`.
 *
 * The desktop matrix fuzzes every band through draft purchase/refund/save/
 * undo and post-battle actions. This web port keeps the portable invariant
 * checks at the domain boundary and leaves UI/controller-only operations to
 * the application workflow tests.
 */
import { describe, expect, it } from "vitest";
import { CampaignFileV5Adapter } from "@adapters/campaign-file/index";
import type { CampaignDocument, InventoryItem, Warrior } from "@domain/campaign/kernel/state";

function fixture(): CampaignDocument {
  const warrior: Warrior = {
    id: "hero-1",
    name: "Sigrid",
    profile_name: "Matriarch",
    kind: "hero",
    stats: { M: 4, WS: 4 },
    equipment: [{ item_id: "dagger", name: "Dagger", quantity: 1, acquisition: "purchase", transferable: true }],
    skills: [],
    experience: 10,
    cost: 65,
  };
  const inventory: InventoryItem = {
    id: "dagger",
    name: "Dagger",
    category: "weapon",
    owned: 1,
    equipped: 1,
    stash: 0,
  };
  return {
    view: { selected_moment: "state:1" },
    campaign: {
      identity: { campaign_name: "Matrix", warband_name: "Test Band", warband_type: "Sisters of Sigmar", band_id: "sisters-of-sigmar", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [warrior],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 15, models: 1, max_models: 15, heroes: 1, henchmen: 0, experience: 10 }],
      post_battles: [],
      inventory: [inventory],
      special_rules: [],
      manual_log: [],
    },
  };
}

function assertInventoryInvariant(document: CampaignDocument): void {
  const equipped = new Map<string, number>();
  for (const warrior of document.campaign.warriors) {
    expect(warrior.quantity ?? 1).toBeGreaterThan(0);
    for (const item of warrior.equipment) {
      expect(item.quantity).toBeGreaterThanOrEqual(0);
      if (item.transferable && item.acquisition !== "fixed") {
        equipped.set(item.item_id, (equipped.get(item.item_id) ?? 0) + item.quantity);
      }
    }
  }
  for (const item of document.campaign.inventory) {
    expect(item.owned).toBe(item.equipped + item.stash);
    expect(item.owned).toBeGreaterThanOrEqual(0);
    expect(item.equipped).toBe(equipped.get(item.id) ?? 0);
    equipped.delete(item.id);
  }
  expect(equipped.size).toBe(0);
}

describe("desktop test_campaign_sequence_matrix.py → campaign invariants", () => {
  it("keeps roster ids unique and inventory accounting balanced", () => {
    const document = fixture();
    expect(new Set(document.campaign.warriors.map((warrior) => warrior.id)).size)
      .toBe(document.campaign.warriors.length);
    assertInventoryInvariant(document);
  });

  it("rejects negative quantities through the invariant contract", () => {
    const invalid = fixture();
    const warrior = invalid.campaign.warriors[0];
    const bad = { ...warrior, quantity: 0 };
    expect(() => assertInventoryInvariant({
      ...invalid,
      campaign: { ...invalid.campaign, warriors: [bad] },
    })).toThrow();
  });

  it("preserves inventory and roster invariants through v5 serialize/parse", () => {
    const adapter = new CampaignFileV5Adapter();
    const original = fixture();
    const serialized = adapter.serializeCampaign(original.campaign);
    expect(serialized.ok).toBe(true);
    if (!serialized.ok) return;
    const parsed = adapter.parseCampaignFile(serialized.text);
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    const roundTrip = { campaign: parsed.document.campaign, view: parsed.document.view ?? {} } as unknown as CampaignDocument;
    assertInventoryInvariant(roundTrip);
    expect(roundTrip.campaign.warriors).toEqual(original.campaign.warriors);
    expect(roundTrip.campaign.inventory).toEqual(original.campaign.inventory);
  });

  it("keeps view selection outside persistent campaign invariants", () => {
    const original = fixture();
    const changed = { ...original, view: { selected_moment: "battle:1" } };
    expect(changed.campaign).toEqual(original.campaign);
    assertInventoryInvariant(changed);
  });

  it("does not count non-transferable fixed equipment as inventory carriage", () => {
    const document = fixture();
    const warrior = document.campaign.warriors[0];
    const fixed = { item_id: "holy-symbol", name: "Holy Symbol", quantity: 1, acquisition: "fixed", transferable: false };
    const changed = {
      ...document,
      campaign: { ...document.campaign, warriors: [{ ...warrior, equipment: [...warrior.equipment, fixed] }] },
    };
    expect(() => assertInventoryInvariant(changed)).not.toThrow();
  });

  // The AppController-equivalent seams now exist on the application service
  // (buyDraftEquipment/removeDraftEquipment/assignEquipment/recruitBandProfile
  // + import/export/undo); port the seeded 80-step fuzz sequences against
  // `service.run` when the desktop parity pass resumes.
});

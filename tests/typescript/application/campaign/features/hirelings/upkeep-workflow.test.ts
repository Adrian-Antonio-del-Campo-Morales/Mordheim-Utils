/**
 * Parity port of the desktop `test_hired_sword_upkeep_must_be_paid_or_the_hireling_leaves`
 * from `test_post_battle_engine.py`, grounded in desktop `resolve_hireling_upkeep`.
 * Exercised against the web `resolveHirelingUpkeep` seam — no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument } from "@domain/campaign/index";
import { resolveHirelingUpkeep } from "@app/campaign/features/hirelings/upkeep-workflow";

function makeFixture(costs: unknown): CampaignDocument {
  const doc: unknown = {
    view: {},
    campaign: {
      identity: { campaign_name: "Upkeep", warband_name: "Test", warband_type: "Sisters of Sigmar", band_id: "sisters-of-sigmar", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "hero-1", name: "Sigrid", profile_name: "Matriarch", kind: "hero", stats: { M: 4, WS: 4 }, equipment: [], skills: [], experience: 10, cost: 65 },
        { id: "h1", name: "Ogre Bodyguard", profile_name: "Hired Sword", kind: "hireling", stats: { M: 6, WS: 3 }, equipment: [{ item_id: "club", name: "Club", quantity: 1, transferable: true }], skills: [], experience: 0, cost: 90, hireling_rating: 75, special_rules: ["Returning a Favour: no hiring fee; upkeep begins after the next battle", "Stubborn"] },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 1, max_models: 15, heroes: 1, henchmen: 0, experience: 10 }],
      post_battles: [{
        battle_number: 1, complete: false, active_step: 0, completed_steps: [], review_open: false,
        pending_follow_ups: [{ id: "upkeep:test", type: "hireling_upkeep", warrior_id: "h1", costs }],
      }],
      inventory: [{ id: "club", name: "Club", category: "weapon", owned: 1, equipped: 1, stash: 0 }],
      special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

describe("resolveHirelingUpkeep (desktop resolve_hireling_upkeep)", () => {
  it("paying deducts the declared gold and keeps the hireling", () => {
    const result = resolveHirelingUpkeep(makeFixture([["gold_crowns", 15]]), { follow_up_id: "upkeep:test", pay: true });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.post_battles[0].gold_delta).toBe(-15);
    expect(result.document.campaign.post_battles[0].pending_follow_ups).toHaveLength(0);
    expect(result.document.campaign.warriors.some((w) => w.id === "h1")).toBe(true);
  });

  it("rejects payment the warband cannot afford", () => {
    const result = resolveHirelingUpkeep(makeFixture([["gold_crowns", 9999]]), { follow_up_id: "upkeep:test", pay: true });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("Not enough");
  });

  it("the hireling leaves and its carried gear is discarded when unpaid", () => {
    const result = resolveHirelingUpkeep(makeFixture([["gold_crowns", 15]]), { follow_up_id: "upkeep:test", pay: false });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.warriors.some((w) => w.id === "h1")).toBe(false);
    expect(result.document.campaign.inventory.find((i) => i.id === "club")).toBeUndefined();
    expect(result.document.campaign.post_battles[0].pending_follow_ups).toHaveLength(0);
  });

  it("rejects an unknown upkeep follow-up", () => {
    const result = resolveHirelingUpkeep(makeFixture([["gold_crowns", 15]]), { follow_up_id: "nope", pay: true });
    expect(result.ok).toBe(false);
  });

  it("strips the Returning-a-Favour rule once the upkeep is paid", () => {
    const result = resolveHirelingUpkeep(makeFixture([["gold_crowns", 15]]), { follow_up_id: "upkeep:test", pay: true });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const hireling = result.document.campaign.warriors.find((w) => w.id === "h1");
    expect(hireling?.special_rules?.some((rule) => rule.startsWith("Returning a Favour:"))).toBe(false);
    // Other rules survive the strip.
    expect(hireling?.special_rules).toContain("Stubborn");
  });
});
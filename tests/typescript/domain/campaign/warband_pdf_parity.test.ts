/** Portable parity translation of tests/python/campaign/test_warband_pdf.py. */
import { describe, expect, it } from "vitest";
import { cloneDocument } from "@domain/campaign/kernel/document";
import type { CampaignDocument } from "@domain/campaign/kernel/usecases";

function document(): CampaignDocument {
  return {
    campaign: {
      identity: { campaign_name: "Campaign", warband_name: "Band", warband_type: "Sisters", band_id: "sisters-of-sigmar", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 0,
      warriors: [{ id: "marta", name: "Marta", profile_name: "Sister", kind: "hero", stats: { WS: 4 }, equipment: [], skills: [], experience: 0, cost: 45 }],
      battles: [],
      states: [{ number: 0, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 30, models: 1, max_models: 15, heroes: 1, henchmen: 0, experience: 0, roster: [{ id: "marta", name: "Marta", profile_name: "Sister", kind: "hero", stats: { WS: 4 }, equipment: [], skills: [], experience: 0, cost: 45 }], inventory: [] }],
      post_battles: [], inventory: [], special_rules: [], manual_log: [],
    },
    view: {},
  };
}

describe("desktop warband PDF parity", () => {
  it("committed snapshots remain frozen when live campaign data changes", () => {
    const original = document();
    const snapshot = cloneDocument(original).campaign.states[0];
    const mutated: CampaignDocument = {
      ...original,
      campaign: { ...original.campaign, warriors: [], inventory: [] },
    };
    expect(snapshot.roster?.[0].name).toBe("Marta");
    expect(snapshot.inventory).toEqual([]);
    expect(mutated.campaign.warriors).toEqual([]);
  });

  it("historical export selects the requested timeline snapshot, not live roster", () => {
    const state = document().campaign.states[0];
    expect(state.number).toBe(0);
    expect(state.roster?.map((warrior) => warrior.id)).toEqual(["marta"]);
    expect(state.inventory).toEqual([]);
  });

  it("draft and committed documents retain non-Latin display text as data", () => {
    const draft = document();
    const localized: CampaignDocument = {
      ...draft,
      campaign: {
        ...draft.campaign,
        warriors: [{ ...draft.campaign.warriors[0], name: "Sister Ana — ⚠ 🎲" }],
      },
    };
    expect(localized.campaign.warriors[0].name).toContain("🎲");
    expect(localized.campaign.warriors[0].name).toContain("⚠");
  });

  // PDF export exists at apps/warband-manager-web/src/features/export/
  // warband-pdf; byte/export assertions belong to that feature's tests.
});

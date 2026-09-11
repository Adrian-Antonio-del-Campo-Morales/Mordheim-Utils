import { describe, expect, it } from "vitest";

import type { CampaignDocument, TimelineState, Warrior } from "../campaign/types";
import { createWarbandPdf } from "./warband-pdf";

const hero: Warrior = {
  id: "marta",
  name: "Marta — \u201eCu\u00e9ntamelo\u201c \u26a0 \u{1f3b2}",
  profile_name: "Sister",
  kind: "hero",
  stats: { M: 4, WS: 4, BS: 4, S: 3, T: 3, W: 1, I: 4, A: 1, Ld: 8 },
  equipment: [],
  skills: [],
  experience: 4,
  cost: 45,
};

const henchman: Warrior = {
  id: "g1",
  name: "Sisters",
  profile_name: "Novice",
  kind: "henchman",
  stats: { M: 4, WS: 3, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
  equipment: [{ item_id: "item.sword", name: "Sword", quantity: 2 }],
  skills: [],
  experience: 0,
  quantity: 3,
  cost: 25,
};

function documentWith(selected_moment?: string): CampaignDocument {
  const state: TimelineState = {
    number: 0,
    date: "2026-09-10",
    gold: 480,
    wyrdstone: 1,
    rating: 55,
    models: 2,
    max_models: 15,
    heroes: 1,
    henchmen: 1,
    experience: 4,
    roster: [hero],
    inventory: [{ id: "item.axe", name: "Axe", category: "weapon", owned: 1, equipped: 0, stash: 1 }],
  };
  return {
    campaign: {
      identity: { campaign_name: "Campaign", warband_name: "Band", warband_type: "Sisters", band_id: "sisters-of-sigmar", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 0,
      warriors: [hero, henchman],
      battles: [{ number: 1, date: "2026-09-10", scenario: "scenario.skirmish", opponent: "Orcs", result: "win", gold_delta: 20, wyrdstone: 1, xp_delta: 4, casualties: 0, advances: 0, rating_before: 30, rating_after: 55, models_before: 2, models_after: 2, out_of_action_ids: [] }],
      states: [state],
      post_battles: [],
      inventory: [],
      special_rules: [],
      manual_log: [],
    },
    view: selected_moment ? { selected_moment } : {},
  };
}

describe("warband PDF exporter (desktop parity port)", () => {
  it("renders a valid PDF for the draft, a committed state and non-latin text", async () => {
    for (const selected of ["draft:0", "state:0", "post:1"]) {
      const bytes = await createWarbandPdf(documentWith(selected), "es");
      const text = Buffer.from(bytes).toString("latin1");
      expect(text.startsWith("%PDF-")).toBe(true);
      expect(text.trimEnd().endsWith("%%EOF")).toBe(true);
      expect(bytes.length).toBeGreaterThan(500);
    }
  });
});

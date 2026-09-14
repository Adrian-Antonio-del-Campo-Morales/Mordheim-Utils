/**
 * Campaign review tests: the review read model and auxiliary
 * exporters. Core rule — **no rules in exporters**: exports are pure
 * projections (byte-stable for equal documents, never mutate the input,
 * never call use cases). The review summary reports pending work that
 * blocks a safe save.
 */

import { describe, expect, it } from "vitest";

import type { CampaignDocument, Warrior } from "../../../../domain/campaign/kernel/state";
import { ledgerText, reviewSummary, rosterSummaryText } from "./review-exports";

function warrior(overrides: Partial<Warrior>): Warrior {
  return {
    id: "w1",
    name: "Sigrid",
    profile_name: "Captain",
    kind: "hero",
    stats: { M: 4, WS: 4 },
    equipment: [],
    skills: [],
    experience: 5,
    cost: 35,
    manual_log: [],
    ...overrides,
  } as Warrior;
}

function document(overrides: {
  warriors?: Warrior[];
  post_battles?: CampaignDocument["campaign"]["post_battles"];
}): CampaignDocument {
  return {
    campaign: {
      identity: {
        campaign_name: "Review Campaign",
        warband_name: "Ledger Band",
        warband_type: "Witch Hunters",
        band_id: "witch_hunters",
        mercenary_variant: null,
      },
      configuration: {
        is_draft: false,
        starting_gold: 500,
        minimum_models: 3,
        maximum_models: 15,
        hero_limit: 4,
      },
      resources: { gold: 240, wyrdstone_shards: 2, stash_value: 30, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 2,
      warriors: overrides.warriors ?? [warrior({})],
      battles: [
        {
          number: 1,
          date: "01 Aug 2026",
          scenario: "Skirmish",
          opponent: "Cultists",
          result: "Victory",
          gold_delta: 35,
          wyrdstone: 1,
          xp_delta: 3,
          casualties: 0,
          advances: 0,
          rating_before: 90,
          rating_after: 105,
          models_before: 6,
          models_after: 7,
          out_of_action_ids: null,
        },
      ],
      states: [
        {
          number: 1,
          date: "01 Aug 2026",
          gold: 200,
          wyrdstone: 1,
          rating: 100,
          models: 6,
          max_models: 15,
          heroes: 2,
          henchmen: 4,
          experience: 10,
        },
        {
          number: 2,
          date: "08 Aug 2026",
          gold: 240,
          wyrdstone: 2,
          rating: 115,
          models: 6,
          max_models: 15,
          heroes: 2,
          henchmen: 4,
          experience: 13,
        },
      ],
      post_battles: overrides.post_battles ?? [],
      inventory: [
        { id: "mace", name: "Mace", category: "ccw", owned: 2, equipped: 1, stash: 1, value: 5 },
      ],
      special_rules: [],
      manual_log: [{ message: "Warband re-equipped before the storm.", date: "02 Aug 2026" }],
    },
    view: {},
  } as unknown as CampaignDocument;
}

describe("reviewSummary", () => {
  it("aggregates identity, resources, roster and pending work", () => {
    const doc = document({
      warriors: [warrior({}), warrior({ id: "w2", kind: "henchman", quantity: 3 }), warrior({ id: "h1", kind: "hireling", games_to_miss: 1 })],
      post_battles: [
        {
          battle_number: 1,
          complete: false,
          active_step: 4,
          completed_steps: [0, 1, 2, 3],
          review_open: false,
          pending_follow_ups: [{ id: "f1", type: "injury_roll" }],
        },
      ],
    });
    const summary = reviewSummary(doc);
    expect(summary).toMatchObject({
      campaign_name: "Review Campaign",
      warband_name: "Ledger Band",
      gold: 240,
      wyrdstone_shards: 2,
      warriors: 5,
      heroes: 1,
      henchmen: 3,
      hirelings: 1,
      battles: 1,
      states: 2,
      current_state_number: 2,
      post_battle_pending: true,
      open_follow_ups: 1,
      inventory_items: 1,
      inventory_owned: 2,
      absent_warriors: 1,
    });
  });

  it("reports a clean committed campaign with no pending work", () => {
    const summary = reviewSummary(document({}));
    expect(summary.post_battle_pending).toBe(false);
    expect(summary.open_follow_ups).toBe(0);
    expect(summary.absent_warriors).toBe(0);
    expect(summary.is_draft).toBe(false);
  });
});

describe("auxiliary exporters are pure projections", () => {
  it("ledger and roster export byte-stable text", () => {
    const doc = document({});
    expect(ledgerText(doc)).toBe(ledgerText(structuredClone(doc)));
    expect(rosterSummaryText(doc)).toBe(rosterSummaryText(structuredClone(doc)));
    expect(ledgerText(doc)).toContain("[Battle 1] 01 Aug 2026 — Skirmish vs Cultists: Victory (gold +35, xp +3)");
    expect(ledgerText(doc)).toContain("[Manual log (02 Aug 2026)] Warband re-equipped before the storm.");
    expect(rosterSummaryText(doc)).toContain("- Sigrid | Captain (hero) | xp 5 | 1 model(s)");
  });

  it("exports never mutate the document (no rules in exporters)", () => {
    const doc = document({});
    const before = structuredClone(doc);
    ledgerText(doc);
    rosterSummaryText(doc);
    reviewSummary(doc);
    expect(doc).toEqual(before);
  });

  it("the ledger includes post-battle event log entries verbatim", () => {
    const doc = document({
      post_battles: [
        {
          battle_number: 1,
          complete: true,
          active_step: 8,
          completed_steps: [0, 1, 2, 3, 4, 5, 6, 7],
          review_open: false,
          event_log: [{ step: 3, action: "sell_wyrdstone", message: "Sold 1 shard(s) for 35 gc." }],
        },
      ],
    });
    expect(ledgerText(doc)).toContain("[Post-Battle 1 step 3] Sold 1 shard(s) for 35 gc.");
  });
});

/**
 * Parity port of the desktop commit-projection behaviour in
 * `test_post_battle_engine.py` (projected gold/members/rating/experience and
 * commit gates), grounded in desktop `post_battle_engine.py` projections.
 * Exercised against the web `finalizePostBattle` seam in
 * `finalize-post-battle-workflow.ts` — no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument } from "../../../../domain/campaign/index";
import { finalizePostBattle } from "./finalize-post-battle-workflow";

/** A pending post-battle at the final review step, ready to commit. */
function makePending(): CampaignDocument {
  const doc: unknown = {
    view: { selected_moment: "post:1" },
    campaign: {
      identity: { campaign_name: "Finalize", warband_name: "Test", warband_type: "Sisters of Sigmar", band_id: "sisters-of-sigmar", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "hero-1", name: "Sigrid", profile_name: "Matriarch", kind: "hero", stats: { M: 4, WS: 4 }, equipment: [], skills: [], experience: 10, cost: 65 },
        { id: "hench-1", name: "Novices", profile_name: "Novice", kind: "henchman", stats: { M: 4, WS: 3 }, equipment: [], skills: [], experience: 5, cost: 30, quantity: 2 },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 2, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0 }],
      post_battles: [{
        battle_number: 1, complete: false, active_step: 7, completed_steps: [0, 1, 2, 3, 4, 5, 6], review_open: false,
        pending_follow_ups: [], gold_delta: 20, wyrdstone_delta: 1, wyrdstone_sold: 0,
        experience_applied: true, pending_advances: [],
        step_state: { exploration: { resolved: true }, veterans: { resolved: true } },
        sale_resolved: true, equipment_obligations: [], acknowledgements: {}, event_log: [], searches: {},
      }],
      inventory: [], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

describe("finalizePostBattle projections (desktop projected_*)", () => {
  it("commits a next state whose gold, wyrdstone, rating and roster follow deltas + warriors", () => {
    const result = finalizePostBattle(makePending());
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const states = result.document.campaign.states;
    const committed = states[states.length - 1];
    expect(committed.number).toBe(2);
    expect(committed.gold).toBe(520);
    expect(committed.wyrdstone).toBe(3);
    expect(committed.models).toBe(3);
    expect(committed.heroes).toBe(1);
    expect(committed.henchmen).toBe(2);
    expect(committed.experience).toBe(20);
    expect(committed.rating).toBe(35);
    const post = result.document.campaign.post_battles[0];
    expect(post.complete).toBe(true);
    expect(post.review_open).toBe(true);
  });

  it("blocks the commit while equipment obligations are pending", () => {
    const doc = makePending();
    (doc.campaign.post_battles[0] as any).equipment_obligations = [
      { warrior_id: "hench-1", item_id: "hammer", item_name: "Hammer", copies_per_model: 1 },
    ];
    const result = finalizePostBattle(doc);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("Equip");
  });

  it("blocks the commit before experience/advances are resolved", () => {
    const doc = makePending();
    (doc.campaign.post_battles[0] as any).pending_advances = [
      { warrior_id: "hero-1", committed: false },
    ];
    const result = finalizePostBattle(doc);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("advance");
  });

  it("blocks the commit until exploration, sale and veterans are resolved", () => {
    const doc = makePending();
    (doc.campaign.post_battles[0] as { step_state?: unknown }).step_state = {};
    const result = finalizePostBattle(doc);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("exploration");
  });

});

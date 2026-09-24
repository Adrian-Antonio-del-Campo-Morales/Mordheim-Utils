/**
 * Parity port of the desktop Bitter Enmity behaviour in
 * `test_post_battle_engine.py` (`test_bitter_enmity_records_the_selected_target`),
 * grounded in desktop `resolve_hatred_target`.
 * Exercised against the web `resolveHatred` seam in
 * `injury-decisions-workflow.ts` — no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument } from "@domain/campaign/index";

import { resolveEyeInjury, resolveHatred } from "@app/campaign/features/injuries/injury-decisions-workflow";

/** A pending post-battle with a relationship (Bitter Enmity) follow-up parked. */
function makePending(): CampaignDocument {
  const doc: unknown = {
    view: { selected_moment: "post:1" },
    campaign: {
      identity: { campaign_name: "Hatred", warband_name: "Test", warband_type: "Middenheim", band_id: "middenheim", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "hero-1", name: "Sigrid", profile_name: "Captain", kind: "hero", stats: { M: 4, WS: 4 }, equipment: [], skills: [], experience: 10, cost: 65, hatreds: [] },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0 }],
      post_battles: [{
        battle_number: 1, complete: false, active_step: 2, completed_steps: [0, 1], review_open: false,
        pending_follow_ups: [{ id: "injury:hero-1:1", type: "relationship", warrior_id: "hero-1" }],
        gold_delta: 0, wyrdstone_delta: 0, wyrdstone_sold: 0,
        experience_applied: false, pending_advances: [],
        step_state: {}, sale_resolved: false, equipment_obligations: [], acknowledgements: {}, event_log: [], searches: {},
      }],
      inventory: [], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

/** A pending post-battle with an eye-injury follow-up and a carried sword. */
function makeEyePending(): CampaignDocument {
  const doc: unknown = {
    view: { selected_moment: "post:1" },
    campaign: {
      identity: { campaign_name: "Eye", warband_name: "Test", warband_type: "Middenheim", band_id: "middenheim", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "hero-1", name: "Sigrid", profile_name: "Captain", kind: "hero", stats: { M: 4, WS: 4 }, equipment: [{ item_id: "sword", quantity: 1, transferable: true }], skills: [], experience: 10, cost: 65, lost_eyes: [] },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0 }],
      post_battles: [{
        battle_number: 1, complete: false, active_step: 2, completed_steps: [0, 1], review_open: false,
        pending_follow_ups: [{ id: "injury:hero-1:1", type: "eye_injury", warrior_id: "hero-1" }],
        gold_delta: 0, wyrdstone_delta: 0, wyrdstone_sold: 0,
        experience_applied: false, pending_advances: [{ warrior_id: "hero-1", committed: false }],
        step_state: {}, sale_resolved: false, equipment_obligations: [{ warrior_id: "hero-1", item_id: "sword", item_name: "Sword", copies_per_model: 1 }], acknowledgements: {}, event_log: [], searches: {},
      }],
      inventory: [{ id: "sword", owned: 1, equipped: 1, stash: 0, value: 10 }], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

describe("resolveHatred (desktop resolve_hatred_target)", () => {
  it("records the selected target and closes the follow-up", () => {
    const result = resolveHatred(makePending(), { follow_up_id: "injury:hero-1:1", target: "Reiklander Captain" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const post = result.document.campaign.post_battles[0];
    expect(result.document.campaign.warriors[0].hatreds).toEqual(["Reiklander Captain"]);
    expect(post.pending_follow_ups).not.toContainEqual(expect.objectContaining({ id: "injury:hero-1:1" }));
    expect(post.event_log?.[0].description).toContain("permanently hates Reiklander Captain");
  });

  it("does not duplicate a target already recorded", () => {
    const doc = makePending();
    (doc.campaign.warriors[0] as unknown as { hatreds: string[] }).hatreds = ["Reiklander Captain"];
    const result = resolveHatred(doc, { follow_up_id: "injury:hero-1:1", target: "Reiklander Captain" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.warriors[0].hatreds).toEqual(["Reiklander Captain"]);
  });

  it("rejects a blank target", () => {
    const result = resolveHatred(makePending(), { follow_up_id: "injury:hero-1:1", target: "   " });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("hated");
  });

  it("rejects an unknown relationship follow-up", () => {
    const result = resolveHatred(makePending(), { follow_up_id: "injury:hero-1:9", target: "Reiklander Captain" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("Bitter Enmity");
  });
});

describe("resolveEyeInjury (desktop resolve_lost_eye)", () => {
  it("records the eye and closes the follow-up", () => {
    const result = resolveEyeInjury(makeEyePending(), { follow_up_id: "injury:hero-1:1", eye: "left" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.warriors[0].lost_eyes).toEqual(["left"]);
    expect(result.document.campaign.post_battles[0].pending_follow_ups).toEqual([]);
  });

  it("rejects an invalid or already-lost eye", () => {
    const doc = makeEyePending();
    (doc.campaign.warriors[0] as unknown as { lost_eyes: string[] }).lost_eyes = ["left"];
    const repeated = resolveEyeInjury(doc, { follow_up_id: "injury:hero-1:1", eye: "left" });
    expect(repeated.ok).toBe(false);
    if (!repeated.ok) expect(repeated.message).toContain("remaining eye");
    const bad = resolveEyeInjury(makeEyePending(), { follow_up_id: "injury:hero-1:1", eye: "blink" });
    expect(bad.ok).toBe(false);
    if (!bad.ok) expect(bad.message).toContain("remaining eye");
  });

  it("rejects an unknown eye-injury follow-up", () => {
    const result = resolveEyeInjury(makeEyePending(), { follow_up_id: "injury:hero-1:9", eye: "left" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("Unknown eye-injury");
  });

  it("retires the warrior on a second eye, discarding carried gear and pending work", () => {
    const doc = makeEyePending();
    (doc.campaign.warriors[0] as unknown as { lost_eyes: string[] }).lost_eyes = ["right"];
    const result = resolveEyeInjury(doc, { follow_up_id: "injury:hero-1:1", eye: "left" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.warriors.map((w) => w.id)).not.toContain("hero-1");
    expect(result.document.campaign.inventory).toEqual([]);
    const post = result.document.campaign.post_battles[0];
    expect(post.pending_follow_ups).toEqual([]);
    expect(post.pending_advances).toEqual([]);
    expect(post.equipment_obligations).toEqual([]);
    expect(post.event_log?.[0].description).toContain("retires");
  });
});
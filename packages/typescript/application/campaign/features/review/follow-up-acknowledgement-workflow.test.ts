/**
 * Parity port of the desktop follow-up acknowledgement behaviour in
 * `mordheim_campaign/domain/models.py` (`acknowledge`, `is_acknowledged`,
 * `unacknowledged_follow_ups`) — no dedicated desktop test; ported from the
 * implementation. Exercised against the web
 * `canAcknowledgeFollowUp` / `followUpNeedsResolution` / `acknowledgeFollowUp`
 * seams in `follow-up-acknowledgement-workflow.ts` — no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument, OpenPayload } from "../../../../domain/campaign/index";

import { acknowledgeFollowUp, canAcknowledgeFollowUp, followUpNeedsResolution } from "./follow-up-acknowledgement-workflow";

function makeDoc(pending_follow_ups: OpenPayload[]): CampaignDocument {
  const doc: unknown = {
    view: { selected_moment: "post:1" },
    campaign: {
      identity: { campaign_name: "Ack", warband_name: "Test", warband_type: "Middenheim", band_id: "middenheim", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0 }],
      post_battles: [{
        battle_number: 1, complete: false, active_step: 2, completed_steps: [0, 1], review_open: false,
        pending_follow_ups, gold_delta: 0, wyrdstone_delta: 0, wyrdstone_sold: 0,
        experience_applied: false, pending_advances: [],
        step_state: {}, sale_resolved: false, equipment_obligations: [], acknowledgements: {}, event_log: [], searches: {},
      }],
      inventory: [], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

describe("acknowledgeFollowUp (desktop models.py acknowledge)", () => {
  it("records the follow-up id under its step and logs the event", () => {
    const doc = makeDoc([{ id: "f1", step: 2, type: "encounter", description: "Found an Outhouse", encounter_id: "campaign.encounter.outhouse" }]);
    const result = acknowledgeFollowUp(doc, { follow_up_id: "f1" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const post = result.document.campaign.post_battles[0];
    expect(post.acknowledgements?.["2"]).toEqual(["f1"]);
    expect(post.event_log?.at(-1)).toMatchObject({ type: "follow_up_acknowledged" });
  });

  it("is idempotent when the follow-up is already acknowledged", () => {
    const doc = makeDoc([{ id: "f1", step: 2, type: "encounter", description: "Found an Outhouse", encounter_id: "campaign.encounter.outhouse" }]);
    const first = acknowledgeFollowUp(doc, { follow_up_id: "f1" });
    expect(first.ok).toBe(true);
    if (!first.ok) return;
    const second = acknowledgeFollowUp(first.document, { follow_up_id: "f1" });
    expect(second.ok).toBe(true);
    if (!second.ok) return;
    expect(second.document.campaign.post_battles[0].acknowledgements?.["2"]).toEqual(["f1"]);
  });

  it("rejects acknowledging a follow-up that requires its specific resolution", () => {
    const doc = makeDoc([{ id: "f1", step: 2, type: "injury_followup", description: "Roll a 2D6" }]);
    const result = acknowledgeFollowUp(doc, { follow_up_id: "f1" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("requires its specific resolution");
  });

  it("rejects a sold-to-the-pits encounter that must be resolved", () => {
    const doc = makeDoc([{ id: "f1", step: 2, type: "encounter", encounter_id: "campaign.encounter.sold-to-the-pits" }]);
    const result = acknowledgeFollowUp(doc, { follow_up_id: "f1" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("requires its specific resolution");
  });

  it("rejects an unknown follow-up", () => {
    const result = acknowledgeFollowUp(makeDoc([]), { follow_up_id: "nope" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("Unknown post-battle follow-up");
  });
});

describe("canAcknowledgeFollowUp / followUpNeedsResolution", () => {
  it("flags required types and mandatory rows as non-acknowledgeable", () => {
    expect(canAcknowledgeFollowUp({ id: "a", step: 2, type: "injury_followup" })).toBe(false);
    expect(canAcknowledgeFollowUp({ id: "a", step: 2, type: "prisoner" })).toBe(false);
    expect(canAcknowledgeFollowUp({ id: "a", step: 2, type: "eye_injury" })).toBe(false);
    expect(canAcknowledgeFollowUp({ id: "a", step: 2, type: "encounter", mandatory: true })).toBe(false);
    expect(canAcknowledgeFollowUp({ id: "a", step: 2, type: "encounter", encounter_id: "campaign.encounter.sold-to-the-pits" })).toBe(false);
    expect(canAcknowledgeFollowUp({ id: "a", step: 2, type: "encounter", encounter_id: "campaign.encounter.outhouse" })).toBe(true);
  });

  it("reports a follow-up as needing resolution until it is acknowledged", () => {
    const row: OpenPayload = { id: "f1", step: 2, type: "encounter", description: "Found an Outhouse", encounter_id: "campaign.encounter.outhouse" };
    expect(followUpNeedsResolution(row, {})).toBe(true);
    expect(followUpNeedsResolution(row, { "2": ["f1"] })).toBe(false);
  });

  it("always needs resolution for a required follow-up regardless of acknowledgement", () => {
    const row: OpenPayload = { id: "f1", step: 2, type: "injury_followup" };
    expect(followUpNeedsResolution(row, { "2": ["f1"] })).toBe(true);
  });
});
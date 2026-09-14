/**
 * Parity port of the desktop exploration follow-up behaviour in
 * `test_post_battle_engine.py`
 * (`test_returning_a_favour_adds_the_selected_hired_sword_for_free`).
 * Exercised against the web `continueExploration` seam in
 * `exploration-workflow.ts` — no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument, OpenPayload } from "../../../../domain/campaign/index";

import { continueExploration } from "./exploration-workflow";

const PROFILE = "hireling.hired-sword.undead-hunter";

/** Reader fake: one eligible hired sword, its profile, and its upkeep. */
const reader: any = {
  campaignRows(section: string) {
    if (section === "hired-swords-and-dramatis:hired_swords") {
      return [
        {
          id: "campaign.hireling.hired-sword.undead-hunter",
          profile_id: PROFILE,
          hiring_fee: { resources: { gold_crowns: { cost: 35 } } },
          upkeep: { resources: { gold_crowns: { cost: 15 } } },
          eligibility: {},
        },
      ];
    }
    return [];
  },
  list() {
    return [];
  },
  campaignSection(section: string) {
    if (section === "hirelings") return { rules: [] };
    return {};
  },
  queryKnowledge(query: { id: { kind: string; value: string } }) {
    if (query.id.kind === "hireling_id" && query.id.value === PROFILE) {
      return {
        ok: true,
        record: {
          names: { en: "Undead Hunter" },
          data: { warband_rating: { kind: "fixed", value: 25 }, characteristics: { M: 4, WS: 4 }, skills: [], rule_ids: [], upkeep_resources: [["gold", 15]] },
        },
      };
    }
    return { ok: false, reason: "not_found" };
  },
};

/** A pending post-battle with a Returning-a-Favour follow-up parked. */
function makeDoc(): CampaignDocument {
  const doc: unknown = {
    view: { selected_moment: "post:1" },
    campaign: {
      identity: { campaign_name: "Favour", warband_name: "Test", warband_type: "Middenheim", band_id: "middenheim", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "hero-1", name: "Sigrid", profile_name: "Captain", kind: "hero", stats: { M: 4, WS: 4 }, equipment: [], skills: [], experience: 10, cost: 65 },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0 }],
      post_battles: [{
        battle_number: 1, complete: false, active_step: 3, completed_steps: [0, 1, 2], review_open: false,
        pending_follow_ups: [{
          id: "exploration:1", type: "exploration_followup", step: 3, result_id: "campaign.exploration.returning-a-favour",
          description: "Returning a Favour", queue: [{ type: "choose_hireling", label: "Choose a Hired Sword" }], messages: [],
        }],
        gold_delta: 0, wyrdstone_delta: 0, wyrdstone_sold: 0,
        experience_applied: true, pending_advances: [],
        step_state: {}, sale_resolved: false, equipment_obligations: [], acknowledgements: {}, event_log: [], searches: {},
      }],
      inventory: [], special_rules: [], manual_log: [], unique_reward_ids: [],
    },
  };
  return doc as CampaignDocument;
}

const pendingOf = (doc: CampaignDocument): OpenPayload | null =>
  (doc.campaign.post_battles[0].pending_follow_ups?.[0] as OpenPayload | undefined)?.["pending"] as OpenPayload ?? null;

describe("continueExploration — Returning a Favour", () => {
  it("preserves each follow-up roll for the exploration summary", () => {
    const doc = makeDoc();
    const post = doc.campaign.post_battles[0];
    (post as unknown as { step_state: Record<string, unknown> }).step_state = { exploration: { resolved: true, dice: [5, 4], total: 9 } };
    (post.pending_follow_ups![0] as OpenPayload)["queue"] = [];
    (post.pending_follow_ups![0] as OpenPayload)["pending"] = { kind: "roll", label: { es: "Cantidad de coronas" }, dice_count: 2, dice_sides: 6, spec: { type: "resource_roll", recipient: "warband", resource: "gold_crowns", multiplier: 1 } };
    const result = continueExploration(doc, reader, { roll: 7, dice: [4, 3] });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect((result.document.campaign.post_battles[0].step_state?.["exploration"] as OpenPayload)["follow_up_rolls"]).toEqual([{ label: { es: "Cantidad de coronas" }, dice: [4, 3], total: 7 }]);
  });

  it("offers the eligible Hired Sword and hires it for free with the special rule", () => {
    const staged = continueExploration(makeDoc(), reader, {});
    expect(staged.ok).toBe(true);
    if (!staged.ok) return;
    const pending = pendingOf(staged.document);
    expect(pending?.["kind"]).toBe("choose_option");
    const option = ((pending?.["options"] ?? []) as OpenPayload[]).find((row) => row["id"] === PROFILE);
    expect(option).toBeDefined();

    const before = staged.document.campaign.warriors.length;
    const hired = continueExploration(staged.document, reader, { option_id: PROFILE });
    expect(hired.ok).toBe(true);
    if (!hired.ok) return;
    const warriors = hired.document.campaign.warriors;
    expect(warriors.length).toBe(before + 1);
    const newcomer = warriors[warriors.length - 1];
    expect(newcomer.kind).toBe("hireling");
    expect(newcomer.profile_id).toBe(PROFILE);
    expect(newcomer.cost).toBe(0);
    expect(newcomer.special_rules?.some((rule) => rule.includes("Returning a Favour"))).toBe(true);
    // The follow-up closes once its queue drains.
    expect(hired.document.campaign.post_battles[0].pending_follow_ups).toEqual([]);
    expect((hired.document.campaign.post_battles[0].step_state?.["exploration"] as OpenPayload)["special_effects"])
      .toContain("Undead Hunter");
  });

  it("rejects an option that is not offered", () => {
    const staged = continueExploration(makeDoc(), reader, {});
    if (!staged.ok) return;
    const bad = continueExploration(staged.document, reader, { option_id: "nope" });
    expect(bad.ok).toBe(false);
    if (!bad.ok) expect(bad.message).toContain("available outcomes");
  });
});

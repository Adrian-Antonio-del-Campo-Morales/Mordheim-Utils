/**
 * Parity port of the desktop hired-sword hire behaviour in
 * `test_post_battle_engine.py` (`test_hire_hireling_from_catalogue`,
 * `test_hired_swords_use_separate_capacity_income_and_rating_counts`) and the
 * `hire_hireling` guards. Exercised against the web `hireHireling` kernel seam
 * — plain Node, no React, no service.
 */
import { describe, expect, it } from "vitest";

import type { KnowledgeReader, OpenPayload } from "../index";
import type { CampaignDocument } from "./usecases";
import { hireHireling } from "./hirelings";

/** Minimal artefact-shaped reader for a hired-sword profile. */
function makeReader(overrides: OpenPayload = {}): KnowledgeReader {
  const profile: OpenPayload = {
    warband_rating: { kind: "base_plus_experience", base: 15, per_experience_point: 1 },
    characteristics: { M: 4, WS: 4, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
    equipment: { fixed_items: [{ item_id: "hunting_rifle", quantity: { value: 1 } }] },
    upkeep_resources: [["gold", 15]],
    starting_skill_ids: [],
    rule_ids: [],
    ...overrides,
  };
  const records: Record<string, OpenPayload> = {
    "hireling_id:hireling.hired-sword.undead-hunter": { id: "hireling.hired-sword.undead-hunter", name: "Undead Hunter", names: { en: "Undead Hunter" }, ...profile },
    "item_id:hunting_rifle": { item_id: "hunting_rifle", kind: "ranged-weapon", name: "Hunting Rifle", names: { en: "Hunting Rifle" }, value: 0 },
  };
  return {
    queryKnowledge(query: { id: { kind: string; value: string } }) {
      const row = records[`${query.id.kind}:${query.id.value}`];
      if (!row) return { ok: false as const, reason: "not_found" as const };
      const { id, name, names, ...data } = row;
      return {
        ok: true as const,
        record: {
          kind: query.id.kind.replace(/_id$/, "") as never,
          id: query.id as never,
          names: (names ?? { en: name }) as Record<string, string>,
          data: data as OpenPayload,
        },
      };
    },
    queryMany() {
      return [];
    },
    campaignSection(section: string) {
      if (section === "hirelings") return { rules: [] };
      return {};
    },
  } as unknown as KnowledgeReader;
}

function makeDoc(is_draft = false, warriors: unknown[] = []): CampaignDocument {
  const doc: unknown = {
    view: { selected_moment: "post:1" },
    campaign: {
      identity: { campaign_name: "Hire", warband_name: "Test", warband_type: "Middenheim", band_id: "middenheim", mercenary_variant: null },
      configuration: { is_draft, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors,
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0 }],
      post_battles: [],
      inventory: [], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

const PROFILE = "hireling.hired-sword.undead-hunter";

describe("hireHireling (desktop hire_hireling)", () => {
  it("hires a catalogue Hired Sword, copying stats and granting fixed equipment", () => {
    const result = hireHireling(makeDoc(), { profile_id: PROFILE, fee: 35 }, makeReader());
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const hired = result.state.campaign.warriors.find((w) => w.kind === "hireling");
    expect(hired?.profile_id).toBe(PROFILE);
    expect(hired?.cost).toBe(35);
    expect(hired?.hireling_rating).toBe(15);
    expect(hired?.stats.M).toBe(4);
    expect(hired?.upkeep_resources).toEqual([["gold", 15]]);
    // The fixed item lands in the inventory as equipped (desktop grants loadout).
    const rifle = result.state.campaign.inventory.find((row) => row.id === "hunting_rifle");
    expect(rifle?.owned).toBe(1);
    expect(rifle?.equipped).toBe(1);
  });

  it("falls back to the rating base as cost when no fee is given", () => {
    const result = hireHireling(makeDoc(), { profile_id: PROFILE }, makeReader());
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.state.campaign.warriors.find((w) => w.kind === "hireling")?.cost).toBe(15);
  });

  it("uses a fixed warband_rating block when the profile has one", () => {
    const reader = makeReader({ warband_rating: { kind: "fixed", value: 75 } });
    const result = hireHireling(makeDoc(), { profile_id: PROFILE }, reader);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.state.campaign.warriors.find((w) => w.kind === "hireling")?.hireling_rating).toBe(75);
  });

  it("rejects hiring the same profile twice", () => {
    const first = hireHireling(makeDoc(), { profile_id: PROFILE }, makeReader());
    expect(first.ok).toBe(true);
    if (!first.ok) return;
    const again = hireHireling(first.state, { profile_id: PROFILE }, makeReader());
    expect(again.ok).toBe(false);
    if (!again.ok) expect(again.reason).toBe("conflict");
  });

  it("allows hiring in a draft and rejects an unknown profile", () => {
    const draft = hireHireling(makeDoc(true), { profile_id: PROFILE }, makeReader());
    expect(draft.ok).toBe(true);
    if (draft.ok) expect(draft.state.campaign.warriors.some((warrior) => warrior.kind === "hireling")).toBe(true);
    const unknown = hireHireling(makeDoc(), { profile_id: "nope" }, makeReader());
    expect(unknown.ok).toBe(false);
    if (!unknown.ok) expect(unknown.reason).toBe("not_found");
  });

  it("gates a conditional hire on the acceptance roll (desktop acceptance_roll)", () => {
    const missing = hireHireling(makeDoc(), { profile_id: PROFILE, roll_ge: 4 }, makeReader());
    expect(missing.ok).toBe(false);
    if (!missing.ok) expect(missing.reason).toBe("prerequisite_missing");
    const failed = hireHireling(makeDoc(), { profile_id: PROFILE, roll_ge: 4, acceptance_roll: 3 }, makeReader());
    expect(failed.ok).toBe(false);
    if (!failed.ok) expect(failed.message).toContain("failed");
    const passed = hireHireling(makeDoc(), { profile_id: PROFILE, roll_ge: 4, acceptance_roll: 5 }, makeReader());
    expect(passed.ok).toBe(true);
  });

  it("resolves a variable fee from fee_base + fee_roll (desktop fee_roll)", () => {
    const missing = hireHireling(makeDoc(), { profile_id: PROFILE, fee_base: 70, fee_dice: [3, 6] }, makeReader());
    expect(missing.ok).toBe(false);
    if (!missing.ok) expect(missing.message).toContain("Roll");
    const tooLow = hireHireling(makeDoc(), { profile_id: PROFILE, fee_base: 70, fee_dice: [3, 6], fee_roll: 2 }, makeReader());
    expect(tooLow.ok).toBe(false);
    if (!tooLow.ok) expect(tooLow.message).toContain("below the minimum");
    const ok = hireHireling(makeDoc(), { profile_id: PROFILE, fee_base: 70, fee_dice: [3, 6], fee_roll: 12 }, makeReader());
    expect(ok.ok).toBe(true);
    if (ok.ok) expect(ok.state.campaign.warriors.find((w) => w.kind === "hireling")?.cost).toBe(82);
  });

  it("rejects a fee declared both flat and as dice", () => {
    const result = hireHireling(makeDoc(), { profile_id: PROFILE, fee: 35, fee_dice: [3, 6], fee_roll: 12 }, makeReader());
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("conflict");
  });

  it("carries a hireling rule's maximum-models modifier onto the warrior", () => {
    const reader = makeReader({ rule_ids: ["campaign.hireling.rule.halfling-scout"] }) as KnowledgeReader & {
      campaignSection?(section: string): Readonly<Record<string, unknown>>;
    };
    (reader as { campaignSection: (s: string) => unknown }).campaignSection = (section: string) =>
      section === "hirelings"
        ? { rules: [{ id: "campaign.hireling.rule.halfling-scout", mechanics: [{ type: "warband.maximum_models_modifier", value: 1 }] }] }
        : {};
    const result = hireHireling(makeDoc(), { profile_id: PROFILE }, reader);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.state.campaign.warriors.find((w) => w.kind === "hireling")?.maximum_models_modifier).toBe(1);
  });
});

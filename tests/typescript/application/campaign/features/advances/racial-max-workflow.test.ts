/**
 * Parity port of the desktop `test_racial_maximum_blocks_further_increases`
 * from `test_post_battle_advancements.py`, grounded in the desktop engine.
 * Exercised against the web `resolveAdvanceRoll` → `applyCharacteristic` seam —
 * no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument } from "@domain/campaign/index";
import type { KnowledgeReader } from "@domain/campaign/kernel/ports";
import { resolveAdvanceRoll } from "@app/campaign/features/advances/advance-resolution-workflow";

type CatalogueReader = KnowledgeReader & {
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
  list?(kind: string): readonly Readonly<Record<string, unknown>>[];
};

/** Human warband with racial max T 4; hero roll 9 sub-roll → +1 T. */
function racialReader(): CatalogueReader {
  return {
    queryKnowledge: () => ({ ok: false as const, reason: "not_found" }),
    queryMany: (queries) => queries.map(() => ({ ok: false as const, reason: "not_found" })),
    list: (kind) => {
      if (kind === "warband_group") return [{ id: "warband-group.human", band_ids: ["sisters-of-sigmar"] }];
      if (kind === "racial_maximum") return [{ profile: "human", characteristics: { toughness: 4 } }];
      return [];
    },
    campaignSection: (section) =>
      section === "experience-and-advances"
        ? { advancement_tables: [{ applies_to: "hero", resolution: { branches: [
            { when: { min: 9, max: 9 }, result: { type: "roll_table", branches: [
              { when: { min: 1, max: 6 }, result: { type: "choose_one", options: [
                { type: "characteristic_increase", characteristic: "toughness", amount: 1 },
              ] } },
            ] } },
          ] } }] }
        : {},
  };
}

function fixture(toughness: number): CampaignDocument {
  const doc: unknown = {
    view: {},
    campaign: {
      identity: { campaign_name: "Max", warband_name: "Test", warband_type: "Sisters of Sigmar", band_id: "sisters-of-sigmar", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "matriarch", name: "Sigrid", profile_name: "Matriarch", kind: "hero", profile_id: "sigmarite-matriarch", stats: { M: 4, WS: 4, T: toughness }, equipment: [], skills: [], experience: 20, cost: 65 },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 1, max_models: 15, heroes: 1, henchmen: 0, experience: 20 }],
      post_battles: [{
        battle_number: 1, complete: false, active_step: 0, completed_steps: [], review_open: false, pending_follow_ups: [],
        pending_advances: [{ warrior_id: "matriarch", warrior_name: "Sigrid", table: "hero", threshold: 20, roll_total: null, subroll: null, committed: false, applied_label: "" }],
      }],
      inventory: [], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

describe("racial maximum reopens the advance for a reroll", () => {
  it("blocks a +1 T at the human racial maximum", () => {
    const rolled = resolveAdvanceRoll(fixture(4), racialReader(), { warrior_id: "matriarch", threshold: 20, roll_total: 9 });
    expect(rolled.ok && rolled.needs_subroll).toBe(true);
    if (!rolled.ok || !rolled.needs_subroll) return;
    const result = resolveAdvanceRoll(rolled.document, racialReader(), { warrior_id: "matriarch", threshold: 20, roll_total: 9, subroll: 6 });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const row = result.document.campaign.post_battles[0].pending_advances!.find((r) => r["warrior_id"] === "matriarch")!;
    expect(row["committed"]).toBe(false);
    expect(row["roll_total"]).toBeNull(); // reopened for a reroll
    expect((row["roll_history"] as string[])?.length).toBeGreaterThan(0);
    expect((row["roll_history"] as string[])[0]).toContain("advance cap");
  });

  it("blocks a henchman at the base+1 cap", () => {
    // Henchman cap = profile base (T 3) + 1 = 4; warrior already at 4.
    const henchReader: CatalogueReader = {
      queryKnowledge: (query) =>
        query.id.kind === "profile_id"
          ? { ok: true as const, record: { kind: "profile", id: { kind: "profile_id", value: "sister" }, names: { en: "Sister" }, data: { characteristics: { T: 3 } } } }
          : { ok: false as const, reason: "not_found" },
      queryMany: (queries) => queries.map(() => ({ ok: false as const, reason: "not_found" })),
      campaignSection: (section) =>
        section === "experience-and-advances"
          ? { advancement_tables: [{ applies_to: "henchman_group", resolution: { branches: [
              { when: { min: 9, max: 9 }, result: { type: "roll_table", branches: [
                { when: { min: 1, max: 6 }, result: { type: "choose_one", options: [
                  { type: "characteristic_increase", characteristic: "toughness", amount: 1 },
                ] } },
              ] } },
            ] } }] }
          : {},
    };
    const doc: unknown = {
      view: {},
      campaign: {
        identity: { campaign_name: "HenchCap", warband_name: "Test", warband_type: "Sisters of Sigmar", band_id: "sisters-of-sigmar", mercenary_variant: null },
        configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
        resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
        current_state_number: 1,
        warriors: [{ id: "sister", name: "Sisters", profile_name: "Sister", kind: "henchman", profile_id: "sister", stats: { M: 4, WS: 3, T: 4 }, equipment: [], skills: [], experience: 20, cost: 45, quantity: 1 }],
        battles: [],
        states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 1, max_models: 15, heroes: 0, henchmen: 1, experience: 20 }],
        post_battles: [{
          battle_number: 1, complete: false, active_step: 0, completed_steps: [], review_open: false, pending_follow_ups: [],
          pending_advances: [{ warrior_id: "sister", warrior_name: "Sisters", table: "henchman_group", threshold: 8, roll_total: null, subroll: null, committed: false, applied_label: "" }],
        }],
        inventory: [], special_rules: [], manual_log: [],
      },
    };
    const rolled = resolveAdvanceRoll(doc as CampaignDocument, henchReader, { warrior_id: "sister", threshold: 8, roll_total: 9 });
    expect(rolled.ok && rolled.needs_subroll).toBe(true);
    if (!rolled.ok || !rolled.needs_subroll) return;
    const result = resolveAdvanceRoll(rolled.document, henchReader, { warrior_id: "sister", threshold: 8, roll_total: 9, subroll: 6 });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const row = result.document.campaign.post_battles[0].pending_advances!.find((r) => r["warrior_id"] === "sister")!;
    expect(row["committed"]).toBe(false);
    expect(row["roll_total"]).toBeNull();
    expect((row["roll_history"] as string[])[0]).toContain("advance cap");
  });

  it("allows the increase below the racial maximum", () => {
    const rolled = resolveAdvanceRoll(fixture(3), racialReader(), { warrior_id: "matriarch", threshold: 20, roll_total: 9 });
    expect(rolled.ok && rolled.needs_subroll).toBe(true);
    if (!rolled.ok || !rolled.needs_subroll) return;
    const result = resolveAdvanceRoll(rolled.document, racialReader(), { warrior_id: "matriarch", threshold: 20, roll_total: 9, subroll: 6 });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const hero = result.document.campaign.warriors.find((w) => w.id === "matriarch")!;
    expect(hero.stats["T"]).toBe(4);
    expect(hero.stat_advances).toEqual({ T: 1 });
    expect(result.document.campaign.post_battles[0].pending_advances!.find((r) => r["warrior_id"] === "matriarch")!["committed"]).toBe(true);
  });
});
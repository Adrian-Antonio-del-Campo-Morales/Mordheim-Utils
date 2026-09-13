/**
 * Parity port of the desktop battle-experience behaviour in
 * `test_post_battle_advancements.py` / `test_extended_audit_regressions.py`
 * (`apply_battle_experience`, `add_xp`, `sync_pending_advances`), grounded in
 * desktop `post_battle_engine.py`. Exercised against the web
 * `experienceAwards` / `applyBattleExperience` seams — no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument, Warrior, OpenPayload } from "../../../../domain/campaign/index";
import type { KnowledgeReader } from "../../../../domain/campaign/kernel/ports";
import { applyBattleExperience, experienceAwards } from "./experience-workflow";

/** Neutral KB: every profile may gain experience; default advance thresholds. */
const knowledge: KnowledgeReader = {
  queryKnowledge: () => ({ ok: false as const, reason: "not_found" }),
  queryMany: (queries) => queries.map(() => ({ ok: false as const, reason: "not_found" })),
};

function hero(id: string, name: string, experience: number): Warrior {
  return { id, name, profile_name: "Matriarch", kind: "hero", profile_id: id, stats: { M: 4, WS: 4 }, equipment: [], skills: [], experience, cost: 65 };
}

function henchman(id: string, name: string, experience: number): Warrior {
  return { id, name, profile_name: "Sister", kind: "henchman", profile_id: id, stats: { M: 4, WS: 3 }, equipment: [], skills: [], experience, cost: 45, quantity: 1 };
}

function makePending(xpDelta: number, warriors: readonly Warrior[], absentees: readonly unknown[] = [], opponentRating?: number | null): CampaignDocument {
  const doc: unknown = {
    view: {},
    campaign: {
      identity: { campaign_name: "XP", warband_name: "Test", warband_type: "Sisters of Sigmar", band_id: "sisters-of-sigmar", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [...warriors],
      battles: [{ number: 1, scenario_id: "scenario.skirmish", scenario_name: "Skirmish", opponent: "X", result: "Draw", xp_delta: xpDelta, rating_before: 100, opponent_rating: opponentRating, absentees, xp_awards: {}, out_of_action_ids: [] }],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 1, max_models: 15, heroes: 1, henchmen: 0, experience: 10 }],
      post_battles: [{ battle_number: 1, complete: false, active_step: 0, completed_steps: [], review_open: false, experience_applied: false, pending_advances: [], pending_follow_ups: [] }],
      inventory: [], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

describe("experienceAwards read model", () => {
  it("gives the common award to survivors and zero to absentees", () => {
    const doc = makePending(4, [hero("hero-1", "Sigrid", 5), henchman("absent-1", "Greta", 5)], [{ id: "absent-1" }]);
    const awards = experienceAwards(doc, knowledge);
    const byId = new Map(awards.map((row) => [row.warrior_id, row]));
    expect(byId.get("hero-1")).toMatchObject({ amount: 4, eligible: true, absent: false });
    expect(byId.get("absent-1")).toMatchObject({ amount: 0, absent: true });
  });

  it("adds the underdog bonus to every participating eligible warrior", () => {
    const doc = makePending(1, [hero("hero-1", "Sigrid", 5), henchman("absent-1", "Greta", 5)], [{ id: "absent-1" }], 201);
    expect(experienceAwards(doc, knowledge).map((row) => row.amount)).toEqual([4, 0]);
  });

  it.each([[150, 0], [151, 1], [176, 2], [201, 3], [251, 4], [401, 5]])("uses the published underdog band for opponent rating %i", (opponentRating, bonus) => {
    const doc = makePending(0, [hero("hero-1", "Sigrid", 5)], [], opponentRating);
    expect(experienceAwards(doc, knowledge)[0].amount).toBe(bonus);
  });
});

describe("applyBattleExperience (desktop apply_battle_experience)", () => {
  it("does not grant advances retroactively for initial experience", () => {
    const result = applyBattleExperience(makePending(1, [hero("hero-1", "Sigrid", 20)]), knowledge);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.post_battles[0].pending_advances).toEqual([]);
  });

  it("awards XP once and seeds a pending advance when a threshold is crossed", () => {
    const doc = makePending(4, [hero("hero-1", "Sigrid", 5), henchman("hench-1", "Novices", 5)]);
    const result = applyBattleExperience(doc, knowledge);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const heroRow = result.document.campaign.warriors.find((w) => w.id === "hero-1")!;
    expect(heroRow.experience).toBe(9);
    // Henchman 5+4=9 crosses the 9-XP henchman threshold → an advance is seeded.
    const advances = result.document.campaign.post_battles[0].pending_advances!;
    expect(advances.some((row) => row["warrior_id"] === "hench-1" && row["threshold"] === 9)).toBe(true);
    expect(result.document.campaign.post_battles[0].experience_applied).toBe(true);
    // Applying a second time is a typed conflict.
    const again = applyBattleExperience(result.document, knowledge);
    expect(again.ok).toBe(false);
    if (!again.ok) expect(again.reason).toBe("conflict");
  });

  it("honours per-warrior scenario awards over the common delta", () => {
    const doc = makePending(0, [hero("hero-1", "Sigrid", 5), hero("hero-2", "Greta", 5)]);
    (doc.campaign.battles[0] as { xp_awards?: Record<string, number> }).xp_awards = { "hero-1": 5, "hero-2": 2 };
    const result = applyBattleExperience(doc, knowledge);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const hero1 = result.document.campaign.warriors.find((w) => w.id === "hero-1")!;
    const hero2 = result.document.campaign.warriors.find((w) => w.id === "hero-2")!;
    expect(hero1.experience).toBe(10);
    expect(hero2.experience).toBe(7);
  });

  it("seeds the advance crossed by experience granted during injuries", () => {
    const doc = makePending(0, [hero("hero-1", "Sigrid", 24)]);
    (doc.campaign.post_battles[0] as { step_state?: Record<string, OpenPayload> }).step_state = { injury_experience_before: { "hero-1": 23 } };
    const result = applyBattleExperience(doc, knowledge);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.post_battles[0].pending_advances).toEqual([
      expect.objectContaining({ warrior_id: "hero-1", threshold: 24, committed: false }),
    ]);
  });
});

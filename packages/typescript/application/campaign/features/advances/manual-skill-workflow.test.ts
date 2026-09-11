/**
 * Parity port of the desktop `set_manual_skill` (controller.py), grounded in
 * the desktop guards and audit log. Exercised against the web `setManualSkill`
 * seam in `manual-skill-workflow.ts` — no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument, Warrior } from "../../../../domain/campaign/index";
import type { KnowledgeReader } from "../../../../domain/campaign/kernel/ports";
import { setManualSkill } from "./manual-skill-workflow";

/** KB: profile with an inherent rule; three skills with categories. */
function reader(): KnowledgeReader {
  const queryKnowledge: KnowledgeReader["queryKnowledge"] = (query) => {
    if (query.id.kind === "skill_id") {
      const skill: Record<string, string> = {
        combat: "Combat Skill", start: "Start Skill", str: "Strength Skill",
      };
      const category: Record<string, string> = { combat: "Combat", start: "Combat", str: "Strength" };
      const id = String(query.id.value);
      if (!skill[id]) return { ok: false, reason: "not_found" };
      return { ok: true, record: { kind: "skill", id: { kind: "skill_id", value: id }, names: { en: skill[id] }, data: { category: category[id] } } };
    }
    if (query.id.kind === "profile_id") {
      return { ok: true, record: { kind: "profile", id: { kind: "profile_id", value: "hero-1" }, names: { en: "Matriarch" }, data: { type: "hero", inherent_rules: ["Start Skill"], combat_traits: { starting_skills: [] } } } };
    }
    return { ok: false, reason: "not_found" };
  };
  return { queryKnowledge, queryMany: (queries) => queries.map((q) => queryKnowledge(q)) };
}

function makeFixture(warrior: Warrior, hasPendingPost = true): CampaignDocument {
  const doc: unknown = {
    view: {},
    campaign: {
      identity: { campaign_name: "Skills", warband_name: "Test", warband_type: "Sisters of Sigmar", band_id: "sisters-of-sigmar", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [warrior],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 1, max_models: 15, heroes: 1, henchmen: 0, experience: 10 }],
      post_battles: hasPendingPost ? [{ battle_number: 1, complete: false, active_step: 0, completed_steps: [], review_open: false, pending_follow_ups: [] }] : [],
      inventory: [], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

function hero(skills: readonly string[] = []): Warrior {
  return { id: "hero-1", name: "Sigrid", profile_name: "Matriarch", kind: "hero", profile_id: "hero-1", stats: { M: 4, WS: 4 }, equipment: [], skills: [...skills], experience: 10, cost: 65, skill_access: ["Combat"] };
}

describe("setManualSkill (desktop set_manual_skill)", () => {
  it("adds a legal skill and records the audit entry", () => {
    const result = setManualSkill(makeFixture(hero()), reader(), { warrior_id: "hero-1", skill_id: "combat", present: true, reason: "Campaign reward" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const h = result.document.campaign.warriors[0];
    expect(h.skills).toEqual(["Combat Skill"]);
    expect(result.document.campaign.manual_log).toEqual([
      expect.objectContaining({ type: "manual_skill_correction", action: "added", skill: "Combat Skill", reason: "Campaign reward" }),
    ]);
  });

  it("removes a legal skill and records the audit entry", () => {
    const result = setManualSkill(makeFixture(hero(["Combat Skill"])), reader(), { warrior_id: "hero-1", skill_id: "combat", present: false, reason: "Errata" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.warriors[0].skills).toEqual([]);
    expect(result.document.campaign.manual_log).toEqual([
      expect.objectContaining({ action: "removed", skill: "Combat Skill" }),
    ]);
  });

  it("requires a reason", () => {
    const result = setManualSkill(makeFixture(hero()), reader(), { warrior_id: "hero-1", skill_id: "combat", present: true, reason: "  " });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("reason");
  });

  it("allows editing only during creation or post-battle", () => {
    const result = setManualSkill(makeFixture(hero(), false), reader(), { warrior_id: "hero-1", skill_id: "combat", present: true, reason: "Reward" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("creation or post-battle");
  });

  it("cannot remove an inherent or starting skill", () => {
    const result = setManualSkill(makeFixture(hero(["Start Skill"])), reader(), { warrior_id: "hero-1", skill_id: "start", present: false, reason: "Correction" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("cannot be removed");
  });

  it("rejects adding a skill outside the warrior's skill access", () => {
    const result = setManualSkill(makeFixture(hero()), reader(), { warrior_id: "hero-1", skill_id: "str", present: true, reason: "Reward" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("skill access");
  });
});
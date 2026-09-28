/**
 * T10 — Born Marksmen (`axe-hurlers--born-marksmen`).
 *
 * "If an Axe Hurler rolls a 'That Lad's Got Talent' as an advancement, he may
 * always choose Shooting skills as one of his two skill list choices. He may do
 * this even if there are no heroes with Shooting Skills in the warband."
 *
 * The crafted reader publishes a band whose hero tables do NOT include Shooting,
 * so the grant is what makes the choice possible. The advance flow must then
 * allow a published Shooting skill and reject one outside the chosen tables, a
 * profile the grant does not name, and a duplicate.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument } from "@domain/campaign/index";
import type { KnowledgeReader } from "@domain/campaign/kernel/ports";
import {
  commitAdvanceChoice,
  promoteHenchman,
  promotionTablesForWarrior,
  resolveAdvanceRoll,
  setPromotionSkillTables,
} from "@app/campaign/features/advances/advance-resolution-workflow";

type CatalogueReader = KnowledgeReader & {
  list?(kind: string): readonly Readonly<Record<string, unknown>>[];
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
};

const BAND = "dwarf-slayer-cult-web";
const SKILLS: Readonly<Record<string, { category: string; kind: string; name: string }>> = {
  "skill.marksman": { category: "shooting", kind: "general", name: "Marksman" },
  "skill.strike": { category: "combat", kind: "general", name: "Strike" },
};

/** A band with a Combat/Speed hero table and the Born Marksmen grant. */
function reader(): CatalogueReader {
  return {
    queryKnowledge: (query) => {
      if (query.id.kind !== "skill_id") return { ok: false as const, reason: "not_found" };
      const skill = SKILLS[query.id.value];
      return skill
        ? { ok: true as const, record: { kind: "skill" as const, id: query.id.value, names: { en: skill.name }, data: { category: skill.category, kind: skill.kind } } }
        : { ok: false as const, reason: "not_found" };
    },
    queryMany: (queries) => queries.map(() => ({ ok: false as const, reason: "not_found" })),
    list: (kind) =>
      kind === "profile"
        ? [{ id: "giant-slayer", band_id: BAND, type: "hero", skill_access: ["combat", "speed"] }]
        : [],
    campaignSection: (section) => {
      if (section === "experience-and-advances") {
        return { advancement_tables: [{ applies_to: "hero", resolution: { branches: [{ when: { min: 2, max: 12 }, result: { type: "choose_skill" } }] } }] };
      }
      if (section === "recruitment-and-veterans") {
        return {
          advance_access_clauses: [
            { id: "campaign.advance-access.axe-hurlers-born-marksmen", band_id: BAND, rule_id: "axe-hurlers--born-marksmen", trigger: "that-lads-got-talent", profile_ids: ["axe-hurlers"], skill_lists: ["shooting"] },
          ],
        };
      }
      return {};
    },
  };
}

function document(profileId: string): CampaignDocument {
  return {
    view: {},
    campaign: {
      identity: { campaign_name: "Marksmen", warband_name: "Slayers", warband_type: "Slayers", band_id: BAND, mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "slayer", name: "Slayer", profile_name: "giant-slayer", kind: "hero", profile_id: "giant-slayer", stats: {}, equipment: [], skills: [], experience: 10, cost: 0 },
        { id: "hurlers", name: "Hurlers", profile_name: profileId, kind: "henchman", profile_id: profileId, stats: {}, equipment: [], skills: [], experience: 6, cost: 0, quantity: 2 },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-28", gold: 500, wyrdstone: 0, rating: 0, models: 2, max_models: 15, heroes: 1, henchmen: 1, experience: 16 }],
      post_battles: [{
        battle_number: 1, complete: false, active_step: 1, completed_steps: [], review_open: false,
        pending_advances: [{ warrior_id: "hurlers", warrior_name: "Hurlers", table: "henchman_group", threshold: null, roll_total: 10, subroll: null, committed: false, applied_label: "", advance_options: [{ kind: "promote_henchman" }] }],
        step_state: {}, event_log: [], gold_delta: 0,
      }],
      inventory: [], special_rules: [], manual_log: [],
    },
  } as CampaignDocument;
}

function promote(doc: CampaignDocument, name: string): { document: CampaignDocument; heroId: string } {
  const promoted = promoteHenchman(doc, reader(), { warrior_id: "hurlers", threshold: null, member_name: name });
  expect(promoted.ok, promoted.ok ? "" : promoted.message).toBe(true);
  if (!promoted.ok) throw new Error(promoted.message);
  const hero = promoted.document.campaign.warriors.find((row) => row.id.includes("promoted"))!;
  return { document: promoted.document, heroId: hero.id };
}

function pendingRow(document: CampaignDocument, warriorId: string) {
  return document.campaign.post_battles[0].pending_advances!.find((row) => row["warrior_id"] === warriorId);
}

describe("Born Marksmen (advancement-time skill access)", () => {
  it("offers Shooting to the Axe Hurler even though the band's hero tables omit it", () => {
    const { document: promoted, heroId } = promote(document("axe-hurlers"), "Nato");
    expect(promotionTablesForWarrior(promoted, reader(), heroId)).toEqual(["combat", "speed", "shooting"]);
    const setup = setPromotionSkillTables(promoted, reader(), { warrior_id: heroId, tables: ["shooting", "speed"] });
    expect(setup.ok, setup.ok ? "" : setup.message).toBe(true);
    if (!setup.ok) return;
    expect(setup.document.campaign.warriors.find((row) => row.id === heroId)?.skill_access).toEqual(["shooting", "speed"]);
    expect(pendingRow(setup.document, heroId)!["promotion_setup_pending"]).toBe(false);
  });

  it("lets the promoted hero commit a published Shooting skill and rejects one outside the tables", () => {
    const { document: promoted, heroId } = promote(document("axe-hurlers"), "Nato");
    const setup = setPromotionSkillTables(promoted, reader(), { warrior_id: heroId, tables: ["shooting", "speed"] });
    expect(setup.ok).toBe(true);
    if (!setup.ok) return;
    const rolled = resolveAdvanceRoll(setup.document, reader(), { warrior_id: heroId, threshold: null, roll_total: 5 });
    expect(rolled.ok, rolled.ok ? "" : rolled.message).toBe(true);
    if (!rolled.ok) return;
    const allowed = commitAdvanceChoice(rolled.document, reader(), { warrior_id: heroId, threshold: null, kind: "choose_skill", skill_id: "skill.marksman" });
    expect(allowed.ok, allowed.ok ? "" : allowed.message).toBe(true);
    if (!allowed.ok) return;
    expect(allowed.document.campaign.warriors.find((row) => row.id === heroId)?.skills).toEqual(["Marksman"]);
    // Duplicate: the same skill cannot be learned twice.
    const duplicate = commitAdvanceChoice(allowed.document, reader(), { warrior_id: heroId, threshold: null, kind: "choose_skill", skill_id: "skill.marksman" });
    expect(duplicate.ok).toBe(false);
    if (!duplicate.ok) expect(duplicate.message).toContain("already knows");

    // A skill outside the chosen tables is refused.
    const fresh = setPromotionSkillTables(promoted, reader(), { warrior_id: heroId, tables: ["shooting", "speed"] });
    expect(fresh.ok).toBe(true);
    if (!fresh.ok) return;
    const reroll = resolveAdvanceRoll(fresh.document, reader(), { warrior_id: heroId, threshold: null, roll_total: 5 });
    if (!reroll.ok) return;
    const outside = commitAdvanceChoice(reroll.document, reader(), { warrior_id: heroId, threshold: null, kind: "choose_skill", skill_id: "skill.strike" });
    expect(outside.ok).toBe(false);
    if (!outside.ok) expect(outside.message).toContain("outside this Hero's skill tables");
  });

  it("does not grant Shooting to a profile the clause does not name", () => {
    const { document: promoted, heroId } = promote(document("troll-slayers"), "Troll");
    expect(promotionTablesForWarrior(promoted, reader(), heroId)).toEqual(["combat", "speed"]);
    const refused = setPromotionSkillTables(promoted, reader(), { warrior_id: heroId, tables: ["shooting", "speed"] });
    expect(refused.ok).toBe(false);
    if (!refused.ok) expect(refused.message).toContain("available");
  });
});

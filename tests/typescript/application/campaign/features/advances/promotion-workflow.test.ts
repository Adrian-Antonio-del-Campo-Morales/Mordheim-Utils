/**
 * Parity port of the desktop promotion tests in `test_post_battle_advancements.py`
 * (`promote_henchman`, `set_promotion_skill_tables`), grounded in the desktop
 * `post_battle_engine.py` implementations. Exercised against the web seams
 * `promoteHenchman`, `setPromotionSkillTables`, `promotionHeroTables` in
 * `advance-resolution-workflow.ts` — no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument } from "@domain/campaign/index";
import type { KnowledgeReader } from "@domain/campaign/kernel/ports";
import {
  commitAdvanceChoice,
  promoteHenchman,
  promotionHeroTables,
  promotionTablesForWarrior,
  resolveAdvanceRoll,
  setPromotionSkillTables,
} from "@app/campaign/features/advances/advance-resolution-workflow";

type CatalogueReader = KnowledgeReader & {
  list?(kind: string): readonly Readonly<Record<string, unknown>>[];
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
};

/** One Hero profile with the skill lists the promoted Henchman may choose. */
function reader(): CatalogueReader {
  return {
    queryKnowledge: () => ({ ok: false as const, reason: "not_found" }),
    queryMany: (queries) => queries.map(() => ({ ok: false as const, reason: "not_found" })),
    list: (kind) =>
      kind === "profile"
        ? [{ id: "profile.matriarch", band_id: "sisters-of-sigmar", type: "hero", skill_access: ["Combat", "Speed", "Accuracy", "Strength"] }]
        : [],
    campaignSection: (section) =>
      section === "experience-and-advances"
        ? {
            advancement_tables: [
              { applies_to: "hero", resolution: { branches: [
                { when: { min: 8, max: 8 }, result: { type: "roll_table", branches: [
                  { when: { min: 1, max: 6 }, result: { type: "choose_one", options: [
                    { type: "characteristic_increase", characteristic: "weapon_skill", amount: 1 },
                  ] } },
                ] } },
              ] } },
            ],
          }
        : {},
  };
}

/** A pending post-battle with an offered Lad's Got Talent advance. */
function makePromotion(quantity = 2, heroLimit = 5): CampaignDocument {
  const doc: unknown = {
    view: {},
    campaign: {
      identity: { campaign_name: "Promo", warband_name: "Test", warband_type: "Sisters of Sigmar", band_id: "sisters-of-sigmar", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: heroLimit },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "matriarch", name: "Sigrid", profile_name: "Matriarch", kind: "hero", profile_id: "matriarch", stats: { M: 4, WS: 4 }, equipment: [], skills: [], experience: 10, cost: 65 },
        {
          id: "novices", name: "Novices", profile_name: "Novice", kind: "henchman", profile_id: "novice",
          stats: { M: 4, WS: 4, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
          equipment: [{ item_id: "club", name: "Club", quantity, per_model: true, transferable: false, acquisition: "fixed", unit_cost: 0 }],
          skills: [], experience: 8, cost: 30, quantity, stat_advances: { WS: 1 },
        },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 3, max_models: 15, heroes: 1, henchmen: 1, experience: 18 }],
      post_battles: [{
        battle_number: 1, complete: false, active_step: 0, completed_steps: [], review_open: false,
        pending_follow_ups: [],
        pending_advances: [
          { warrior_id: "novices", warrior_name: "Novices", table: "henchman_group", threshold: null, roll_total: null, subroll: null, committed: false, applied_label: "", advance_options: [{ kind: "promote_henchman" }] },
        ],
        veteran_pool: 0, sale_resolved: true, step_state: {}, gold_delta: 0, equipment_obligations: [], event_log: [], searches: {},
      }],
      inventory: [], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

function pendingRow(document: CampaignDocument, warriorId: string) {
  return document.campaign.post_battles[0].pending_advances!.find((row) => row["warrior_id"] === warriorId);
}

describe("promoteHenchman (desktop promote_henchman)", () => {
  it("splits the group and preserves the promoted member's state", () => {
    const result = promoteHenchman(makePromotion(2), reader(), { warrior_id: "novices", threshold: null, member_name: "Novice Olaf" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const hero = result.document.campaign.warriors.find((w) => w.kind === "hero" && w.id.includes("promoted"))!;
    expect(hero.name).toBe("Novice Olaf");
    expect(hero.kind).toBe("hero");
    expect(hero.experience).toBe(8);
    expect(hero.stats["WS"]).toBe(4);
    expect(hero.stat_advances).toEqual({ WS: 1 });
    const novices = result.document.campaign.warriors.find((w) => w.id === "novices")!;
    expect((novices as { quantity?: number }).quantity).toBe(1);
    expect(novices.kind).toBe("henchman");
    // Remaining group rerolls; the Hero gets a separate immediate advance.
    const groupRow = pendingRow(result.document, "novices")!;
    expect(groupRow["roll_total"]).toBeNull();
    expect(groupRow["reroll_exclude_promotion"]).toBe(true);
    const heroRow = pendingRow(result.document, hero.id)!;
    expect(heroRow["promotion_setup_pending"]).toBe(true);
  });

  it("replaces a single-model group with the Hero", () => {
    const result = promoteHenchman(makePromotion(1), reader(), { warrior_id: "novices", threshold: null });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.warriors.some((w) => w.id === "novices")).toBe(false);
    expect(result.document.campaign.warriors.some((w) => w.kind === "hero" && w.id.includes("promoted"))).toBe(true);
  });

  it("the remaining group rerolls results 10-12 after a promotion", () => {
    const promoted = promoteHenchman(makePromotion(2), reader(), { warrior_id: "novices", threshold: null });
    expect(promoted.ok).toBe(true);
    if (!promoted.ok) return;
    const result = resolveAdvanceRoll(promoted.document, reader(), { warrior_id: "novices", threshold: null, roll_total: 11 });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const groupRow = pendingRow(result.document, "novices")!;
    expect(groupRow["roll_total"]).toBeNull();
    expect((groupRow["roll_history"] as string[] | undefined)?.length).toBeGreaterThan(0);
  });

  it("at the hero limit reopens the advance for a reroll instead of promoting", () => {
    // heroLimit 1 with the existing Matriarch Hero → already at the cap.
    const result = promoteHenchman(makePromotion(2, 1), reader(), { warrior_id: "novices", threshold: null, member_name: "Novice Olaf" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.warriors.some((w) => w.name === "Novice Olaf")).toBe(false);
    expect(pendingRow(result.document, "novices")!["roll_total"]).toBeNull();
  });
});

describe("setPromotionSkillTables (desktop set_promotion_skill_tables)", () => {
  it("lists the warband Hero skill tables", () => {
    expect(promotionHeroTables(makePromotion(2), reader())).toEqual(["Combat", "Speed", "Accuracy", "Strength"]);
  });

  it("accepts exactly two available Hero skill lists and clears the setup", () => {
    const promoted = promoteHenchman(makePromotion(2), reader(), { warrior_id: "novices", threshold: null });
    expect(promoted.ok).toBe(true);
    if (!promoted.ok) return;
    const hero = promoted.document.campaign.warriors.find((w) => w.kind === "hero" && w.id.includes("promoted"))!;
    const result = setPromotionSkillTables(promoted.document, reader(), { warrior_id: hero.id, tables: ["Combat", "Speed"] });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const updated = result.document.campaign.warriors.find((w) => w.id === hero.id)!;
    expect(updated.skill_access).toEqual(["Combat", "Speed"]);
    expect(pendingRow(result.document, hero.id)!["promotion_setup_pending"]).toBe(false);
  });

  it("commits the Hero's stat advance once the two skill lists are chosen", () => {
    const promoted = promoteHenchman(makePromotion(2), reader(), { warrior_id: "novices", threshold: null, member_name: "Novice Olaf" });
    expect(promoted.ok).toBe(true);
    if (!promoted.ok) return;
    const hero = promoted.document.campaign.warriors.find((w) => w.kind === "hero" && w.id.includes("promoted"))!;
    const setup = setPromotionSkillTables(promoted.document, reader(), { warrior_id: hero.id, tables: ["Combat", "Speed"] });
    expect(setup.ok).toBe(true);
    if (!setup.ok) return;
    // The Hero's immediate advance needs a sub-roll first.
    const rolled = resolveAdvanceRoll(setup.document, reader(), { warrior_id: hero.id, threshold: null, roll_total: 8 });
    expect(rolled.ok && rolled.needs_subroll).toBe(true);
    if (!rolled.ok || !rolled.needs_subroll) return;
    const resolved = resolveAdvanceRoll(rolled.document, reader(), { warrior_id: hero.id, threshold: null, roll_total: 8, subroll: 2 });
    expect(resolved.ok).toBe(true);
    if (!resolved.ok) return;
    const updated = resolved.document.campaign.warriors.find((w) => w.id === hero.id)!;
    expect(updated.stats["WS"]).toBe(5);
    expect(updated.stat_advances).toEqual({ WS: 2 });
    expect(pendingRow(resolved.document, hero.id)!["committed"]).toBe(true);
  });

  it("rejects lists outside the warband Hero tables or the wrong count", () => {
    const promoted = promoteHenchman(makePromotion(2), reader(), { warrior_id: "novices", threshold: null });
    expect(promoted.ok).toBe(true);
    if (!promoted.ok) return;
    const hero = promoted.document.campaign.warriors.find((w) => w.kind === "hero" && w.id.includes("promoted"))!;
    const badTable = setPromotionSkillTables(promoted.document, reader(), { warrior_id: hero.id, tables: ["Combat", "Not a table"] });
    expect(badTable.ok).toBe(false);
    if (!badTable.ok) expect(badTable.message).toContain("available");
    const wrongCount = setPromotionSkillTables(promoted.document, reader(), { warrior_id: hero.id, tables: ["Combat"] });
    expect(wrongCount.ok).toBe(false);
  });
});

/**
 * External-audit regression: the printed promotion grant of the Ogre
 * (`compiler.promoted-hero-skill-access`) governs the promoted Hero's tables
 * without granting them to the unpromoted Henchman.
 */
describe("promoted Ogre skill tables (compiler.promoted-hero-skill-access)", () => {
  const OGRE_BAND = "ostlanders";
  function ogreReader(): CatalogueReader {
    const queryKnowledge: CatalogueReader["queryKnowledge"] = (query) => {
      if (query.id.kind === "skill_id") {
        const value = query.id.value as string;
        if (value === "skill.arcane-lore" || value === "skill.mighty-blow") return { ok: true, record: {
          kind: "skill", id: { kind: "skill_id", value }, names: { en: value },
          data: { category: value === "skill.arcane-lore" ? "academic" : "strength" } } };
      }
      return { ok: false as const, reason: "not_found" };
    };
    return {
      queryKnowledge,
      queryMany: (queries) => queries.map((query) => queryKnowledge(query)),
      list: (kind) => kind === "profile" ? [
        { id: "ogre", band_id: OGRE_BAND, type: "henchman", skill_access: [], promotion_skill_access: ["combat", "strength"] },
        { id: "elder", band_id: OGRE_BAND, type: "hero", skill_access: ["combat", "shooting", "strength", "speed", "special"] },
      ] : [],
      campaignSection: () => ({}),
    };
  }

  /** A promoted Ogre Hero with a pending skill advance; `skillAccess` is the state under test. */
  function promotedOgre(skillAccess: readonly string[]): CampaignDocument {
    const doc: unknown = {
      view: {},
      campaign: {
        identity: { campaign_name: "Promo", warband_name: "Test", warband_type: "Ostlanders", band_id: OGRE_BAND, mercenary_variant: null },
        configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
        resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
        current_state_number: 1,
        warriors: [{ id: "ogre#promoted", name: "Ogre Champion", profile_name: "Ogre", kind: "hero", profile_id: "ogre",
          stats: { M: 6, WS: 3, BS: 2, S: 4, T: 4, W: 3, I: 3, A: 1, Ld: 8 }, equipment: [], skills: [], experience: 8, cost: 110,
          skill_access: [...skillAccess] }],
        battles: [], states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 1, max_models: 15, heroes: 1, henchmen: 0, experience: 8 }],
        post_battles: [{ battle_number: 1, complete: false, active_step: 0, completed_steps: [], review_open: false,
          pending_follow_ups: [],
          pending_advances: [{ warrior_id: "ogre#promoted", warrior_name: "Ogre Champion", table: "hero", threshold: null,
            roll_total: 11, subroll: null, committed: false, applied_label: "", advance_options: [{ kind: "choose_skill" }] }],
          veteran_pool: 0, sale_resolved: true, step_state: {}, gold_delta: 0, equipment_obligations: [], event_log: [], searches: {} }],
        inventory: [], special_rules: [], manual_log: [],
      },
    };
    return doc as CampaignDocument;
  }

  /** A pending promotion of a single Ogre Henchman in the Ostlanders band. */
  function makeOgrePromotion(): CampaignDocument {
    const doc: unknown = {
      view: {},
      campaign: {
        identity: { campaign_name: "Promo", warband_name: "Test", warband_type: "Ostlanders", band_id: OGRE_BAND, mercenary_variant: null },
        configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
        resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
        current_state_number: 1,
        warriors: [{ id: "ogres", name: "Ogres", profile_name: "Ogre", kind: "henchman", profile_id: "ogre",
          stats: { M: 6, WS: 3, BS: 2, S: 4, T: 4, W: 3, I: 3, A: 1, Ld: 8 }, equipment: [], skills: [], experience: 8, cost: 110, quantity: 1 }],
        battles: [], states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 1, max_models: 15, heroes: 0, henchmen: 1, experience: 8 }],
        post_battles: [{ battle_number: 1, complete: false, active_step: 0, completed_steps: [], review_open: false,
          pending_follow_ups: [],
          pending_advances: [{ warrior_id: "ogres", warrior_name: "Ogres", table: "henchman_group", threshold: null,
            roll_total: null, subroll: null, committed: false, applied_label: "", advance_options: [{ kind: "promote_henchman" }] }],
          veteran_pool: 0, sale_resolved: true, step_state: {}, gold_delta: 0, equipment_obligations: [], event_log: [], searches: {} }],
        inventory: [], special_rules: [], manual_log: [],
      },
    };
    return doc as CampaignDocument;
  }

  it("offers the printed grant instead of the band's generic hero tables", () => {
    const promoted = promoteHenchman(makeOgrePromotion(), ogreReader(), { warrior_id: "ogres", threshold: null });
    expect(promoted.ok).toBe(true);
    if (!promoted.ok) return;
    const hero = promoted.document.campaign.warriors.find((w) => w.kind === "hero" && w.id.includes("promoted"))!;
    expect(promotionTablesForWarrior(promoted.document, ogreReader(), hero.id)).toEqual(["combat", "strength"]);
    expect(setPromotionSkillTables(promoted.document, ogreReader(), { warrior_id: hero.id, tables: ["combat", "strength"] }).ok).toBe(true);
    expect(setPromotionSkillTables(promoted.document, ogreReader(), { warrior_id: hero.id, tables: ["shooting", "speed"] }).ok).toBe(false);
  });

  it("refuses an academic skill and accepts the granted tables", () => {
    const arcane = commitAdvanceChoice(promotedOgre(["combat", "strength"]), ogreReader(),
      { warrior_id: "ogre#promoted", threshold: null, kind: "choose_skill", skill_id: "skill.arcane-lore" });
    expect(arcane.ok).toBe(false);
    if (!arcane.ok) expect(arcane.message).toContain("outside");
    const granted = commitAdvanceChoice(promotedOgre(["combat", "strength"]), ogreReader(),
      { warrior_id: "ogre#promoted", threshold: null, kind: "choose_skill", skill_id: "skill.mighty-blow" });
    expect(granted.ok).toBe(true);
  });

  it("still refuses an academic skill for an unprepared promoted state", () => {
    const result = commitAdvanceChoice(promotedOgre([]), ogreReader(),
      { warrior_id: "ogre#promoted", threshold: null, kind: "choose_skill", skill_id: "skill.arcane-lore" });
    expect(result.ok).toBe(false);
  });
});
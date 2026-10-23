/**
 * Parity port of the desktop advance-commit tests in
 * `test_post_battle_advancements.py` (`commit_pending_advance` with
 * choose_skill / generate_spell / duplicate_spell), grounded in the desktop
 * controller/engine. Exercised against the web `commitAdvanceChoice` seam —
 * no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument, OpenPayload } from "@domain/campaign/index";
import type { KnowledgeReader } from "@domain/campaign/kernel/ports";
import { commitAdvanceChoice, resolveAdvanceRoll } from "@app/campaign/features/advances/advance-resolution-workflow";

type CatalogueReader = KnowledgeReader & { campaignSection?(section: string): Readonly<Record<string, unknown>> };

/** A wizard lore + a Combat skill; only the Matriarch profile is a wizard. */
function reader(): CatalogueReader {
  const queryKnowledge: KnowledgeReader["queryKnowledge"] = (query) => {
    if (query.id.kind === "lore_id" && query.id.value === "lore.sigmar") {
      return { ok: true, record: { kind: "lore", id: { kind: "lore_id", value: "lore.sigmar" }, names: { en: "Sigmar" }, data: { spells: [{ id: "spell.comet", name: "Comet" }, { id: "spell.hammer", name: "Sigmar's Hammer" }] } } };
    }
    if (query.id.kind === "skill_id" && query.id.value === "combat-master") {
      return { ok: true, record: { kind: "skill", id: { kind: "skill_id", value: "combat-master" }, names: { en: "Combat Master" }, data: { category: "Combat" } } };
    }
    return { ok: false, reason: "not_found" };
  };
  return {
    queryKnowledge,
    queryMany: (queries) => queries.map((q) => queryKnowledge(q)),
    campaignSection: (section) =>
      section === "magic"
        ? { lore_assignments: { rows: [{ profile_id: "sigmarite-matriarch", band: "sisters-of-sigmar", lore: "lore.sigmar" }] } }
        : {},
  };
}

function makeFixture(targetId: string, options: readonly OpenPayload[], knownSkills: readonly string[] = []): CampaignDocument {
  const doc: unknown = {
    view: {},
    campaign: {
      identity: { campaign_name: "Commit", warband_name: "Test", warband_type: "Sisters of Sigmar", band_id: "sisters-of-sigmar", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "matriarch", name: "Sigrid", profile_name: "Matriarch", kind: "hero", profile_id: "sigmarite-matriarch", stats: { M: 4, WS: 4 }, equipment: [], skills: [...knownSkills], experience: 20, cost: 65, skill_access: ["Combat"] },
        { id: "anna", name: "Anna", profile_name: "Sister Superior", kind: "hero", profile_id: "sister-superior", stats: { M: 4, WS: 3 }, equipment: [], skills: [], experience: 20, cost: 45, skill_access: ["Combat"] },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 2, max_models: 15, heroes: 2, henchmen: 0, experience: 40 }],
      post_battles: [{
        battle_number: 1, complete: false, active_step: 0, completed_steps: [], review_open: false, pending_follow_ups: [],
        pending_advances: [{ warrior_id: targetId, warrior_name: targetId, table: "hero", threshold: 20, roll_total: 11, subroll: null, committed: false, applied_label: "", advance_options: options }],
      }],
      inventory: [], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

function pendingRow(document: CampaignDocument, targetId: string) {
  return document.campaign.post_battles[0].pending_advances!.find((row) => row["warrior_id"] === targetId);
}

describe("commitAdvanceChoice — skill (desktop commit_pending_advance)", () => {
  it("adds a skill from the warrior's tables and rejects a repeated commit", () => {
    const result = commitAdvanceChoice(makeFixture("matriarch", [{ kind: "choose_skill" }]), reader(), { warrior_id: "matriarch", threshold: 20, kind: "choose_skill", skill_id: "combat-master" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const hero = result.document.campaign.warriors.find((w) => w.id === "matriarch")!;
    expect(hero.skills).toEqual(["Combat Master"]);
    expect(pendingRow(result.document, "matriarch")!["committed"]).toBe(true);
    const again = commitAdvanceChoice(result.document, reader(), { warrior_id: "matriarch", threshold: 20, kind: "choose_skill", skill_id: "combat-master" });
    expect(again.ok).toBe(false);
  });
});

describe("commitAdvanceChoice — spell (desktop commit_pending_advance)", () => {
  it("a wizard learns a spell from their own lore", () => {
    const result = commitAdvanceChoice(makeFixture("matriarch", [{ kind: "generate_spell" }]), reader(), { warrior_id: "matriarch", threshold: 20, kind: "generate_spell", skill_id: "spell.comet" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const hero = result.document.campaign.warriors.find((w) => w.id === "matriarch")!;
    expect(hero.skills).toEqual(["Comet"]);
    expect(pendingRow(result.document, "matriarch")!["committed"]).toBe(true);
  });

  it("a non-wizard cannot learn spells", () => {
    const result = commitAdvanceChoice(makeFixture("anna", [{ kind: "generate_spell" }]), reader(), { warrior_id: "anna", threshold: 20, kind: "generate_spell", skill_id: "spell.comet" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("lore");
  });
});

describe("commitAdvanceChoice — duplicate spell (desktop duplicate_spell)", () => {
  it("persists a difficulty modifier and does not add a second skill entry", () => {
    const result = commitAdvanceChoice(makeFixture("matriarch", [{ kind: "generate_spell" }], ["Comet"]), reader(), { warrior_id: "matriarch", threshold: 20, kind: "duplicate_spell", skill_id: "spell.comet" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const hero = result.document.campaign.warriors.find((w) => w.id === "matriarch")!;
    expect(hero.skills).toEqual(["Comet"]);
    expect(hero.spell_difficulty_modifiers).toEqual({ "spell.comet": -1 });
  });

  it("rejects duplicating a spell the warrior does not know yet", () => {
    const result = commitAdvanceChoice(makeFixture("matriarch", [{ kind: "generate_spell" }], []), reader(), { warrior_id: "matriarch", threshold: 20, kind: "duplicate_spell", skill_id: "spell.comet" });
    expect(result.ok).toBe(false);
  });
});

describe("resolveAdvanceRoll offers choose_skill + generate_spell only to wizards", () => {
  /** Advancement table whose roll-11 branch offers a skill and a spell. */
  function rollReader(): CatalogueReader {
    return {
      queryKnowledge: () => ({ ok: false as const, reason: "not_found" }),
      queryMany: (queries) => queries.map(() => ({ ok: false as const, reason: "not_found" })),
      campaignSection: (section) => {
        if (section === "experience-and-advances") {
          return { advancement_tables: [{ applies_to: "hero", resolution: { branches: [{ when: { min: 11, max: 11 }, result: { type: "choose_one", options: [{ type: "choose_skill" }, { type: "generate_spell" }] } }] } }] };
        }
        if (section === "magic") {
          return { lore_assignments: { rows: [{ profile_id: "sigmarite-matriarch", band: "sisters-of-sigmar", lore: "lore.sigmar" }] } };
        }
        return {};
      },
    };
  }

  function rollFixture(targetId: string): CampaignDocument {
    const doc: unknown = {
      view: {},
      campaign: {
        identity: { campaign_name: "Roll", warband_name: "Test", warband_type: "Sisters of Sigmar", band_id: "sisters-of-sigmar", mercenary_variant: null },
        configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
        resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
        current_state_number: 1,
        warriors: [
          { id: "matriarch", name: "Sigrid", profile_name: "Matriarch", kind: "hero", profile_id: "sigmarite-matriarch", stats: { M: 4, WS: 4 }, equipment: [], skills: [], experience: 20, cost: 65, skill_access: ["Combat"] },
          { id: "anna", name: "Anna", profile_name: "Sister Superior", kind: "hero", profile_id: "sister-superior", stats: { M: 4, WS: 3 }, equipment: [], skills: [], experience: 20, cost: 45, skill_access: ["Combat"] },
        ],
        battles: [],
        states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 2, max_models: 15, heroes: 2, henchmen: 0, experience: 40 }],
        post_battles: [{
          battle_number: 1, complete: false, active_step: 0, completed_steps: [], review_open: false, pending_follow_ups: [],
          pending_advances: [{ warrior_id: targetId, warrior_name: targetId, table: "hero", threshold: 20, roll_total: null, subroll: null, committed: false, applied_label: "" }],
        }],
        inventory: [], special_rules: [], manual_log: [],
      },
    };
    return doc as CampaignDocument;
  }

  function offeredKinds(document: CampaignDocument, targetId: string): Set<string> {
    const row = document.campaign.post_battles[0].pending_advances!.find((r) => r["warrior_id"] === targetId)!;
    return new Set(((row["advance_options"] as OpenPayload[]) ?? []).map((option) => String(option["kind"])));
  }

  it("a wizard keeps the spell option", () => {
    const result = resolveAdvanceRoll(rollFixture("matriarch"), rollReader(), { warrior_id: "matriarch", threshold: 20, roll_total: 11 });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(offeredKinds(result.document, "matriarch")).toEqual(new Set(["choose_skill", "generate_spell"]));
  });

  it("a non-wizard loses the spell option", () => {
    const result = resolveAdvanceRoll(rollFixture("anna"), rollReader(), { warrior_id: "anna", threshold: 20, roll_total: 11 });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(offeredKinds(result.document, "anna")).toEqual(new Set(["choose_skill"]));
  });
});
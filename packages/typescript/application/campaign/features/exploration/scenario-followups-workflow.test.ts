/**
 * Parity port of the desktop scenario-reward tests in `test_battle_creation.py`
 * (`test_tome_reward_grants_exactly_two_selected_spells`,
 * `test_encampment_reward_requires_destroy_or_occupy_choice`), grounded in the
 * desktop `post_battle_engine.py` implementations. Exercised against the web
 * `scenario-followups-workflow.ts` seams — no service, no React.
 */
import { describe, expect, it } from "vitest";

import type { CampaignDocument, OpenPayload, Warrior } from "../../../../domain/campaign/index";
import type { KnowledgeReader } from "../../../../domain/campaign/kernel/ports";
import {
  resolveScenarioEncampment,
  resolveScenarioSpellReward,
  scenarioSpellOptions,
} from "./scenario-followups-workflow";

type CatalogueReader = KnowledgeReader & { campaignSection?(section: string): Readonly<Record<string, unknown>> };

/** A Mercenaries band with one Hero and the warband's magic lores. */
function reader(): CatalogueReader {
  return {
    queryKnowledge: () => ({ ok: false as const, reason: "not_found" }),
    queryMany: (queries) => queries.map(() => ({ ok: false as const, reason: "not_found" })),
    campaignSection: (section) =>
      section === "magic"
        ? {
            lore_assignments: { rows: [{ profile_id: "hero-1", band: "mercenaries", lore: "lore.battle-magic" }] },
            lores: [
              { id: "lore.lesser-magic", spells: [{ id: "spell.dazzle", name: "Dazzle" }, { id: "spell.tire", name: "Tire" }] },
              { id: "lore.battle-magic", spells: [{ id: "spell.fireball", name: "Fireball" }] },
            ],
          }
        : {},
  };
}

function makeFixture(followUp: OpenPayload, overrides: Partial<Warrior> = {}): CampaignDocument {
  const doc: unknown = {
    view: {},
    campaign: {
      identity: { campaign_name: "Rewards", warband_name: "Test", warband_type: "Mercenaries", band_id: "mercenaries", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 1,
      warriors: [
        { id: "hero-1", name: "Renzo", profile_name: "Captain", kind: "hero", profile_id: "hero-1", stats: { M: 4, WS: 4 }, equipment: [], skills: [], experience: 10, cost: 65, ...overrides },
      ],
      battles: [],
      states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 1, max_models: 15, heroes: 1, henchmen: 0, experience: 10 }],
      post_battles: [{ battle_number: 1, complete: false, active_step: 0, completed_steps: [], review_open: false, pending_follow_ups: [followUp] }],
      inventory: [], special_rules: [], manual_log: [],
    },
  };
  return doc as CampaignDocument;
}

describe("resolveScenarioSpellReward (desktop resolve_scenario_spell_reward)", () => {
  const tome: OpenPayload = { id: "tome", type: "scenario_spell_reward", label: "Tome of Magic" };

  it("lists the spells a Hero may learn, including the warband's own lore", () => {
    const options = scenarioSpellOptions(makeFixture(tome), reader(), "hero-1");
    expect(options.map((spell) => spell.id)).toEqual(["spell.dazzle", "spell.tire", "spell.fireball"]);
  });

  it("grants exactly the two selected spells to the Hero", () => {
    const result = resolveScenarioSpellReward(makeFixture(tome), reader(), {
      follow_up_id: "tome",
      hero_id: "hero-1",
      spell_ids: ["spell.dazzle", "spell.fireball"],
    });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const hero = result.document.campaign.warriors.find((w) => w.id === "hero-1")!;
    expect(hero.skills).toEqual(["Dazzle", "Fireball"]);
    expect(result.document.campaign.post_battles[0].pending_follow_ups).toHaveLength(0);
  });

  it("requires exactly two spells", () => {
    const result = resolveScenarioSpellReward(makeFixture(tome), reader(), {
      follow_up_id: "tome",
      hero_id: "hero-1",
      spell_ids: ["spell.dazzle"],
    });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("exactly two");
  });

  it("rejects spells outside the Hero's available lores", () => {
    const result = resolveScenarioSpellReward(makeFixture(tome), reader(), {
      follow_up_id: "tome",
      hero_id: "hero-1",
      spell_ids: ["spell.nonexistent", "spell.dazzle"],
    });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("available");
  });

  it("rejects spells the Hero already knows", () => {
    const result = resolveScenarioSpellReward(makeFixture(tome, { skills: ["Dazzle"] }), reader(), {
      follow_up_id: "tome",
      hero_id: "hero-1",
      spell_ids: ["spell.dazzle", "spell.fireball"],
    });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("already");
  });
});

describe("resolveScenarioEncampment (desktop resolve_scenario_encampment)", () => {
  const camp: OpenPayload = { id: "camp", type: "scenario_encampment", label: "Captured camp" };

  it("occupying records a captured-camp special rule and clears the follow-up", () => {
    const result = resolveScenarioEncampment(makeFixture(camp), { follow_up_id: "camp", choice: "occupy" });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.special_rules.some((rule) => String(rule.text).toLowerCase().includes("captured camp"))).toBe(true);
    expect(result.document.campaign.post_battles[0].pending_follow_ups).toHaveLength(0);
  });

  it("rejects any choice other than destroy or occupy", () => {
    const result = resolveScenarioEncampment(makeFixture(camp), { follow_up_id: "camp", choice: "burn" });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("destroy or occupy");
  });
});
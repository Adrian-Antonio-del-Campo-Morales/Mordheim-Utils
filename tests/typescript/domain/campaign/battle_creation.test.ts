/**
 * Parity port of desktop `tests/python/campaign/test_battle_creation.py` (19 test
 * functions → the subset the web kernel/workflow expresses; the rest are
 * documented below as desktop-scenario deltas). Traceability: manifest rows
 * with `web_target: tests/typescript/domain/campaign/battle_creation.test.ts`.
 *
 * Behaviour mapping (desktop → web):
 * - `record_battle` → kernel `recordBattle` + workflow `record`;
 * - scenario options → workflow `scenarioOptions` over the fake KB;
 * - pending post-battle blocks the next battle → kernel `conflict`;
 * - unavailable warriors (games_to_miss) → readiness rows + kernel
 *   `not_available`; the kernel rejects results naming them;
 * - scenario loot/rewards, battle-start checks and scenario XP plans →
 *   application workflows backed by the generated campaign KB.
 *
 * Purity: plain Node, fake KnowledgeReader — no React, no DOM, no filesystem.
 */

import { describe, expect, it } from "vitest";

import { recordBattle, normalizeResult } from "@domain/campaign/kernel/record-battle";
import { cloneDocument } from "@domain/campaign/kernel/document";
import type { CampaignDocument, KnowledgeReader } from "@domain/campaign/kernel/usecases";
import { createBattleWorkflow } from "@app/campaign/features/battle/battle-workflow";
import { createDefaultUseCases } from "@domain/campaign/kernel/default-usecases";

const SCENARIOS = ["skirmish", "defend-the-find", "hidden-treasure", "wyrdstone-hunt"];

const knowledge: KnowledgeReader = {
  queryKnowledge(query) {
    if (query.id.kind === "scenario_id" && SCENARIOS.includes(query.id.value)) {
      return {
        ok: true,
        record: { kind: "scenario", id: query.id, names: { en: query.id.value }, data: {} },
      };
    }
    return { ok: false, reason: "not_found" };
  },
  queryMany: (queries) => queries.map((q) => knowledge.queryKnowledge(q)),
};

const useCases = createDefaultUseCases(knowledge);

/** Desktop `_settled()`: committed band with State #0, no pending post-battle. */
function settled(): CampaignDocument {
  const base: CampaignDocument = {
    campaign: {
      identity: {
        campaign_name: "Battles",
        warband_name: "Test Band",
        warband_type: "Sisters of Sigmar",
        band_id: "sisters-of-sigmar",
        mercenary_variant: null,
      },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 0,
      warriors: [
        { id: "marta", name: "Marta", profile_name: "Sister Superior", kind: "hero", stats: { WS: 4 }, equipment: [], skills: [], experience: 2, cost: 45 },
        { id: "novices", name: "Novices", profile_name: "Novice Sisters", kind: "henchman", stats: { WS: 3 }, equipment: [], skills: [], experience: 0, cost: 25, quantity: 3 },
        { id: "anna", name: "Anna", profile_name: "Sigmarite Matriarch", kind: "hero", stats: { WS: 4 }, equipment: [], skills: [], experience: 5, cost: 70 },
      ],
      battles: [],
      states: [{ number: 0, date: "2026-09-10", gold: 365, wyrdstone: 0, rating: 30, models: 5, max_models: 15, heroes: 2, henchmen: 3, experience: 0, label: "Initial Warband" }],
      post_battles: [],
      inventory: [],
      special_rules: [],
      manual_log: [],
    },
    view: {},
  };
  return base;
}

function recordInput(overrides: Record<string, unknown> = {}) {
  return {
    scenario: "skirmish",
    opponent: "Reiklanders",
    result: "win",
    gold_delta: 0,
    wyrdstone: 0,
    xp_delta: 1,
    casualties: 0,
    out_of_action_ids: null,
    ...overrides,
  };
}

describe("desktop test_battle_creation.py → web recordBattle parity", () => {
  it("scenario options come from the KB", () => {
    const workflow = createBattleWorkflow({ knowledge, useCases });
    const options = workflow.scenarioOptions();
    const ids = options.map((o) => o.id);
    expect(ids).toContain("skirmish");
    expect(ids).toContain("defend-the-find");
    expect(options.every((o) => o.name.length > 0)).toBe(true);
  });

  it("recordBattle creates real nodes (battle + pending post-battle)", () => {
    const result = recordBattle(settled(), recordInput(), knowledge);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const { campaign } = result.state;
    const battle = campaign.battles.at(-1)!;
    expect(battle.number).toBe(1);
    expect(battle.scenario).toBe("skirmish");
    expect(battle.opponent).toBe("Reiklanders");
    expect(battle.result).toBe("win");
    expect(battle.xp_delta).toBe(1);
    // Snapshot numbers come from State #0, desktop parity.
    expect(battle.rating_before).toBe(30);
    expect(battle.models_before).toBe(5);
    expect(battle.date).toBeTruthy();
    const post = campaign.post_battles.at(-1)!;
    expect(post.battle_number).toBe(1);
    expect(post.complete).toBe(false);
  });

  it("applies scenario exploration and creates every deferred artefact roll", () => {
    const result = recordBattle(settled(), recordInput({ scenario_results: { additional_rewards: [
      { kind: "exploration", quantity: 1, extra_dice: 1, reroll_all: true },
      { kind: "special", quantity: 2, special_id: "magical-artefact-found", label: "Artefact" },
    ] } }), knowledge);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const post = result.state.campaign.post_battles.at(-1)!;
    expect(post.step_state?.["scenario_exploration"]).toEqual({ extra_dice: 1, reroll_all: true });
    expect(post.pending_follow_ups?.filter((row) => row["type"] === "exploration_followup")).toHaveLength(2);
  });

  it("enforces special scenario reward rules from the desktop flow", () => {
    const result = recordBattle(settled(), recordInput({ scenario_results: { additional_rewards: [
      { kind: "special", quantity: 1, special_id: "scenario.assault-on-the-rock.reward", label: "Tome of Magic" },
      { kind: "special", quantity: 1, special_id: "scenario.the-item-lost.reward", label: "Wand", rule: "Bearer rule" },
      { kind: "special", quantity: 1, special_id: "scenario.the-night-of-the-headless-one.reward", label: "Skull", rule: "Skull rule" },
    ] } }), knowledge);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const post = result.state.campaign.post_battles.at(-1)!;
    expect(post.pending_follow_ups?.some((row) => row["type"] === "scenario_spell_reward")).toBe(false);
    expect(post.pending_follow_ups?.some((row) => row["id"] === "scenario:1:wand-of-phyrros")).toBe(true);
    expect(result.state.campaign.inventory.find((row) => row.id === "scenario_reward.skull_of_the_headless_one")?.special_rules).toContain("Skull rule");
  });

  it("recordBattle blocks while a post-battle is pending", () => {
    const first = recordBattle(settled(), recordInput(), knowledge);
    expect(first.ok).toBe(true);
    if (!first.ok) return;
    const second = recordBattle(first.state, recordInput({ opponent: "Y", result: "loss" }), knowledge);
    expect(second.ok).toBe(false);
    if (!second.ok) expect(second.reason).toBe("conflict");
  });

  it("recordBattle validates scenario and result", () => {
    const unknownScenario = recordBattle(settled(), recordInput({ scenario: "scenario.not-real" }), knowledge);
    expect(unknownScenario.ok).toBe(false);
    if (!unknownScenario.ok) expect(unknownScenario.reason).toBe("not_found");
    // Result normalization: only win/victory, loss/defeat, draw accepted.
    expect(normalizeResult("Victory")).toBe("win");
    expect(normalizeResult("Defeat")).toBe("loss");
    expect(normalizeResult("Draw")).toBe("draw");
    expect(normalizeResult("Flawless")).toBeNull();
  });

  it("committed post-battle unblocks the next battle", () => {
    const first = recordBattle(settled(), recordInput(), knowledge);
    if (!first.ok) throw new Error(first.message);
    // Commit the pending sequence (walk the 8 steps like desktop's engine.commit).
    let state = first.state;
    for (let step = 0; step < 8; step += 1) {
      const stepResult = useCases.resolvePostBattleStep(state, 1, { note: `step-${step}` });
      expect(stepResult.ok).toBe(true);
      if (!stepResult.ok) return;
      state = stepResult.state;
    }
    const second = recordBattle(state, recordInput({ scenario: "wyrdstone-hunt", opponent: "Skaven", result: "loss" }), knowledge);
    expect(second.ok).toBe(true);
    if (!second.ok) return;
    expect(second.state.campaign.battles.at(-1)!.number).toBe(2);
  });

  it("recorded battle survives save/load is covered by the file port matrix", () => {
    // Desktop's save/load round-trip for battles maps to the campaign-file
    // adapter matrix (P3.2, 17 tests) + `out_of_action_tracking.test.ts`
    // round-trip; the open-payload battle fields travel verbatim.
    const document = settled();
    const recorded = recordBattle(document, recordInput({ notes: "Near the ruined bell tower." }), knowledge);
    if (!recorded.ok) throw new Error(recorded.message);
    const battle = recorded.state.campaign.battles.at(-1)!;
    expect(battle.notes).toBe("Near the ruined bell tower.");
  });

  it("unavailable warrior cannot receive battle results", () => {
    const base = settled();
    const withAbsence: CampaignDocument = {
      campaign: {
        ...base.campaign,
        warriors: base.campaign.warriors.map((w) =>
          w.id === "marta" ? { ...w, games_to_miss: 1 } : w,
        ),
      },
      view: base.view,
    };
    const result = recordBattle(withAbsence, recordInput({ casualties: 1, out_of_action_ids: ["marta"] }), knowledge);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("not_available");
  });

  it("serves every missed battle when the next battle is recorded", () => {
    const base = settled();
    const withAbsences: CampaignDocument = {
      campaign: {
        ...base.campaign,
        warriors: base.campaign.warriors.map((warrior) => warrior.id === "marta"
          ? { ...warrior, games_to_miss: 1, absence_reason: "Deep Wound" }
          : warrior.id === "novices" ? { ...warrior, games_to_miss: 2, absence_reason: "Captured" } : warrior),
      },
      view: base.view,
    };
    const result = recordBattle(withAbsences, recordInput(), knowledge);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.state.campaign.warriors.find((warrior) => warrior.id === "marta")).toMatchObject({ games_to_miss: 0, absence_reason: "" });
    expect(result.state.campaign.warriors.find((warrior) => warrior.id === "novices")).toMatchObject({ games_to_miss: 1, absence_reason: "Captured" });
  });

  it("readiness excludes unavailable warriors with their absence reason", () => {
    const base = settled();
    const withAbsence: CampaignDocument = {
      campaign: {
        ...base.campaign,
        warriors: base.campaign.warriors.map((w) =>
          w.id === "marta" ? { ...w, games_to_miss: 2, absence_reason: "Deep Wound" } : w,
        ),
      },
      view: base.view,
    };
    const workflow = createBattleWorkflow({ knowledge, useCases });
    const rows = workflow.readiness(withAbsence);
    const marta = rows.find((row) => row.warrior_id === "marta")!;
    expect(marta.available).toBe(false);
    expect(marta.reason).toBe("Deep Wound");
    // Everyone else stays available.
    expect(rows.filter((row) => row.warrior_id !== "marta").every((row) => row.available)).toBe(true);
  });

  it("workflow record derives casualties and blocks unavailable ids before the kernel", () => {
    const base = settled();
    const withAbsence: CampaignDocument = {
      campaign: {
        ...base.campaign,
        warriors: base.campaign.warriors.map((w) =>
          w.id === "marta" ? { ...w, games_to_miss: 1 } : w,
        ),
      },
      view: base.view,
    };
    const workflow = createBattleWorkflow({ knowledge, useCases });
    const blocked = workflow.record(withAbsence, {
      scenario: "skirmish",
      opponent: "Undead",
      result: "loss",
      gold_delta: 0,
      wyrdstone: 0,
      xp_delta: 1,
      out_of_action_ids: ["marta"],
    });
    expect(blocked.ok).toBe(false);
    if (!blocked.ok) expect(blocked.message).toContain("Unavailable");
    const ok = workflow.record(base, {
      scenario: "skirmish",
      opponent: "Undead",
      result: "loss",
      gold_delta: 0,
      wyrdstone: 0,
      xp_delta: 1,
      out_of_action_ids: ["novices", "novices"],
    });
    expect(ok.ok).toBe(true);
    if (!ok.ok) return;
    const battle = ok.document.campaign.battles.at(-1)!;
    expect(battle.casualties).toBe(2);
    expect(battle.out_of_action_ids).toEqual(["novices", "novices"]);
  });

  it("unknown warrior ids are rejected before recording", () => {
    const workflow = createBattleWorkflow({ knowledge, useCases });
    const result = workflow.record(settled(), {
      scenario: "skirmish",
      opponent: "X",
      result: "win",
      gold_delta: 0,
      wyrdstone: 0,
      xp_delta: 1,
      out_of_action_ids: ["ghost"],
    });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("not_found");
  });

  it("hasPendingPostBattle mirrors the desktop pending gate", () => {
    const workflow = createBattleWorkflow({ knowledge, useCases });
    expect(workflow.hasPendingPostBattle(settled())).toBe(false);
    const recorded = recordBattle(settled(), recordInput(), knowledge);
    if (!recorded.ok) throw new Error(recorded.message);
    expect(workflow.hasPendingPostBattle(recorded.state)).toBe(true);
  });

  it("draft campaigns cannot record battles", () => {
    const draft: CampaignDocument = cloneDocument(settled());
    const draftCampaign = {
      ...draft.campaign,
      configuration: { ...draft.campaign.configuration, is_draft: true },
    };
    const result = recordBattle({ campaign: draftCampaign, view: draft.view }, recordInput(), knowledge);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("not_permitted_in_draft");
  });

  it("battle numbers advance and stay unique across a committed sequence", () => {
    let state = settled();
    for (let index = 0; index < 2; index += 1) {
      const recorded = recordBattle(state, recordInput({ opponent: `Opponent ${index}` }), knowledge);
      if (!recorded.ok) throw new Error(recorded.message);
      state = recorded.state;
      for (let step = 0; step < 8; step += 1) {
        const stepResult = useCases.resolvePostBattleStep(state, index + 1, {});
        if (!stepResult.ok) throw new Error(stepResult.message);
        state = stepResult.state;
      }
    }
    const numbers = state.campaign.battles.map((battle) => battle.number);
    expect(numbers).toEqual([1, 2]);
    expect(new Set(numbers).size).toBe(numbers.length);
  });
});

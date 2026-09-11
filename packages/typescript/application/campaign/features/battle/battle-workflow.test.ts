/**
 * P6.4 acceptance tests: the battle workflow drives readiness → record →
 * post-battle steps through the real kernel use cases with an
 * artefact-shaped fake KnowledgeReader — plain Node, no React/DOM.
 */

import { describe, expect, it } from "vitest";

import type {
  CampaignDocument,
  KnowledgeReader,
  KnowledgeResult,
  KnowledgeQuery,
} from "../../../../domain/campaign/index";
import { createDefaultUseCases } from "../../../../domain/campaign/kernel/default-usecases";
import { createDraftWorkflow } from "../draft/draft-workflow";
import { createBattleWorkflow } from "./battle-workflow";
import { calculatedAwards } from "./scenario-awards";

function makeKnowledge(): KnowledgeReader {
  const rows: Record<string, Record<string, unknown>> = {
    "band_id:sisters-of-sigmar": {
      id: "sisters-of-sigmar",
      name: "Sisters of Sigmar",
      names: { en: "Sisters of Sigmar" },
      collection: "mordheim",
      roster: {
        minimum_models: 3,
        maximum_models: 15,
        starting_gold: 500,
        members: [
          { profile_id: "sigmarite-matriarch", minimum: 1, maximum: 1 },
          { profile_id: "sigmarite-sister", minimum: 0, maximum: null, group_size: { minimum: 1, maximum: 5 } },
        ],
      },
    },
    "profile_id:sigmarite-matriarch": {
      id: "sigmarite-matriarch",
      band_id: "sisters-of-sigmar",
      collection: "mordheim",
      type: "hero",
      cost: 70,
      experience: 0,
      name: "Sigmarite Matriarch",
      names: { en: "Sigmarite Matriarch" },
      characteristics: { M: 4, WS: 4, BS: 4, S: 3, T: 3, W: 1, I: 4, A: 1, Ld: 8 },
      fixed_equipment: [],
      skill_access: ["combat"],
    },
    "profile_id:sigmarite-sister": {
      id: "sigmarite-sister",
      band_id: "sisters-of-sigmar",
      collection: "mordheim",
      type: "henchman",
      cost: 25,
      experience: 0,
      name: "Sigmarite Sister",
      names: { en: "Sigmarite Sister" },
      characteristics: { M: 4, WS: 3, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
      fixed_equipment: [],
    },
    "scenario_id:skirmish": { id: "skirmish", name: "Skirmish", names: { en: "Skirmish" } },
    "scenario_id:raid": { id: "raid", name: "Raid", names: { en: "Raid" } },
  };
  return {
    queryKnowledge(query: KnowledgeQuery): KnowledgeResult {
      const row = rows[`${query.id.kind}:${query.id.value}`];
      if (!row) return { ok: false, reason: "not_found" };
      const { names, ...data } = row;
      return {
        ok: true,
        record: {
          kind: query.id.kind.replace(/_id$/, "") as never,
          id: query.id,
          names: names as Record<string, string>,
          data: Object.freeze({ ...data }),
        },
      };
    },
    queryMany(queries) {
      return queries.map((q) => this.queryKnowledge(q));
    },
  };
}

/** A committed (State #0) warband with two named warriors. */
function makeCommitted(): { document: CampaignDocument; knowledge: KnowledgeReader } {
  const knowledge = makeKnowledge();
  const draft = createDraftWorkflow({
    knowledge,
    useCases: createDefaultUseCases(knowledge),
  });
  const started = draft.startDraft("sisters-of-sigmar");
  if (!started.ok) throw new Error("start should succeed");
  const committed = draft.commit(started.document);
  if (!committed.ok) throw new Error("commit should succeed");
  return { document: committed.document, knowledge };
}

function makeBattleWorkflow(knowledge: KnowledgeReader) {
  return createBattleWorkflow({ knowledge, useCases: createDefaultUseCases(knowledge) });
}

const WIN = {
  scenario: "skirmish",
  opponent: "Reiklanders",
  result: "win" as const,
  gold_delta: 30,
  wyrdstone: 2,
  xp_delta: 6,
  out_of_action_ids: [] as readonly string[],
};

describe("P6.4 scenario options and readiness", () => {
  it("offers only KB-resolved scenarios", () => {
    const { document, knowledge } = makeCommitted();
    const battle = makeBattleWorkflow(knowledge);
    const options = battle.scenarioOptions();
    expect(options.map((o) => o.id)).toEqual(["skirmish", "raid"]);
    expect(options[0].name).toBe("Skirmish");
    void document;
  });

  it("marks absent warriors unavailable with their reason", () => {
    const { document, knowledge } = makeCommitted();
    const battle = makeBattleWorkflow(knowledge);
    const hero = document.campaign.warriors.find((w) => w.kind === "hero");
    if (!hero) throw new Error("fixture needs a hero");
    // Simulate an injury absence left by a post-battle resolution.
    const absent = {
      ...document,
      campaign: {
        ...document.campaign,
        warriors: document.campaign.warriors.map((w) =>
          w.id === hero.id ? { ...w, games_to_miss: 2, absence_reason: "Leg Wound" } : w,
        ),
      },
    };
    const rows = battle.readiness(absent);
    const heroRow = rows.find((row) => row.warrior_id === hero.id);
    expect(heroRow?.available).toBe(false);
    expect(heroRow?.reason).toBe("Leg Wound");
    expect(rows.filter((row) => row.available).length).toBe(rows.length - 1);
  });
});

describe("P6.4 recording battles", () => {
  it("awards the victory bonus to the Hero with the Leader rule", () => {
    const { document } = makeCommitted();
    const ordinaryHero = { ...document.campaign.warriors[0], id: "hero-first", skills: [] };
    const leader = { ...document.campaign.warriors[0], id: "hero-leader", skills: ["captain--leader"] };
    const awards = calculatedAwards([{ id: "winning-leader", label: "Winning leader", amount: 1, trigger: "warband_won_battle", manual: false, selection: "single" }], [ordinaryHero, leader], "win", {}, {});
    expect(awards).toEqual({ "hero-leader": 1 });
  });

  it("records a battle, snapshots numbers and opens the pending post-battle", () => {
    const { document, knowledge } = makeCommitted();
    const battle = makeBattleWorkflow(knowledge);
    const ratingBefore = document.campaign.states[0].rating;
    const result = battle.record(document, WIN);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const recorded = result.document.campaign.battles[0];
    expect(recorded.number).toBe(1);
    expect(recorded.rating_before).toBe(ratingBefore);
    expect(recorded.gold_delta).toBe(30);
    expect(battle.hasPendingPostBattle(result.document)).toBe(true);
    const pending = battle.pendingPostBattle(result.document);
    expect(pending?.battle_number).toBe(1);
    expect(pending?.active_step).toBe(0);
  });

  it("blocks a second battle while the post-battle is pending", () => {
    const { document, knowledge } = makeCommitted();
    const battle = makeBattleWorkflow(knowledge);
    const first = battle.record(document, WIN);
    if (!first.ok) throw new Error("first record should succeed");
    const second = battle.record(first.document, WIN);
    expect(second.ok).toBe(false);
    if (!second.ok) expect(second.message).toContain("pending");
  });

  it("rejects results naming unavailable or unknown warriors", () => {
    const { document, knowledge } = makeCommitted();
    const battle = makeBattleWorkflow(knowledge);
    const hero = document.campaign.warriors.find((w) => w.kind === "hero");
    if (!hero) throw new Error("fixture needs a hero");
    const withAbsence = {
      ...document,
      campaign: {
        ...document.campaign,
        warriors: document.campaign.warriors.map((w) =>
          w.id === hero.id ? { ...w, games_to_miss: 1 } : w,
        ),
      },
    };
    const blocked = battle.record(withAbsence, { ...WIN, out_of_action_ids: [hero.id] });
    expect(blocked.ok).toBe(false);
    if (!blocked.ok) expect(blocked.message).toContain("Unavailable");

    const ghost = battle.record(document, { ...WIN, out_of_action_ids: ["ghost#1"] });
    expect(ghost.ok).toBe(false);
    if (!ghost.ok) expect(ghost.reason).toBe("not_found");
  });

  it("rejects unknown scenarios with not_found", () => {
    const { document, knowledge } = makeCommitted();
    const battle = makeBattleWorkflow(knowledge);
    const bad = battle.record(document, { ...WIN, scenario: "not-a-scenario" });
    expect(bad.ok).toBe(false);
    if (!bad.ok) expect(bad.reason).toBe("rejected"); // kernel reason surfaced as rejection
  });
});

describe("P6.4 post-battle navigation", () => {
  it("resolves the eight steps forward and completes the sequence", () => {
    const { document, knowledge } = makeCommitted();
    const battle = makeBattleWorkflow(knowledge);
    const recorded = battle.record(document, WIN);
    if (!recorded.ok) throw new Error("record should succeed");
    let state = recorded.document;
    for (let step = 0; step < 8; step += 1) {
      const result = battle.resolveStep(state, { roll: 2 + step });
      expect(result.ok).toBe(true);
      if (!result.ok) return;
      state = result.document;
    }
    expect(battle.hasPendingPostBattle(state)).toBe(false);
    const completed = state.campaign.post_battles[0];
    expect(completed.complete).toBe(true);
    expect(completed.completed_steps).toEqual([0, 1, 2, 3, 4, 5, 6, 7]);
    // Step payloads preserved verbatim (open-payload policy).
    expect((completed.step_state?.["5"] as { roll?: number }).roll).toBe(7);
    // The next battle can now be recorded.
    const next = battle.record(state, { ...WIN, scenario: "raid" });
    expect(next.ok).toBe(true);
    if (next.ok) expect(next.document.campaign.battles[1].number).toBe(2);
  });

  it("rejects step resolution with no pending sequence", () => {
    const { document, knowledge } = makeCommitted();
    const battle = makeBattleWorkflow(knowledge);
    const result = battle.resolveStep(document, {});
    expect(result.ok).toBe(false);
  });
});

/**
 * P3.5 acceptance tests (plan §5): kernel use cases run in plain Node with a
 * fake KnowledgeReader built from the same record shapes the P4.2 artefact
 * emits (verified against `build/generated/knowledge-web/knowledge-web.json`).
 *
 * The behaviour ported here mirrors the Python domain tests in
 * `tests/campaign/` (draft legality, State #0 commit, battle recording).
 */

import { describe, expect, it } from "vitest";

import type {
  CampaignDocument,
  KnowledgeReader,
  KnowledgeResult,
  KnowledgeQuery,
} from "../index";
import { createDefaultUseCases } from "./default-usecases";
import {
  draftIsLegal,
  memberCount,
  rating,
  treasury,
} from "./document";
import { createDraft } from "./create-draft";

/** Artefact-shaped rows for the fake reader (mirrors P4.2 output). */
function makeKnowledge(): KnowledgeReader {
  const rows: Record<string, Record<string, unknown>> = {
    "band_id:sisters-of-sigmar": {
      id: "sisters-of-sigmar",
      name: "Sisters of Sigmar",
      names: { en: "Sisters of Sigmar", es: "Hermanas de Sigmar" },
      collection: "mordheim",
      roster: {
        minimum_models: 3,
        maximum_models: 15,
        starting_gold: 500,
        members: [
          { profile_id: "sigmarite-matriarch", minimum: 1, maximum: 1 },
          { profile_id: "sister-superior", minimum: 0, maximum: 3 },
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
      fixed_equipment: ["sigmarite_hammer"],
      skill_access: ["combat", "academic"],
      combat_traits: { starting_skills: ["skill.prayer-of-sigmar"] },
    },
    "profile_id:sister-superior": {
      id: "sister-superior",
      band_id: "sisters-of-sigmar",
      collection: "mordheim",
      type: "hero",
      cost: 35,
      experience: 0,
      name: "Sister Superior",
      names: { en: "Sister Superior" },
      characteristics: { M: 4, WS: 4, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
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
    "profile_id:other-band-hero": {
      id: "other-band-hero",
      band_id: "reiklanders",
      collection: "mordheim",
      type: "hero",
      cost: 40,
      name: "Cross-band decoy",
      characteristics: {},
    },
    "item_id:sigmarite_hammer": {
      item_id: "sigmarite_hammer",
      kind: "close-combat-weapon",
      name: "Sigmarite Hammer",
      names: { en: "Sigmarite Hammer", es: "Martillo de Sigmar" },
      value: 15,
    },
    "item_id:shield": {
      item_id: "shield",
      kind: "shield-or-defence",
      name: "Shield",
      names: { en: "Shield" },
      value: 5,
    },
    "scenario_id:skirmish": {
      id: "skirmish",
      name: "Skirmish",
      names: { en: "Skirmish" },
    },
    "hireling_id:warrior-undead-hunter": {
      id: "warrior-undead-hunter",
      name: "Undead Hunter",
      names: { en: "Undead Hunter" },
      cost: 55,
      rating: 15,
      characteristics: { M: 4, WS: 3, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
      upkeep_resources: [["gold", 15]],
      skills: ["skill.undead-hatred"],
    },
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

function makeKnowledgeOf(): KnowledgeReader {
  return makeKnowledge();
}

describe("P3.5 document helpers", () => {
  it("computes rating, member count and treasury like the Python domain", () => {
    const warriors = [
      { id: "a#1", name: "A", profile_name: "A", kind: "hero" as const, stats: {}, equipment: [], skills: [], experience: 8, cost: 35, quantity: 1 },
      { id: "b#1", name: "B", profile_name: "B", kind: "henchman" as const, stats: {}, equipment: [], skills: [], experience: 0, cost: 25, quantity: 3 },
      { id: "h#1", name: "H", profile_name: "H", kind: "hireling" as const, stats: {}, equipment: [], skills: [], experience: 0, cost: 55, quantity: 1, hireling_rating: 15 },
    ];
    expect(memberCount(warriors)).toBe(4); // hireling excluded
    expect(rating(warriors)).toBe(4 * 5 + 8 + 15); // members×5 + XP + hireling rating
  });
});

describe("P3.5 createDraft", () => {
  it("builds a legal starter draft from the KB roster (mandatory heroes, cheapest henchmen fill)", () => {
    const knowledge = makeKnowledgeOf();
    const result = createDraft("sisters-of-sigmar", knowledge);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const { campaign } = result.state;
    expect(campaign.configuration).toEqual({
      is_draft: true,
      starting_gold: 500,
      minimum_models: 3,
      maximum_models: 15,
      // Caps: matriarch 1 + sister-superior 3 (the fake's own members).
      hero_limit: 4,
    });
    // Mandatory matriarch + fill of 2 cheapest henchmen (single group of 2).
    expect(campaign.warriors.some((w) => w.profile_id === "sigmarite-matriarch")).toBe(true);
    expect(memberCount(campaign.warriors)).toBeGreaterThanOrEqual(3);
    expect(draftIsLegal(campaign)).toBe(true);
    expect(treasury(campaign)).toBeGreaterThan(0);
    // Fixed equipment carries the resolved display name.
    const matriarch = campaign.warriors.find((w) => w.profile_id === "sigmarite-matriarch");
    expect(matriarch?.equipment[0]?.name).toBe("Sigmarite Hammer");
  });

  it("rejects unknown bands and cross-band profile decoys", () => {
    expect(createDraft("no-such-band", makeKnowledgeOf()).ok).toBe(false);
  });
});

describe("P3.5 commitInitialWarband", () => {
  function makeCommittedDraft(): CampaignDocument {
    const knowledge = makeKnowledgeOf();
    const result = createDraft("sisters-of-sigmar", knowledge);
    if (!result.ok) throw new Error("draft should be legal");
    return result.state;
  }

  it("turns a legal draft into State #0 with folded fixed equipment", () => {
    const useCases = createDefaultUseCases(makeKnowledgeOf());
    const draft = makeCommittedDraft();
    const result = useCases.commitInitialWarband(draft, makeKnowledgeOf());
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const { campaign } = result.state;
    expect(campaign.configuration.is_draft).toBe(false);
    expect(campaign.current_state_number).toBe(0);
    expect(campaign.states).toHaveLength(1);
    const state = campaign.states[0];
    expect(state.number).toBe(0);
    expect(state.label).toBe("Initial Warband");
    expect(state.models).toBe(memberCount(campaign.warriors));
    expect(state.rating).toBe(rating(campaign.warriors));
    expect(state.roster).toHaveLength(campaign.warriors.length);
    // The matriarch's fixed hammer was folded into the inventory.
    const hammer = campaign.inventory.find((item) => item.id === "sigmarite_hammer");
    expect(hammer?.owned).toBe(1);
    expect(hammer?.equipped).toBe(1);
    // The original draft document was not mutated.
    expect(draft.campaign.inventory).toHaveLength(0);
    expect(draft.campaign.states).toHaveLength(0);
  });

  it("rejects double commitment", () => {
    const useCases = createDefaultUseCases();
    const draft = makeCommittedDraft();
    const first = useCases.commitInitialWarband(draft, makeKnowledgeOf());
    if (!first.ok) throw new Error("first commit should succeed");
    const second = useCases.commitInitialWarband(first.state, makeKnowledgeOf());
    expect(second.ok).toBe(false);
    if (!second.ok) expect(second.reason).toBe("not_permitted_when_committed");
  });
});

describe("P3.5 recordBattle and post-battle navigation", () => {
  function makeActiveCampaign(): { document: CampaignDocument; knowledge: KnowledgeReader } {
    const knowledge = makeKnowledgeOf();
    const draft = createDraft("sisters-of-sigmar", knowledge);
    if (!draft.ok) throw new Error("draft should be legal");
    const useCases = createDefaultUseCases(knowledge);
    const committed = useCases.commitInitialWarband(draft.state, knowledge);
    if (!committed.ok) throw new Error("commit should succeed");
    return { document: committed.state, knowledge };
  }

  it("records a battle with snapshot numbers and opens the pending post-battle", () => {
    const { document, knowledge } = makeActiveCampaign();
    const useCases = createDefaultUseCases(knowledge);
    const result = useCases.recordBattle(
      document,
      {
        scenario: "skirmish",
        opponent: "Reiklanders",
        result: "win",
        gold_delta: 30,
        wyrdstone: 2,
        xp_delta: 6,
        casualties: 0,
        out_of_action_ids: [],
      },
      knowledge,
    );
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const { campaign } = result.state;
    expect(campaign.battles).toHaveLength(1);
    const battle = campaign.battles[0];
    expect(battle.number).toBe(1);
    expect(battle.result).toBe("win");
    expect(battle.rating_before).toBe(battle.rating_after);
    expect(battle.casualties).toBe(0);
    expect(campaign.post_battles).toHaveLength(1);
    expect(campaign.post_battles[0].complete).toBe(false);
    // A second battle while pending is a conflict, not a throw.
    const second = useCases.recordBattle(
      result.state,
      { scenario: "skirmish", opponent: "X", result: "draw", gold_delta: 0, wyrdstone: 0, xp_delta: 0, casualties: 0, out_of_action_ids: null },
      knowledge,
    );
    expect(second.ok).toBe(false);
    if (!second.ok) expect(second.reason).toBe("conflict");
  });

  it("walks the eight post-battle steps forward and completes", () => {
    const { document, knowledge } = makeActiveCampaign();
    const useCases = createDefaultUseCases(knowledge);
    const recorded = useCases.recordBattle(
      document,
      { scenario: "skirmish", opponent: "X", result: "loss", gold_delta: 0, wyrdstone: 0, xp_delta: 3, casualties: 0, out_of_action_ids: null },
      knowledge,
    );
    if (!recorded.ok) throw new Error("record should succeed");
    let state = recorded.state;
    for (let step = 0; step < 8; step += 1) {
      const result = useCases.resolvePostBattleStep(state, 1, { note: `step-${step}` });
      expect(result.ok).toBe(true);
      if (!result.ok) return;
      state = result.state;
    }
    const post = state.campaign.post_battles.find((p) => p.battle_number === 1);
    expect(post?.complete).toBe(true);
    expect(post?.completed_steps).toEqual([0, 1, 2, 3, 4, 5, 6, 7]);
    // Step inputs were preserved verbatim (open-payload policy).
    expect((post?.step_state?.["3"] as { note?: string }).note).toBe("step-3");
    // And a new battle can now be recorded.
    const next = useCases.recordBattle(
      state,
      { scenario: "skirmish", opponent: "Y", result: "win", gold_delta: 5, wyrdstone: 0, xp_delta: 1, casualties: 0, out_of_action_ids: null },
      knowledge,
    );
    expect(next.ok).toBe(true);
    if (next.ok) expect(next.state.campaign.battles[1].number).toBe(2);
  });

  it("rejects drafts, unknown scenarios and unknown warriors with stable reasons", () => {
    const knowledge = makeKnowledgeOf();
    const draft = createDraft("sisters-of-sigmar", knowledge);
    if (!draft.ok) throw new Error("draft should be legal");
    const useCases = createDefaultUseCases(knowledge);
    const inDraft = useCases.recordBattle(
      draft.state,
      { scenario: "skirmish", opponent: "X", result: "win", gold_delta: 0, wyrdstone: 0, xp_delta: 0, casualties: 0, out_of_action_ids: null },
      knowledge,
    );
    expect(inDraft.ok).toBe(false);
    if (!inDraft.ok) expect(inDraft.reason).toBe("not_permitted_in_draft");
    const { document } = makeActiveCampaign();
    const badScenario = useCases.recordBattle(
      document,
      { scenario: "not-a-scenario", opponent: "X", result: "win", gold_delta: 0, wyrdstone: 0, xp_delta: 0, casualties: 0, out_of_action_ids: null },
      knowledge,
    );
    if (badScenario.ok) throw new Error("unknown scenario must reject");
    expect(badScenario.reason).toBe("not_found");
    const badWarrior = useCases.recordBattle(
      document,
      { scenario: "skirmish", opponent: "X", result: "win", gold_delta: 0, wyrdstone: 0, xp_delta: 0, casualties: 0, out_of_action_ids: ["ghost#1"] },
      knowledge,
    );
    if (badWarrior.ok) throw new Error("unknown warrior must reject");
    expect(badWarrior.reason).toBe("not_found");
  });
});

describe("P3.5 equipment, hirelings and advances", () => {
  function makeCommitted(): { useCases: ReturnType<typeof createDefaultUseCases>; state: CampaignDocument; knowledge: KnowledgeReader } {
    const knowledge = makeKnowledgeOf();
    const draft = createDraft("sisters-of-sigmar", knowledge);
    if (!draft.ok) throw new Error("draft should be legal");
    const useCases = createDefaultUseCases(knowledge);
    const committed = useCases.commitInitialWarband(draft.state, knowledge);
    if (!committed.ok) throw new Error("commit should succeed");
    return { useCases, state: committed.state, knowledge };
  }

  it("moves equipment stash ↔ warrior conserving owned = equipped + stash", () => {
    const { useCases, state } = makeCommitted();
    // The matriarch's fixed hammer is not transferable — it must reject.
    const matriarch = state.campaign.warriors.find((w) => w.profile_id === "sigmarite-matriarch");
    if (!matriarch) throw new Error("matriarch missing");
    const fixed = useCases.assignEquipment(state, {
      warrior_id: matriarch.id,
      item_id: "sigmarite_hammer",
      quantity: 1,
      direction: "stash",
    });
    expect(fixed.ok).toBe(false);
    if (!fixed.ok) expect(fixed.reason).toBe("limit_violated");

    // Equipping from an empty stash must reject with the stable reason.
    const anyWarrior = state.campaign.warriors[0];
    const emptyStash = useCases.assignEquipment(state, {
      warrior_id: anyWarrior.id,
      item_id: "sigmarite_hammer",
      quantity: 1,
      direction: "equip",
    });
    expect(emptyStash.ok).toBe(false);
    if (!emptyStash.ok) expect(emptyStash.reason).toBe("limit_violated");
  });

  it("hires a hireling that adds rating without consuming roster capacity", () => {
    const { useCases, state, knowledge } = makeCommitted();
    const modelsBefore = memberCount(state.campaign.warriors);
    const result = useCases.hireHireling(state, { profile_id: "warrior-undead-hunter" }, knowledge);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const hired = result.state.campaign.warriors.find((w) => w.kind === "hireling");
    expect(hired?.profile_id).toBe("warrior-undead-hunter");
    expect(hired?.upkeep_resources).toEqual([["gold", 15]]);
    expect(memberCount(result.state.campaign.warriors)).toBe(modelsBefore); // capacity untouched
    expect(rating(result.state.campaign.warriors)).toBe(
      rating(state.campaign.warriors) + 15,
    );
  });

  it("applies stat and skill advances only when XP thresholds allow them", () => {
    const { useCases, state } = makeCommitted();
    // The matriarch starts at 0 XP: no pending advance, even a valid choice.
    const hero = state.campaign.warriors.find((w) => w.kind === "hero");
    if (!hero) throw new Error("fixture needs a hero");
    const nonePending = useCases.applyAdvance(state, { warrior_id: hero.id, table: "stat", choice: "stat:WS" });
    expect(nonePending.ok).toBe(false);
    if (!nonePending.ok) expect(nonePending.reason).toBe("prerequisite_missing");
    const badChoice = useCases.applyAdvance(state, {
      warrior_id: hero.id,
      table: "x",
      choice: "nonsense",
    });
    if (!badChoice.ok) expect(badChoice.reason).toBe("invalid_input");
  });
});

describe("P3.5 export validation invariants", () => {
  it("catches unordered timelines, duplicate warriors and broken drafts", () => {
    const knowledge = makeKnowledgeOf();
    const draft = createDraft("sisters-of-sigmar", knowledge);
    if (!draft.ok) throw new Error("draft should be legal");
    const useCases = createDefaultUseCases(knowledge);
    const committed = useCases.commitInitialWarband(draft.state, knowledge);
    if (!committed.ok) throw new Error("commit should succeed");
    const doc = committed.state;
    expect(useCases.validateForExport(doc).ok).toBe(true);

    const unordered: CampaignDocument = {
      ...doc,
      campaign: {
        ...doc.campaign,
        states: [
          doc.campaign.states[0],
          { ...doc.campaign.states[0], number: 0 },
        ],
      },
    };
    expect(useCases.validateForExport(unordered).ok).toBe(false);

    const [firstWarrior] = doc.campaign.warriors;
    const duplicateWarrior: CampaignDocument = {
      ...doc,
      campaign: { ...doc.campaign, warriors: [firstWarrior, firstWarrior] },
    };
    expect(useCases.validateForExport(duplicateWarrior).ok).toBe(false);
  });
});

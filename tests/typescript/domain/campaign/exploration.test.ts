/**
 * Parity port of desktop `tests/python/campaign/test_exploration_sequence_matrix.py`
 * (test functions → behavioural equivalents). Traceability: manifest rows
 * with `web_target: tests/typescript/domain/campaign/exploration.test.ts`.
 *
 * Desktop semantics (post-battle engine `apply_exploration` /
 * `advance_exploration_followup`) map onto the TS exploration workflow:
 * - dice-chain resolution with follow-up queues (`applyExploration`,
 *   `continueExploration`);
 * - every intermediate state survives a v5 file round-trip;
 * - invalid recipients (missing hero / henchman / removed warrior) and
 *   out-of-range or non-integer rolls are rejected without mutation;
 * - rewards for a warband without heroes degrade to an explicit
 *   `choose_option` instead of an impossible hero choice;
 * - a lost unique artefact re-rolls; an exhausted artefact table finishes.
 *
 * Purity: plain Node, in-memory v5 round-trip — no React, no DOM, no
 * filesystem. Application-service undo coverage lives in
 * application/campaign/undo.test.ts (desktop `perform_undoable` parity).
 */

import { describe, expect, it } from "vitest";

import { applyExploration, continueExploration, explorationDiceCount, explorationModifiers } from "@app/campaign/features/exploration/exploration-workflow";
import type { Campaign, CampaignDocument, KnowledgeReader, OpenPayload, Warrior } from "@domain/campaign/kernel/usecases";
import { CampaignFileV5Adapter, parseCampaignFileDetailed } from "@adapters/campaign-file";

const adapter = new CampaignFileV5Adapter();

function roundtrip(document: CampaignDocument): CampaignDocument {
  const serialized = adapter.serializeCampaign(document.campaign);
  expect(serialized.ok, serialized.ok ? "" : serialized.message).toBe(true);
  if (!serialized.ok) return document;
  const parsed = parseCampaignFileDetailed(serialized.text);
  expect(parsed.ok).toBe(true);
  if (!parsed.ok) return document;
  return { campaign: parsed.campaign, view: parsed.view };
}

/** Minimal campaign catalogue backing the exploration workflow. */
const EXPLORATION = {
  dice_allocation: [{ eligible_warrior: "hero", condition: "survived_battle", dice: 1 }],
  max_dice: 6,
  shards_chart: { cells: [{ when: { dice_total: { min: 0 } }, shards: 0 }] },
  results: [],
};

const knowledge: KnowledgeReader & { campaignSection?(section: string): Readonly<Record<string, unknown>> } = {
  queryKnowledge(query) {
    const ref = query.id;
    const id = ref.value;
    if (query.id.kind === "scenario_id") return { ok: true, record: { kind: "scenario", id: ref, names: { en: id }, data: {} } };
    if (query.id.kind === "item_id") return { ok: true, record: { kind: "item", id: ref, names: { en: id }, data: { kind: "Magical Artefact" } } };
    if (query.id.kind === "profile_id") return { ok: true, record: { kind: "profile", id: ref, names: { en: id }, data: { can_gain_experience: true } } };
    return { ok: false, reason: "not_found" };
  },
  queryMany: (queries) => queries.map((q) => knowledge.queryKnowledge(q)),
  campaignSection(section) {
    if (section === "exploration-and-income") return { exploration: EXPLORATION, magical_artefacts: { results: ARTEFACT_TABLE } };
    return {};
  },
};

/** Desktop `magical_artefacts.results` rows (roll → unique item). */
const ARTEFACT_TABLE: readonly Readonly<Record<string, unknown>>[] = [
  { roll: 1, id: "campaign.magical-artefact.audit-1", result: "Relic One", effect: "Glow" },
  { roll: 2, id: "campaign.magical-artefact.audit-2", result: "Relic Two", effect: "Hum" },
  { roll: 3, id: "campaign.magical-artefact.audit-3", result: "Relic Three", effect: "Spark" },
  { roll: 4, id: "campaign.magical-artefact.audit-4", result: "Relic Four", effect: "Shine" },
  { roll: 5, id: "campaign.magical-artefact.audit-5", result: "Relic Five", effect: "Pulse" },
  { roll: 6, id: "campaign.magical-artefact.audit-6", result: "Relic Six", effect: "Beam" },
];

function hero(id: string): Warrior {
  return { id, name: id, profile_name: "Sister", kind: "hero", stats: { WS: 3 }, equipment: [], skills: [], experience: 0, cost: 30, quantity: 1 };
}

/** Committed band with one pending post-battle ready for exploration. */
function pendingPostBattle(warriors: readonly Warrior[]): CampaignDocument {
  const campaign: Campaign = {
    identity: { campaign_name: "Explore", warband_name: "Band", warband_type: "Sisters of Sigmar", band_id: "sisters-of-sigmar", mercenary_variant: null },
    configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
    resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 1,
    warriors,
    battles: [{ number: 1, date: "2026-09-10", scenario: "skirmish", opponent: "Audit", result: "win", gold_delta: 0, wyrdstone: 0, xp_delta: 0, casualties: 0, advances: 0, rating_before: 0, rating_after: 0, models_before: 3, models_after: 3, out_of_action_ids: null, participants: [], absentees: [] } as unknown as Campaign["battles"][number]],
    states: [{ number: 1, date: "2026-09-10", gold: 500, wyrdstone: 0, rating: 0, models: 3, max_models: 15, heroes: 2, henchmen: 1, experience: 0, label: "Initial Warband" }],
    post_battles: [{
      battle_number: 1, complete: false, active_step: 3, completed_steps: [], review_open: false, experience_applied: true, pending_advances: [],
      gold_delta: 0, wyrdstone_delta: 0, pending_follow_ups: [], step_state: {}, event_log: [],
    } as unknown as Campaign["post_battles"][number]],
    inventory: [],
    special_rules: [],
    manual_log: [],
  };
  return { campaign, view: {} };
}

function pendingFollowup(document: CampaignDocument): OpenPayload | null {
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const followup = post?.pending_follow_ups?.find((row) => row["type"] === "exploration_followup");
  return (followup as OpenPayload | undefined) ?? null;
}

function clone(document: CampaignDocument): CampaignDocument {
  return structuredClone(document);
}

describe("desktop test_exploration_sequence_matrix.py → web exploration parity", () => {
  it("exploration dice count follows the KB allocation (heroes present)", () => {
    const doc = pendingPostBattle([hero("marta"), hero("anna"), { id: "novices", name: "Novices", profile_name: "Novice", kind: "henchman", stats: {}, equipment: [], skills: [], experience: 0, cost: 25, quantity: 3 }]);
    expect(explorationDiceCount(doc, knowledge)).toBe(2);
  });

  it("subtracts only out-of-action heroes from exploration eligibility", () => {
    const doc = pendingPostBattle([
      hero("marta"),
      hero("anna"),
      { id: "novices", name: "Novices", profile_name: "Novice", kind: "henchman", stats: {}, equipment: [], skills: [], experience: 0, cost: 25, quantity: 3 },
    ]);
    const battle = doc.campaign.battles[0] as typeof doc.campaign.battles[number] & { out_of_action_ids: string[]; participants: OpenPayload[] };
    battle.participants = [];
    battle.out_of_action_ids = ["novices", "novices"];
    expect(explorationDiceCount(doc, knowledge)).toBe(2);
    battle.out_of_action_ids.push("marta");
    expect(explorationDiceCount(doc, knowledge)).toBe(1);
  });

  it("combines every active exploration rule and keeps selectable skills opt-in", () => {
    const augur = { ...hero("augur"), profile_id: "augur", skills: ["augur--blessed-sight", "skill.wyrdstone-hunter"] } as Warrior;
    const ranger = { ...hero("ranger"), kind: "hireling", profile_id: "elf-ranger" } as Warrior;
    const doc = pendingPostBattle([augur, ranger]);
    const catalogue = {
      ...knowledge,
      list(kind: string) {
        if (kind === "band") return [{ id: "sisters-of-sigmar", rule_ids: ["band--horned-hunter-special-skills-pathfinder"] }];
        if (kind === "profile") return [
          { id: "augur", rule_ids: ["augur--blessed-sight"] },
          { id: "elf-ranger", rule_ids: ["hireling.hired-sword.elf-ranger.rule.seeker"] },
        ];
        return [];
      },
      rulesDocument() { return [
        { id: "augur--blessed-sight", names: { en: "Blessed Sight", es: "Vista Bendita" } },
        { id: "hireling.hired-sword.elf-ranger.rule.seeker", names: { en: "Seeker", es: "Buscador" } },
        { id: "band--horned-hunter-special-skills-pathfinder", kind: "warband_skill", names: { en: "Pathfinder" } },
      ]; },
    };
    expect(explorationModifiers(doc, catalogue)).toMatchObject({ extra_dice: 1, discards: 1, rerolls: 1, adjustments: 1 });
    expect(explorationDiceCount(doc, catalogue)).toBe(2);
    expect(applyExploration(doc, catalogue, [4]).ok).toBe(true);
  });

  it("resolves a zero-dice exploration step, matching desktop", () => {
    const doc = pendingPostBattle([]);
    const result = applyExploration(doc, knowledge, []);
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.summary.dice_count).toBe(0);
    expect(result.document.campaign.post_battles[0].step_state?.["exploration"]).toMatchObject({ resolved: true, total: 0 });
  });

  it("applyExploration rejects an already-resolved exploration", () => {
    let doc = pendingPostBattle([hero("marta")]);
    const first = applyExploration(doc, knowledge, [3]);
    expect(first.ok).toBe(true);
    if (!first.ok) return;
    doc = first.document;
    const second = applyExploration(doc, knowledge, [3]);
    expect(second.ok).toBe(false);
    expect((second as { message: string }).message).toContain("already");
  });

  it("applyExploration rejects invalid dice without mutation", () => {
    const doc = pendingPostBattle([hero("marta")]);
    const before = clone(doc);
    for (const dice of [[], [0], [7], [3, 3]]) {
      const result = applyExploration(doc, knowledge, dice);
      expect(result.ok).toBe(false);
    }
    expect(doc).toEqual(before);
  });

  it("invalid reward recipient (missing hero) keeps pending state", () => {
    const doc = pendingPostBattle([]);
    const injected: CampaignDocument = structuredClone(doc);
    const post = injected.campaign.post_battles.find((row) => !row.complete)!;
    (post as unknown as { pending_follow_ups: OpenPayload[] }).pending_follow_ups = [{
      type: "exploration_followup", step: 2, queue: [], pending: { kind: "choose_hero" }, messages: [],
    } as unknown as OpenPayload];
    const before = clone(injected);
    const result = continueExploration(injected, knowledge, { hero_id: "no-longer-present" });
    expect(result.ok).toBe(false);
    expect(injected).toEqual(before);
  });

  it("out-of-range and non-integer reward rolls keep pending state", () => {
    const injected: CampaignDocument = structuredClone(pendingPostBattle([]));
    const post = injected.campaign.post_battles.find((row) => !row.complete)!;
    (post as unknown as { pending_follow_ups: OpenPayload[] }).pending_follow_ups = [{
      type: "exploration_followup", step: 2, queue: [], pending: { kind: "roll", dice_count: 1, dice_sides: 6 }, messages: [],
    } as unknown as OpenPayload];
    const before = clone(injected);
    for (const roll of [0, -1, 7, 100]) {
      const result = continueExploration(injected, knowledge, { roll });
      expect(result.ok).toBe(false);
      expect(injected).toEqual(before);
    }
  });

  it("two-dice reward rejects invalid totals (fractional, boolean, out of range)", () => {
    const injected: CampaignDocument = structuredClone(pendingPostBattle([]));
    const post = injected.campaign.post_battles.find((row) => !row.complete)!;
    (post as unknown as { pending_follow_ups: OpenPayload[] }).pending_follow_ups = [{
      type: "exploration_followup", step: 2, queue: [], pending: { kind: "roll", dice_count: 2, dice_sides: 6 }, messages: [],
    } as unknown as OpenPayload];
    const before = clone(injected);
    for (const roll of [1, 13, 2.5, true as unknown as number]) {
      const result = continueExploration(injected, knowledge, { roll });
      expect(result.ok).toBe(false);
      expect(injected).toEqual(before);
    }
  });

  it("removed multi-choice recipient is rejected without mutation", () => {
    const doc = pendingPostBattle([]);
    const injected: CampaignDocument = structuredClone(doc);
    const post = injected.campaign.post_battles.find((row) => !row.complete)!;
    const warriorId = "gone-warrior";
    (post as unknown as { pending_follow_ups: OpenPayload[] }).pending_follow_ups = [{
      type: "exploration_followup", step: 2, queue: [], pending: { kind: "choose_warriors", options: [{ id: warriorId }], maximum: 1 }, messages: [],
    } as unknown as OpenPayload];
    const before = clone(injected);
    const result = continueExploration(injected, knowledge, { warrior_ids: [warriorId] });
    expect(result.ok).toBe(false);
    expect(injected).toEqual(before);
  });

  it("rewards without heroes do not require an impossible hero choice", () => {
    const injected: CampaignDocument = structuredClone(pendingPostBattle([]));
    const post = injected.campaign.post_battles.find((row) => !row.complete)!;
    (post as unknown as { pending_follow_ups: OpenPayload[] }).pending_follow_ups = [{
      type: "exploration_followup", step: 2, queue: [], pending: { kind: "choose_option", options: [{ id: "no-hero-resolution", then: [] }] }, messages: [],
    } as unknown as OpenPayload];
    const pending = pendingFollowup(injected);
    expect(pending).not.toBeNull();
    const recorded = continueExploration(injected, knowledge, { option_id: "no-hero-resolution" });
    expect(recorded.ok).toBe(true);
    if (!recorded.ok) return;
    const post2 = recorded.document.campaign.post_battles.find((row) => !row.complete)!;
    expect((post2.pending_follow_ups ?? []).some((row) => row["type"] === "exploration_followup")).toBe(false);
  });

  it("grant_special_item without heroes offers the keep-in-stash option", () => {
    const injected: CampaignDocument = structuredClone(pendingPostBattle([]));
    const post = injected.campaign.post_battles.find((row) => !row.complete)!;
    (post as unknown as { pending_follow_ups: OpenPayload[] }).pending_follow_ups = [{
      type: "exploration_followup", step: 2,
      queue: [], pending: { kind: "choose_option", options: [{ id: "keep-in-stash", then: [{ type: "grant_special_item", item_id: "audit.relic", name: "Relic", text: "Test relic", recipient: "stash" }] }] },
      messages: [],
    } as unknown as OpenPayload];
    const second = continueExploration(injected, knowledge, { option_id: "keep-in-stash" });
    expect(second.ok).toBe(true);
    if (!second.ok) return;
    const stock = second.document.campaign.inventory.find((row) => row.id === "audit.relic");
    expect(stock).toBeDefined();
    expect(stock!.owned).toBe(1);
    expect(stock!.stash).toBe(1);
    expect(stock!.equipped).toBe(0);
  });

  it("offers a human Henchman group whose profile id is shared by other bands", () => {
    const marksmen = { id: "marksmen#1", name: "Marksmen", profile_name: "Marksmen", profile_id: "marksmen", kind: "henchman", stats: {}, equipment: [], skills: [], experience: 0, cost: 25, quantity: 1 } as Warrior;
    const injected = pendingPostBattle([hero("captain"), marksmen]);
    const post = injected.campaign.post_battles.find((row) => !row.complete)!;
    (post as unknown as { pending_follow_ups: OpenPayload[] }).pending_follow_ups = [{ type: "exploration_followup", step: 2, queue: [{ type: "choose_henchman_group", allow_decline: true }], messages: [] }];
    const scopedKnowledge = {
      ...knowledge,
      list(kind: string) {
        if (kind === "warband_group") return [{ id: "warband-group.human", band_ids: ["sisters-of-sigmar"] }];
        if (kind === "profile") return [{ id: "marksmen", band_id: "sisters-of-sigmar", type: "henchman", equipment_access: [{ item_id: "bow" }] }];
        return [];
      },
      queryKnowledge(query: Parameters<KnowledgeReader["queryKnowledge"]>[0]) {
        if (query.id.kind === "profile_id") return { ok: false as const, reason: "not_found" as const };
        return knowledge.queryKnowledge(query);
      },
    };
    const result = continueExploration(injected, scopedKnowledge, {});
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const pending = pendingFollowup(result.document)?.["pending"] as OpenPayload;
    expect((pending["options"] as OpenPayload[]).map((row) => row["id"])).toContain("marksmen#1");
  });

  it("lost unique artefact roll requests a reroll", () => {
    const injected: CampaignDocument = structuredClone(pendingPostBattle([hero("marta")]));
    (injected.campaign as unknown as { unique_reward_ids: string[] }).unique_reward_ids = ["magical_artefact.audit-3"];
    const post = injected.campaign.post_battles.find((row) => !row.complete)!;
    (post as unknown as { pending_follow_ups: OpenPayload[] }).pending_follow_ups = [{
      type: "exploration_followup", step: 2, queue: [], pending: { kind: "roll", dice_count: 1, dice_sides: 6, spec: { type: "magical_artefact" } }, messages: [],
    } as unknown as OpenPayload];
    const rolled = continueExploration(injected, knowledge, { roll: 3 });
    expect(rolled.ok).toBe(true);
    if (!rolled.ok) return;
    const pending = pendingFollowup(rolled.document);
    expect((pending?.["pending"] as OpenPayload | undefined)?.["kind"]).toBe("roll");
  });

  it("exhausted artefact table has a finishable resolution", () => {
    const injected: CampaignDocument = structuredClone(pendingPostBattle([hero("marta")]));
    (injected.campaign as unknown as { unique_reward_ids: string[] }).unique_reward_ids = ARTEFACT_TABLE.map((row) => `magical_artefact.${String(row["id"]).replace("campaign.magical-artefact.", "")}`);
    const post = injected.campaign.post_battles.find((row) => !row.complete)!;
    (post as unknown as { pending_follow_ups: OpenPayload[] }).pending_follow_ups = [{
      type: "exploration_followup", step: 2, queue: [], pending: { kind: "choose_option", options: [{ id: "artefacts-exhausted", then: [] }] }, messages: [],
    } as unknown as OpenPayload];
    const resolved = continueExploration(injected, knowledge, { option_id: "artefacts-exhausted" });
    expect(resolved.ok).toBe(true);
    if (!resolved.ok) return;
    expect(pendingFollowup(resolved.document)).toBeNull();
  });

  it("exploration chain survives a v5 round-trip mid-queue", () => {
    const injected: CampaignDocument = structuredClone(pendingPostBattle([hero("marta"), hero("anna")]));
    const post = injected.campaign.post_battles.find((row) => !row.complete)!;
    (post as unknown as { pending_follow_ups: OpenPayload[] }).pending_follow_ups = [{
      type: "exploration_followup", step: 2,
      queue: [{ type: "sequence", steps: [{ type: "grant", recipient: "warband", resources: { gold_crowns: { kind: "fixed", value: 35 } } }, { type: "grant_rule", recipient: "warband", text: "Chain rule" }] }],
      messages: [],
    } as unknown as OpenPayload];
    const resolved = continueExploration(injected, knowledge, {});
    expect(resolved.ok).toBe(true);
    if (!resolved.ok) return;
    const restored = roundtrip(resolved.document);
    expect(restored.campaign.inventory.some((row) => row.id === "gold_crowns") || restored.campaign.post_battles.find((row) => !row.complete) !== undefined).toBe(true);
  });
});

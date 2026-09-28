/**
 * T10 — campaign mutations.
 *
 * The published case is `shallows-beasts-mim / band--aquatic-mutants`: "Any Hero
 * may start the campaign with a single mutation ... if they pay the appropriate
 * cost". The catalogue lists the ids it prices; the grant rule names the ids the
 * band may buy and, separately, the printed names the catalogue does not carry.
 * The transaction buys at the listed price (doubled for a second mutation) while
 * the member is recruited, and persists the purchase.
 */
import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { CampaignFileV5Adapter, parseCampaignFileDetailed } from "@adapters/campaign-file";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import {
  availableMutations,
  buyMutation,
  mutationCatalogue,
  mutationGrantRulesOf,
  mutationPrice,
  mutationsOf,
  recruitedDuringPost,
} from "@domain/campaign/kernel/mutations";
import type { Campaign, CampaignDocument, Warrior } from "@domain/campaign/kernel/usecases";

const REPO_ROOT = join(import.meta.dirname, "..", "..", "..", "..");
const OVERRIDE = process.env.MORDHEIM_KNOWLEDGE_ARTEFACT;
const CANDIDATES = OVERRIDE
  ? [OVERRIDE]
  : [
      join(REPO_ROOT, "build", "generated", "knowledge-web", "knowledge-web.json"),
      join(REPO_ROOT, "outputs", "web-public", "knowledge", "knowledge-web.json"),
    ];
const ARTEFACT_PATH = CANDIDATES.find((path) => existsSync(path));
const adapter = new CampaignFileV5Adapter();

const BAND = "shallows-beasts-mim";
const BLACKBLOOD = "campaign.mutation.blackblood";
const TENTACLE = "campaign.mutation.tentacle";

function warrior(id: string, profileId: string, kind: Warrior["kind"] = "hero"): Warrior {
  return { id, name: `${profileId} ${id}`, profile_name: profileId, kind, stats: {}, equipment: [], skills: [], experience: 0, cost: 0, quantity: 1, profile_id: profileId };
}

function campaign(warriors: readonly Warrior[], isDraft: boolean, postBattles: readonly Record<string, unknown>[] = []): Campaign {
  return {
    identity: { campaign_name: "Mutations", warband_name: "Reavers", warband_type: "Reavers", band_id: BAND, mercenary_variant: null },
    configuration: { is_draft: isDraft, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
    resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: isDraft ? 0 : 1,
    warriors,
    battles: [],
    states: isDraft ? [] : [{ number: 1, date: "2026-09-28", gold: 500, wyrdstone: 0, rating: 0, models: 1, max_models: 15, heroes: 1, henchmen: 0, experience: 0 }],
    post_battles: postBattles,
    inventory: [],
    special_rules: [],
    manual_log: [],
  };
}

function draft(warriors: readonly Warrior[]): CampaignDocument {
  return { campaign: campaign(warriors, true), view: { selected_moment: "draft:0" } };
}

describe.skipIf(!ARTEFACT_PATH)("T10 mutations (generated artefact)", () => {
  const artefact = JSON.parse(readFileSync(ARTEFACT_PATH as string, "utf8"));
  const reader = ArtefactKnowledgeReader.from(artefact);

  it("publishes the priced ids the printed grant lists and the names it does not", () => {
    const rules = mutationGrantRulesOf(reader, BAND);
    expect(rules).toHaveLength(1);
    const rule = rules[0]!;
    expect(rule.rule_id).toBe("band--aquatic-mutants");
    expect(rule.recipients).toBe("hero");
    expect(rule.limit_per_warrior).toBe(1);
    expect(rule.mutation_ids).toEqual([BLACKBLOOD, "campaign.mutation.great-claw", TENTACLE]);
    // The printed names with no catalogue entry are published, not invented.
    expect(rule.unrouted_mutation_names).toEqual(["prehensile tail", "beak", "electrical touch", "mer-creature", "suckers", "eye stalks"]);
    expect(availableMutations(reader, BAND).map((mutation) => mutation.id).sort()).toEqual([BLACKBLOOD, "campaign.mutation.great-claw", TENTACLE].sort());
    expect(availableMutations(reader, "masters-of-horror-sylv")).toEqual([]);
    expect(mutationCatalogue(reader).find((mutation) => mutation.id === BLACKBLOOD)?.cost_gc).toBe(30);
    // Listed price the first time, doubled for a second mutation.
    expect(mutationPrice(reader, BLACKBLOOD, 0)).toBe(30);
    expect(mutationPrice(reader, BLACKBLOOD, 1)).toBe(60);
  });

  it("buys a mutation during creation, charges the listed price and persists it", () => {
    const bought = buyMutation(draft([warrior("reaver", "reavers")]), reader, { warrior_id: "reaver", mutation_id: BLACKBLOOD });
    expect(bought.ok, bought.ok ? "" : bought.message).toBe(true);
    if (!bought.ok) return;
    expect(mutationsOf(bought.state, "reaver")).toEqual([BLACKBLOOD]);
    const record = bought.state.campaign.special_rules.find((row) => row["kind"] === "mutation")!;
    expect(record).toMatchObject({ warrior_id: "reaver", mutation_id: BLACKBLOOD, cost_gc: 30, order: 1, rule_id: "band--aquatic-mutants" });
    // The cost is charged against the draft treasury.
    expect(bought.state.campaign.warriors.find((row) => row.id === "reaver")?.cost).toBe(30);

    const serialized = adapter.serializeCampaign(bought.state.campaign);
    expect(serialized.ok, serialized.ok ? "" : serialized.message).toBe(true);
    if (!serialized.ok) return;
    const parsed = parseCampaignFileDetailed(serialized.text);
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    const restored: CampaignDocument = { campaign: parsed.campaign, view: parsed.view };
    expect(mutationsOf(restored, "reaver")).toEqual([BLACKBLOOD]);
  });

  it("refuses a duplicate, a second mutation over the printed limit, an unpriced name and a non-Hero", () => {
    const first = buyMutation(draft([warrior("reaver", "reavers")]), reader, { warrior_id: "reaver", mutation_id: BLACKBLOOD });
    expect(first.ok).toBe(true);
    if (!first.ok) return;

    const duplicate = buyMutation(first.state, reader, { warrior_id: "reaver", mutation_id: BLACKBLOOD });
    expect(duplicate.ok).toBe(false);
    if (!duplicate.ok) expect(duplicate.reason).toBe("conflict");

    const overLimit = buyMutation(first.state, reader, { warrior_id: "reaver", mutation_id: TENTACLE });
    expect(overLimit.ok).toBe(false);
    if (!overLimit.ok) expect(overLimit.reason).toBe("limit_reached");

    const unpriced = buyMutation(draft([warrior("reaver", "reavers")]), reader, { warrior_id: "reaver", mutation_id: "campaign.mutation.mer-creature" });
    expect(unpriced.ok).toBe(false);
    if (!unpriced.ok) expect(unpriced.reason).toBe("not_found");

    const henchman = buyMutation(draft([warrior("wrecker", "wreckers", "henchman")]), reader, { warrior_id: "wrecker", mutation_id: BLACKBLOOD });
    expect(henchman.ok).toBe(false);
    if (!henchman.ok) expect(henchman.reason).toBe("invalid_input");
  });

  it("refuses a purchase with insufficient funds", () => {
    const state = draft([warrior("reaver", "reavers")]);
    const poor: CampaignDocument = { campaign: { ...state.campaign, configuration: { ...state.campaign.configuration, starting_gold: 10 } }, view: state.view };
    const result = buyMutation(poor, reader, { warrior_id: "reaver", mutation_id: BLACKBLOOD });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("limit_violated");
  });

  it("buys for a member this post-battle recruited and books the cost on the pending battle", () => {
    const post = { battle_number: 1, complete: false, active_step: 7, completed_steps: [], review_open: false, gold_delta: 0, wyrdstone_delta: 0, pending_advances: [], step_state: {}, event_log: [{ step: 7, type: "recruit", warrior_id: "reaver", profile_id: "reavers", quantity: 1, gold: 40 }] };
    const postBattle: CampaignDocument = { campaign: campaign([warrior("reaver", "reavers")], false, [post]), view: {} };
    const bought = buyMutation(postBattle, reader, { warrior_id: "reaver", mutation_id: BLACKBLOOD });
    expect(bought.ok, bought.ok ? "" : bought.message).toBe(true);
    if (!bought.ok) return;
    expect(bought.state.campaign.post_battles[0]?.gold_delta).toBe(-30);
    expect(bought.state.campaign.post_battles[0]?.event_log?.at(-1)).toMatchObject({ type: "mutation", mutation_id: BLACKBLOOD });
    // Reopening the file keeps the recruitment moment: the persisted event log
    // still says who joined this post-battle, so the gate stays open for the
    // member it recruited (and only for him).
    // Reopening the file: the fixture records no battle row, so this exercises the
    // persisted document (the adapter round trip is asserted in the creation
    // test above), which is what the gate reads after a reload.
    const restored: CampaignDocument = JSON.parse(JSON.stringify(bought.state)) as CampaignDocument;
    const pending = restored.campaign.post_battles.find((row) => !row.complete)!;
    expect(recruitedDuringPost(pending, "reaver")).toBe(true);
    expect(recruitedDuringPost(pending, "someone-else")).toBe(false);
    expect(mutationsOf(restored, "reaver")).toEqual([BLACKBLOOD]);
    expect(restored.campaign.post_battles[0]?.gold_delta).toBe(-30);
    // The printed grant allows one mutation per warrior, so the refusal after the
    // reopen is the grant limit and no longer the recruitment moment.
    const second = buyMutation(restored, reader, { warrior_id: "reaver", mutation_id: TENTACLE });
    expect(second.ok).toBe(false);
    if (!second.ok) expect(second.reason).toBe("limit_reached");
  });

  it("refuses a veteran during a post-battle that did not recruit him", () => {
    const post = { battle_number: 1, complete: false, active_step: 7, completed_steps: [], review_open: false, gold_delta: 0, wyrdstone_delta: 0, pending_advances: [], step_state: {}, event_log: [{ step: 7, type: "recruit", warrior_id: "other", profile_id: "reavers", quantity: 1, gold: 40 }] };
    const postBattle: CampaignDocument = { campaign: campaign([warrior("reaver", "reavers")], false, [post]), view: {} };
    const late = buyMutation(postBattle, reader, { warrior_id: "reaver", mutation_id: BLACKBLOOD });
    expect(late.ok).toBe(false);
    if (late.ok) return;
    expect(late.reason).toBe("not_permitted_when_committed");
    expect(late.subject_ids).toEqual(["reaver"]);
  });

  it("buys for a member added to an existing group by this post-battle", () => {
    const post = { battle_number: 1, complete: false, active_step: 7, completed_steps: [], review_open: false, gold_delta: 0, wyrdstone_delta: 0, pending_advances: [], step_state: {}, event_log: [{ step: 7, type: "recruit_member", warrior_id: "wrecker", profile_id: "wreckers", quantity: 1, gold: 20 }] };
    const postBattle: CampaignDocument = { campaign: campaign([warrior("wrecker", "wreckers")], false, [post]), view: {} };
    const bought = buyMutation(postBattle, reader, { warrior_id: "wrecker", mutation_id: BLACKBLOOD });
    expect(bought.ok, bought.ok ? "" : bought.message).toBe(true);
    if (!bought.ok) return;
    expect(mutationsOf(bought.state, "wrecker")).toEqual([BLACKBLOOD]);
  });

  it("refuses a purchase policy the catalogue does not publish", () => {
    const unknown: typeof reader = {
      ...reader,
      campaignSection: (section: string) => {
        const data = reader.campaignSection!(section);
        if (section !== "mutations") return data;
        return { ...data, rules: { ...(data["rules"] as Record<string, unknown>), purchase: { timing: "at_recruitment_only", pricing: { first_mutation: "listed_price", second_and_subsequent: "triple_listed_price" } } } };
      },
    } as typeof reader;
    const result = buyMutation(draft([warrior("reaver", "reavers")]), unknown, { warrior_id: "reaver", mutation_id: BLACKBLOOD });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("not_available");
    expect(mutationPrice(unknown, BLACKBLOOD, 0)).toBeNull();
  });
});

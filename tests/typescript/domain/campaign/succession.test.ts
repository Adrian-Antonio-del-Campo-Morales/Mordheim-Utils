/**
 * T10 — leader succession.
 *
 * The published case is `pirates-of-the-cathayan-sea-sar / band--succession`:
 * "If the Disgraced Warlord is killed, one of the Shanghai'ers will take over".
 * The KB publishes the leader and successor profiles; the domain seats a
 * successor once the leader is gone and refuses to invent the core-book
 * tie-break (several candidates ask for a choice, none keeps the succession
 * owed).
 *
 * Assertions read the freshly generated artefact; the KB side is gated in
 * `tests/python/construction/test_construction_campaign_obligations.py`.
 */
import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { CampaignFileV5Adapter, parseCampaignFileDetailed } from "@adapters/campaign-file";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import {
  currentLeaderId,
  pendingSuccession,
  succeedLeader,
  successionClausesOf,
  successionLog,
} from "@domain/campaign/kernel/succession";
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

const BAND = "pirates-of-the-cathayan-sea-sar";
const CLAUSE = "campaign.succession.cathayan-pirates";

function warrior(id: string, profileId: string): Warrior {
  return { id, name: `${profileId} ${id}`, profile_name: profileId, kind: "hero", stats: {}, equipment: [], skills: [], experience: 0, cost: 0, quantity: 1, profile_id: profileId };
}

function campaign(warriors: readonly Warrior[], specialRules: readonly Record<string, unknown>[] = []): Campaign {
  return {
    identity: { campaign_name: "Succession", warband_name: "Cathay", warband_type: "Cathay", band_id: BAND, mercenary_variant: null },
    configuration: { is_draft: false, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
    resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 1,
    warriors,
    battles: [],
    states: [{ number: 1, date: "2026-09-28", gold: 500, wyrdstone: 0, rating: 0, models: 1, max_models: 15, heroes: 1, henchmen: 0, experience: 0 }],
    post_battles: [],
    inventory: [],
    special_rules: specialRules,
    manual_log: [],
  };
}

function document(warriors: readonly Warrior[], specialRules: readonly Record<string, unknown>[] = []): CampaignDocument {
  return { campaign: campaign(warriors, specialRules), view: {} };
}

describe.skipIf(!ARTEFACT_PATH)("T10 leader succession (generated artefact)", () => {
  const artefact = JSON.parse(readFileSync(ARTEFACT_PATH as string, "utf8"));
  const reader = ArtefactKnowledgeReader.from(artefact);

  it("publishes the leader and successor profiles of the printed clause", () => {
    const clauses = successionClausesOf(reader, BAND);
    expect(clauses).toHaveLength(1);
    expect(clauses[0]).toMatchObject({
      id: CLAUSE,
      rule_id: "band--succession",
      leader_profile_ids: ["disgraced-warlord"],
      successor_profile_ids: ["shanghaires"],
    });
    expect(successionClausesOf(reader, "masters-of-horror-sylv")).toEqual([]);
  });

  it("reads the leader from the roster and reports no pending succession", () => {
    const state = document([warrior("warlord", "disgraced-warlord"), warrior("mate", "shanghaires")]);
    expect(currentLeaderId(state, reader)).toBe("warlord");
    expect(pendingSuccession(state, reader)).toBeNull();
  });

  it("seats the only eligible successor once the leader is gone and persists it", () => {
    const state = document([warrior("mate", "shanghaires")]);
    const pending = pendingSuccession(state, reader);
    expect(pending?.candidates).toEqual(["mate"]);
    const seated = succeedLeader(state, reader, { clause_id: CLAUSE });
    expect(seated.ok, seated.ok ? "" : seated.message).toBe(true);
    if (!seated.ok) return;
    expect(currentLeaderId(seated.state, reader)).toBe("mate");
    expect(successionLog(seated.state)).toHaveLength(1);
    expect(successionLog(seated.state)[0]).toMatchObject({ kind: "leader_succession", clause_id: CLAUSE, successor_id: "mate", order: 1 });

    const serialized = adapter.serializeCampaign(seated.state.campaign);
    expect(serialized.ok, serialized.ok ? "" : serialized.message).toBe(true);
    if (!serialized.ok) return;
    const parsed = parseCampaignFileDetailed(serialized.text);
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    const restored: CampaignDocument = { campaign: parsed.campaign, view: parsed.view };
    expect(currentLeaderId(restored, reader)).toBe("mate");
    expect(pendingSuccession(restored, reader)).toBeNull();
  });

  it("asks which successor takes over when several candidates remain", () => {
    const state = document([warrior("mate-a", "shanghaires"), warrior("mate-b", "shanghaires")]);
    const ambiguous = succeedLeader(state, reader, { clause_id: CLAUSE });
    expect(ambiguous.ok).toBe(false);
    if (!ambiguous.ok) expect(ambiguous.reason).toBe("invalid_input");

    const chosen = succeedLeader(state, reader, { clause_id: CLAUSE, successor_warrior_id: "mate-b" });
    expect(chosen.ok, chosen.ok ? "" : chosen.message).toBe(true);
    if (chosen.ok) expect(currentLeaderId(chosen.state, reader)).toBe("mate-b");

    const outsider = succeedLeader(state, reader, { clause_id: CLAUSE, successor_warrior_id: "warlord" });
    expect(outsider.ok).toBe(false);
  });

  it("keeps the succession owed when no eligible successor exists", () => {
    const state = document([warrior("monk", "dragon-monk")]);
    const pending = pendingSuccession(state, reader);
    expect(pending).not.toBeNull();
    expect(pending?.candidates).toEqual([]);
    const result = succeedLeader(state, reader, { clause_id: CLAUSE });
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("prerequisite_missing");
  });

  it("refuses a succession while the leader still leads, and an unknown clause", () => {
    const state = document([warrior("warlord", "disgraced-warlord"), warrior("mate", "shanghaires")]);
    const early = succeedLeader(state, reader, { clause_id: CLAUSE });
    expect(early.ok).toBe(false);
    if (!early.ok) expect(early.reason).toBe("conflict");
    const unknown = succeedLeader(state, reader, { clause_id: "campaign.succession.nope" });
    expect(unknown.ok).toBe(false);
    if (!unknown.ok) expect(unknown.reason).toBe("not_found");
  });

  it("loads a campaign written before the clause existed (legacy leader)", () => {
    const legacy = document([warrior("warlord", "disgraced-warlord"), warrior("mate", "shanghaires")]);
    expect(successionLog(legacy)).toEqual([]);
    expect(currentLeaderId(legacy, reader)).toBe("warlord");
    // Once the original leader leaves, the printed successor can be seated.
    const afterLoss = document([warrior("mate", "shanghaires")]);
    expect(currentLeaderId(afterLoss, reader)).toBeNull();
    expect(pendingSuccession(afterLoss, reader)?.clause.id).toBe(CLAUSE);
  });
});

/**
 * T10 — warband-creation decisions.
 *
 * The published case is `adventurers-kaz / imperial-noble--family-heirloom`:
 * "When creating the warband roll a D6 to see what its power is". The roll is a
 * creation decision of the campaign, so the campaign kernel publishes the table
 * as data (`campaign.recruitment-and-veterans.creation_decisions`), demands the
 * roll while a recipient is in the draft, records the outcome with injected
 * dice and refuses to commit the warband until it is resolved.
 *
 * Assertions read the freshly generated artefact when
 * `MORDHEIM_KNOWLEDGE_ARTEFACT` points at it; the KB side is gated in
 * `tests/python/construction/test_construction_campaign_obligations.py`.
 *
 * Purity: plain Node, the real reader and the real v5 adapter — no React.
 */
import { describe, expect, it } from "vitest";
import { existsSync } from "node:fs";
import { readArtefactDocument } from "../../../support/kb-artefact";
import { join } from "node:path";

import { CampaignFileV5Adapter, parseCampaignFileDetailed } from "@adapters/campaign-file";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { commitInitialWarband } from "@domain/campaign/kernel/commit-warband";
import {
  creationDecisionOutcomeFor,
  creationDecisionsOf,
  owedCreationDecisions,
  recordedCreationDecision,
  resolveCreationDecision,
} from "@domain/campaign/kernel/creation-decisions";
import type { CampaignDocument } from "@domain/campaign/kernel/usecases";

const REPO_ROOT = join(import.meta.dirname, "..", "..", "..", "..");
const OVERRIDE = process.env.MORDHEIM_KNOWLEDGE_ARTEFACT;
const CANDIDATES = OVERRIDE
  ? [OVERRIDE]
  : [
      // The build output first: T10's evidence is the freshly generated
      // artefact, while `outputs/` still holds the pre-T10 copy T12 regenerates.
      join(REPO_ROOT, "build", "generated", "knowledge-web", "knowledge-web.json"),
      join(REPO_ROOT, "outputs", "web-public", "knowledge", "knowledge-web.json"),
    ];
const ARTEFACT_PATH = CANDIDATES.find((path) => existsSync(path));

const BAND = "adventurers-kaz";
const DECISION = "campaign.creation.family-heirloom";
const NOBLE = "imperial-noble";
const adapter = new CampaignFileV5Adapter();

/** A legal `adventurers-kaz` draft holding one Imperial Noble. */
function draft(profileIds: readonly string[] = [NOBLE]): CampaignDocument {
  const document: unknown = {
    view: { selected_moment: "draft:0" },
    campaign: {
      identity: {
        campaign_name: "Heirloom",
        warband_name: "Karak Azgal",
        warband_type: "Karak Azgal",
        band_id: BAND,
        mercenary_variant: null,
      },
      configuration: { is_draft: true, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 0,
      warriors: profileIds.map((profileId, index) => ({
        id: `w${index + 1}`,
        name: `Warrior ${index + 1}`,
        profile_name: profileId,
        kind: "hero",
        stats: {},
        equipment: [],
        skills: [],
        experience: 0,
        cost: 0,
        quantity: 1,
        profile_id: profileId,
      })),
      battles: [],
      states: [],
      post_battles: [],
      inventory: [],
      special_rules: [],
      manual_log: [],
    },
  };
  return document as CampaignDocument;
}

function roundtrip(document: CampaignDocument): CampaignDocument {
  const serialized = adapter.serializeCampaign(document.campaign);
  expect(serialized.ok, serialized.ok ? "" : serialized.message).toBe(true);
  if (!serialized.ok) return document;
  const parsed = parseCampaignFileDetailed(serialized.text);
  expect(parsed.ok).toBe(true);
  if (!parsed.ok) return document;
  return { campaign: parsed.campaign, view: parsed.view };
}

describe.skipIf(!ARTEFACT_PATH)("T10 creation decisions (generated artefact)", () => {
  const artefact = readArtefactDocument(ARTEFACT_PATH as string);
  const reader = ArtefactKnowledgeReader.from(artefact);

  it("publishes the printed Family Heirloom D6 as stable data", () => {
    const decisions = creationDecisionsOf(reader, BAND);
    expect(decisions).toHaveLength(1);
    const decision = decisions[0]!;
    expect(decision.id).toBe(DECISION);
    expect(decision.rule_id).toBe("imperial-noble--family-heirloom");
    expect(decision.profile_ids).toEqual([NOBLE]);
    expect(decision.required).toBe(true);
    expect(decision.dice).toEqual({ count: 1, sides: 6 });
    expect(decision.outcomes.map((outcome) => [outcome.result_id, outcome.min, outcome.max])).toEqual([
      ["psychology-reroll", 1, 2],
      ["fear-orcs-goblins-skaven", 3, 4],
      ["reroll-one-die", 5, 6],
    ]);
    // Spanish travels with the English canonical text, never as an identity.
    expect(decision.name_i18n.es).toBe("Reliquia Familiar");
    expect(decision.outcomes[2]?.result_i18n.es).toContain("repetir un dado");
    // Another band publishes no creation roll.
    expect(creationDecisionsOf(reader, "masters-of-horror-sylv")).toEqual([]);
  });

  it("reaches every roll of the printed table", () => {
    const decision = creationDecisionsOf(reader, BAND)[0]!;
    for (const [roll, resultId] of [[1, "psychology-reroll"], [2, "psychology-reroll"], [3, "fear-orcs-goblins-skaven"], [5, "reroll-one-die"], [6, "reroll-one-die"]] as const) {
      expect(creationDecisionOutcomeFor(decision, roll)?.result_id).toBe(resultId);
    }
  });

  it("owes the roll only while a recipient is in the draft", () => {
    expect(owedCreationDecisions(draft([]), reader)).toEqual([]);
    expect(owedCreationDecisions(draft(["imperial-captain"]), reader)).toEqual([]);
    const owed = owedCreationDecisions(draft(), reader);
    expect(owed.map((decision) => decision.id)).toEqual([DECISION]);
  });

  it("records the outcome with injected dice and refuses a second roll", () => {
    const readout = resolveCreationDecision(draft(), reader, { decision_id: DECISION, roll: 4 });
    expect(readout.ok).toBe(true);
    if (!readout.ok) return;
    const record = recordedCreationDecision(readout.state, DECISION)!;
    expect(record).toMatchObject({
      kind: "creation_decision",
      decision_id: DECISION,
      rule_id: "imperial-noble--family-heirloom",
      outcome_id: "fear-orcs-goblins-skaven",
      roll: 4,
      order: 1,
    });
    expect(String(record.text)).toContain("Fear");
    expect(owedCreationDecisions(readout.state, reader)).toEqual([]);

    const again = resolveCreationDecision(readout.state, reader, { decision_id: DECISION, roll: 5 });
    expect(again.ok).toBe(false);
    if (!again.ok) expect(again.reason).toBe("conflict");
  });

  it("rejects a roll outside the printed dice and an unknown decision", () => {
    for (const roll of [0, 7, 2.5]) {
      const result = resolveCreationDecision(draft(), reader, { decision_id: DECISION, roll });
      expect(result.ok, String(roll)).toBe(false);
      if (!result.ok) expect(result.reason).toBe("invalid_input");
    }
    const unknown = resolveCreationDecision(draft(), reader, { decision_id: "campaign.creation.nope", roll: 3 });
    expect(unknown.ok).toBe(false);
    if (!unknown.ok) expect(unknown.reason).toBe("not_found");
  });

  it("blocks the commit while the required roll is missing and accepts it afterwards", () => {
    const blocked = commitInitialWarband(draft(), reader);
    expect(blocked.ok).toBe(false);
    if (!blocked.ok) {
      expect(blocked.reason).toBe("prerequisite_missing");
      expect(blocked.message).toContain("Family Heirloom");
      expect(blocked.subject_ids).toEqual([DECISION]);
    }
    const resolved = resolveCreationDecision(draft(), reader, { decision_id: DECISION, roll: 2 });
    expect(resolved.ok).toBe(true);
    if (!resolved.ok) return;
    const committed = commitInitialWarband(resolved.state, reader);
    expect(committed.ok, committed.ok ? "" : committed.message).toBe(true);
    if (committed.ok) expect(committed.state.campaign.configuration.is_draft).toBe(false);
  });

  it("keeps the recorded decision across a v5 round-trip and reloads an older campaign", () => {
    const resolved = resolveCreationDecision(draft(), reader, { decision_id: DECISION, roll: 5 });
    expect(resolved.ok).toBe(true);
    if (!resolved.ok) return;
    const restored = roundtrip(resolved.state);
    const record = recordedCreationDecision(restored, DECISION);
    expect(record).toMatchObject({ outcome_id: "reroll-one-die", roll: 5, order: 1 });
    expect(owedCreationDecisions(restored, reader)).toEqual([]);
    // A file written before the decision existed carries no record: it loads
    // unchanged and the roll becomes owed again.
    const legacy = roundtrip(draft());
    expect(recordedCreationDecision(legacy, DECISION)).toBeNull();
    expect(owedCreationDecisions(legacy, reader).map((decision) => decision.id)).toEqual([DECISION]);
  });
});

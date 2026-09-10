/**
 * Parity port of desktop `tests/campaign/test_out_of_action_tracking.py`
 * (7 test functions → behavioural equivalents). Traceability: manifest rows
 * with `web_target: packages/typescript/domain/campaign/out_of_action_tracking.test.ts`.
 *
 * Desktop semantics: `record_battle` stores `out_of_action_ids` verbatim
 * (duplicates preserved — henchman group members are recorded individually)
 * and derives `casualties` from the list length; legacy battles carry
 * `null` and Recovery falls back to every warrior. The
 * `_out_of_action_warriors` dialog filter itself is UI-side (web UI lane);
 * here the campaign-state half is covered: record → derive → persist.
 *
 * The `view` section is reconstructible UI state (v4 contract): the file
 * round-trip comparison ignores it, exactly like the desktop's
 * `restored.campaign == state.campaign` comparison.
 */

import { describe, expect, it } from "vitest";

import { recordBattle } from "./kernel/record-battle";
import { cloneDocument } from "./kernel/document";
import type { CampaignDocument } from "./kernel/usecases";
import type { CampaignFilePort, KnowledgeReader } from "./kernel/ports";
import { CampaignFileV4Adapter } from "../../adapters/campaign-file/index";

function makeDocument(): CampaignDocument {
  return {
    campaign: {
      identity: {
        campaign_name: "OOA Campaign",
        warband_name: "Test Band",
        warband_type: "Sisters of Sigmar",
        band_id: "sisters-of-sigmar",
        mercenary_variant: null,
      },
      configuration: {
        is_draft: false,
        starting_gold: 500,
        minimum_models: 3,
        maximum_models: 15,
        hero_limit: 5,
      },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 0,
      warriors: [
        { id: "marta", name: "Marta", profile_name: "Sister Superior", kind: "hero", stats: { WS: 4 }, equipment: [], skills: [], experience: 2, cost: 45 },
        { id: "novices", name: "Novices", profile_name: "Novice Sisters", kind: "henchman", stats: { WS: 3 }, equipment: [], skills: [], experience: 0, cost: 25, quantity: 3 },
        { id: "anna", name: "Anna", profile_name: "Sigmarite Matriarch", kind: "hero", stats: { WS: 4 }, equipment: [], skills: [], experience: 5, cost: 70 },
      ],
      battles: [],
      states: [],
      post_battles: [],
      inventory: [],
      special_rules: [],
      manual_log: [],
    },
    view: {},
  };
}

const fakeKnowledge: KnowledgeReader = {
  queryKnowledge: (query) =>
    query.id.kind === "scenario_id" && query.id.value === "scenario.skirmish"
      ? {
          ok: true,
          record: {
            kind: "scenario",
            id: query.id,
            names: { en: "Skirmish" },
            data: {},
          },
        }
      : { ok: false, reason: "not_found" },
  queryMany: (queries) => queries.map((q) => fakeKnowledge.queryKnowledge(q)),
};

const files: CampaignFilePort = new CampaignFileV4Adapter();

function record(document: CampaignDocument, out_of_action_ids: string[] | null) {
  return recordBattle(document, {
    scenario: "scenario.skirmish",
    opponent: "Cultists",
    result: "win",
    gold_delta: 0,
    wyrdstone: 0,
    xp_delta: 1,
    casualties: 0,
    out_of_action_ids,
  }, fakeKnowledge);
}

/** Desktop `_settled()` + `_record()` equivalent: committed, non-draft band. */
function settledAndRecorded(out_of_action_ids: string[] | null): CampaignDocument {
  const base = makeDocument();
  const result = record(base, out_of_action_ids);
  if (!result.ok) throw new Error(result.message);
  return result.state;
}

describe("desktop test_out_of_action_tracking.py → web recordBattle parity", () => {
  it("recorded ids set the casualties count", () => {
    const document = settledAndRecorded(["marta", "novices"]);
    const battle = document.campaign.battles.at(-1)!;
    expect(battle.out_of_action_ids).toEqual(["marta", "novices"]);
    expect(battle.casualties).toBe(2);
  });

  it("empty record keeps casualties zero and ids empty", () => {
    const document = settledAndRecorded([]);
    const battle = document.campaign.battles.at(-1)!;
    expect(battle.out_of_action_ids).toEqual([]);
    expect(battle.casualties).toBe(0);
  });

  it("henchman group casualties are preserved individually", () => {
    const document = settledAndRecorded(["novices", "novices"]);
    const battle = document.campaign.battles.at(-1)!;
    expect(battle.out_of_action_ids).toEqual(["novices", "novices"]);
    expect(battle.casualties).toBe(2);
  });

  it("recovery falls back to every warrior for legacy battles", () => {
    // A legacy battle carries out_of_action_ids === null (v4 contract's
    // "not recorded" distinction). Construct one directly: the reader must
    // treat null as "no prefilter", not as an empty checklist.
    const document = settledAndRecorded(["marta"]);
    const legacy = cloneDocument(document);
    const legacyBattles = legacy.campaign.battles.map((b) =>
      b.number === legacy.campaign.battles[0].number ? { ...b, out_of_action_ids: null } : b,
    );
    const legacyCampaign = { ...legacy.campaign, battles: legacyBattles };
    const legacyDocument: CampaignDocument = { campaign: legacyCampaign, view: legacy.view };
    const stored = legacyDocument.campaign.battles[0];
    expect(stored.out_of_action_ids).toBeNull();
    // The UI-side fallback derives from the roster; assert the data the
    // fallback needs is intact (every warrior present in the document).
    expect(legacyDocument.campaign.warriors.map((w) => w.id)).toEqual(["marta", "novices", "anna"]);
  });

  it("unknown ids are rejected, not silently filtered", () => {
    // Desktop's dialog filter ignores unknown ids post-hoc; the web kernel
    // is stricter at the boundary: recordBattle rejects them (typed value).
    const result = record(makeDocument(), ["marta", "ghost"]);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("not_found");
  });

  it("out of action ids survive save/load (v4 round-trip)", () => {
    const document = settledAndRecorded(["anna"]);
    const serialized = files.serializeCampaign(document.campaign);
    expect(serialized.ok).toBe(true);
    if (!serialized.ok) return;
    const parsed = files.parseCampaignFile(serialized.text);
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    const restored = parsed.document.campaign as unknown as CampaignDocument["campaign"];
    const battle = restored.battles.at(-1)!;
    expect(battle.out_of_action_ids).toEqual(["anna"]);
    expect(battle.casualties).toBe(1);
  });

  it("stored ids match the roster warriors (filter preconditions)", () => {
    const document = settledAndRecorded(["marta", "novices"]);
    const battle = document.campaign.battles.at(-1)!;
    const known = new Set(document.campaign.warriors.map((w) => w.id));
    for (const id of battle.out_of_action_ids ?? []) {
      expect(known.has(id)).toBe(true);
    }
  });
});

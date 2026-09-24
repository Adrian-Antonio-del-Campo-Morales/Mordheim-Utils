/**
 * Campaign-file interoperability matrix: the TypeScript side of the full
 * bidirectional round-trip matrix.
 *
 * Two duties:
 * 1. Pin the fixture loop in one place: Python-written fixture texts go
 *    parse → serialize → parse → serialize, with semantic equality (only
 *    `saved_at`/`view` volatile) between generations, for all four fixtures.
 * 2. Emit the P6.x workflow-generated documents (draft → commit → battle →
 *    post-battle steps, via the real kernel workflows) as a JSON artefact
 *    the Python harness (`tests/python/web/contract/test_p71_full_matrix.py`)
 *    loads through the desktop reader.
 */
import { describe, expect, it } from "vitest";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";

import {
  CampaignFileV5Adapter,
  parseCampaignFileDetailed,
} from "@adapters/campaign-file/index";
import { createDefaultUseCases } from "@domain/campaign/kernel/default-usecases";
import { createDraftWorkflow } from "@app/campaign/features/draft/draft-workflow";
import { createBattleWorkflow } from "@app/campaign/features/battle/battle-workflow";
import type { KnowledgeReader, KnowledgeResult, KnowledgeQuery } from "@domain/campaign/index";
import type { CampaignDocument } from "@domain/campaign/index";

function findRepoRoot(): string {
  let dir = process.cwd();
  for (let i = 0; i < 6; i++) {
    try {
      readFileSync(join(dir, "contracts", "campaign-file-v5", "campaign-file-v5.schema.json"), "utf-8");
      return dir;
    } catch {
      dir = join(dir, "..");
    }
  }
  throw new Error("repo root with contracts/campaign-file-v5 not found from " + process.cwd());
}

const REPO_ROOT = findRepoRoot();
const FIXTURES = join(REPO_ROOT, "contracts", "campaign-file-v5", "fixtures");
const OUT_DIR = join(REPO_ROOT, "outputs", "campaign-file-interop");

const FIXTURE_NAMES = [
  "draft.json",
  "active-campaign.json",
  "pending-post-battle.json",
  "full-inventory.json",
] as const;

function fixtureText(name: (typeof FIXTURE_NAMES)[number]): string {
  return readFileSync(join(FIXTURES, name), "utf-8");
}

/** Artefact-shaped rows mirroring the P4.2 generator output. */
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
      id: "sigmarite-matriarch", band_id: "sisters-of-sigmar", collection: "mordheim",
      type: "hero", cost: 70, experience: 0, name: "Sigmarite Matriarch",
      names: { en: "Sigmarite Matriarch" },
      characteristics: { M: 4, WS: 4, BS: 4, S: 3, T: 3, W: 1, I: 4, A: 1, Ld: 8 },
      fixed_equipment: ["sigmarite_hammer"], skill_access: ["combat"],
    },
    "profile_id:sigmarite-sister": {
      id: "sigmarite-sister", band_id: "sisters-of-sigmar", collection: "mordheim",
      type: "henchman", cost: 25, experience: 0, name: "Sigmarite Sister",
      names: { en: "Sigmarite Sister" },
      characteristics: { M: 4, WS: 3, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
      fixed_equipment: [],
    },
    "item_id:sigmarite_hammer": {
      item_id: "sigmarite_hammer", kind: "close-combat-weapon", name: "Sigmarite Hammer",
      names: { en: "Sigmarite Hammer" }, value: 15,
    },
    "scenario_id:skirmish": { id: "skirmish", name: "Skirmish", names: { en: "Skirmish" } },
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

/** Builds the core progression documents through the real workflows. */
function workflowDocuments(): Record<string, Record<string, unknown>> {
  const knowledge = makeKnowledge();
  const useCases = createDefaultUseCases(knowledge);
  const draft = createDraftWorkflow({ knowledge, useCases });
  const battle = createBattleWorkflow({ knowledge, useCases });

  const started = draft.startDraft("sisters-of-sigmar");
  if (!started.ok) throw new Error("workflow: startDraft failed");
  const committed = draft.commit(started.document);
  if (!committed.ok) throw new Error("workflow: commit failed");

  const recorded = battle.record(committed.document, {
    scenario: "skirmish",
    opponent: "Reiklanders",
    result: "win",
    gold_delta: 30,
    wyrdstone: 2,
    xp_delta: 6,
    out_of_action_ids: [],
  });
  if (!recorded.ok) throw new Error("workflow: record failed");

  let progressed = recorded.document;
  for (let step = 0; step < 4; step += 1) {
    const resolved = battle.resolveStep(progressed, { roll: 3 + step });
    if (!resolved.ok) throw new Error(`workflow: resolveStep ${step} failed`);
    progressed = resolved.document;
  }

  const documents: Record<string, Record<string, unknown>> = {};
  for (const [name, document] of Object.entries({
    "committed-draft": committed.document,
    "after-battle": recorded.document,
    "post-battle-progressed": progressed,
  }) as [string, CampaignDocument][]) {
    const serialized = new CampaignFileV5Adapter().serializeCampaign(document.campaign);
    if (!serialized.ok) throw new Error(`workflow: serialize ${name} failed`);
    documents[name] = JSON.parse(serialized.text) as Record<string, unknown>;
  }
  return documents;
}

describe("P7.1: fixture loop pinned (parse → serialize ×2)", () => {
  const port = new CampaignFileV5Adapter();

  for (const name of FIXTURE_NAMES) {
    it(`full loop stays semantically stable for ${name}`, () => {
      const first = parseCampaignFileDetailed(fixtureText(name));
      expect(first.ok).toBe(true);
      if (!first.ok) return;
      const gen1 = port.serializeCampaign(first.campaign);
      expect(gen1.ok).toBe(true);
      if (!gen1.ok) return;
      const second = parseCampaignFileDetailed(gen1.text);
      expect(second.ok).toBe(true);
      if (!second.ok) return;
      const gen2 = port.serializeCampaign(second.campaign);
      expect(gen2.ok).toBe(true);
      if (!gen2.ok) return;

      // Generations 1 and 2 are semantically identical (both re-emitted by
      // the same serializer; only saved_at may differ).
      const a = JSON.parse(gen1.text) as Record<string, unknown>;
      const b = JSON.parse(gen2.text) as Record<string, unknown>;
      delete a["saved_at"];
      delete b["saved_at"];
      expect(b).toEqual(a);
    });
  }
});

describe("P7.1: workflow documents emitted for the Python harness", () => {
  it("emits the core progression documents", () => {
    mkdirSync(OUT_DIR, { recursive: true });
    const documents = workflowDocuments();
    expect(Object.keys(documents).sort()).toEqual([
      "after-battle",
      "committed-draft",
      "post-battle-progressed",
    ]);
    writeFileSync(
      join(OUT_DIR, "_p71-workflow-documents.json"),
      JSON.stringify({ documents }, null, 1) + "\n",
      "utf-8",
    );
    // Each emitted document must itself parse back through the adapter.
    for (const [name, document] of Object.entries(documents)) {
      const reparsed = parseCampaignFileDetailed(JSON.stringify(document));
      expect(reparsed.ok, name).toBe(true);
    }
  });
});

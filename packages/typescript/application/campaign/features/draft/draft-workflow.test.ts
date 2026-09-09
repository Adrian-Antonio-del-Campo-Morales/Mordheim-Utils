/**
 * P6.2 acceptance tests (plan §7): the draft workflow drives create →
 * compose → commit through the real kernel use cases with an
 * artefact-shaped fake KnowledgeReader — plain Node, no React/DOM.
 * The final committed draft round-trips through a fake file port (export →
 * re-import) proving timeline/roster/inventory conservation.
 */

import { describe, expect, it } from "vitest";

import type {
  CampaignDocument,
  CampaignFilePort,
  KnowledgeReader,
  KnowledgeResult,
  KnowledgeQuery,
  ParseResult,
  SerializeResult,
} from "../../../../domain/campaign/index";
import { createDefaultUseCases } from "../../../../domain/campaign/kernel/default-usecases";
import { createDraftWorkflow } from "./draft-workflow";

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
    "band_id:reiklanders": {
      id: "reiklanders",
      name: "Reiklanders",
      names: { en: "Reiklanders" },
      collection: "mordheim",
      roster: { minimum_models: 3, maximum_models: 15, starting_gold: 500, members: [] },
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
      skill_access: ["combat"],
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

/** Minimal in-memory file port mirroring the P3.2 adapter semantics. */
function makeFilePort(): CampaignFilePort {
  return {
    parseCampaignFile(text: string): ParseResult {
      return {
        ok: true,
        document: {
          marker: "MORDHEIM_CAMPAIGN_MANAGER",
          format_version: 4,
          saved_at: "2026-09-09T00:00:00Z",
          campaign: JSON.parse(text) as Record<string, unknown>,
        },
      };
    },
    serializeCampaign(campaign): SerializeResult {
      return { ok: true, text: JSON.stringify(campaign) };
    },
  };
}

function makeWorkflow() {
  const knowledge = makeKnowledge();
  return {
    workflow: createDraftWorkflow({ knowledge, useCases: createDefaultUseCases(knowledge) }),
    filePort: makeFilePort(),
  };
}

describe("P6.2 warband selection", () => {
  it("resolves KB band candidates into options, filtering unknown ids", () => {
    const { workflow } = makeWorkflow();
    const options = workflow.resolveWarbandOptions([
      "sisters-of-sigmar",
      "reiklanders",
      "no-such-band",
    ]);
    expect(options.map((o) => o.band_id)).toEqual(["sisters-of-sigmar", "reiklanders"]);
    const sisters = options[0];
    expect(sisters.name).toBe("Sisters of Sigmar");
    expect(sisters.es_name).toBe("Hermanas de Sigmar");
    expect(sisters.collection).toBe("mordheim");
  });
});

describe("P6.2 draft creation and composition", () => {
  it("starts a legal draft with the mandatory hero and minimum models", () => {
    const { workflow } = makeWorkflow();
    const result = workflow.startDraft("sisters-of-sigmar", "My Campaign");
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const { campaign } = result.document;
    expect(campaign.identity.campaign_name).toBe("My Campaign");
    expect(campaign.configuration.is_draft).toBe(true);
    const status = workflow.status(result.document);
    expect(status.legal).toBe(true);
    expect(status.treasury).toBeGreaterThan(0);
  });

  it("adds a hero row with purchased equipment and reflects the limits", () => {
    const { workflow } = makeWorkflow();
    const started = workflow.startDraft("sisters-of-sigmar");
    if (!started.ok) throw new Error("start should succeed");
    const result = workflow.addRow(started.document, {
      profile_id: "sister-superior",
      kind: "hero",
      quantity: 1,
      equipment: ["shield"],
    });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const added = result.document.campaign.warriors.find((w) => w.profile_id === "sister-superior");
    expect(added).toBeTruthy();
    expect(added?.equipment.some((e) => e.item_id === "shield" && e.acquisition === "purchase")).toBe(true);
    const status = workflow.status(result.document);
    expect(status.models).toBe(workflow.status(started.document).models + 1);
    // The row (35) + its shield (5) left the treasury: 380 → 340.
    expect(status.treasury).toBe(workflow.status(started.document).treasury - 40);
  });

  it("rejects composition that exceeds the model limit or the treasury", () => {
    const { workflow } = makeWorkflow();
    const started = workflow.startDraft("sisters-of-sigmar");
    if (!started.ok) throw new Error("start should succeed");
    // Model limit: the starter holds 3 models; a 13-model group reaches 16 > 15.
    const overModels = workflow.addRow(started.document, {
      profile_id: "sigmarite-sister",
      kind: "henchman",
      quantity: 13,
      equipment: [],
    });
    expect(overModels.ok).toBe(false);
    if (!overModels.ok) expect(overModels.message).toContain("models");

    // Treasury: the draft has 380 gold left; a hero row costing 35 that also
    // buys 76 shields (5 each = 380) needs 415 in total → limit_violated.
    const overGold = workflow.addRow(started.document, {
      profile_id: "sister-superior",
      kind: "hero",
      quantity: 1,
      equipment: Array.from({ length: 76 }, () => "shield"),
    });
    expect(overGold.ok).toBe(false);
    if (!overGold.ok) expect(overGold.message).toContain("gold");
  });

  it("removes a purchased row and frees its equipment back to the stash", () => {
    const { workflow } = makeWorkflow();
    const started = workflow.startDraft("sisters-of-sigmar");
    if (!started.ok) throw new Error("start should succeed");
    const added = workflow.addRow(started.document, {
      profile_id: "sister-superior",
      kind: "hero",
      quantity: 1,
      equipment: ["shield"],
    });
    if (!added.ok) throw new Error("add should succeed");
    const addedRow = added.document.campaign.warriors.find((w) => w.profile_id === "sister-superior");
    if (!addedRow) throw new Error("row missing");
    const removed = workflow.removeRow(added.document, addedRow.id);
    expect(removed.ok).toBe(true);
    if (!removed.ok) return;
    expect(removed.document.campaign.warriors.some((w) => w.profile_id === "sister-superior")).toBe(false);
    // The shield (purchased for this row) is back in the stash.
    const shield = removed.document.campaign.inventory.find((item) => item.id === "shield");
    expect(shield?.stash).toBe(1);
    expect(shield?.equipped).toBe(0);
  });

  it("protects the last hero of a draft", () => {
    const { workflow } = makeWorkflow();
    const started = workflow.startDraft("sisters-of-sigmar");
    if (!started.ok) throw new Error("start should succeed");
    const matriarch = started.document.campaign.warriors.find((w) => w.kind === "hero");
    if (!matriarch) throw new Error("fixture needs a hero");
    const result = workflow.removeRow(started.document, matriarch.id);
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.message).toContain("at least one hero");
  });
});

describe("P6.2 commit and round-trip", () => {
  it("commits a legal draft to State #0; rejects an illegal one", () => {
    const { workflow } = makeWorkflow();
    const started = workflow.startDraft("sisters-of-sigmar");
    if (!started.ok) throw new Error("start should succeed");
    const committed = workflow.commit(started.document);
    expect(committed.ok).toBe(true);
    if (!committed.ok) return;
    const { campaign } = committed.document;
    expect(campaign.configuration.is_draft).toBe(false);
    expect(campaign.current_state_number).toBe(0);
    expect(campaign.states).toHaveLength(1);
    // Double commit is rejected.
    const again = workflow.commit(committed.document);
    expect(again.ok).toBe(false);
  });

  it("round-trips the committed draft through export → re-import", () => {
    const { workflow, filePort } = makeWorkflow();
    const started = workflow.startDraft("sisters-of-sigmar");
    if (!started.ok) throw new Error("start should succeed");
    const added = workflow.addRow(started.document, {
      profile_id: "sister-superior",
      kind: "hero",
      quantity: 1,
      equipment: ["shield"],
    });
    if (!added.ok) throw new Error("add should succeed");
    const committed = workflow.commit(added.document);
    if (!committed.ok) throw new Error("commit should succeed");

    const serialized = filePort.serializeCampaign(committed.document.campaign);
    expect(serialized.ok).toBe(true);
    if (!serialized.ok) return;
    const parsed = filePort.parseCampaignFile(serialized.text);
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    const reimported = parsed.document.campaign as unknown as CampaignDocument["campaign"];
    expect(reimported.identity.band_id).toBe("sisters-of-sigmar");
    expect(reimported.warriors).toHaveLength(committed.document.campaign.warriors.length);
    expect(reimported.states).toHaveLength(1);
    expect(reimported.states[0].number).toBe(0);
    expect(reimported.inventory.map((i) => i.id).sort()).toEqual(
      committed.document.campaign.inventory.map((i) => i.id).sort(),
    );
  });
});

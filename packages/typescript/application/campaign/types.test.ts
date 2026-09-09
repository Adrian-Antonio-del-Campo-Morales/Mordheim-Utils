import { describe, expect, it } from "vitest";

import type {
  CampaignDocument,
  CampaignUseCases,
  KnowledgeReader,
  UseCaseRejectionReason,
  UseCaseResult,
} from "../../domain/campaign/index";
import type { CampaignAppService } from "./index";
import type { Campaign } from "../../domain/campaign/index";

/**
 * P3.4 acceptance criterion: domain, application and UI tasks can compile
 * against these interfaces using fakes — in plain Node, no React/DOM.
 */

const draftCampaign: Campaign = {
  identity: {
    campaign_name: "Test",
    warband_name: "Test Band",
    warband_type: "Display Name",
    band_id: "sisters-of-sigmar",
    mercenary_variant: null,
  },
  configuration: {
    is_draft: true,
    starting_gold: 500,
    minimum_models: 3,
    maximum_models: 15,
    hero_limit: 5,
  },
  resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
  current_state_number: 0,
  warriors: [],
  battles: [],
  states: [],
  post_battles: [],
  inventory: [],
  special_rules: [],
  manual_log: [],
};

const document: CampaignDocument = { campaign: draftCampaign, view: {} };

const fakeKnowledge: KnowledgeReader = {
  queryKnowledge: (query) =>
    query.id.value === "sisters-of-sigmar"
      ? {
          ok: true,
          record: {
            kind: "band",
            id: query.id,
            names: { en: "Sisters of Sigmar", es: "Hermanas de Sigmar" },
            data: {},
          },
        }
      : { ok: false, reason: "not_found" },
  queryMany: (queries) => queries.map((q) => fakeKnowledge.queryKnowledge(q)),
};

/** A fake use-case set any feature block can build on. */
const fakeUseCases: CampaignUseCases = {
  createDraft: () => ({ ok: true, state: document }),
  composeDraft: () => rejected("not_permitted_in_draft", "no"),
  commitInitialWarband: () => ({ ok: true, state: document }),
  selectMoment: () => ({ ok: true, state: { ...document, view: { selected_moment: "state:0" } } }),
  recordBattle: () => rejected("prerequisite_missing", "commit first"),
  resolvePostBattleStep: () => rejected("not_found", "no post-battle"),
  applyAdvance: () => rejected("not_found", "no advance"),
  assignEquipment: () => rejected("not_found", "no item"),
  hireHireling: () => rejected("not_found", "no hireling"),
  buyTradingItem: () => rejected("not_found", "no item"),
  sellStashItem: () => rejected("not_found", "no item"),
  validateForExport: () => ({ ok: true, state: document }),
};

function rejected(reason: UseCaseRejectionReason, message: string): UseCaseResult {
  return { ok: false, reason, message };
}

/** A fake app service showing the UI-facing seam. */
const fakeApp: CampaignAppService = {
  importCampaign: async () => ({ ok: true, document }),
  exportCampaign: async () => ({
    ok: true,
    document,
    payload: { filename: "test.mordheim", text: "{}" },
  }),
  run: async () => ({ ok: true, document }),
  selectMoment: () => ({ ok: true, document }),
  isDirty: () => false,
  current: () => document,
};

describe("P3.4 frozen interfaces", () => {
  it("domain fakes compile and run in plain Node", () => {
    const result = fakeUseCases.selectMoment(document, "state:0");
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.state.view.selected_moment).toBe("state:0");
    }
    expect(fakeKnowledge.queryKnowledge({ id: { kind: "band_id", value: "sisters-of-sigmar" } }).ok).toBe(true);
    expect(fakeKnowledge.queryKnowledge({ id: { kind: "item_id", value: "dagger" } })).toEqual({
      ok: false,
      reason: "not_found",
    });
  });

  it("application fake compiles against the service interface", async () => {
    const imported = await fakeApp.importCampaign({ text: "{}" });
    expect(imported.ok).toBe(true);
    expect(fakeApp.isDirty()).toBe(false);
    expect(fakeApp.current()?.campaign.identity.band_id).toBe("sisters-of-sigmar");
  });

  it("rejected operations are values, not exceptions", () => {
    const result = fakeUseCases.applyAdvance(document, { warrior_id: "w1", table: "stat", choice: "S" });
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(typeof result.message).toBe("string");
    }
  });
});

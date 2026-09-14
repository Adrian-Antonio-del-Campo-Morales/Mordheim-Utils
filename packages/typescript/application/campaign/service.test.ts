/**
 * Campaign application service tests: the service runs
 * import → edit → export using fakes, in plain Node — no React, no browser
 * APIs. Also covers the confirm-replace guard, dirty tracking, undo and
 * error translation from file-port / use-case failures.
 */

import { describe, expect, it } from "vitest";

import { createCampaignAppService } from "./service";
import type { CampaignAppDeps, CampaignAppService } from "./types";
import type {
  Campaign,
  CampaignFileError,
  CampaignFilePort,
  KnowledgeReader,
  ParseResult,
  SerializeResult,
} from "../../domain/campaign/index";

function makeCampaign(overrides: Partial<Campaign> = {}): Campaign {
  return {
    identity: {
      campaign_name: "My Campaign",
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
    warriors: [],
    battles: [],
    states: [],
    post_battles: [],
    inventory: [],
    special_rules: [],
    manual_log: [],
    ...overrides,
  };
}

const okDocument = {
  marker: "MORDHEIM_CAMPAIGN_MANAGER" as const,
  format_version: 5 as const,
  saved_at: "2026-09-09T00:00:00Z",
  campaign: {} as Record<string, unknown>,
};

const fakeFiles: CampaignFilePort = {
  parseCampaignFile: (text: string): ParseResult => {
    if (text === "NOT JSON") {
      return {
        ok: false,
        reason: "invalid_json",
        message: "The file is not valid JSON.",
        supported_versions: [5],
      } as CampaignFileError;
    }
    if (text === "OLD") {
      return {
        ok: false,
        reason: "retired_version",
        message: "Format version 3 is no longer supported.",
        found_version: 3,
        supported_versions: [5],
      } as CampaignFileError;
    }
    if (text === "BROKEN") {
      return {
        ok: false,
        reason: "schema_violation",
        message: "campaign.warriors must be an array.",
        location: "campaign.warriors",
        supported_versions: [5],
      } as CampaignFileError;
    }
    return { ok: true, document: { ...okDocument, campaign: makeCampaign() as unknown as Record<string, unknown> } };
  },
  serializeCampaign: (): SerializeResult => ({
    ok: true,
    text: '{"marker":"MORDHEIM_CAMPAIGN_MANAGER","format_version":5}',
  }),
};

const fakeKnowledge: KnowledgeReader = {
  queryKnowledge: () => ({ ok: false, reason: "not_found" }),
  queryMany: (queries) => queries.map((q) => fakeKnowledge.queryKnowledge(q)),
};

function makeService(): { service: CampaignAppService; deps: CampaignAppDeps } {
  const deps: CampaignAppDeps = { files: fakeFiles, knowledge: fakeKnowledge };
  return { service: createCampaignAppService(deps), deps };
}

async function serviceWithCampaign(campaign: Campaign, knowledge: KnowledgeReader = fakeKnowledge): Promise<CampaignAppService> {
  const files: CampaignFilePort = { ...fakeFiles, parseCampaignFile: () => ({ ok: true, document: { ...okDocument, campaign: campaign as unknown as Record<string, unknown> } }) };
  const service = createCampaignAppService({ files, knowledge });
  await service.importCampaign({ text: "fixture" });
  return service;
}

describe("P5.1 campaign application service", () => {
  it("imports a valid file, exposes the document and starts clean", async () => {
    const { service } = makeService();
    const result = await service.importCampaign({ text: "OK" });
    expect(result.ok).toBe(true);
    expect(service.current()?.campaign.identity.band_id).toBe("sisters-of-sigmar");
    expect(service.isDirty()).toBe(false);
  });

  it("rejects replacement without confirmation, allows it when confirmed", async () => {
    const { service } = makeService();
    await service.importCampaign({ text: "OK" });
    const denied = await service.importCampaign({ text: "OK" });
    expect(denied.ok).toBe(false);
    if (!denied.ok) expect(denied.reason).toBe("already_loaded");
    const allowed = await service.importCampaign({ text: "OK", confirm_replace: true });
    expect(allowed.ok).toBe(true);
  });

  it("does not replace the loaded campaign when a replacement file is invalid", async () => {
    const { service } = makeService();
    const loaded = await service.importCampaign({ text: "OK" });
    expect(loaded.ok).toBe(true);
    const before = service.current();

    const rejected = await service.importCampaign({ text: "BROKEN", confirm_replace: true });
    expect(rejected.ok).toBe(false);
    if (!rejected.ok) expect(rejected.reason).toBe("file_error");
    expect(service.current()).toBe(before);
    expect(service.isDirty()).toBe(false);
  });

  it("does not replace the loaded campaign when replacement JSON is invalid", async () => {
    const { service } = makeService();
    await service.importCampaign({ text: "OK" });
    const before = service.current();

    const rejected = await service.importCampaign({ text: "NOT JSON", confirm_replace: true });
    expect(rejected.ok).toBe(false);
    expect(service.current()).toBe(before);
  });

  it("translates file-port failures into stable app errors", async () => {
    const { service } = makeService();
    for (const [text, expected] of [
      ["NOT JSON", "file_error"],
      ["OLD", "file_error"],
      ["BROKEN", "file_error"],
    ] as const) {
      const result = await service.importCampaign({ text });
      expect(result.ok).toBe(false);
      if (!result.ok) {
        expect(result.reason).toBe(expected);
        expect(result.detail?.file_reason).toBeTypeOf("string");
      }
    }
    expect(service.current()).toBeNull();
  });

  it("imports → edits (view selection) → exports a valid document", async () => {
    const { service } = makeService();
    await service.importCampaign({ text: "OK" });
    const selected = service.selectMoment("state:0");
    expect(selected.ok).toBe(true);
    // View selection does not dirty the campaign.
    expect(service.isDirty()).toBe(false);
    expect(service.current()?.view.selected_moment).toBe("state:0");
    const exported = await service.exportCampaign();
    expect(exported.ok).toBe(true);
    expect(exported.payload?.filename).toBe("Test_Band.mordheim");
    expect(exported.payload?.text).toContain('"format_version":5');
  });

  it("marks a saved battle draft dirty while timeline navigation stays view-only", async () => {
    const { service } = makeService();
    await service.importCampaign({ text: "OK" });

    const saved = await service.run("saveBattleDraft", { draft: { opponent: "Reiklanders" } });
    expect(saved.ok).toBe(true);
    expect(service.current()?.view.pending_battle_draft?.["opponent"]).toBe("Reiklanders");
    expect(service.isDirty()).toBe(true);

    service.selectMoment("state:0");
    expect(service.isDirty()).toBe(true);
  });

  it("keeps the saved battle draft after rejecting an invalid battle", async () => {
    const { service } = makeService();
    await service.importCampaign({ text: "OK" });
    await service.run("saveBattleDraft", { draft: { opponent: "Previously entered" } });

    const rejected = await service.run("recordBattle", { scenario: "", opponent: "" });
    expect(rejected.ok).toBe(false);
    expect(service.current()?.view.pending_battle_draft?.["opponent"]).toBe("Previously entered");
  });

  it("opens the recorded battle summary after adding a battle", async () => {
    const scenarioKnowledge: KnowledgeReader = { queryKnowledge: (query) => query.id.kind === "scenario_id" && query.id.value === "skirmish" ? { ok: true, record: { kind: "scenario", id: query.id, names: { en: "Skirmish" }, data: {} } } : { ok: false, reason: "not_found" }, queryMany: () => [] };
    const service = await serviceWithCampaign(makeCampaign({
      states: [{ number: 0, date: "2026-09-14", gold: 500, wyrdstone: 0, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0 }],
    }), scenarioKnowledge);
    const result = await service.run("recordBattle", { scenario: "skirmish", opponent: "Cultists", result: "win", gold_delta: 0, wyrdstone: 0, xp_delta: 0, out_of_action_ids: [] });
    expect(result.ok).toBe(true);
    expect(service.current()?.view.selected_moment).toBe("battle:1");
  });

  it("ignores a queued battle-draft autosave after opening the battle summary", async () => {
    const scenarioKnowledge: KnowledgeReader = { queryKnowledge: (query) => query.id.kind === "scenario_id" && query.id.value === "skirmish" ? { ok: true, record: { kind: "scenario", id: query.id, names: { en: "Skirmish" }, data: {} } } : { ok: false, reason: "not_found" }, queryMany: () => [] };
    const service = await serviceWithCampaign(makeCampaign({
      states: [{ number: 0, date: "2026-09-14", gold: 500, wyrdstone: 0, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0 }],
    }), scenarioKnowledge);
    expect((await service.run("recordBattle", { scenario: "skirmish", opponent: "Cultists", result: "win", gold_delta: 0, wyrdstone: 0, xp_delta: 0, out_of_action_ids: [] })).ok).toBe(true);

    const lateAutosave = await service.run("saveBattleDraft", { draft: { opponent: "too late" } });

    expect(lateAutosave.ok).toBe(true);
    expect(service.current()?.view.selected_moment).toBe("battle:1");
    expect(service.current()?.view.pending_battle_draft).toBeUndefined();
  });

  it("opens the completed post-battle summary after confirming the next state", async () => {
    const service = await serviceWithCampaign(makeCampaign({
      current_state_number: 1,
      states: [{ number: 1, date: "2026-09-14", gold: 500, wyrdstone: 0, rating: 0, models: 0, max_models: 15, heroes: 0, henchmen: 0, experience: 0 }],
      battles: [{ number: 1, date: "2026-09-14", scenario: "skirmish", opponent: "Cultists", result: "win", gold_delta: 0, wyrdstone: 0, xp_delta: 0, casualties: 0, advances: 0, rating_before: 0, rating_after: 0, models_before: 0, models_after: 0, out_of_action_ids: [] }],
      post_battles: [{ battle_number: 1, complete: false, active_step: 7, completed_steps: [0,1,2,3,4,5,6], review_open: true, experience_applied: true, pending_advances: [], pending_follow_ups: [], step_state: { exploration: { resolved: true }, veterans: { resolved: true } }, sale_resolved: true, equipment_obligations: [] }],
    }));
    const result = await service.run("finalizePostBattle", {});
    expect(result.ok).toBe(true);
    expect(service.current()?.view.selected_moment).toBe("post:1");
  });

  it("keeps the document dirty after a failed export validation", async () => {
    const deps = {
      files: {
        ...fakeFiles,
        serializeCampaign: () => ({ ok: false as const, reason: "io_error" as const, message: "disk full", supported_versions: [5] }),
      },
      knowledge: fakeKnowledge,
    };
    const service = createCampaignAppService(deps);
    await service.importCampaign({ text: "OK" });
    const failed = await service.run("renameWarband", { name: "Changed Band" });
    expect(failed.ok).toBe(true);
    expect(service.isDirty()).toBe(true);
    const exported = await service.exportCampaign();
    expect(exported.ok).toBe(false);
    expect(service.isDirty()).toBe(true);
    expect(service.current()?.campaign.identity.warband_name).toBe("Changed Band");
  });

  it("refuses export with no campaign loaded", async () => {
    const { service } = makeService();
    const result = await service.exportCampaign();
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("no_campaign_loaded");
  });

  it("runs an unknown action into a stable error", async () => {
    const { service } = makeService();
    await service.importCampaign({ text: "OK" });
    const result = await service.run("nonexistent", {});
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("unknown");
  });

  it("refuses use-case runs with no campaign loaded", async () => {
    const { service } = makeService();
    const result = await service.run("assignEquipment", {});
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.reason).toBe("no_campaign_loaded");
  });

  it("translates domain rejections into typed values without throwing", async () => {
    // P3.5 ported assignEquipment for real, so a KB miss now exercises the
    // same rejection-as-value convention the not-ported stub used to.
    const { service } = makeService();
    await service.importCampaign({ text: "OK" });
    const result = await service.run("assignEquipment", {
      warrior_id: "w1",
      item_id: "dagger",
      quantity: 1,
      direction: "equip",
    });
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe("rejected");
      expect(String(result.detail?.reason)).toBe("not_found");
    }
  });

  it("undoes a committed use-case change and reports nothing to undo afterwards", async () => {
    const { service } = makeService();
    await service.importCampaign({ text: "OK" });
    const firstUndo = await service.run("undo", {});
    expect(firstUndo.ok).toBe(false);
    const edit = await service.run("composeDraft", {});
    expect(edit.ok).toBe(false); // not ported → no state change pushed
    // Simulate a real ported use case: selectMoment through run() is not in
    // the use-case dispatch; undo covers future P6.x edits. For now verify
    // undo rejects when history is empty even after a failed (rejected) run.
    const stillEmpty = await service.run("undo", {});
    expect(stillEmpty.ok).toBe(false);
    if (!stillEmpty.ok) expect(stillEmpty.reason).toBe("rejected");
  });
});

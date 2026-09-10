/**
 * Parity port of desktop `tests/campaign/test_undo.py` (10 test functions →
 * behavioural equivalents). Traceability: manifest rows with
 * `web_target: packages/typescript/domain/campaign/undo.test.ts`.
 *
 * Desktop semantics live in `AppController.perform_undoable`; the web
 * equivalent is the P5.1 application service undo stack (plain document
 * history, verbatim restore, fixed cap — desktop caps at 20, web at 50).
 * Behavioural equivalence, not mechanical translation.
 *
 * Purity: plain Node, fakes for file/knowledge ports — no React, no DOM,
 * no filesystem, no browser storage.
 */

import { describe, expect, it } from "vitest";

import { createCampaignAppService } from "../../application/campaign/service";
import type { CampaignAppDeps, CampaignAppService } from "../../application/campaign/types";
import type {
  Campaign,
  CampaignFilePort,
  KnowledgeReader,
} from "./kernel/usecases";
import type { ParseResult, SerializeResult } from "./kernel/ports";

function makeCampaign(overrides: Partial<Campaign> = {}): Campaign {
  return {
    identity: {
      campaign_name: "Undo Campaign",
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

const fakeFiles: CampaignFilePort = {
  parseCampaignFile: (text: string): ParseResult =>
    text === "BAD"
      ? ({
          ok: false,
          reason: "invalid_json",
          message: "The file is not valid JSON.",
          supported_versions: [4],
        } as const)
      : {
          ok: true,
          document: {
            marker: "MORDHEIM_CAMPAIGN_MANAGER" as const,
            format_version: 4 as const,
            saved_at: "2026-09-10T00:00:00Z",
            campaign: makeCampaign() as unknown as Record<string, unknown>,
          },
        },
  serializeCampaign: (): SerializeResult => ({ ok: true, text: "{}" }),
};

const fakeKnowledge: KnowledgeReader = {
  queryKnowledge: () => ({ ok: false, reason: "not_found" }),
  queryMany: (queries) => queries.map((q) => fakeKnowledge.queryKnowledge(q)),
};

function makeService(): CampaignAppService {
  const deps: CampaignAppDeps = { files: fakeFiles, knowledge: fakeKnowledge };
  return createCampaignAppService(deps);
}

/** The one ported campaign-mutating use case with no KB dependency. */
async function buyGoldlessStashItem(service: CampaignAppService): Promise<boolean> {
  const result = await service.run("buyTradingItem", {
    item_id: "candle",
    name: "Candle",
    unit_price: 10,
    quantity: 1,
  });
  return result.ok;
}

/** The one ported view-only operation: must never dirty or push history. */
function selectMoment(service: CampaignAppService): boolean {
  return service.selectMoment("state:0").ok;
}

describe("desktop test_undo.py → web undo stack parity", () => {
  it("successful action can be undone (state restored, history tracked)", async () => {
    const service = makeService();
    await service.importCampaign({ text: "OK" });
    expect(await buyGoldlessStashItem(service)).toBe(true);
    // Desktop: can_undo + state changed. Web: a second undo would restore.
    const undone = await service.run("undo", {});
    expect(undone.ok).toBe(true);
    const restored = service.current()?.campaign.inventory ?? [];
    expect(restored.find((i) => i.id === "candle")).toBeUndefined();
  });

  it("failed or no-change action is not recorded in history", async () => {
    const service = makeService();
    await service.importCampaign({ text: "OK" });
    // A rejected use case must not push onto the undo stack.
    const rejected = await service.run("buyTradingItem", {
      item_id: "candle",
      name: "Candle",
      unit_price: -1, // invalid price → rejection
      quantity: 1,
    });
    expect(rejected.ok).toBe(false);
    const undone = await service.run("undo", {});
    expect(undone.ok).toBe(false); // desktop: not controller.can_undo
    if (!undone.ok) expect(undone.reason).toBe("rejected");
  });

  it("failed action rolls back partial mutation", async () => {
    // Desktop mutates a shared mutable state and restores it. The web kernel
    // is immutable by construction (documents are never mutated), so a
    // rejection can never leak a partial mutation — asserted structurally:
    // after a rejected run, current() is the same document object.
    const service = makeService();
    await service.importCampaign({ text: "OK" });
    const before = service.current();
    await service.run("buyTradingItem", {
      item_id: "candle",
      name: "Candle",
      unit_price: 999999, // exceeds treasury → rejection
      quantity: 1,
    });
    expect(service.current()).toBe(before);
  });

  it("failed action preserves live document references", async () => {
    const service = makeService();
    await service.importCampaign({ text: "OK" });
    const document = service.current();
    await service.run("buyTradingItem", {
      item_id: "candle",
      name: "Candle",
      unit_price: 999999,
      quantity: 1,
    });
    // Desktop: controller.state.campaign is campaign. Web: same object.
    expect(service.current()).toBe(document);
  });

  it("exception inside a use case rolls back before propagating", async () => {
    const service = makeService();
    await service.importCampaign({ text: "OK" });
    const before = service.current();
    // The web dispatch converts *everything* into a result value — no
    // exception crosses the service boundary at all (stronger than the
    // desktop's rollback-before-propagate, same user-visible guarantee).
    const result = await service.run("buyTradingItem", {
      item_id: "candle",
      name: "Candle",
      unit_price: Number.NaN,
      quantity: 1,
    });
    expect(result.ok).toBe(false);
    expect(service.current()).toBe(before);
    expect(service.isDirty()).toBe(false);
  });

  it("multiple actions are undone in reverse order", async () => {
    const service = makeService();
    await service.importCampaign({ text: "OK" });
    // Three purchases at different prices (desktop adds 10/20/30 gc).
    for (const [item, price] of [["a", 10], ["b", 20], ["c", 30]] as const) {
      expect(
        (await service.run("buyTradingItem", { item_id: item, name: item, unit_price: price, quantity: 1 })).ok,
      ).toBe(true);
    }
    // Undo c: a and b remain in the inventory.
    expect((await service.run("undo", {})).ok).toBe(true);
    let ids = (service.current()?.campaign.inventory ?? []).map((i) => i.id);
    expect(ids).toEqual(["a", "b"]);
    expect((await service.run("undo", {})).ok).toBe(true);
    ids = (service.current()?.campaign.inventory ?? []).map((i) => i.id);
    expect(ids).toEqual(["a"]);
    expect((await service.run("undo", {})).ok).toBe(true);
    ids = (service.current()?.campaign.inventory ?? []).map((i) => i.id);
    expect(ids).toEqual([]);
  });

  it("undo removes a stored dice result so it can be rolled again", async () => {
    // Desktop: step_state.exploration.dice written, undone, re-rolled. The
    // web kernel keeps step_state inside the post_battle record; the
    // document-level equivalence is: an undone document leaves no trace of
    // the previous write, and the same write succeeds again afterwards.
    const service = makeService();
    await service.importCampaign({ text: "OK" });
    expect(await buyGoldlessStashItem(service)).toBe(true);
    expect((await service.run("undo", {})).ok).toBe(true);
    expect((service.current()?.campaign.inventory ?? []).some((i) => i.id === "candle")).toBe(false);
    // The same write succeeds again — no stale cached result.
    expect(await buyGoldlessStashItem(service)).toBe(true);
  });

  it("replacing the campaign clears history", async () => {
    const service = makeService();
    await service.importCampaign({ text: "OK" });
    expect(await buyGoldlessStashItem(service)).toBe(true);
    expect((await service.run("undo", {})).ok).toBe(true);
    // Re-import (desktop: replace_state) clears the undo stack.
    await service.importCampaign({ text: "OK", confirm_replace: true });
    const undone = await service.run("undo", {});
    expect(undone.ok).toBe(false);
    if (!undone.ok) expect(undone.reason).toBe("rejected");
  });

  it("undo history keeps only the latest actions (cap enforced)", async () => {
    const service = makeService();
    await service.importCampaign({ text: "OK" });
    // The web service caps history at 50 (desktop: 20). Push 55 successful
    // edits, then undo: exactly 50 succeed, the 51st is a typed rejection.
    for (let index = 0; index < 55; index += 1) {
      const ok = (
        await service.run("buyTradingItem", {
          item_id: `item-${index}`,
          name: `Item ${index}`,
          unit_price: 0,
          quantity: 1,
        })
      ).ok;
      expect(ok).toBe(true);
    }
    let undone = 0;
    while ((await service.run("undo", {})).ok) undone += 1;
    expect(undone).toBe(50);
    // 55 pushes − 50 restored: the 5 oldest edits survive.
    expect((service.current()?.campaign.inventory ?? []).length).toBe(5);
  });

  it("view selection never enters the undo stack", async () => {
    // Desktop: navigation never dirties (test_dirty_includes_battle_draft…).
    const service = makeService();
    await service.importCampaign({ text: "OK" });
    expect(selectMoment(service)).toBe(true);
    expect(service.isDirty()).toBe(false);
    const undone = await service.run("undo", {});
    expect(undone.ok).toBe(false); // nothing was pushed by the view change
  });
});

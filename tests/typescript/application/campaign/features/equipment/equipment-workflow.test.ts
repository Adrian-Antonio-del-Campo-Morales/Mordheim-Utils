/**
 * P6.3 acceptance tests: the equipment feature workflow over the real
 * application service (real P3.2 file port, neutral KB) — inventory read
 * model with equipped/stash splits, assign/withdraw conserving
 * `owned = equipped + stash`, rejections as typed values.
 */
import { describe, expect, it } from "vitest";

import { CampaignFileV5Adapter } from "@adapters/campaign-file/index";
import type { Campaign } from "@domain/campaign/kernel/state";
import type { KnowledgeReader as KnowledgeReaderPort } from "@domain/campaign/kernel/ports";
import { createCampaignAppService } from "@app/campaign/service";
import type { CampaignAppService } from "@app/campaign/types";
import { equipmentOverview } from "@app/campaign/features/equipment/equipment-workflow";

const neutralKnowledge: KnowledgeReaderPort = {
  queryKnowledge: () => ({ ok: false, reason: "not_found" }),
  queryMany: (queries) => queries.map((q) => neutralKnowledge.queryKnowledge(q)),
};

function campaign(): Campaign {
  return {
    identity: {
      campaign_name: "Gear Campaign",
      warband_name: "Armoury Band",
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
    resources: { stash_value: 10, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 1,
    warriors: [
      {
        id: "w1",
        name: "Sigrid",
        profile_name: "Sigmarite Matriarch",
        kind: "hero",
        stats: { M: 4, WS: 4 },
        equipment: [
          { item_id: "dagger", name: "Dagger", quantity: 1, acquisition: "fixed" },
        ],
        skills: [],
        experience: 8,
        cost: 65,
      },
      {
        id: "w2",
        name: "Greta",
        profile_name: "Sister Superior",
        kind: "hero",
        stats: { M: 4, WS: 3 },
        equipment: [],
        skills: [],
        experience: 4,
        cost: 45,
      },
    ],
    battles: [],
    states: [
      {
        number: 1,
        date: "Cyber 1",
        gold: 300,
        wyrdstone: 0,
        rating: 100,
        models: 6,
        max_models: 15,
        heroes: 3,
        henchmen: 3,
        experience: 12,
      },
    ],
    post_battles: [],
    inventory: [
      {
        id: "mace",
        name: "Mace",
        category: "close-combat-weapon",
        owned: 3,
        equipped: 0,
        stash: 3,
        value: 5,
      },
    ],
    special_rules: [],
    manual_log: [],
  };
}

function makeService(): CampaignAppService {
  return createCampaignAppService({
    files: new CampaignFileV5Adapter(),
    knowledge: neutralKnowledge,
  });
}

async function loadedService(): Promise<CampaignAppService> {
  const service = makeService();
  const raw = {
    marker: "MORDHEIM_CAMPAIGN_MANAGER",
    format_version: 5,
    saved_at: "2026-09-09T12:00:00Z",
    campaign: campaign() as unknown as Record<string, unknown>,
    view: {},
  };
  const imported = await service.importCampaign({ text: JSON.stringify(raw) });
  expect(imported.ok).toBe(true);
  return service;
}

describe("P6.3: equipment overview read model", () => {
  it("lists rows with the equipped/stash split and warrior entries", async () => {
    const service = await loadedService();
    const overview = equipmentOverview(service.current()!);
    expect(overview.rows).toEqual([
      {
        id: "mace",
        name: "Mace",
        category: "close-combat-weapon",
        owned: 3,
        equipped: 0,
        stash: 3,
        value: 5,
        transferable: true,
      },
    ]);
    expect(overview.warriors.map((w) => w.warrior_name)).toEqual(["Sigrid", "Greta"]);
    // Sigrid's dagger is fixed (profile equipment), not withdrawable.
    const sigrid = overview.warriors[0];
    expect(sigrid.entries).toEqual([
      { item_id: "dagger", name: "Dagger", quantity: 1, fixed: true },
    ]);
  });
});

describe("P6.3: assign & withdraw via the service", () => {
  it("equips from the stash conserving owned = equipped + stash and dirties", async () => {
    const service = await loadedService();
    const result = await service.run("assignEquipment", {
      warrior_id: "w2",
      item_id: "mace",
      quantity: 2,
      direction: "equip",
    });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const item = result.document.campaign.inventory.find((i) => i.id === "mace");
    expect(item).toMatchObject({ owned: 3, equipped: 2, stash: 1 });
    const greta = result.document.campaign.warriors.find((w) => w.id === "w2");
    expect(greta?.equipment).toEqual([
      { item_id: "mace", name: "Mace", quantity: 2, acquisition: "stash_assignment", unit_cost: 5, acquisition_costs: [5, 5] },
    ]);
    // Real campaign mutation → dirty.
    expect(service.isDirty()).toBe(true);
  });

  it("withdraws equipped units back to the stash", async () => {
    const service = await loadedService();
    expect(
      (
        await service.run("assignEquipment", {
          warrior_id: "w2",
          item_id: "mace",
          quantity: 2,
          direction: "equip",
        })
      ).ok,
    ).toBe(true);
    const result = await service.run("assignEquipment", {
      warrior_id: "w2",
      item_id: "mace",
      quantity: 1,
      direction: "stash",
    });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const item = result.document.campaign.inventory.find((i) => i.id === "mace");
    expect(item).toMatchObject({ owned: 3, equipped: 1, stash: 2 });
    const greta = result.document.campaign.warriors.find((w) => w.id === "w2");
    expect(greta?.equipment).toEqual([
      { item_id: "mace", name: "Mace", quantity: 1, acquisition: "stash_assignment", unit_cost: 5, acquisition_costs: [5] },
    ]);
  });

  it("rejects over-drawing the stash as a typed value", async () => {
    const service = await loadedService();
    const result = await service.run("assignEquipment", {
      warrior_id: "w2",
      item_id: "mace",
      quantity: 99,
      direction: "equip",
    });
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(result.reason).toBe("rejected");
      expect(String(result.detail?.reason)).toBe("limit_violated");
    }
  });

  it("refuses to withdraw a fixed (profile) entry", async () => {
    const service = await loadedService();
    const result = await service.run("assignEquipment", {
      warrior_id: "w1",
      item_id: "dagger",
      quantity: 1,
      direction: "stash",
    });
    expect(result.ok).toBe(false);
    if (!result.ok) {
      expect(String(result.detail?.reason)).toBe("limit_violated");
    }
  });

  it("undoes an assignment through the service undo stack", async () => {
    const service = await loadedService();
    await service.run("assignEquipment", {
      warrior_id: "w2",
      item_id: "mace",
      quantity: 1,
      direction: "equip",
    });
    expect(service.isDirty()).toBe(true);
    const undone = await service.run("undo", {});
    expect(undone.ok).toBe(true);
    expect(service.isDirty()).toBe(false);
    const item = service.current()!.campaign.inventory.find((i) => i.id === "mace");
    expect(item).toMatchObject({ owned: 3, equipped: 0, stash: 3 });
  });
});

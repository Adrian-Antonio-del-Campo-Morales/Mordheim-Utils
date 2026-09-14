/**
 * P6.6 acceptance tests: the advances feature over the real application
 * service (real P3.2 file port, neutral KB) — pending read model, applying
 * stat/skill choices, typed rejections, and export round-trip of the
 * advanced warrior snapshot.
 */
import { describe, expect, it } from "vitest";

import { CampaignFileV5Adapter } from "../../../../adapters/campaign-file/index";
import type { Campaign } from "../../../../domain/campaign/kernel/state";
import type { KnowledgeReader as KnowledgeReaderPort } from "../../../../domain/campaign/kernel/ports";
import { createCampaignAppService } from "../../service";
import type { CampaignAppService } from "../../types";
import { advancesOverview } from "./advances-workflow";

const neutralKnowledge: KnowledgeReaderPort = {
  queryKnowledge: () => ({ ok: false, reason: "not_found" }),
  queryMany: (queries) => queries.map((q) => neutralKnowledge.queryKnowledge(q)),
};

function campaign(): Campaign {
  return {
    identity: {
      campaign_name: "Advances Campaign",
      warband_name: "Veteran Band",
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
        // Hero XP 40 reaches first two desktop thresholds.
        id: "w1",
        name: "Sigrid",
        profile_name: "Sigmarite Matriarch",
        kind: "hero",
        stats: { M: 4, WS: 4, S: 3 },
        equipment: [],
        skills: [],
        experience: 40,
        cost: 65,
      },
      {
        // XP 4 is below first hero threshold.
        id: "w2",
        name: "Greta",
        profile_name: "Sister Superior",
        kind: "hero",
        stats: { M: 4, WS: 4, S: 3 },
        equipment: [],
        skills: ["strong-willed"],
        experience: 4,
        cost: 45,
        stat_advances: { WS: 1 },
      },
      {
        // Hireling: never eligible.
        id: "h1",
        name: "Warrior for Hire",
        profile_name: "Hired Sword",
        kind: "hireling",
        stats: { M: 4, WS: 3 },
        equipment: [],
        skills: [],
        experience: 12,
        cost: 35,
        hireling_rating: 15,
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
    inventory: [],
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

describe("P6.6: pending-advance read model", () => {
  it("computes earned/taken/pending per warrior from XP and the ledger", async () => {
    const service = await loadedService();
    const overview = advancesOverview(service.current()!);
    const byId = new Map(overview.warriors.map((w) => [w.warrior_id, w]));

    // Sigrid: XP 40 reaches hero thresholds 20 and 40.
    expect(byId.get("w1")).toMatchObject({ earned: 2, taken: 0, pending: 2, eligible: true });
    // Greta: XP 4 earns no advance; 1 stat + 1 skill
    // taken → 0 pending (over-taken clamps at 0).
    expect(byId.get("w2")).toMatchObject({
      earned: 0,
      taken: 2,
      pending: 0,
      learned_skills: ["strong-willed"],
    });
    // Hireling: never eligible, never pending.
    expect(byId.get("h1")).toMatchObject({ eligible: false, pending: 0 });
    expect(overview.total_pending).toBe(2);
  });
});

describe("P6.6: applying choices via the service", () => {
  it("applies a stat advance: stats +1 and ledger updated, dirty set", async () => {
    const service = await loadedService();
    const result = await service.run("applyAdvance", {
      warrior_id: "w1",
      table: "common",
      choice: "stat:WS",
    });
    expect(result.ok).toBe(true);
    if (!result.ok) return;
    const sigrid = result.document.campaign.warriors.find((w) => w.id === "w1");
    expect(sigrid?.stats["WS"]).toBe(5);
    expect(sigrid?.stat_advances).toEqual({ WS: 1 });
    expect(service.isDirty()).toBe(true);

    // The read model reflects the taken advance.
    const overview = advancesOverview(service.current()!);
    expect(overview.warriors.find((w) => w.warrior_id === "w1")).toMatchObject({
      taken: 1,
      pending: 1,
    });
  });

  it("applies a skill advance and rejects duplicates as a typed conflict", async () => {
    const service = await loadedService();
    expect(
      (
        await service.run("applyAdvance", {
          warrior_id: "w1",
          table: "common",
          choice: "skill:step-aside",
        })
      ).ok,
    ).toBe(true);
    const duplicate = await service.run("applyAdvance", {
      warrior_id: "w1",
      table: "common",
      choice: "skill:step-aside",
    });
    expect(duplicate.ok).toBe(false);
    if (!duplicate.ok) {
      expect(duplicate.reason).toBe("rejected");
      expect(String(duplicate.detail?.reason)).toBe("conflict");
    }
  });

  it("rejects malformed choices and unearned advances as typed values", async () => {
    const service = await loadedService();
    const malformed = await service.run("applyAdvance", {
      warrior_id: "w1",
      table: "common",
      choice: "become-invincible",
    });
    expect(malformed.ok).toBe(false);
    if (!malformed.ok) {
      expect(String(malformed.detail?.reason)).toBe("invalid_input");
    }
    const unearned = await service.run("applyAdvance", {
      warrior_id: "w2",
      table: "common",
      choice: "stat:S",
    });
    expect(unearned.ok).toBe(false);
    if (!unearned.ok) {
      expect(String(unearned.detail?.reason)).toBe("prerequisite_missing");
    }
    const hireling = await service.run("applyAdvance", {
      warrior_id: "h1",
      table: "common",
      choice: "stat:S",
    });
    expect(hireling.ok).toBe(false);
    if (!hireling.ok) {
      expect(String(hireling.detail?.reason)).toBe("invalid_input");
    }
  });
});

describe("P6.6: export round-trip preserves the advanced snapshot", () => {
  it("stat advances survive export → reimport verbatim", async () => {
    const service = await loadedService();
    expect(
      (
        await service.run("applyAdvance", {
          warrior_id: "w1",
          table: "common",
          choice: "stat:WS",
        })
      ).ok,
    ).toBe(true);
    const exported = await service.exportCampaign();
    expect(exported.ok).toBe(true);
    if (!exported.ok || !exported.payload) return;

    const second = makeService();
    const reimported = await second.importCampaign({ text: exported.payload.text });
    expect(reimported.ok).toBe(true);
    const sigrid = second
      .current()!
      .campaign.warriors.find((w) => w.id === "w1");
    expect(sigrid?.stats["WS"]).toBe(5);
    expect(sigrid?.stat_advances).toEqual({ WS: 1 });
  });
});

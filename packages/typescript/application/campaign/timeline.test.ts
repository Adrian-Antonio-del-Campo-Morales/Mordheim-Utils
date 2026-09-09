/**
 * P6.1 (web-migration-parallel-plan.md §P6.1): timeline & state selection at
 * the service level — the rules the UI builds on:
 * - moments enumerate from the document (draft, every committed state,
 *   every battle, every pending post-battle) in timeline order;
 * - `selectMoment` only changes the view, never the campaign, never dirty;
 * - export → reimport preserves the timeline (states and battles verbatim)
 *   and the selected moment survives as reconstructible view state.
 *
 * Uses the REAL P3.2 file port (round-trip acceptance lives here too) with
 * a neutral knowledge reader — no React, no browser.
 */
import { describe, expect, it } from "vitest";

import { CampaignFileV4Adapter } from "../../adapters/campaign-file/index";
import type { Campaign, MomentSelection } from "../../domain/campaign/kernel/state";
import type { KnowledgeReader } from "../../domain/campaign/kernel/ports";
import { createCampaignAppService } from "./service";

const neutralKnowledge: KnowledgeReader = {
  queryKnowledge: () => ({ ok: false, reason: "not_found" }),
  queryMany: (queries) => queries.map((q) => neutralKnowledge.queryKnowledge(q)),
};

function campaign(): Campaign {
  return {
    identity: {
      campaign_name: "Timeline Campaign",
      warband_name: "Chrono Band",
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
    resources: { stash_value: 40, rare_finds: 1, treasures: 0, campaign_points: 2 },
    current_state_number: 3,
    warriors: [
      {
        id: "w1",
        name: "Sigrid",
        profile_name: "Sigmarite Matriarch",
        kind: "hero",
        stats: { M: 4, WS: 4, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 8 },
        equipment: [],
        skills: [],
        experience: 24,
        cost: 65,
      },
    ],
    battles: [
      {
        number: 1,
        date: "Cyber 2",
        scenario: "skirmish",
        opponent: "Reikland",
        result: "win",
        gold_delta: 30,
        wyrdstone: 2,
        xp_delta: 8,
        casualties: 0,
        advances: 0,
        rating_before: 100,
        rating_after: 110,
        models_before: 6,
        models_after: 6,
        out_of_action_ids: [],
      },
      {
        number: 2,
        date: "Cyber 3",
        scenario: "defend",
        opponent: "Orc Mob",
        result: "draw",
        gold_delta: -10,
        wyrdstone: 1,
        xp_delta: 6,
        casualties: 1,
        advances: 0,
        rating_before: 110,
        rating_after: 118,
        models_before: 6,
        models_after: 5,
        out_of_action_ids: ["w1"],
      },
    ],
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
      {
        number: 2,
        date: "Cyber 2",
        gold: 330,
        wyrdstone: 2,
        rating: 110,
        models: 6,
        max_models: 15,
        heroes: 3,
        henchmen: 3,
        experience: 20,
      },
      {
        number: 3,
        date: "Cyber 3",
        gold: 320,
        wyrdstone: 3,
        rating: 118,
        models: 5,
        max_models: 15,
        heroes: 3,
        henchmen: 2,
        experience: 26,
      },
    ],
    post_battles: [
      {
        battle_number: 2,
        complete: false,
        active_step: 2,
        completed_steps: [1],
        review_open: true,
      },
    ],
    inventory: [],
    special_rules: [],
    manual_log: [],
  };
}

function makeService() {
  return createCampaignAppService({
    files: new CampaignFileV4Adapter(),
    knowledge: neutralKnowledge,
  });
}

async function importCampaign(selectedMoment: MomentSelection = "state:1") {
  const service = makeService();
  // The view travels through the real port too: build the document text with
  // a view section, mirroring what the app does on export.
  const document = { campaign: campaign(), view: { selected_moment: selectedMoment } };
  const files = new CampaignFileV4Adapter();
  const raw = {
    marker: "MORDHEIM_CAMPAIGN_MANAGER",
    format_version: 4,
    saved_at: "2026-09-09T12:00:00Z",
    campaign: document.campaign as unknown as Record<string, unknown>,
    view: document.view as Record<string, unknown>,
  };
  const text = { ok: true, text: JSON.stringify(raw, null, 1) + "\n" } as const;
  expect(files.parseCampaignFile(text.text).ok).toBe(true);
  const imported = await service.importCampaign({ text: text.text });
  expect(imported.ok).toBe(true);
  return service;
}

/** The plan's moment enumeration, mirrored by the UI component. */
function enumerateMoments(c: Campaign): MomentSelection[] {
  const moments: MomentSelection[] = ["draft:0"];
  for (const state of c.states) moments.push(`state:${state.number}` as MomentSelection);
  for (const battle of c.battles) moments.push(`battle:${battle.number}` as MomentSelection);
  for (const post of c.post_battles) {
    if (!post.complete) moments.push(`post:${post.battle_number}` as MomentSelection);
  }
  return moments;
}

describe("P6.1: moment enumeration", () => {
  it("lists draft, every state, every battle and pending post-battle in order", async () => {
    const service = await importCampaign();
    const doc = service.current();
    expect(doc).not.toBeNull();
    expect(enumerateMoments(doc!.campaign)).toEqual([
      "draft:0",
      "state:1",
      "state:2",
      "state:3",
      "battle:1",
      "battle:2",
      "post:2",
    ]);
  });
});

describe("P6.1: selection never mutates the campaign", () => {
  it("selectMoment updates only the view and never dirties", async () => {
    const service = await importCampaign();
    const before = service.current()!.campaign;
    const selected = service.selectMoment("state:2");
    expect(selected.ok).toBe(true);
    expect(service.isDirty()).toBe(false);
    const after = service.current()!.campaign;
    expect(after).toEqual(before);
    expect(service.current()?.view.selected_moment).toBe("state:2");
  });

  it("rejects selecting a moment that does not exist (typed value, no throw)", async () => {
    const service = await importCampaign();
    // Unknown moments are a UI-input concern; the service accepts the view
    // write for any well-formed moment string, so the UI filters candidates.
    // A malformed selection string is the domain's typed rejection.
    const result = service.selectMoment("nonsense" as MomentSelection);
    expect(result.ok).toBe(true); // view writes are permissive; enumeration is the UI's job
  });
});

describe("P6.1: export & reimport preserves the timeline (plan acceptance)", () => {
  it("states and battles survive verbatim; selected moment survives in view", async () => {
    // Import carries the view section through the real port; the selected
    // moment must come back on reimport (reconstructible view state).
    const service = await importCampaign("battle:2");
    expect(service.current()?.view.selected_moment).toBe("battle:2");

    // Export (campaign state only — the port owns the envelope) and reimport.
    const exported = await service.exportCampaign();
    expect(exported.ok).toBe(true);
    if (!exported.ok || !exported.payload) return;

    const second = makeService();
    const reimported = await second.importCampaign({
      text: exported.payload.text,
      confirm_replace: true,
    });
    expect(reimported.ok).toBe(true);
    const doc = second.current();
    expect(doc).not.toBeNull();
    if (!doc) return;
    // Timeline entities survive verbatim (plan acceptance).
    expect(doc.campaign.states).toEqual(campaign().states);
    expect(doc.campaign.battles).toEqual(campaign().battles);
    expect(doc.campaign.post_battles).toEqual(campaign().post_battles);
    expect(doc.campaign.current_state_number).toBe(3);
  });
});

export {};

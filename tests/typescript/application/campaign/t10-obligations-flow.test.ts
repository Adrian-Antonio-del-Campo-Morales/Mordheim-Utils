/**
 * T10 — campaign obligations through the real application service.
 *
 * Every case goes through `createCampaignAppService`, the seam the web
 * interface consumes: the document enters the way the interface loads it
 * (import + domain validation) and leaves it the way the interface exports it
 * (v5 payload). The four mechanisms covered here are the ones T09 handed to T10:
 *
 * - the warband-creation roll (`imperial-noble--family-heirloom`);
 * - the printed market scope (`repeater_pistol_moh`) and the unique find that is
 *   not sold (`runic_attlas_plate_mail`, granted by the exploration chart under
 *   its canonical item id);
 * - the bounded band special-skill tables on the advance flow;
 * - the Rout-test roster facts source (the exemption the campaign publishes).
 *
 * Purity: plain Node with the real adapter and the generated artefact.
 */
import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";

import { CampaignFileV5Adapter, parseCampaignFileDetailed } from "@adapters/campaign-file";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { createCampaignAppService } from "@app/campaign/service";
import { continueExploration } from "@app/campaign/features/exploration/exploration-workflow";
import type { Campaign } from "@domain/campaign/kernel/usecases";

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
const adapter = new CampaignFileV5Adapter();

const KAZ = "adventurers-kaz";
const MASTERS = "masters-of-horror-sylv";
const DECISION = "campaign.creation.family-heirloom";

function baseCampaign(overrides: Partial<Campaign> & { band?: string }): Campaign {
  const { band, ...rest } = overrides;
  return {
    identity: { campaign_name: "T10", warband_name: "Band", warband_type: "Band", band_id: band ?? KAZ, mercenary_variant: null },
    configuration: { is_draft: false, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
    resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 1,
    warriors: [],
    battles: [],
    states: [{ number: 1, date: "2026-09-27", gold: 500, wyrdstone: 0, rating: 0, models: 1, max_models: 15, heroes: 1, henchmen: 0, experience: 0 }],
    post_battles: [],
    inventory: [],
    special_rules: [],
    manual_log: [],
    ...rest,
    ...(rest.identity ? { identity: { ...rest.identity } } : {}),
  };
}

function warrior(id: string, profileId: string, extra: Record<string, unknown> = {}) {
  return {
    id,
    name: `Warrior ${id}`,
    profile_name: profileId,
    kind: "hero",
    stats: {},
    equipment: [],
    skills: [],
    experience: 0,
    cost: 0,
    quantity: 1,
    profile_id: profileId,
    ...extra,
  };
}

function pendingPost(battleNumber: number, extra: Record<string, unknown> = {}) {
  return {
    battle_number: battleNumber,
    complete: false,
    active_step: 1,
    completed_steps: [],
    review_open: false,
    experience_applied: true,
    pending_advances: [],
    gold_delta: 0,
    wyrdstone_delta: 0,
    pending_follow_ups: [],
    step_state: {},
    event_log: [],
    ...extra,
  };
}

function battle(number: number, extra: Record<string, unknown> = {}) {
  return {
    number,
    date: "2026-09-27",
    scenario: "skirmish",
    opponent: "Audit",
    result: "win",
    gold_delta: 0,
    wyrdstone: 0,
    xp_delta: 0,
    casualties: 0,
    advances: 0,
    rating_before: 0,
    rating_after: 0,
    models_before: 1,
    models_after: 1,
    out_of_action_ids: null,
    ...extra,
  };
}

/** Load a crafted document through the service's real import path. */
async function loadService(campaign: Campaign, reader: ArtefactKnowledgeReader) {
  const serialized = adapter.serializeCampaign(campaign);
  expect(serialized.ok, serialized.ok ? "" : serialized.message).toBe(true);
  if (!serialized.ok) throw new Error(serialized.message);
  const service = createCampaignAppService({ files: adapter, knowledge: reader });
  const imported = await service.importCampaign({ text: serialized.text });
  expect(imported.ok, imported.ok ? "" : imported.message).toBe(true);
  return service;
}

describe.skipIf(!ARTEFACT_PATH)("T10 campaign obligations (application service)", () => {
  const artefact = JSON.parse(readFileSync(ARTEFACT_PATH as string, "utf8"));
  const reader = ArtefactKnowledgeReader.from(artefact);

  it("records the creation roll, blocks the commit, and survives export/reimport", async () => {
    const campaign = baseCampaign({
      configuration: { is_draft: true, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
      current_state_number: 0,
      states: [],
      warriors: [warrior("noble", "imperial-noble")],
    });
    const service = await loadService(campaign, reader);

    const blocked = await service.run("commitInitialWarband", {});
    expect(blocked.ok).toBe(false);
    if (!blocked.ok) expect(blocked.message).toContain("Family Heirloom");

    const rolled = await service.run("resolveCreationDecision", { decision_id: DECISION, roll: 5 });
    expect(rolled.ok, rolled.ok ? "" : rolled.message).toBe(true);
    if (!rolled.ok) return;
    expect(rolled.document.campaign.special_rules.at(-1)).toMatchObject({
      decision_id: DECISION,
      outcome_id: "reroll-one-die",
      roll: 5,
    });

    const committed = await service.run("commitInitialWarband", {});
    expect(committed.ok, committed.ok ? "" : committed.message).toBe(true);

    const exported = await service.exportCampaign();
    expect(exported.ok).toBe(true);
    if (!exported.ok || !exported.payload) return;
    const parsed = parseCampaignFileDetailed(exported.payload.text);
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(parsed.campaign.special_rules).toEqual([
      expect.objectContaining({ decision_id: DECISION, outcome_id: "reroll-one-die", roll: 5, order: 1 }),
    ]);

    // Reopen the exported file: the decision is still recorded, not owed again.
    const reopened = createCampaignAppService({ files: adapter, knowledge: reader });
    expect((await reopened.importCampaign({ text: exported.payload.text })).ok).toBe(true);
    expect((await reopened.run("resolveCreationDecision", { decision_id: DECISION, roll: 3 })).ok).toBe(false);
  });

  it("lets the Masters of Horror buy the printed Repeater Pistol and refuses every other warband", async () => {
    const campaign = baseCampaign({
      band: MASTERS,
      post_battles: [pendingPost(1)],
      battles: [battle(1)],
      warriors: [warrior("scientist", "mad-scientist")],
    });
    const service = await loadService(campaign, reader);
    const bought = await service.run("buyTradingItem", { item_id: "repeater_pistol_moh", quantity: 1, unit_price: 34 });
    expect(bought.ok, bought.ok ? "" : bought.message).toBe(true);
    if (bought.ok) {
      expect(bought.document.campaign.inventory.find((row) => row.id === "repeater_pistol_moh")?.owned).toBe(1);
    }

    const outsider = await loadService(
      baseCampaign({ post_battles: [pendingPost(1)], battles: [battle(1)], warriors: [warrior("noble", "imperial-noble")] }),
      reader,
    );
    const refused = await outsider.run("buyTradingItem", { item_id: "repeater_pistol_moh", quantity: 1, unit_price: 34 });
    expect(refused.ok).toBe(false);
    if (!refused.ok) expect(refused.message).toContain("not available to this warband");

    const unique = await outsider.run("buyTradingItem", { item_id: "runic_attlas_plate_mail", quantity: 1, unit_price: 0 });
    expect(unique.ok).toBe(false);
    if (!unique.ok) expect(unique.message).toContain("not sold");
  });

  it("grants Att'la's Plate Mail on the exploration chart under its canonical id, once", async () => {
    const campaign = baseCampaign({
      battles: [battle(1)],
      warriors: [warrior("marta", "imperial-noble")],
      post_battles: [
        pendingPost(1, {
          pending_follow_ups: [
            { type: "exploration_followup", step: 2, queue: [], pending: { kind: "roll", dice_count: 1, dice_sides: 6, spec: { type: "magical_artefact" } }, messages: [] },
          ],
        }),
      ],
    });
    const rolled = continueExploration({ campaign, view: {} }, reader as never, { roll: 3 });
    expect(rolled.ok, rolled.ok ? "" : rolled.message).toBe(true);
    if (!rolled.ok) return;
    const chosen = continueExploration(rolled.document, reader as never, { hero_id: "marta" });
    expect(chosen.ok, chosen.ok ? "" : chosen.message).toBe(true);
    if (!chosen.ok) return;
    const row = chosen.document.campaign.inventory.find((item) => item.id === "runic_attlas_plate_mail");
    expect(row, JSON.stringify(chosen.document.campaign.inventory)).toBeDefined();
    expect(row?.rarity).toBe("Unique");
    expect(chosen.document.campaign.unique_reward_ids).toContain("runic_attlas_plate_mail");
    // The item reaches the bearer as the catalogue id as well.
    expect(chosen.document.campaign.warriors[0]?.equipment.map((item) => item.item_id)).toContain("runic_attlas_plate_mail");
  });

  it("bounds the band special-skill table on the advance flow", async () => {
    const pendingAdvance = (warriorId: string) => ({
      warrior_id: warriorId,
      warrior_name: warriorId,
      table: "hero",
      threshold: 2,
      roll_total: 6,
      subroll: null,
      committed: false,
      applied_label: "",
      advance_options: [{ kind: "choose_skill", characteristic: null, amount: 1 }],
    });
    const build = async (profileId: string, skillAccess: readonly string[]) => {
      const campaign = baseCampaign({
        warriors: [warrior("hero", profileId, { skill_access: skillAccess })],
        battles: [battle(1)],
        post_battles: [pendingPost(1, { pending_advances: [pendingAdvance("hero")] })],
      });
      return loadService(campaign, reader);
    };

    const elf = await build("elf", ["shooting", "special", "speed"]);
    const allowed = await elf.run("commitAdvanceChoice", { warrior_id: "hero", threshold: 2, kind: "choose_skill", skill_id: "skill.fey" });
    expect(allowed.ok, allowed.ok ? "" : allowed.message).toBe(true);
    if (allowed.ok) {
      expect(allowed.document.campaign.warriors[0]?.skills).toEqual(["Fey"]);
      expect(allowed.document.campaign.post_battles[0]?.pending_advances?.[0]?.["committed"]).toBe(true);
    }

    // A special skill the band's own list does not print is refused.
    const outside = await elf.run("commitAdvanceChoice", { warrior_id: "hero", threshold: 2, kind: "choose_skill", skill_id: "skill.monster-slayer" });
    expect(outside.ok).toBe(false);
    if (!outside.ok) expect(outside.message).toContain("not on the published special-skill list");

    // A profile the table does not name cannot use it, even holding the slot.
    const captain = await build("imperial-captain", ["combat", "special"]);
    const refused = await captain.run("commitAdvanceChoice", { warrior_id: "hero", threshold: 2, kind: "choose_skill", skill_id: "skill.fey" });
    expect(refused.ok).toBe(false);
    if (!refused.ok) expect(refused.message).toContain("imperial-captain");

    // A band whose printed list is still prose cannot grant anything: the choice
    // is refused with the code that names the gap, so the whole special catalogue
    // is never handed over. The flow opens when the canonical list is published.
    const campaign = baseCampaign({
      band: "khemri-mages",
      warriors: [warrior("hero", "archmage", { skill_access: ["academic", "speed", "special"] })],
      battles: [battle(1)],
      post_battles: [pendingPost(1, { pending_advances: [pendingAdvance("hero")] })],
    });
    const prose = await loadService(campaign, reader);
    const refusedProse = await prose.run("commitAdvanceChoice", { warrior_id: "hero", threshold: 2, kind: "choose_skill", skill_id: "skill.monster-slayer" });
    expect(refusedProse.ok).toBe(false);
    if (!refusedProse.ok) {
      expect(refusedProse.detail?.["reason"]).toBe("skill_pending_special_list");
      expect(refusedProse.message).toContain("prose-only");
    }
    // Nothing was granted and the advance is still pending for a reroll.
    expect(prose.current()!.campaign.warriors[0]?.skills).toEqual([]);
    expect(prose.current()!.campaign.post_battles[0]?.pending_advances?.[0]?.["committed"]).toBeFalsy();
  });

  it("requires the missing Dame of the Mare before any other recruit", async () => {
    const campaign = baseCampaign({
      band: "order-of-the-mare-web",
      warriors: [warrior("paragon", "paragon")],
      battles: [battle(1)],
      post_battles: [pendingPost(1)],
    });
    const service = await loadService(campaign, reader);

    const refused = await service.run("recruitBandProfile", { profile_id: "bowmen", quantity: 1 });
    expect(refused.ok).toBe(false);
    if (!refused.ok) {
      expect(refused.detail?.["reason"]).toBe("lifecycle_member_required");
      expect(refused.message).toContain("dame-of-the-mare");
    }

    const replacement = await service.run("recruitBandProfile", { profile_id: "dame-of-the-mare", quantity: 1 });
    expect(replacement.ok, replacement.ok ? "" : replacement.message).toBe(true);
    if (!replacement.ok) return;

    // The clause is discharged: the printed replacement is in the roster and
    // every other recruit is legal again.
    const allowed = await service.run("recruitBandProfile", { profile_id: "bowmen", quantity: 1 });
    expect(allowed.ok, allowed.ok ? "" : allowed.message).toBe(true);
    if (!allowed.ok) return;
    expect(allowed.document.campaign.warriors.filter((row) => row.profile_id === "dame-of-the-mare")).toHaveLength(1);
    expect(allowed.document.campaign.warriors.filter((row) => row.profile_id === "bowmen")).toHaveLength(1);

    // Reopening the saved file keeps the satisfied clause satisfied and the
    // replacement in the roster.
    const serialized = adapter.serializeCampaign(allowed.document.campaign);
    expect(serialized.ok, serialized.ok ? "" : serialized.message).toBe(true);
    if (!serialized.ok) return;
    const reopened = createCampaignAppService({ files: adapter, knowledge: reader });
    expect((await reopened.importCampaign({ text: serialized.text })).ok).toBe(true);
    expect((await reopened.run("recruitBandProfile", { profile_id: "bowmen", quantity: 1 })).ok).toBe(true);
  });

  it("applies the lifecycle gate to every route that can add a row to the roster", async () => {
    // The published clause is one rule applied at the single point every roster
    // increase crosses (the service dispatch), not a condition repeated in each
    // feature module: a profile, a member of an existing group, a Hired Sword
    // and a Dramatis Persona all cross it. A draft owns no lost member, so the
    // campaign is committed (see the `is_draft` case in `lifecycle.test`).
    const campaign = baseCampaign({
      band: "order-of-the-mare-web",
      warriors: [warrior("paragon", "paragon"), warrior("bowmen", "bowmen", { kind: "henchman", quantity: 1 })],
      battles: [battle(1)],
      post_battles: [pendingPost(1)],
    });
    const service = await loadService(campaign, reader);

    const additions: readonly (readonly [string, Record<string, unknown>])[] = [
      ["recruitBandProfile", { profile_id: "bowmen", quantity: 1 }],
      ["recruitGroupMember", { warrior_id: "bowmen" }],
      ["hireHireling", { profile_id: "hireling.hired-sword.bard", fee: 20 }],
      ["hireDramatisSearch", { hero_id: "paragon" }],
    ];

    // While the Dame is missing, no route adds anything, and only the clause's
    // own profile is allowed through.
    for (const [action, input] of additions) {
      const refused = await service.run(action, input);
      expect(refused.ok, action).toBe(false);
      if (!refused.ok) {
        expect(refused.detail?.["reason"], action).toBe("lifecycle_member_required");
        expect(refused.message, action).toContain("dame-of-the-mare");
      }
    }

    const replacement = await service.run("recruitBandProfile", { profile_id: "dame-of-the-mare", quantity: 1 });
    expect(replacement.ok, replacement.ok ? "" : replacement.message).toBe(true);
    if (!replacement.ok) return;

    // The clause is discharged: every route is reached again (its own outcome is
    // the route's business, but none is refused by the lifecycle gate).
    for (const [action, input] of additions) {
      const reached = await service.run(action, input);
      if (!reached.ok) expect(reached.detail?.["reason"], action).not.toBe("lifecycle_member_required");
    }
  });

  it("removes a doomed promotion instead of creating the Hero", async () => {
    const doomedService = async (quantity: number) => {
      const campaign = baseCampaign({
        band: "skaven-of-clan-pestilens-lus",
        warriors: [
          warrior("priest", "plague-priest"),
          warrior("slaves", "skaven-slaves", { kind: "henchman", quantity }),
        ],
        battles: [battle(1)],
        post_battles: [pendingPost(1, {
          pending_advances: [{
            warrior_id: "slaves",
            warrior_name: "slaves",
            table: "henchman_group",
            threshold: null,
            roll_total: 10,
            subroll: null,
            committed: false,
            applied_label: "",
            advance_options: [{ kind: "promote_henchman" }],
          }],
        })],
      });
      return loadService(campaign, reader);
    };

    // A group keeps its remaining members, rerolls the advance, and records why
    // nobody became a Hero.
    const group = await doomedService(2);
    const partial = await group.run("promoteHenchman", { warrior_id: "slaves", threshold: null, member_name: "Doomed One" });
    expect(partial.ok, partial.ok ? "" : partial.message).toBe(true);
    if (!partial.ok) return;
    expect(partial.document.campaign.warriors.some((row) => row.id.includes("promoted"))).toBe(false);
    expect(partial.document.campaign.warriors.find((row) => row.id === "slaves")?.quantity).toBe(1);
    expect(partial.document.campaign.post_battles[0]?.pending_advances?.[0]?.["roll_history"]).toContain(
      "Doomed: the promoted skaven-slaves is removed from the roster instead of becoming a Hero.",
    );

    // The last member of the group is removed outright and the saved file
    // reopens without him, with the advance closed.
    const single = await doomedService(1);
    const removed = await single.run("promoteHenchman", { warrior_id: "slaves", threshold: null, member_name: "Doomed One" });
    expect(removed.ok, removed.ok ? "" : removed.message).toBe(true);
    if (!removed.ok) return;
    expect(removed.document.campaign.warriors.some((row) => row.id === "slaves")).toBe(false);
    expect(removed.document.campaign.post_battles[0]?.pending_advances?.[0]?.["committed"]).toBe(true);
    const serialized = adapter.serializeCampaign(removed.document.campaign);
    expect(serialized.ok, serialized.ok ? "" : serialized.message).toBe(true);
    if (!serialized.ok) return;
    const parsed = parseCampaignFileDetailed(serialized.text);
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(parsed.campaign.warriors.some((row) => (row as { id?: string }).id === "slaves")).toBe(false);
  });
});

/**
 * T10 — the re-opened clusters through the real application service.
 *
 * Withdrawal, leader succession and mutation acquisition are non-React
 * consequences the web interface will present; each one travels through
 * `createCampaignAppService.run`, the same seam the interface consumes, and is
 * exported/reimported as a v5 file.
 */
import { describe, expect, it } from "vitest";
import { existsSync } from "node:fs";
import { readArtefactDocument } from "../../../support/kb-artefact";
import { join } from "node:path";

import { CampaignFileV5Adapter, parseCampaignFileDetailed } from "@adapters/campaign-file";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { createCampaignAppService } from "@app/campaign/service";
import { withdrawalLog } from "@domain/campaign/kernel/withdrawal";
import { successionLog } from "@domain/campaign/kernel/succession";
import { mutationsOf } from "@domain/campaign/kernel/mutations";
import type { Campaign } from "@domain/campaign/kernel/usecases";

const REPO_ROOT = join(import.meta.dirname, "..", "..", "..", "..");
const OVERRIDE = process.env.MORDHEIM_KNOWLEDGE_ARTEFACT;
const CANDIDATES = OVERRIDE
  ? [OVERRIDE]
  : [
      join(REPO_ROOT, "build", "generated", "knowledge-web", "knowledge-web.json"),
      join(REPO_ROOT, "outputs", "web-public", "knowledge", "knowledge-web.json"),
    ];
const ARTEFACT_PATH = CANDIDATES.find((path) => existsSync(path));
const adapter = new CampaignFileV5Adapter();

function baseCampaign(overrides: Partial<Campaign> & { band?: string }): Campaign {
  const { band, ...rest } = overrides;
  return {
    identity: { campaign_name: "T10b", warband_name: "Band", warband_type: "Band", band_id: band ?? "pirates-of-the-cathayan-sea-sar", mercenary_variant: null },
    configuration: { is_draft: false, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
    resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
    current_state_number: 1,
    warriors: [],
    battles: [],
    states: [{ number: 1, date: "2026-09-28", gold: 500, wyrdstone: 0, rating: 0, models: 1, max_models: 15, heroes: 1, henchmen: 0, experience: 0 }],
    post_battles: [],
    inventory: [],
    special_rules: [],
    manual_log: [],
    ...rest,
  };
}

function warrior(id: string, profileId: string, kind: "hero" | "henchman" = "hero", quantity = 1) {
  return { id, name: `${profileId} ${id}`, profile_name: profileId, kind, stats: {}, equipment: [], skills: [], experience: 0, cost: 0, quantity, profile_id: profileId };
}

async function loadService(campaign: Campaign, reader: ArtefactKnowledgeReader) {
  const serialized = adapter.serializeCampaign(campaign);
  expect(serialized.ok, serialized.ok ? "" : serialized.message).toBe(true);
  if (!serialized.ok) throw new Error(serialized.message);
  const service = createCampaignAppService({ files: adapter, knowledge: reader });
  const imported = await service.importCampaign({ text: serialized.text });
  expect(imported.ok, imported.ok ? "" : imported.message).toBe(true);
  return service;
}

describe.skipIf(!ARTEFACT_PATH)("T10 re-opened clusters (application service)", () => {
  const artefact = readArtefactDocument(ARTEFACT_PATH as string);
  const reader = ArtefactKnowledgeReader.from(artefact);

  it("withdraws the members that left the table and keeps the audit across a reopen", async () => {
    const campaign = baseCampaign({ warriors: [warrior("warlord", "disgraced-warlord"), warrior("mates", "shanghaires", "hero", 2)] });
    const service = await loadService(campaign, reader);
    const result = await service.run("withdrawLeftTableMembers", { member_ids: ["mates"], reason: "left the table", battle_number: 1 });
    expect(result.ok, result.ok ? "" : result.message).toBe(true);
    if (!result.ok) return;
    expect(result.document.campaign.warriors.find((row) => row.id === "mates")?.quantity).toBe(1);
    expect(withdrawalLog(result.document)).toHaveLength(1);

    const exported = await service.exportCampaign();
    expect(exported.ok).toBe(true);
    if (!exported.ok || !exported.payload) return;
    const parsed = parseCampaignFileDetailed(exported.payload.text);
    expect(parsed.ok).toBe(true);
    if (!parsed.ok) return;
    expect(parsed.campaign.warriors.find((row) => row.id === "mates")?.quantity).toBe(1);
    expect(parsed.campaign.manual_log.some((row) => (row as { kind?: string }).kind === "left_table_withdrawal")).toBe(true);

    const reopened = createCampaignAppService({ files: adapter, knowledge: reader });
    expect((await reopened.importCampaign({ text: exported.payload.text })).ok).toBe(true);
    const again = await reopened.run("withdrawLeftTableMembers", { member_ids: ["warlord"] });
    expect(again.ok).toBe(true);
    const unknown = await reopened.run("withdrawLeftTableMembers", { member_ids: ["ghost"] });
    expect(unknown.ok).toBe(false);
    if (!unknown.ok) expect(unknown.detail?.["reason"]).toBe("not_found");
  });

  it("seats a successor when the leader is gone and refuses it while the leader still leads", async () => {
    const leaderless = baseCampaign({ warriors: [warrior("mate", "shanghaires")] });
    const service = await loadService(leaderless, reader);
    const seated = await service.run("succeedLeader", { clause_id: "campaign.succession.cathayan-pirates" });
    expect(seated.ok, seated.ok ? "" : seated.message).toBe(true);
    if (!seated.ok) return;
    expect(successionLog(seated.document)).toHaveLength(1);

    const withLeader = baseCampaign({ warriors: [warrior("warlord", "disgraced-warlord"), warrior("mate", "shanghaires")] });
    const other = await loadService(withLeader, reader);
    const early = await other.run("succeedLeader", { clause_id: "campaign.succession.cathayan-pirates" });
    expect(early.ok).toBe(false);
  });

  it("buys a mutation while recruiting and refuses a duplicate", async () => {
    const campaign = baseCampaign({
      band: "shallows-beasts-mim",
      configuration: { is_draft: true, starting_gold: 500, minimum_models: 1, maximum_models: 15, hero_limit: 5 },
      current_state_number: 0,
      states: [],
      warriors: [warrior("reaver", "reavers")],
    });
    const service = await loadService(campaign, reader);
    const bought = await service.run("buyMutation", { warrior_id: "reaver", mutation_id: "campaign.mutation.blackblood" });
    expect(bought.ok, bought.ok ? "" : bought.message).toBe(true);
    if (!bought.ok) return;
    expect(mutationsOf(bought.document, "reaver")).toEqual(["campaign.mutation.blackblood"]);
    const duplicate = await service.run("buyMutation", { warrior_id: "reaver", mutation_id: "campaign.mutation.blackblood" });
    expect(duplicate.ok).toBe(false);
    if (!duplicate.ok) expect(duplicate.detail?.["reason"]).toBe("conflict");
  });
});

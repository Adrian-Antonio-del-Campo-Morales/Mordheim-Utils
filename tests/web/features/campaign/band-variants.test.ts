import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { activeBandRuleIds, warbandVariants } from "@domain/campaign/band-variants";
import { createService } from "@src/features/campaign/default-deps";

function knowledge() {
  const raw = JSON.parse(readFileSync(resolve(process.cwd(), "../../outputs/web-public/knowledge/knowledge-web.json"), "utf8"));
  return ArtefactKnowledgeReader.from(raw);
}

describe("warband family variants", () => {
  it("exposes the canonical Mercenary and Tilean choices", () => {
    const reader = knowledge();
    expect(warbandVariants(reader, "mercenaries").map((row) => row.id)).toEqual(["marienburg", "middenheim", "ostermark", "reikland"]);
    expect(warbandVariants(reader, "tileans").map((row) => row.id)).toEqual(["miragleans", "remasens", "tileans", "trantios"]);
  });

  it("requires a valid variant and applies its starting treasury", async () => {
    const reader = knowledge();
    const missing = await createService(reader).createCampaign({ band_id: "mercenaries", campaign_name: "Test", warband_name: "Test" });
    expect(missing).toMatchObject({ ok: false, message: "Choose a valid warband variant." });
    const invalid = await createService(reader).createCampaign({ band_id: "tileans", campaign_name: "Test", warband_name: "Test", variant: "unknown" });
    expect(invalid).toMatchObject({ ok: false, message: "Choose a valid warband variant." });

    const mercenaries = createService(reader);
    expect((await mercenaries.createCampaign({ band_id: "mercenaries", campaign_name: "Test", warband_name: "Test", variant: "marienburg" })).ok).toBe(true);
    expect(mercenaries.current()?.campaign.configuration.starting_gold).toBe(600);
    const tileans = createService(reader);
    expect((await tileans.createCampaign({ band_id: "tileans", campaign_name: "Test", warband_name: "Test", variant: "trantios" })).ok).toBe(true);
    expect(tileans.current()?.campaign.configuration.starting_gold).toBe(600);
    for (const [band_id, variant] of [["mercenaries", "reikland"], ["mercenaries", "middenheim"], ["mercenaries", "ostermark"], ["tileans", "tileans"], ["tileans", "miragleans"], ["tileans", "remasens"]]) {
      const standard = createService(reader);
      expect((await standard.createCampaign({ band_id, campaign_name: "Test", warband_name: "Test", variant })).ok).toBe(true);
      expect(standard.current()?.campaign.configuration.starting_gold).toBe(500);
    }
  });

  it("activates common rules plus only the selected variant rules", async () => {
    const reader = knowledge();
    const service = createService(reader);
    await service.createCampaign({ band_id: "tileans", campaign_name: "Test", warband_name: "Test", variant: "miragleans" });
    const rules = activeBandRuleIds(reader, service.current()!);
    expect(rules).toContain("band--human-maximum-characteristics");
    expect(rules).toContain("band--miraglean-crossbow-mastery");
    expect(rules).not.toContain("band--remasen-officer-leadership");
    expect(rules).not.toContain("band--trantio-wealth");

    const mercenaries = createService(reader);
    await mercenaries.createCampaign({ band_id: "mercenaries", campaign_name: "Test", warband_name: "Test", variant: "reikland" });
    const mercenaryRules = activeBandRuleIds(reader, mercenaries.current()!);
    expect(mercenaryRules).toContain("band--reikland-command-radius");
    expect(mercenaryRules).not.toContain("band--middenheim-physical-prowess");
    expect(mercenaryRules).not.toContain("band--marienburg-wealth");
    expect(mercenaryRules).not.toContain("band--ostermark-stubborn-resolve");
  });

  it("applies Middenheim profile bonuses and locks the selected variant", async () => {
    const reader = knowledge();
    const service = createService(reader);
    await service.createCampaign({ band_id: "mercenaries", campaign_name: "Test", warband_name: "Test", variant: "middenheim" });
    const added = await service.run("composeDraft", { band_id: "mercenaries", rows: [{ profile_id: "mercenary-captain", kind: "hero", quantity: 1, equipment: [] }] });
    expect(added.ok).toBe(true);
    expect(service.current()?.campaign.warriors[0].stats.S).toBe(4);
    expect(await service.run("setMercenaryVariant", { variant: "reikland" })).toMatchObject({ ok: false, message: "The warband variant is locked after selection." });
  });

  it("round-trips the selected variant through a v5 file", async () => {
    const reader = knowledge();
    const source = createService(reader);
    await source.createCampaign({ band_id: "mercenaries", campaign_name: "Test", warband_name: "Test", variant: "reikland" });
    const exported = await source.prepareExport();
    expect(exported.ok).toBe(true);
    if (!exported.ok || !exported.payload) return;
    const target = createService(reader);
    expect((await target.importCampaign({ text: exported.payload.text })).ok).toBe(true);
    expect(target.current()?.campaign.identity.mercenary_variant).toBe("reikland");
  });

  it("lets a legacy draft choose its missing variant exactly once", async () => {
    const reader = knowledge();
    const source = createService(reader);
    await source.createCampaign({ band_id: "tileans", campaign_name: "Legacy", warband_name: "Legacy", variant: "tileans" });
    const exported = await source.prepareExport();
    expect(exported.ok).toBe(true);
    if (!exported.ok || !exported.payload) return;
    const legacy = JSON.parse(exported.payload.text);
    legacy.campaign.identity.mercenary_variant = null;

    const target = createService(reader);
    expect((await target.importCampaign({ text: JSON.stringify(legacy) })).ok).toBe(true);
    expect((await target.run("setMercenaryVariant", { variant: "trantios" })).ok).toBe(true);
    expect(target.current()?.campaign.configuration.starting_gold).toBe(600);
    expect(await target.run("setMercenaryVariant", { variant: "tileans" })).toMatchObject({ ok: false, message: "The warband variant is locked after selection." });
  });
});

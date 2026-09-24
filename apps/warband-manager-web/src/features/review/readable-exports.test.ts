import { describe, expect, it } from "vitest";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { CampaignDocument } from "../campaign/types";
import { localizedLedger, localizedRoster } from "./readable-exports";
import { historyEventText } from "./history-presentation";

const knowledge = ArtefactKnowledgeReader.from({
  schema_version: 1, ruleset: "test",
  bands: [{ id: "internal_band", names: { es: "Banda", en: "Warband" } }],
  profiles: [{ id: "internal_profile", names: { es: "Capitana", en: "Captain" } }],
  items: [{ item_id: "internal_sword", names: { es: "Espada", en: "Sword" } }],
  skills: [{ id: "spell.internal_a", names: { es: "Luz", en: "Light" } }, { id: "spell.internal_b", names: { es: "Fuego", en: "Fire" } }],
});
const document = { campaign: {
  identity: { campaign_name: "My own campaign", warband_name: "Mi banda personal", band_id: "internal_band", warband_type: "STALE_BAND" },
  current_state_number: 1, states: [],
  warriors: [{ id: "internal_warrior", name: "My_name_with_tags", profile_id: "internal_profile", profile_name: "STALE_PROFILE", kind: "hero", experience: 3, quantity: 1, equipment: [{ item_id: "internal_sword", name: "STALE_ITEM", quantity: 2 }], skills: [] }],
  battles: [{ number: 1, date: "2026-09-22", scenario: "missing_scenario", opponent: "My opponent", result: "win", gold_delta: 1, xp_delta: 2, notes: "My literal personal notes" }],
  post_battles: [{ battle_number: 1, event_log: [{ type: "buy_item", item_id: "internal_sword", quantity: 2, gold: 10, description: "STALE_EVENT" }, { type: "UNSAFE_EVENT_TAG", message: "UNSAFE_MESSAGE", description: "UNSAFE_DESCRIPTION" }] }],
  manual_log: [{ type: "manual_resource_correction", resource: "gold_crowns", delta: 2, reason: "My literal correction reason" }, { message: "UNKNOWN_LEGACY_SYSTEM_TEXT" }],
} } as unknown as CampaignDocument;

describe("readable export boundary", () => {
  it("re-resolves new history facts across es/en/es and rejects legacy snapshots", () => {
    const event = { type: "scenario_spell_reward", warrior_id: "gone", warrior_personal_name: "My hero", spell_ids: ["spell.internal_a", "spell.internal_b"], description: "STALE_SPELLS" };
    for (const locale of ["es", "en", "es"] as const) {
      const rendered = historyEventText(event, document, locale, knowledge);
      expect(rendered).toContain(locale === "es" ? "Luz, Fuego" : "Light, Fire");
      expect(rendered).toContain("My hero");
      expect(rendered).not.toMatch(/internal_|STALE_/);
      expect(historyEventText({ type: "recruit_member", warrior_personal_name: "My group", gold: 17 }, document, locale, knowledge)).toContain("My group");
      expect(historyEventText({ ...event, spell_ids: undefined }, document, locale, knowledge)).toBe(locale === "es" ? "Información no disponible" : "Information unavailable");
    }
  });
  it.each(["es", "en"] as const)("resolves source references and preserves personal fields in %s", (locale) => {
    const roster = localizedRoster(document, locale, knowledge), ledger = localizedLedger(document, locale, knowledge);
    expect(roster).toContain(locale === "es" ? "Capitana" : "Captain");
    expect(roster).toContain(locale === "es" ? "2 Espada" : "2 Sword");
    expect(roster).toContain("My_name_with_tags");
    expect(ledger).toContain(locale === "es" ? "2 × Espada: compra por 10 co." : "2 × Sword: bought for 10 gc.");
    expect(ledger).toContain("My literal personal notes");
    expect(ledger).toContain("My literal correction reason");
    expect(ledger).toContain(locale === "es" ? "Información no disponible" : "Information unavailable");
    expect(roster + ledger).not.toMatch(/STALE_|UNSAFE_|UNKNOWN_LEGACY|internal_|missing_scenario/);
  });
  it("uses saved personal provenance after a warrior leaves", () => {
    const event = { type: "hireling_upkeep", warrior_id: "departed_id", warrior_personal_name: "My departed warrior", pay: false };
    expect(historyEventText(event, document, "es")).toContain("My departed warrior se marcha");
    expect(historyEventText(event, document, "en")).toContain("My departed warrior leaves");
  });
  it.each(["es", "en"] as const)("renders recruitment and upgrades from facts in %s", (locale) => {
    const recruitment = historyEventText({ type: "recruit", warrior_id: "gone", warrior_personal_name: "My recruit", profile_id: "internal_profile", quantity: 2, gold: 40, description: "STALE_RECRUIT" }, document, locale, knowledge);
    const upgrade = historyEventText({ type: "upgrade_weapon", base_item_id: "internal_sword", item_id: "internal_sword", gold: 15, description: "STALE_UPGRADE" }, document, locale, knowledge);
    expect(recruitment).toContain(locale === "es" ? "My recruit (Capitana)" : "My recruit (Captain)");
    expect(recruitment).toContain("40");
    expect(upgrade).toContain(locale === "es" ? "Espada: mejora Espada por 15 co." : "Sword: upgraded with Sword for 15 gc.");
    expect(recruitment + upgrade).not.toMatch(/internal_|STALE_/);
    expect(historyEventText({ type: "recruit", quantity: "internal_tag", gold: 40 }, document, locale, knowledge)).toBe(locale === "es" ? "Información no disponible" : "Information unavailable");
  });
  it("interprets exact legacy v5 action messages without exposing the captured prose", () => {
    expect(historyEventText({ action: "sell_wyrdstone", message: "Sold 1 shard(s) for 35 gc." }, document, "es")).toBe("Se vendieron 1 fragmento(s) por 35 co.");
    expect(historyEventText({ action: "sell_wyrdstone", message: "prefix Sold 1 shard(s) for 35 gc." }, document, "es")).toBe("Información no disponible");
  });
  it("rejects corrupted facts and partial matches to legacy prose", () => {
    expect(historyEventText({ type: "exploration", shards: "RAW_TAG" }, document, "es")).toBe("Información no disponible");
    expect(historyEventText({ type: "exploration", description: "prefix Found 4 wyrdstone shards." }, document, "es")).toBe("Información no disponible");
    expect(historyEventText({ type: "exploration", description: "Found 4 wyrdstone shards." }, document, "es")).toContain("4 fragmento(s)");
  });
});

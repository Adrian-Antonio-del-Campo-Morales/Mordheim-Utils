import { describe, expect, it, vi } from "vitest";
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { PDFPage, PDFDocument, PDFRawStream, decodePDFRawStream } from "pdf-lib";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

import type { CampaignDocument, TimelineState, Warrior } from "@src/features/campaign/types";
import { createWarbandPdf } from "@src/features/export/warband-pdf";

const hero: Warrior = {
  id: "marta",
  name: "Marta — \u201eCu\u00e9ntamelo\u201c \u26a0 \u{1f3b2}",
  profile_name: "Sister",
  kind: "hero",
  stats: { M: 4, WS: 4, BS: 4, S: 3, T: 3, W: 1, I: 4, A: 1, Ld: 8 },
  equipment: [],
  skills: [],
  experience: 4,
  cost: 45,
};

const henchman: Warrior = {
  id: "g1",
  name: "Sisters",
  profile_name: "Novice",
  kind: "henchman",
  stats: { M: 4, WS: 3, BS: 3, S: 3, T: 3, W: 1, I: 3, A: 1, Ld: 7 },
  equipment: [{ item_id: "item.sword", name: "Sword", quantity: 2 }],
  skills: [],
  experience: 0,
  quantity: 3,
  cost: 25,
};

function documentWith(selected_moment?: string): CampaignDocument {
  const state: TimelineState = {
    number: 0,
    label: "STALE_INTERNAL_STATE_LABEL",
    date: "2026-09-10",
    gold: 480,
    wyrdstone: 1,
    rating: 55,
    models: 2,
    max_models: 15,
    heroes: 1,
    henchmen: 1,
    experience: 4,
    roster: [hero],
    inventory: [{ id: "item.axe", name: "Axe", category: "weapon", owned: 1, equipped: 0, stash: 1 }],
  };
  return {
    campaign: {
      identity: { campaign_name: "Campaign", warband_name: "Band", warband_type: "Sisters", band_id: "sisters-of-sigmar", mercenary_variant: null },
      configuration: { is_draft: false, starting_gold: 500, minimum_models: 3, maximum_models: 15, hero_limit: 5 },
      resources: { stash_value: 0, rare_finds: 0, treasures: 0, campaign_points: 0 },
      current_state_number: 0,
      warriors: [hero, henchman],
      battles: [{ number: 1, date: "2026-09-10", scenario: "scenario.skirmish", opponent: "Orcs", result: "win", gold_delta: 20, wyrdstone: 1, xp_delta: 4, casualties: 0, advances: 0, rating_before: 30, rating_after: 55, models_before: 2, models_after: 2, out_of_action_ids: [] }],
      states: [state],
      post_battles: [],
      inventory: [],
      special_rules: [],
      manual_log: [],
    },
    view: selected_moment ? { selected_moment } : {},
  };
}

describe("warband PDF exporter (desktop parity port)", () => {
  it.each(["es", "en"] as const)("rejects poisoned KB captures in writer calls and serialized PDF streams (%s)", async (locale) => {
    const marker = "RAW_KB_POISON_";
    const band = marker + "BAND", profile = marker + "PROFILE", item = marker + "ITEM";
    const reader = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test",
      bands: [{ id: band, name: marker + "BAND_NAME", names: { es: "Banda prueba", en: "Test warband" } }],
      profiles: [{ id: profile, name: marker + "PROFILE_NAME", names: { es: "Capitana", en: "Captain" } }],
      items: [{ item_id: item, name: marker + "ITEM_NAME", names: { es: "Espada", en: "Sword" } }], skills: [],
    });
    const base = documentWith();
    const poisoned: CampaignDocument = { ...base, campaign: { ...base.campaign,
      identity: { ...base.campaign.identity, band_id: band, warband_type: marker + "SAVED_BAND" },
      warriors: [{ ...hero, name: "Personal name", profile_id: profile, profile_name: marker + "SAVED_PROFILE", equipment: [{ item_id: item, name: marker + "SAVED_ITEM", quantity: 1 }] }],
    } };
    const draw = vi.spyOn(PDFPage.prototype, "drawText");
    try {
      const bytes = await createWarbandPdf(poisoned, locale, reader);
      const calls = draw.mock.calls.map(([text]) => text).join("\n");
      expect(calls).not.toContain(marker);
      expect(calls).toContain(locale === "es" ? "Espada" : "Sword");
      const loaded = await PDFDocument.load(bytes);
      expect(loaded.getPageCount()).toBeGreaterThan(0);
      const streams = loaded.context.enumerateIndirectObjects().flatMap(([, object]) => object instanceof PDFRawStream ? [Buffer.from(decodePDFRawStream(object).decode()).toString("latin1")] : []).join("\n");
      // pdf-lib emits the standard-font text as hex strings in page content streams.
      const extracted = [...streams.matchAll(/<([0-9a-f]+)>/gi)].map((match) => Buffer.from(match[1], "hex").toString("latin1")).join("\n");
      expect(extracted).toContain("Personal name");
      expect(extracted).toContain(locale === "es" ? "Espada" : "Sword");
      expect(extracted).not.toContain(marker);
    } finally { draw.mockRestore(); }
  });
  it.each(["es", "en"] as const)("prints resolved KB labels and personal names in %s", async (locale) => {
    const knowledge = ArtefactKnowledgeReader.from({
      schema_version: 1, ruleset: "test",
      bands: [{ id: "sisters-of-sigmar", names: { es: "Hermanas", en: "Sisters" } }],
      profiles: [{ id: "test.profile", band_id: "sisters-of-sigmar", names: { es: "Hermana", en: "Sister" } }],
      items: [{ item_id: "item.sword", names: { es: "Espada", en: "Sword" } }],
      skills: [],
      campaign: { hirelings: { profiles: [{ id: "test.hireling", names: { es: "Mercenario", en: "Mercenary" } }] } },
    });
    const original = documentWith();
    const document: CampaignDocument = { ...original, campaign: { ...original.campaign,
      identity: { ...original.campaign.identity, warband_type: "STALE_BAND_LABEL" },
      warriors: [
      { ...hero, name: "Personal_name", profile_id: "test.profile", profile_name: "STALE_PROFILE_LABEL", stat_advances: { WS: 1 }, equipment: [{ item_id: "item.sword", name: "STALE_ITEM_LABEL", quantity: 1 }] },
      { ...hero, id: "hired", name: "Hired_personal_name", kind: "hireling", profile_id: "test.hireling", profile_name: "STALE_HIRELING_LABEL" },
      ],
    } };
    const draw = vi.spyOn(PDFPage.prototype, "drawText");
    try {
      const bytes = await createWarbandPdf(document, locale, knowledge);
      if (process.env.PRESENTATION_PDF_DIR) {
        const directory = resolve(process.env.PRESENTATION_PDF_DIR);
        mkdirSync(directory, { recursive: true });
        writeFileSync(resolve(directory, `localized-${locale}.pdf`), bytes);
      }
      const printed = draw.mock.calls.map(([text]) => text).join("\n");
      expect(printed).toContain("Personal_name");
      expect(printed).toContain("Hired_personal_name");
      for (const label of locale === "es" ? ["Hermanas", "Hermana", "Espada", "Mercenario", "HA +1"] : ["Sisters", "Sister", "Sword", "Mercenary", "WS +1"]) expect(printed).toContain(label);
      expect(printed).not.toMatch(/STALE_|test\.profile|test\.hireling|item\.sword/);
      expect(printed).not.toContain("?");
      expect(draw.mock.calls.some(([text]) => text.startsWith(locale === "es" ? "Piedra Bruja:" : "Wyrdstone:"))).toBe(true);
    } finally {
      draw.mockRestore();
    }
  });

  it.each(["es", "en"] as const)("does not print stored KB labels or IDs without knowledge in %s", async (locale) => {
    const original = documentWith();
    const document: CampaignDocument = { ...original, campaign: { ...original.campaign,
      identity: { ...original.campaign.identity, warband_type: "STALE_BAND_LABEL" },
      warriors: [{ ...hero, name: "Personal_name", profile_id: "missing.profile", profile_name: "STALE_PROFILE_LABEL", skills: ["missing.skill"], equipment: [{ item_id: "missing.item", name: "STALE_ITEM_LABEL", quantity: 1 }] }],
    } };
    const draw = vi.spyOn(PDFPage.prototype, "drawText");
    try {
      await createWarbandPdf(document, locale);
      const printed = draw.mock.calls.map(([text]) => text).join("\n");
      expect(printed).toContain("Personal_name");
      expect(printed).not.toMatch(/STALE_|missing\.|scenario\.skirmish/);
      expect(printed).not.toContain(locale === "es" ? "Unavailable" : "No disponible");
    } finally {
      draw.mockRestore();
    }
  });

  it("renders a valid PDF for the draft, a committed state and non-latin text", async () => {
    for (const selected of ["draft:0", "state:0", "post:1"]) {
      const bytes = await createWarbandPdf(documentWith(selected), "es");
      const text = Buffer.from(bytes).toString("latin1");
      expect(text.startsWith("%PDF-")).toBe(true);
      expect(text.trimEnd().endsWith("%%EOF")).toBe(true);
      expect(bytes.length).toBeGreaterThan(500);
    }
  });

  it("does not export a captured system state label", async () => {
    const draw = vi.spyOn(PDFPage.prototype, "drawText");
    try {
      await createWarbandPdf(documentWith("state:0"), "es");
      const printed = draw.mock.calls.map(([text]) => text).join("\n");
      expect(printed).not.toContain("STALE_INTERNAL_STATE_LABEL");
      expect(printed).toContain("ESTADO #0");
    } finally { draw.mockRestore(); }
  });
});

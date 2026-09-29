import { describe, expect, it } from "vitest";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { scenarioText } from "@src/features/campaign/displayText";
import { textDate } from "@src/features/campaign/presentation-values";

/**
 * The two persisted v5 date shapes and the two battle-scenario shapes. The web
 * writer stores ISO dates and canonical scenario ids; the desktop reference
 * writer stores `%d %b %Y` dates and the display label captured at battle time.
 * Both resolve through the shared resolvers, and an unknown reference yields a
 * specific localized absence notice — never the generic one, never the raw id.
 */
const knowledge = ArtefactKnowledgeReader.from({
  schema_version: 1,
  ruleset: "mordheim",
  bands: [],
  profiles: [],
  skills: [],
  items: [],
  campaign: {
    scenarios: {
      scenarios: [
        { id: "scenario.skirmish", name: "Skirmish", name_i18n: { es: "Escaramuza" } },
        { id: "scenario.raid", name: "Raid", name_i18n: { es: "Incursión" } },
        // Two scenarios captured the same label: the resolver must not guess.
        { id: "scenario.ambush-one", name: "Ambush", name_i18n: { es: "Emboscada" } },
        { id: "scenario.ambush-two", name: "Ambush", name_i18n: { es: "Emboscada doble" } },
      ],
    },
  },
});

describe("stored date resolution", () => {
  it("formats both persisted v5 date shapes in the active locale", () => {
    expect(textDate("2026-07-14", "en")).toBe("7/14/2026");
    expect(textDate("2026-07-14", "es")).toBe("14/7/2026");
    // Desktop reference writer shape: `date.today().strftime("%d %b %Y")`.
    expect(textDate("14 Jul 2026", "es")).toBe("14/7/2026");
    expect(textDate("14 Jul 2026", "en")).toBe("7/14/2026");
    expect(textDate("7 Aug 2026", "en")).toBe("8/7/2026");
  });

  it("rejects stored values that are not a recognized date", () => {
    expect(textDate("Cyber 2", "es")).toBe("Información no disponible");
    expect(textDate("2026-13-40", "es")).toBe("Información no disponible");
    expect(textDate("2026-02-30", "en")).toBe("Information unavailable");
    expect(textDate(undefined, "en")).toBe("Information unavailable");
  });
});

describe("battle scenario resolution", () => {
  it("resolves canonical ids and captured desktop labels to the localized KB name", () => {
    expect(scenarioText(knowledge, "scenario.skirmish", "es")).toBe("Escaramuza");
    expect(scenarioText(knowledge, "Skirmish", "es")).toBe("Escaramuza");
    expect(scenarioText(knowledge, "Skirmish", "en")).toBe("Skirmish");
    expect(scenarioText(knowledge, "Raid", "es")).toBe("Incursión");
  });

  it("shows a specific localized notice, never the generic one or the raw reference", () => {
    for (const locale of ["es", "en"] as const) {
      const text = scenarioText(knowledge, "Search & Destroy", locale);
      expect(text).toBe(
        locale === "es"
          ? "El escenario no está reconocido en la base de conocimiento."
          : "The scenario is not recognized in the knowledge base.",
      );
      expect(text).not.toBe(locale === "es" ? "Información no disponible" : "Information unavailable");
      expect(text).not.toContain("Search & Destroy");
    }
    expect(scenarioText(knowledge, undefined, "en")).toBe("The scenario is not recognized in the knowledge base.");
  });

  it("refuses to guess between two scenarios that captured the same label", () => {
    expect(scenarioText(knowledge, "Ambush", "es")).toBe("El escenario no está reconocido en la base de conocimiento.");
  });
});

/**
 * Mandatory regression case of the dynamic visible-completeness layer: the
 * "Reglas compartidas" tab through the real `RulesCatalogue` against the REAL
 * generated artefacts (no data filtering, no fixtures).
 *
 * The requirement (2A2B plan): the shared rules category must contain exactly
 * the 68 real shared rules (`shared-rule.*`) — no band-local copy — and every
 * entry's name and effect must resolve in ES and EN with zero generic fallbacks
 * and zero ids shown as text.
 *
 * Current product state: `rules-prose.json` publishes 1,924 rows under the
 * `special-rules` stem (68 shared + 1,856 band-local copies), so `RulesCatalogue`
 * renders the copies as "Información no disponible". This test therefore fails
 * against the current artefact BY DESIGN: the red is the real defect, and the
 * detector must not be relaxed to pass it. Do not repair the catalogue, the
 * generator or the data inside this task.
 */
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { RulesCatalogue } from "@app/rules/rules-catalogue";
import { classifyVisibleText, buildIdInventory, GENERIC_FALLBACKS } from "../../../tools/web/presentation-completeness-detector.mjs";
import { readArtefactDocument } from "../../support/kb-artefact";

const PUBLISHED = resolve(process.cwd(), "..", "..", "outputs", "web-public", "knowledge", "knowledge-web.json");
const SHARED_EXPECTED = 68;

const artefact = readArtefactDocument(PUBLISHED);
const knowledge = ArtefactKnowledgeReader.from(artefact);
const catalogue = new RulesCatalogue(knowledge);
const inventory = buildIdInventory(artefact);
const fallbackTexts = Object.values(GENERIC_FALLBACKS).flat();
const sharedRows = ((artefact as Record<string, unknown>).rules_prose as Record<string, readonly Record<string, unknown>[]> | undefined)?.["special-rules"] ?? [];

describe('regression: "Reglas compartidas" publishes exactly the real shared rules', () => {
  it("publishes exactly 68 shared-rules rows in the special-rules stem", () => {
    expect(sharedRows.length).toBe(SHARED_EXPECTED);
  });

  it("every special-rules row id starts with shared-rule.", () => {
    const foreign = sharedRows.filter((row) => !String(row.id).startsWith("shared-rule."));
    expect(foreign.map((row) => String(row.id)).slice(0, 10)).toEqual([]);
  });

  it("no band-local rule leaks into the shared category (RulesCatalogue, both locales)", () => {
    for (const locale of ["es", "en"] as const) {
      const entries = catalogue.entries("special-rules", locale);
      const locals = entries.filter((entry) => !entry.entry_id.startsWith("shared-rule."));
      expect(locals.map((entry) => entry.entry_id).slice(0, 10), `locale ${locale}`).toEqual([]);
    }
  });

  it("name and effect resolve in ES for every shared entry", () => {
    for (const entry of catalogue.entries("special-rules", "es")) {
      expect(entry.name.trim(), `${entry.entry_id} name (es)`).not.toBe("");
      expect(entry.effect.trim(), `${entry.entry_id} effect (es)`).not.toBe("");
      expect(entry.name).not.toBe(entry.entry_id);
    }
  });

  it("name and effect resolve in EN for every shared entry", () => {
    for (const entry of catalogue.entries("special-rules", "en")) {
      expect(entry.name.trim(), `${entry.entry_id} name (en)`).not.toBe("");
      expect(entry.effect.trim(), `${entry.entry_id} effect (en)`).not.toBe("");
      expect(entry.name).not.toBe(entry.entry_id);
    }
  });

  it("zero generic fallbacks in the shared category, both locales", () => {
    for (const locale of ["es", "en"] as const) {
      for (const entry of catalogue.entries("special-rules", locale)) {
        for (const [field, text] of [["name", entry.name], ["effect", entry.effect]] as const) {
          const finding = classifyVisibleText(text, { locale, surface: `rules-catalogue/special-rules`, category: "special-rules", field, ref: { kind: "rule", id: entry.entry_id }, idInventory: inventory });
          if (finding?.kind === "generic-fallback" && !fallbackTexts.includes(text.trim())) continue;
          expect(finding, `${entry.entry_id}.${field} (${locale}) → "${text}"`).toBeNull();
        }
      }
    }
  });

  it("zero ids used as visible text in the shared category, both locales", () => {
    for (const locale of ["es", "en"] as const) {
      for (const entry of catalogue.entries("special-rules", locale)) {
        expect(entry.name, `${entry.entry_id} name as id (${locale})`).not.toBe(entry.entry_id);
        expect(entry.effect, `${entry.entry_id} effect as id (${locale})`).not.toBe(entry.entry_id);
        const idFinding = classifyVisibleText(entry.name, { locale, surface: "regression", field: "name", ref: { kind: "rule", id: entry.entry_id }, idInventory: inventory });
        expect(idFinding?.kind, `${entry.entry_id} name (${locale})`).not.toBe("technical-id");
      }
    }
  });
});

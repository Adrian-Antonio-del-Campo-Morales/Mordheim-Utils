/**
 * Per-family gate for the visible fallbacks closed after `4631eae`.
 *
 * Every family is asserted twice, against the real generated artefacts and the
 * real consumers:
 *
 *  1. the data resolves — no `TODO-TRANSLATE` entry left in the family, and the
 *     composed catalogue text a person reads carries no generic fallback;
 *  2. the gate is not vacuous — the exact pre-fix composition (a fallback glued
 *     to the label, bullet, die result or chip that carried it) is still flagged
 *     by the shared classifier.
 *
 * A family that regresses fails here, in the static gate and in the dynamic
 * completeness audit, without any allowlist.
 */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { RulesCatalogue } from "@app/rules/rules-catalogue";
import { classifyVisibleText } from "../../../../tools/web/presentation-completeness-detector.mjs";
import { readArtefactDocument } from "../../../support/kb-artefact";

const PUBLISHED = resolve(process.cwd(), "..", "..", "outputs", "web-public", "knowledge", "knowledge-web.json");
const DISPLAY = resolve(process.cwd(), "..", "..", "outputs", "web-public", "knowledge", "display-text.json");

const knowledge = ArtefactKnowledgeReader.from(readArtefactDocument(PUBLISHED));
const catalogue = new RulesCatalogue(knowledge);
const display = JSON.parse(readFileSync(DISPLAY, "utf8")) as {
  readonly translation_todos: readonly { readonly status: string; readonly location: string }[];
  readonly presentation_entries: readonly { readonly source: string; readonly fields: Record<string, Record<string, string>> }[];
};

/** The families closed after `4631eae`: their generated source stem and fields. */
const FAMILIES = [
  { name: "scenario authors", source: "campaign/scenarios/scenarios/", fields: ["author"] },
  { name: "scenario wyrdstone", source: "campaign/scenarios/scenarios/", fields: ["wyrdstone"] },
  { name: "scenario notes", source: "campaign/scenarios/scenarios/", fields: ["notes"] },
  { name: "scenario loot rewards", source: "campaign/scenarios/scenarios/", fields: ["reward"] },
  { name: "serious-injury results", source: "campaign/serious-injuries/tables/", fields: ["result", "name"] },
] as const;

/** Composed shapes the six families leaked through, and the fragment that carried it. */
const REGRESSIONS = [
  ["scenario author", "Autor: Información no disponible", "es"],
  ["scenario author", "Author: Information unavailable", "en"],
  ["scenario notes", "Notas: Información no disponible", "es"],
  ["scenario loot", "• 5+ Información no disponible", "es"],
  ["scenario loot", "• 4+ Information unavailable", "en"],
  ["scenario wyrdstone", "Piedra bruja: Información no disponible", "es"],
  ["spell difficulty", "Nigromancia · Dificultad Información no disponible", "es"],
  ["spell difficulty", "Lesser Magic · difficulty Information unavailable", "en"],
  ["serious-injury result", "11-15 — TODO-TRANSLATE", "es"],
] as const;

describe("visible fallback families closed after 4631eae", () => {
  for (const family of FAMILIES) {
    it(`${family.name} publishes no pending translation`, () => {
      const location = new RegExp(`^${family.source.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}.*:(?:${family.fields.join("|")})\\.(?:es|en)$`);
      expect(display.translation_todos.filter((todo) => location.test(todo.location)).map((todo) => todo.location)).toEqual([]);
      const values = display.presentation_entries
        .filter((entry) => entry.source.startsWith(family.source))
        .flatMap((entry) => family.fields.flatMap((field) => Object.values(entry.fields[field] ?? {})));
      expect(values.filter((value) => value === "TODO-TRANSLATE")).toEqual([]);
      // The family must actually exist in the artefact: an empty set is not a pass.
      expect(values.length).toBeGreaterThan(0);
    });
  }

  it("composes every audited catalogue entry without a generic fallback", () => {
    let inspected = 0;
    for (const category of ["scenarios", "injuries", "spells", "equipment", "skills", "special-rules", "band-rules", "conditions", "core-rules"]) {
      for (const locale of ["es", "en"] as const) {
        for (const entry of catalogue.entries(category, locale)) {
          for (const [field, value] of [["effect", String(entry.effect)], ["name", String(entry.name)]] as const) {
            inspected += 1;
            const finding = classifyVisibleText(value, { locale, surface: `rules-catalogue/${category}`, category, field, ref: { kind: "rule", id: entry.entry_id } });
            expect(finding, `${category}/${entry.entry_id} ${field} (${locale}): ${finding?.found}`).toBeNull();
          }
          for (const tag of entry.tags) {
            inspected += 1;
            expect(classifyVisibleText(String(tag), { locale, surface: `rules-catalogue/${category}`, category })).toBeNull();
          }
        }
      }
    }
    expect(inspected).toBeGreaterThan(1000);
  });

  it("still reddens for the pre-fix shape of every family", () => {
    for (const [family, text, locale] of REGRESSIONS) {
      const finding = classifyVisibleText(text, { locale, surface: `regression/${family}` });
      expect(finding, `${family}: ${text}`).not.toBeNull();
      expect(["generic-fallback", "raw-text"]).toContain(finding?.kind);
    }
  });
});

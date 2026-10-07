/**
 * Equipment-catalogue completeness regression — the equipment family of the
 * dynamic visible-completeness layer (`gui-text-completeness.json`).
 *
 * Derived from the real generated artefact through the maintained loader and
 * the real `RulesCatalogue`, it walks EVERY published equipment entry in ES and
 * EN and requires:
 *
 * - a resolved name (never empty, never the entry id, never a generic fallback);
 * - a resolved effect: either the published description (the six exploration
 *   magical artefacts, whose text lives in the campaign table) or the specific
 *   localized absence notice for the canonical rows whose source publishes no
 *   description at all — never `Información no disponible` / `Information
 *   unavailable`, never an id;
 * - zero identifiers used as presentation and zero raw/pending markers;
 * - translation consistency: one English description maps to exactly one
 *   Spanish description inside the catalogue, and every entry resolves in both
 *   locales;
 * - KB↔staging parity where applicable: a row only carries the structured
 *   absence when the canonical source genuinely declares no prose field (the
 *   staging-parity side of that decision lives in the Python knowledge suite).
 *
 * The suite also pins the three resolution states apart: an absent description
 * (no declared field → structured notice), an unknown reference (rejected with
 * `unknown-reference`, never presented as absent content) and a resolution
 * error on a declared field (an ambiguous reference must not be disguised as an
 * absent description).
 */
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { fieldValues, sourceDescriptionUnavailableText } from "@adapters/knowledge-reader/presentation";
import { RulesCatalogue } from "@app/rules/rules-catalogue";
import { buildIdInventory, classifyVisibleText, GENERIC_FALLBACKS, RAW_MARKERS } from "../../../tools/web/presentation-completeness-detector.mjs";
import { readArtefactDocument } from "../../support/kb-artefact";

const PUBLISHED = resolve(process.cwd(), "..", "..", "outputs", "web-public", "knowledge", "knowledge-web.json");
const artefact = readArtefactDocument(PUBLISHED);
const knowledge = ArtefactKnowledgeReader.from(artefact);
const catalogue = new RulesCatalogue(knowledge);
const inventory = buildIdInventory(artefact);
const fallbackTexts = Object.values(GENERIC_FALLBACKS).flat();

const entries = { es: catalogue.entries("equipment", "es"), en: catalogue.entries("equipment", "en") };

/** The item row behind a catalogue entry, addressed exactly as `entryIdOf` does. */
const itemRows = new Map(knowledge.list("item").map((row) => [String(row.id ?? row.item_id ?? ""), row]));
const rowOf = (entryId: string) => itemRows.get(entryId);

/** Mirrors `RulesCatalogue.translatedText`: no `effect`/`description`/`text`/`note` declared. */
function declaresNoProse(row: Readonly<Record<string, unknown>> | undefined): boolean {
  if (!row) return false;
  return !(["effect", "description", "text", "note"] as const).some(
    (field) => field in row || `${field}_i18n` in row || Object.keys(fieldValues(row, field)).length,
  );
}

const realEffect = (text: string, locale: "es" | "en") =>
  Boolean(text.trim()) && text.trim() !== String(sourceDescriptionUnavailableText(locale)).trim();

describe("equipment catalogue resolves in ES and EN (real artefact)", () => {
  it("publishes the same entry ids in both locales", () => {
    const ids = (locale: "es" | "en") => entries[locale].map((entry) => entry.entry_id).sort();
    expect(ids("es")).toEqual(ids("en"));
  });

  it("resolves a real name for every entry in ES and EN", () => {
    for (const locale of ["es", "en"] as const) {
      for (const entry of entries[locale]) {
        expect(entry.name.trim(), `${entry.entry_id} name (${locale})`).not.toBe("");
        expect(entry.name, `${entry.entry_id} name as id (${locale})`).not.toBe(entry.entry_id);
        const finding = classifyVisibleText(entry.name, { locale, surface: "rules-catalogue/equipment", category: "equipment", field: "name", ref: { kind: "rule", id: entry.entry_id }, idInventory: inventory });
        expect(finding, `${entry.entry_id} name "${entry.name}" (${locale})`).toBeNull();
      }
    }
  });

  it("resolves an effect or a structured absence notice for every entry in ES and EN", () => {
    for (const locale of ["es", "en"] as const) {
      for (const entry of entries[locale]) {
        const absence = String(sourceDescriptionUnavailableText(locale)).trim();
        expect(entry.effect.trim(), `${entry.entry_id} effect (${locale})`).not.toBe("");
        expect(entry.effect, `${entry.entry_id} effect as id (${locale})`).not.toBe(entry.entry_id);
        expect(fallbackTexts.includes(entry.effect.trim()), `${entry.entry_id} generic fallback (${locale})`).toBe(false);
        expect(RAW_MARKERS.some((marker) => entry.effect.includes(marker)), `${entry.entry_id} raw marker (${locale})`).toBe(false);
        // A structured absence is only valid for a row that declares no prose.
        if (entry.effect.trim() === absence) {
          expect(declaresNoProse(rowOf(entry.entry_id)), `${entry.entry_id} absence with declared prose (${locale})`).toBe(true);
        }
        const finding = classifyVisibleText(entry.effect, { locale, surface: "rules-catalogue/equipment", category: "equipment", field: "effect", ref: { kind: "rule", id: entry.entry_id }, idInventory: inventory });
        // The product's specific localized notices are not fallbacks.
        if (finding?.kind === "generic-fallback" && fallbackTexts.includes(entry.effect.trim())) continue;
        expect(finding, `${entry.entry_id} effect "${entry.effect.slice(0, 80)}" (${locale})`).toBeNull();
      }
    }
  });

  it("never shows a generic fallback or an identifier as presentation", () => {
    for (const locale of ["es", "en"] as const) {
      for (const entry of entries[locale]) {
        for (const [field, text] of [["name", entry.name], ["effect", entry.effect]] as const) {
          expect(fallbackTexts.includes(text.trim()), `${entry.entry_id}.${field} (${locale})`).toBe(false);
          const finding = classifyVisibleText(text, { locale, surface: "rules-catalogue/equipment", category: "equipment", field, ref: { kind: "rule", id: entry.entry_id }, idInventory: inventory });
          expect(finding?.kind, `${entry.entry_id}.${field} (${locale})`).not.toBe("technical-id");
          expect(finding?.kind, `${entry.entry_id}.${field} (${locale})`).not.toBe("raw-text");
        }
      }
    }
  });

  it("keeps one Spanish description per English description", () => {
    const byEnglish = new Map<string, Set<string>>();
    for (const entry of entries.en) {
      const spanish = entries.es.find((candidate) => candidate.entry_id === entry.entry_id);
      if (!spanish || !realEffect(entry.effect, "en")) continue;
      if (!realEffect(spanish.effect, "es")) continue;
      const seen = byEnglish.get(entry.effect.trim()) ?? new Set<string>();
      seen.add(spanish.effect.trim());
      byEnglish.set(entry.effect.trim(), seen);
    }
    const conflicts = [...byEnglish.entries()].filter(([, spanish]) => spanish.size > 1);
    expect(conflicts.map(([english]) => english.slice(0, 60)).slice(0, 5)).toEqual([]);
  });

  it("reuses the canonical Spanish name of the magical artefacts", () => {
    // The campaign exploration table links one artefact to the canonical item
    // (Att'la's Plate Mail); the catalogue must show the canonical Spanish form.
    const canonical = knowledge.resolveKbText({ kind: "item", id: "runic_attlas_plate_mail" }, "name", "es");
    const entry = entries.es.find((candidate) => candidate.entry_id === "campaign.magical-artefact.attlas-plate-mail");
    expect(canonical.ok).toBe(true);
    expect(entry?.name).toBe(canonical.ok ? canonical.text : "");
  });
});

describe("equipment catalogue separates absence from resolution failures", () => {
  it("documents exactly 22 canonical rows whose source publishes no description", () => {
    const absent = entries.es.filter((entry) => entry.effect.trim() === String(sourceDescriptionUnavailableText("es")).trim());
    expect(absent.length).toBe(22);
    for (const entry of absent) {
      const row = rowOf(entry.entry_id);
      expect(row, `${entry.entry_id} row`).toBeDefined();
      expect(declaresNoProse(row), `${entry.entry_id} declares prose`).toBe(true);
    }
  });

  it("resolves the six exploration magical artefacts from published text", () => {
    const magical = entries.es.filter((entry) => entry.entry_id.startsWith("campaign.magical-artefact."));
    expect(magical.length).toBe(6);
    for (const entry of magical) {
      expect(realEffect(entry.effect, "es"), `${entry.entry_id} es effect`).toBe(true);
      const english = entries.en.find((candidate) => candidate.entry_id === entry.entry_id);
      expect(english && realEffect(english.effect, "en"), `${entry.entry_id} en effect`).toBe(true);
      expect(declaresNoProse(rowOf(entry.entry_id)), `${entry.entry_id} should declare its effect`).toBe(false);
    }
  });

  it("rejects an unknown reference instead of presenting it as absent content", () => {
    const unknown = knowledge.resolveKbText({ kind: "item", id: "does-not-exist" }, "effect", "es");
    expect(unknown).toMatchObject({ ok: false, reason: "unknown-reference" });
    expect(catalogue.entry("equipment", "does-not-exist", "es")).toBeNull();
  });

  it("does not disguise a resolution failure as an absent description", () => {
    // A declared field whose reference is ambiguous fails to resolve; that is a
    // resolution error, never the structured absence notice.
    const ambiguous = knowledge.resolveKbText({ kind: "rule", id: "abomination--fear" }, "effect", "es");
    expect(ambiguous.ok).toBe(false);
    if (!ambiguous.ok) expect(ambiguous.reason).toBe("ambiguous-reference");
    const entry = catalogue.entries("special-rules", "es").find((candidate) => candidate.entry_id === "abomination--fear");
    expect(entry?.effect).not.toBe(sourceDescriptionUnavailableText("es"));
  });
});

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
 * Current product state: `rules-prose.json` used to publish 1,924 rows under the
 * `special-rules` stem (68 shared + 1,856 band-local copies), so `RulesCatalogue`
 * rendered the copies as "Información no disponible". The generator now publishes
 * the promoted `shared-rule.*` catalogue there, and only that. The tests below
 * pin both halves of the contract: the shared tab carries the 68 real shared
 * rules, and excluding a band-local row from it is only legitimate while the row
 * stays correct and reachable in "Reglas de banda" (prose, search, profile links,
 * `rule_ref` names and every id a profile references).
 */
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { adaptDistanceText } from "@app/rules/distance-display";
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
const rulesProse = (artefact as Record<string, unknown>).rules_prose as Record<string, readonly Record<string, unknown>[]> | undefined;
const sharedRows = rulesProse?.["special-rules"] ?? [];
const bandRows = rulesProse?.["profile-special-rules"] ?? [];
const profiles = ((artefact as Record<string, unknown>).profiles as readonly Record<string, unknown>[] | undefined) ?? [];
const displayNames = ((artefact as Record<string, unknown>).display_names as Record<string, Record<string, string>> | undefined) ?? {};

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

  it("keeps the shared stem free of band-scoped rows (no band_id)", () => {
    const withBand = sharedRows.filter((row) => row.band_id != null && row.band_id !== "");
    expect(withBand.map((row) => String(row.id)).slice(0, 10)).toEqual([]);
  });

  it("shows the published, localized name and effect of each shared rule, ES and EN", () => {
    for (const locale of ["es", "en"] as const) {
      const entries = new Map(catalogue.entries("special-rules", locale).map((entry) => [entry.entry_id, entry]));
      expect(entries.size, `locale ${locale}`).toBe(SHARED_EXPECTED);
      for (const row of sharedRows) {
        const id = String(row.id);
        const entry = entries.get(id);
        expect(entry, `${id} missing from ${locale}`).toBeDefined();
        const names = (row.names ?? {}) as Record<string, string>;
        const effects = (row.effects ?? {}) as Record<string, string>;
        // The catalogue shows the published name and effect, adapted only by the
        // locale's distance convention: never a fallback, an id or a placeholder.
        expect(entry!.name, `${id}.name (${locale})`).toBe(names[locale]);
        expect(entry!.effect, `${id}.effect (${locale})`).toBe(adaptDistanceText(effects[locale], locale, id));
        expect(entry!.name.trim(), `${id}.name empty (${locale})`).not.toBe("");
        expect(entry!.effect.trim(), `${id}.effect empty (${locale})`).not.toBe("");
        expect(entry!.name, `${id}.name is id (${locale})`).not.toBe(id);
        expect(entry!.effect, `${id}.effect is id (${locale})`).not.toBe(id);
      }
    }
  });
});

/**
 * The other half of the contract: a band-local row is excluded from the shared
 * tab only while it stays correct and reachable in "Reglas de banda". These are
 * the legacy consumers that keep resolving the excluded ids (prose, search,
 * profile links, `rule_ref` labels and profile `rule_ids`).
 */
describe('the excluded band-local rules stay correct and reachable in "Reglas de banda"', () => {
  it("publishes the band-local rules in the band document, every one scoped by band", () => {
    expect(bandRows.length).toBeGreaterThan(1800);
    const unscoped = bandRows.filter((row) => row.band_id == null || row.band_id === "");
    expect(unscoped.map((row) => String(row.id)).slice(0, 10)).toEqual([]);
  });

  it('renders real localized prose for the "Reglas de banda" entries, ES and EN', () => {
    for (const locale of ["es", "en"] as const) {
      const entries = catalogue.entries("band-rules", locale);
      expect(entries.length, `locale ${locale}`).toBeGreaterThan(0);
      const broken = entries.filter((entry) =>
        entry.name.trim() === "" || entry.effect.trim() === "" ||
        entry.name === entry.entry_id || entry.effect === entry.entry_id ||
        fallbackTexts.includes(entry.name.trim()) || fallbackTexts.includes(entry.effect.trim()),
      );
      expect(broken.map((entry) => entry.entry_id).slice(0, 10), `locale ${locale}`).toEqual([]);
    }
  });

  it("loses no rule id: every id a profile references stays published somewhere", () => {
    const published = new Set<string>();
    for (const rows of Object.values(rulesProse ?? {})) {
      for (const row of rows) published.add(String(row.id));
    }
    const dangling: string[] = [];
    for (const profile of profiles) {
      for (const id of (profile.rule_ids as readonly unknown[] | undefined) ?? []) {
        if (!published.has(String(id))) dangling.push(`${String(profile.id)}→${String(id)}`);
      }
    }
    expect(profiles.length).toBeGreaterThan(0);
    expect(dangling.slice(0, 10)).toEqual([]);
  });

  it("still finds shared and band-local rules through search", () => {
    const shared = catalogue.search("always hungry", { locale: "en", category_id: "special-rules" });
    expect(shared.map((entry) => entry.entry_id)).toContain("shared-rule.always-hungry");
    const local = catalogue.search("Fear (Abomination)", { locale: "en", category_id: "band-rules" });
    expect(local.map((entry) => entry.rule_id)).toContain("abomination--fear");
    expect(catalogue.search("Miedo", { locale: "es", category_id: "band-rules" }).length).toBeGreaterThan(0);
  });

  it("still links shared rules to the warband profiles that carry them", () => {
    const leader = catalogue.entry("special-rules", "shared-rule.leader");
    expect(leader).not.toBeNull();
    const links = catalogue.profileLinks("special-rules", leader!);
    expect(links.length).toBeGreaterThan(0);
    expect([...new Set(links.map((link) => link.relation))]).toEqual(["special rule"]);
    const spanish = catalogue.profileLinks("special-rules", leader!, "es");
    expect([...new Set(spanish.map((link) => link.relation))]).toEqual(["regla especial"]);
  });

  it("keeps the referenced shared rule's name on rule_ref band rules", () => {
    const scoped = "averlanders:captain:captain--leader";
    expect(displayNames[scoped]).toBeDefined();
    expect(displayNames[scoped]).toEqual(displayNames["shared-rule.leader"]);
    expect(displayNames[scoped].es).toBe("Líder");
  });
});

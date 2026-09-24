/**
 * Parity port of desktop `tests/python/campaign/test_rules_catalogue.py` against the
 * real web KB artefact, driving the application-level `RulesCatalogue`
 * (seam source: `adapters/knowledge-reader/rules_catalogue_parity.test.ts`).
 */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { RulesCatalogue, type RuleEntry, type RulesCategory, type ProfileLink } from "@app/rules/rules-catalogue";
import type { CatalogueText } from "@app/rules/catalogue-text";

// @ts-expect-error A raw string is not a catalogue presentation value.
const rawCatalogueText: CatalogueText = "unreviewed";
// @ts-expect-error The catalogue cannot expose a raw entry name.
const rawEntryName: RuleEntry["name"] = "unreviewed";
// @ts-expect-error Category labels must come from fixed vocabulary.
const rawCategoryLabel: RulesCategory["label"] = "unreviewed";
// @ts-expect-error Profile relations must come from fixed vocabulary.
const rawRelation: ProfileLink["relation"] = "unreviewed";
void [rawCatalogueText, rawEntryName, rawCategoryLabel, rawRelation];

const ARTEFACT_PATH = resolve(__dirname, "../../../../outputs/web-public/knowledge/knowledge-web.json");
const ARTEFACT = JSON.parse(
  readFileSync(
    ARTEFACT_PATH,
    "utf-8",
  ),
) as Record<string, unknown>;
ARTEFACT.rules_prose = JSON.parse(
  readFileSync(resolve(ARTEFACT_PATH, "..", String(ARTEFACT.rules_prose_url)), "utf-8"),
);

function catalogue(): RulesCatalogue {
  return new RulesCatalogue(ArtefactKnowledgeReader.from(ARTEFACT));
}

describe("desktop test_rules_catalogue.py → web RulesCatalogue", () => {
  it("keeps canonical shared rules separate from scoped warband rules", () => {
    const c = catalogue();
    const sharedRules = c.entries("special-rules").filter((entry) => entry.entry_id.startsWith("shared-rule."));
    expect(sharedRules).toHaveLength(68);
    expect(c.entries("band-rules").length).toBeGreaterThan(900);
    expect(new Set(c.entries("band-rules").map((entry) => entry.entry_id)).size).toBe(c.entries("band-rules").length);
    expect(c.entries("conditions").length).toBeGreaterThan(0);
  });

  it("categories expose only non-empty ones in display order", () => {
    const ids = catalogue().categories().map((category) => category.category_id);
    expect(ids[0]).toBe("special-rules");
    for (const categoryId of ["band-rules", "conditions", "skills", "equipment", "spells", "scenarios", "injuries"]) {
      expect(ids).toContain(categoryId);
    }
  });

  it("entries carry localized names and effects", () => {
    const c = catalogue();
    const hungry = c.entry("special-rules", "shared-rule.always-hungry");
    expect(hungry?.name).toBe("Always Hungry");
    expect(hungry?.effect).toContain("A Troll requires");
    const spell = c.entry("spells", "spell.lesser-magic.fires-of-uzhul");
    expect(spell?.name).toBe("Fires of U'Zhul");
    expect(spell?.tags.join(" ")).toContain("difficulty 7");
  });

  it("spanish locale resolves i18n fields", () => {
    const c = catalogue();
    const hungry = c.entry("special-rules", "shared-rule.always-hungry", "es");
    expect(hungry?.name).toBe("Siempre Hambriento");
    expect(c.entry("skills", "skill.acrobat", "es")?.effect).toContain("Iniciativa");
    expect(c.entry("equipment", "sword", "es")?.effect).toContain("Cuerpo a cuerpo");
    expect(c.entry("injuries", "campaign.serious-injuries.hero", "es")?.effect).toContain("11-15 — Información no disponible");
    expect(c.entry("injuries", "campaign.serious-injuries.hero", "es")?.name).toBe("Tabla de Heridas Graves de Héroes");
    expect(c.entry("injuries", "campaign.serious-injuries.henchman", "es")?.name).toBe("Tabla de Heridas Graves de Secuaces");
    expect(c.entry("scenarios", "scenario.hidden-treasure", "es")?.effect).toContain("Experiencia:");
    const names = c.entries("equipment", "es").map((row) => row.name);
    expect(names).toEqual([...names].sort((a, b) => a.localeCompare(b, "es", { sensitivity: "base" })));
  });

  it("adapts distances in Spanish entries and search results", () => {
    const c = catalogue();
    const english = c.entry("spells", "spell.lesser-magic.fires-of-uzhul");
    const spanish = c.entry("spells", "spell.lesser-magic.fires-of-uzhul", "es");
    const leader = c.entry("special-rules", "shared-rule.leader", "es");
    const dread = c.entry("spells", "spell.lesser-magic.dread-of-aramar", "es");
    const waaagh = c.entry("special-rules", "shared-rule.waaagh", "es");
    expect(english?.effect).toContain('18"');
    expect(spanish?.effect).toContain("45 cm");
    expect(spanish?.effect).not.toContain('18"');
    expect(leader?.effect).toContain("15 cm");
    expect(dread?.effect).toContain("5D6 cm");
    expect(waaagh?.effect).toContain("+1D6+2 cm");
    expect(c.search("45 cm", { locale: "es" }).some((row) => row.entry_id === "spell.lesser-magic.fires-of-uzhul")).toBe(true);
  });

  it("search matches names and effects and ignores accents", () => {
    const c = catalogue();
    const hits = c.search("always hungry");
    expect(hits.some((row) => row.entry_id === "shared-rule.always-hungry")).toBe(true);
    const scoped = c.search("frenzy", { category_id: "conditions" });
    expect(scoped.length).toBeGreaterThan(0);
    expect(scoped.every((row) => row.category_id === "conditions")).toBe(true);
    expect(c.search("")).toEqual([]);
    expect(c.search("zzzz-no-such-entry")).toEqual([]);
  });

  it("entry accessor returns the entry or null", () => {
    const c = catalogue();
    const combatOrder = c.entry("core-rules", "combat-order");
    expect(combatOrder).not.toBeNull();
    expect(combatOrder?.effect.length).toBeGreaterThan(0);
    expect(c.entry("core-rules", "no-such-id")).toBeNull();
  });

  it("cross-links from skills to warband profiles", () => {
    const c = catalogue();
    const entry = c.entry("skills", "skill.acrobat");
    expect(entry).not.toBeNull();
    const links = c.profileLinks("skills", entry!);
    expect(links.length).toBeGreaterThan(0);
    expect(links.every((link) => ["skill table", "starting skill"].includes(link.relation))).toBe(true);
    expect(links.every((link) => link.band && link.profile)).toBe(true);
  });

  it("cross-links from equipment to warband profiles", () => {
    const c = catalogue();
    // The web artefact's equipment category is the item family; `dagger` is a
    // family member with profile links (desktop used blessed_water, a Trading
    // Post offer outside the web item family).
    const entry = c.entry("equipment", "dagger");
    expect(entry).not.toBeNull();
    const links = c.profileLinks("equipment", entry!);
    expect(links.length).toBeGreaterThan(0);
    expect(links.every((link) => ["permitted equipment", "starting equipment"].includes(link.relation))).toBe(true);
  });

  it("cross-links special rules to the profiles that receive them", () => {
    const c = catalogue();
    const entry = c.entry("special-rules", "shared-rule.leader");
    expect(entry).not.toBeNull();
    const links = c.profileLinks("special-rules", entry!);
    expect(links.length).toBeGreaterThan(0);
    expect(links.every((link) => link.relation === "special rule")).toBe(true);
  });

  it("cross-links from spells to wizard profiles", () => {
    const c = catalogue();
    const spell = c.entry("spells", "spell.prayers-of-sigmar.armour-of-righteousness");
    expect(spell).not.toBeNull();
    const links = c.profileLinks("spells", spell!);
    expect(links.length).toBeGreaterThan(0);
    expect(links.every((link) => link.relation === "spell lore")).toBe(true);
    expect(links.some((link) => link.profile.includes("Matriarch"))).toBe(true);
  });

  it("categories without roster semantics have no links", () => {
    const c = catalogue();
    const [first] = c.entries("conditions");
    expect(c.profileLinks("conditions", first)).toEqual([]);
  });

  it("never substitutes English or identifiers for missing Spanish catalogue text", () => {
    const data = structuredClone(ARTEFACT);
    const rules = data.rules_prose as Record<string, Record<string, unknown>[]>;
    rules["special-rules"] = [{ id: "technical_rule_id", names: { en: "English only" }, effect: "Untranslated prose" }];
    const c = new RulesCatalogue(ArtefactKnowledgeReader.from(data));
    const entry = c.entry("special-rules", "technical_rule_id", "es");
    expect(entry?.name).toBe("Información no disponible");
    expect(entry?.effect).toBe("Información no disponible");
    expect(c.categories("es").find((category) => category.category_id === "special-rules")?.label).toBe("Reglas compartidas");
  });

  it("localizes scenario enums and rule relations instead of displaying internal values", () => {
    const c = catalogue();
    const scenario = c.entry("scenarios", "scenario.hidden-treasure", "es");
    expect(scenario?.effect).toContain("Uno contra uno");
    expect(scenario?.effect).not.toContain("1v1");
    const rule = c.entry("special-rules", "shared-rule.leader", "es")!;
    expect(c.profileLinks("special-rules", rule, "es").every((link) => link.relation === "regla especial")).toBe(true);
  });
});

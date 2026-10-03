/**
 * F050 — readable EN/ES resolution of the canonical `campaign.limit.racial-maximum.*`
 * citations the published band-rule prose carries.
 *
 * The real artefact proves the Sisters case, the multi-citation rows and that no
 * browsable catalogue entry leaks an id; the synthetic controls prove the
 * resolver's explicit states (known, unknown, repeated, duplicated id, no
 * citation, partial row, missing translation) and that prose without a citation
 * never reads the campaign catalogue.
 */
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { unavailableText } from "@adapters/knowledge-reader/presentation";
import { resolveLimitCitations } from "@app/rules/reference-citations";
import { RulesCatalogue } from "@app/rules/rules-catalogue";
import { WarbandReferences } from "@app/rules/warband-reference";
import { readArtefactDocument, readArtefactReader } from "../../../support/kb-artefact";

const ARTEFACT_PATH = resolve(__dirname, "../../../../outputs/web-public/knowledge/knowledge-web.json");
const real = () => readArtefactReader(ARTEFACT_PATH);

/** Expected resolved statlines, computed from the published rows independently. */
const HUMAN = {
  en: "M 4, WS 6, BS 6, S 4, T 4, W 3, I 6, A 4, Ld 9",
  es: "M 10, HA 6, HP 6, F 4, R 4, H 3, I 6, A 4, L 9",
} as const;
const DWARF = {
  en: "M 3, WS 7, BS 6, S 4, T 5, W 3, I 5, A 4, Ld 10",
  es: "M 8, HA 7, HP 6, F 4, R 5, H 3, I 5, A 4, L 10",
} as const;
const BULL_CENTAUR = {
  en: "M 8, WS 7, BS 6, S 5, T 5, W 4, I 6, A 5, Ld 10",
  es: "M 20, HA 7, HP 6, F 5, R 5, H 4, I 6, A 5, L 10",
} as const;
const GRAVE_GUARD = {
  en: "M 5, WS 5, BS 5, S 4, T 4, W 4, I 5, A 4, Ld 10",
  es: "M 12, HA 5, HP 5, F 4, R 4, H 4, I 5, A 4, L 10",
} as const;
const ABSENCE = {
  en: "Racial maximums not published in the catalogue",
  es: "Máximos raciales no publicados en el catálogo",
} as const;

function synthetic(rows: readonly Readonly<Record<string, unknown>>[]): ArtefactKnowledgeReader {
  return ArtefactKnowledgeReader.from({
    schema_version: 1, ruleset: "test",
    bands: [{ id: "a", name: "A" }], profiles: [], skills: [], items: [],
    rules_prose: { "profile-special-rules": rows },
    campaign: {
      racial_maximums: [
        { id: "campaign.limit.racial-maximum.human", profile: "human", characteristics: {
          movement: 4, weapon_skill: 6, ballistic_skill: 6, strength: 4, toughness: 4,
          wounds: 3, initiative: 6, attacks: 4, leadership: 9,
        } },
        { id: "campaign.limit.racial-maximum.partial", profile: "partial", characteristics: { strength: 4 } },
      ],
    },
  });
}

describe("canonical limit citations", () => {
  it.each(["es", "en"] as const)("resolves the real Sisters maximum reference to its profile in %s", (locale) => {
    const entry = new WarbandReferences(real()).sheet("sisters-of-sigmar", locale)!.rules
      .find((rule) => rule.id === "band--human-maximum-characteristics")!;
    expect(String(entry.effect)).not.toContain("campaign.limit.");
    expect(String(entry.effect)).toContain(locale === "es" ? "Las Hermanas de Sigmar son Humanas" : "Sisters of Sigmar are Humans");
    expect(String(entry.effect)).toContain(HUMAN[locale]);
  });

  it.each(["es", "en"] as const)("resolves every published citation of the real catalogue in %s", (locale) => {
    const document = readArtefactDocument(ARTEFACT_PATH) as {
      rules_prose?: Record<string, readonly { id?: string; band_id?: string; effect?: string }[]>;
    };
    // Traceability: every published prose row whose source still carries a
    // canonical reference resolves through the catalogue without leaking it.
    const citing = Object.entries(document.rules_prose ?? {}).flatMap(([stem, rows]) =>
      rows.filter((row) => typeof row.effect === "string" && row.effect.includes("(campaign.limit.")).map((row) => ({ stem, row })),
    );
    expect(citing.length).toBeGreaterThanOrEqual(21);
    const catalogue = new RulesCatalogue(real());
    for (const { row } of citing) {
      const entry = catalogue.entry("band-rules", `${String(row.band_id)}:${String(row.id)}`, locale);
      expect(entry, `${row.band_id}:${row.id}`).not.toBeNull();
      expect(String(entry!.effect), `${row.band_id}:${row.id}`).not.toContain("campaign.limit.");
    }
    // Every browsable category of the real catalogue is free of raw ids and of
    // the absence label, which no current citation needs.
    const categories = catalogue.categories(locale).map((category) => category.category_id);
    const entries = categories.flatMap((category) => catalogue.entries(category, locale));
    expect(entries.length).toBeGreaterThan(1000);
    expect(entries.filter((entry) => String(entry.effect).includes("campaign.limit.")).map((entry) => entry.entry_id)).toEqual([]);
    expect(entries.filter((entry) => String(entry.effect).includes(ABSENCE[locale])).map((entry) => entry.entry_id)).toEqual([]);
    // A three-citation row resolves each linked profile, not only the first.
    const blackDwarfs = String(catalogue.entry("band-rules", "black-dwarfs:band--characteristic-maximum", locale)!.effect);
    expect(blackDwarfs).toContain(DWARF[locale]);
    expect(blackDwarfs).toContain(BULL_CENTAUR[locale]);
    expect(blackDwarfs).toContain(HUMAN[locale]);
    // A row that cites the same profile twice resolves both occurrences.
    const restlessDead = String(catalogue.entry("band-rules", "restless-dead:band--restless-dead-maximum-characteristics", locale)!.effect);
    expect(restlessDead.split(GRAVE_GUARD[locale])).toHaveLength(3);
    // Preservation: the canonical source reference is still published verbatim.
    const sisters = (document.rules_prose ?? {})["profile-special-rules"]
      ?.find((row) => row.band_id === "sisters-of-sigmar" && row.id === "band--human-maximum-characteristics");
    expect(sisters?.effect).toContain("(campaign.limit.racial-maximum.human)");
  });

  it.each(["es", "en"] as const)("resolves known, unknown and repeated synthetic citations in %s", (locale) => {
    const catalogue = new RulesCatalogue(synthetic([
      { id: "rule.known", name: "Known", effect: "A profile (campaign.limit.racial-maximum.human).", effect_i18n: { es: "Un perfil (campaign.limit.racial-maximum.human)." } },
      { id: "rule.unknown", name: "Unknown", effect: "A profile (campaign.limit.racial-maximum.absent).", effect_i18n: { es: "Un perfil (campaign.limit.racial-maximum.absent)." } },
      { id: "rule.repeated", name: "Repeated", effect: "One (campaign.limit.racial-maximum.human), two (campaign.limit.racial-maximum.human).", effect_i18n: { es: "Una (campaign.limit.racial-maximum.human), dos (campaign.limit.racial-maximum.human)." } },
      { id: "rule.partial", name: "Partial", effect: "A profile (campaign.limit.racial-maximum.partial).", effect_i18n: { es: "Un perfil (campaign.limit.racial-maximum.partial)." } },
    ]));
    expect(String(catalogue.entry("band-rules", "rule.known", locale)!.effect))
      .toBe(locale === "es" ? `Un perfil (${HUMAN.es}).` : `A profile (${HUMAN.en}).`);
    expect(String(catalogue.entry("band-rules", "rule.unknown", locale)!.effect))
      .toBe(locale === "es" ? `Un perfil (${ABSENCE.es}).` : `A profile (${ABSENCE.en}).`);
    expect(String(catalogue.entry("band-rules", "rule.repeated", locale)!.effect))
      .toBe(locale === "es" ? `Una (${HUMAN.es}), dos (${HUMAN.es}).` : `One (${HUMAN.en}), two (${HUMAN.en}).`);
    // A row that does not publish all nine characteristics is an explicit
    // absence in both locales, never a partial statline.
    expect(String(catalogue.entry("band-rules", "rule.partial", locale)!.effect))
      .toBe(locale === "es" ? `Un perfil (${ABSENCE.es}).` : `A profile (${ABSENCE.en}).`);
  });

  it.each(["es", "en"] as const)("refuses to choose between two rows published under one citation id in %s", (locale) => {
    // The maintained reader indexes this family by id, so the seam collapses a
    // duplicated id before the resolver runs. A caller that supplies two rows
    // for one id must not get an arbitrary pick: the citation degrades to the
    // explicit absence instead of a statline the catalogue does not define.
    const proseRow = { id: "rule.duplicated", name: "Duplicated", effect: "One (campaign.limit.racial-maximum.human).", effect_i18n: { es: "Una (campaign.limit.racial-maximum.human)." } };
    const reader = ArtefactKnowledgeReader.from({
      schema_version: 1, ruleset: "test",
      bands: [{ id: "a", name: "A" }], profiles: [], skills: [], items: [],
      rules_prose: { "profile-special-rules": [proseRow] },
    });
    const human = {
      movement: 4, weapon_skill: 6, ballistic_skill: 6, strength: 4, toughness: 4,
      wounds: 3, initiative: 6, attacks: 4, leadership: 9,
    };
    const duplicated = [
      { id: "campaign.limit.racial-maximum.human", profile: "human", characteristics: human },
      { id: "campaign.limit.racial-maximum.human", profile: "human-alternate", characteristics: { ...human, movement: 5 } },
    ];
    const text = reader.recordText(proseRow, "effect", locale);
    expect(String(resolveLimitCitations(text, () => duplicated, locale)))
      .toBe(locale === "es" ? `Una (${ABSENCE.es}).` : `One (${ABSENCE.en}).`);
  });

  it("leaves prose without a citation untouched and never reads the campaign catalogue for it", () => {
    // A deferred campaign catalogue that is not loaded: a prose row without a
    // canonical citation must still resolve, so reading a band rule never starts
    // depending on the fragment.
    const deferred = ArtefactKnowledgeReader.from({
      schema_version: 1, ruleset: "test", bands: [], profiles: [], skills: [], items: [],
      catalogue_url: "knowledge-catalogue.json", catalogue_digest: "unused",
      rules_prose: { "profile-special-rules": [{ id: "rule.plain", name: "Plain", effect: "No citation here." }] },
    });
    expect(String(new RulesCatalogue(deferred).entry("band-rules", "rule.plain", "en")!.effect)).toBe("No citation here.");
    const catalogue = new RulesCatalogue(synthetic([
      { id: "rule.plain", name: "Plain", effect: "No citation here.", effect_i18n: { es: "Sin cita aquí." } },
    ]));
    expect(String(catalogue.entry("band-rules", "rule.plain", "es")!.effect)).toBe("Sin cita aquí.");
  });

  it("keeps the existing missing-translation contract instead of inventing resolved text", () => {
    // The row declares no Spanish text: the reader answers with its localized
    // unavailable notice before any citation is interpreted. English still
    // resolves, so the state belongs to the row's translation, not the resolver.
    const catalogue = new RulesCatalogue(synthetic([
      { id: "rule.untranslated", name: "Untranslated", effect: "A profile (campaign.limit.racial-maximum.human)." },
    ]));
    expect(String(catalogue.entry("band-rules", "rule.untranslated", "en")!.effect)).toBe(`A profile (${HUMAN.en}).`);
    expect(String(catalogue.entry("band-rules", "rule.untranslated", "es")!.effect)).toBe(unavailableText("es"));
  });
});

import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { KnowledgeArtefact } from "@adapters/knowledge-reader/artefact-types";
import { presentationEntries } from "@adapters/knowledge-reader/presentation";
import { WarbandReferences } from "@app/rules/warband-reference";
import { readArtefactReader } from "../../../support/kb-artefact";

const real = () => new WarbandReferences(readArtefactReader(resolve(__dirname, "../../../../outputs/web-public/knowledge/knowledge-web.json")));

describe("warband reference sheets", () => {
  it.each(["es", "en"] as const)("resolves Sisters equipment, readable maxima and Augur restrictions in %s", (locale) => {
    const sheet = real().sheet("sisters-of-sigmar", locale)!;
    expect(sheet.equipment[0].items.find((item) => item.id === "blessed_water")).toMatchObject({ name: locale === "es" ? "Agua Bendita" : "Blessed Water", cost: 10 });
    expect(sheet.equipment[0].items.find((item) => item.id === "holy_tome")).toMatchObject({ name: locale === "es" ? "Tomo Sagrado" : "Holy Tome", cost: 120 });
    // F050: the canonical citation is rendered as the linked maximum profile,
    // in the active locale and with the surrounding rule prose preserved.
    const maximum = sheet.rules.find((rule) => rule.id === "band--human-maximum-characteristics")!;
    expect(maximum.effect).not.toContain("campaign.limit.");
    expect(maximum.effect).toContain(locale === "es" ? "Las Hermanas de Sigmar son Humanas" : "Sisters of Sigmar are Humans");
    expect(maximum.effect).toContain(locale === "es"
      ? "M 10, HA 6, HP 6, F 4, R 4, H 3, I 6, A 4, L 9"
      : "M 4, WS 6, BS 6, S 4, T 4, W 3, I 6, A 4, Ld 9");
    const restrictions = sheet.warriors.find((warrior) => warrior.id === "augur")?.restrictions;
    if (locale === "es") expect(restrictions).toBe("La Vidente nunca lleva armadura.");
    else expect(restrictions).toContain("armour");
  });

  it.each(["es", "en"] as const)("resolves Underworld list names, item references, recipients and restrictions in %s", (locale) => {
    const sheet = real().sheet("underworld-alliance-mim", locale)!;
    expect(sheet.equipment).toHaveLength(3);
    expect(sheet.equipment[0].name).toContain(locale === "es" ? "Lista de Equipo" : "Equipment List");
    const miscellaneous = sheet.equipment.find((list) => list.id === "miscellaneous-items")!;
    expect(miscellaneous.profiles).toHaveLength(4);
    const blowpipe = sheet.equipment.flatMap((list) => list.items).find((item) => item.id === "blowpipe")!;
    expect(blowpipe).toMatchObject({ name: locale === "es" ? "Cerbatana" : "Blowpipe", cost: 25 });
    expect(blowpipe.effect).toBeTruthy();
    for (const list of sheet.equipment) {
      expect(list.name).not.toMatch(/Información no disponible|Information unavailable/);
      for (const item of list.items) {
        expect(item.name).not.toMatch(/ausente|missing|unavailable|no disponible/i);
        expect(item.notes ?? "").not.toMatch(/Información no disponible|Information unavailable/);
      }
    }
    expect(sheet.warriors.find((warrior) => warrior.id === "giant-rats")?.restrictions).toBe(locale === "es" ? "Las Ratas Gigantes nunca usan armaduras ni armas." : "Giant Rats never use any armour or weapons.");
    expect(sheet.warriors.find((warrior) => warrior.id === "sewer-squigs")?.restrictions).toContain(locale === "es" ? "5D6-2,5 cm" : "2D6-1 inches");
  });

  it("reads the real Sisters sheet including recruitment, skills, equipment and prayers", () => {
    const sheet = real().sheet("sisters-of-sigmar", "es")!;
    expect(sheet.name).toBe("Hermanas de Sigmar");
    expect(sheet.roster).toMatchObject({ starting_gold: 500, minimum_models: 3, maximum_models: 15 });
    expect(sheet.warriors).toHaveLength(5);
    expect(sheet.warriors.find((warrior) => warrior.id === "sigmarite-matriarch")).toMatchObject({ cost: 70, experience: 20, minimum: 1, maximum: 1 });
    expect(sheet.warriors.find((warrior) => warrior.id === "augur")?.skillAccess).toEqual(["academic", "speed", "special"]);
    expect(sheet.abilities).toHaveLength(5);
    expect(sheet.magic[0].spells).toHaveLength(6);
    expect(sheet.equipment[0].items.find((item) => item.id === "sigmarite_hammer")?.cost).toBe(15);
    expect(sheet.equipment[0]).toMatchObject({ complete: true, name: "Lista de Equipo de las Hermanas de Sigmar" });
    expect(sheet.equipment[0].profiles).toContain("Vidente");
    expect(sheet.equipment[0].items.find((item) => item.id === "dagger")?.notes).toBe("Primera daga gratis; las siguientes cuestan 2 co.");
    expect(sheet.equipment[0].items.find((item) => item.id === "holy_tome")?.notes).toBe("Solo heroínas.");
  });

  it("includes bands without rules and searches names only, ignoring accents", () => {
    const references = real();
    expect(references.list("es").length).toBeGreaterThan(80);
    expect(references.list("es", "HERMANAS DE SIGMAR").map((band) => band.id)).toEqual(["sisters-of-sigmar"]);
    expect(references.list("es", "matriarca")).toEqual([]);
    const empty = new WarbandReferences(ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [{ id: "empty", name: "Empty", name_i18n: { es: "Vacía" } }], profiles: [], items: [], skills: [], campaign: {} }));
    expect(empty.list("es", "vacia")).toHaveLength(1);
    expect(empty.sheet("empty", "es")?.rules).toEqual([]);
    expect(empty.sheet("missing", "es")).toBeNull();
  });

  it("keeps duplicated profile and rule identities in their owning band", () => {
    const references = new WarbandReferences(ArtefactKnowledgeReader.from({
      schema_version: 1, ruleset: "test", items: [], skills: [], campaign: {},
      bands: [{ id: "a", name: "A" }, { id: "b", name: "B" }],
      profiles: [{ id: "leader", band_id: "a", name: "Own leader" }, { id: "leader", band_id: "b", name: "Foreign leader" }],
      rules_prose: { "profile-special-rules": [
        { id: "same", band_id: "a", name: "Own rule", effect: "Own effect", applies_to: { profile_ids: ["leader"] } },
        { id: "same", band_id: "b", name: "Foreign rule", effect: "Foreign effect", applies_to: { profile_ids: ["leader"] } },
      ] },
    }));
    const sheet = references.sheet("a", "en")!;
    expect(sheet.warriors).toHaveLength(1);
    expect(sheet.warriors[0].name).toBe("Own leader");
    expect(sheet.warriors[0].rules.map((rule) => rule.effect)).toEqual(["Own effect"]);
  });

  it("accepts complete list metadata and shared-rule delegation without applying variants to the base roster", () => {
    const document: KnowledgeArtefact = {
      schema_version: 1, ruleset: "test", skills: [],
      bands: [{ id: "a", name: "A", roster: { starting_gold: 500, members: [{ profile_id: "leader", minimum: 1, maximum: 1 }] }, variants: [{ id: "rich", name: "Rich", starting_gold: 600, roster_members: [{ profile_id: "leader", maximum: 2 }], equipment_lists: ["own-list"] }] }],
      profiles: [{ id: "leader", band_id: "a", name: "Leader", equipment_access: [{ item_id: "dagger", list_id: "own-list" }] }],
      items: [{ item_id: "dagger", name: "Dagger", name_i18n: { es: "Daga" }, effect: "A dagger.", effect_i18n: { es: "Una daga." } }],
      rules_prose: { "special-rules": [{ id: "shared-rule.leader", name: "Leadership", name_i18n: { es: "Liderazgo" }, effect: "Leads.", effect_i18n: { es: "Dirige." } }] },
      campaign: { "warband-reference": { rows: [{ band_id: "a",
        equipment_lists: [{ id: "own-list", name: "Equipment", name_i18n: { es: "Equipo propio" }, items: [{ item_id: "dagger", cost: 2, notes: "First free", notes_i18n: { es: "Primera gratis" } }] }],
        rule_refs: [{ id: "local-leader", rule_ref: "shared-rule.leader", applies_to: { profile_ids: ["leader"] } }],
        profile_restrictions: [{ profile_id: "leader", notes: "No armour", notes_i18n: { es: "Sin armadura" } }],
      }] } },
    };
    // Production metadata uses the generator's nested presentation entries.
    // The adapter's small-fixture index only covers the established families.
    const listSource = "campaign/warband-reference/rows/[band_id=a]/equipment_lists/[id=own-list]";
    const references = new WarbandReferences(ArtefactKnowledgeReader.from({ ...document, presentation_entries: [
      ...presentationEntries(document),
      { ref: { kind: "record", id: "own-list", bandId: "a" }, source: listSource, fields: { name: { en: "Equipment", es: "Equipo propio" } } },
      { ref: { kind: "record", id: `${listSource}/items/[item_id=dagger]`, bandId: "a" }, source: `${listSource}/items/[item_id=dagger]`, fields: { notes: { en: "First free", es: "Primera gratis" } } },
      { ref: { kind: "record", id: "restriction", bandId: "a" }, source: "campaign/warband-reference/rows/[band_id=a]/profile_restrictions/[profile_id=leader]", fields: { notes: { en: "No armour", es: "Sin armadura" } } },
    ] }));
    const sheet = references.sheet("a", "es")!;
    expect(sheet.equipment[0]).toMatchObject({ name: "Equipo propio", complete: true });
    expect(sheet.equipment[0].items[0]).toMatchObject({ name: "Daga", notes: "Primera gratis", cost: 2 });
    expect(sheet.warriors[0].rules[0]).toMatchObject({ name: "Liderazgo", effect: "Dirige." });
    expect(sheet.warriors[0].restrictions).toBe("Sin armadura");
    expect(sheet.roster.starting_gold).toBe(500);
    expect(sheet.warriors[0].maximum).toBe(1);
    expect(sheet.variants[0]).toMatchObject({ gold: 600, lists: ["Equipo propio"], members: [{ maximum: 2 }] });
  });
});

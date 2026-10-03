/**
 * F044 contract fixture: the two equipment-access declarations the strict audit
 * cannot see in today's documents are consumed by the maintained reference
 * projection.
 *
 * A list-level `notes`/`notes_i18n` pair, published from the list row, is
 * resolved per locale; `applies_to.profile_types` selects the recipients over
 * the same profile kinds `profiles.yaml` declares. Everything below is a
 * clearly synthetic fixture — never a canonical warband — and nothing here
 * grants equipment or changes an eligibility decision: the executable rules
 * live in the shared construction module, not in this projection.
 */
import { describe, expect, it } from "vitest";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { KnowledgeArtefact } from "@adapters/knowledge-reader/artefact-types";
import { presentationEntries } from "@adapters/knowledge-reader/presentation";
import { WarbandReferences } from "@app/rules/warband-reference";

const BAND = "contract-fixture";
const MIXED_LIST = "mixed-list";

/** Locator of one published list row, the shape the generator writes. */
const listSource = (id: string) => `campaign/warband-reference/rows/[band_id=${BAND}]/equipment_lists/[id=${id}]`;

function fixture(): KnowledgeArtefact {
  const note = { en: "Synthetic list note.", es: "Nota sintética de la lista." };
  const document: KnowledgeArtefact = {
    schema_version: 1, ruleset: "contract-fixture", skills: [],
    bands: [{ id: BAND, name: "Synthetic band" }],
    items: [{ item_id: "dagger", name: "Synthetic dagger", effect: "Synthetic effect.", effect_i18n: { es: "Efecto sintético." } }],
    profiles: [
      { id: "synthetic-hero", band_id: BAND, name: "Synthetic hero", name_i18n: { es: "Héroe sintético" }, type: "hero", equipment_access: [] },
      { id: "synthetic-beast", band_id: BAND, name: "Synthetic beast", name_i18n: { es: "Bestia sintética" }, type: "animal", equipment_access: [] },
      { id: "synthetic-henchman", band_id: BAND, name: "Synthetic henchman", name_i18n: { es: "Secuaz sintético" }, type: "henchman", equipment_access: [] },
    ],
    campaign: { "warband-reference": { rows: [{
      band_id: BAND,
      equipment_lists: [
        { id: MIXED_LIST, name: "Mixed list", name_i18n: { es: "Lista mixta" }, notes: note.en, notes_i18n: { es: note.es },
          applies_to: { profile_types: ["hero", "animal"] }, items: [{ item_id: "dagger", cost: 2 }] },
        { id: "henchman-list", name: "Henchman list", name_i18n: { es: "Lista de secuaces" },
          applies_to: { profile_types: ["henchman"] }, items: [{ item_id: "dagger", cost: 3 }] },
        { id: "summoned-list", name: "Summoned list", name_i18n: { es: "Lista de invocados" },
          applies_to: { profile_types: ["summoned"] }, items: [{ item_id: "dagger", cost: 4 }] },
      ],
      rule_refs: [], profile_restrictions: [],
    }] } },
  };
  return { ...document, presentation_entries: [
    ...presentationEntries(document),
    { ref: { kind: "record", id: MIXED_LIST, bandId: BAND }, source: listSource(MIXED_LIST), fields: { name: { en: "Mixed list", es: "Lista mixta" }, notes: note } },
    { ref: { kind: "record", id: "henchman-list", bandId: BAND }, source: listSource("henchman-list"), fields: { name: { en: "Henchman list", es: "Lista de secuaces" } } },
    { ref: { kind: "record", id: "summoned-list", bandId: BAND }, source: listSource("summoned-list"), fields: { name: { en: "Summoned list", es: "Lista de invocados" } } },
  ] };
}

const references = () => new WarbandReferences(ArtefactKnowledgeReader.from(fixture()));

describe("equipment-access list contract", () => {
  it("resolves the list-level note in both locales, and reports none for a list without one", () => {
    const english = references().sheet(BAND, "en")!;
    const spanish = references().sheet(BAND, "es")!;
    expect(english.equipment.find((list) => list.id === MIXED_LIST)?.notes).toBe("Synthetic list note.");
    expect(spanish.equipment.find((list) => list.id === MIXED_LIST)?.notes).toBe("Nota sintética de la lista.");
    expect(english.equipment.find((list) => list.id === "henchman-list")?.notes).toBeUndefined();
  });

  it("selects the recipients of a list by the declared profile kinds", () => {
    const equipment = references().sheet(BAND, "en")!;
    const mixed = equipment.equipment.find((list) => list.id === MIXED_LIST)!;
    expect(mixed.profiles).toHaveLength(2);
    expect(mixed.profiles).toEqual(expect.arrayContaining(["Synthetic hero", "Synthetic beast"]));
    expect(mixed.profiles).not.toContain("Synthetic henchman");
    expect(equipment.equipment.find((list) => list.id === "henchman-list")!.profiles).toEqual(["Synthetic henchman"]);
    expect(equipment.equipment.find((list) => list.id === "summoned-list")!.profiles).toEqual([]);
    const spanish = references().sheet(BAND, "es")!;
    expect(spanish.equipment.find((list) => list.id === "henchman-list")!.profiles).toEqual(["Secuaz sintético"]);
  });
});

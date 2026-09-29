import { describe, expect, it } from "vitest";
import { ArtefactKnowledgeReader, resolveName } from "@adapters/knowledge-reader/index";
import { PresentationIndex, fieldValues } from "@adapters/knowledge-reader/presentation";

describe("strict presentation contract", () => {
  const entries = [
    { ref: { kind: "rule", id: "same", bandId: "a" }, source: "a", fields: { name: { en: "First", es: "Primera" } } },
    { ref: { kind: "rule", id: "same", bandId: "b" }, source: "b", fields: { name: { en: "Second", es: "Segunda" } } },
    { ref: { kind: "item", id: "same" }, source: "item", fields: { name: { en: "Item", es: "Objeto" } } },
  ];
  it("uses the kind and exact scope, rejecting absent or ambiguous references", () => {
    const index = new PresentationIndex(entries);
    expect(index.resolve({ kind: "item", id: "same" }, "name", "es")).toMatchObject({ ok: true, text: "Objeto", locale: "es", source: "item" });
    expect(index.resolve({ kind: "rule", id: "same", bandId: "b" }, "name", "es")).toMatchObject({ ok: true, text: "Segunda" });
    expect(index.resolve({ kind: "rule", id: "same" }, "name", "es")).toMatchObject({ ok: false, reason: "ambiguous-reference" });
    expect(index.resolve({ kind: "rule", id: "same", bandId: "wrong" }, "name", "es")).toMatchObject({ ok: false, reason: "unknown-reference" });
  });
  it.each([undefined, "", "TODO-TRANSLATE"])("rejects missing or pending translations: %s", (es) => {
    const index = new PresentationIndex([{ ref: { kind: "item", id: "technical_id" }, source: "items/[item_id=technical_id]", fields: { name: { en: "English", ...(es === undefined ? {} : { es }) } } }]);
    expect(index.resolve({ kind: "item", id: "technical_id" }, "name", "es")).toMatchObject({ ok: false, reason: "missing-translation" });
    expect(resolveName({ id: "technical_id", names: { en: "English", es } }, "es")).toBe("Información no disponible");
  });
  it("does not return captured labels or technical values for unknown entities", () => {
    const reader = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [], items: [], skills: [] });
    expect(reader.itemName("internal_tag", "es")).toBe("Información no disponible");
    expect(reader.displayNameText({ kind: "item", id: "internal_tag" }, "es")).toMatchObject({ status: "missing", sourceLocale: null });
    expect(reader.legacyText("internal_tag", "en")).toBe("Information unavailable");
    reader.displayNameText({ kind: "item", id: "internal_tag" }, "es");
    expect(reader.presentationDiagnostics()).toEqual([{ ok: false, reason: "unknown-reference", ref: { kind: "item", id: "internal_tag" }, field: "name", locale: "es" }]);
  });
  it("does not treat an effect operation array as translated prose", () => {
    expect(fieldValues({ effects: [{ type: "warrior.internal_tag" }], note: "English note", note_i18n: { es: "Nota" } }, "effect")).toEqual({});
  });
  it("lets explicit pending translations invalidate canonical text", () => {
    expect(fieldValues({ name: "Old text", names: { en: "TODO-TRANSLATE", es: "Nombre" } }, "name")).toEqual({ es: "Nombre" });
    expect(fieldValues({ name: "Old text", name_i18n: { en: "" } }, "name")).toEqual({});
  });
  it("rejects ambiguous captured labels even when their translations agree", () => {
    const reader = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [], skills: [], items: [
      { item_id: "one", names: { en: "Same", es: "Igual" } },
      { item_id: "two", names: { en: "Same", es: "Igual" } },
    ] });
    expect(reader.legacyText("Same", "es")).toBe("Información no disponible");
  });
  it("resolves legacy abilities only by exact identity and available owner context", () => {
    const reader = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [], items: [], skills: [], rules_prose: { rules: [
      { id: "a--rule", band_id: "a", applies_to: { profile_ids: ["mage"] }, names: { en: "Same", es: "Igual" } },
      { id: "b--rule", band_id: "b", applies_to: { profile_ids: ["mage"] }, names: { en: "Same", es: "Igual" } },
    ] } });
    expect(reader.legacyAbilityRef("Same", "mage", "a")).toEqual({ kind: "rule", id: "a--rule", bandId: "a", profileId: "mage" });
    expect(reader.legacyAbilityRef("Same", "mage")).toBeUndefined();
    expect(reader.legacyAbilityRef("same", "mage", "a")).toBeUndefined();
    expect(reader.legacyAbilityRef("a--rule", "mage", "b")).toBeUndefined();
  });
  it("resolves an ambiguous captured label inside the owning profile's declared rules", () => {
    const reader = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], items: [], skills: [],
      profiles: [{ id: "matriarch", names: { en: "Matriarch", es: "Matriarca" }, rule_ids: ["matriarch--leader"] }],
      rules_prose: { rules: [
        { id: "matriarch--leader", names: { en: "Leader", es: "Líder" } },
        { id: "foreign--leader", names: { en: "Leader", es: "Líder ajeno" } },
      ] },
    });
    // The shared display name alone stays unresolved: no owner context, no row.
    expect(reader.legacyAbilityRef("Leader")).toBeUndefined();
    // The profile declares exactly one of them, so its own capture resolves.
    expect(reader.legacyAbilityRef("Leader", "matriarch")).toEqual({ kind: "rule", id: "matriarch--leader" });
    // A profile that declares no such rule gains nothing from the label.
    expect(reader.legacyAbilityRef("Leader", "stranger")).toBeUndefined();
  });
  it.each([
    null,
    [{ ref: { kind: "item", id: "id" }, source: "items/[item_id=id]", fields: { name: { es: 1 } } }],
    [{ ref: { kind: "item", id: "id", bandId: 7 }, source: "items/[item_id=id]", fields: {} }],
    [entries[0], entries[0]],
  ])("rejects malformed or duplicate presentation data at the input boundary", (presentation_entries) => {
    expect(() => ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [], items: [], skills: [], presentation_entries })).toThrow();
  });
  it("rejects mixed display artefacts when loading", async () => {
    const main = { schema_version: 1, ruleset: "test", bands: [], profiles: [], items: [], skills: [], presentation_digest: "new", display_text_url: "display.json" };
    const fetcher = (async (url: string) => new Response(JSON.stringify(url.endsWith("display.json") ? { presentation_digest: "old", presentation_entries: [] } : main))) as typeof fetch;
    await expect(ArtefactKnowledgeReader.fromUrl("http://localhost/knowledge.json", fetcher)).rejects.toThrow("Incompatible display");
  });
});

/**
 * The presentation index joins an entry to the row it describes through a
 * stable locator, never through the position the row occupies in an array.
 *
 * The negative case comes first: the superseded format addressed a rule as
 * `rules_prose/special-rules/1`, so inserting one row moved every later entry
 * onto another rule's prose. The remaining assertions are the regression that
 * keeps that from coming back, plus the rejections the contract now owes:
 * a locator that addresses no row, a shifted hint two rows could claim, a
 * duplicate identity and an ambiguous scope.
 */
import { describe, expect, it } from "vitest";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { locatorError, locatorStep, locatorSteps, presentationEntries } from "@adapters/knowledge-reader/presentation";

type Row = Record<string, unknown>;

const rule = (id: string, en: string, es: string): Row => ({
  id,
  names: { en, es },
  effect: `${en} effect`,
  effect_i18n: { es: `${es} efecto` },
});

/** A small but complete document: bands, a profile, equipment and shared rules. */
function document(rules: readonly Row[], campaign?: Row): Row {
  return {
    schema_version: 1,
    ruleset: "test",
    bands: [{ id: "barbarian", names: { en: "Barbarian", es: "Bárbaro" } }],
    profiles: [{ id: "chief", band_id: "barbarian", names: { en: "Chief", es: "Jefe" } }],
    items: [{ item_id: "sword", names: { en: "Sword", es: "Espada" } }],
    skills: [],
    rules_prose: { "special-rules": rules },
    ...(campaign ? { campaign } : {}),
  };
}

/** The superseded join: walk the source as a JSON path of array positions. */
function positionalWalk(root: unknown, source: string): Row | undefined {
  let node: unknown = root;
  for (const step of source.split("/")) {
    node = Array.isArray(node) ? node[Number(step)] : (node as Record<string, unknown> | undefined)?.[step];
  }
  return node && typeof node === "object" ? (node as Row) : undefined;
}

/** Follow plain object keys to an array of rows. */
function rows(root: Row, ...keys: string[]): Row[] {
  let node: unknown = root;
  for (const key of keys) node = (node as Row)[key];
  return node as Row[];
}

describe("stable presentation locators", () => {
  it("demonstrates the positional join it replaces: an inserted row moves every later entry", () => {
    const before = document([rule("shared-rule.a", "Alpha", "Alfa"), rule("shared-rule.b", "Beta", "Beta")]);
    const inserted = document([rule("shared-rule.zero", "Zero", "Cero"), ...rows(before, "rules_prose", "special-rules")]);
    // `shared-rule.b` was addressed by the second array position.
    expect(positionalWalk(before, "rules_prose/special-rules/1")).toMatchObject({ id: "shared-rule.b" });
    // One row in front of it is enough for the same address to reach another rule.
    expect(positionalWalk(inserted, "rules_prose/special-rules/1")).toMatchObject({ id: "shared-rule.a" });
  });

  it("addresses a row by its own identifier and the scope that makes it unambiguous", () => {
    expect(locatorStep([{ id: "only" }], 0)).toBe("[id=only]");
    expect(locatorStep([{ id: "same", band_id: "a" }, { id: "same", band_id: "b" }], 1)).toBe("[id=same,band_id=b]");
    expect(locatorStep([{ item_id: "dagger", list_id: "wizard" }, { item_id: "dagger", list_id: "mercenary" }], 0)).toBe("[item_id=dagger,list_id=wizard]");
  });

  it("always splits a selector before a key and never at a value carrying a slash", () => {
    expect(locatorSteps("rules_prose/localized-labels/[id=localized-label.Animal Handler – Horse/Warhorse]")).toEqual([
      "rules_prose",
      "localized-labels",
      "[id=localized-label.Animal Handler – Horse/Warhorse]",
    ]);
  });

  it("rejects the superseded positional format instead of walking it", () => {
    expect(locatorError("rules_prose/special-rules/1")).toBe(`invalid locator step "1"`);
    expect(locatorError("items/[item_id=sword]")).toBeNull();
    const artefact = document([rule("shared-rule.a", "Alpha", "Alfa")]);
    const entries = [{ ref: { kind: "rule", id: "shared-rule.a" }, source: "rules_prose/special-rules/0", fields: { name: { en: "Alpha", es: "Alfa" } } }];
    expect(() => ArtefactKnowledgeReader.from({ ...artefact, presentation_entries: entries })).toThrow(/Invalid presentation locator/);
  });

  it("keeps every id on its own prose when a row is inserted in front of it", () => {
    const rules = [rule("shared-rule.a", "Alpha", "Alfa"), rule("shared-rule.b", "Beta", "Beta"), rule("shared-rule.c", "Gamma", "Gama")];
    const before = document(rules);
    const entries = presentationEntries(before);
    expect(entries.some((entry) => entry.source.includes("rules_prose/special-rules/[id="))).toBe(true);
    const reader = ArtefactKnowledgeReader.from({ ...document([rule("shared-rule.zero", "Zero", "Cero"), ...rules]), presentation_entries: entries });
    expect(reader.resolveKbText({ kind: "rule", id: "shared-rule.b" }, "name", "es")).toMatchObject({ ok: true, text: "Beta" });
    expect(reader.resolveKbText({ kind: "rule", id: "shared-rule.c" }, "effect", "es")).toMatchObject({ ok: true, text: "Gama efecto" });
    expect(reader.resolveKbText({ kind: "item", id: "sword" }, "name", "es")).toMatchObject({ ok: true, text: "Espada" });
  });

  it("keeps every id on its own prose when the rows are reordered", () => {
    const rules = [rule("shared-rule.a", "Alpha", "Alfa"), rule("shared-rule.b", "Beta", "Beta"), rule("shared-rule.c", "Gamma", "Gama")];
    const entries = presentationEntries(document(rules));
    const reader = ArtefactKnowledgeReader.from({ ...document([...rules].reverse()), presentation_entries: entries });
    for (const [id, text] of [["shared-rule.a", "Alpha"], ["shared-rule.b", "Beta"], ["shared-rule.c", "Gamma"]] as const) {
      expect(reader.resolveKbText({ kind: "rule", id }, "name", "en")).toMatchObject({ ok: true, text });
    }
  });

  it("recovers an index-only step whose row moved, and rejects one two rows could claim", () => {
    // The producer emits these locators for rows whose published scalars are
    // identical and which only their prose tells apart.
    const hinted = (note: string): Row => ({ type: "step", notes: [note] });
    const campaign = (values: readonly Row[]): Row => ({ x: { options: values } });
    const entriesFor = (values: readonly string[]) => values.map((note, index) => ({
      ref: { kind: "record", id: `campaign/x/options/[#${index}]` },
      source: `campaign/x/options/[#${index}]`,
      fields: { notes: { en: note } },
    }));

    const ones = entriesFor(["Alpha", "Beta"]);
    const sameOrder = document([], campaign([hinted("Alpha"), hinted("Beta")]));
    expect(ArtefactKnowledgeReader.from({ ...sameOrder, presentation_entries: ones }).recordText(rows(sameOrder, "campaign", "x", "options")[0], "notes", "en")).toBe("Alpha");

    // The entry that said `[#0]` still reaches its own row, now at position 1.
    const shiftedDocument = document([], campaign([hinted("Zero"), hinted("Alpha"), hinted("Beta")]));
    const shifted = ArtefactKnowledgeReader.from({ ...shiftedDocument, presentation_entries: ones });
    expect(shifted.recordText(rows(shiftedDocument, "campaign", "x", "options")[1], "notes", "en")).toBe("Alpha");
    expect(shifted.recordText(rows(shiftedDocument, "campaign", "x", "options")[2], "notes", "en")).toBe("Beta");

    // Two rows whose published text is identical: a shifted hint cannot be
    // resolved by picking one of them.
    const twins = entriesFor(["Same", "Same"]);
    const ambiguous = document([], campaign([hinted("Other"), hinted("Same"), hinted("Same")]));
    expect(() => ArtefactKnowledgeReader.from({ ...ambiguous, presentation_entries: twins })).toThrow(/Ambiguous presentation locator/);
  });

  it("rejects a locator that addresses a row the document no longer publishes", () => {
    const rules = [rule("shared-rule.a", "Alpha", "Alfa"), rule("shared-rule.b", "Beta", "Beta")];
    const entries = presentationEntries(document(rules));
    const artefact = document([rules[0]]);
    expect(() => ArtefactKnowledgeReader.from({ ...artefact, presentation_entries: entries })).toThrow(/does not address a row/);
  });

  it("rejects a row whose prose was rewritten under the same identity", () => {
    const entries = presentationEntries(document([rule("shared-rule.a", "Alpha", "Alfa")]));
    const rewritten = document([rule("shared-rule.a", "Changed", "Cambiado")]);
    expect(() => ArtefactKnowledgeReader.from({ ...rewritten, presentation_entries: entries })).toThrow(/does not address a row/);
  });

  it("rejects a duplicate identity, and a scope whose prose contradicts the row", () => {
    const artefact = document([rule("shared-rule.a", "Alpha", "Alfa")]);
    const source = "rules_prose/special-rules/[id=shared-rule.a]";
    const duplicate = [
      { ref: { kind: "rule", id: "shared-rule.a" }, source, fields: { name: { en: "Alpha", es: "Alfa" } } },
      { ref: { kind: "rule", id: "shared-rule.a" }, source, fields: { name: { en: "Alpha", es: "Alfa" } } },
    ];
    expect(() => ArtefactKnowledgeReader.from({ ...artefact, presentation_entries: duplicate })).toThrow(/Duplicate presentation identity/);
    // Two scopes claim one row with different prose: the row can only carry one
    // of them, so the document is rejected instead of showing either silently.
    const scoped = [
      { ref: { kind: "rule", id: "shared-rule.a", bandId: "barbarian" }, source, fields: { name: { en: "Alpha", es: "Alfa" } } },
      { ref: { kind: "rule", id: "shared-rule.a", bandId: "reiklander" }, source, fields: { name: { en: "Other", es: "Otro" } } },
    ];
    expect(() => ArtefactKnowledgeReader.from({ ...artefact, presentation_entries: scoped })).toThrow(/does not address a row/);
  });

  it("resolves both locales from the same record, never from the id", () => {
    const reader = ArtefactKnowledgeReader.from(document([rule("shared-rule.a", "Alpha", "Alfa")]));
    expect(reader.resolveKbText({ kind: "rule", id: "shared-rule.a" }, "name", "en")).toMatchObject({ ok: true, text: "Alpha", ref: { kind: "rule", id: "shared-rule.a" } });
    expect(reader.resolveKbText({ kind: "rule", id: "shared-rule.a" }, "name", "es")).toMatchObject({ ok: true, text: "Alfa", ref: { kind: "rule", id: "shared-rule.a" } });
    expect(reader.resolveKbText({ kind: "item", id: "sword" }, "name", "en")).toMatchObject({ ok: true, text: "Sword" });
    expect(reader.resolveKbText({ kind: "item", id: "sword" }, "name", "es")).toMatchObject({ ok: true, text: "Espada" });
  });
});

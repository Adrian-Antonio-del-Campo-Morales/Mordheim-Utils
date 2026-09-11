/** Portable parity translation of tests/campaign/test_rules_catalogue.py. */
import { describe, expect, it } from "vitest";
import { ArtefactKnowledgeReader } from "./index";

function reader() {
  return ArtefactKnowledgeReader.from({
    schema_version: 1,
    ruleset: "mordheim",
    collections: [], bands: [], profiles: [], items: [], skills: [], weapon_hands: {},
    rules_prose: {
      "special-rules": [
        { id: "shared-rule.always-hungry", name: "Always Hungry", effect: "A Troll requires food." },
      ],
      conditions: [{ id: "condition.frenzy", name: "Frenzy", effect: "Frenzied fighters charge." }],
      "core-combat": [{ id: "combat-order", name: "Combat Order", effect: "Resolve initiative." }],
    },
    campaign: {},
  });
}

describe("desktop rules catalogue parity", () => {
  it("loads prose documents and preserves entry ids, names, and effects", () => {
    const catalogue = reader();
    expect(catalogue.rulesDocument("special-rules")).toHaveLength(1);
    expect(catalogue.rulesDocument("special-rules")[0]).toMatchObject({
      id: "shared-rule.always-hungry",
      name: "Always Hungry",
      effect: "A Troll requires food.",
    });
    expect(catalogue.rulesDocument("missing")).toEqual([]);
  });

  it("keeps campaign catalogue rows addressable by stable section", () => {
    const catalogue = ArtefactKnowledgeReader.from({
      schema_version: 1, ruleset: "mordheim", collections: [], bands: [], profiles: [], items: [], skills: [], weapon_hands: {},
      campaign: { scenarios: [{ id: "scenario.skirmish", name: "Skirmish" }] },
    });
    expect(catalogue.campaignRows("scenarios")).toEqual([{ id: "scenario.skirmish", name: "Skirmish" }]);
  });

  // application/rules/rules-catalogue.ts provides categories, localized
  // entries, accent-insensitive search and profile cross-links.
});

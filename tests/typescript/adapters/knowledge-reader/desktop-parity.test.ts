/** Portable parity tests translated from tests/python/campaign/test_knowledge_port.py. */
import { describe, expect, it } from "vitest";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

function artefact() {
  return {
    schema_version: 1,
    ruleset: "mordheim",
    collections: [{ id: "mordheim", name: "Mordheim", rulesets: ["mordheim"] }],
    bands: [
      {
        id: "sisters-of-sigmar",
        name: "Sisters of Sigmar",
        roster: { minimum_models: 3, maximum_models: 15, starting_gold: 500, hero_limit: 5 },
      },
      { id: "mercenaries", name: "Mercenaries", roster: { minimum_models: 3, maximum_models: 15 } },
    ],
    profiles: [
      {
        id: "sigmarite-matriarch", collection: "mordheim", band_id: "sisters-of-sigmar",
        name: "Sigmarite Matriarch", type: "hero", cost: 70, experience: 20,
        characteristics: { M: 4, WS: 4, BS: 4, S: 3, T: 3, W: 1, I: 4, A: 1, Ld: 8 },
        required: true, inherent_rules: ["Leader", "Prayers of Sigmar"],
        skill_tables: ["Combat", "Academic", "Strength", "Speed", "Special"],
      },
      { id: "sigmarite-sister", collection: "mordheim", band_id: "sisters-of-sigmar", name: "Sister", type: "henchman", group_maximum: 5 },
    ],
    items: [
      { item_id: "dagger", name: "Dagger", cost: 2 },
      { item_id: "light_armour", name: "Light Armour", cost: 20 },
    ],
    skills: [],
    campaign: {},
    weapon_hands: {},
  };
}

const reader = ArtefactKnowledgeReader.from(artefact());

describe("desktop KnowledgePort parity", () => {
  it("exposes canonical warband and profile ids without name-based lookup", () => {
    const band = reader.queryKnowledge({ id: { kind: "band_id", value: "sisters-of-sigmar" } });
    const profile = reader.queryKnowledge({ id: { kind: "profile_id", value: "sigmarite-matriarch" } });
    expect(band.ok).toBe(true);
    expect(profile.ok).toBe(true);
    expect(reader.queryKnowledge({ id: { kind: "band_id", value: "Sisters of Sigmar" } }).ok).toBe(false);
  });

  it("preserves canonical roster and profile rules as payload", () => {
    const band = reader.queryKnowledge({ id: { kind: "band_id", value: "sisters-of-sigmar" } });
    const profile = reader.queryKnowledge({ id: { kind: "profile_id", value: "sigmarite-matriarch" } });
    expect(band.ok && band.record.data["roster"]).toEqual({ minimum_models: 3, maximum_models: 15, starting_gold: 500, hero_limit: 5 });
    expect(profile.ok && profile.record.data["cost"]).toBe(70);
    expect(profile.ok && profile.record.data["required"]).toBe(true);
    expect(profile.ok && profile.record.data["inherent_rules"]).toEqual(["Leader", "Prayers of Sigmar"]);
    expect(profile.ok && profile.record.data["skill_tables"]).toEqual(["Combat", "Academic", "Strength", "Speed", "Special"]);
  });

  it("resolves canonical equipment ids and rejects unknown ids", () => {
    const dagger = reader.queryKnowledge({ id: { kind: "item_id", value: "dagger" } });
    expect(dagger.ok && dagger.record.data["cost"]).toBe(2);
    expect(reader.queryKnowledge({ id: { kind: "item_id", value: "does-not-exist" } })).toEqual({ ok: false, reason: "not_found" });
  });

  // Starter-legality enforcement exists in the kernel (draftIsLegal) and the
  // draft workflow (addRow/adjustGroup/commit); port the every-warband
  // legality matrix against those seams.
});

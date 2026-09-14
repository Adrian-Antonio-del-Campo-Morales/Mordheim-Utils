import { describe, expect, it } from "vitest";

import type { Warrior } from "./types";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { warriorAbilities, knowledgeName, localizedLabel } from "./displayText";

describe("warriorAbilities", () => {
  it("restores every inherent hireling ability in older campaign files", () => {
    const warrior = {
      id: "ranger#1",
      name: "Elf Ranger",
      profile_name: "Elf Ranger",
      profile_id: "hireling.hired-sword.elf-ranger",
      kind: "hireling",
      stats: {},
      equipment: [],
      skills: [],
      experience: 0,
      cost: 40,
    } as Warrior;
    const knowledge = {
      list: (kind: string) => kind === "hireling" ? [{
        id: warrior.profile_id,
        starting_skill_ids: [],
        rule_ids: [
          "hireling.hired-sword.elf-ranger.rule.seeker",
          "hireling.hired-sword.elf-ranger.rule.excellent-sight",
          "hireling.hired-sword.elf-ranger.rule.campaign-eligibility",
        ],
      }] : [],
    } as never;

    expect(warriorAbilities(knowledge, warrior)).toEqual([
      "hireling.hired-sword.elf-ranger.rule.seeker",
      "hireling.hired-sword.elf-ranger.rule.excellent-sight",
    ]);
  });
});

describe("localized UI labels", () => {
  it("translates stat and domain keys without exposing technical identifiers", () => {
    expect(localizedLabel("weapon_skill", "es")).toBe("Habilidad de Armas");
    expect(localizedLabel("gold_crowns", "es")).not.toBe("gold_crowns");
    expect(localizedLabel("campaign.follow_up.unknown", "es")).toBe("Información no disponible");
  });

  it("uses a readable fallback when a knowledge record is unavailable", () => {
    expect(knowledgeName(undefined, "item", "missing.item", "es")).toBe("Información no disponible");
    expect(knowledgeName(undefined, "skill", "missing.skill", "en")).toBe("Information unavailable");
    expect(knowledgeName(undefined, "item", "missing.item", "es", "Missing Item")).toBe("EN · traducción pendiente: Missing Item");
  });

  it("keeps canonical labels for normal records before falling back to the shared index", () => {
    const knowledge = ArtefactKnowledgeReader.from({
      schema_version: 1, ruleset: "mordheim", bands: [{ id: "sisters", names: { en: "Sisters", es: "Hermanas" } }],
      profiles: [{ id: "augur", names: { en: "Augur", es: "Vidente" } }], items: [{ item_id: "dagger", names: { en: "Dagger", es: "Daga" } }], skills: [],
      display_names: { "skill.blessed-sight": { en: "Blessed Sight", es: "Vista Bendecida" } },
      campaign: { "serious-injuries": { tables: [{ id: "hero", results: [{ id: "injury.hand", result: "Hand Injury" }] }] } },
    });
    expect(knowledgeName(knowledge, "band", "sisters", "es", "Sisters")).toBe("Hermanas");
    expect(knowledgeName(knowledge, "profile", "augur", "es", "Augur")).toBe("Vidente");
    expect(knowledgeName(knowledge, "item", "dagger", "es", "Dagger")).toBe("Daga");
    expect(knowledgeName(knowledge, "injury", "injury.hand", "es", "Hand Injury")).toBe("Herida en la Mano");
    expect(knowledgeName(knowledge, "skill", "skill.blessed-sight", "es")).toBe("Vista Bendecida");
  });
});

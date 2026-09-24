import { knowledgeHintDetails } from "./KnowledgeHintDetails";
import { describe, expect, it } from "vitest";

import type { Warrior } from "./types";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { warriorAbilities, variantName, knowledgeDescription, knowledgeName, localizedLabel, warriorName, readableValue, numberText, persistedSystemText } from "./displayText";

describe("saved presentation boundaries", () => {
  it("uses declared prose fields but never substitutes for a missing translation", () => {
    const reader = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [], skills: [], items: [
      { item_id: "note-only", names: { en: "Note", es: "Nota" }, note_i18n: { en: "A note", es: "Una nota" } },
      { item_id: "untranslated-effect", names: { en: "Effect", es: "Efecto" }, effect_i18n: { en: "The effect" }, note_i18n: { es: "No sustituye el efecto" } },
    ] });
    expect(knowledgeDescription(reader, { kind: "item", id: "note-only" }, "es").text).toBe("Una nota");
    expect(knowledgeDescription(reader, { kind: "item", id: "untranslated-effect" }, "es").status).toBe("missing");
    expect(knowledgeHintDetails({ knowledge: reader, kind: "item", id: "untranslated-effect", locale: "es" }).tooltip).toBe(knowledgeDescription(reader, { kind: "item", id: "untranslated-effect" }, "es").text);
    expect(knowledgeDescription(reader, { kind: "item", id: "untranslated-effect" }, "es").text).not.toContain("No sustituye");
  });
  it("resolves variants by their owning band without using captured display names", () => {
    const reader = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", profiles: [], items: [], skills: [], bands: [
      { id: "first", names: { es: "Primera", en: "First" }, variants: [{ id: "shared", names: { es: "Variante primera", en: "First variant" } }] },
      { id: "second", names: { es: "Segunda", en: "Second" }, variants: [{ id: "shared", names: { es: "Variante segunda", en: "Second variant" } }] },
    ] });
    expect(variantName(reader, "first", "shared", "es")).toBe("Variante primera");
    expect(variantName(reader, "second", "shared", "en")).toBe("Second variant");
    expect(variantName(reader, "missing", "shared", "es")).toBe("Información no disponible");
  });
  it("rejects strings disguised as numeric values", () => {
    expect(numberText("internal_tag", "es")).toBe("Información no disponible");
    expect(numberText(NaN, "en")).toBe("Information unavailable");
    expect(numberText(2.5, "es")).toBe("2,5");
  });
  it("resolves exact historical system messages without accepting arbitrary text", () => {
    expect(persistedSystemText("Captured camp occupied; captured stash contents are recorded manually during Equipment.", undefined, "es")).toContain("Campamento capturado");
    expect(persistedSystemText("INTERNAL_RULE_TAG", undefined, "es")).toBe("Información no disponible");
  });
});

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
  it("does not trust an imported locale map as presentation provenance", () => {
    expect(readableValue({ es: "internal_tag", en: "Raw English" }, "es")).toBe("Información no disponible");
    expect(readableValue({ en: "Raw English" }, "en")).toBe("Information unavailable");
  });
  it("shows the persisted warrior name without translating it", () => {
    const warrior={name:"Sigmarite Matriarch",profile_name:"Sigmarite Matriarch",profile_id:"matriarch"};
    const knowledge=ArtefactKnowledgeReader.from({schema_version:1,ruleset:"mordheim",bands:[],profiles:[{id:"matriarch",names:{en:"Sigmarite Matriarch",es:"Matriarca Sigmarita"}}],items:[],skills:[]});
    expect(warriorName(knowledge,warrior,"es")).toBe("Sigmarite Matriarch");
  });

  it("translates stat and domain keys without exposing technical identifiers", () => {
    expect(localizedLabel("weapon_skill", "es")).toBe("Habilidad de Armas");
    expect(localizedLabel("gold_crowns", "es")).not.toBe("gold_crowns");
    expect(localizedLabel("campaign.follow_up.unknown", "es")).toBe("Información no disponible");
  });

  it("uses a readable fallback when a knowledge record is unavailable", () => {
    expect(knowledgeName(undefined, "item", "missing.item", "es")).toBe("Información no disponible");
    expect(knowledgeName(undefined, "skill", "missing.skill", "en")).toBe("Information unavailable");
    expect(knowledgeName(undefined, "item", "missing.item", "es")).toBe("Información no disponible");
  });

  it("keeps canonical labels for normal records using exact references", () => {
    const knowledge = ArtefactKnowledgeReader.from({
      schema_version: 1, ruleset: "mordheim", bands: [{ id: "sisters", names: { en: "Sisters", es: "Hermanas" } }],
      profiles: [{ id: "augur", names: { en: "Augur", es: "Vidente" } }], items: [{ item_id: "dagger", names: { en: "Dagger", es: "Daga" } }], skills: [{ id: "skill.blessed-sight", names: { en: "Blessed Sight", es: "Vista Bendecida" } }],
      campaign: { "serious-injuries": { tables: [{ id: "hero", results: [{ id: "injury.hand", result: "Hand Injury", result_i18n: { es: "Herida en la Mano" } }] }] } },
    });
    expect(knowledgeName(knowledge, "band", "sisters", "es")).toBe("Hermanas");
    expect(knowledgeName(knowledge, "profile", "augur", "es")).toBe("Vidente");
    expect(knowledgeName(knowledge, "item", "dagger", "es")).toBe("Daga");
    expect(knowledgeName(knowledge, "injury", "injury.hand", "es")).toBe("Herida en la Mano");
    expect(knowledgeName(knowledge, "skill", "skill.blessed-sight", "es")).toBe("Vista Bendecida");
  });
});

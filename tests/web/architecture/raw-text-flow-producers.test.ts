/**
 * Marked-data proofs for the producers the flow tracer reports as carriers.
 *
 * `audit:gui:deep` flags the rules browser and the scenario award table as
 * `raw-text-flow` because their inputs are raw KB rows. These probes keep the
 * canonical fields, ids and stale captures poisoned at the source and assert
 * that only resolved, active-language text can reach presentation.
 * `presentation-poison.test.tsx` covers the mounted screens; this file covers
 * the producers those screens call.
 */

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { RulesCatalogue } from "@app/rules/rules-catalogue";
import { scenarioAwards } from "@app/campaign/features/battle/scenario-awards";
import { knowledgeName } from "@src/features/campaign/displayText";
import { presentationOutput } from "@src/features/campaign/presentation-output";
import { describe, expect, it } from "vitest";

const marker = "RAW_KB_POISON_";
const bandId = `${marker}BAND`;
const profileId = `${marker}PROFILE`;
const skillId = `${marker}SKILL`;
const untranslatedSkillId = `${marker}SKILL_UNTRANSLATED`;

function catalogueKnowledge() {
  return ArtefactKnowledgeReader.from({
    schema_version: 1,
    ruleset: "test",
    bands: [{ id: bandId, name: `${marker}BAND_NAME`, names: { es: "Banda marcada", en: "Marked band" } }],
    profiles: [{ id: profileId, band_id: bandId, name: `${marker}PROFILE_NAME`, names: { es: "Perfil marcado", en: "Marked profile" }, skill_access: ["Combat"] }],
    items: [],
    skills: [
      { id: skillId, name: `${marker}SKILL_NAME`, names: { es: "Habilidad marcada", en: "Marked skill" }, category: "Combat" },
      { id: untranslatedSkillId, name: `${marker}SKILL_UNTRANSLATED`, names: { es: "Sin categoría conocida", en: "Unknown category skill" }, category: `${marker}CATEGORY` },
      { id: `${marker}SKILL_CANONICAL_ONLY`, name: `${marker}SKILL_CANONICAL_ONLY` },
    ],
    rules_prose: {
      "special-rules": [
        {
          id: "shared-rule.marked",
          name: `${marker}NAME`,
          effect: `${marker}EFFECT`,
          names: { es: "Regla marcada", en: "Marked rule" },
          effect_i18n: { es: "Efecto marcado", en: "Marked effect" },
        },
        { id: "shared-rule.untranslated", name: `${marker}UNTRANSLATED`, effect_i18n: { en: `${marker}ENGLISH_ONLY` } },
      ],
    },
  });
}

/**
 * The scenario award prose lives in `campaign/experience-and-advances`, which
 * the generated artefact ships through its presentation index. The fixture
 * mirrors that contract with an explicit entry so `recordText` can bind the row.
 */
function awardsKnowledge() {
  return ArtefactKnowledgeReader.from({
    schema_version: 1,
    ruleset: "test",
    bands: [],
    profiles: [],
    skills: [],
    items: [],
    campaign: {
      scenarios: {
        scenarios: [{ id: "skirmish", progression: { experience: [{ ref: "award.survived" }, { amount: 1, amount_dice: `${marker}DICE`, effect: `${marker}MANUAL_EFFECT` }] } }],
      },
      "experience-and-advances": {
        awards: [
          {
            id: "award.survived",
            trigger: "survived_battle",
            effect: `${marker}AWARD_EFFECT`,
            effect_i18n: { es: "Todos los supervivientes ganan 1 EXP", en: "All survivors gain 1 EXP" },
          },
        ],
      },
    },
    presentation_entries: [
      {
        ref: { kind: "record", id: "campaign/experience-and-advances/awards/0" },
        fields: { effect: { es: "Todos los supervivientes ganan 1 EXP", en: "All survivors gain 1 EXP" } },
        source: "campaign/experience-and-advances/awards/0",
      },
    ],
  });
}

describe("rules browser presentation", () => {
  it("resolves names and prose in the active language without exposing markers or ids", () => {
    const entry = new RulesCatalogue(catalogueKnowledge()).entry("special-rules", "shared-rule.marked", "es")!;
    expect(presentationOutput(entry.name)).toBe("Regla marcada");
    expect(presentationOutput(entry.effect)).toBe("Efecto marcado");
    expect(`${entry.name} ${entry.effect}`).not.toContain(marker);
    // The id stays an identity: it is never turned into a label.
    expect(entry.entry_id).toBe("shared-rule.marked");
    expect(new RulesCatalogue(catalogueKnowledge()).entry("special-rules", "shared-rule.marked", "en")?.name).toBe("Marked rule");
  });

  it("keeps a declared but untranslated entry unavailable instead of falling back", () => {
    const entry = new RulesCatalogue(catalogueKnowledge()).entry("special-rules", "shared-rule.untranslated", "es")!;
    expect(presentationOutput(entry.name)).toBe("Información no disponible");
    expect(presentationOutput(entry.effect)).toBe("Información no disponible");
    expect(`${entry.name} ${entry.effect}`).not.toContain(marker);
  });

  it("builds tags from the closed vocabulary only", () => {
    const catalogue = new RulesCatalogue(catalogueKnowledge());
    expect(catalogue.entry("skills", skillId, "es")?.tags.map((tag) => presentationOutput(tag))).toEqual(["Combate"]);
    expect(catalogue.entry("skills", skillId, "en")?.tags.map((tag) => presentationOutput(tag))).toEqual(["Combat"]);
    // An unknown tag is dropped, never title-cased or shown as a label.
    expect(catalogue.entry("skills", untranslatedSkillId, "es")?.tags).toEqual([]);
  });

  it("resolves cross-links through KB rows while keeping profile ids as identity", () => {
    const catalogue = new RulesCatalogue(catalogueKnowledge());
    const links = catalogue.profileLinks("skills", catalogue.entry("skills", skillId, "es")!, "es");
    expect(links).toHaveLength(1);
    const [link] = links;
    expect(presentationOutput(link.band)).toBe("Banda marcada");
    expect(presentationOutput(link.profile)).toBe("Perfil marcado");
    expect(link.profile_id).toBe(profileId);
    expect(`${link.band} ${link.profile} ${link.relation}`).not.toContain(marker);
  });
});

describe("scenario award presentation", () => {
  it("resolves award prose in the active language and never uses a capture as the label", () => {
    const [structured, manual] = scenarioAwards(awardsKnowledge(), "skirmish", "es");
    expect(presentationOutput(structured.label)).toBe("Todos los supervivientes ganan 1 EXP");
    expect(structured.id).toBe("award.survived");
    expect(manual.id).toBe("skirmish:manual:1");
    // A stored effect that is not a resolved KB reference is a notice, not its text.
    expect(presentationOutput(manual.label)).toBe("Información no disponible");
    expect(`${structured.label} ${manual.label}`).not.toContain(marker);
  });

  it("returns nothing for an unknown scenario instead of inventing a label", () => {
    expect(scenarioAwards(awardsKnowledge(), `${marker}SCENARIO`, "es")).toEqual([]);
  });
});

describe("poisoned-source probe", () => {
  it("proves the fixtures are poisoned and that raw captures never leave the resolver", () => {
    const knowledge = catalogueKnowledge();
    expect(JSON.stringify(knowledge.list("skill"))).toContain(marker);
    expect(presentationOutput(knowledgeName(knowledge, "skill", skillId, "es"))).toBe("Habilidad marcada");
    expect(presentationOutput(knowledgeName(knowledge, "skill", skillId, "en"))).toBe("Marked skill");
    // Declared translations always win over the stale canonical capture.
    expect(presentationOutput(knowledgeName(knowledge, "skill", untranslatedSkillId, "es"))).toBe("Sin categoría conocida");
    expect(presentationOutput(knowledgeName(knowledge, "skill", untranslatedSkillId, "en"))).toBe("Unknown category skill");
    // Spanish never falls back to canonical English or to another language, and
    // an unknown reference is a localized notice, never an id.
    expect(presentationOutput(knowledgeName(knowledge, "skill", `${marker}SKILL_CANONICAL_ONLY`, "es"))).toBe("Información no disponible");
    expect(presentationOutput(knowledgeName(knowledge, "skill", `${marker}MISSING`, "en"))).toBe("Information unavailable");
  });
});

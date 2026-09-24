/**
 * P4.3 tests: the KnowledgeReader adapter against the *real* generated
 * artefact (when present) and against synthetic fixtures (always), covering:
 * - stable-id resolution and typed absence (`not_found`, never a guess);
 * - locale resolution chain (requested -> en -> any -> id);
 * - record immutability and payload preserve-in-place;
 * - corrupt artefact rejection (build must fail, per the plan).
 */
import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { ArtefactKnowledgeReader, resolveName } from "@adapters/knowledge-reader/index";

const REPO_ROOT = join(import.meta.dirname, "..", "..", "..", "..");
const ARTEFACT_PATH = join(
  REPO_ROOT,
  "build",
  "generated",
  "knowledge-web",
  "knowledge-web.json",
);

function syntheticArtefact() {
  return {
    schema_version: 1,
    ruleset: "mordheim",
    collections: [{ id: "mordheim", name: "Mordheim", rulesets: ["mordheim"] }],
    bands: [
      {
        id: "sisters-of-sigmar",
        name: "Sisters of Sigmar",
        name_i18n: { es: "Hermanas de Sigmar" },
        roster: { minimum_models: 3, maximum_models: 15 },
      },
      { id: "orc-mob", name: "Orc Mob", roster: {} },
    ],
    profiles: [
      {
        id: "sigmarite-matriarch",
        collection: "mordheim",
        band_id: "sisters-of-sigmar",
        name: "Sigmarite Matriarch",
        type: "hero",
        cost: 65,
      },
    ],
    items: [
      {
        item_id: "dagger",
        name: "Dagger",
        name_i18n: { es: "Daga" },
        kind: "close-combat-weapon",
      },
      { item_id: "mace", name: "Mace", kind: "close-combat-weapon" },
    ],
    skills: [{ id: "skill.acrobat", name: "Acrobat", name_i18n: { es: "Acróbata" }, category: "speed", effects: { en: "May fall safely.", es: "Puede caer sin sufrir daño." } }],
    rules_prose: { "profile-special-rules": [{ id: "augur--blessed-sight", names: { en: "Blessed Sight", es: "Vista Bendecida" }, effects: { es: "Puede repetir chequeos fallidos." }, band_id: "sisters-of-sigmar", applies_to: { profile_ids: ["augur"] } }] },
    mechanics: { skills: [{ id: "skill.blessed-sight", names: { en: "Blessed Sight", es: "Vista Bendecida" }, effects: { es: "Puede repetir chequeos fallidos." } }] },
    campaign: {
      scenarios: {
        scenarios: [
          { id: "scenario.defend-the-find", name: "Defend the Find", player_mode: "1v1" },
        ],
      },
      mutations: {
        mutations: [{ id: "campaign.mutation.daemon-soul", name: "Daemon Soul" }],
      },
      magic: {
        lores: [{ id: "lore.prayers-of-sigmar", name: "Prayers of Sigmar" }],
      },
      "serious-injuries": {
        tables: [
          {
            id: "table.serious-injuries-head",
            rows: [{ id: "injury.multiple-wounds", name: "Multiple Wounds" }],
          },
        ],
      },
      hirelings: {
        profiles: [{ id: "hireling.warrior", name: "Warrior" }],
      },
      warband_groups: [{ id: "warband-group.beastmen", band_ids: ["beastmen-raiders"] }],
      racial_maximums: [{ id: "campaign.limit.racial-maximum.black-orc" }],
      post_battle_sequence: [
        { id: "campaign.step.experience", name: "Experience", order: 2 },
      ],
    },
    weapon_hands: { "mech.two-handed": 2 },
  };
}

const reader = ArtefactKnowledgeReader.from(syntheticArtefact());

describe("artefact validation", () => {
  it("rejects non-object artefacts", () => {
    expect(() => ArtefactKnowledgeReader.from("nope")).toThrow();
    expect(() => ArtefactKnowledgeReader.from(null)).toThrow();
    expect(() => ArtefactKnowledgeReader.from([1, 2, 3])).toThrow();
  });

  it("rejects wrong schema_version and missing sections", () => {
    expect(() => ArtefactKnowledgeReader.from({ ...syntheticArtefact(), schema_version: 2 })).toThrow(/schema_version/);
    expect(() => {
      const broken = syntheticArtefact() as Record<string, unknown>;
      delete broken["profiles"];
      ArtefactKnowledgeReader.from(broken);
    }).toThrow(/profiles/);
  });
});

describe("stable id resolution", () => {
  it("resolves every KnowledgeKind by its stable id", () => {
    const cases = [
      { kind: "band_id", value: "sisters-of-sigmar" },
      { kind: "profile_id", value: "sigmarite-matriarch" },
      { kind: "item_id", value: "dagger" },
      { kind: "skill_id", value: "skill.acrobat" },
      { kind: "scenario_id", value: "scenario.defend-the-find" },
      { kind: "rule_id", value: "injury.multiple-wounds" },
      { kind: "lore_id", value: "lore.prayers-of-sigmar" },
      { kind: "hireling_id", value: "hireling.warrior" },
    ] as const;
    for (const id of cases) {
      const result = reader.queryKnowledge({ id, locale: "en" });
      expect(result.ok, `missing ${id.value}`).toBe(true);
      if (result.ok) {
        expect(result.record.id.value).toBe(id.value);
        expect(Object.keys(result.record.data).length).toBeGreaterThan(0);
      }
    }
  });

  it("returns typed not_found for unknown ids — never a name guess", () => {
    const result = reader.queryKnowledge({
      id: { kind: "item_id", value: "does-not-exist" },
    });
    expect(result).toEqual({ ok: false, reason: "not_found" });
  });

  it("does not mix id spaces (band id asked as item_id is not_found)", () => {
    const result = reader.queryKnowledge({
      id: { kind: "item_id", value: "sisters-of-sigmar" },
    });
    expect(result.ok).toBe(false);
  });
});

describe("locale resolution chain", () => {
  it("prefers the requested locale", () => {
    const band = reader.queryKnowledge({
      id: { kind: "band_id", value: "sisters-of-sigmar" },
      locale: "es",
    });
    expect(band.ok && band.record.names.es).toBe("Hermanas de Sigmar");
    expect(resolveName({ id: "sisters-of-sigmar", name: "Sisters of Sigmar", name_i18n: { es: "Hermanas de Sigmar" } }, "es")).toBe("Hermanas de Sigmar");
  });

  it("reports unavailable when the locale is missing", () => {
    expect(resolveName({ id: "mace", name: "Mace" }, "es")).toBe("Información no disponible");
  });

  it("never substitutes another locale or the identifier", () => {
    expect(resolveName({ id: "x", name: "", name_i18n: { es: "Hola" } }, "en")).toBe("Information unavailable");
    expect(resolveName({ id: "x" }, "en")).toBe("Information unavailable");
  });
});

describe("central display names", () => {
  it("requires typed references and keeps contextual rules exact", () => {
    expect(reader.resolveKbText({ kind: "skill", id: "skill.acrobat" }, "name", "es")).toMatchObject({ ok: true, text: "Acróbata" });
    const rule = { kind: "rule" as const, id: "augur--blessed-sight", bandId: "sisters-of-sigmar", profileId: "augur" };
    expect(reader.resolveKbText(rule, "name", "es")).toMatchObject({ ok: true, text: "Vista Bendecida" });
    expect(reader.resolveKbText({ kind: "skill", id: "skill.blessed-sight", scope: "global" }, "effect", "es")).toMatchObject({ ok: true, text: "Puede repetir chequeos fallidos." });
    expect(reader.resolveKbText({ ...rule, bandId: "wrong" }, "name", "es")).toMatchObject({ ok: false, reason: "unknown-reference" });
    expect(reader.resolveKbText({ kind: "skill", id: "missing.skill" }, "name", "es")).toMatchObject({ ok: false, reason: "unknown-reference" });
  });
});

describe("payload preserve-in-place", () => {
  it("travels the whole row verbatim except names", () => {
    const result = reader.queryKnowledge({
      id: { kind: "profile_id", value: "sigmarite-matriarch" },
    });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.record.data["cost"]).toBe(65);
      expect(result.record.data["type"]).toBe("hero");
      expect("names" in result.record.data).toBe(false);
    }
  });

  it("returns frozen record snapshots (no live references)", () => {
    const result = reader.queryKnowledge({
      id: { kind: "item_id", value: "dagger" },
    });
    expect(result.ok).toBe(true);
    if (result.ok) expect(Object.isFrozen(result.record.data)).toBe(true);
  });
});

describe("queryMany", () => {
  it("resolves many ids in one call preserving order", () => {
    const results = reader.queryMany([
      { id: { kind: "item_id", value: "mace" } },
      { id: { kind: "item_id", value: "nope" } },
      { id: { kind: "band_id", value: "orc-mob" } },
    ]);
    expect(results.map((r) => r.ok)).toEqual([true, false, true]);
  });
});

describe("real generated artefact", () => {
  const artefactExists = existsSync(ARTEFACT_PATH);
  it.skipIf(!artefactExists)("indexes the generated artefact end to end", () => {
    const artefact = JSON.parse(readFileSync(ARTEFACT_PATH, "utf-8"));
    const real = ArtefactKnowledgeReader.from(artefact);
    const band = real.queryKnowledge({
      id: { kind: "band_id", value: "sisters-of-sigmar" },
    });
    expect(band.ok).toBe(true);
    const item = real.queryKnowledge({
      id: { kind: "item_id", value: "dagger" },
    });
    expect(item.ok).toBe(true);
    const skill = real.queryKnowledge({
      id: { kind: "skill_id", value: "skill.acrobat" },
    });
    expect(skill.ok).toBe(true);
    const missing = real.queryKnowledge({
      id: { kind: "item_id", value: "definitely-not-an-item" },
    });
    expect(missing.ok).toBe(false);
  });
});

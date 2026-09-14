/**
 * TS mirror of the shared KB parity vectors. Reads
 * the same vector files as tests/web/parity/vectors_kb_python_test.py and
 * asserts the same invariants against the same generated artefact, so the
 * Python builder and the TS reader cannot drift apart.
 *
 * Vectors with status "blocked" are parity gaps: counted, never
 * silently dropped.
 */
import { readFileSync, existsSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const ROOT = resolve(__dirname, "../..");
const ARTEFACT_PATH = resolve(
  ROOT,
  "apps/warband-manager-web/public/knowledge/knowledge-web.json",
);

interface VectorFile {
  source_family: string;
  source_tests: number;
  vectors: Array<Record<string, unknown> & { id: string; status?: string }>;
  gap?: { blocked_vectors: number };
}

const hasArtefact = existsSync(ARTEFACT_PATH);
const artefact: any = hasArtefact
  ? JSON.parse(readFileSync(ARTEFACT_PATH, "utf-8"))
  : null;
if (artefact?.rules_prose_url) {
  artefact.rules_prose = JSON.parse(readFileSync(resolve(ARTEFACT_PATH, "..", artefact.rules_prose_url), "utf-8"));
}
const vectorsRoot = resolve(ROOT, "tests/web/parity/vectors");

function loadVectorFile(name: string): VectorFile {
  return JSON.parse(readFileSync(resolve(vectorsRoot, name), "utf-8"));
}

describe.skipIf(!hasArtefact)("shared KB parity vectors (TS mirror)", () => {
  const knowledgePort = loadVectorFile("knowledge_port.json");
  const rulesCatalogue = loadVectorFile("rules_catalogue.json");

  it("vector files exist and keep parity with the Python runner", () => {
    expect(knowledgePort.source_tests).toBe(9);
    expect(rulesCatalogue.source_tests).toBe(10);
    expect(rulesCatalogue.gap?.status).toBe("RESOLVED");
    expect(rulesCatalogue.vectors.every((v) => v.status === "ready")).toBe(true);
    expect(
      knowledgePort.vectors.filter((v) => v.status !== "blocked").length,
    ).toBe(9);
  });

  it("kb: bands >= 80 in the two canonical collections", () => {
    expect(artefact.bands.length).toBeGreaterThanOrEqual(80);
    expect([...new Set(artefact.bands.map((b: any) => b.collection))].sort()).toEqual([
      "mordheim",
      "trollheim",
    ]);
  });

  it("kb: every band has a usable roster shape", () => {
    for (const band of artefact.bands) {
      expect(band.id, band.id).toBeTruthy();
      expect(band.roster.minimum_models).toBeGreaterThanOrEqual(3);
      expect(band.roster.maximum_models).toBeGreaterThanOrEqual(band.roster.minimum_models);
      expect(band.roster.starting_gold).toBeGreaterThan(0);
    }
  });

  it("kb: sisters roster is canonical", () => {
    const band = artefact.bands.find(
      (b: any) => b.id === "sisters-of-sigmar" && b.collection === "mordheim",
    );
    expect(band).toBeTruthy();
    expect(band.roster.minimum_models).toBe(3);
    expect(band.roster.maximum_models).toBe(15);
    expect(band.roster.starting_gold).toBe(500);
  });

  it("kb: matriarch profile is canonical", () => {
    const p = artefact.profiles.find(
      (row: any) => row.id === "sigmarite-matriarch" && row.band_id === "sisters-of-sigmar",
    );
    expect(p).toBeTruthy();
    expect(p.cost).toBe(70);
    expect(p.experience).toBe(20);
    expect(p.characteristics).toEqual({
      M: 4, WS: 4, BS: 4, S: 3, T: 3, W: 1, I: 4, A: 1, Ld: 8,
    });
  });

  it("kb: every profile carries the full characteristic set", () => {
    const keys = ["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld"].sort();
    for (const p of artefact.profiles) {
      expect(Object.keys(p.characteristics).sort(), p.id).toEqual(keys);
    }
  });

  it("kb: sigmarite hammer resolves its canonical EN name", () => {
    const item = artefact.items.find((i: any) => i.item_id === "sigmarite_hammer");
    expect(item.names.en).toBe("Sigmarite Hammer");
  });

  it("kb: post-battle sequence carries the 10 canonical steps", () => {
    const steps = artefact.campaign.post_battle_sequence;
    expect(steps.length).toBe(10);
    expect(steps.slice(0, 3).map((s: any) => s.id)).toEqual([
      "campaign.step.serious-injuries",
      "campaign.step.experience",
      "campaign.step.exploration",
    ]);
  });

  it("kb: artefact declares the mordheim ruleset", () => {
    expect(artefact.ruleset).toBe("mordheim");
  });

  it("kb: artefact exposes the search index seam", () => {
    expect(typeof artefact.indexes).toBe("object");
  });

  // --------------------------------------------- rules prose (gap RESOLVED)

  const prose = artefact.rules_prose as Record<string, any[]>;

  it("rules: prose documents present", () => {
    expect(["special-rules", "conditions", "core-combat"].every((s) => s in prose)).toBe(true);
  });

  it("rules: 68 canonical shared rules", () => {
    expect(prose["special-rules"]).toHaveLength(68);
  });

  it("rules: prose stems include canonical documents and generated localization indexes", () => {
    expect(Object.keys(prose).sort()).toEqual([
      "conditions",
      "core-combat",
      "localized-labels",
      "profile-special-rules",
      "racial-maximums",
      "resolution",
      "special-rules",
    ]);
  });

  it("rules: Always Hungry EN name + effect", () => {
    const row = prose["special-rules"].find((r: any) => r.id === "shared-rule.always-hungry");
    expect(row.names.en).toBe("Always Hungry");
    expect(row.effects.en.startsWith("A Troll requires")).toBe(true);
  });

  it("rules: Always Hungry ES i18n", () => {
    const row = prose["special-rules"].find((r: any) => r.id === "shared-rule.always-hungry");
    expect(row.names.es).toBe("Siempre Hambriento");
  });

  it("rules: Fires of U'Zhul resolves from the magic lores", () => {
    const spell = artefact.campaign.magic.lores
      .flatMap((lore: any) => lore.spells ?? [])
      .find((s: any) => s.id === "spell.lesser-magic.fires-of-uzhul");
    expect(spell).toBeTruthy();
    expect(spell.name).toBe("Fires of U'Zhul");
    expect(spell.difficulty).toBe(7);
  });

  it("rules: search seam matches names and effects (accent-insensitive data)", () => {
    const row = prose["special-rules"].find((r: any) => r.id === "shared-rule.always-hungry");
    const hay = `${row.names.en} ${row.effects.en}`.toLowerCase();
    expect(hay.includes("always hungry")).toBe(true);
  });

  it("rules: scoped search by stem finds the entry", () => {
    const ids = prose["special-rules"].map((r: any) => r.id);
    expect(ids).toContain("shared-rule.always-hungry");
  });
});

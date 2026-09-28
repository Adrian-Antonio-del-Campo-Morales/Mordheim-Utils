/**
 * Coherence test: the frozen ports must stay compatible with
 * the real artefact produced by `tools/knowledge/generate_knowledge_web.py`
 * (P4.2). If the generator's output shape drifts, this test fails — fix the
 * drift at the contract level,
 * not by loosening this file.
 *
 * T12 fase D split the artefact: `knowledge-web.json` is the initial document
 * and `knowledge-catalogue.json` carries the equipment catalogue plus the
 * campaign sections, addressed by `catalogue_url` + `catalogue_digest`. Shape
 * assertions run on the published initial document; content assertions run on
 * the document a loader gets once every referenced fragment is merged — the
 * same contract the browser adapter follows through `ensureCatalogue`.
 *
 * Runs in plain Node on the real generated artefact (skip if it has not been
 * generated yet — run `python tools/knowledge/generate_knowledge_web.py`).
 */
import { describe, expect, it } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { readArtefactDocument } from "../../../support/kb-artefact";

const ARTEFACT_PATH = fileURLToPath(
  new URL("../../../../outputs/web-public/knowledge/knowledge-web.json", import.meta.url),
);

interface Artefact {
  schema_version: number;
  ruleset: string;
  collections: Record<string, unknown>[];
  bands: Record<string, unknown>[];
  profiles: Record<string, unknown>[];
  items: Record<string, unknown>[];
  skills: Record<string, unknown>[];
  weapon_hands: Record<string, number>;
  campaign: Record<string, unknown>;
  catalogue_url: string;
  catalogue_digest: string;
  indexes: Record<string, unknown>;
}

describe.skipIf(!existsSync(ARTEFACT_PATH))("P4.2 artefact ↔ P3.4 ports coherence", () => {
  const initial: Artefact = JSON.parse(readFileSync(ARTEFACT_PATH, "utf8"));
  const artefact: Artefact = readArtefactDocument(ARTEFACT_PATH) as unknown as Artefact;

  it("the initial document has the agreed top-level shape and defers the campaign catalogue", () => {
    expect(initial.schema_version).toBe(1);
    expect(initial.ruleset).toBe("mordheim");
    for (const key of ["collections", "bands", "profiles", "skills", "indexes", "weapon_hands"]) {
      expect(initial, key).toHaveProperty(key);
    }
    // Deferred by contract, never absent: the equipment catalogue and the
    // campaign sections travel in the digest-addressed fragment.
    expect(Object.hasOwn(initial, "items"), "items must be deferred").toBe(false);
    expect(Object.hasOwn(initial, "campaign"), "campaign must be deferred").toBe(false);
    expect(typeof initial.catalogue_url).toBe("string");
    expect(initial.catalogue_digest).toMatch(/^[0-9a-f]{64}$/);
  });

  it("the merged document publishes items and campaign sections again", () => {
    expect(artefact.items.length).toBeGreaterThan(0);
    expect(Object.keys(artefact.campaign).length).toBeGreaterThan(0);
  });

  it("every record family carries a per-locale names map with canonical English (port contract)", () => {
    for (const family of [artefact.collections, artefact.bands, artefact.profiles, artefact.items, artefact.skills]) {
      for (const record of family) {
        const names = record.names as Record<string, string> | undefined;
        expect(names, JSON.stringify(record).slice(0, 120)).toBeTypeOf("object");
        expect(Object.keys(names ?? {}).length).toBeGreaterThan(0);
        expect(Object.values(names ?? {})[0].length).toBeGreaterThan(0);
      }
    }
  });

  it("items use item_id, other families use id — matching the Id union value mapping", () => {
    for (const item of artefact.items) {
      expect(typeof item.item_id).toBe("string");
      expect((item.item_id as string).length).toBeGreaterThan(0);
    }
    for (const band of artefact.bands) expect(typeof band.id).toBe("string");
    for (const profile of artefact.profiles) expect(typeof profile.id).toBe("string");
    for (const skill of artefact.skills) expect(typeof skill.id).toBe("string");
  });

  it("campaign section keys are YAML stems / agreed sub-sections (KnowledgeKind families)", () => {
    const allowed = new Set([
      "trading-post", "scenarios", "serious-injuries", "experience-and-advances",
      "exploration-and-income", "magic", "mutations", "hired-swords-and-dramatis",
      "hirelings", "warband_groups", "racial_maximums", "post_battle_sequence",
      "scenario-rewards", "warband-rating", "recruitment-and-veterans", "trading-and-rarity",
    ]);
    for (const key of Object.keys(artefact.campaign)) {
      expect(allowed.has(key), `unexpected campaign key ${key}`).toBe(true);
    }
    const steps = artefact.campaign.post_battle_sequence as Record<string, unknown>[];
    for (const step of steps) {
      for (const field of ["id", "name", "resolves", "order", "repeatability"]) {
        expect(step, `post-battle step missing ${field}`).toHaveProperty(field);
      }
    }
  });

  it("indexes are coherent with the record arrays", () => {
    const byId = initial.indexes.items_by_id as Record<string, number>;
    expect(Object.keys(byId).length).toBe(artefact.items.length);
    for (const [id, index] of Object.entries(byId)) {
      expect((artefact.items[index] as Record<string, unknown>).item_id).toBe(id);
    }
    const bandsByCollection = initial.indexes.bands_by_collection as Record<string, string[]>;
    const bandCount = Object.values(bandsByCollection).reduce((sum, ids) => sum + ids.length, 0);
    expect(bandCount).toBe(artefact.bands.length);
  });
});

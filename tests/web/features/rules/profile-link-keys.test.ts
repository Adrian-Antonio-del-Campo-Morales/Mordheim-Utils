/**
 * «Disponible para» profile links: React keys must never collide.
 *
 * The published artefact contains distinct bands that resolve to the same
 * visible name (Pit Fighters, Lizardmen, …), and the same profile id can be
 * published by several bands. Keying a link row by the band's *name*
 * (`${band}:${profile_id}:${relation}`) produced 5 865 duplicate React keys
 * across the 83 332 links the rules page can render: React dropped rows.
 *
 * The key is now `${band_id}:${profile_id}:${relation}` — canonical identity,
 * never array positions, and never the localized display name. This test walks
 * every category in both locales and asserts the composition is unique, and
 * reddens if the pre-fix band-name shape returns.
 */
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { RulesCatalogue } from "@app/rules/rules-catalogue";
import { readArtefactDocument } from "../../../support/kb-artefact";

const PUBLISHED = resolve(process.cwd(), "..", "..", "outputs", "web-public", "knowledge", "knowledge-web.json");
const artefact = readArtefactDocument(PUBLISHED);
const knowledge = ArtefactKnowledgeReader.from(artefact);
const catalogue = new RulesCatalogue(knowledge);

/** Categories whose entries carry profile links. */
const CATEGORIES = ["special-rules", "band-rules", "skills", "equipment", "spells"] as const;

function collectLinks(locale: "es" | "en") {
  const links: { categoryId: string; entryId: string; link: ReturnType<RulesCatalogue["profileLinks"]>[number] }[] = [];
  for (const categoryId of CATEGORIES) {
    for (const entry of catalogue.entries(categoryId, locale)) {
      for (const link of catalogue.profileLinks(categoryId, entry, locale)) links.push({ categoryId, entryId: entry.entry_id, link });
    }
  }
  return links;
}

describe("profile links («Disponible para») keys never collide", () => {
  const links = [...collectLinks("es"), ...collectLinks("en")];

  it("the artefact really publishes colliding band display names", () => {
    // The gate is only meaningful because distinct bands share a display name
    // and some profile ids are published by more than one band.
    const byName = new Map<string, Set<string>>();
    for (const band of (artefact.bands as readonly Record<string, unknown>[])) {
      const name = String(knowledge.recordText(band, "name", "en"));
      byName.set(name, (byName.get(name) ?? new Set()).add(String(band.id)));
    }
    const homonyms = [...byName.entries()].filter(([, ids]) => ids.size > 1);
    expect(homonyms.length, "distinct bands sharing one display name").toBeGreaterThan(0);
  });

  it("every rendered list keys uniquely by band identity, profile identity and relation", () => {
    expect(links.length).toBeGreaterThan(50_000);
    // React keys must be unique within one rendered list: the rules page shows
    // the links of the browsed entry only, so the assertion is per entry.
    const seen = new Map<string, string>();
    for (const { categoryId, entryId, link } of links) {
      const listKey = `${categoryId}:${entryId}`;
      const key = `${listKey} > ${link.band_id}:${link.profile_id}:${link.relation}`;
      expect(seen.get(key), `${key} rendered twice`).toBeUndefined();
      seen.set(key, listKey);
    }
  });

  it("every link carries its canonical band_id, distinct from the display name", () => {
    const bandIds = new Set((artefact.bands as readonly Record<string, unknown>[]).map((band) => String(band.id)));
    for (const { link } of links) {
      expect(bandIds.has(link.band_id), `band_id ${link.band_id} is a published band`).toBe(true);
    }
  });

  it("the pre-fix key shape (band display name) still collides — the gate cannot pass vacuously", () => {
    const legacyKeys = new Map<string, number>();
    for (const { link } of links) {
      const key = `${link.band}:${link.profile_id}:${link.relation}`;
      legacyKeys.set(key, (legacyKeys.get(key) ?? 0) + 1);
    }
    const duplicates = [...legacyKeys.values()].filter((count) => count > 1).reduce((total, count) => total + count, 0);
    expect(duplicates, "links sharing the legacy band-name key").toBeGreaterThan(0);
  });
});

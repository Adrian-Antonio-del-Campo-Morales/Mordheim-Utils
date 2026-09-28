/**
 * T12 fase D — the deferred campaign catalogue.
 *
 * The published artefact keeps the initial document small (open the app, choose
 * a warband) and publishes the equipment catalogue plus the campaign sections as
 * one fragment addressed by `catalogue_url` + `catalogue_digest`. These are the
 * guarantees the product relies on:
 *
 * - loading the initial document never downloads the catalogue (no covert
 *   startup fetch), while prose and display fragments still load eagerly;
 * - a flow that needs a deferred family awaits `ensureCatalogue(kind)`, and
 *   concurrent calls share a single request;
 * - the second call neither downloads nor merges the catalogue again;
 * - reading a deferred family before loading it is a deterministic error, never
 *   an empty list or a technical name;
 * - a missing fragment or a mismatched digest fails visibly, deterministically
 *   and without a partial merge;
 * - once loaded, the read contract is the previous synchronous one (ids, maps
 *   and presentation text resolution included).
 */
import { describe, expect, it, vi } from "vitest";
import { createHash } from "node:crypto";

import {
  ArtefactKnowledgeReader,
  KnowledgeReaderError,
} from "@adapters/knowledge-reader/index";

const ITEMS = [
  {
    item_id: "sword",
    name: "Sword",
    names: { en: "Sword", es: "Espada" },
    kind: "close-combat-weapon",
  },
];

const CAMPAIGN = {
  "trading-post": { items: [{ item_id: "sword", price: 10 }] },
  magic: { lores: [{ id: "lore.hedge", names: { en: "Hedge Magic", es: "Magia Silvestre" } }] },
  scenarios: { scenarios: [{ id: "scenario.skirmish", names: { en: "Skirmish", es: "Escaramuza" } }] },
};

const FRAGMENT = { items: ITEMS, campaign: CAMPAIGN, indexes: { items_by_id: { sword: 0 } } };

const digestOf = (value: unknown): string =>
  createHash("sha256").update(JSON.stringify(value), "utf8").digest("hex");

const CATALOGUE_URL = "knowledge/knowledge-catalogue.json";

/** Initial document: no `items`, no `campaign` — both deferred. */
function initialDocument(digest: string = digestOf(FRAGMENT)): Record<string, unknown> {
  return {
    schema_version: 1,
    ruleset: "mordheim",
    collections: [],
    bands: [{ id: "sisters-of-sigmar", names: { en: "Sisters of Sigmar", es: "Hermanas de Sigmar" } }],
    profiles: [
      {
        id: "sister",
        collection: "mordheim",
        band_id: "sisters-of-sigmar",
        names: { en: "Sister", es: "Hermana" },
      },
    ],
    skills: [],
    rules_prose_url: "knowledge/rules-prose.json",
    display_text_url: "knowledge/display-text.json",
    catalogue_url: CATALOGUE_URL,
    catalogue_digest: digest,
    presentation_entries: [
      { ref: { kind: "item", id: "sword" }, fields: { name: { en: "Sword", es: "Espada" } }, source: "items/0" },
      {
        ref: { kind: "scenario", id: "scenario.skirmish" },
        fields: { name: { en: "Skirmish", es: "Escaramuza" } },
        source: "campaign/scenarios/scenarios/0",
      },
    ],
  };
}

/** Fetch stub that records every requested URL and serves the fragment. */
function artefactServer(options: { fragment?: unknown; catalogueStatus?: number } = {}) {
  const requested: string[] = [];
  const fetchFn = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    requested.push(url);
    if (url.endsWith(CATALOGUE_URL)) {
      const status = options.catalogueStatus ?? 200;
      return status === 200
        ? new Response(JSON.stringify(options.fragment ?? FRAGMENT), { status, headers: { "content-type": "application/json" } })
        : new Response("missing", { status });
    }
    if (url.endsWith("rules-prose.json")) return new Response("{}", { status: 200 });
    if (url.endsWith("display-text.json")) return new Response("{}", { status: 200 });
    return new Response(JSON.stringify(initialDocument()), { status: 200 });
  }) as unknown as typeof fetch;
  return {
    requested,
    fetchFn,
    catalogueRequests: (): number => requested.filter((url) => url.endsWith(CATALOGUE_URL)).length,
  };
}

describe("T12 fase D — deferred campaign catalogue", () => {
  it("keeps the initial document usable and refuses to guess the deferred families", () => {
    const reader = ArtefactKnowledgeReader.from(initialDocument());

    expect(reader.list("band")).toHaveLength(1);
    expect(reader.list("profile")).toHaveLength(1);
    expect(reader.isCatalogueLoaded("items")).toBe(false);
    expect(reader.isCatalogueLoaded("campaign")).toBe(false);

    // Reading before loading is an error: never an empty list, never "not_found"
    // for an id that the catalogue does publish.
    expect(() => reader.list("item")).toThrow(KnowledgeReaderError);
    expect(() => reader.list("item")).toThrow(/ensureCatalogue\("items"\)/);
    expect(() => reader.list("scenario")).toThrow(/ensureCatalogue\("campaign"\)/);
    expect(() => reader.campaignSection("magic")).toThrow(/ensureCatalogue\("campaign"\)/);
    expect(() => reader.queryKnowledge({ id: { kind: "item_id", value: "sword" } })).toThrow(KnowledgeReaderError);
  });

  it("loads no catalogue at startup and the whole catalogue on demand", async () => {
    const server = artefactServer();
    const reader = await ArtefactKnowledgeReader.fromUrl("knowledge/knowledge-web.json", server.fetchFn);

    // Startup: initial document + the fragments that were already eager (the
    // display fragment is skipped here because the initial document already
    // carries the presentation index). The catalogue is never requested.
    expect(server.requested.some((url) => url.endsWith("knowledge-web.json"))).toBe(true);
    expect(server.requested.some((url) => url.endsWith("rules-prose.json"))).toBe(true);
    expect(server.catalogueRequests()).toBe(0);

    await reader.ensureCatalogue("items");
    expect(server.catalogueRequests()).toBe(1);
    expect(reader.isCatalogueLoaded("items")).toBe(true);
    expect(reader.isCatalogueLoaded("campaign")).toBe(true);

    // The synchronous read contract, rebuilt from the same ids and row shapes.
    expect(reader.list("item")).toHaveLength(1);
    const item = reader.list("item")[0];
    expect(reader.recordText(item, "name", "es")).toBe("Espada");
    expect(reader.recordText(item, "name", "en")).toBe("Sword");
    expect(reader.queryKnowledge({ id: { kind: "item_id", value: "sword" } })).toMatchObject({ ok: true });
    expect(reader.campaignSection("trading-post").items).toHaveLength(1);
    expect(reader.list("scenario")).toHaveLength(1);
    expect(reader.recordText(reader.list("scenario")[0], "name", "es")).toBe("Escaramuza");
    expect(reader.itemName("sword", "es")).toBe("Espada");
  });

  it("coalesces concurrent ensure calls into a single request", async () => {
    const server = artefactServer();
    const reader = await ArtefactKnowledgeReader.fromUrl("knowledge/knowledge-web.json", server.fetchFn);

    await Promise.all([reader.ensureCatalogue("items"), reader.ensureCatalogue("campaign")]);

    expect(server.catalogueRequests()).toBe(1);
  });

  it("does not download or mix the catalogue again on later calls", async () => {
    const server = artefactServer();
    const reader = await ArtefactKnowledgeReader.fromUrl("knowledge/knowledge-web.json", server.fetchFn);
    await reader.ensureCatalogue("items");
    const loaded = reader.list("item");

    await reader.ensureCatalogue("items");
    await reader.ensureCatalogue("campaign");
    await Promise.all([reader.ensureCatalogue("items"), reader.ensureCatalogue("items")]);

    expect(server.catalogueRequests()).toBe(1);
    expect(reader.list("item")).toHaveLength(loaded.length);
    expect(reader.list("item")[0]).toBe(loaded[0]);
  });

  it("fails deterministically on a mismatched digest, without a partial merge", async () => {
    const server = artefactServer({ fragment: { ...FRAGMENT, items: [...ITEMS, { item_id: "tampered" }] } });
    const reader = await ArtefactKnowledgeReader.fromUrl("knowledge/knowledge-web.json", server.fetchFn);

    await expect(reader.ensureCatalogue("items")).rejects.toBeInstanceOf(KnowledgeReaderError);
    await expect(reader.ensureCatalogue("items")).rejects.toThrow("Incompatible KB catalogue artefact");
    // No partial merge, no silent empty catalogue, no refetch on the retry.
    expect(reader.isCatalogueLoaded("items")).toBe(false);
    expect(() => reader.list("item")).toThrow(/ensureCatalogue\("items"\)/);
    expect(server.catalogueRequests()).toBe(1);
  });

  it("fails deterministically when the fragment is missing", async () => {
    const server = artefactServer({ catalogueStatus: 404 });
    const reader = await ArtefactKnowledgeReader.fromUrl("knowledge/knowledge-web.json", server.fetchFn);

    await expect(reader.ensureCatalogue("items")).rejects.toBeInstanceOf(KnowledgeReaderError);
    await expect(reader.ensureCatalogue("campaign")).rejects.toThrow(/HTTP 404/);
    expect(() => reader.list("scenario")).toThrow(KnowledgeReaderError);
  });

  it("offers an explicit whole-artefact load for tools and tests", async () => {
    const server = artefactServer();
    const reader = await ArtefactKnowledgeReader.fromFullUrl("knowledge/knowledge-web.json", server.fetchFn);

    expect(reader.isCatalogueLoaded("items")).toBe(true);
    expect(reader.isCatalogueLoaded("campaign")).toBe(true);
    expect(reader.list("item")).toHaveLength(1);
    expect(reader.list("scenario")).toHaveLength(1);
    expect(server.catalogueRequests()).toBe(1);
  });

  it("treats an inline document as already loaded (pre-partition compatibility)", () => {
    const reader = ArtefactKnowledgeReader.from({
      schema_version: 1,
      ruleset: "mordheim",
      collections: [],
      bands: [],
      profiles: [],
      skills: [],
      items: ITEMS,
      campaign: CAMPAIGN,
    });

    expect(reader.isCatalogueLoaded("items")).toBe(true);
    expect(reader.list("item")).toHaveLength(1);
    expect(reader.list("scenario")).toHaveLength(1);
  });

  it("rejects an artefact that neither publishes nor defers the equipment catalogue", () => {
    const { catalogue_url: _url, catalogue_digest: _digest, ...withoutCatalogue } = initialDocument();

    expect(() => ArtefactKnowledgeReader.from(withoutCatalogue)).toThrow(/items is missing and no catalogue_url/);
  });
});

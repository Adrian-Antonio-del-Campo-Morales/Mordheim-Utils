/**
 * P5.2 acceptance — `ArtefactKnowledgeReader.fromUrl`: fetches the artefact,
 * validates it, and fails with typed actionable `KnowledgeReaderError`s
 * (network / HTTP / JSON / schema), never a raw Response or SyntaxError.
 */

import { describe, expect, it, vi } from "vitest";

import { ArtefactKnowledgeReader, KnowledgeReaderError } from "@adapters/knowledge-reader/index";

/** Minimal valid artefact (mirrors the real generator's top-level shape). */
const validArtefact = {
  schema_version: 1,
  ruleset: "mordheim",
  collections: ["mordheim"],
  bands: [
    {
      id: "sisters-of-sigmar",
      name: "Sisters of Sigmar",
      names: { en: "Sisters of Sigmar" },
      collection: "mordheim",
      roster: { minimum_models: 3, maximum_models: 15, starting_gold: 500, members: [] },
    },
  ],
  profiles: [],
  items: [],
  skills: [],
};

function fetchOk(body: unknown): typeof fetch {
  return (() =>
    Promise.resolve(
      new Response(JSON.stringify(body), { status: 200, headers: { "content-type": "application/json" } }),
    )) as typeof fetch;
}

function fetchStatus(status: number): typeof fetch {
  return (() => Promise.resolve(new Response("nope", { status }))) as typeof fetch;
}

describe("ArtefactKnowledgeReader.fromUrl", () => {
  it("fetches, validates and resolves ids through the built reader", async () => {
    const reader = await ArtefactKnowledgeReader.fromUrl("/knowledge/knowledge-web.json", fetchOk(validArtefact));
    const result = reader.queryKnowledge({ id: { kind: "band_id", value: "sisters-of-sigmar" } });
    expect(result.ok).toBe(true);
    if (result.ok) {
      expect(result.record.names["en"]).toBe("Sisters of Sigmar");
    }
    const missing = reader.queryKnowledge({ id: { kind: "band_id", value: "nope" } });
    expect(missing).toEqual({ ok: false, reason: "not_found" });
  });

  it("loads partitioned rules prose beside the main artefact", async () => {
    const fetchFn = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ ...validArtefact, rules_prose_url: "rules-prose.json" })))
      .mockResolvedValueOnce(new Response(JSON.stringify({ "special-rules": [] })));
    await ArtefactKnowledgeReader.fromUrl("https://example.test/knowledge/knowledge-web.json", fetchFn);
    expect(fetchFn).toHaveBeenNthCalledWith(2, "https://example.test/knowledge/rules-prose.json", { cache: "no-cache" });
  });

  it("loads partitioned display text beside the main artefact", async () => {
    const fetchFn = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ ...validArtefact, display_text_url: "display-text.json" })))
      .mockResolvedValueOnce(new Response(JSON.stringify({ presentation_entries: [{ ref: { kind: "skill", id: "skill.acrobat" }, source: "skills/0", fields: { name: { es: "Acróbata" } } }] })));
    const reader = await ArtefactKnowledgeReader.fromUrl("https://example.test/knowledge/knowledge-web.json", fetchFn);
    expect(fetchFn).toHaveBeenNthCalledWith(2, "https://example.test/knowledge/display-text.json", { cache: "no-cache" });
    expect(reader.resolveKbText({ kind: "skill", id: "skill.acrobat" }, "name", "es")).toMatchObject({ ok: true, text: "Acróbata" });
  });

  it("rejects HTTP failures with a typed error naming the url and status", async () => {
    await expect(
      ArtefactKnowledgeReader.fromUrl("/missing.json", fetchStatus(404)),
    ).rejects.toMatchObject({
      name: "KnowledgeReaderError",
      message: expect.stringContaining("HTTP 404"),
    });
  });

  it("rejects non-JSON bodies with a typed parse error", async () => {
    const badJson = (() => Promise.resolve(new Response("<html>", { status: 200 }))) as typeof fetch;
    await expect(ArtefactKnowledgeReader.fromUrl("/x.json", badJson)).rejects.toBeInstanceOf(KnowledgeReaderError);
  });

  it("rejects schema-invalid artefacts through the validator", async () => {
    await expect(
      ArtefactKnowledgeReader.fromUrl("/x.json", fetchOk({ bands: "not-a-list" })),
    ).rejects.toMatchObject({ name: "KnowledgeReaderError" });
  });

  it("wraps network failures (fetch rejecting) with the url in the message", async () => {
    const networkError = (() => Promise.reject(new TypeError("offline"))) as typeof fetch;
    await expect(
      ArtefactKnowledgeReader.fromUrl("/knowledge/knowledge-web.json", networkError),
    ).rejects.toMatchObject({
      message: expect.stringContaining("offline"),
    });
  });
});

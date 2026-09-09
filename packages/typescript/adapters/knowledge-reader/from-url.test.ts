/**
 * P5.2 acceptance — `ArtefactKnowledgeReader.fromUrl`: fetches the artefact,
 * validates it, and fails with typed actionable `KnowledgeReaderError`s
 * (network / HTTP / JSON / schema), never a raw Response or SyntaxError.
 */

import { describe, expect, it } from "vitest";

import { ArtefactKnowledgeReader, KnowledgeReaderError } from "./index";

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

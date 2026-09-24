import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { PresentationEntry, TextField } from "@adapters/knowledge-reader/presentation";

const directory = resolve(process.cwd(), "public/knowledge");
const read = (file: string) => JSON.parse(readFileSync(resolve(directory, file), "utf8"));
const main = read("knowledge-web.json");
const display = read("display-text.json");
const reader = ArtefactKnowledgeReader.from({ ...main, ...display, rules_prose: read("rules-prose.json") });

describe("complete generated presentation index", () => {
  it.each(["es", "en"] as const)("resolves every indexed field exactly or reports its declared TODO in %s", (locale) => {
    expect(display.presentation_digest).toBe(main.presentation_digest);
    expect(display.presentation_entries.length).toBeGreaterThan(1000);
    const todos = new Set(display.translation_todos.map((todo: { status: string; location: string }) => {
      expect(todo.status).toBe("TODO-TRANSLATE");
      return todo.location;
    }));
    for (const entry of display.presentation_entries as PresentationEntry[]) {
      for (const [field, values] of Object.entries(entry.fields)) {
        const result = reader.resolveKbText(entry.ref, field as TextField, locale);
        const location = `${entry.source}:${field}.${locale}`;
        if (values[locale]?.includes("TODO-TRANSLATE")) {
          expect(todos.has(location), location).toBe(true);
          expect(result, location).toMatchObject({ ok: false, reason: "missing-translation" });
        } else {
          expect(result, location).toMatchObject({ ok: true, text: values[locale], locale, field, ref: entry.ref });
        }
      }
    }
  });
});

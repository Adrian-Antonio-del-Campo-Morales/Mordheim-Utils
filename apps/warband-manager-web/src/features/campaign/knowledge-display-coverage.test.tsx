import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import "@testing-library/jest-dom/vitest";
import { describe, expect, it } from "vitest";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { knowledgeHintDetails } from "./KnowledgeHintDetails";
import { knowledgeDescription, knowledgeText } from "./displayText";

type HintKind = "item" | "skill" | "rule" | "injury";
type Entry = { readonly kind: HintKind; readonly id: string; readonly profileId?: string; readonly bandId?: string };

function reader(): ArtefactKnowledgeReader {
  const path = resolve(process.cwd(), "public/knowledge/knowledge-web.json");
  const artefact = JSON.parse(readFileSync(path, "utf8"));
  artefact.rules_prose = JSON.parse(readFileSync(resolve(path, "..", artefact.rules_prose_url), "utf8"));
  Object.assign(artefact, JSON.parse(readFileSync(resolve(path, "..", artefact.display_text_url), "utf8")));
  return ArtefactKnowledgeReader.from(artefact);
}

/** These are catalogue classes, not per-id exemptions: they are labels, not tooltip entries. */
const NO_TOOLTIP_KINDS = new Set(["band", "profile", "lore", "scenario", "hireling"]);

function entries(knowledge: ArtefactKnowledgeReader): readonly Entry[] {
  const rules = ["special-rules", "profile-special-rules", "conditions", "core-combat"]
    .flatMap((section) => knowledge.rulesDocument(section))
    .map((row) => {
      const appliesTo = row.applies_to as Readonly<Record<string, unknown>> | undefined;
      const profileIds = Array.isArray(appliesTo?.profile_ids) ? appliesTo.profile_ids : [];
      return { kind: "rule" as const, id: String(row.id), profileId: profileIds[0] == null ? undefined : String(profileIds[0]), bandId: typeof row.band_id === "string" ? row.band_id : undefined };
    });
  const injuries = (knowledge.campaignSection("serious-injuries").tables as readonly Record<string, unknown>[] | undefined ?? [])
    .flatMap((table) => Array.isArray(table.results) ? table.results : [])
    .map((row) => ({ kind: "injury" as const, id: String((row as Record<string, unknown>).id ?? "") }))
    .filter((row) => row.id);
  return [
    ...knowledge.list("item").map((row) => ({ kind: "item" as const, id: String(row.item_id) })),
    ...knowledge.list("skill").map((row) => ({ kind: "skill" as const, id: String(row.id) })),
    ...rules,
    ...injuries,
  ];
}

describe("published KB display coverage", () => {
  const coverageReader = reader();
  const coverageEntries = entries(coverageReader);
  for (const locale of ["es", "en"] as const) {
    it(`resolves every published name and description in ${locale}`, () => {
      const knowledge = reader();
      for (const entry of entries(knowledge)) {
        const name = knowledgeText(knowledge, entry.kind, entry.id, locale, entry.profileId, entry.bandId);
        const resolvedName = knowledge.resolveKbText(entry, "name", locale);
        if (resolvedName.ok) expect(name.text).toBe(resolvedName.text);
        else {
          expect(resolvedName.reason, `${entry.kind}:${entry.id} name`).toBe("missing-translation");
          expect(name.text).toBe(locale === "es" ? "Información no disponible" : "Information unavailable");
        }
        expect(name.text).not.toBe(entry.id);
        if (!NO_TOOLTIP_KINDS.has(entry.kind)) {
          const description = knowledgeDescription(knowledge, entry, locale);
          const fields = (["effect", "description", "text", "note"] as const).map((field) => knowledge.resolveKbText(entry, field, locale));
          if (description.status === "missing") {
            const declared = fields.find((result) => result.ok || result.reason !== "missing-field");
            if (declared) expect(declared, `${entry.kind}:${entry.id} description`).toMatchObject({ ok: false, reason: "missing-translation" });
            expect(description.text).toBe(locale === "es" ? "No hay una descripción disponible para este elemento." : "No description is available for this entry.");
          } else expect(fields.some((result) => result.ok && result.text === description.text)).toBe(true);
          expect(description.text.trim(), `${entry.kind}:${entry.id} description`).not.toBe("");
        }
      }
    });

    // Each chunk checks the exact tooltip factory used by KnowledgeHint. The
    // focused component suite covers native popover interaction once.
    for (let start = 0; start < coverageEntries.length; start += 100) {
      const batch = coverageEntries.slice(start, start + 100);
      it(`builds accessible tooltip batch ${start / 100 + 1} in ${locale}`, () => {
        for (const entry of batch) {
          const tooltip = knowledgeHintDetails({ knowledge: coverageReader, ...entry, locale });
          expect(tooltip.name.trim(), `${entry.kind}:${entry.id} accessible name`).not.toBe("");
          expect(tooltip.tooltip.trim(), `${entry.kind}:${entry.id} tooltip`).not.toBe("");
          expect(tooltip.name).not.toBe(entry.id);
          expect(tooltip.tooltip).not.toBe(entry.id);
        }
      }, 200000);
    }
  }
});

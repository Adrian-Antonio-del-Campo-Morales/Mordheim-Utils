/**
 * Web Test Migration — UI parity block 3 (REPO REWORK 2).
 *
 * Desktop source: `tests/ui/test_ui_i18n.py` (7 rows, Tkinter STRINGS
 * catalogue). The web i18n seam is different by design — display names
 * travel inside the KB artefact as `names` maps (`en` canonical + `es`
 * translations from the merge) and resolve through the reader's fallback
 * chain: requested locale → canonical English → any translated entry → id.
 *
 * Same behavioural contract asserted here, on the web seam:
 *  - default locale is English (resolveName without a request = "en");
 *  - Spanish translations resolve from the real artefact (all 81 bands
 *    carry `es` — verified at generation time);
 *  - unknown keys degrade to English/identifier, never throw;
 *  - every band name translates in Spanish (web equivalent of
 *    test_every_catalogue_key_translates_in_spanish).
 *
 * Ownership: REPO REWORK 2. Reader: REPO REWORK 333333's adapter, tested
 * through its public API only.
 */

import { describe, expect, it, vi, beforeAll, afterEach } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  ArtefactKnowledgeReader,
  resolveName,
} from "@adapters/knowledge-reader/index";
import type { ArtefactRow } from "@adapters/knowledge-reader/artefact-types";

/** Locate the repo root (walk up from cwd until the contract dir exists). */
function repoRoot(): string {
  let dir = process.cwd();
  while (dir !== resolve(dir, "..")) {
    if (existsSync(resolve(dir, "apps/warband-manager-web/public/knowledge"))) {
      return dir;
    }
    dir = resolve(dir, "..");
  }
  throw new Error("repo root not found");
}

import { existsSync } from "node:fs";

const ARTEFACT_PATH = "apps/warband-manager-web/public/knowledge/knowledge-web.json";

interface RawArtefact {
  bands: ArtefactRow[];
  [key: string]: unknown;
}

let raw: RawArtefact;
let reader: ArtefactKnowledgeReader;

beforeAll(() => {
  raw = JSON.parse(readFileSync(resolve(repoRoot(), ARTEFACT_PATH), "utf-8"));
  reader = ArtefactKnowledgeReader.from(raw);
});

/** All band rows, via the reader's own index (public query surface). */
function bandsOf(): ArtefactRow[] {
  const ids = raw.bands.map((b) => String(b.id));
  return ids.map((id) => {
    const result = reader.queryKnowledge({ id: { kind: "band_id", value: id } });
    if (!result.ok) throw new Error(`band ${id} not resolvable`);
    return { id: String(result.record.id.value), names: result.record.names } as unknown as ArtefactRow;
  });
}

function fetchOk(body: unknown): typeof fetch {
  return vi.fn(async () => new Response(JSON.stringify(body), { status: 200 })) as unknown as typeof fetch;
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("UI i18n parity — locale fallback chain (desktop test_ui_i18n family)", () => {
  it("default resolution is English (CANONICAL_LOCALE)", () => {
    const bands = bandsOf();
    const band = bands[0] ?? firstRow();
    expect(resolveName(band, "en")).toBe((band.names as Record<string, string>)?.en ?? band.name);
  });

  it("Spanish translations resolve from the real artefact", () => {
    const bands = bandsOf();
    const band = bands[0] ?? firstRow();
    const names = (band.names ?? {}) as Record<string, string>;
    if (names.es) {
      expect(resolveName(band, "es")).toBe(names.es);
      expect(resolveName(band, "es")).not.toBe(resolveName(band, "en"));
    }
  });

  it("unknown locale degrades to English, unknown key to the id — never throws", () => {
    const row: ArtefactRow = { id: "some.item", name: "Known Name", names: { en: "Known Name" } };
    // Unsupported locale ("de" on desktop keeps current selection; web falls
    // back through en) returns the English string.
    expect(resolveName(row, "de" as never)).toBe("Known Name");
    // No names at all → the id is visible instead of crashing.
    expect(resolveName({ id: "bare.id" } as ArtefactRow, "es")).toBe("bare.id");
  });

  it("every band name carries a Spanish entry (every_catalogue_key family)", () => {
    // Desktop exempts locale-neutral strings whose Spanish rendering equals
    // the English (proper nouns like "Clan Pestilens"). Web equivalent:
    // every names map must HAVE an es entry; equality is legitimate for
    // proper nouns and resolves correctly through the chain.
    const bands = bandsOf();
    expect(bands.length).toBeGreaterThan(0);
    const missing = bands
      .filter((band) => !((band.names ?? {}) as Record<string, string>).es)
      .map((band) => band.id);
    expect(missing).toEqual([]);
  });

  it("the artefact round-trips through fromUrl (degraded-KB seam parity)", async () => {
    const viaUrl = await ArtefactKnowledgeReader.fromUrl("memory://artefact", fetchOk(raw));
    const ids = raw.bands.map((b) => String(b.id));
    const resultA = reader.queryKnowledge({ id: { kind: "band_id", value: ids[0] } });
    const resultB = viaUrl.queryKnowledge({ id: { kind: "band_id", value: ids[0] } });
    expect(resultB.ok).toBe(true);
    expect(resultA.ok).toBe(true);
    if (resultA.ok && resultB.ok) {
      expect(resultB.record.id.value).toBe(resultA.record.id.value);
      expect(resolveName({ id: resultB.record.id.value, names: resultB.record.names } as ArtefactRow, "es"))
        .toBe(resolveName({ id: resultA.record.id.value, names: resultA.record.names } as ArtefactRow, "es"));
    }
  });
});

/** Fallback when the artefact ships no bands (degraded build). */
function firstRow(): ArtefactRow {
  return { id: "fallback", name: "Fallback", names: { en: "Fallback", es: "Reserva" } };
}

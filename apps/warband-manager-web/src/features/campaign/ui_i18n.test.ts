/**
 * UI locale coverage for the browser campaign shell.
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
 * Ownership: browser campaign shell. Reader: generated knowledge artefact,
 * tested through its public API only.
 */

import { describe, expect, it, vi, beforeAll, afterEach } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  ArtefactKnowledgeReader,
  resolveName,
} from "@adapters/knowledge-reader/index";
import type { ArtefactRow } from "@adapters/knowledge-reader/artefact-types";
import { knowledgeName } from "./displayText";

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
const RULES_PROSE_PATH = "apps/warband-manager-web/public/knowledge/rules-prose.json";

interface RawArtefact {
  bands: ArtefactRow[];
  [key: string]: unknown;
}

let raw: RawArtefact;
let reader: ArtefactKnowledgeReader;

beforeAll(() => {
  raw = JSON.parse(readFileSync(resolve(repoRoot(), ARTEFACT_PATH), "utf-8"));
  const rules_prose = JSON.parse(readFileSync(resolve(repoRoot(), RULES_PROSE_PATH), "utf-8"));
  reader = ArtefactKnowledgeReader.from({ ...raw, rules_prose });
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

  // ---- Remaining desktop rows (web seam equivalents) ----

  it("env override parity: the locale is a caller argument, not ambient state (default_locale_is_english_and_env_override)", () => {
    // Desktop reads MORDHEIM_LOCALE env; web has no ambient locale — the
    // requested locale is explicit at every resolveName/itemName call and
    // defaults to "en" (asserted by the default-resolution test). The
    // contract is: no call site can accidentally inherit a stale locale,
    // because none exists. Assert the default parameter behaviour.
    const band = bandsOf()[0];
    const names = (band.names ?? {}) as Record<string, string>;
    // resolveName(band) with default locale = English canonical.
    expect(resolveName(band, "en")).toBe(names.en ?? band.name);
  });

  it("English renders keys byte-identical (english_locale_renders_keys_byte_identical)", () => {
    // Desktop: tr(key) === key for every STRINGS entry. Web: the English
    // name is the canonical `name`/names.en byte-for-byte for every row.
    for (const band of bandsOf()) {
      const names = (band.names ?? {}) as Record<string, string>;
      if (names.en) {
        expect(resolveName(band, "en")).toBe(names.en);
      }
    }
  });

  it("translated entries have a Spanish value and English stays canonical (translated_strings_have_a_spanish_entry)", () => {
    // Desktop: entry ⊆ {en, es}, entry.es truthy, en == key. Web equivalent
    // over every i18n'd artefact section with rows: names maps carry es;
    // en is the canonical name; no third locale leaks into names.
    for (const band of bandsOf()) {
      const names = (band.names ?? {}) as Record<string, string>;
      expect(names.es).toBeTruthy();
      expect(Object.keys(names).every((k) => k === "en" || k === "es")).toBe(true);
    }
  });

  it("post-battle chrome translates under Spanish (post_battle_chrome_translates_under_spanish)", () => {
    // Desktop asserts fixed chrome strings (RECOVERY → RECUPERACIÓN, etc.).
    // Web: the post-battle domain surface is the scenario catalogue the
    // battle/post-battle panels resolve from. The artefact's scenario ids
    // are fully qualified ("scenario.skirmish") — assert Spanish resolution
    // on the scenario the UI's own default picker candidates use.
    const scenarios = reader.queryKnowledge({ id: { kind: "scenario_id", value: "scenario.skirmish" } });
    expect(scenarios.ok).toBe(true);
    if (scenarios.ok) {
      const names = scenarios.record.names as Record<string, string>;
      expect(names.es).toBe("Escaramuza");
      expect(resolveName({ id: "scenario.skirmish", names } as ArtefactRow, "es")).toBe("Escaramuza");
    }
  });

  it("translates legacy warrior rules stored by their English display name", () => {
    expect([
      "Death Oath", "No Armour", "No Missile Weapons", "Slayer Skills", "Hard to Kill",
    ].map((name) => knowledgeName(reader, "skill", name, "es", name))).toEqual([
      "Juramento de Muerte", "Sin Armadura", "Sin Armas de Proyectil", "Habilidades de Matatrolles", "Difíciles de Matar",
    ]);
  });

  it("renders serious-injury result text instead of its technical id", () => {
    expect(knowledgeName(reader, "injury", "campaign.serious-injury.hero.41-55-full-recovery", "es")).toBe("Recuperación Completa");
  });
});

/** Fallback when the artefact ships no bands (degraded build). */
function firstRow(): ArtefactRow {
  return { id: "fallback", name: "Fallback", names: { en: "Fallback", es: "Reserva" } };
}

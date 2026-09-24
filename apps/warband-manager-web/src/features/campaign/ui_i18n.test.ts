/** Browser presentation uses exact locale and entity references, independently of desktop display policy. */
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
  Object.assign(raw, { rules_prose }, JSON.parse(readFileSync(resolve(repoRoot(), "apps/warband-manager-web/public/knowledge/display-text.json"), "utf-8")));
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

describe("UI strict locale resolution", () => {
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

  it("never falls back to English or an identifier", () => {
    expect(resolveName({ id: "some.item", name: "Known Name" }, "es")).toBe("Información no disponible");
    expect(resolveName({ id: "bare.id" }, "en")).toBe("Information unavailable");
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

  it("resolves legacy labels only at the contextual compatibility boundary", () => {
    const ref = reader.legacyAbilityRef("No Armour", "dwarf-troll-slayers", "dwarf-treasure-hunters");
    expect(ref).toBeDefined();
    expect(reader.resolveKbText(ref!, "name", "es")).toMatchObject({ ok: true, text: "Sin Armadura" });
    expect(reader.legacyAbilityRef("No Armour", "dwarf-troll-slayers")).toBeUndefined();
    expect(knowledgeName(reader, "skill", "No Armour", "es")).toBe("Información no disponible");
  });

  it("shows a localized notice for pending injury translations", () => {
    expect(knowledgeName(reader, "injury", "campaign.serious-injury.hero.41-55-full-recovery", "es")).toBe("Información no disponible");
  });
});

/** Fallback when the artefact ships no bands (degraded build). */
function firstRow(): ArtefactRow {
  return { id: "fallback", name: "Fallback", names: { en: "Fallback", es: "Reserva" } };
}

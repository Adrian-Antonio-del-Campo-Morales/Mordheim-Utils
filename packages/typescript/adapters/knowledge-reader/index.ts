/**
 * Web migration KnowledgeReader adapter over the
 * generated KB web artefact (tools/knowledge/generate_knowledge_web.py ->
 * build/generated/knowledge-web/knowledge-web.json).
 *
 * Contract honoured (from domain/campaign/kernel/ports.ts):
 * - stable ids resolve; a missing id is `{ok:false, reason:"not_found"}`,
 *   never a name-based guess;
 * - display names resolve per requested locale with the artefact's fallback
 *   chain (requested locale -> canonical English -> any translated entry ->
 *   id), mirroring `mordheim_knowledge.i18n` without importing it;
 * - records are immutable snapshots; payload maps travel verbatim;
 * - no YAML ever reaches callers; the adapter consumes only the artefact.
 */
import type {
  Id,
  KnowledgeKind,
  KnowledgeQuery,
  KnowledgeReader,
  KnowledgeRecord,
  KnowledgeResult,
  Locale,
} from "../../domain/campaign/kernel/ports";
import { ID_KIND_BY_FAMILY } from "../../domain/campaign/kernel/ports";
import type {
  ArtefactRow,
  KnowledgeArtefact,
} from "./artefact-types";
import { validateArtefact } from "./artefact-types";

export type { ArtefactValidation, KnowledgeArtefact } from "./artefact-types";

const ID_FIELD_BY_KIND: Readonly<Record<KnowledgeKind, string>> = {
  band: "id",
  profile: "id",
  item: "item_id",
  skill: "id",
  scenario: "id",
  post_battle_step: "id",
  injury: "id",
  lore: "id",
  mutation: "id",
  hireling: "id",
  warband_group: "id",
  racial_maximum: "id",
};

/** Artefact id-space of each domain `Id` kind. */
const KIND_SOURCE: Readonly<Record<Id["kind"], KnowledgeKind>> = {
  band_id: "band",
  collection_id: "band", // collections and bands share the family/row index
  profile_id: "profile",
  item_id: "item",
  skill_id: "skill",
  scenario_id: "scenario",
  rule_id: "injury", // special rules resolve through the campaign sections
  lore_id: "lore",
  hireling_id: "hireling",
  injury_id: "injury",
  mutation_id: "mutation",
  post_battle_step_id: "post_battle_step",
  warband_group_id: "warband_group",
  racial_maximum_id: "racial_maximum",
};

/** Maps for the record families that live in the `campaign` section. */
interface CampaignMaps {
  scenarios: Map<string, ArtefactRow>;
  postBattleSteps: Map<string, ArtefactRow>;
  injuries: Map<string, ArtefactRow>;
  lores: Map<string, ArtefactRow>;
  mutations: Map<string, ArtefactRow>;
  hirelings: Map<string, ArtefactRow>;
  warbandGroups: Map<string, ArtefactRow>;
  racialMaximums: Map<string, ArtefactRow>;
};

export class KnowledgeReaderError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "KnowledgeReaderError";
  }
}

const TITLE_CASE_MINOR_WORDS: Readonly<Set<string>> = new Set([
  "a", "an", "the", "and", "but", "or", "nor", "for", "of", "on", "in", "at", "to", "from", "by", "as", "vs", "versus", "per", "over", "under", "with", "without",
  "de", "del", "al", "y", "e", "o", "u", "ni", "en", "con", "sin", "por", "para", "que", "el", "la", "los", "las", "un", "una", "unos", "unas", "entre", "hasta", "desde", "sobre", "contra", "según", "segun",
]);

/** Project display policy: visible text uses title case without changing ids or URLs. */
export function titleCaseDisplay(value: string): string {
  if (!value || /:\/\//.test(value)) return value;
  if (/^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}$/.test(value)) return value;
  const words = value.split(/(\s+)/);
  const indexes = words.flatMap((word, index) => /\S/.test(word) ? [index] : []);
  return words.map((word, index) => {
    if (!/\S/.test(word)) return word;
    const position = indexes.indexOf(index);
    return word.split("-").map((part) => {
      const letters = part.replace(/[^\p{L}\p{N}]/gu, "");
      if (!letters) return part;
      if (/^[A-Z0-9]+$/.test(letters) && letters.length <= 3) return part;
      const lower = part.toLocaleLowerCase();
      const key = letters.toLocaleLowerCase();
      if (TITLE_CASE_MINOR_WORDS.has(key) && position > 0 && position < indexes.length - 1) return lower;
      return lower.split("'").map((segment) => {
        const first = segment.search(/[\p{L}\p{N}]/u);
        return first < 0 ? segment : segment.slice(0, first) + segment[first].toLocaleUpperCase() + segment.slice(first + 1);
      }).join("'");
    }).join("-");
  }).join("");
}

function rowNames(row: ArtefactRow): Readonly<Record<string, string>> {
  const merged = row.names;
  const i18n = row.name_i18n;
  const names: Record<string, string> = {};
  const canonical = typeof row.name === "string" ? row.name.trim() : "";
  if (canonical) names.en = canonical;
  if (typeof i18n === "object" && i18n !== null) {
    for (const [locale, value] of Object.entries(i18n as Record<string, unknown>)) {
      if (typeof value === "string" && value && !names[locale]) names[locale] = value;
    }
  }
  if (typeof merged === "object" && merged !== null) {
    for (const [locale, value] of Object.entries(merged as Record<string, unknown>)) {
      if (typeof value === "string" && value && !names[locale]) names[locale] = value;
    }
  }
  return names;
}

/**
 * Resolve the display name for one locale following the KB fallback chain:
 * requested locale -> canonical English -> any translated entry. Returns the
 * id itself as last resort (ids remain visible instead of crashing).
 */
export function resolveName(
  row: ArtefactRow,
  locale: Locale,
): string {
  const names = rowNames(row);
  const requested = names[locale];
  if (requested) return requested;
  const canonical = names.en ?? row.name;
  if (typeof canonical === "string" && canonical) return canonical;
  for (const value of Object.values(names)) {
    if (value) return value;
  }
  return titleCaseDisplay(String(row.id ?? row.item_id ?? ""));
}

export class ArtefactKnowledgeReader implements KnowledgeReader {
  private readonly bands: Map<string, ArtefactRow>;
  private readonly profiles: Map<string, ArtefactRow>;
  private readonly items: Map<string, ArtefactRow>;
  private readonly skills: Map<string, ArtefactRow>;
  private readonly campaignMaps: CampaignMaps;
  private readonly campaignRaw: Readonly<Record<string, unknown>>;
  private readonly rulesProse: Readonly<Record<string, readonly ArtefactRow[]>>;
  private readonly weaponHands: Readonly<Record<string, number>>;

  private constructor(artefact: KnowledgeArtefact) {
    this.bands = ArtefactKnowledgeReader.indexById(artefact.bands, "id");
    this.profiles = ArtefactKnowledgeReader.indexProfiles(artefact.profiles);
    this.items = ArtefactKnowledgeReader.indexById(artefact.items, "item_id");
    this.skills = ArtefactKnowledgeReader.indexById(artefact.skills, "id");
    this.rulesProse = artefact.rules_prose ?? {};
    this.weaponHands = artefact.weapon_hands ?? {};
    this.campaignRaw = (artefact.campaign ?? {}) as Readonly<Record<string, unknown>>;
    this.campaignMaps = ArtefactKnowledgeReader.indexCampaignSections(
      artefact.campaign ?? {},
    );
  }

  /**
   * Build a reader from a parsed artefact. Throws `KnowledgeReaderError` on
   * a structurally invalid artefact — the build must fail, per the plan.
   */
  static from(artefact: unknown): ArtefactKnowledgeReader {
    const validation = validateArtefact(artefact);
    if (!validation.ok) {
      throw new KnowledgeReaderError(validation.message);
    }
    return new ArtefactKnowledgeReader(artefact as KnowledgeArtefact);
  }

  /**
   * Fetch the generated artefact from a URL once, validate it and build the
   * reader. The browser bundle ships the artefact as a static asset
   * (`public/knowledge/knowledge-web.json`, staged by CI); nothing is
   * inlined into the JS chunk.
   *
   * Failure modes are typed and actionable — a load failure is a
   * `KnowledgeReaderError` with the reason (`http`/`parse`/`invalid`), never
   * a raw `Response` or a `SyntaxError` leaking into the UI.
   */
  static async fromUrl(url: string, fetchFn: typeof fetch = fetch): Promise<ArtefactKnowledgeReader> {
    let response: Response;
    try {
      response = await fetchFn(url);
    } catch (cause) {
      throw new KnowledgeReaderError(`Could not fetch the knowledge artefact from "${url}": ${(cause as Error).message}`);
    }
    if (!response.ok) {
      throw new KnowledgeReaderError(
        `Knowledge artefact request failed: HTTP ${response.status} for "${url}".`,
      );
    }
    let artefact: unknown;
    try {
      artefact = await response.json();
    } catch (cause) {
      throw new KnowledgeReaderError(
        `Knowledge artefact at "${url}" is not valid JSON: ${(cause as Error).message}`,
      );
    }
    // One validation pass (`from` re-validates; both are cheap relative to
    // the network hop, and `from` stays the single entry point for fakes).
    return ArtefactKnowledgeReader.from(artefact);
  }

  private static indexById(
    rows: readonly ArtefactRow[],
    idField: string,
  ): Map<string, ArtefactRow> {
    const index = new Map<string, ArtefactRow>();
    for (const row of rows) {
      const id = row[idField];
      if (typeof id === "string" && id) index.set(id, row);
    }
    return index;
  }

  /** Profiles are unique per (collection, band_id, id) — key by `collection/band/id`. */
  private static indexProfiles(
    rows: readonly ArtefactRow[],
  ): Map<string, ArtefactRow> {
    const index = new Map<string, ArtefactRow>();
    for (const row of rows) {
      const id = row.id;
      if (typeof id !== "string" || !id) continue;
      const collection = typeof row.collection === "string" ? row.collection : "";
      const bandId = typeof row.band_id === "string" ? row.band_id : "";
      index.set(`${collection}/${bandId}/${id}`, row);
      // Unscoped fallback (last matching profile wins deterministically:
      // rows arrive sorted by id from the generator).
      index.set(id, row);
    }
    return index;
  }

  /** Maps for the record families that live in the `campaign` section. */
  private static indexCampaignSections(
    campaign: Readonly<Record<string, unknown>>,
  ): CampaignMaps {
    const empty = new Map<string, ArtefactRow>();
    const maps: CampaignMaps = {
      scenarios: empty,
      postBattleSteps: empty,
      injuries: empty,
      lores: empty,
      mutations: empty,
      hirelings: empty,
      warbandGroups: empty,
      racialMaximums: empty,
    };
    const scenariosDoc = campaign["scenarios"];
    if (Array.isArray(scenariosDoc)) {
      maps.scenarios = ArtefactKnowledgeReader.indexById(scenariosDoc as ArtefactRow[], "id");
    } else if (scenariosDoc && typeof scenariosDoc === "object") {
      const rows = (scenariosDoc as ArtefactRow)["scenarios"];
      if (Array.isArray(rows)) {
        maps.scenarios = ArtefactKnowledgeReader.indexById(rows as ArtefactRow[], "id");
      }
    }
    const hirelings = campaign["hirelings"];
    if (hirelings && typeof hirelings === "object") {
      const profiles = (hirelings as ArtefactRow)["profiles"];
      if (Array.isArray(profiles)) {
        maps.hirelings = ArtefactKnowledgeReader.indexById(profiles as ArtefactRow[], "id");
      }
    }
    const warbandGroups = campaign["warband_groups"];
    if (Array.isArray(warbandGroups)) {
      maps.warbandGroups = ArtefactKnowledgeReader.indexById(warbandGroups as ArtefactRow[], "id");
    }
    const racialMaximums = campaign["racial_maximums"];
    if (Array.isArray(racialMaximums)) {
      maps.racialMaximums = ArtefactKnowledgeReader.indexById(racialMaximums as ArtefactRow[], "id");
    }
    const mutationsDoc = campaign["mutations"];
    if (mutationsDoc && typeof mutationsDoc === "object") {
      const rows = (mutationsDoc as ArtefactRow)["mutations"];
      if (Array.isArray(rows)) {
        maps.mutations = ArtefactKnowledgeReader.indexById(rows as ArtefactRow[], "id");
      }
    }
    const magic = campaign["magic"];
    if (magic && typeof magic === "object") {
      const lores = (magic as ArtefactRow)["lores"];
      if (Array.isArray(lores)) {
        maps.lores = ArtefactKnowledgeReader.indexById(lores as ArtefactRow[], "id");
      }
    }
    const sequence = campaign["post_battle_sequence"];
    if (Array.isArray(sequence)) {
      maps.postBattleSteps = ArtefactKnowledgeReader.indexById(sequence as ArtefactRow[], "id");
    }
    // Injuries: serious-injuries tables carry rows with stable ids in the
    // artefact's campaign section; index every row of every table.
    const seriousInjuries = campaign["serious-injuries"];
    if (seriousInjuries && typeof seriousInjuries === "object") {
      const tables = (seriousInjuries as ArtefactRow)["tables"];
      if (Array.isArray(tables)) {
        const injuries = new Map<string, ArtefactRow>();
        for (const table of tables as ArtefactRow[]) {
          const rows = table["results"] ?? table["rows"];
          if (!Array.isArray(rows)) continue;
          for (const row of rows as ArtefactRow[]) {
            const id = row["id"];
            if (typeof id === "string" && id && !injuries.has(id)) injuries.set(id, {
              ...row,
              applies_to: table["applies_to"],
              table_id: table["id"],
            });
          }
        }
        maps.injuries = injuries;
      }
    }
    return maps;
  }

  private mapFor(kind: KnowledgeKind): Map<string, ArtefactRow> {
    switch (kind) {
      case "band":
        return this.bands;
      case "profile":
        return this.profiles;
      case "item":
        return this.items;
      case "skill":
        return this.skills;
      case "scenario":
        return this.campaignMaps.scenarios;
      case "post_battle_step":
        return this.campaignMaps.postBattleSteps;
      case "injury":
        return this.campaignMaps.injuries;
      case "lore":
        return this.campaignMaps.lores;
      case "mutation":
        return this.campaignMaps.mutations;
      case "hireling":
        return this.campaignMaps.hirelings;
      case "warband_group":
        return this.campaignMaps.warbandGroups;
      case "racial_maximum":
        return this.campaignMaps.racialMaximums;
    }
  }

  private toRecord(
    kind: KnowledgeKind,
    id: string,
    row: ArtefactRow,
  ): KnowledgeRecord {
    const { names: _names, name_i18n: _i18n, ...raw } = row;
    const data: Readonly<Record<string, unknown>> = Object.freeze(raw);
    const record: KnowledgeRecord = {
      kind,
      id: { kind: ID_KIND_BY_FAMILY[kind], value: id },
      names: rowNames(row),
      data,
    };
    return record;
  }

  queryKnowledge(query: KnowledgeQuery): KnowledgeResult {
    const kind = KIND_SOURCE[query.id.kind];
    const idField = ID_FIELD_BY_KIND[kind];
    const map = this.mapFor(kind);
    const row = map.get(query.id.value);
    if (!row) {
      return { ok: false, reason: "not_found" };
    }
    const value = row[idField];
    if (typeof value !== "string" || value !== query.id.value) {
      return { ok: false, reason: "not_found" };
    }
    return { ok: true, record: this.toRecord(kind, query.id.value, row) };
  }

  queryMany(queries: readonly KnowledgeQuery[]): readonly KnowledgeResult[] {
    return queries.map((query) => this.queryKnowledge(query));
  }

  /** Catalogue rows, including scoped profiles once each. */
  list(kind: KnowledgeKind): readonly ArtefactRow[] {
    return [...new Set(this.mapFor(kind).values())];
  }

  // ------------------------------------------------------------------
  // P6.7 listings (additive, not part of the frozen KnowledgeReader port).
  // Offers/collections live in the artefact's `campaign` section as raw
  // rows; the feature layer (application/features/hirelings) applies the
  // eligibility rules. Listings return the raw row plus resolved display
  // names — never a name-based identity.
  // ------------------------------------------------------------------

  /** Raw rows of the artefact's `campaign` section, for listing features. */
  campaignRows(section: string): readonly ArtefactRow[] {
    const value = this.campaignRaw[section];
    if (Array.isArray(value)) return value as ArtefactRow[];
    // Listing workflows address nested catalogues as `section:sublist`
    // (for example hired swords versus Dramatis Personae).  Keep the
    // public reader structural while resolving that canonical shape here.
    const separator = section.indexOf(":");
    if (separator < 0) return [];
    const parent = this.campaignRaw[section.slice(0, separator)];
    const child = parent && typeof parent === "object"
      ? (parent as Record<string, unknown>)[section.slice(separator + 1)]
      : undefined;
    return Array.isArray(child) ? child as ArtefactRow[] : [];
  }

  /** Raw object sections (e.g. `trading-post`, `hirelings`). */
  campaignSection(section: string): Readonly<Record<string, unknown>> {
    const value = this.campaignRaw[section];
    return value && typeof value === "object" ? (value as Readonly<Record<string, unknown>>) : {};
  }

  /** Browsable prose rows from one canonical rules document. */
  rulesDocument(stem: string): readonly ArtefactRow[] {
    return this.rulesProse[stem] ?? [];
  }

  /** Display name of a stable KB item id (trading rows only carry ids). */
  itemName(itemId: string, locale: Locale = "en"): string {
    const row = this.items.get(itemId) ?? this.campaignMaps.hirelings.get(itemId);
    if (!row) return itemId;
    const names = rowNames(row);
    return titleCaseDisplay(names[locale] ?? names["en"] ?? itemId);
  }

  /** Number of hands required by a canonical weapon, when the KB declares it. */
  weaponHandsFor(itemId: string): number | null { const value=this.weaponHands[itemId]; return Number.isInteger(value) ? value : null; }
}

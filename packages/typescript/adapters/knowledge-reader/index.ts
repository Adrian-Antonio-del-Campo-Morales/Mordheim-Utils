/**
 * KnowledgeReader adapter over the generated KB web artefact (tools/knowledge/generate_knowledge_web.py ->
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

/** A user-facing KB value, with its fallback status kept out of the text. */
export type DisplayStatus = "translated" | "canonical-fallback" | "missing";
export interface LocalizedText {
  readonly text: string;
  readonly sourceLocale: Locale | null;
  readonly status: DisplayStatus;
}

/** Stable identity plus the context needed for duplicated band rules. */
export interface DisplayRef {
  readonly kind: "band" | "profile" | "item" | "skill" | "rule" | "scenario" | "injury" | "hireling" | "lore";
  readonly id: string;
  readonly profileId?: string;
  readonly bandId?: string;
}

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

function localizedText(values: Readonly<Record<string, string>> | undefined, locale: Locale, fallback?: unknown): LocalizedText {
  if (values?.[locale]) return { text: values[locale], sourceLocale: locale, status: "translated" };
  if (values?.en) return { text: values.en, sourceLocale: "en", status: locale === "en" ? "translated" : "canonical-fallback" };
  const alternate = Object.entries(values ?? {}).find(([, value]) => Boolean(value));
  if (alternate) return { text: alternate[1], sourceLocale: alternate[0] as Locale, status: "canonical-fallback" };
  const value = typeof fallback === "string" ? fallback.trim() : "";
  // Stable ids are useful internally, never as visible recovery text.
  if (value && !/^[a-z0-9]+(?:[._:-][a-z0-9]+)+$/i.test(value)) {
    return { text: value, sourceLocale: "en", status: locale === "en" ? "translated" : "canonical-fallback" };
  }
  return { text: locale === "es" ? "Información no disponible" : "Information unavailable", sourceLocale: null, status: "missing" };
}

/** Like resolveName, but safe for UI: it never turns an id into visible text. */
export function resolveNameText(row: ArtefactRow, locale: Locale, fallback?: unknown): LocalizedText {
  return localizedText(rowNames(row), locale, fallback);
}

export class ArtefactKnowledgeReader implements KnowledgeReader {
  private readonly bands: Map<string, ArtefactRow>;
  private readonly profiles: Map<string, ArtefactRow>;
  private readonly items: Map<string, ArtefactRow>;
  private readonly skills: Map<string, ArtefactRow>;
  private readonly displayNames: Readonly<Record<string, Readonly<Record<string, string>>>>;
  private readonly displayEffects: Readonly<Record<string, Readonly<Record<string, string>>>>;
  private readonly campaignMaps: CampaignMaps;
  private readonly campaignRaw: Readonly<Record<string, unknown>>;
  private readonly rulesProse: Readonly<Record<string, readonly ArtefactRow[]>>;
  private readonly weaponHands: Readonly<Record<string, number>>;

  private constructor(artefact: KnowledgeArtefact) {
    this.bands = ArtefactKnowledgeReader.indexById(artefact.bands, "id");
    this.profiles = ArtefactKnowledgeReader.indexProfiles(artefact.profiles);
    this.items = ArtefactKnowledgeReader.indexById(artefact.items, "item_id");
    for (const item of ArtefactKnowledgeReader.magicalArtefactItems(artefact.campaign ?? {})) {
      this.items.set(String(item.item_id), item);
    }
    this.skills = ArtefactKnowledgeReader.indexById(artefact.skills, "id");
    this.displayNames = artefact.display_names ?? {};
    this.displayEffects = artefact.display_effects ?? {};
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
      response = await fetchFn(url, { cache: "no-cache" });
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
    let document = artefact as KnowledgeArtefact;
    if (typeof document.rules_prose_url === "string" && !document.rules_prose) {
      const pageUrl = (globalThis as { location?: { href: string } }).location?.href ?? "http://localhost/";
      const rulesUrl = new URL(document.rules_prose_url, new URL(url, pageUrl)).toString();
      let rulesResponse: Response;
      try {
        rulesResponse = await fetchFn(rulesUrl, { cache: "no-cache" });
      } catch (cause) {
        throw new KnowledgeReaderError(`Could not fetch the rules prose artefact from "${rulesUrl}": ${(cause as Error).message}`);
      }
      if (!rulesResponse.ok) {
        throw new KnowledgeReaderError(`Rules prose artefact request failed: HTTP ${rulesResponse.status} for "${rulesUrl}".`);
      }
      try {
        const rulesProse = await rulesResponse.json() as Readonly<Record<string, readonly ArtefactRow[]>>;
        document = { ...document, rules_prose: rulesProse };
      } catch (cause) {
        throw new KnowledgeReaderError(`Rules prose artefact at "${rulesUrl}" is not valid JSON: ${(cause as Error).message}`);
      }
    }
    if (typeof document.display_text_url === "string" && !document.display_names && !document.display_effects) {
      const pageUrl = (globalThis as { location?: { href: string } }).location?.href ?? "http://localhost/";
      const displayUrl = new URL(document.display_text_url, new URL(url, pageUrl)).toString();
      let displayResponse: Response;
      try {
        displayResponse = await fetchFn(displayUrl, { cache: "no-cache" });
      } catch (cause) {
        throw new KnowledgeReaderError(`Could not fetch the display text artefact from "${displayUrl}": ${(cause as Error).message}`);
      }
      if (!displayResponse.ok) {
        throw new KnowledgeReaderError(`Display text artefact request failed: HTTP ${displayResponse.status} for "${displayUrl}".`);
      }
      try {
        document = { ...document, ...await displayResponse.json() as Pick<KnowledgeArtefact, "display_names" | "display_effects"> };
      } catch (cause) {
        throw new KnowledgeReaderError(`Display text artefact at "${displayUrl}" is not valid JSON: ${(cause as Error).message}`);
      }
    }
    // One validation pass (`from` re-validates; both are cheap relative to
    // the network hop, and `from` stays the single entry point for fakes).
    return ArtefactKnowledgeReader.from(document);
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

  /** Exploration artefacts become inventory items under their stable reward id. */
  private static magicalArtefactItems(campaign: Readonly<Record<string, unknown>>): ArtefactRow[] {
    const document = campaign["exploration-and-income"];
    const table = document && typeof document === "object"
      ? (document as ArtefactRow)["magical_artefacts"]
      : undefined;
    const results = table && typeof table === "object"
      ? (table as ArtefactRow)["results"]
      : undefined;
    if (!Array.isArray(results)) return [];
    return (results as ArtefactRow[]).flatMap((row) => {
      const sourceId = typeof row.id === "string" ? row.id : "";
      const result = typeof row.result === "string" ? row.result : "";
      if (!sourceId.startsWith("campaign.magical-artefact.") || !result) return [];
      const localized = row.result_i18n;
      const names: Record<string, string> = { en: result };
      if (localized && typeof localized === "object") {
        for (const [locale, value] of Object.entries(localized as Record<string, unknown>)) {
          if (typeof value === "string" && value) names[locale] = value;
        }
      }
      return [{ ...row, item_id: `magical_artefact.${sourceId.slice("campaign.magical-artefact.".length)}`, names }];
    });
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

  private displayValues(values: Readonly<Record<string, Readonly<Record<string, string>>>>, id: string, profileId?: string, bandId?: string): Readonly<Record<string, string>> | undefined {
    const scoped = profileId && bandId ? values[`${bandId}:${profileId}:${id}`] : undefined;
    return scoped ?? (profileId ? values[`${profileId}:${id}`] ?? values[id] : values[id]);
  }

  /** One display lookup for roster ids spanning skills, rules, and mechanics. */
  displayName(id: string, locale: Locale, fallback?: unknown, profileId?: string, bandId?: string): string {
    const names = this.displayValues(this.displayNames, id, profileId, bandId);
    if (names?.[locale]) return names[locale];
    if (names?.en) return names.en;
    const alternate = Object.values(names ?? {}).find(Boolean);
    if (alternate) return alternate;
    return titleCaseDisplay(String(fallback ?? id).replace(/[._-]+/g, " "));
  }

  displayNameText(ref: DisplayRef, locale: Locale, fallback?: unknown): LocalizedText {
    return localizedText(this.displayValues(this.displayNames, ref.id, ref.profileId, ref.bandId), locale, fallback);
  }

  displayDescription(id: string, locale: Locale, profileId?: string, bandId?: string): string | undefined {
    const ref: DisplayRef = { kind: "rule", id, ...(profileId ? { profileId } : {}), ...(bandId ? { bandId } : {}) };
    const value = this.displayDescriptionText(ref, locale);
    return value.status === "missing" ? undefined : value.text;
  }

  displayDescriptionText(ref: DisplayRef, locale: Locale): LocalizedText {
    return localizedText(this.displayValues(this.displayEffects, ref.id, ref.profileId, ref.bandId), locale);
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

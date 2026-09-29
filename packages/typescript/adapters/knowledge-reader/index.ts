/**
 * KnowledgeReader adapter over the generated KB web artefact (tools/knowledge/generate_knowledge_web.py ->
 * outputs/web-public/knowledge/knowledge-web.json).
 *
 * Contract honoured (from domain/campaign/kernel/ports.ts):
 * - stable ids resolve; a missing id is `{ok:false, reason:"not_found"}`,
 *   never a name-based guess;
 * - display text resolves only in the requested locale; incomplete or invalid
 *   references produce a localized unavailable notice, never a raw identifier;
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
import { PresentationIndex, presentationEntries, unavailableText, isTranslatedText, fieldValues, type TextReference, type TextField, type TextResolution, type PresentationEntry, type ResolvedKbText } from "./presentation";
export { fieldValues, unavailableText, isTranslatedText } from "./presentation";
export type { TextReference, TextField, TextResolution } from "./presentation";

export type { ArtefactValidation, KnowledgeArtefact } from "./artefact-types";

/** A user-facing KB value, with its fallback status kept out of the text. */
export type DisplayStatus = "translated" | "missing";
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
  readonly tableId?: string;
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

/**
 * Families published by the deferred campaign catalogue (T12 fase D): the
 * equipment catalogue and the campaign sections. Both travel in one fragment;
 * `ensureCatalogue` names the family the calling flow actually needs.
 */
export type CatalogueKind = "items" | "campaign";

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
  return fieldValues(row, "name");
}

/**
 * Resolve the declared name in one locale, or a localized unavailable notice.
 */
export function resolveName(
  row: ArtefactRow,
  locale: Locale,
): string {
  return localizedText(rowNames(row), locale).text;
}

function localizedText(values: Readonly<Record<string, string>> | undefined, locale: Locale): LocalizedText {
  const text = values?.[locale];
  return isTranslatedText(text)
    ? { text, sourceLocale: locale, status: "translated" }
    : { text: unavailableText(locale), sourceLocale: null, status: "missing" };
}

/** Like resolveName, but safe for UI: it never turns an id into visible text. */
export function resolveNameText(row: ArtefactRow, locale: Locale): LocalizedText {
  return localizedText(rowNames(row), locale);
}

export class ArtefactKnowledgeReader implements KnowledgeReader {
  private readonly presentation: PresentationIndex;
  private readonly presentationErrors = new Map<string, Extract<TextResolution, { ok: false }>>();
  private readonly presentationRows = new WeakMap<object, TextReference>();
  private readonly presentationEntries: readonly PresentationEntry[];
  private readonly bands: Map<string, ArtefactRow>;
  private readonly profiles: Map<string, ArtefactRow>;
  private items: Map<string, ArtefactRow>;
  private readonly skills: Map<string, ArtefactRow>;
  private campaignMaps: CampaignMaps;
  private campaignRaw: Readonly<Record<string, unknown>>;
  private readonly rulesProse: Readonly<Record<string, readonly ArtefactRow[]>>;
  private readonly weaponHands: Readonly<Record<string, number>>;
  /** The assembled document; deferred families are merged back into it. */
  private document: KnowledgeArtefact;
  private readonly fetcher: typeof fetch;
  private readonly baseUrl: string | null;
  private readonly catalogueUrl: string | null;
  private readonly catalogueDigest: string | null;
  /** Families the initial document does not publish; see `ensureCatalogue`. */
  private readonly deferredFamilies = new Set<CatalogueKind>();
  private readonly loadedFamilies = new Set<CatalogueKind>();
  /** Single in-flight load: concurrent ensure calls share one request. */
  private catalogueLoad: Promise<void> | null = null;

  private constructor(
    artefact: KnowledgeArtefact,
    origin: { url: string; fetchFn: typeof fetch } | null = null,
  ) {
    this.document = artefact;
    this.fetcher = origin?.fetchFn ?? fetch;
    this.baseUrl = origin?.url ?? null;
    this.catalogueUrl = typeof artefact.catalogue_url === "string" && artefact.catalogue_url ? artefact.catalogue_url : null;
    this.catalogueDigest = typeof artefact.catalogue_digest === "string" && artefact.catalogue_digest ? artefact.catalogue_digest : null;
    if (this.catalogueUrl) {
      if (!Array.isArray(artefact.items)) this.deferredFamilies.add("items");
      if (artefact.campaign === undefined) this.deferredFamilies.add("campaign");
    }
    this.presentationEntries = presentationEntries(artefact);
    this.presentation = new PresentationIndex(this.presentationEntries);
    this.bindPresentationRows();
    this.bands = ArtefactKnowledgeReader.indexById(artefact.bands, "id");
    this.profiles = ArtefactKnowledgeReader.indexProfiles(artefact.profiles);
    this.items = ArtefactKnowledgeReader.indexById(artefact.items ?? [], "item_id");
    if (!this.deferredFamilies.has("items")) {
      for (const item of ArtefactKnowledgeReader.magicalArtefactItems(artefact.campaign ?? {})) {
        this.items.set(String(item.item_id), item);
        this.bindMagicalArtefactPresentation(item);
      }
    }
    this.skills = ArtefactKnowledgeReader.indexById(artefact.skills, "id");
    this.rulesProse = artefact.rules_prose ?? {};
    this.weaponHands = artefact.weapon_hands ?? {};
    this.campaignRaw = (artefact.campaign ?? {}) as Readonly<Record<string, unknown>>;
    this.campaignMaps = ArtefactKnowledgeReader.indexCampaignSections(
      artefact.campaign ?? {},
    );
  }

  /**
   * Binds every presentation entry to the row object its `source` points at.
   * The constructor binds the whole document; a deferred catalogue re-binds
   * only the families it merged, so `recordText` keeps working on loaded rows.
   */
  private bindPresentationRows(families?: ReadonlySet<string>): void {
    for (const entry of this.presentationEntries) {
      const segments = entry.source.split("/");
      if (families && !families.has(segments[0])) continue;
      let row: unknown = this.document;
      for (const segment of segments) {
        row = row && typeof row === "object" ? (row as Record<string, unknown>)[segment] : undefined;
      }
      if (row && typeof row === "object") this.presentationRows.set(row, entry.ref);
    }
  }

  /**
   * Bind an exploration magical artefact to the presentation entry published
   * for its inventory id (`magical_artefact.<slug>`). The item is a derived copy
   * of the campaign table row, so the source-path binding never reaches it and
   * `recordText` would otherwise report the generic fallback for a name and an
   * effect the artefact actually publishes.
   */
  private bindMagicalArtefactPresentation(row: ArtefactRow): void {
    const id = String(row.item_id ?? "");
    const entry = this.presentationEntries.find(
      (candidate) => candidate.ref.kind === "item" && candidate.ref.id === id,
    );
    if (entry) this.presentationRows.set(row, entry.ref);
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
   * (`outputs/web-public/knowledge/knowledge-web.json`, served by Vite); nothing is
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
        if (document.rules_prose_digest) {
          const bytes = new TextEncoder().encode(JSON.stringify(rulesProse));
          const hash = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)), (byte) => byte.toString(16).padStart(2, "0")).join("");
          if (hash !== document.rules_prose_digest) throw new KnowledgeReaderError("Incompatible rules presentation artefact");
        }
        document = { ...document, rules_prose: rulesProse };
      } catch (cause) {
        throw new KnowledgeReaderError(`Rules prose artefact at "${rulesUrl}" is not valid JSON: ${(cause as Error).message}`);
      }
    }
    if (typeof document.display_text_url === "string" && !document.presentation_entries) {
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
        const display = await displayResponse.json() as Pick<KnowledgeArtefact, "display_names" | "display_effects" | "presentation_entries" | "presentation_digest">;
        if (document.display_text_digest) {
          const bytes = new TextEncoder().encode(JSON.stringify(display));
          const hash = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)), (byte) => byte.toString(16).padStart(2, "0")).join("");
          if (hash !== document.display_text_digest) throw new KnowledgeReaderError("Incompatible display presentation content");
        }
        if (document.presentation_digest && display.presentation_digest !== document.presentation_digest) throw new KnowledgeReaderError("Incompatible display presentation artefact");
        if (document.presentation_digest && !Array.isArray(display.presentation_entries)) throw new KnowledgeReaderError("Missing display presentation entries");
        document = { ...document,
          ...(display.display_names !== undefined ? { display_names: display.display_names } : {}),
          ...(display.display_effects !== undefined ? { display_effects: display.display_effects } : {}),
          ...(display.presentation_entries !== undefined ? { presentation_entries: display.presentation_entries } : {}),
        };
      } catch (cause) {
        throw new KnowledgeReaderError(`Display text artefact at "${displayUrl}" is not valid JSON: ${(cause as Error).message}`);
      }
    }
    // One validation pass (`from` re-validates; both are cheap relative to
    // the network hop, and `from` stays the single entry point for fakes).
    const validation = validateArtefact(document);
    if (!validation.ok) throw new KnowledgeReaderError(validation.message);
    // The deferred catalogue is never fetched here: the first flow that needs
    // items or campaign sections calls `ensureCatalogue` (T12 fase D).
    return new ArtefactKnowledgeReader(document, { url, fetchFn });
  }

  /**
   * T12 fase D — deferred campaign catalogue.
   *
   * The published artefact keeps the initial document small (open the app,
   * choose a warband) and publishes the equipment catalogue and the campaign
   * sections as one fragment addressed by `catalogue_url` + `catalogue_digest`.
   * `fromUrl` does not fetch it; the first flow that needs it — construction and
   * starting equipment, the market, equipment transfers, the campaign inventory,
   * the PDF writer or any item/campaign name or effect resolver — awaits
   * `ensureCatalogue(kind)`.
   *
   * Contract: idempotent (a second call neither downloads nor merges again),
   * shared in flight (concurrent calls coalesce into one request), and a
   * missing fragment or a wrong digest produces a deterministic
   * `KnowledgeReaderError` instead of empty lists or technical names. Once
   * loaded, the read contract is the previous synchronous one: the same maps are
   * rebuilt from the same ids and row shapes.
   */
  async ensureCatalogue(kind: CatalogueKind): Promise<void> {
    if (!this.deferredFamilies.has(kind)) return;
    if (this.loadedFamilies.has(kind)) return;
    if (!this.catalogueLoad) this.catalogueLoad = this.loadCatalogue();
    await this.catalogueLoad;
    if (!this.loadedFamilies.has(kind)) {
      throw new KnowledgeReaderError(
        `KB catalogue "${kind}" is not published by "${this.catalogueUrl ?? ""}".`,
      );
    }
  }

  /** Has `kind` been published inline, or already loaded on demand? */
  isCatalogueLoaded(kind: CatalogueKind): boolean {
    return !this.deferredFamilies.has(kind) || this.loadedFamilies.has(kind);
  }

  /**
   * Explicit whole-artefact load: the same URL + digest mechanism, for tools and
   * tests that legitimately need every family (the product loads lazily).
   */
  static async fromFullUrl(url: string, fetchFn: typeof fetch = fetch): Promise<ArtefactKnowledgeReader> {
    const reader = await ArtefactKnowledgeReader.fromUrl(url, fetchFn);
    await Promise.all([reader.ensureCatalogue("items"), reader.ensureCatalogue("campaign")]);
    return reader;
  }

  /** Reading a deferred family before loading it is an error, never empty data. */
  private requireCatalogue(kind: CatalogueKind): void {
    if (this.isCatalogueLoaded(kind)) return;
    throw new KnowledgeReaderError(
      `KB catalogue "${kind}" is deferred and not loaded: await ensureCatalogue("${kind}") before reading it.`,
    );
  }

  private async loadCatalogue(): Promise<void> {
    const reference = this.catalogueUrl;
    if (!reference || !this.baseUrl) {
      throw new KnowledgeReaderError(
        "KB catalogue is deferred but this reader was built without a catalogue_url.",
      );
    }
    const pageUrl = (globalThis as { location?: { href: string } }).location?.href ?? "http://localhost/";
    const url = new URL(reference, new URL(this.baseUrl, pageUrl)).toString();
    // Called as a bare function: `this.fetcher(...)` would bind the reader as
    // the receiver of the global `fetch` ("Illegal invocation" in browsers).
    const fetcher: typeof fetch = this.fetcher;
    let response: Response;
    try {
      response = await fetcher(url, { cache: "no-cache" });
    } catch (cause) {
      throw new KnowledgeReaderError(`Could not fetch the KB catalogue from "${url}": ${(cause as Error).message}`);
    }
    if (!response.ok) {
      throw new KnowledgeReaderError(`KB catalogue request failed: HTTP ${response.status} for "${url}".`);
    }
    let fragment: { items?: unknown; campaign?: unknown };
    try {
      fragment = await response.json() as { items?: unknown; campaign?: unknown };
    } catch (cause) {
      throw new KnowledgeReaderError(`KB catalogue at "${url}" is not valid JSON: ${(cause as Error).message}`);
    }
    if (this.catalogueDigest) {
      const bytes = new TextEncoder().encode(JSON.stringify(fragment));
      const hash = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)), (byte) => byte.toString(16).padStart(2, "0")).join("");
      if (hash !== this.catalogueDigest) throw new KnowledgeReaderError("Incompatible KB catalogue artefact");
    }
    this.applyCatalogue(fragment);
  }

  /** Rebuilds the deferred maps from the fragment; never a partial merge. */
  private applyCatalogue(fragment: { items?: unknown; campaign?: unknown }): void {
    if (this.deferredFamilies.has("items")) {
      const rows = Array.isArray(fragment.items) ? fragment.items as ArtefactRow[] : [];
      this.items = ArtefactKnowledgeReader.indexById(rows, "item_id");
    }
    if (this.deferredFamilies.has("campaign")) {
      const campaign = fragment.campaign && typeof fragment.campaign === "object" && !Array.isArray(fragment.campaign)
        ? fragment.campaign as Readonly<Record<string, unknown>>
        : {};
      this.campaignRaw = campaign;
      this.campaignMaps = ArtefactKnowledgeReader.indexCampaignSections(campaign);
    }
    if (this.deferredFamilies.has("items")) {
      for (const item of ArtefactKnowledgeReader.magicalArtefactItems(this.campaignRaw)) {
        this.items.set(String(item.item_id), item);
        this.bindMagicalArtefactPresentation(item);
      }
    }
    this.document = {
      ...this.document,
      ...(this.deferredFamilies.has("items") ? { items: Array.isArray(fragment.items) ? fragment.items as readonly ArtefactRow[] : [] } : {}),
      ...(this.deferredFamilies.has("campaign") ? { campaign: this.campaignRaw } : {}),
    };
    this.bindPresentationRows(new Set<string>(["items", "campaign"]));
    for (const kind of ["items", "campaign"] as const) this.loadedFamilies.add(kind);
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
        this.requireCatalogue("items");
        return this.items;
      case "skill":
        return this.skills;
      case "scenario":
        this.requireCatalogue("campaign");
        return this.campaignMaps.scenarios;
      case "post_battle_step":
        this.requireCatalogue("campaign");
        return this.campaignMaps.postBattleSteps;
      case "injury":
        this.requireCatalogue("campaign");
        return this.campaignMaps.injuries;
      case "lore":
        this.requireCatalogue("campaign");
        return this.campaignMaps.lores;
      case "mutation":
        this.requireCatalogue("campaign");
        return this.campaignMaps.mutations;
      case "hireling":
        this.requireCatalogue("campaign");
        return this.campaignMaps.hirelings;
      case "warband_group":
        this.requireCatalogue("campaign");
        return this.campaignMaps.warbandGroups;
      case "racial_maximum":
        this.requireCatalogue("campaign");
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

  resolveKbText(ref: TextReference, field: TextField, locale: Locale): TextResolution {
    const result = this.presentation.resolve(ref, field, locale);
    if (!result.ok && result.reason !== "missing-field") {
      const key = JSON.stringify([result.reason, ref.kind, ref.id, ref.bandId, ref.profileId, ref.tableId, ref.scope, field, locale]);
      // Bound imported-data diagnostics without exposing them in visible text.
      if (this.presentationErrors.size < 1000 || this.presentationErrors.has(key)) this.presentationErrors.set(key, result);
    }
    return result;
  }

  presentationDiagnostics(): readonly Extract<TextResolution, { ok: false }>[] {
    return [...this.presentationErrors.values()];
  }

  /** Isolated v5 compatibility: exact stored ability id/name, never approximate. */
  legacyAbilityRef(value: string, profileId?: string, bandId?: string): TextReference | undefined {
    const matches = this.presentationEntries.filter((entry) => {
      if (entry.ref.kind !== "skill" && entry.ref.kind !== "rule") return false;
      if (entry.source.startsWith("rules_prose/localized-labels/")) return false;
      if (entry.ref.profileId !== undefined && entry.ref.profileId !== profileId) return false;
      if (entry.ref.bandId !== undefined && entry.ref.bandId !== bandId) return false;
      return entry.ref.id === value || Object.values(entry.fields.name ?? {}).includes(value);
    });
    return matches.length === 1 ? matches[0].ref : undefined;
  }

  /** Original records only; a caller cannot supply an unrelated text fallback. */
  recordText(row: Readonly<Record<string, unknown>> | undefined, field: TextField, locale: Locale): ResolvedKbText {
    if (!row) return unavailableText(locale);
    const ref = this.presentationRows.get(row);
    if (ref) {
      const result = this.resolveKbText(ref, field, locale);
      return result.ok ? result.text : unavailableText(locale);
    }
    return unavailableText(locale);
  }

  /** Exact compatibility for captured v5 labels. Ambiguity never selects a row. */
  legacyText(value: unknown, locale: Locale): ResolvedKbText {
    if (typeof value !== "string") return unavailableText(locale);
    const matches = new Map<string, Set<ResolvedKbText>>();
    for (const entry of this.presentationEntries) {
      for (const [field, texts] of Object.entries(entry.fields)) {
        if (Object.values(texts).includes(value)) {
          const key = JSON.stringify(entry.ref);
          const translations = matches.get(key) ?? new Set<ResolvedKbText>();
          const resolved = this.resolveKbText(entry.ref, field as TextField, locale);
          translations.add(resolved.ok ? resolved.text : unavailableText(locale));
          matches.set(key, translations);
        }
      }
    }
    if (matches.size !== 1) return unavailableText(locale);
    const values = [...matches.values()][0];
    return values.size === 1 ? [...values][0] : unavailableText(locale);
  }

  displayNameText(ref: DisplayRef, locale: Locale): LocalizedText {
    const result = this.resolveKbText(ref, "name", locale);
    return result.ok ? { text: result.text, sourceLocale: locale, status: "translated" } : localizedText(undefined, locale);
  }

  displayDescriptionText(ref: DisplayRef, locale: Locale): LocalizedText {
    for (const field of ["effect", "description", "text", "note"] as const) {
      const result = this.resolveKbText(ref, field, locale);
      if (result.ok) return { text: result.text, sourceLocale: locale, status: "translated" };
      if (result.reason !== "missing-field") break;
    }
    return localizedText(undefined, locale);
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
    this.requireCatalogue("campaign");
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
    this.requireCatalogue("campaign");
    const value = this.campaignRaw[section];
    return value && typeof value === "object" ? (value as Readonly<Record<string, unknown>>) : {};
  }

  /** Browsable prose rows from one canonical rules document. */
  rulesDocument(stem: string): readonly ArtefactRow[] {
    return this.rulesProse[stem] ?? [];
  }

  /** Display name of a stable KB item id (trading rows only carry ids). */
  itemName(itemId: string, locale: Locale = "en"): string {
    this.requireCatalogue("items");
    this.requireCatalogue("campaign");
    const row = this.items.get(itemId) ?? this.campaignMaps.hirelings.get(itemId);
    return row ? resolveName(row, locale) : unavailableText(locale);
  }

  /** Number of hands required by a canonical weapon, when the KB declares it. */
  weaponHandsFor(itemId: string): number | null { const value=this.weaponHands[itemId]; return Number.isInteger(value) ? value : null; }
}

import type { ArtefactRow, KnowledgeArtefact } from "./artefact-types";

export type PresentationLocale = "es" | "en";
declare const resolvedTextBrand: unique symbol;
/** Only the resolver and its localized failure notice may construct this type. */
export type ResolvedKbText = string & { readonly [resolvedTextBrand]: true };
export const presentationFields = ["name", "effect", "description", "text", "note", "notes", "label", "result", "outcome", "rule", "reward", "author", "wyrdstone"] as const;
export type TextField = typeof presentationFields[number];
export interface TextReference {
  readonly kind: string;
  readonly id: string;
  readonly bandId?: string;
  readonly profileId?: string;
  readonly tableId?: string;
  readonly scope?: "global";
}
export interface PresentationEntry {
  readonly ref: TextReference;
  readonly fields: Partial<Record<TextField, Readonly<Record<string, string>>>>;
  /**
   * The stable locator of the row this entry describes: path keys joined by
   * `/`, with every array step written as a selector (`[id=...]`) or, for a row
   * the source does not identify canonically, as a verified hint (`[#3]`).
   * Never a bare array position: see `locatorStep` and the reader's binder.
   */
  readonly source: string;
}
export type TextResolution =
  | { readonly ok: true; readonly text: ResolvedKbText; readonly locale: PresentationLocale; readonly ref: TextReference; readonly field: TextField; readonly source: string }
  | { readonly ok: false; readonly reason: "unknown-reference" | "ambiguous-reference" | "missing-translation" | "missing-field"; readonly ref: TextReference; readonly field: TextField; readonly locale: PresentationLocale };

export function unavailableText(locale: PresentationLocale): ResolvedKbText {
  return (locale === "es" ? "Información no disponible" : "Information unavailable") as ResolvedKbText;
}

/**
 * The specific, localized notice for a record whose source publishes no
 * description at all. It is a structured absence, not a resolution failure:
 * rendering the generic `unavailableText` (or an id) here would be the visible
 * fallback defect the completeness gate rejects.
 */
export function sourceDescriptionUnavailableText(locale: PresentationLocale): ResolvedKbText {
  return (locale === "es"
    ? "La fuente no publica una descripción para este objeto."
    : "The source does not publish a description for this entry.") as ResolvedKbText;
}

export function isTranslatedText(value: unknown): value is string {
  return typeof value === "string" && Boolean(value.trim()) && !value.includes("TODO-TRANSLATE");
}

/** Canonical identifier fields a catalogue row may publish for itself. */
export const LOCATOR_IDENTITY_FIELDS = ["id", "item_id", "result_id"] as const;
/** Only brackets and commas are structural inside a selector value. */
const LOCATOR_RESERVED = /[[\],{}]/;

/** A published scalar usable in a selector, as the text it is written as. */
export function selectorValue(value: unknown): string | null {
  return typeof value === "string" && value ? value : null;
}

/** Does this row publish every pair of the conjunction? */
export function rowMatchesSelector(row: unknown, pairs: readonly (readonly [string, string])[]): boolean {
  if (!row || typeof row !== "object" || Array.isArray(row)) return false;
  const record = row as Record<string, unknown>;
  return pairs.every(([field, value]) => selectorValue(record[field]) === value);
}

/**
 * One step of a stable row locator inside an array.
 *
 * The step names the smallest conjunction of fields the row publishes that
 * addresses exactly one row of its array: its canonical identifier first, plus
 * whatever published scope makes that identifier unambiguous. A row no
 * conjunction of published fields tells apart from a sibling is addressed by a
 * positional hint the resolver verifies against the text of the entry. See
 * `PresentationEntry.source` and the binder in `index.ts`.
 */
export function locatorStep(rows: readonly unknown[], index: number): string {
  const row = rows[index];
  if (row && typeof row === "object" && !Array.isArray(row)) {
    const record = row as Record<string, unknown>;
    const candidates = [
      ...LOCATOR_IDENTITY_FIELDS.filter((field) => selectorValue(record[field]) !== null),
      ...Object.keys(record).filter((field) => !(LOCATOR_IDENTITY_FIELDS as readonly string[]).includes(field) && selectorValue(record[field]) !== null).sort(),
    ];
    const pairs: [string, string][] = [];
    for (const field of candidates) {
      const value = selectorValue(record[field]);
      if (value === null || LOCATOR_RESERVED.test(`${field}${value}`)) continue;
      pairs.push([field, value]);
      if (rows.filter((candidate) => rowMatchesSelector(candidate, pairs)).length === 1) {
        return `[${pairs.map(([name, text]) => `${name}=${text}`).join(",")}]`;
      }
    }
  }
  return `[#${index}]`;
}

/** A parsed locator step: a path key, a field conjunction, or a positional hint. */
export type ParsedLocatorStep =
  | { readonly kind: "key"; readonly key: string }
  | { readonly kind: "selector"; readonly pairs: readonly (readonly [string, string])[] }
  | { readonly kind: "hint"; readonly index: number };

/** Parse one step, or `null` when it is not part of the grammar. */
export function parseLocatorStep(step: string): ParsedLocatorStep | null {
  if (!step.startsWith("[") || !step.endsWith("]")) {
    // A bare number is the superseded positional step, never a document key.
    return /^[^/[\]]+$/.test(step) && !/^\d+$/.test(step) ? { kind: "key", key: step } : null;
  }
  const body = step.slice(1, -1);
  const hint = /^#(\d+)$/.exec(body);
  if (hint) return { kind: "hint", index: Number(hint[1]) };
  const pairs: [string, string][] = [];
  for (const part of body.split(",")) {
    const separator = part.indexOf("=");
    if (separator <= 0) return null;
    pairs.push([part.slice(0, separator), part.slice(separator + 1)]);
  }
  return pairs.length ? { kind: "selector", pairs } : null;
}

/** The steps of a locator, splitting only outside a bracketed selector. */
export function locatorSteps(source: string): string[] {
  const steps: string[] = [];
  let current = "";
  let bracketed = false;
  for (const character of source) {
    if (character === "[") bracketed = true;
    else if (character === "]") bracketed = false;
    if (character === "/" && !bracketed) {
      steps.push(current);
      current = "";
      continue;
    }
    current += character;
  }
  steps.push(current);
  return steps;
}

/** `null` for a well-formed locator, or a specific reason why it is rejected. */
export function locatorError(source: string): string | null {
  for (const step of locatorSteps(source)) {
    if (!step) return "empty locator step";
    if (!parseLocatorStep(step)) return `invalid locator step ${JSON.stringify(step)}`;
  }
  return null;
}

/** Read one declared locale only. Raw strings are canonical English, never Spanish. */
export function fieldValues(row: ArtefactRow, field: TextField): Readonly<Record<string, string>> {
  const values: Record<string, string> = {};
  const canonical = field === "notes" && Array.isArray(row[field]) && row[field].every((line) => typeof line === "string") ? row[field].join("\n") : row[field];
  if (isTranslatedText(canonical)) values.en = canonical;
  for (const candidate of [row[`${field}_i18n`], row[field === "name" ? "names" : field === "effect" ? "effects" : `${field}_i18n`]]) {
    if (candidate && typeof candidate === "object" && !Array.isArray(candidate)) {
      for (const [locale, value] of Object.entries(candidate)) {
        // Explicit pending or empty translations override canonical values.
        if (isTranslatedText(value)) values[locale] = value;
        else delete values[locale];
      }
    }
  }
  return values;
}

/** Also used for small in-memory fixtures. Production uses the generated entries. */
export function presentationEntries(artefact: KnowledgeArtefact): readonly PresentationEntry[] {
  if (artefact.presentation_entries) return artefact.presentation_entries;
  const entries: PresentationEntry[] = [];
  const add = (kind: string, rows: readonly ArtefactRow[], source: string, context: Partial<TextReference> = {}) => {
    for (const [index, row] of rows.entries()) {
      const id = row.id ?? row.item_id;
      if (typeof id !== "string") continue;
      const fields: PresentationEntry["fields"] = {};
      for (const field of presentationFields) {
        const values = fieldValues(row, field);
        if (Object.keys(values).length) fields[field] = values;
      }
      if (!fields.name && fields.result) fields.name = fields.result;
      const entryKind = kind === "rule" && /^(skill|spell)\./.test(id) ? "skill" : kind;
      const ref = { ...context, kind: entryKind, id, ...(typeof row.band_id === "string" ? { bandId: row.band_id } : {}) };
      const applies = row.applies_to as { profile_ids?: string[] } | undefined;
      const profiles = applies?.profile_ids;
      const step = locatorStep(rows, index);
      if (profiles?.length) {
        for (const profileId of profiles) entries.push({ ref: { ...ref, profileId }, fields, source: `${source}/${step}` });
      } else entries.push({ ref, fields, source: `${source}/${step}` });
    }
  };
  for (const [kind, rows] of [["band", artefact.bands], ["profile", artefact.profiles], ["item", artefact.items ?? []], ["skill", artefact.skills], ["collection", artefact.collections ?? []]] as const) add(kind, rows, { band: "bands", profile: "profiles", item: "items", skill: "skills", collection: "collections" }[kind]);    for (const [bandIndex, band] of artefact.bands.entries()) {
    if (!Array.isArray(band.variants)) continue;
    const variants = band.variants as readonly unknown[];
    for (const [variantIndex, variant] of band.variants.entries()) {
      const source = `bands/${locatorStep(artefact.bands, bandIndex)}/variants/${locatorStep(variants, variantIndex)}`;
      const fields: PresentationEntry["fields"] = { name: fieldValues(variant, "name") };
      entries.push({ ref: { kind: "record", id: source }, fields, source });
    }
  }
  for (const [section, rows] of Object.entries(artefact.rules_prose ?? {})) add("rule", rows, `rules_prose/${section}`);
  for (const [family, rows] of Object.entries(artefact.mechanics ?? {})) {
    for (const [index, row] of rows.entries()) {
      const kind = typeof row.id === "string" && /^(skill|spell)\./.test(row.id) ? "skill" : "mechanic";
      const start = entries.length;
      const step = locatorStep(rows, index);
      add(kind, [row], `mechanics/${family}`);
      for (let i = start; i < entries.length; i++) entries[i] = { ...entries[i], source: `mechanics/${family}/${step}` };
    }
  }
  const campaign = artefact.campaign ?? {};
  const sectionRows = (section: string, key: string): ArtefactRow[] => {
    const value = (campaign[section] as ArtefactRow | undefined)?.[key];
    return Array.isArray(value) ? value : [];
  };
  add("hireling", sectionRows("hirelings", "profiles"), "campaign/hirelings/profiles");
  add("rule", sectionRows("hirelings", "rules"), "campaign/hirelings/rules");
  add("scenario", sectionRows("scenarios", "scenarios"), "campaign/scenarios/scenarios");
  add("lore", sectionRows("magic", "lores"), "campaign/magic/lores");
  add("record", sectionRows("serious-injuries", "tables"), "campaign/serious-injuries/tables");    const lores = sectionRows("magic", "lores");
  for (const [index, lore] of lores.entries()) {
    if (Array.isArray(lore.spells)) add("skill", lore.spells, `campaign/magic/lores/${locatorStep(lores, index)}/spells`);
  }
  const injuryTables = sectionRows("serious-injuries", "tables");
  for (const [index, table] of injuryTables.entries()) {
    if (Array.isArray(table.results)) add("injury", table.results, `campaign/serious-injuries/tables/${locatorStep(injuryTables, index)}/results`, { tableId: String(table.id) });
  }
  return entries;
}

export class PresentationIndex {
  private readonly entries = new Map<string, PresentationEntry[]>();
  constructor(entries: readonly PresentationEntry[]) {
    for (const entry of entries) {
      const key = JSON.stringify([entry.ref.kind, entry.ref.id]);
      const bucket = this.entries.get(key) ?? [];
      if (!bucket.some((candidate) => JSON.stringify(candidate.ref) === JSON.stringify(entry.ref) && JSON.stringify(candidate.fields) === JSON.stringify(entry.fields))) bucket.push(entry);
      this.entries.set(key, bucket);
    }
  }
  resolve(ref: TextReference, field: TextField, locale: PresentationLocale): TextResolution {
    const candidates = (this.entries.get(JSON.stringify([ref.kind, ref.id])) ?? []).filter((entry) =>
      (["bandId", "profileId", "tableId"] as const).every((key) => ref.scope === "global" ? ref[key] === undefined && entry.ref[key] === undefined : ref[key] === undefined || ref[key] === entry.ref[key]));
    const reason = !candidates.length ? "unknown-reference" : candidates.length !== 1 ? "ambiguous-reference" : undefined;
    if (reason) return { ok: false, reason, ref, field, locale };
    const entry = candidates[0];
    if (!Object.hasOwn(entry.fields, field)) return { ok: false, reason: "missing-field", ref, field, locale };
    const text = entry.fields[field]?.[locale];
    if (!isTranslatedText(text)) return { ok: false, reason: "missing-translation", ref, field, locale };
    return { ok: true, text: text as ResolvedKbText, locale, ref: entry.ref, field, source: entry.source };
  }
}

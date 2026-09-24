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
  readonly source: string;
}
export type TextResolution =
  | { readonly ok: true; readonly text: ResolvedKbText; readonly locale: PresentationLocale; readonly ref: TextReference; readonly field: TextField; readonly source: string }
  | { readonly ok: false; readonly reason: "unknown-reference" | "ambiguous-reference" | "missing-translation" | "missing-field"; readonly ref: TextReference; readonly field: TextField; readonly locale: PresentationLocale };

export function unavailableText(locale: PresentationLocale): ResolvedKbText {
  return (locale === "es" ? "Información no disponible" : "Information unavailable") as ResolvedKbText;
}

export function isTranslatedText(value: unknown): value is string {
  return typeof value === "string" && Boolean(value.trim()) && !value.includes("TODO-TRANSLATE");
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
      if (profiles?.length) {
        for (const profileId of profiles) entries.push({ ref: { ...ref, profileId }, fields, source: `${source}/${index}` });
      } else entries.push({ ref, fields, source: `${source}/${index}` });
    }
  };
  for (const [kind, rows] of [["band", artefact.bands], ["profile", artefact.profiles], ["item", artefact.items], ["skill", artefact.skills], ["collection", artefact.collections ?? []]] as const) add(kind, rows, { band: "bands", profile: "profiles", item: "items", skill: "skills", collection: "collections" }[kind]);
  for (const [bandIndex, band] of artefact.bands.entries()) {
    if (!Array.isArray(band.variants)) continue;
    for (const [variantIndex, variant] of band.variants.entries()) {
      const source = `bands/${bandIndex}/variants/${variantIndex}`;
      const fields: PresentationEntry["fields"] = { name: fieldValues(variant, "name") };
      entries.push({ ref: { kind: "record", id: source }, fields, source });
    }
  }
  for (const [section, rows] of Object.entries(artefact.rules_prose ?? {})) add("rule", rows, `rules_prose/${section}`);
  for (const [family, rows] of Object.entries(artefact.mechanics ?? {})) {
    for (const [index, row] of rows.entries()) {
      const kind = typeof row.id === "string" && /^(skill|spell)\./.test(row.id) ? "skill" : "mechanic";
      const start = entries.length;
      add(kind, [row], `mechanics/${family}`);
      for (let i = start; i < entries.length; i++) entries[i] = { ...entries[i], source: `mechanics/${family}/${index}` };
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
  add("record", sectionRows("serious-injuries", "tables"), "campaign/serious-injuries/tables");
  for (const [index, lore] of sectionRows("magic", "lores").entries()) {
    if (Array.isArray(lore.spells)) add("skill", lore.spells, `campaign/magic/lores/${index}/spells`);
  }
  for (const [index, table] of sectionRows("serious-injuries", "tables").entries()) {
    if (Array.isArray(table.results)) add("injury", table.results, `campaign/serious-injuries/tables/${index}/results`, { tableId: String(table.id) });
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

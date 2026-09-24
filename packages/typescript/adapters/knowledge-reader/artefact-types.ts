/**
 * P4.3: raw shapes of the generated KB web artefact.
 *
 * The artefact is produced by `tools/knowledge/generate_knowledge_web.py` into
 * `outputs/web-public/knowledge/knowledge-web.json`. These types describe
 * the *document* as stored — the adapter (index.ts) flattens it into the
 * domain's `KnowledgeRecord`s.
 */

export type LocaleText = Readonly<Record<string, string>>;

/** Raw KB row: everything travels; names/effects per locale when present. */
export interface ArtefactRow {
  readonly id?: string;
  readonly item_id?: string;
  readonly [key: string]: unknown;
}

export interface ArtefactIndexes {
  readonly bands_by_collection?: Readonly<Record<string, readonly string[]>>;
  readonly items_by_id?: Readonly<Record<string, number>>;
}

export interface KnowledgeArtefact {
  readonly presentation_entries?: readonly import("./presentation").PresentationEntry[];
  readonly presentation_digest?: string;
  readonly rules_prose_digest?: string;
  readonly display_text_digest?: string;
  readonly schema_version: number;
  readonly ruleset: string;
  readonly collections?: readonly ArtefactRow[];
  readonly bands: readonly ArtefactRow[];
  readonly profiles: readonly ArtefactRow[];
  readonly items: readonly ArtefactRow[];
  readonly skills: readonly ArtefactRow[];
  readonly mechanics?: Readonly<Record<string, readonly ArtefactRow[]>>;
  readonly display_names?: Readonly<Record<string, LocaleText>>;
  readonly display_effects?: Readonly<Record<string, LocaleText>>;
  readonly weapon_hands?: Readonly<Record<string, number>>;
  readonly rules_prose?: Readonly<Record<string, readonly ArtefactRow[]>>;
  readonly rules_prose_url?: string;
  readonly display_text_url?: string;
  readonly campaign?: Readonly<Record<string, unknown>>;
  readonly indexes?: ArtefactIndexes;
}

/** Validation of an artefact before it is indexed. */
export type ArtefactValidation =
  | { readonly ok: true }
  | {
      readonly ok: false;
      readonly reason: "not_an_object" | "missing_section" | "bad_schema_version" | "bad_presentation";
      readonly message: string;
    };

export function validateArtefact(value: unknown): ArtefactValidation {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return { ok: false, reason: "not_an_object", message: "KB artefact must be a JSON object" };
  }
  const artefact = value as KnowledgeArtefact;
  if (artefact.schema_version !== 1) {
    return {
      ok: false,
      reason: "bad_schema_version",
      message: `KB artefact schema_version ${String(artefact.schema_version)} unsupported (expected 1)`,
    };
  }
  for (const section of ["bands", "profiles", "items", "skills"] as const) {
    if (!Array.isArray(artefact[section])) {
      return { ok: false, reason: "missing_section", message: `KB artefact section ${section} missing or not an array` };
    }
  }
  if (artefact.presentation_entries !== undefined) {
    const object = (row: unknown): row is Record<string, unknown> => row !== null && typeof row === "object" && !Array.isArray(row);
    const fields = new Set(["name", "effect", "description", "text", "note", "notes", "label", "result", "outcome", "rule", "reward", "author", "wyrdstone"]);
    const identities = new Set<string>();
    if (!Array.isArray(artefact.presentation_entries)) return { ok: false, reason: "bad_presentation", message: "Invalid presentation entries" };
    for (const entry of artefact.presentation_entries) {
      if (!object(entry) || !object(entry.ref) || typeof entry.ref.kind !== "string" || !entry.ref.kind || typeof entry.ref.id !== "string" || !entry.ref.id || typeof entry.source !== "string" || !entry.source || !object(entry.fields)) {
        return { ok: false, reason: "bad_presentation", message: "Invalid presentation entry" };
      }
      for (const scope of ["bandId", "profileId", "tableId"] as const) {
        if (entry.ref[scope] !== undefined && (typeof entry.ref[scope] !== "string" || !entry.ref[scope])) return { ok: false, reason: "bad_presentation", message: "Invalid presentation scope" };
      }
      if (entry.ref.scope !== undefined && (entry.ref.scope !== "global" || entry.ref.bandId !== undefined || entry.ref.profileId !== undefined || entry.ref.tableId !== undefined)) return { ok: false, reason: "bad_presentation", message: "Invalid global presentation scope" };
      const identity = JSON.stringify([entry.ref.kind, entry.ref.id, entry.ref.bandId, entry.ref.profileId, entry.ref.tableId]);
      if (identities.has(identity)) return { ok: false, reason: "bad_presentation", message: "Duplicate presentation identity" };
      identities.add(identity);
      for (const [field, values] of Object.entries(entry.fields)) {
        if (!fields.has(field) || !object(values) || Object.values(values).some((text) => typeof text !== "string")) return { ok: false, reason: "bad_presentation", message: "Invalid presentation field" };
      }
    }
  }
  return { ok: true };
}

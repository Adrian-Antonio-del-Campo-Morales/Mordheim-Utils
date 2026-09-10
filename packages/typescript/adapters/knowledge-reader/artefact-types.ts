/**
 * P4.3: raw shapes of the generated KB web artefact.
 *
 * The artefact is produced by `tools/knowledge/generate_knowledge_web.py` into
 * `build/generated/knowledge-web/knowledge-web.json`; its shape is agreed in
 * `docs/decisions/web-knowledge-catalog-inventory.md`. These types describe
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
  readonly schema_version: number;
  readonly ruleset: string;
  readonly collections?: readonly ArtefactRow[];
  readonly bands: readonly ArtefactRow[];
  readonly profiles: readonly ArtefactRow[];
  readonly items: readonly ArtefactRow[];
  readonly skills: readonly ArtefactRow[];
  readonly weapon_hands?: Readonly<Record<string, number>>;
  readonly rules_prose?: Readonly<Record<string, readonly ArtefactRow[]>>;
  readonly campaign?: Readonly<Record<string, unknown>>;
  readonly indexes?: ArtefactIndexes;
}

/** Validation of an artefact before it is indexed. */
export type ArtefactValidation =
  | { readonly ok: true }
  | {
      readonly ok: false;
      readonly reason: "not_an_object" | "missing_section" | "bad_schema_version";
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
  return { ok: true };
}

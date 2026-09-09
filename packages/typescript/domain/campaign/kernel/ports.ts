/**
 * P3.4 (web-migration-parallel-plan.md §2.2/§4): frozen public knowledge and
 * file ports. These are the seams that let domain, application, UI and the
 * adapters (P3.2, P4.3) be developed and tested in parallel against fakes.
 *
 * Contracts honoured by every implementation:
 * - `queryKnowledge` returns canonical KB records keyed by stable ids; a
 *   missing id is an empty result or a typed error, never a name-based guess.
 * - file ports speak the `.mordheim` v4 contract; `saved_at` is the only
 *   volatile field in semantic comparisons.
 * - No React, DOM, browser globals or filesystem inside these modules.
 */

import type { Campaign } from "./state";

/** Discriminator for the canonical KB record kinds (P4.1 inventory). */
export type KnowledgeKind =
  | "band"
  | "profile"
  | "item"
  | "skill"
  | "scenario"
  | "post_battle_step"
  | "injury"
  | "lore"
  | "mutation"
  | "hireling"
  | "warband_group"
  | "racial_maximum";

/** Locale code of the display text requested from the KB. */
export type Locale = "en" | "es";

/**
 * Canonical KB record. The web KB artefact (P4.2/P4.3) materializes records in
 * this shape; the domain never sees YAML.
 */
export interface KnowledgeRecord {
  readonly kind: KnowledgeKind;
  /** Stable KB id, byte-identical to `sources/knowledge/`. */
  readonly id: Id;
  /** Display names per locale; the caller picks. */
  readonly names: Readonly<Record<Locale, string>> | Readonly<Record<string, string>>;
  /** Canonical payload (preserve-in-place; consumer decides what to read). */
  readonly data: Readonly<Record<string, unknown>>;
}

/** Stable id reference — a tagged union so callers cannot mix id spaces.
 *
 *  The kind discriminators cover every `KnowledgeKind` family emitted by the
 *  P4.2 generator (verified against the real artefact, see
 *  docs/decisions/web-rework-parallel-log.md). Field mapping in the raw
 *  artefact: `items` rows use `item_id`; every other family uses `id`.
 */
export type Id =
  | { readonly kind: "band_id"; readonly value: string }
  | { readonly kind: "profile_id"; readonly value: string }
  | { readonly kind: "item_id"; readonly value: string }
  | { kind: "skill_id"; value: string }
  | { kind: "scenario_id"; value: string }
  | { kind: "rule_id"; value: string }
  | { kind: "lore_id"; value: string }
  | { kind: "hireling_id"; value: string }
  | { kind: "injury_id"; value: string }
  | { kind: "mutation_id"; value: string }
  | { kind: "post_battle_step_id"; value: string }
  | { kind: "warband_group_id"; value: string }
  | { kind: "racial_maximum_id"; value: string }
  | { kind: "collection_id"; value: string };

/** Artifact record family → id discriminator, in one place for adapters. */
export const ID_KIND_BY_FAMILY: Readonly<Record<KnowledgeKind, Id["kind"]>> = {
  band: "band_id",
  profile: "profile_id",
  item: "item_id",
  skill: "skill_id",
  scenario: "scenario_id",
  post_battle_step: "post_battle_step_id",
  injury: "injury_id",
  lore: "lore_id",
  mutation: "mutation_id",
  hireling: "hireling_id",
  warband_group: "warband_group_id",
  racial_maximum: "racial_maximum_id",
};

export interface KnowledgeQuery {
  readonly id: Id;
  /** Requested display locale; default `en`. */
  readonly locale?: Locale;
}

/** Typed absence: `record: null` means the id does not exist in the KB. */
export type KnowledgeResult =
  | { readonly ok: true; readonly record: KnowledgeRecord }
  | { readonly ok: false; readonly reason: "not_found" };

/**
 * The knowledge read model of the domain. Implemented by the P4.3 adapter
 * over the generated artefact; faked in tests. No YAML ever reaches callers.
 */
export interface KnowledgeReader {
  queryKnowledge(query: KnowledgeQuery): KnowledgeResult;
  /** Resolve many ids in one call (roster rendering, export checks). */
  queryMany(queries: readonly KnowledgeQuery[]): readonly KnowledgeResult[];
}

/** Why a campaign file operation failed (stable, testable reasons). */
export type CampaignFileErrorReason =
  | "invalid_json"
  | "bad_marker"
  | "retired_version"
  | "unsupported_version"
  | "schema_violation"
  | "unknown_section"
  | "io_error";

export interface CampaignFileError {
  /** Discriminator so `ParseResult`/`SerializeResult` narrow by `ok`. */
  readonly ok: false;
  readonly reason: CampaignFileErrorReason;
  /** Human-readable, actionable; never includes internal stack traces. */
  readonly message: string;
  /** JSON path or location hint where available (e.g. `campaign.warriors[3]`). */
  readonly location?: string;
  /** For retired/unsupported versions: the version found. */
  readonly found_version?: number;
  /** Versions the reader supports. */
  readonly supported_versions: readonly number[];
}

/** A parsed, validated `.mordheim` v4 document (raw contract shape). */
export interface CampaignFileV4 {
  readonly marker: "MORDHEIM_CAMPAIGN_MANAGER";
  readonly format_version: 4;
  readonly saved_at: string;
  readonly campaign: Record<string, unknown>;
  readonly view?: Record<string, unknown>;
}

export interface ParseOk {
  readonly ok: true;
  readonly document: CampaignFileV4;
}

export type ParseResult = ParseOk | CampaignFileError;

export type SerializeResult =
  | { readonly ok: true; readonly text: string }
  | CampaignFileError;

/**
 * File adapter port (implemented by P3.2). The application uses only this —
 * never JSON.parse on campaign text directly.
 */
export interface CampaignFilePort {
  /** Parse and validate campaign file text against the v4 contract. */
  parseCampaignFile(text: string): ParseResult;
  /** Serialize a campaign state into a valid v4 document text. */
  serializeCampaign(campaign: Campaign): SerializeResult;
}

/** In-memory representation of a loaded file for the application layer. */
export interface LoadedCampaignFile {
  readonly document: CampaignFileV4;
  readonly campaign: Campaign;
  readonly view: Record<string, unknown>;
}

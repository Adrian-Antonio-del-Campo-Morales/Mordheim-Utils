/**
 * Campaign-file adapter: the real `.mordheim` v5 file
 * adapter — reader, validator and writer of the neutral contract defined in
 * `contracts/campaign-file-v5/`.
 *
 * Source of truth: `contracts/campaign-file-v5/campaign-file-v5.schema.json`.
 * The structural rules are NOT re-implemented by hand: the schema is imported
 * directly from the contract file and a small
 * generic draft 2020-12 validator walks it (`./schema-validator.ts`). Every
 * structural violation carries the schema's JSON path, mirroring the Python
 * reader's error reporting.
 *
 * Contract honoured (from domain/campaign/kernel/ports.ts):
 * - envelope checks in order: invalid JSON -> bad marker -> retired v1-4
 *   (naming found + supported) -> unsupported version -> schema violation;
 * - `saved_at` is the only volatile field (semantic comparisons ignore it —
 *   see the contract README's comparison rules);
 * - open payload maps (`step_state`, `participants`, `searches`, ...) are
 *   preserved in place, never pruned or reordered;
 * - no React, DOM, browser APIs or filesystem in this module: text comes in,
 *   text goes out, the caller owns IO.
 */
import type {
  CampaignFileError,
  CampaignFilePort,
  CampaignFileV5,
  ParseResult,
  SerializeResult,
} from "../../domain/campaign/kernel/ports";
import type { Campaign } from "../../domain/campaign/kernel/state";
import SCHEMA_JSON from "../../../../contracts/campaign-file-v5/campaign-file-v5.schema.json";
import { validateAgainstSchema } from "./schema-validator";

const MARKER = "MORDHEIM_CAMPAIGN_MANAGER";
const SUPPORTED_VERSIONS: readonly number[] = [5];
const RETIRED_VERSIONS = [1, 2, 3, 4];

/** A successfully imported document plus its typed campaign projection. */
export interface ParsedCampaignFile {
  readonly ok: true;
  readonly document: CampaignFileV5;
  readonly campaign: Campaign;
  /** Always an object (an absent view section reads as `{}`). */
  readonly view: Record<string, unknown>;
}

type ErrorExtras = Partial<
  Omit<CampaignFileError, "ok" | "reason" | "message" | "supported_versions">
>;

function error(
  reason: CampaignFileError["reason"],
  message: string,
  extras?: ErrorExtras,
): CampaignFileError {
  return { ok: false, reason, message, supported_versions: SUPPORTED_VERSIONS, ...extras };
}

/**
 * The envelope gates: exactly the rejection ladder of the contract README,
 * in order, so the cheapest and most specific failure wins.
 */
function parseEnvelope(text: string): ParseResult {
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch (e) {
    return error("invalid_json", `The file is not valid JSON: ${(e as Error).message}`);
  }
  if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
    return error("invalid_json", "The file's top level must be a JSON object.");
  }
  const doc = parsed as Record<string, unknown>;
  if (doc["marker"] !== MARKER) {
    return error("bad_marker", "This file is not a Mordheim campaign file (marker mismatch).");
  }
  const version = doc["format_version"];
  if (typeof version !== "number" || !Number.isInteger(version)) {
    return error(
      "unsupported_version",
      `The format version is missing or malformed (${JSON.stringify(version) ?? "undefined"}).`,
    );
  }
  if (RETIRED_VERSIONS.includes(version)) {
    return error(
      "retired_version",
      `Format version ${version} is retired. This application reads only format version 5; no automatic migration is available.`,
      { found_version: version },
    );
  }
  if (version !== 5) {
    return error(
      "unsupported_version",
      `Format version ${version} is newer than this application supports. Update the application to open this file.`,
      { found_version: version },
    );
  }
  if (typeof doc["saved_at"] !== "string") {
    return error(
      "schema_violation",
      "The document is missing the saved_at timestamp.",
      { location: "saved_at" },
    );
  }
  if (typeof doc["campaign"] !== "object" || doc["campaign"] === null) {
    return error(
      "schema_violation",
      "The document is missing the campaign section.",
      { location: "campaign" },
    );
  }
  return { ok: true, document: doc as unknown as CampaignFileV5 };
}

/**
 * Default file port. `parseCampaignFile` and `serializeCampaign` never throw:
 * every failure is a typed `CampaignFileError` value.
 */
import { validateCampaignSemantics } from "./semantics";

/**
 * Exploration follow-up captions are canonical `label_key` references, not
 * stored sentences: the contract allows no captured text, no single-locale
 * objects and no mirrored pairs. A document whose history carries any of
 * those belongs to an earlier format and is rejected at load with the
 * specific `incompatible_format` error — before any component can render it.
 */
const CAPTION_KEYS: ReadonlySet<string> = new Set([
  "resource",
  "item",
  "characteristic_test",
  "roll_table",
  "magical_artefact",
]);

function isCaptionRow(row: unknown): row is Record<string, unknown> {
  return typeof row === "object" && row !== null && !Array.isArray(row);
}

function incompatibleCaption(location: string): CampaignFileError {
  return error(
    "incompatible_format",
    "This file stores exploration follow-up captions as captured text. Current documents persist a canonical label_key per follow-up roll; captured-caption files belong to an earlier format and cannot be opened.",
    { location },
  );
}

function validateExplorationCaptions(doc: Record<string, unknown>): CampaignFileError | null {
  const campaign = doc["campaign"];
  if (typeof campaign !== "object" || campaign === null || Array.isArray(campaign)) return null;
  const posts = (campaign as Record<string, unknown>)["post_battles"];
  if (!Array.isArray(posts)) return null;
  for (const [postIndex, post] of posts.entries()) {
    if (!isCaptionRow(post)) continue;
    const states = post["step_state"];
    if (!isCaptionRow(states)) continue;
    const exploration = states["exploration"];
    if (!isCaptionRow(exploration)) continue;
    const rolls = exploration["follow_up_rolls"];
    if (!Array.isArray(rolls)) continue;
    for (const [rollIndex, roll] of rolls.entries()) {
      if (!isCaptionRow(roll)) continue;
      if (typeof roll["label_key"] === "string" && CAPTION_KEYS.has(roll["label_key"])) continue;
      return incompatibleCaption(`campaign.post_battles[${postIndex}].step_state.exploration.follow_up_rolls[${rollIndex}].label_key`);
    }
  }
  return null;
}

export class CampaignFileV5Adapter implements CampaignFilePort {
  parseCampaignFile(text: string): ParseResult {
    const envelope = parseEnvelope(text);
    if (!envelope.ok) {
      return envelope;
    }
    const doc = envelope.document as unknown as Record<string, unknown>;
    const schemaErrors = validateAgainstSchema(SCHEMA_JSON, doc);
    if (schemaErrors.length > 0) {
      const first = schemaErrors[0];
      return error("schema_violation", first.message, { location: first.location });
    }
    // Semantic hardening (TS mirror of the desktop `_validate_domain`):
    // cross-field invariants the JSON Schema cannot express.
    const semanticErrors = validateCampaignSemantics(
      (doc as { campaign?: unknown }).campaign as never,
    );
    if (semanticErrors.length > 0) {
      return error("schema_violation", semanticErrors[0].message, { location: "campaign" });
    }
    const captionError = validateExplorationCaptions(doc);
    if (captionError) return captionError;
    return { ok: true, document: envelope.document };
  }

  serializeCampaign(campaign: Campaign): SerializeResult {
    const document: Record<string, unknown> = {
      marker: MARKER,
      format_version: 5,
      saved_at: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
      campaign: campaign as unknown as Record<string, unknown>,
    };
    const schemaErrors = validateAgainstSchema(SCHEMA_JSON, document);
    if (schemaErrors.length > 0) {
      const first = schemaErrors[0];
      return error(
        "schema_violation",
        `Refusing to save: the document violates the contract (${first.message})`,
        { location: first.location },
      );
    }
    const semanticErrors = validateCampaignSemantics(campaign as never);
    if (semanticErrors.length > 0) {
      return error(
        "schema_violation",
        `Refusing to save: the document violates the contract (${semanticErrors[0].message})`,
        { location: "campaign" },
      );
    }
    return { ok: true, text: JSON.stringify(document, null, 1) + "\n" };
  }
}

/** Parse + typed projection in one call, or the first typed error. */
export function parseCampaignFileDetailed(
  text: string,
): ParsedCampaignFile | CampaignFileError {
  const result = new CampaignFileV5Adapter().parseCampaignFile(text);
  if (!result.ok) {
    return result;
  }
  const doc = result.document as unknown as Record<string, unknown>;
  return {
    ok: true,
    document: result.document,
    campaign: doc["campaign"] as unknown as Campaign,
    view: (doc["view"] ?? {}) as Record<string, unknown>,
  };
}

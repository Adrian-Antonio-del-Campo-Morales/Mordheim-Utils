/**
 * Minimal deterministic file port used by isolated tests.
 *
 * Production composition uses the real v4 adapter; this implementation exists
 * only to exercise UI error paths without filesystem or browser I/O.
 */
import type { Campaign, CampaignFilePort, ParseResult, SerializeResult } from "./types";

const MARKER = "MORDHEIM_CAMPAIGN_MANAGER";

export class FakeCampaignFilePort implements CampaignFilePort {
  parseCampaignFile(text: string): ParseResult {
    let parsed: unknown;
    try {
      parsed = JSON.parse(text);
    } catch {
      return {
        ok: false,
        reason: "invalid_json",
        message: "The file is not valid JSON.",
        supported_versions: [4],
      };
    }
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      return {
        ok: false,
        reason: "invalid_json",
        message: "The file's top level must be a JSON object.",
        supported_versions: [4],
      };
    }
    const doc = parsed as Record<string, unknown>;
    if (doc["marker"] !== MARKER) {
      return {
        ok: false,
        reason: "bad_marker",
        message: "This file is not a Mordheim campaign file (wrong marker).",
        supported_versions: [4],
      };
    }
    const version = doc["format_version"];
    if (typeof version === "number" && version < 4) {
      return {
        ok: false,
        reason: "retired_version",
        message: `Format version ${version} is no longer supported.`,
        found_version: version,
        supported_versions: [4],
      };
    }
    if (version !== 4) {
      return {
        ok: false,
        reason: "unsupported_version",
        message: `Format version ${String(version)} is not supported.`,
        found_version: typeof version === "number" ? version : undefined,
        supported_versions: [4],
      };
    }
    if (typeof doc["campaign"] !== "object" || doc["campaign"] === null) {
      return {
        ok: false,
        reason: "schema_violation",
        message: "The document is missing the campaign section.",
        location: "campaign",
        supported_versions: [4],
      };
    }
    return { ok: true, document: doc as never };
  }

  serializeCampaign(campaign: Campaign): SerializeResult {
    const document = {
      marker: MARKER,
      format_version: 4,
      saved_at: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
      campaign: campaign as unknown as Record<string, unknown>,
    };
    return { ok: true, text: JSON.stringify(document, null, 1) + "\n" };
  }
}

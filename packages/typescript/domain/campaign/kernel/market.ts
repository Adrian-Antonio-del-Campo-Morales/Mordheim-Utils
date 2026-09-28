/**
 * T10: trading-post availability verdict.
 *
 * The KB publishes each market entry with an `availability` kind and a list of
 * typed `restrictions`. This module turns those into one stable verdict, in the
 * domain, so the service and the interface cannot disagree about whether a
 * printed item may be bought.
 *
 * Reading of the restriction vocabulary (contract
 * `contracts/knowledge-editorial-v1/campaign-trading-post.yaml.schema.json`):
 * - `warband_only` / `warband_forbidden` always name the bands or groups they
 *   scope, and are evaluated;
 * - `condition` carries the source wording in `note` and, since T10, may also
 *   name the `band_ids`/`groups` the printed clause scopes
 *   (`Masters of Horror only`). A scoped `condition` is evaluated exactly like
 *   `warband_only`; an unscoped one keeps refusing the purchase, because the
 *   application cannot place an editorial note, while an unscoped note next to a
 *   structured scope on the same entry is redundant prose and does not block;
 * - `profile_only` and `heroes_only` are not purchase availability: the first
 *   carries the per-warband limit elsewhere in the entry, the second is an
 *   assignment rule evaluated when equipment reaches a warrior.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { IdString, OpenPayload } from "../index";

export type MarketIssueCode =
  | "market_not_listed"
  | "market_not_common"
  | "market_warband_only"
  | "market_warband_forbidden"
  | "market_condition_unstructured";

export interface MarketIssue {
  readonly code: MarketIssueCode;
  readonly message: string;
  /** Source wording of the clause, when the entry carries one. */
  readonly note?: string;
}

export interface MarketAvailabilityInput {
  /** One `campaign.trading-post.items[]` row (or the equivalent catalogue row). */
  readonly offer: Readonly<Record<string, unknown>>;
  readonly band_id: IdString;
  /** Warband groups the band belongs to (`warband-group.*`). */
  readonly groups: readonly IdString[];
  /** Display name used in the message; the item id when no name is known. */
  readonly item_name: string;
}

function restrictionsOf(offer: Readonly<Record<string, unknown>>): readonly OpenPayload[] {
  const rows = offer["restrictions"];
  return Array.isArray(rows) ? (rows as OpenPayload[]).filter((row) => row && typeof row === "object") : [];
}

function identifiers(value: unknown): readonly string[] {
  return Array.isArray(value) ? value.map(String) : [];
}

/** Whether a restriction's declared scope covers the band. */
function scopeMatches(restriction: OpenPayload, input: MarketAvailabilityInput): boolean {
  const bandIds = identifiers(restriction["band_ids"]);
  const groupIds = identifiers(restriction["groups"]);
  return bandIds.includes(input.band_id) || groupIds.some((id) => input.groups.includes(id));
}

/** Whether the restriction declares a machine-readable scope at all. */
function hasScope(restriction: OpenPayload): boolean {
  return identifiers(restriction["band_ids"]).length > 0 || identifiers(restriction["groups"]).length > 0;
}

/**
 * The availability verdict of one market offer for one warband, or `null` when
 * the printed data lets the warband buy it.
 */
export function marketAvailabilityIssueFor(input: MarketAvailabilityInput): MarketIssue | null {
  const availability = (input.offer["availability"] ?? {}) as OpenPayload;
  const kind = String(availability["kind"] ?? "common");
  if (kind !== "common") {
    return {
      code: "market_not_common",
      message: kind === "not_sold"
        ? `${input.item_name} is not sold: the source prints it as a unique find, not as a market entry.`
        : `Rare items must be obtained through a successful rare search: ${input.item_name} is not a common item.`,
    };
  }
  const restrictions = restrictionsOf(input.offer);
  const scoped = restrictions.some(
    (restriction) => restriction["type"] === "warband_only" || restriction["type"] === "warband_forbidden" || hasScope(restriction),
  );
  for (const restriction of restrictions) {
    const type = String(restriction["type"] ?? "");
    const note = typeof restriction["note"] === "string" ? restriction["note"] : undefined;
    if (type === "warband_only" || (type === "condition" && hasScope(restriction))) {
      if (!scopeMatches(restriction, input)) {
        return {
          code: "market_warband_only",
          message: `${input.item_name} is not available to this warband.`,
          ...(note ? { note } : {}),
        };
      }
      continue;
    }
    if (type === "warband_forbidden" && scopeMatches(restriction, input)) {
      return {
        code: "market_warband_forbidden",
        message: `${input.item_name} is forbidden to this warband.`,
        ...(note ? { note } : {}),
      };
    }
    if (type === "condition" && !hasScope(restriction) && !scoped) {
      return {
        code: "market_condition_unstructured",
        message: `${input.item_name} carries an unscoped purchase condition: ${note ?? "no structured scope is published"}.`,
        ...(note ? { note } : {}),
      };
    }
  }
  return null;
}

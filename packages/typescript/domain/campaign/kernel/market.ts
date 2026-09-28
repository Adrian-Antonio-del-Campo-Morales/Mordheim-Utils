/**
 * T10 (post-review): trading-post availability verdict.
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
 *   `warband_only`;
 * - since the T10 review, an **unscoped** `condition` is never ignored, even
 *   when another restriction on the same entry already carries a scope: without
 *   a published `structure` it refuses the purchase
 *   (`market_condition_unstructured`). A published `structure` makes the clause
 *   machine-readable instead:
 *   `repeats_entry` (an editorial declaration that the note repeats what the
 *   entry already publishes — scope, availability kind or price — and adds no
 *   requirement of its own), `creation_only` (the printed "only when the
 *   warband is created"), `characteristic_roll`, `purchase_unit`, and the
 *   recipient-scoped `profile_ids` / `skill_ids` / `max_per_wizard`, which the
 *   purchase cannot decide for a stash copy and which the assignment route
 *   reads from the same published block;
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
  | "market_creation_only"
  | "market_condition_unstructured";

export interface MarketIssue {
  readonly code: MarketIssueCode;
  readonly message: string;
  /** Source wording of the clause, when the entry carries one. */
  readonly note?: string;
}

/** The recipient facts a market entry can scope with `profile_ids`/`skill_ids`. */
export interface MarketRecipient {
  readonly profile_id: IdString | null;
  readonly kind: string;
  readonly skill_ids: readonly IdString[];
}

export interface MarketAvailabilityInput {
  /** One `campaign.trading-post.items[]` row (or the equivalent catalogue row). */
  readonly offer: Readonly<Record<string, unknown>>;
  readonly band_id: IdString;
  /** Warband groups the band belongs to (`warband-group.*`). */
  readonly groups: readonly IdString[];
  /** Display name used in the message; the item id when no name is known. */
  readonly item_name: string;
  /**
   * Whether the purchase happens while the warband is still being created. A
   * `creation_only` condition (`standard_of_nagarythe`: "may only be purchased
   * when the warband is created") is refused everywhere else.
   */
  readonly at_creation?: boolean;
}

function restrictionsOf(offer: Readonly<Record<string, unknown>>): readonly OpenPayload[] {
  const rows = offer["restrictions"];
  return Array.isArray(rows) ? (rows as OpenPayload[]).filter((row) => row && typeof row === "object") : [];
}

function identifiers(value: unknown): readonly string[] {
  return Array.isArray(value) ? value.map(String) : [];
}

/** The published structured requirement of a `condition`, when the KB carries one. */
function structureOf(restriction: OpenPayload): OpenPayload | null {
  const structure = restriction["structure"];
  return structure && typeof structure === "object" && !Array.isArray(structure)
    ? (structure as OpenPayload)
    : null;
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
 * Why one `condition` clause is not decided by the entry, or `null` when the
 * publication lets the purchase proceed.
 *
 * A note that carries no `structure` is a pending requirement: the application
 * cannot place the printed clause, so it refuses the purchase explicitly
 * instead of dropping it. That decision is deliberately independent of whether
 * the same entry also publishes a scope — a warband restriction must not make
 * an unrelated clause disappear.
 */
function conditionIssueFor(
  input: MarketAvailabilityInput,
  restriction: OpenPayload,
  note: string | undefined,
): MarketIssue | null {
  const structure = structureOf(restriction);
  if (!structure) {
    return {
      code: "market_condition_unstructured",
      message: `${input.item_name} carries a purchase condition the catalogue does not publish in a structured form: ${note ?? "no structured requirement is published"}.`,
      ...(note ? { note } : {}),
    };
  }
  // Editorial declaration, verified at ingestion: the note repeats requirements
  // the entry already publishes (scope, availability kind, price) and adds none.
  if (structure["repeats_entry"] === true) return null;
  if (structure["creation_only"] === true && input.at_creation !== true) {
    return {
      code: "market_creation_only",
      message: `${input.item_name} may only be bought while the warband is being created.`,
      ...(note ? { note } : {}),
    };
  }
  // `profile_ids`, `skill_ids`, `max_per_wizard`, `characteristic_roll` and
  // `purchase_unit` are published requirements of the entry but not decisions of
  // the purchase: a stash copy has no recipient and the roll belongs to the
  // battle layer. They travel with the entry and the assignment/price routes read
  // them from the same block.
  return null;
}

/**
 * Why one market entry cannot reach one warrior, or `null` when it may.
 *
 * The recipient-scoped half of a structured `condition` cannot be decided by a
 * purchase into the stash (there is no recipient yet), so the assignment route
 * reads it from the same published block: `profile_ids` (`nightmare`: "Vampires,
 * Necromancers and Grave Guards only", `whirling_blades`: "Slayers only") and
 * `skill_ids`.
 */
export function marketAssignmentIssueFor(
  offer: Readonly<Record<string, unknown>>,
  recipient: MarketRecipient,
  itemName: string,
): MarketIssue | null {
  for (const restriction of restrictionsOf(offer)) {
    if (String(restriction["type"] ?? "") !== "condition") continue;
    const structure = structureOf(restriction);
    if (!structure) continue;
    const note = typeof restriction["note"] === "string" ? restriction["note"] : undefined;
    const profiles = identifiers(structure["profile_ids"]);
    if (profiles.length > 0 && !(recipient.profile_id && profiles.includes(recipient.profile_id))) {
      return {
        code: "market_condition_unstructured",
        message: `${itemName} is restricted to ${profiles.join(", ")}: ${recipient.profile_id ?? recipient.kind} may not carry it.`,
        ...(note ? { note } : {}),
      };
    }
    const skills = identifiers(structure["skill_ids"]);
    if (skills.length > 0 && !skills.some((skill) => recipient.skill_ids.includes(skill))) {
      return {
        code: "market_condition_unstructured",
        message: `${itemName} requires ${skills.join(", ")}: ${recipient.profile_id ?? recipient.kind} does not have it.`,
        ...(note ? { note } : {}),
      };
    }
  }
  return null;
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
  for (const restriction of restrictionsOf(input.offer)) {
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
    if (type === "condition") {
      const issue = conditionIssueFor(input, restriction, note);
      if (issue) return issue;
    }
  }
  return null;
}

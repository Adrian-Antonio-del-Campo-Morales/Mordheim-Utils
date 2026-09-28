/**
 * T10: roster-lifecycle clauses.
 *
 * Some printed band rules operate on a warband *after* it was built: the Dame of
 * the Mare must be replaced before anything else is recruited, and a Skaven
 * Slave who rolls "the lad's got talent" is executed instead of promoted. The KB
 * publishes each of them in
 * `campaign.recruitment-and-veterans.lifecycle_clauses` as a band, a rule, the
 * trigger the campaign already observes, an operation from a closed vocabulary
 * and the profiles it operates on, so this module never reads the rule prose.
 *
 * The clauses are rule knowledge; which of them is satisfied right now is
 * campaign state, recomputed from the roster on every read and never persisted.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { CampaignDocument, IdString, OpenPayload } from "../index";
import type { KnowledgeReader } from "./ports";

/** Reader that can also reach the published campaign catalogues. */
export type LifecycleReader = KnowledgeReader & {
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
};

export type LifecycleOperation = "require_member" | "remove_member";
export type LifecycleTrigger = "recruitment" | "henchman_promotion";

export interface LifecycleClauseFacts {
  readonly id: IdString;
  readonly band_id: IdString;
  readonly rule_id: IdString;
  readonly trigger: LifecycleTrigger;
  readonly operation: LifecycleOperation;
  readonly profile_ids: readonly IdString[];
  readonly name: string;
  readonly name_i18n: Readonly<Record<string, string>>;
  readonly effect: string;
}

function names(value: unknown): Readonly<Record<string, string>> {
  if (!value || typeof value !== "object") return {};
  const out: Record<string, string> = {};
  for (const [key, text] of Object.entries(value as OpenPayload)) {
    if (typeof text === "string" && text.trim()) out[key] = text;
  }
  return out;
}

/** Every lifecycle clause the artefact publishes for a band, in catalogue order. */
export function lifecycleClausesOf(
  reader: LifecycleReader,
  bandId: IdString,
): readonly LifecycleClauseFacts[] {
  const rows = reader.campaignSection?.("recruitment-and-veterans")?.["lifecycle_clauses"];
  if (!Array.isArray(rows) || !bandId) return [];
  return rows.flatMap((entry) => {
    if (!entry || typeof entry !== "object") return [];
    const row = entry as OpenPayload;
    const id = String(row["id"] ?? "");
    const operation = String(row["operation"] ?? "");
    const trigger = String(row["trigger"] ?? "");
    if (!id || String(row["band_id"] ?? "") !== bandId) return [];
    if (operation !== "require_member" && operation !== "remove_member") return [];
    if (trigger !== "recruitment" && trigger !== "henchman_promotion") return [];
    return [{
      id,
      band_id: String(row["band_id"] ?? ""),
      rule_id: String(row["rule_id"] ?? ""),
      trigger,
      operation,
      profile_ids: Array.isArray(row["profile_ids"]) ? row["profile_ids"].map(String) : [],
      name: String(row["name"] ?? id),
      name_i18n: names(row["name_i18n"]),
      effect: String(row["effect"] ?? ""),
    }];
  });
}

function profilesInRoster(document: CampaignDocument): ReadonlySet<string> {
  return new Set(document.campaign.warriors.map((warrior) => String(warrior.profile_id ?? "")));
}

/**
 * `require_member` clauses whose profile is missing from the roster, so the
 * warband still owes the replacement.
 */
export function missingRequiredMembers(
  document: CampaignDocument,
  reader: LifecycleReader,
): readonly LifecycleClauseFacts[] {
  // A clause of this family replaces a member the warband *lost* mid-campaign
  // ("if the Dame is killed, she must be replaced before any other recruit").
  // A draft has lost nobody: the clause cannot be owed while the warband is
  // still being composed, and the roster may be built in any order.
  if (document.campaign.configuration.is_draft) return [];
  const present = profilesInRoster(document);
  return lifecycleClausesOf(reader, document.campaign.identity.band_id).filter(
    (clause) =>
      clause.trigger === "recruitment" &&
      clause.operation === "require_member" &&
      clause.profile_ids.length > 0 &&
      !clause.profile_ids.some((profileId) => present.has(profileId)),
  );
}

export interface LifecycleIssue {
  readonly code: "lifecycle_member_required";
  readonly message: string;
  readonly clause_id: IdString;
  readonly rule_id: IdString;
  readonly profile_ids: readonly IdString[];
}

/**
 * Why recruiting `profileId` is refused right now, or `null` when it is allowed.
 * The profiles a clause names are the only ones it lets through while it is
 * unmet; recruiting one of them is exactly what discharges the clause.
 */
export function recruitmentGateIssueFor(
  document: CampaignDocument,
  reader: LifecycleReader,
  profileId: IdString,
): LifecycleIssue | null {
  for (const clause of missingRequiredMembers(document, reader)) {
    if (clause.profile_ids.includes(profileId)) continue;
    return {
      code: "lifecycle_member_required",
      message: `Recruit ${clause.profile_ids.join(", ")} first: ${clause.name} is missing from the warband.`,
      clause_id: clause.id,
      rule_id: clause.rule_id,
      profile_ids: clause.profile_ids,
    };
  }
  return null;
}

/**
 * The `remove_member` clause that fires when the named profile is promoted, or
 * `null` when the printed rules let the promotion happen.
 */
export function promotionRemovalClauseFor(
  reader: LifecycleReader,
  bandId: IdString,
  profileId: IdString | null,
): LifecycleClauseFacts | null {
  if (!profileId) return null;
  return (
    lifecycleClausesOf(reader, bandId).find(
      (clause) =>
        clause.trigger === "henchman_promotion" &&
        clause.operation === "remove_member" &&
        clause.profile_ids.includes(profileId),
    ) ?? null
  );
}

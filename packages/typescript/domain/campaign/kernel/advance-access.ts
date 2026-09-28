/**
 * T10: advancement-time skill-list access.
 *
 * Some printed band rules widen the skill tables a profile may choose from when
 * it rolls a specific advance. The published case is
 * `dwarf-slayer-cult-web / axe-hurlers--born-marksmen`: "If an Axe Hurler rolls
 * a 'That Lad's Got Talent' as an advancement, he may always choose Shooting
 * skills as one of his two skill list choices. He may do this even if there are
 * no heroes with Shooting Skills in the warband."
 *
 * The KB publishes each grant in
 * `campaign.recruitment-and-veterans.advance_access_clauses` as a band, a rule,
 * the trigger the campaign already observes, the recipient profiles and the
 * granted skill lists, so the advance flow never reads the rule prose.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { IdString, OpenPayload } from "../index";
import type { KnowledgeReader } from "./ports";

/** Reader that can also reach the published campaign catalogues. */
export type AdvanceAccessReader = KnowledgeReader & {
  campaignSection?(section: string): Readonly<Record<string, unknown>>;
};

export type AdvanceAccessTrigger = "that-lads-got-talent";

export interface AdvanceAccessClauseFacts {
  readonly id: IdString;
  readonly band_id: IdString;
  readonly rule_id: IdString;
  readonly trigger: AdvanceAccessTrigger;
  readonly profile_ids: readonly IdString[];
  /** Skill lists the profile may additionally choose from (e.g. `shooting`). */
  readonly skill_lists: readonly IdString[];
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

function identifiers(value: unknown): readonly IdString[] {
  return Array.isArray(value) ? value.map(String).filter((id) => id.length > 0) : [];
}

/** Every advancement-access grant the artefact publishes for a band. */
export function advanceAccessClausesOf(
  reader: AdvanceAccessReader,
  bandId: IdString,
): readonly AdvanceAccessClauseFacts[] {
  const rows = reader.campaignSection?.("recruitment-and-veterans")?.["advance_access_clauses"];
  if (!Array.isArray(rows) || !bandId) return [];
  return rows.flatMap((entry) => {
    if (!entry || typeof entry !== "object") return [];
    const row = entry as OpenPayload;
    const id = String(row["id"] ?? "");
    if (!id || String(row["band_id"] ?? "") !== bandId) return [];
    if (row["trigger"] !== "that-lads-got-talent") return [];
    return [{
      id,
      band_id: String(row["band_id"] ?? ""),
      rule_id: String(row["rule_id"] ?? ""),
      trigger: "that-lads-got-talent",
      profile_ids: identifiers(row["profile_ids"]),
      skill_lists: identifiers(row["skill_lists"]),
      name: String(row["name"] ?? id),
      name_i18n: names(row["name_i18n"]),
      effect: String(row["effect"] ?? ""),
    }];
  });
}

/** The grant that widens `profileId`'s skill tables, or `null`. */
export function advanceAccessGrantFor(
  reader: AdvanceAccessReader,
  bandId: IdString,
  profileId: IdString | null,
): AdvanceAccessClauseFacts | null {
  if (!profileId) return null;
  return advanceAccessClausesOf(reader, bandId).find((clause) => clause.profile_ids.includes(profileId)) ?? null;
}

/** Additional skill lists the printed grant opens for `profileId`. */
export function additionalSkillListsFor(
  reader: AdvanceAccessReader,
  bandId: IdString,
  profileId: IdString | null,
): readonly IdString[] {
  return advanceAccessGrantFor(reader, bandId, profileId)?.skill_lists ?? [];
}

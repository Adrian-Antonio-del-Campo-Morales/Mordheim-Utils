/**
 * T10 (post-review): the one place where the frozen T09 construction contract is
 * applied to a concrete equipment change.
 *
 * The construction contract answers "may this member hold this kit?" for a
 * profile. Every roster mutation that adds or removes equipment — a creation
 * purchase, a stash assignment, a transfer, the commit gate — must ask that same
 * question about *the kit the member ends up with*, never about one item in
 * isolation and never through a second table of tokens kept by the caller. This
 * module composes the frozen primitives (`equipmentIssueFor` for the item being
 * added, `memberEquipmentIssuesFor` for the complete set) and separates the
 * codes that make a composition invalid from the codes that are reports for the
 * KB, so an unknown item row or a prose-only clause is still surfaced without
 * blocking a legal choice.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { KnowledgeReader } from "./ports";
import type { CampaignDocument, IdString, UseCaseRejection, Warrior } from "./usecases";
import {
  equipmentIssueFor,
  memberEquipmentIssuesFor,
  profileFactsOf,
  type ConstructionIssue,
  type ConstructionIssueCode,
} from "../construction";

/**
 * Construction verdicts that make a composition invalid. Everything else the
 * contract returns is a report for the KB (`equipment_unknown_item`,
 * `construction_clause_unstructured`) and must never refuse a legal choice.
 */
export const FATAL_EQUIPMENT_CODES: readonly ConstructionIssueCode[] = [
  "equipment_not_permitted",
  "equipment_forbidden",
  "equipment_limit_exceeded",
  "equipment_required_missing",
];

/** Whether one construction code refuses the change (as opposed to reporting). */
export function equipmentVerdictIsFatal(code: ConstructionIssueCode): boolean {
  return FATAL_EQUIPMENT_CODES.includes(code);
}

/** Distinct item ids a warrior row holds, one entry per equipment row. */
export function equipmentSetOf(warrior: Warrior): readonly IdString[] {
  return [...new Set(warrior.equipment.map((entry) => entry.item_id))];
}

/** Copies of one item a warrior row holds across all of its entries. */
export function equipmentCopiesOf(warrior: Warrior, itemId: IdString): number {
  return warrior.equipment
    .filter((entry) => entry.item_id === itemId)
    .reduce((total, entry) => total + (entry.quantity ?? 1), 0);
}

/**
 * Verdict of one equipment change of one member against the T09 contract.
 *
 * - `added_item_ids` are the ids the change introduces; each one is evaluated
 *   per item, together with the item kind and tags, the band-wide and
 *   profile-level prohibitions and the equipment lists the selected variant
 *   activates;
 * - `resulting_item_ids` is the member's complete kit after the change, so the
 *   whole-set limits (compulsory family, missile-weapon cap, per-profile
 *   exemptions) are decided as a set and a partial view cannot make an invalid
 *   kit look legal.
 *
 * Returns the first fatal issue, or an informational issue when no fatal one
 * applies, or `null` when the change is legal.
 */
export function equipmentChangeIssueFor(args: {
  readonly document: CampaignDocument;
  readonly reader: KnowledgeReader;
  readonly warrior_id: IdString;
  readonly added_item_ids?: readonly IdString[];
  readonly resulting_item_ids: readonly IdString[];
}): ConstructionIssue | null {
  const warrior = args.document.campaign.warriors.find((row) => row.id === args.warrior_id);
  // Hirelings and hand-authored rows carry no band profile: the contract is the
  // band's construction rules and does not apply to them.
  if (!warrior?.profile_id) return null;
  const profile = profileFactsOf(
    args.reader,
    args.document.campaign.identity.band_id,
    warrior.profile_id,
  );
  if (!profile) return null;
  const variant = args.document.campaign.identity.mercenary_variant ?? null;
  let report: ConstructionIssue | null = null;
  for (const itemId of [...new Set(args.added_item_ids ?? [])]) {
    const issue = equipmentIssueFor(args.reader, profile, itemId, variant);
    if (!issue) continue;
    if (equipmentVerdictIsFatal(issue.code)) return issue;
    report ??= issue;
  }
  for (const issue of memberEquipmentIssuesFor(args.reader, profile, args.resulting_item_ids)) {
    if (equipmentVerdictIsFatal(issue.code)) return issue;
    report ??= issue;
  }
  return report;
}

/**
 * Typed rejection of a fatal equipment verdict, or `null` when the change is
 * legal. A container that is not on the member's lists is `not_available`; a
 * prohibition or a whole-set limit is `limit_violated`.
 */
export function equipmentChangeRejectionFor(args: {
  readonly document: CampaignDocument;
  readonly reader: KnowledgeReader;
  readonly warrior_id: IdString;
  readonly added_item_ids?: readonly IdString[];
  readonly resulting_item_ids: readonly IdString[];
}): UseCaseRejection | null {
  const issue = equipmentChangeIssueFor(args);
  if (!issue || !equipmentVerdictIsFatal(issue.code)) return null;
  return {
    ok: false,
    reason: issue.code === "equipment_not_permitted" ? "not_available" : "limit_violated",
    message: issue.message,
    subject_ids: issue.subject_ids,
  };
}

/** Stable reason one fatal equipment verdict becomes in the service. */
export function equipmentVerdictReason(
  code: ConstructionIssueCode,
): "not_available" | "limit_violated" {
  return code === "equipment_not_permitted" ? "not_available" : "limit_violated";
}

/**
 * Item ids a warrior row would hold after `remainingCopies` copies of `itemId`
 * stay or arrive: the row keeps the item while at least one copy remains.
 */
export function equipmentSetAfterChange(
  warrior: Warrior,
  itemId: IdString,
  remainingCopies: number,
): readonly IdString[] {
  const ids = new Set(equipmentSetOf(warrior));
  if (remainingCopies > 0) ids.add(itemId);
  else ids.delete(itemId);
  return [...ids];
}

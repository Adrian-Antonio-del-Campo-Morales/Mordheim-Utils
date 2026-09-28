/**
 * T11: the typed integration point for "these members left the table".
 *
 * Detecting that a member already left the table is a battle-time fact owned by
 * T13 — `kernel/withdrawal.ts` states it explicitly and refuses to invent battle
 * state. The interface therefore never guesses who left: it exposes this thin
 * adapter, which hands the ordered list the battle produced to the campaign
 * service and returns the stable verdict.
 *
 * Contract handed to T13 (2026-09-28):
 * - call it **once per battle**, with the roster-row ids whose models had
 *   already left the table when the warband withdrew; a henchman-group id
 *   repeats once per model that left;
 * - do not resend ids from an earlier withdrawal: the operation answers
 *   `conflict` for an id already recorded;
 * - an unknown id answers `not_found`, and a draft answers
 *   `not_permitted_in_draft`.
 *
 * The consequence itself (roster removal, per-model equipment write-off, audit
 * trail) belongs to T10 and is not reproduced here.
 */

import type { AppResult, CampaignAppService } from "./types";
import { campaignIssueSignal, type CampaignIssueCode } from "./campaign-obligations";

/** Battle-produced list of the members that left the table, in recorded order. */
export interface LeftTableWithdrawalEvent {
  readonly member_ids: readonly string[];
  /** Free-text reason captured from the caller; never an identity. */
  readonly reason?: string;
  /** Battle during which they left, when the caller knows it. */
  readonly battle_number?: number;
}

export type WithdrawalDispatch =
  | { readonly ok: true }
  | { readonly ok: false; readonly code: CampaignIssueCode | null; readonly subjectIds: readonly string[] };

function dispatch(result: AppResult): WithdrawalDispatch {
  if (result.ok) return { ok: true };
  const signal = campaignIssueSignal(result);
  return { ok: false, code: signal.code, subjectIds: signal.subjectIds };
}

/**
 * Apply the withdrawal through the real campaign service. Returns the stable
 * code and parameters so the caller can phrase the verdict without parsing the
 * English diagnostic.
 */
export async function withdrawLeftTableMembers(service: CampaignAppService, event: LeftTableWithdrawalEvent): Promise<WithdrawalDispatch> {
  return dispatch(await service.run("withdrawLeftTableMembers", {
    member_ids: [...event.member_ids],
    ...(event.reason === undefined ? {} : { reason: event.reason }),
    ...(event.battle_number === undefined ? {} : { battle_number: event.battle_number }),
  }));
}

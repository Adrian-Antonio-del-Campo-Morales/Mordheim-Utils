/**
 * T10: the campaign half of "the warband withdrew".
 *
 * Several printed band rules withdraw a warrior from the *roster* once he has
 * already left the table and the warband routs — for example the Pirate Swabbies
 * ("Blimey, They Got Away!"): "If the Pirate Warband itself Routs, any Swabbies
 * who have already left the table in previous turns ... Remove them from your
 * warband roster as if they had been killed."
 *
 * A member leaving the table is a fact supplied within Warband Manager. What the
 * campaign owns is the roster consequence, so this module exposes one operation:
 * it receives the ids of the members that left and applies the removal. The
 * Warband Manager caller is the only source of that list; Combat Lab does not
 * produce it or call this operation. The operation and its tests do not establish
 * detection or UI capture of the table fact. Nothing here
 * invents battle state.
 *
 * Contract:
 * - a hero, hireling or one-member henchman group is removed from the roster;
 * - a henchman group loses exactly one member per id occurrence; the group is
 *   removed when its last member leaves;
 * - the departing share of per-model equipment is written off (the source says
 *   "as if they had been killed", so nothing returns to the stash);
 * - the removal is written once into `campaign.manual_log` with a stable
 *   marker, so a reopen restores the same audit trail;
 * - an unknown id is refused (`not_found`) and an id already recorded as
 *   withdrawn is refused (`conflict`), so a repeated call cannot remove a
 *   member twice.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { CampaignDocument, IdString, InventoryItem, OpenPayload, Warrior } from "../index";
import type { UseCaseResult } from "../index";
import { withCampaign } from "./document";

/** Stable marker of a withdrawal audit entry inside `campaign.manual_log`. */
export const WITHDRAWAL_MARKER = "left_table_withdrawal";

export interface WithdrawalInput {
  /**
   * Ids of the roster rows whose members left the table, in the order the
   * caller recorded them. A group id may repeat once per member that left.
   */
  readonly member_ids: readonly IdString[];
  /** Free-text reason captured from the caller; never an identity. */
  readonly reason?: string;
  /** Battle during which the members left, when the caller knows it. */
  readonly battle_number?: number;
}

/** One member the operation removed, recorded for the audit trail. */
export interface WithdrawnMember {
  readonly warrior_id: IdString;
  readonly name: string;
  readonly profile_id: IdString | null;
  /** How many models the withdrawal took from that row (1, or the group size). */
  readonly quantity: number;
}

/** Audit entries of this campaign, newest last. */
export function withdrawalLog(document: CampaignDocument): readonly OpenPayload[] {
  return document.campaign.manual_log.filter((row) => row["kind"] === WITHDRAWAL_MARKER);
}

/** Ids already fully removed by a previous withdrawal, for the double-removal guard. */
export function withdrawnMemberIds(document: CampaignDocument): ReadonlySet<IdString> {
  const gone = new Set<IdString>();
  for (const entry of withdrawalLog(document)) {
    const members = Array.isArray(entry["members"]) ? entry["members"] : [];
    for (const member of members) {
      if (member && typeof member === "object" && typeof (member as OpenPayload)["warrior_id"] === "string") {
        gone.add(String((member as OpenPayload)["warrior_id"]));
      }
    }
  }
  return gone;
}

/**
 * Write off `count` copies of the departing share of a row's equipment.
 * Per-model items lose `count × copiesPerModel`; a fully removed row loses
 * every copy. The returned inventory keeps the owned/equipped counters honest.
 */
function writeOffEquipment(
  warrior: Warrior,
  count: number,
  inventory: readonly InventoryItem[],
): { readonly equipment: readonly Warrior["equipment"][number][]; readonly inventory: InventoryItem[] } {
  const quantity = warrior.quantity ?? 1;
  const full = count >= quantity;
  const next = inventory.map((item) => ({ ...item }));
  const writeOff = (itemId: IdString, amount: number): void => {
    const stock = next.find((row) => row.id === itemId);
    if (!stock || amount <= 0) return;
    stock.owned = Math.max(0, stock.owned - amount);
    stock.equipped = Math.max(0, stock.equipped - amount);
  };
  const equipment = warrior.equipment.flatMap((item) => {
    if (full) {
      writeOff(item.item_id, item.quantity);
      return [];
    }
    if (!item.per_model) return [item];
    const perModel = Math.max(1, Math.floor(item.quantity / quantity));
    const removed = Math.min(item.quantity, perModel * count);
    writeOff(item.item_id, removed);
    const remaining = item.quantity - removed;
    return remaining > 0 ? [{ ...item, quantity: remaining }] : [];
  });
  return { equipment, inventory: next.filter((item) => item.owned > 0 || item.stash > 0 || item.equipped > 0) };
}

/**
 * Apply the withdrawal of the members that left the table. Returns a new
 * document with the roster and the audit trail updated, or a typed rejection.
 */
export function withdrawLeftTableMembers(
  document: CampaignDocument,
  input: WithdrawalInput,
): UseCaseResult {
  if (document.campaign.configuration.is_draft) {
    return { ok: false, reason: "not_permitted_in_draft", message: "A draft has no battle withdrawal; edit the composition instead." };
  }
  const ids = input.member_ids.map((id) => String(id)).filter((id) => id.length > 0);
  if (ids.length === 0) {
    return { ok: false, reason: "invalid_input", message: "Name at least one member that left the table." };
  }
  const gone = withdrawnMemberIds(document);
  let warriors: Warrior[] = [...document.campaign.warriors];
  let inventory: InventoryItem[] = [...document.campaign.inventory];
  const members: WithdrawnMember[] = [];

  for (const id of ids) {
    const index = warriors.findIndex((warrior) => warrior.id === id);
    if (index < 0) {
      return gone.has(id)
        ? { ok: false, reason: "conflict", message: `${id} was already withdrawn from the roster.`, subject_ids: [id] }
        : { ok: false, reason: "not_found", message: `${id} is not a member of this warband.`, subject_ids: [id] };
    }
    const warrior = warriors[index];
    const quantity = warrior.quantity ?? 1;
    const written = writeOffEquipment(warrior, 1, inventory);
    inventory = written.inventory;
    if (quantity <= 1) {
      warriors = warriors.filter((row) => row.id !== id);
      members.push({ warrior_id: id, name: warrior.name, profile_id: warrior.profile_id ?? null, quantity });
    } else {
      warriors = warriors.map((row) => row.id === id ? { ...row, quantity: quantity - 1, equipment: written.equipment } : row);
      members.push({ warrior_id: id, name: warrior.name, profile_id: warrior.profile_id ?? null, quantity: 1 });
    }
  }

  const order = withdrawalLog(document).length + 1;
  const entry: OpenPayload = {
    kind: WITHDRAWAL_MARKER,
    order,
    ...(input.battle_number === undefined ? {} : { battle_number: input.battle_number }),
    reason: String(input.reason ?? "left the table"),
    members,
    text: members.map((member) => `${member.name} removed from the roster after leaving the table.`).join(" "),
  };
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const postBattles = post && input.battle_number !== undefined
    ? document.campaign.post_battles.map((row) =>
        row === post
          ? { ...row, event_log: [...(row.event_log ?? []), { ...entry, step: row.active_step, type: WITHDRAWAL_MARKER }] }
          : row,
      )
    : document.campaign.post_battles;

  return {
    ok: true,
    state: withCampaign(document, {
      ...document.campaign,
      warriors,
      inventory,
      post_battles: postBattles,
      manual_log: [...document.campaign.manual_log, entry],
    }),
  };
}

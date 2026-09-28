/**
 * T10: the campaign side of the Rout test.
 *
 * The Rout test itself is a battle rule (T13). What the campaign owns is the
 * *roster fact* the test reads: which recorded participants count towards the
 * warband's muster, and which ones the printed rules remove from that count.
 *
 * The published case is `lothern-sea-patrol-sar / raw-recruits--dont-mind-them`:
 * "Any Raw Recruits who are running away or have been taken out of action do not
 * count towards the need to take a Rout test for the warband." The band rule
 * names its recipients (`applies_to.profile_ids`), and the artefact materialises
 * the derived `rout_test_exempt` fact on those profiles, so this module never
 * reads the rule prose.
 *
 * Evaluated against the battle's recorded roster snapshot (`participants`) when
 * the battle carries one, so a later roster change cannot rewrite history.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { CampaignDocument, IdString, OpenPayload } from "../index";
import type { KnowledgeReader } from "./ports";
import { profileFactsOf } from "../construction";

export interface RoutTestMemberFacts {
  readonly warrior_id: IdString;
  readonly name: string;
  /** Models the row contributes (henchman groups count by quantity). */
  readonly quantity: number;
  readonly profile_id: IdString | null;
  readonly out_of_action: boolean;
  /** Whether the printed rules exclude this member from the Rout-test count. */
  readonly exempt: boolean;
  /** `quantity` when the member counts, `0` when it is excluded. */
  readonly counted_models: number;
}

export interface RoutTestFacts {
  readonly battle_number: number;
  readonly members: readonly RoutTestMemberFacts[];
  /** Models the recorded muster holds, exempt or not. */
  readonly models: number;
  /** Models that count towards the Rout test. */
  readonly counted_models: number;
  readonly out_of_action_models: number;
  /** Excluded models that are out of action: casualties the test ignores. */
  readonly exempt_out_of_action_models: number;
}

function quantityOf(value: unknown): number {
  const quantity = Number(value ?? 1);
  return Number.isInteger(quantity) && quantity > 0 ? quantity : 1;
}

/**
 * Whether the profile publishes the printed Rout-test exemption.
 *
 * The profile is resolved by band **and** id (`profileFactsOf`): the exemption is
 * a property of one band's rule, and the same profile id is printed by several
 * bands, so a global lookup by id would import another band's rule.
 */
function profileIsRoutExempt(
  reader: KnowledgeReader,
  bandId: IdString,
  profileId: IdString | null,
): boolean {
  if (!profileId) return false;
  return profileFactsOf(reader, bandId, profileId)?.rout_test_exempt === true;
}

/**
 * Rout-test roster facts of one recorded battle, or `null` when the battle is
 * unknown. Nothing is persisted: the facts are recomputed from the battle and
 * the profiles, so a reload always restores the same numbers.
 */
export function routTestFactsFor(
  document: CampaignDocument,
  reader: KnowledgeReader,
  battleNumber: number,
): RoutTestFacts | null {
  const battle = document.campaign.battles.find((row) => row.number === battleNumber);
  if (!battle) return null;
  const roster = document.campaign.warriors;
  const snapshot: readonly OpenPayload[] = battle.participants?.length
    ? battle.participants
    : roster.map((warrior) => ({
        id: warrior.id,
        name: warrior.name,
        quantity: warrior.quantity ?? 1,
      }));
  const outOfAction = new Set((battle.out_of_action_ids ?? []).map(String));
  const members = snapshot.map((row) => {
    const warriorId = String(row["id"] ?? "");
    const warrior = roster.find((item) => item.id === warriorId) ?? null;
    const profileId = warrior?.profile_id ?? null;
    const quantity = quantityOf(row["quantity"] ?? warrior?.quantity);
    const exempt = profileIsRoutExempt(reader, document.campaign.identity.band_id, profileId);
    const casualty = outOfAction.has(warriorId);
    const counted = !(exempt && casualty);
    return {
      warrior_id: warriorId,
      name: String(warrior?.name ?? row["name"] ?? warriorId),
      quantity,
      profile_id: profileId,
      out_of_action: casualty,
      exempt,
      counted_models: counted ? quantity : 0,
    };
  });
  const casualties = members.filter((member) => member.out_of_action);
  return {
    battle_number: battle.number,
    members,
    models: members.reduce((total, member) => total + member.quantity, 0),
    counted_models: members.reduce((total, member) => total + member.counted_models, 0),
    out_of_action_models: casualties.reduce((total, member) => total + member.quantity, 0),
    exempt_out_of_action_models: casualties
      .filter((member) => member.exempt)
      .reduce((total, member) => total + member.quantity, 0),
  };
}

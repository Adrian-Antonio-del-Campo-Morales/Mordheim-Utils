/**
 * P6.5 (web-migration-parallel-plan.md §7): injuries & recovery feature —
 * application-layer rules over the immutable document helpers of the P3.5
 * kernel (`withCampaign`, `pendingPostBattle`). The frozen use-case port has
 * no injury operation, so the transformations here are pure document maps —
 * they never mutate the input and results are values, never exceptions.
 *
 * Owns the *workflow* of the injury rules (ported from the desktop
 * `application/post_battle_engine.py`):
 *  - `injuryOverview` — who is injured, absent, or has unresolved rolls;
 *  - `applyInjuryOutcome` — apply a rolled serious-injury outcome: lasting
 *    conditions, missed games (absence), stat modifiers, lost eyes; unknown
 *    effect kinds are preserved as pending follow-ups (open-payload policy,
 *    contract §"unknown fields");
 *  - `recordFollowUp` — park an unresolved roll on the pending post-battle
 *    so the document stays resumable across save/load;
 *  - `recover` — decrement missed games and clear the absence (and a fully
 *    recovered warrior's injury condition), lifting the P6.4 readiness
 *    restriction that reads `games_to_miss`.
 *
 * Step navigation itself stays in P6.4's `resolveStep`; this module only
 * fills the payloads the sequence carries.
 *
 * Purity: no React, no DOM, no filesystem, no KnowledgeReader dependency.
 */

import type {
  CampaignDocument,
  IdString,
  OpenPayload,
  Warrior,
} from "../../../../domain/campaign/index";
import {
  pendingPostBattle,
  withCampaign,
} from "../../../../domain/campaign/kernel/document";

/** Why a workflow operation failed (stable reasons for the UI). */
export type InjuriesWorkflowError =
  | { readonly ok: false; readonly reason: "not_found" | "conflict" | "invalid_input"; readonly message: string };

export type InjuriesWorkflowResult =
  | { readonly ok: true; readonly document: CampaignDocument }
  | InjuriesWorkflowError;

/** A serious-injury outcome as the UI's roll form produces it. */
export interface InjuryOutcomeInput {
  readonly warrior_id: IdString;
  readonly battle_number?: number;
  /** One-based casualty ordinal for a henchman group recorded Out of Action more than once. */
  readonly casualty_index?: number;
  /** Stable KB id of the rolled result (e.g. `smashed_hand`). */
  readonly result_id: string;
  /** Volatile display text of the result. */
  readonly result: string;
  /** Typed effects this port understands (see `InjuryEffect`). */
  readonly effects?: readonly InjuryEffect[];
  /** Free-form payload for effects this port does not interpret. */
  readonly extra_effects?: readonly OpenPayload[];
  /** Text of the follow-up roll the outcome chains, if any. */
  readonly follow_up?: string;
}

/** Effects the web port interprets (mirrors desktop `_apply_injury_effects`). */
export type InjuryEffect =
  | { readonly kind: "miss_games"; readonly value: number }
  | { readonly kind: "add_condition"; readonly condition_id: string }
  | { readonly kind: "stat_modifier"; readonly stat: string; readonly value: number }
  | { readonly kind: "lost_eye"; readonly side: "left" | "right" }
  | { readonly kind: "remove_warrior" }
  | { readonly kind: "discard_equipment" }
  | { readonly kind: "grant_experience"; readonly value: number }
  | { readonly kind: "battle_start_check"; readonly check: OpenPayload }
  | { readonly kind: "equipment_limit"; readonly maximum_one_handed_weapons: number }
  | { readonly kind: "follow_up"; readonly type: string; readonly payload?: OpenPayload };

/** Read-model row: one warrior's injury & recovery status. */
export interface InjuryRow {
  readonly warrior_id: IdString;
  readonly name: string;
  readonly kind: string;
  readonly condition: string | null;
  readonly condition_detail: string | null;
  /** Games the warrior still misses (absence blocks battle readiness). */
  readonly games_to_miss: number;
  readonly absence_reason: string | null;
  /** Unresolved injury rolls parked on the pending post-battle. */
  readonly pending_follow_ups: readonly OpenPayload[];
  /** Applied, acknowledged injury history (preserve-in-place payloads). */
  readonly injury_records: readonly OpenPayload[];
  /** True while the warrior is blocked from the next battle. */
  readonly restricted: boolean;
}

/** Full injuries read model for the panel. */
export interface InjuriesOverview {
  readonly warriors: readonly InjuryRow[];
  /** Injury follow-ups across all warriors, in post-battle order. */
  readonly open_rolls: readonly OpenPayload[];
  readonly total_restricted: number;
}

function injuryFollowUps(document: CampaignDocument): readonly OpenPayload[] {
  const pending = pendingPostBattle(document);
  if (pending === null) return [];
  return (pending.pending_follow_ups ?? []).filter(
    (followUp: OpenPayload) => (followUp as { type?: string }).type === "injury_roll",
  );
}

/** Read model for the injuries panel. */
export function injuryOverview(document: CampaignDocument): InjuriesOverview {
  const followUps = injuryFollowUps(document);
  const warriors = document.campaign.warriors.map((warrior: Warrior): InjuryRow => {
    const gamesToMiss = warrior.games_to_miss ?? 0;
    const pending = followUps.filter(
      (followUp) => (followUp as { warrior_id?: string }).warrior_id === warrior.id,
    );
    return {
      warrior_id: warrior.id,
      name: warrior.name,
      kind: warrior.kind,
      condition: warrior.condition ?? null,
      condition_detail: warrior.condition_detail ?? null,
      games_to_miss: gamesToMiss,
      absence_reason: warrior.absence_reason ?? null,
      pending_follow_ups: pending,
      injury_records: warrior.injury_records ?? [],
      restricted: gamesToMiss > 0,
    };
  });
  return {
    warriors,
    open_rolls: followUps,
    total_restricted: warriors.filter((row) => row.restricted).length,
  };
}

/** Apply one rolled outcome to a warrior, immutably. */
export function applyInjuryOutcome(
  document: CampaignDocument,
  input: InjuryOutcomeInput,
): InjuriesWorkflowResult {
  const warrior = document.campaign.warriors.find((w) => w.id === input.warrior_id);
  if (!warrior) {
    return { ok: false, reason: "not_found", message: `Unknown warrior id: ${input.warrior_id}.` };
  }
  const casualtyIndex = input.casualty_index ?? 1;
  if (!Number.isInteger(casualtyIndex) || casualtyIndex < 1) {
    return { ok: false, reason: "invalid_input", message: "casualty_index must be a positive integer." };
  }
  if (input.battle_number !== undefined && (warrior.injury_records ?? []).some((record) => Number(record["battle_number"]) === input.battle_number && Number(record["casualty_index"] ?? 1) === casualtyIndex)) {
    return { ok: false, reason: "conflict", message: `${warrior.name} already has this serious-injury result for this battle.` };
  }
  const effects = [...(input.effects ?? []), ...(input.extra_effects ?? [])];
  let gamesToMiss = warrior.games_to_miss ?? 0;
  let absenceReason = warrior.absence_reason ?? null;
  let condition = warrior.condition ?? null;
  let conditionDetail = warrior.condition_detail ?? null;
  const statModifiers: Record<string, number> = { ...(warrior.stat_modifiers ?? {}) };
  const equipmentLimits: Record<string, number> = { ...(warrior.equipment_limits ?? {}) };
  const lostEyes = [...(warrior.lost_eyes ?? [])];
  const uninterpreted: OpenPayload[] = [];
  const followUps: OpenPayload[] = [];
  let experience=warrior.experience, removeWarrior=false, discardEquipment=false;
  let battleChecks=[...(warrior.battle_start_checks??[])];

  for (const effect of effects) {
    const kind = (effect as { kind?: string }).kind;
    if (kind === "miss_games") {
      const value = Number((effect as { value?: unknown }).value ?? 0);
      if (!Number.isInteger(value) || value <= 0) {
        return {
          ok: false,
          reason: "invalid_input",
          message: `miss_games value must be a positive integer, got ${String(value)}.`,
        };
      }
      gamesToMiss += value;
      absenceReason = input.result;
    } else if (kind === "add_condition") {
      condition = "Injured";
      conditionDetail = String((effect as { condition_id?: unknown }).condition_id ?? "lasting condition");
    } else if (kind === "stat_modifier") {
      const stat = String((effect as { stat?: unknown }).stat ?? "");
      const value = Number((effect as { value?: unknown }).value ?? 0);
      if (!stat || !Number.isInteger(value)) {
        return { ok: false, reason: "invalid_input", message: "stat_modifier needs a stat key and an integer value." };
      }
      statModifiers[stat] = (statModifiers[stat] ?? 0) + value;
    } else if (kind === "lost_eye") {
      lostEyes.push(String((effect as { side?: unknown }).side ?? "left"));
    } else if (kind === "remove_warrior") {
      removeWarrior=true;
    } else if (kind === "discard_equipment") {
      discardEquipment=true;
    } else if (kind === "grant_experience") {
      const value=Number((effect as {value?:unknown}).value??0); if(!Number.isInteger(value)||value<0)return{ok:false,reason:"invalid_input",message:"grant_experience needs a non-negative integer."}; experience+=value;
    } else if (kind === "battle_start_check") {
      const check=(effect as {check?:OpenPayload}).check; if(!check)return{ok:false,reason:"invalid_input",message:"battle_start_check needs KB check data."}; battleChecks=[...battleChecks,check];
    } else if (kind === "equipment_limit") {
      const value=Number((effect as {maximum_one_handed_weapons?:unknown}).maximum_one_handed_weapons); if(!Number.isInteger(value)||value<0)return{ok:false,reason:"invalid_input",message:"equipment_limit needs a non-negative whole-number limit."}; equipmentLimits["maximum_one_handed_weapons"]=Math.min(equipmentLimits["maximum_one_handed_weapons"]??value,value); condition="Injured"; conditionDetail=`Arm wound (max ${value} one-handed weapon(s))`;
    } else if (kind === "follow_up") {
      const item=effect as {type?:unknown;payload?:OpenPayload}; if(typeof item.type!=="string"||!item.type)return{ok:false,reason:"invalid_input",message:"follow_up needs a type."}; followUps.push({id:`${item.type}:${warrior.id}:${input.result_id}:${casualtyIndex}`,step:"injuries",type:item.type,warrior_id:warrior.id,casualty_index:casualtyIndex,result_id:input.result_id,...(item.payload??{})});
    } else {
      // Open-payload policy: preserve what this port does not interpret.
      uninterpreted.push(effect);
    }
  }
  if(input.result_id.includes("blinded-in-one-eye"))followUps.push({id:`eye_injury:${warrior.id}:${input.result_id}:${casualtyIndex}`,step:"injuries",type:"eye_injury",warrior_id:warrior.id,casualty_index:casualtyIndex,result_id:input.result_id});

  const record: OpenPayload = {
    result_id: input.result_id,
    result: input.result,
    effects: [...effects],
    applied_at_step: "injuries",
    ...(input.battle_number !== undefined ? { battle_number: input.battle_number } : {}),
    ...(input.battle_number !== undefined ? { casualty_index: casualtyIndex } : {}),
  };
  const nextWarrior: Warrior = {
    ...warrior,
    ...(gamesToMiss !== (warrior.games_to_miss ?? 0) ? { games_to_miss: gamesToMiss } : {}),
    ...(absenceReason !== null ? { absence_reason: absenceReason } : {}),
    ...(condition !== null ? { condition } : {}),
    ...(conditionDetail !== null ? { condition_detail: conditionDetail } : {}),
    ...(Object.keys(statModifiers).length > 0 ? { stat_modifiers: statModifiers } : {}),
    ...(Object.keys(equipmentLimits).length > 0 ? { equipment_limits: equipmentLimits } : {}),
    ...(lostEyes.length > 0 ? { lost_eyes: lostEyes } : {}),
    ...(experience!==warrior.experience?{experience}:{}),
    ...(battleChecks.length?{battle_start_checks:battleChecks}:{}),
    injury_records: [...(warrior.injury_records ?? []), record],
  };
  const lost=new Map<string,number>(); if((removeWarrior||discardEquipment))for(const item of warrior.equipment)if(item.transferable!==false)lost.set(item.item_id,(lost.get(item.item_id)??0)+item.quantity);
  const inventory=document.campaign.inventory.map((item)=>{const quantity=lost.get(item.id)??0;return quantity?{...item,owned:Math.max(0,item.owned-quantity),equipped:Math.max(0,item.equipped-quantity),stash:Math.max(0,item.stash-quantity)}:item;}).filter((item)=>item.owned>0);
  let campaign = {
    ...document.campaign,
    inventory,
    warriors: removeWarrior?document.campaign.warriors.filter((w)=>w.id!==input.warrior_id):document.campaign.warriors.map((w) => (w.id === input.warrior_id ? {...nextWarrior,equipment:discardEquipment?nextWarrior.equipment.filter((item)=>item.transferable===false):nextWarrior.equipment} : w)),
  };
  let nextDocument: CampaignDocument = withCampaign(document, campaign);

  if(removeWarrior) nextDocument=withCampaign(nextDocument,{...nextDocument.campaign,post_battles:nextDocument.campaign.post_battles.map((post)=>post.battle_number!==input.battle_number?post:{...post,pending_advances:(post.pending_advances??[]).filter((row)=>row["warrior_id"]!==warrior.id||row["committed"]),pending_follow_ups:(post.pending_follow_ups??[]).filter((row)=>row["warrior_id"]!==warrior.id),equipment_obligations:(post.equipment_obligations??[]).filter((row)=>row["warrior_id"]!==warrior.id),searches:Object.fromEntries(Object.entries(post.searches??{}).filter(([id])=>id!==warrior.id)}})});
  if(followUps.length){const pending=pendingPostBattle(nextDocument);if(!pending)return{ok:false,reason:"conflict",message:"There is no pending post-battle for this injury follow-up."};nextDocument=withCampaign(nextDocument,{...nextDocument.campaign,post_battles:nextDocument.campaign.post_battles.map((post)=>post===pending?{...post,pending_follow_ups:[...(post.pending_follow_ups??[]),...followUps]}:post)});}
  if (input.follow_up || uninterpreted.length > 0) {
    const parked = recordFollowUp(nextDocument, {
      warrior_id: input.warrior_id,
      casualty_index: casualtyIndex,
      result_id: input.result_id,
      description: input.follow_up ?? "Resolve the uninterpreted injury effect.",
      ...(uninterpreted.length > 0 ? { payload: { extra_effects: uninterpreted } } : {}),
    });
    if (!parked.ok) return parked;
    nextDocument = parked.document;
  }
  return { ok: true, document: nextDocument };
}

/** Park an unresolved injury roll on the pending post-battle (resumable). */
export function recordFollowUp(
  document: CampaignDocument,
  input: {
    readonly warrior_id: IdString;
    readonly casualty_index?: number;
    readonly result_id: string;
    readonly description: string;
    readonly payload?: OpenPayload;
  },
): InjuriesWorkflowResult {
  const pending = pendingPostBattle(document);
  if (pending === null) {
    return {
      ok: false,
      reason: "conflict",
      message: "There is no pending post-battle to park the injury follow-up on.",
    };
  }
  const followUp: OpenPayload = {
    id: `injury:${input.warrior_id}:${input.result_id}:${input.casualty_index ?? 1}`,
    step: "injuries",
    type: "injury_roll",
    warrior_id: input.warrior_id,
    casualty_index: input.casualty_index ?? 1,
    result_id: input.result_id,
    description: input.description,
    ...(input.payload ? { payload: input.payload } : {}),
  };
  const campaign = {
    ...document.campaign,
    post_battles: document.campaign.post_battles.map((post) =>
      post.battle_number === pending.battle_number
        ? { ...post, pending_follow_ups: [...(post.pending_follow_ups ?? []), followUp] }
        : post,
    ),
  };
  return { ok: true, document: withCampaign(document, campaign) };
}

/** Resolve a parked follow-up: acknowledge it and apply its outcome. */
export function resolveFollowUp(
  document: CampaignDocument,
  input: { readonly follow_up_id: string; readonly outcome: InjuryOutcomeInput },
): InjuriesWorkflowResult {
  const pending = pendingPostBattle(document);
  if (pending === null) {
    return { ok: false, reason: "conflict", message: "There is no pending post-battle sequence." };
  }
  const remaining = (pending.pending_follow_ups ?? []).filter(
    (followUp: OpenPayload) => (followUp as { id?: string }).id !== input.follow_up_id,
  );
  if (remaining.length === (pending.pending_follow_ups ?? []).length) {
    return { ok: false, reason: "not_found", message: `Unknown follow-up: ${input.follow_up_id}.` };
  }
  const applied = applyInjuryOutcome(document, input.outcome);
  if (!applied.ok) return applied;
  const campaign = {
    ...applied.document.campaign,
    post_battles: applied.document.campaign.post_battles.map((post) =>
      post.battle_number === pending.battle_number ? { ...post, pending_follow_ups: remaining } : post,
    ),
  };
  return { ok: true, document: withCampaign(applied.document, campaign) };
}

/** Recovery: one missed game served; clears the absence (and condition at 0). */
export function recover(
  document: CampaignDocument,
  warriorId: IdString,
): InjuriesWorkflowResult {
  const warrior = document.campaign.warriors.find((w) => w.id === warriorId);
  if (!warrior) {
    return { ok: false, reason: "not_found", message: `Unknown warrior id: ${warriorId}.` };
  }
  const gamesToMiss = warrior.games_to_miss ?? 0;
  if (gamesToMiss === 0) {
    return {
      ok: false,
      reason: "invalid_input",
      message: `${warrior.name} is not missing any games.`,
    };
  }
  const next = gamesToMiss - 1;
  const fullyRecovered = next === 0;
  const campaign = {
    ...document.campaign,
    warriors: document.campaign.warriors.map((w) => {
      if (w.id !== warriorId) return w;
      if (fullyRecovered) {
        // The contract has no nullable absence: drop the keys entirely when the
        // absence ends (JSON round-trip: absent key == not absent).
        const { absence_reason: _dropped, games_to_miss: _games, ...rest } = w;
        return {
          ...rest,
          ...(w.condition === "Injured" ? { condition: null, condition_detail: null } : {}),
        };
      }
      return { ...w, games_to_miss: next };
    }),
  };
  return { ok: true, document: withCampaign(document, campaign) };
}

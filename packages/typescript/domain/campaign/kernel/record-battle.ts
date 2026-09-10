/**
 * P3.5: record a battle — the pure port of the Python
 * `domain/battle_service.record_battle` core (validation, snapshot numbers,
 * battle node, pending post-battle with hireling-upkeep follow-ups).
 *
 * Deliberately narrower than the desktop path: scenario loot application and
 * pre-battle availability arrive with P6.4/P6.5. Everything the port surface
 * (`RecordBattleInput`) expresses is implemented here.
 *
 * Purity: no React, no DOM, no filesystem. Dates use ISO (locale-volatile
 * display formatting belongs to the UI).
 */

import type { IdString, OpenPayload } from "../index";
import type { KnowledgeReader } from "./ports";
import type {
  Battle,
  Campaign,
  CampaignDocument,
  PostBattle,
  RecordBattleInput,
  UseCaseResult,
} from "./usecases";
import { rejected } from "./rejections";
import {
  cloneDocument,
  currentState,
  findWarrior,
  memberCount,
  nextBattleNumber,
  pendingPostBattle,
  rating,
  withCampaign,
} from "./document";

/** Normalizes a result input to the contract's canonical value. */
export function normalizeResult(result: string): "win" | "loss" | "draw" | null {
  const key = result.trim().toLowerCase();
  if (key === "win" || key === "victory") return "win";
  if (key === "loss" || key === "defeat") return "loss";
  if (key === "draw") return "draw";
  return null;
}

/**
 * Records a battle: validates the table facts, snapshots the warband numbers,
 * appends the battle node and opens its pending post-battle with
 * hireling-upkeep follow-ups.
 */
export function recordBattle(
  document: CampaignDocument,
  input: RecordBattleInput,
  knowledge: KnowledgeReader,
): UseCaseResult {
  const { campaign } = document;
  if (campaign.configuration.is_draft) {
    return rejected(
      "not_permitted_in_draft",
      "Commit the initial warband before recording battles.",
    );
  }
  if (pendingPostBattle(document) !== null) {
    const pending = pendingPostBattle(document);
    return rejected(
      "conflict",
      `Post-battle #${pending?.battle_number} is still pending; commit it before recording the next battle.`,
    );
  }
  const scenario = knowledge.queryKnowledge({
    id: { kind: "scenario_id", value: input.scenario },
  });
  if (!scenario.ok) {
    return rejected("not_found", `Unknown scenario: ${input.scenario}.`);
  }
  const result = normalizeResult(input.result);
  if (result === null) {
    return rejected("invalid_input", "Result must be win, loss or draw.");
  }
  if (input.gold_delta < 0 || input.wyrdstone < 0 || input.xp_delta < 0 || input.casualties < 0) {
    return rejected("invalid_input", "Battle numbers must be non-negative.");
  }
  const outOfAction = input.out_of_action_ids ?? [];
  const submittedIds = new Set<IdString>(outOfAction);
  for (const id of submittedIds) {
    const warrior = findWarrior(document, id);
    if (!warrior) {
      return rejected("not_found", `Unknown warrior id in battle results: ${id}.`);
    }
    if (warrior.games_to_miss && warrior.games_to_miss > 0) {
      return rejected(
        "not_available",
        `Unavailable warriors cannot receive battle results: ${warrior.name}.`,
      );
    }
  }

  const number = nextBattleNumber(document);
  const base = currentState(document);
  const baseRating = base?.rating ?? rating(campaign.warriors);
  const baseModels = base?.models ?? memberCount(campaign.warriors);
  const date = new Date().toISOString().slice(0, 10);

  const casualties = outOfAction.length;
  const battle: Battle = {
    number,
    date,
    scenario: input.scenario,
    opponent: input.opponent,
    ...(input.opponent_band_id ? { opponent_band_id: input.opponent_band_id } : {}),
    result,
    gold_delta: Math.trunc(input.gold_delta),
    wyrdstone: Math.max(0, Math.trunc(input.wyrdstone)),
    xp_delta: Math.max(0, Math.trunc(input.xp_delta)),
    casualties,
    advances: 0,
    rating_before: baseRating,
    rating_after: baseRating,
    models_before: baseModels,
    models_after: baseModels,
    ...(input.xp_awards ? { xp_awards: input.xp_awards } : {}),
    ...(input.scenario_results ? { scenario_results: input.scenario_results } : {}),
    ...(input.notes ? { notes: input.notes } : {}),
    out_of_action_ids: [...outOfAction],
    ...(input.participants
      ? {
          participants: input.participants.map((id) => {
            const warrior = findWarrior(document, id);
            return {
              id,
              name: warrior?.name ?? id,
              kind: warrior?.kind ?? "hero",
              quantity: warrior?.quantity ?? 1,
              profile_name: warrior?.profile_name ?? id,
              condition: warrior?.condition ?? "",
            } as OpenPayload;
          }),
        }
      : {}),
  };

  const postBattle: PostBattle = {
    battle_number: number,
    complete: false,
    active_step: 0,
    completed_steps: [],
    review_open: false,
    // Desktop `record_battle` seeds the pending post-battle with the
    // battle's resource deltas so the resolution steps start from them.
    gold_delta: Math.max(0, Math.trunc(input.gold_delta)),
    wyrdstone_delta: Math.max(0, Math.trunc(input.wyrdstone)),
    // Hireling upkeep follow-ups (Python `record_battle` tail).
    ...(campaign.warriors.some((w) => w.kind === "hireling" && w.upkeep_resources?.length)
      ? {
          pending_follow_ups: campaign.warriors
            .filter((w) => w.kind === "hireling" && w.upkeep_resources?.length)
            .map((w) => ({
              id: `upkeep:${number}:${w.id}`,
              step: 6,
              type: "hireling_upkeep",
              warrior_id: w.id,
              costs: w.upkeep_resources?.map(([key, value]) => [key, value] as [string, number]),
              description: `Pay ${w.name}'s upkeep or dismiss the Hired Sword.`,
            })),
        }
      : {}),
  };

  const nextCampaign: Campaign = {
    ...campaign,
    battles: [...campaign.battles, battle],
    post_battles: [...campaign.post_battles, postBattle],
  };
  return { ok: true, state: withCampaign(document, nextCampaign) };
}

/**
 * The snapshot helpers a full post-battle engine (P6.5) will need; kept here
 * so the mutable-state discipline stays in one module.
 */
export function snapshotForNextState(document: CampaignDocument): CampaignDocument {
  return cloneDocument(document);
}

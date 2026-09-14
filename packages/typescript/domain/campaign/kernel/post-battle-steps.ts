/**
 * P3.5: post-battle step navigation — the pure port of the Python
 * `domain/timeline_service` step rules, narrowed to what the frozen port
 * surface expresses (`resolvePostBattleStep`).
 *
 * The browser exposes eight user actions for the canonical post-battle flow;
 * the knowledge base remains the normative source for the underlying ten
 * steps. This module owns navigation discipline: steps resolve in order, the
 * active step only moves forward, and the sequence completes with review.
 *
 * Purity: no React, no DOM, no filesystem.
 */

import type { Campaign, CampaignDocument, OpenPayloadInput, UseCaseResult } from "./usecases";
import { rejected } from "./rejections";
import { pendingPostBattle, withCampaign } from "./document";

/** Number of user-facing actions in the post-battle navigator. */
export const POST_BATTLE_STEP_COUNT = 8;

/**
 * Resolves the active post-battle step and advances to the next one. Step
 * input payloads are preserved in `step_state[step]` verbatim (contract
 * open-payload policy); the engine blocks will read them back.
 */
export function resolvePostBattleStep(
  document: CampaignDocument,
  battleNumber: number,
  input: OpenPayloadInput,
): UseCaseResult {
  const post = pendingPostBattle(document);
  if (post === null) {
    return rejected("not_found", "There is no pending post-battle sequence.");
  }
  if (post.battle_number !== battleNumber) {
    return rejected(
      "conflict",
      `Post-battle #${battleNumber} is not the pending sequence (pending: #${post.battle_number}).`,
    );
  }
  if (post.active_step >= POST_BATTLE_STEP_COUNT) {
    return rejected("invalid_input", "The post-battle sequence is already finished.");
  }
  const step = post.active_step;
  if(step===0){
    const battle=document.campaign.battles.find((row)=>row.number===battleNumber),resolved=(post.step_state?.["injuries"]??{}) as Record<string,unknown>,seen=new Map<string,number>();
    const missing=(battle?.out_of_action_ids??[]).some((id)=>{const casualty=(seen.get(id)??0)+1;seen.set(id,casualty);return !resolved[`${id}:${casualty}`];});
    const injuryFollowUp=(post.pending_follow_ups??[]).some((row)=>row["step"]===0||row["step"]==="injuries"||["injury_roll","injury_followup","eye_injury","prisoner","relationship","encounter"].includes(String(row["type"]??"")));
    if(missing||injuryFollowUp)return rejected("prerequisite_missing","Resolve every serious-injury roll and follow-up before continuing.");
  }
  const stepState = { ...(post.step_state ?? {}) };
  if (Object.keys(input).length > 0) {
    stepState[String(step)] = input;
  }
  const completed = [...post.completed_steps, step].sort((a, b) => a - b);
  const nextActive = step + 1;
  const complete = nextActive >= POST_BATTLE_STEP_COUNT;
  const nextPost = {
    ...post,
    active_step: nextActive,
    completed_steps: completed,
    complete,
    review_open: complete,
    step_state: stepState,
  };
  const campaign: Campaign = {
    ...document.campaign,
    post_battles: document.campaign.post_battles.map((p) =>
      p.battle_number === battleNumber ? nextPost : p,
    ),
  };
  return { ok: true, state: withCampaign(document, campaign) };
}

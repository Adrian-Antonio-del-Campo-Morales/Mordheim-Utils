import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { explorationDiceCount } from "@app/campaign/features/exploration/exploration-workflow";
import type { OpenPayload } from "@domain/campaign/index";
import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { DiceResolver } from "../dice/DiceResolver";

export function ExplorationPanel({document,knowledge}:{readonly document:CampaignDocument;readonly knowledge:ArtefactKnowledgeReader}) {
  const app=useCampaignApp(); const post=document.campaign.post_battles.find((row)=>!row.complete); if(!post)return null;
  const advances=(post.pending_advances??[]).some((row)=>!row["committed"]); const state=post.step_state?.["exploration"] as OpenPayload|undefined; const count=explorationDiceCount(document,knowledge);
  return <section aria-label="Exploration"><h3>03 · Exploration</h3>{state?.["resolved"] ? <><p role="status">Exploration resolved: {String(state["dice_count"])} dice · total {String(state["total"])} · {String(state["shards"])} wyrdstone.</p>{state["special"]&&<p>Special result: {String(state["special"])}. Complete its pending choices below.</p>}</> : !post.experience_applied||advances ? <p role="status">Resolve experience and all advances first.</p> : count===0 ? <button className="primary" onClick={()=>void app.runAction("applyExploration",{dice:[]})}>Resolve exploration without dice</button> : <><p>{count}D6: one die per surviving Hero, plus one for winning, capped by KB.</p><DiceResolver count={count} sides={6} label="Exploration roll" onResolve={(dice)=>void app.runAction("applyExploration",{dice})}/></>}</section>;
}

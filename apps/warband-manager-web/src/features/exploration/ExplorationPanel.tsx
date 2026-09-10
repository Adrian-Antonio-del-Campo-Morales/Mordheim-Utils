import { useState } from "react";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { explorationDiceCount } from "@app/campaign/features/exploration/exploration-workflow";
import type { OpenPayload } from "@domain/campaign/index";
import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { DiceResolver } from "../dice/DiceResolver";

export function ExplorationPanel({document,knowledge}:{readonly document:CampaignDocument;readonly knowledge:ArtefactKnowledgeReader}) {
  const app=useCampaignApp(); const [warriorIds,setWarriorIds]=useState<string[]>([]); const post=document.campaign.post_battles.find((row)=>!row.complete); if(!post)return null;
  const advances=(post.pending_advances??[]).some((row)=>!row["committed"]); const state=post.step_state?.["exploration"] as OpenPayload|undefined; const count=explorationDiceCount(document,knowledge); const followup=post.pending_follow_ups?.find((row)=>row["type"]==="exploration_followup"); const pending=followup?.["pending"] as OpenPayload|undefined;
  return <section aria-label="Exploration"><h3>03 · Exploration</h3>{state?.["resolved"] ? <><p role="status">Exploration resolved: {String(state["dice_count"])} dice · total {String(state["total"])} · {String(state["shards"])} wyrdstone.</p>{state["special"]&&<p>Special result: {String(state["special"])}.</p>}</> : !post.experience_applied||advances ? <p role="status">Resolve experience and all advances first.</p> : count===0 ? <button className="primary" onClick={()=>void app.runAction("applyExploration",{dice:[]})}>Resolve exploration without dice</button> : <><p>{count}D6: one die per surviving Hero, plus one for winning, capped by KB.</p><DiceResolver count={count} sides={6} label="Exploration roll" onResolve={(dice)=>void app.runAction("applyExploration",{dice})}/></>}
    {followup&&!pending&&<button className="primary" onClick={()=>void app.runAction("continueExploration",{})}>Start special result</button>}
    {pending?.["kind"]==="roll"&&<DiceResolver count={Number(pending["dice_count"]??1)} sides={Number(pending["dice_sides"]??6)} label={String(pending["label"]??"Follow-up roll")} onResolve={(dice)=>void app.runAction("continueExploration",{roll:dice.reduce((sum,item)=>sum+item,0)})}/>}
    {pending?.["kind"]==="choose_hero"&&<label>{String(pending["label"]??"Choose a Hero")}<select defaultValue="" onChange={(event)=>{if(event.target.value)void app.runAction("continueExploration",{hero_id:event.target.value});}}><option value="" disabled>Select…</option>{document.campaign.warriors.filter((row)=>row.kind==="hero").map((row)=><option key={row.id} value={row.id}>{row.name}</option>)}</select></label>}
    {pending?.["kind"]==="choose_option"&&<div><p>{String(pending["label"]??"Choose an outcome")}</p>{((pending["options"]??[]) as OpenPayload[]).map((option)=><button key={String(option["id"])} onClick={()=>void app.runAction("continueExploration",{option_id:option["id"]})}>{String(option["label"]??option["id"])}</button>)}</div>}
    {pending?.["kind"]==="choose_warriors"&&<fieldset><legend>{String(pending["label"]??"Choose warriors")}</legend>{((pending["options"]??[]) as OpenPayload[]).map((option)=>{const id=String(option["id"]),checked=warriorIds.includes(id),maximum=Number(pending["maximum"]??1);return <label key={id}><input type="checkbox" checked={checked} disabled={!checked&&warriorIds.length>=maximum} onChange={()=>setWarriorIds((current)=>checked?current.filter((value)=>value!==id):[...current,id])}/>{String(option["label"]??id)}</label>;})}<button type="button" onClick={()=>{void app.runAction("continueExploration",{warrior_ids:warriorIds});setWarriorIds([]);}}>Confirm</button></fieldset>}
    {pending?.["kind"]==="external"&&<button onClick={()=>void app.runAction("continueExploration",{confirm_external:true})}>{String(pending["label"]??"Confirm table-side resolution")}</button>}
    {followup&&Array.isArray(followup["messages"])&&<ul>{(followup["messages"] as string[]).map((message)=><li key={message}>{message}</li>)}</ul>}
  </section>;
}

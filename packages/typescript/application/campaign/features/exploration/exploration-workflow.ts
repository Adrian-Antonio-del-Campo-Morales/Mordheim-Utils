import type { CampaignDocument, KnowledgeReader, OpenPayload } from "../../../../domain/campaign/index";
import { withCampaign } from "../../../../domain/campaign/kernel/document";

interface CatalogueReader extends KnowledgeReader { campaignSection?(section:string):Readonly<Record<string,unknown>> }
type Result={ok:true;document:CampaignDocument;summary:ExplorationSummary}|{ok:false;message:string};
export interface ExplorationSummary { readonly dice_count:number; readonly total:number; readonly shards:number; readonly special:string|null }

function catalogue(reader:CatalogueReader) {
  const document=reader.campaignSection?.("exploration-and-income");
  return (document?.["exploration"]??{}) as Readonly<Record<string,unknown>>;
}
export function eligibleExplorationHeroes(document:CampaignDocument):number {
  const post=document.campaign.post_battles.find((row)=>!row.complete); const battle=post&&document.campaign.battles.find((row)=>row.number===post.battle_number); if(!battle)return 0;
  let heroes=new Set(document.campaign.warriors.filter((row)=>row.kind==="hero").map((row)=>row.id));
  for(const row of battle.absentees??[]) heroes.delete(String(row["id"]??""));
  if(battle.participants?.length) { const participants=new Set(battle.participants.map((row)=>String(row["id"]??""))); heroes=new Set([...heroes].filter((id)=>participants.has(id))); }
  if(battle.out_of_action_ids) for(const id of battle.out_of_action_ids) heroes.delete(id);
  return heroes.size;
}
export function explorationDiceCount(document:CampaignDocument,reader:CatalogueReader):number {
  const post=document.campaign.post_battles.find((row)=>!row.complete); const battle=post&&document.campaign.battles.find((row)=>row.number===post.battle_number); if(!battle)return 0;
  const exploration=catalogue(reader); let count=0;
  for(const row of (exploration["dice_allocation"]??[]) as readonly Readonly<Record<string,unknown>>[]) {
    if(row["eligible_warrior"]==="hero"&&row["condition"]==="survived_battle") count+=Number(row["dice"]??0)*eligibleExplorationHeroes(document);
    if(row["eligible_warrior"]==="warband"&&row["condition"]==="warband_won_battle"&&battle.result==="win") count+=Number(row["dice"]??0);
  }
  return Math.min(count,Number(exploration["max_dice"]??6));
}
function matchingResult(exploration:Readonly<Record<string,unknown>>,dice:readonly number[]) {
  const counts=new Map<number,number>(); for(const die of dice)counts.set(die,(counts.get(die)??0)+1);
  const match=[...counts].filter(([,count])=>count>=2).sort((a,b)=>b[1]-a[1]||b[0]-a[0])[0]; if(!match)return null;
  const pattern=Array.from({length:match[1]},()=>match[0]).join(",");
  return ((exploration["results"]??[]) as readonly Readonly<Record<string,unknown>>[]).find((row)=>row["dice_pattern"]===pattern)??null;
}
export function applyExploration(document:CampaignDocument,reader:CatalogueReader,dice:readonly number[]):Result {
  const post=document.campaign.post_battles.find((row)=>!row.complete); if(!post)return{ok:false,message:"No pending post-battle exploration."};
  if(!post.experience_applied||(post.pending_advances??[]).some((row)=>!row["committed"]))return{ok:false,message:"Resolve experience and every advance before exploration."};
  if((post.step_state?.["exploration"] as OpenPayload|undefined)?.["resolved"])return{ok:false,message:"Exploration has already been resolved."};
  const required=explorationDiceCount(document,reader); if(dice.length!==required||dice.some((die)=>!Number.isInteger(die)||die<1||die>6))return{ok:false,message:`Exploration requires exactly ${required} valid D6 results.`};
  const exploration=catalogue(reader); const total=dice.reduce((sum,die)=>sum+die,0);
  const cell=((exploration["shards_chart"] as Readonly<Record<string,unknown>>)?.["cells"]??[]) as readonly Readonly<Record<string,unknown>>[];
  const shardRow=cell.find((row)=>{const bounds=((row["when"] as Readonly<Record<string,unknown>>)?.["dice_total"]??{}) as Readonly<Record<string,unknown>>;return total>=Number(bounds["min"]??0)&&(bounds["max"]==null||total<=Number(bounds["max"]));});
  const shards=Number(shardRow?.["shards"]??0); const special=matchingResult(exploration,dice); const followups=[...(post.pending_follow_ups??[])];
  if(special)followups.push({type:"exploration_followup",step:3,result_id:String(special["id"]??""),description:`${String(special["outcome"]??"")} special result: resolve the KB follow-up effects.`,queue:special["follow_up"]?[special["follow_up"]]:[],messages:[],hero_id:null});
  const summary={dice_count:dice.length,total,shards,special:special?String(special["outcome"]??""):null};
  const changed={...post,wyrdstone_delta:(post.wyrdstone_delta??0)+shards,pending_follow_ups:followups,step_state:{...(post.step_state??{}),exploration:{resolved:true,dice:[...dice],...summary}},event_log:[...(post.event_log??[]),{step:3,type:"exploration",description:`${shards} wyrdstone shard(s) found.`},...(special?[{step:3,type:"exploration_special",description:String(special["outcome"]??""),result_id:String(special["id"]??"")}]:[])]};
  return{ok:true,summary,document:withCampaign(document,{...document.campaign,post_battles:document.campaign.post_battles.map((row)=>row===post?changed:row)})};
}

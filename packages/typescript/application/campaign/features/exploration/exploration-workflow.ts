import type { CampaignDocument, KnowledgeReader, OpenPayload } from "../../../../domain/campaign/index";
import { withCampaign } from "../../../../domain/campaign/kernel/document";

interface CatalogueReader extends KnowledgeReader { campaignSection?(section:string):Readonly<Record<string,unknown>> }
type Result={ok:true;document:CampaignDocument;summary:ExplorationSummary}|{ok:false;message:string};
type FollowUpResult={ok:true;document:CampaignDocument}|{ok:false;message:string};
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

function pendingFollowup(document:CampaignDocument) {
  const post=document.campaign.post_battles.find((row)=>!row.complete); const followup=post?.pending_follow_ups?.find((row)=>row["type"]==="exploration_followup"); return {post,followup};
}
function processQueue(document:CampaignDocument,reader:CatalogueReader,post:NonNullable<ReturnType<typeof pendingFollowup>["post"]>,followup:OpenPayload):CampaignDocument {
  const queue=[...((followup["queue"]??[]) as OpenPayload[])]; const messages=[...((followup["messages"]??[]) as string[])]; let gold=post.gold_delta??0; let shards=post.wyrdstone_delta??0; let inventory=[...document.campaign.inventory]; let current={...followup};
  while(queue.length) {
    const node=queue.shift()!; const kind=String(node["type"]??"");
    if(kind==="sequence") { queue.unshift(...((node["steps"]??[]) as OpenPayload[])); continue; }
    if(kind==="conditional") { const cases=(node["cases"]??[]) as OpenPayload[]; const selected=cases.find((item)=>{const when=(item["when"]??{}) as OpenPayload;const actual=when["field"]==="context.band_id"?document.campaign.identity.band_id:Number(current["last_roll"]??0);return when["operator"]==="equals"?String(actual)===String(when["value"]):when["operator"]==="in"&&((when["value"]??[]) as unknown[]).map(String).includes(String(actual));}); queue.unshift(...(((selected?.["then"]??node["default"]??[]) as OpenPayload[]))); continue; }
    if(kind==="choose_one"||kind==="choose_option") { current={...current,queue,messages,pending:kind==="choose_one"?{kind:"choose_hero",label:String(node["bind"]??"Choose a Hero")}:{kind:"choose_option",label:String(node["label"]??"Choose an outcome"),options:node["options"]??[]}}; break; }
    if(kind==="characteristic_test"||kind==="roll_table") { const dice=(node["dice"]??{}) as OpenPayload; current={...current,queue,messages,pending:{kind:"roll",label:kind==="characteristic_test"?`${String(node["characteristic"])} test`:"Follow-up roll",dice_count:Number(dice["count"]??1),dice_sides:Number(dice["sides"]??6),spec:node}}; break; }
    if(kind==="grant"||kind==="reward.grant") {
      const resources=(node["resources"]??{}) as Record<string,unknown>; let deferred=false;
      for(const [resource,raw] of Object.entries(resources)) { const spec=(typeof raw==="object"&&raw?raw:{kind:"fixed",value:raw}) as OpenPayload; if(spec["kind"]!=="fixed") { const dice=(spec["dice"]??{}) as OpenPayload; current={...current,queue,messages,pending:{kind:"roll",label:`${resource} reward`,dice_count:Number(dice["count"]??1),dice_sides:Number(dice["sides"]??6),spec:{type:"resource_roll",resource,multiplier:Number(spec["multiplier"]??1),offset:Number(spec["offset"]??0)}}}; deferred=true; break; } const value=Number(spec["value"]??0); if(resource==="gold_crowns")gold+=value; else if(resource==="wyrdstone_fragments")shards+=value; messages.push(`+${value} ${resource}`); }
      if(deferred)break;
      for(const item of (node["items"]??[]) as OpenPayload[]) { const quantity=(item["quantity"]??{}) as OpenPayload; if(quantity["kind"]!=="fixed") { messages.push(`Pending table-side item roll: ${String(item["item_id"])}`); continue; } const id=String(item["item_id"]); const amount=Number(quantity["value"]??1); const known=reader.queryKnowledge({id:{kind:"item_id",value:id}}); const name=known.ok?String(known.record.names["en"]??id):id; const existing=inventory.find((row)=>row.id===id); inventory=existing?inventory.map((row)=>row.id===id?{...row,owned:row.owned+amount,stash:row.stash+amount}:row):[...inventory,{id,name,category:String(known.ok?known.record.data["kind"]??"Reward":"Reward"),owned:amount,equipped:0,stash:amount,value:0}]; messages.push(`+${amount} ${name}`); }
      continue;
    }
    current={...current,queue,messages:[...messages,`Pending unsupported desktop follow-up: ${kind}`],pending:{kind:"external",label:`Resolve ${kind} at the table`}}; break;
  }
  const finished=!queue.length&&!current["pending"];
  const followups=finished?(post.pending_follow_ups??[]).filter((row)=>row!==followup):(post.pending_follow_ups??[]).map((row)=>row===followup?{...current,queue,messages}:row);
  const changedPost={...post,gold_delta:gold,wyrdstone_delta:shards,pending_follow_ups:followups,event_log:finished?[...(post.event_log??[]),{step:3,type:"exploration_followup",description:messages.join("; ")||"follow-up complete"}]:post.event_log};
  return withCampaign(document,{...document.campaign,inventory,post_battles:document.campaign.post_battles.map((row)=>row===post?changedPost:row)});
}
export function continueExploration(document:CampaignDocument,reader:CatalogueReader,input:{roll?:number;hero_id?:string;option_id?:string;confirm_external?:boolean}):FollowUpResult {
  const {post,followup}=pendingFollowup(document); if(!post||!followup)return{ok:false,message:"No exploration follow-up is pending."}; let current={...followup}; const pending=(current["pending"]??null) as OpenPayload|null;
  if(!pending)return{ok:true,document:processQueue(document,reader,post,current)};
  const queue=[...((current["queue"]??[]) as OpenPayload[])]; const messages=[...((current["messages"]??[]) as string[])];
  if(pending["kind"]==="choose_hero") { if(!document.campaign.warriors.some((row)=>row.id===input.hero_id&&row.kind==="hero"))return{ok:false,message:"Choose a Hero still present in the warband."}; current={...current,hero_id:input.hero_id}; const continuation=pending["continuation"]; if(continuation)queue.unshift(continuation as OpenPayload); }
  else if(pending["kind"]==="choose_option") { const option=((pending["options"]??[]) as OpenPayload[]).find((row)=>String(row["id"])===input.option_id); if(!option)return{ok:false,message:"Choose one of the available outcomes."}; messages.push(String(option["label"]??input.option_id)); queue.unshift(...((option["then"]??[]) as OpenPayload[])); }
  else if(pending["kind"]==="roll") { const count=Number(pending["dice_count"]??1),sides=Number(pending["dice_sides"]??6),roll=input.roll; if(!Number.isInteger(roll)||Number(roll)<count||Number(roll)>count*sides)return{ok:false,message:`Roll must be between ${count} and ${count*sides}.`}; const spec=(pending["spec"]??{}) as OpenPayload; current={...current,last_roll:roll}; if(spec["type"]==="resource_roll")queue.unshift({type:"grant",resources:{[String(spec["resource"])]:{kind:"fixed",value:Number(roll)*Number(spec["multiplier"]??1)+Number(spec["offset"]??0)}}}); else if(spec["type"]==="roll_table") { const branch=((spec["branches"]??[]) as OpenPayload[]).find((row)=>{const when=(row["when"]??{}) as OpenPayload;return Number(roll)>=Number(when["min"]??0)&&(when["max"]==null||Number(roll)<=Number(when["max"]));}); queue.unshift(...((branch?.["then"]??spec["default"]??[]) as OpenPayload[])); } else return{ok:false,message:"Characteristic-test follow-up is not connected yet."}; }
  else if(pending["kind"]==="external"&&input.confirm_external) messages.push(String(pending["label"])); else return{ok:false,message:"Complete the pending exploration choice."};
  current={...current,queue,messages}; delete current["pending"];
  const staged=withCampaign(document,{...document.campaign,post_battles:document.campaign.post_battles.map((row)=>row===post?{...post,pending_follow_ups:(post.pending_follow_ups??[]).map((item)=>item===followup?current:item)}:row)});
  const stagedContext=pendingFollowup(staged); return{ok:true,document:processQueue(staged,reader,stagedContext.post!,stagedContext.followup!)};
}

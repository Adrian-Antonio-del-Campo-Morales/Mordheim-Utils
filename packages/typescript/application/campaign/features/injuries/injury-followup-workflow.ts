import type { CampaignDocument, KnowledgeReader, OpenPayload } from "../../../../domain/campaign/index";
import { withCampaign } from "../../../../domain/campaign/kernel/document";
import { applyInjuryOutcome, type InjuryEffect } from "./injuries-workflow";

type Reader=KnowledgeReader&{list?(kind:string):readonly Readonly<Record<string,unknown>>[]};
type Result={ok:true;document:CampaignDocument}|{ok:false;message:string};
function range(value:string,roll:number){const [low,high]=value.split("-").map(Number);return roll>=low&&roll<=(Number.isFinite(high)?high:low);}
function stat(value:unknown){return({movement:"M",weapon_skill:"WS",ballistic_skill:"BS",strength:"S",toughness:"T",wounds:"W",initiative:"I",attacks:"A",leadership:"Ld"} as Record<string,string>)[String(value)]??String(value);}

export function injuryEffects(row:Readonly<Record<string,unknown>>):InjuryEffect[]{
  const mapped=(Array.isArray(row["effects"])?row["effects"]:[]).map((value):InjuryEffect=>{const effect=value as OpenPayload,type=String(effect["type"]??"");
    if(type==="warrior.miss_games"&&typeof effect["games"]==="object"){const games=effect["games"] as OpenPayload;if(games["kind"]==="fixed"||games["value"]!==undefined)return{kind:"miss_games",value:Number(games["value"]??1)};return{kind:"follow_up",type:"injury_roll",payload:{resolution_phase:"effect_roll",dice:games["dice"],effect_kind:"miss_games"}};}
    if(type==="warrior.characteristic_modifier")return{kind:"stat_modifier",stat:stat(effect["characteristic"]),value:Number(effect["modifier"])};
    if(type==="warrior.add_condition")return{kind:"add_condition",condition_id:String(effect["condition_id"])};
    if(type==="warrior.equipment_limit")return{kind:"equipment_limit",maximum_one_handed_weapons:Number(effect["maximum_one_handed_weapons"])};
    if(type==="roster.remove_warrior")return{kind:"remove_warrior"};
    if(type==="equipment.disposition")return{kind:"discard_equipment"};
    if(type==="warrior.battle_start_check")return{kind:"battle_start_check",check:effect};
    if(type==="prisoner.create")return{kind:"follow_up",type:"prisoner"};
    if(type==="relationship.add_hatred")return{kind:"follow_up",type:"relationship",payload:{target_selector:effect["target_selector"]}};
    if(type==="encounter.trigger")return{kind:"follow_up",type:"encounter",payload:{encounter_id:effect["encounter_id"]}};
    if(type==="reward.grant"){const resources=effect["resources"] as OpenPayload|undefined,experience=resources?.["experience"] as OpenPayload|undefined;if(experience?.["kind"]==="fixed")return{kind:"grant_experience",value:Number(experience["value"]??0)};}
    return{kind:"follow_up",type:type||"uninterpreted",payload:effect};
  });
  const resolution=row["resolution"];
  if(resolution&&typeof resolution==="object")mapped.push({kind:"follow_up",type:"injury_roll",payload:{resolution_phase:(resolution as OpenPayload)["type"]==="repeat_table"?"repeat_count":"subtable"}});
  return mapped;
}

function source(reader:KnowledgeReader,follow:OpenPayload){return(reader as Reader).list?.("injury")?.find((row)=>row["id"]===follow["result_id"]);}
export function injuryFollowUpDice(reader:KnowledgeReader,follow:OpenPayload):readonly [number,number]|null{
  if(follow["resolution_phase"]==="repeat_result")return[2,6];
  const direct=follow["dice"] as OpenPayload|undefined,resolution=source(reader,follow)?.["resolution"] as OpenPayload|undefined,dice=direct??resolution?.["dice"] as OpenPayload|undefined;
  if(!dice)return null;const count=Number(dice["count"]??1),sides=Number(dice["sides"]??6);return Number.isInteger(count)&&Number.isInteger(sides)&&count>0&&sides>1?[count,sides]:null;
}
function valid(roll:number,[count,sides]:readonly[number,number]){if(!Number.isInteger(roll))return false;if(count===2&&sides===6){const tens=Math.trunc(roll/10),ones=roll%10;return tens>=1&&tens<=6&&ones>=1&&ones<=6;}return roll>=count&&roll<=count*sides;}
function replace(document:CampaignDocument,post:CampaignDocument["campaign"]["post_battles"][number],follow:OpenPayload,replacements:readonly OpenPayload[],description:string){const changed={...post,pending_follow_ups:(post.pending_follow_ups??[]).flatMap((row)=>row["id"]===follow["id"]?[...replacements]:[row]),event_log:[...(post.event_log??[]),{step:0,type:"injury_followup",warrior_id:follow["warrior_id"],description}]};return withCampaign(document,{...document.campaign,post_battles:document.campaign.post_battles.map((row)=>row.battle_number===post.battle_number?changed:row)});}

export function resolveInjuryTableFollowUp(document:CampaignDocument,reader:KnowledgeReader,input:{follow_up_id:string;roll:number}):Result{
  const post=document.campaign.post_battles.find((row)=>!row.complete),follow=post?.pending_follow_ups?.find((row)=>row["id"]===input.follow_up_id&&(row["type"]==="injury_roll"||row["type"]==="injury_followup")),warrior=document.campaign.warriors.find((row)=>row.id===follow?.["warrior_id"]);if(!post||!follow||!warrior)return{ok:false,message:"Unknown injury follow-up."};
  const dice=injuryFollowUpDice(reader,follow),roll=Math.trunc(input.roll);if(!dice||!valid(roll,dice))return{ok:false,message:"Use a valid result for this injury roll."};
  const phase=String(follow["resolution_phase"]??"subtable"),parent=source(reader,follow),resolution=parent?.["resolution"] as OpenPayload|undefined;
  if(phase==="effect_roll"){
    if(follow["effect_kind"]!=="miss_games")return{ok:false,message:"Unsupported injury effect roll."};
    const applied=applyInjuryOutcome(document,{warrior_id:warrior.id,result_id:String(follow["result_id"]??"injury-effect"),result:String(parent?.["result"]??"Injury"),effects:[{kind:"miss_games",value:roll}]});if(!applied.ok)return{ok:false,message:applied.message};
    const changed=applied.document.campaign.post_battles.find((row)=>row.battle_number===post.battle_number)!;return{ok:true,document:replace(applied.document,changed,follow,[],`${warrior.name} misses ${roll} game(s).`)};
  }
  if(phase==="repeat_count"){
    const repeats=Array.from({length:roll},(_,index)=>({...follow,id:`${String(follow["id"])}:repeat:${index+1}`,resolution_phase:"repeat_result",dice:{count:2,sides:6}}));
    return{ok:true,document:replace(document,post,follow,repeats,`${warrior.name}: ${roll} additional serious injury roll(s) required.`)};
  }
  let outcome:Readonly<Record<string,unknown>>|undefined;
  if(phase==="subtable"&&resolution?.["type"]==="roll_table")outcome=((resolution["branches"]??[]) as readonly Readonly<Record<string,unknown>>[]).find((row)=>{const when=row["when"] as OpenPayload|undefined;return roll>=Number(when?.["min"]??0)&&roll<=Number(when?.["max"]??when?.["min"]??0);});
  if(phase==="repeat_result"&&resolution?.["type"]==="repeat_table"){const excluded=new Set((resolution["reroll_ids"]??[]) as readonly string[]);outcome=(reader as Reader).list?.("injury")?.find((row)=>row["applies_to"]==="hero"&&range(String(row["roll"]??""),roll)&&!excluded.has(String(row["id"])));}
  if(!outcome)return{ok:false,message:"That result is excluded or missing; roll again."};
  const applied=applyInjuryOutcome(document,{warrior_id:warrior.id,result_id:String(outcome["id"]??"injury-followup"),result:String(outcome["result"]??"Resolved injury"),effects:injuryEffects(outcome)});if(!applied.ok)return{ok:false,message:applied.message};
  const changed=applied.document.campaign.post_battles.find((row)=>row.battle_number===post.battle_number)!;return{ok:true,document:replace(applied.document,changed,follow,[],`${warrior.name}: ${String(outcome["result"]??"injury resolved")}`)};
}

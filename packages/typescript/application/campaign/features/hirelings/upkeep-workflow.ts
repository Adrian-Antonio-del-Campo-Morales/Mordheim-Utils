import type { CampaignDocument } from "../../../../domain/campaign/index";
import { currentState, withCampaign } from "../../../../domain/campaign/kernel/document";

type Resource="gold_crowns"|"wyrdstone_fragments"|"treasures"|"campaign_points";
type Result={ok:true;document:CampaignDocument}|{ok:false;message:string};
const LABEL:Record<Resource,string>={gold_crowns:"gc",wyrdstone_fragments:"wyrdstone shard(s)",treasures:"treasure(s)",campaign_points:"campaign point(s)"};

/** Desktop `resolve_hireling_upkeep`: pay every declared resource or dismiss. */
export function resolveHirelingUpkeep(document:CampaignDocument,input:{follow_up_id:string;pay:boolean}):Result {
  const post=document.campaign.post_battles.find((row)=>!row.complete);
  const follow=post?.pending_follow_ups?.find((row)=>row["id"]===input.follow_up_id&&row["type"]==="hireling_upkeep");
  if(!post||!follow)return{ok:false,message:"Unknown Hired Sword upkeep."};
  const warriorId=String(follow["warrior_id"]??""), warrior=document.campaign.warriors.find((row)=>row.id===warriorId);
  const costs=(Array.isArray(follow["costs"])?follow["costs"]:[]).flatMap((row)=>Array.isArray(row)&&typeof row[0]==="string"&&Number.isInteger(row[1])&&row[0] in LABEL?[[row[0] as Resource,Number(row[1])] as const]:[]);
  const available=(resource:Resource)=>resource==="gold_crowns"?(currentState(document)?.gold??0)+(post.gold_delta??0):resource==="wyrdstone_fragments"?(currentState(document)?.wyrdstone??0)+(post.wyrdstone_delta??0):document.campaign.resources[resource]??0;
  if(input.pay)for(const [resource,amount] of costs)if(amount>available(resource))return{ok:false,message:`Not enough ${LABEL[resource]}: ${amount} needed, ${available(resource)} available.`};
  const gold=costs.find(([resource])=>resource==="gold_crowns")?.[1]??0, shards=costs.find(([resource])=>resource==="wyrdstone_fragments")?.[1]??0, treasures=costs.find(([resource])=>resource==="treasures")?.[1]??0, points=costs.find(([resource])=>resource==="campaign_points")?.[1]??0;
  const pending=(post.pending_follow_ups??[]).filter((row)=>row!==follow);
  const changed={...post,gold_delta:(post.gold_delta??0)-(input.pay?gold:0),wyrdstone_delta:(post.wyrdstone_delta??0)-(input.pay?shards:0),pending_follow_ups:pending,event_log:[...(post.event_log??[]),{step:7,type:"hireling_upkeep",warrior_id:warriorId,...(warrior?{warrior_personal_name:warrior.name}:{}),pay:input.pay,costs}]};
  let inventory=document.campaign.inventory;
  if(!input.pay&&warrior){for(const item of warrior.equipment){inventory=inventory.map((row)=>row.id===item.item_id?{...row,owned:Math.max(0,row.owned-item.quantity),equipped:Math.max(0,row.equipped-item.quantity)}:row).filter((row)=>row.owned>0);}}
  // Desktop strips `Returning a Favour:` once the upkeep is paid (the free
  // hire is spent); the rule must not linger on the roster.
  const warriors=input.pay
    ? (warrior?document.campaign.warriors.map((row)=>row.id===warriorId?{...row,special_rules:(row.special_rules??[]).filter((rule)=>!rule.startsWith("Returning a Favour:"))}:row):document.campaign.warriors)
    : document.campaign.warriors.filter((row)=>row.id!==warriorId);
  return{ok:true,document:withCampaign(document,{...document.campaign,resources:{...document.campaign.resources,treasures:document.campaign.resources.treasures-(input.pay?treasures:0),campaign_points:document.campaign.resources.campaign_points-(input.pay?points:0)},warriors,inventory,post_battles:document.campaign.post_battles.map((row)=>row===post?changed:row)})};
}

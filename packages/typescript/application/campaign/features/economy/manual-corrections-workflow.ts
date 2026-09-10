import type { CampaignDocument, KnowledgeReader } from "../../../../domain/campaign/index";
import { currentState, withCampaign } from "../../../../domain/campaign/kernel/document";

type Result={ok:true;document:CampaignDocument}|{ok:false;message:string};

/** Audited desktop-style resource correction, allowed only in draft or post-battle. */
export function correctResource(document:CampaignDocument,input:{resource:string;delta:number;reason:string}):Result {
  const reason=input.reason.trim(), delta=Math.trunc(input.delta), post=document.campaign.post_battles.find((row)=>!row.complete), resource=input.resource;
  if(!reason)return{ok:false,message:"Enter a reason for the resource correction."};
  if(!Number.isInteger(input.delta)||!delta)return{ok:false,message:"Enter a non-zero whole correction."};
  if(!["gold_crowns","wyrdstone_fragments","treasures","campaign_points"].includes(resource))return{ok:false,message:"Unknown resource."};
  if(!document.campaign.configuration.is_draft&&!post)return{ok:false,message:"Resources can be corrected only during creation or post-battle."};
  if(document.campaign.configuration.is_draft&&resource!=="gold_crowns")return{ok:false,message:"Only gold crowns are available during creation."};
  const state=currentState(document), current=resource==="gold_crowns"?(document.campaign.configuration.is_draft?document.campaign.configuration.starting_gold:(state?.gold??0)+(post?.gold_delta??0)):resource==="wyrdstone_fragments"?(state?.wyrdstone??0)+(post?.wyrdstone_delta??0):document.campaign.resources[resource as "treasures"|"campaign_points"];
  if(current+delta<0)return{ok:false,message:`The correction would leave a negative balance (${current+delta}).`};
  if(document.campaign.configuration.is_draft)return{ok:true,document:withCampaign(document,{...document.campaign,configuration:{...document.campaign.configuration,starting_gold:document.campaign.configuration.starting_gold+delta},manual_log:[...document.campaign.manual_log,{type:"manual_resource_correction",resource,delta,reason}]})};
  const changed={...post!,gold_delta:(post!.gold_delta??0)+(resource==="gold_crowns"?delta:0),wyrdstone_delta:(post!.wyrdstone_delta??0)+(resource==="wyrdstone_fragments"?delta:0),event_log:[...(post!.event_log??[]),{step:post!.active_step,type:"manual_resource_correction",description:`${resource}: ${delta>=0?"+":""}${delta} (${reason})`,resource}]};
  const resources={...document.campaign.resources,...(resource==="treasures"?{treasures:document.campaign.resources.treasures+delta}:{}),...(resource==="campaign_points"?{campaign_points:document.campaign.resources.campaign_points+delta}:{})};
  return{ok:true,document:withCampaign(document,{...document.campaign,resources,manual_log:[...document.campaign.manual_log,{type:"manual_resource_correction",resource,delta,reason}],post_battles:document.campaign.post_battles.map((row)=>row===post?changed:row)})};
}

/** Audited desktop `manually_add_item`, using a canonical KB item. */
export function addManualStashItem(document:CampaignDocument,reader:KnowledgeReader,input:{item_id:string;quantity:number;reason:string}):Result {
  const reason=input.reason.trim(), quantity=Math.trunc(input.quantity), post=document.campaign.post_battles.find((row)=>!row.complete), item=reader.queryKnowledge({id:{kind:"item_id",value:input.item_id}});
  if(!reason)return{ok:false,message:"Enter a reason for adding the item."}; if(!Number.isInteger(input.quantity)||quantity<1)return{ok:false,message:"Quantity must be a positive whole number."};
  if(!document.campaign.configuration.is_draft&&!post)return{ok:false,message:"Items can be corrected only during creation or post-battle."}; if(!item.ok)return{ok:false,message:"Select an item from the KB catalogue."};
  const name=item.record.names["en"]??input.item_id, value=typeof item.record.data["value"]==="number"?item.record.data["value"]:0, category=String(item.record.data["kind"]??"Equipment"), existing=document.campaign.inventory.find((row)=>row.id===input.item_id);
  const inventory=existing?document.campaign.inventory.map((row)=>row.id===input.item_id?{...row,owned:row.owned+quantity,stash:row.stash+quantity}:row):[...document.campaign.inventory,{id:input.item_id,name,category,owned:quantity,equipped:0,stash:quantity,value}];
  const log={type:"manual_item_correction",item_id:input.item_id,quantity,reason}; const changed=post?{...post,event_log:[...(post.event_log??[]),{step:post.active_step,type:"manual_item_correction",description:`+${quantity} ${name} (${reason})`,item_id:input.item_id}]}:null;
  return{ok:true,document:withCampaign(document,{...document.campaign,inventory,manual_log:[...document.campaign.manual_log,log],...(changed?{post_battles:document.campaign.post_battles.map((row)=>row===post?changed:row)}:{})})};
}

import type { CampaignDocument, TimelineState } from "../../../../domain/campaign/index";
import { currentState, effectiveMaximumModels, experienceTotal, heroCount, memberCount, modelCount, rating, withCampaign } from "../../../../domain/campaign/kernel/document";
import { followUpNeedsResolution } from "./follow-up-acknowledgement-workflow";

type Result={ok:true;document:CampaignDocument}|{ok:false;message:string};

/** Commit the desktop post-battle result as the next immutable timeline state. */
export function finalizePostBattle(document:CampaignDocument):Result {
  const post=document.campaign.post_battles.find((row)=>!row.complete), base=currentState(document);
  if(!post||!base)return{ok:false,message:"No pending post-battle sequence."};
  if(post.active_step!==7)return{ok:false,message:"Complete each post-battle phase before confirming the next state."};
  if(!post.experience_applied||(post.pending_advances??[]).some((row)=>!row["committed"]))return{ok:false,message:"Resolve experience and every advance before confirming the next state."};
  if(!(post.step_state?.["exploration"] as Record<string,unknown>|undefined)?.["resolved"]||!post.sale_resolved||!(post.step_state?.["veterans"] as Record<string,unknown>|undefined)?.["resolved"])return{ok:false,message:"Complete exploration, wyrdstone sale and veteran availability first."};
  if((post.pending_follow_ups??[]).some((row)=>followUpNeedsResolution(row,post.acknowledgements??{})))return{ok:false,message:"Resolve all pending post-battle follow-ups first."};
  if((post.equipment_obligations??[]).length)return{ok:false,message:"Equip newly recruited henchmen before confirming the next state."};
  const battle=document.campaign.battles.find((row)=>row.number===post.battle_number);
  const stateNumber=document.campaign.current_state_number+1;
  const state:TimelineState={number:stateNumber,date:new Date().toISOString().slice(0,10),gold:base.gold+(post.gold_delta??0),wyrdstone:base.wyrdstone+(post.wyrdstone_delta??0)-(post.wyrdstone_sold??0),rating:rating(document.campaign.warriors),models:modelCount(document.campaign.warriors),max_models:effectiveMaximumModels(document.campaign),heroes:heroCount(document.campaign.warriors),henchmen:document.campaign.warriors.filter((row)=>row.kind==="henchman").reduce((total,row)=>total+(row.quantity??1),0),experience:experienceTotal(document.campaign.warriors),label:`After battle #${post.battle_number}`,roster:structuredClone(document.campaign.warriors),inventory:structuredClone(document.campaign.inventory)};
  const completed={...post,complete:true,active_step:8,completed_steps:[0,1,2,3,4,5,6,7],review_open:true};
  return{ok:true,document:withCampaign(document,{...document.campaign,current_state_number:stateNumber,states:[...document.campaign.states,state],battles:battle?document.campaign.battles.map((row)=>row===battle?{...row,rating_after:state.rating,models_after:state.models,advances:(post.pending_advances??[]).length}:row):document.campaign.battles,post_battles:document.campaign.post_battles.map((row)=>row===post?completed:row)})};
}

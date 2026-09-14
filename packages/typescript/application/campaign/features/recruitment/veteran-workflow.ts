import type { CampaignDocument } from "../../../../domain/campaign/index";
import { withCampaign } from "../../../../domain/campaign/kernel/document";

type Result={ok:true;document:CampaignDocument}|{ok:false;message:string};

/** Desktop apply_veteran_pool, gated by prior product steps. */
export function applyVeteranPool(document:CampaignDocument,dice:readonly number[]):Result {
  const post=document.campaign.post_battles.find((row)=>!row.complete); if(!post)return{ok:false,message:"No pending post-battle veteran roll."};
  if(!post.sale_resolved)return{ok:false,message:"Resolve wyrdstone sale before checking veterans."};
  if((post.step_state?.["veterans"] as Record<string,unknown>|undefined)?.["resolved"])return{ok:false,message:"Veteran availability has already been resolved."};
  if(dice.length!==2||dice.some((die)=>!Number.isInteger(die)||die<1||die>6))return{ok:false,message:"Veteran availability requires exactly 2D6."};
  const pool=dice[0]+dice[1]; const changed={...post,veteran_pool:pool,step_state:{...(post.step_state??{}),veterans:{resolved:true,dice:[...dice],pool}},event_log:[...(post.event_log??[]),{step:5,type:"veteran_pool",pool}]};
  return{ok:true,document:withCampaign(document,{...document.campaign,post_battles:document.campaign.post_battles.map((row)=>row===post?changed:row)})};
}

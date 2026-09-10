import type { CampaignDocument, KnowledgeReader, OpenPayload } from "../../../../domain/campaign/index";
import { currentState, effectiveMaximumModels, memberCount, withCampaign } from "../../../../domain/campaign/kernel/document";

interface CatalogueReader extends KnowledgeReader { campaignSection?(section:string):Readonly<Record<string,unknown>> }
type Result={ok:true;document:CampaignDocument}|{ok:false;message:string};

/** Desktop `add_member_to_group`: hire one veteran into an existing henchman group. */
export function recruitGroupMember(document:CampaignDocument,reader:CatalogueReader,input:{warrior_id:string}):Result {
  const post=document.campaign.post_battles.find((row)=>!row.complete);
  const warrior=document.campaign.warriors.find((row)=>row.id===input.warrior_id);
  if(!post||!warrior||warrior.kind!=="henchman")return{ok:false,message:"Only an existing henchman group can receive a member during post-battle."};
  if(!(post.step_state?.["veterans"] as OpenPayload|undefined)?.["resolved"])return{ok:false,message:"Resolve veteran availability first."};
  const band=reader.queryKnowledge({id:{kind:"band_id",value:document.campaign.identity.band_id}});
  const members=band.ok&&Array.isArray((band.record.data["roster"] as OpenPayload|undefined)?.["members"])?((band.record.data["roster"] as OpenPayload)["members"] as OpenPayload[]):[];
  const member=members.find((row)=>row["profile_id"]===warrior.profile_id);
  if(!member)return{ok:false,message:"This henchman profile is not available to the current warband."};
  const profileMaximum=Number(member["maximum"]??Infinity);
  const groupMaximum=Number(((member["group_size"] as OpenPayload|undefined)?.["maximum"])??Infinity);
  const taken=document.campaign.warriors.filter((row)=>row.profile_id===warrior.profile_id).reduce((total,row)=>total+(row.quantity??1),0);
  if(taken>=profileMaximum)return{ok:false,message:`Roster limit reached (${taken}/${profileMaximum}).`};
  if((warrior.quantity??1)>=groupMaximum)return{ok:false,message:`${warrior.name} holds at most ${groupMaximum} members.`};
  if(memberCount(document.campaign.warriors)+1>effectiveMaximumModels(document.campaign))return{ok:false,message:`Cannot exceed ${effectiveMaximumModels(document.campaign)} warband members.`};
  const veterans=reader.campaignSection?.("recruitment-and-veterans")?.["veteran_availability"];
  const rate=Array.isArray(veterans)?Number((((veterans[0] as OpenPayload)?.["incremental_cost"] as OpenPayload|undefined)?.["per_experience_point_gc"])??2):2;
  const xp=Math.max(0,warrior.experience), pool=post.veteran_pool??0;
  if(xp>pool)return{ok:false,message:`${warrior.name} needs ${xp} Veteran XP; only ${pool} available.`};
  const total=warrior.cost+xp*rate, gold=(currentState(document)?.gold??0)+(post.gold_delta??0);
  if(total>gold)return{ok:false,message:`Not enough gold: ${total} gc needed, ${gold} available.`};
  const oldQuantity=warrior.quantity??1;
  const obligations=warrior.equipment.filter((item)=>item.per_model&&item.acquisition!=="fixed").map((item)=>({warrior_id:warrior.id,item_id:item.item_id,item_name:item.name,copies_per_model:Math.max(1,Math.ceil(item.quantity/oldQuantity))}));
  const changed={...post,veteran_pool:pool-xp,gold_delta:(post.gold_delta??0)-total,equipment_obligations:[...(post.equipment_obligations??[]).filter((row)=>String(row["warrior_id"])!==warrior.id),...obligations],event_log:[...(post.event_log??[]),{step:7,type:"recruit_member",warrior_id:warrior.id,description:`One member joined ${warrior.name} for ${total} gc; matching equipment remains pending.`}]};
  return{ok:true,document:withCampaign(document,{...document.campaign,warriors:document.campaign.warriors.map((row)=>row.id===warrior.id?{...row,quantity:oldQuantity+1}:row),post_battles:document.campaign.post_battles.map((row)=>row===post?changed:row)})};
}

/** Desktop `dismiss_warrior`, including the one-member group variant. */
export function dismissRecruit(document:CampaignDocument,input:{warrior_id:string;one_member?:boolean}):Result {
  const post=document.campaign.post_battles.find((row)=>!row.complete), warrior=document.campaign.warriors.find((row)=>row.id===input.warrior_id);
  if(!post||!warrior)return{ok:false,message:"Choose a current warrior during post-battle."};
  const one=Boolean(input.one_member)&&warrior.kind==="henchman"&&(warrior.quantity??1)>1;
  const quantity=warrior.quantity??1;
  let inventory=[...document.campaign.inventory];
  const equipment=warrior.equipment.flatMap((item)=>{
    const returned=item.acquisition==="fixed"?0:one&&item.per_model?Math.min(item.quantity,Math.max(1,Math.ceil(item.quantity/quantity))):item.quantity;
    if(returned>0){const index=inventory.findIndex((row)=>row.id===item.item_id);if(index>=0){const row=inventory[index];inventory[index]={...row,equipped:Math.max(0,row.equipped-returned),stash:row.stash+returned};}}
    const remaining=item.quantity-returned; return remaining>0?[{...item,quantity:remaining}]:[];
  });
  const warriors=one?document.campaign.warriors.map((row)=>row.id===warrior.id?{...row,quantity:quantity-1,equipment}:row):document.campaign.warriors.filter((row)=>row.id!==warrior.id);
  const obligations=(post.equipment_obligations??[]).filter((row)=>String(row["warrior_id"])!==warrior.id);
  const description=one?`One member dismissed from ${warrior.name}; transferable equipment returned to stash.`:`${warrior.name} dismissed; transferable equipment returned to stash.`;
  const changed={...post,equipment_obligations:obligations,event_log:[...(post.event_log??[]),{step:7,type:one?"dismiss_member":"dismiss_warrior",warrior_id:warrior.id,description}]};
  return{ok:true,document:withCampaign(document,{...document.campaign,warriors,inventory,post_battles:document.campaign.post_battles.map((row)=>row===post?changed:row)})};
}

/** Desktop `recruit_band_profile` for a new Hero or henchman group. */
export function recruitBandProfile(document:CampaignDocument,reader:KnowledgeReader,input:{profile_id:string;quantity?:number;name?:string}):Result {
  const post=document.campaign.post_battles.find((row)=>!row.complete), band=reader.queryKnowledge({id:{kind:"band_id",value:document.campaign.identity.band_id}}), profile=reader.queryKnowledge({id:{kind:"profile_id",value:input.profile_id}});
  if(!post||!band.ok||!profile.ok)return{ok:false,message:"Unknown recruit or no pending post-battle."};
  const roster=(band.record.data["roster"]??{}) as OpenPayload, member=(Array.isArray(roster["members"])?roster["members"] as OpenPayload[]:[]).find((row)=>row["profile_id"]===input.profile_id);
  if(!member)return{ok:false,message:"This profile is not available to the current warband."};
  const data=profile.record.data, kind=data["type"]==="hero"?"hero":"henchman", quantity=Math.max(1,Math.trunc(input.quantity??1));
  if(kind==="hero"&&quantity!==1)return{ok:false,message:"Recruit Heroes individually."};
  const maximum=Number(member["maximum"]??Infinity), groupMaximum=Number(((member["group_size"] as OpenPayload|undefined)?.["maximum"])??Infinity), taken=document.campaign.warriors.filter((row)=>row.profile_id===input.profile_id).reduce((total,row)=>total+(row.quantity??1),0);
  if(taken+quantity>maximum||quantity>groupMaximum)return{ok:false,message:"Roster or group limit reached for this recruit."};
  if(memberCount(document.campaign.warriors)+quantity>effectiveMaximumModels(document.campaign))return{ok:false,message:`Cannot exceed ${effectiveMaximumModels(document.campaign)} warband members.`};
  if(kind==="hero"&&heroCount(document.campaign.warriors)+1>document.campaign.configuration.hero_limit)return{ok:false,message:`Cannot exceed ${document.campaign.configuration.hero_limit} heroes.`};
  const cost=Number(data["cost"]??0)*quantity, gold=(currentState(document)?.gold??0)+(post.gold_delta??0); if(cost>gold)return{ok:false,message:`Not enough gold: ${cost} gc needed, ${gold} available.`};
  const characteristics=(data["characteristics"]??{}) as OpenPayload, stats=Object.fromEntries(Object.entries(characteristics).filter(([,value])=>typeof value==="number"));
  const fixed=Array.isArray(data["fixed_equipment"])?data["fixed_equipment"].filter((id):id is string=>typeof id==="string"):[];
  const equipment=fixed.map((item_id)=>{const item=reader.queryKnowledge({id:{kind:"item_id",value:item_id}});return{item_id,name:item.ok?item.record.names["en"]??item_id:item_id,quantity,acquisition:"fixed" as const,per_model:true};});
  const traits=(data["combat_traits"]??{}) as OpenPayload, skills=[...(Array.isArray(data["inherent_rules"])?data["inherent_rules"]:[]),...(Array.isArray(traits["starting_skills"])?traits["starting_skills"]:[])].filter((value):value is string=>typeof value==="string");
  const base=profile.record.names["en"]??input.profile_id, names=new Set(document.campaign.warriors.map((row)=>row.name)), wanted=String(input.name??"").trim()||(kind==="hero"?base:`${base} Group`); let name=wanted,index=2;while(names.has(name))name=`${wanted} ${index++}`;
  const occurrence=document.campaign.warriors.filter((row)=>row.profile_id===input.profile_id).length+1;
  const warrior={id:`${input.profile_id}#recruit-${occurrence}`,name,profile_name:base,kind,stats,equipment,skills,experience:Number(data["experience"]??0),quantity,cost:Number(data["cost"]??0),profile_id:input.profile_id,skill_access:Array.isArray(data["skill_access"])?data["skill_access"].filter((value):value is string=>typeof value==="string"):[]};
  const changed={...post,gold_delta:(post.gold_delta??0)-cost,event_log:[...(post.event_log??[]),{step:7,type:"recruit",warrior_id:warrior.id,profile_id:input.profile_id,description:`${base} ×${quantity} recruited for ${cost} gc.`}]};
  return{ok:true,document:withCampaign(document,{...document.campaign,warriors:[...document.campaign.warriors,warrior],post_battles:document.campaign.post_battles.map((row)=>row===post?changed:row)})};
}

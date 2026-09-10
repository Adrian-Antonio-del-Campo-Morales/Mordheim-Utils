import type { CampaignDocument, KnowledgeReader, OpenPayload } from "../../../../domain/campaign/index";
import { withCampaign } from "../../../../domain/campaign/kernel/document";

type Result={ok:true;document:CampaignDocument}|{ok:false;message:string};

/** Desktop `set_manual_skill`: audited correction outside a rolled advance. */
export function setManualSkill(document:CampaignDocument,reader:KnowledgeReader,input:{warrior_id:string;skill_id:string;present:boolean;reason:string}):Result {
  const reason=input.reason.trim(), warrior=document.campaign.warriors.find((row)=>row.id===input.warrior_id), skill=reader.queryKnowledge({id:{kind:"skill_id",value:input.skill_id}});
  if(!reason)return{ok:false,message:"Enter a reason for the skill correction."};
  if(!document.campaign.configuration.is_draft&&!document.campaign.post_battles.some((row)=>!row.complete))return{ok:false,message:"Skills can be edited only during creation or post-battle."};
  if(!warrior||!skill.ok)return{ok:false,message:"Unknown warrior or skill."};
  const profile=warrior.profile_id?reader.queryKnowledge({id:{kind:"profile_id",value:warrior.profile_id}}):null, profileData=profile?.ok?profile.record.data:{} as OpenPayload;
  const traits=(profileData["combat_traits"]??{}) as OpenPayload, fixed=new Set([...(Array.isArray(profileData["inherent_rules"])?profileData["inherent_rules"]:[]),...(Array.isArray(traits["starting_skills"])?traits["starting_skills"]:[])].filter((value):value is string=>typeof value==="string"));
  const name=skill.record.names["en"]??input.skill_id, category=String(skill.record.data["category"]??"");
  if(!input.present&&fixed.has(name))return{ok:false,message:"An inherent or starting skill cannot be removed."};
  if(input.present&&warrior.skill_access?.length&&!warrior.skill_access.includes(category))return{ok:false,message:`${name} is not in ${warrior.name}'s skill access.`};
  const skills=input.present?[...new Set([...warrior.skills,name])]:warrior.skills.filter((value)=>value!==name);
  const action=input.present?"added":"removed", entry={type:"manual_skill_correction",warrior_id:warrior.id,warrior:warrior.name,skill:name,action,reason};
  return{ok:true,document:withCampaign(document,{...document.campaign,warriors:document.campaign.warriors.map((row)=>row.id===warrior.id?{...row,skills}:row),manual_log:[...document.campaign.manual_log,entry]})};
}

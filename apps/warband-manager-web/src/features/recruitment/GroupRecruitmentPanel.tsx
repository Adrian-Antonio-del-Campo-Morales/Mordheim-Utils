import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";

/** Existing henchman groups may recruit one veteran at a time. */
export function GroupRecruitmentPanel({document,locale="en"}:{readonly document:CampaignDocument;readonly locale?:"es"|"en"}) {
  const app=useCampaignApp(); const post=document.campaign.post_battles.find((row)=>!row.complete); if(!post)return null;
  const ready=Boolean((post.step_state?.["veterans"] as Record<string,unknown>|undefined)?.["resolved"]);
  const groups=document.campaign.warriors.filter((row)=>row.kind==="henchman");
  const t=locale==="es"?{title:"07 · Reclutamiento",wait:"Resuelve primero los veteranos disponibles.",empty:"No hay grupos de secuaces que ampliar.",pool:"PX de veterano disponibles",add:"Reclutar un miembro",xp:"PX",cost:"Coste base",dismissOne:"Retirar un miembro",dismiss:"Licenciar"}:{title:"07 · Recruitment",wait:"Resolve available veterans first.",empty:"No henchman groups can be expanded.",pool:"Veteran XP available",add:"Recruit one member",xp:"XP",cost:"Base cost",dismissOne:"Dismiss one member",dismiss:"Dismiss"};
  return <section aria-label="Group recruitment"><h3>{t.title}</h3>{!ready?<p role="status">{t.wait}</p>:groups.length===0?<p>{t.empty}</p>:<><p>{t.pool}: {post.veteran_pool??0}</p><table><thead><tr><th>Group</th><th>{t.xp}</th><th>{t.cost}</th><th>Action</th></tr></thead><tbody>{groups.map((group)=><tr key={group.id}><td>{group.name} · {group.quantity??1}</td><td>{group.experience}</td><td>{group.cost} gc</td><td><button onClick={()=>void app.runAction("recruitGroupMember",{warrior_id:group.id})}>{t.add}</button>{(group.quantity??1)>1&&<button onClick={()=>void app.runAction("dismissRecruit",{warrior_id:group.id,one_member:true})}>{t.dismissOne}</button>}<button onClick={()=>void app.runAction("dismissRecruit",{warrior_id:group.id})}>{t.dismiss}</button></td></tr>)}</tbody></table></>}</section>;
}

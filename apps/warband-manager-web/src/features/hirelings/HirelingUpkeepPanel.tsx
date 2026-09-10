import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";

export function HirelingUpkeepPanel({document,locale="en"}:{readonly document:CampaignDocument;readonly locale?:"es"|"en"}) {
  const app=useCampaignApp(); const post=document.campaign.post_battles.find((row)=>!row.complete); if(!post)return null;
  const rows=(post.pending_follow_ups??[]).filter((row)=>row["type"]==="hireling_upkeep"); if(!rows.length)return null;
  const t=locale==="es"?{title:"Mantenimiento de mercenarios",pay:"Pagar",leave:"Dejar marchar"}:{title:"Hired Sword upkeep",pay:"Pay",leave:"Let leave"};
  return <section aria-label="Hireling upkeep"><h3>{t.title}</h3>{rows.map((row)=>{const warrior=document.campaign.warriors.find((item)=>item.id===row["warrior_id"]);const costs=(Array.isArray(row["costs"])?row["costs"]:[]).filter(Array.isArray).map((cost)=>`${cost[1]} ${cost[0]}`).join(" + ");return <article key={String(row["id"])}><strong>{warrior?.name??"Hired Sword"}</strong><p>{costs}</p><button className="primary" onClick={()=>void app.runAction("resolveHirelingUpkeep",{follow_up_id:row["id"],pay:true})}>{t.pay}</button><button onClick={()=>void app.runAction("resolveHirelingUpkeep",{follow_up_id:row["id"],pay:false})}>{t.leave}</button></article>;})}</section>;
}

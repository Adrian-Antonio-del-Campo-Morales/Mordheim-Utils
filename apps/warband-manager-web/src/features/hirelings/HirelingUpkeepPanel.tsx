import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { resourceAmount } from "../campaign/displayText";

export function HirelingUpkeepPanel({document,locale="en"}:{readonly document:CampaignDocument;readonly locale?:"es"|"en"}) {
  const app=useCampaignApp(); const post=document.campaign.post_battles.find((row)=>!row.complete); if(!post)return null;
  const rows=(post.pending_follow_ups??[]).filter((row)=>row["type"]==="hireling_upkeep").sort((a,b)=>{
    const aName=document.campaign.warriors.find((item)=>item.id===a["warrior_id"])?.name??"";
    const bName=document.campaign.warriors.find((item)=>item.id===b["warrior_id"])?.name??"";
    return aName.localeCompare(bName,locale);
  }); if(!rows.length)return null;
  const t=locale==="es"?{title:"Mantenimiento de mercenarios",pay:"Pagar",leave:"Dejar marchar"}:{title:"Hired Sword upkeep",pay:"Pay",leave:"Let leave"};
  return <section aria-label={locale === "es" ? "Mantenimiento de mercenarios" : "Hireling upkeep"}><h3>{t.title}</h3>{rows.map((row)=>{const warrior=document.campaign.warriors.find((item)=>item.id===row["warrior_id"]);const costs=(Array.isArray(row["costs"])?row["costs"]:[]).filter(Array.isArray).map((cost)=>resourceAmount(cost[0],cost[1],locale)).join(" + ");return <article key={String(row["id"])}><strong>{warrior?.name??(locale === "es" ? "Espada de alquiler" : "Hired Sword")}</strong><p>{costs}</p><button className="primary" onClick={()=>void app.runAction("resolveHirelingUpkeep",{follow_up_id:row["id"],pay:true})}>{t.pay}</button><button onClick={()=>void app.runAction("resolveHirelingUpkeep",{follow_up_id:row["id"],pay:false})}>{t.leave}</button></article>;})}</section>;
}

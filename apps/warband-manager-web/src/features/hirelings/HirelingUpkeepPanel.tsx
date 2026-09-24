import { warriorPersonalName, textJoin } from "../campaign/presentation-values";
import { presentationOutput } from "../campaign/presentation-output";
import { translate } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { resourceAmount } from "../campaign/displayText";

export function HirelingUpkeepPanel({document,locale: requestedLocale}:{readonly document:CampaignDocument;readonly locale?:"es"|"en"}) {
  const locale = useLocale(requestedLocale);
  const app=useCampaignApp(); const post=document.campaign.post_battles.find((row)=>!row.complete); if(!post)return null;
  const rows=(post.pending_follow_ups??[]).filter((row)=>row["type"]==="hireling_upkeep").sort((a,b)=>{
    const aName=document.campaign.warriors.find((item)=>item.id===a["warrior_id"])?.name??"";
    const bName=document.campaign.warriors.find((item)=>item.id===b["warrior_id"])?.name??"";
    return aName.localeCompare(bName,locale);
  }); if(!rows.length)return null;
  const t=({ title: translate({ key: "ui.4dacd9fca038" }, locale), pay: translate({ key: "ui.8826dd3f8e40" }, locale), leave: translate({ key: "ui.9d4da9224528" }, locale) });
  return <section aria-label={presentationOutput(translate({ key: "ui.3069e4a2e9a9" }, locale))}><h3>{presentationOutput(t.title)}</h3>{rows.map((row)=>{const warrior=document.campaign.warriors.find((item)=>item.id===row["warrior_id"]);const costs=textJoin((Array.isArray(row["costs"])?row["costs"]:[]).filter(Array.isArray).map((cost)=>resourceAmount(cost[0],cost[1],locale)), " + ");return <article key={String(row["id"])}><strong>{presentationOutput(warriorPersonalName(warrior, locale))}</strong><p>{presentationOutput(costs)}</p><button className="primary" onClick={()=>void app.runAction("resolveHirelingUpkeep",{follow_up_id:row["id"],pay:true})}>{presentationOutput(t.pay)}</button><button onClick={()=>void app.runAction("resolveHirelingUpkeep",{follow_up_id:row["id"],pay:false})}>{presentationOutput(t.leave)}</button></article>;})}</section>;
}

import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { DiceResolver } from "../dice/DiceResolver";

export function VeteranPoolPanel({document,locale="en"}:{readonly document:CampaignDocument;readonly locale?:"es"|"en"}) {
  const app=useCampaignApp(); const post=document.campaign.post_battles.find((row)=>!row.complete); if(!post)return null; const resolved=Boolean((post.step_state?.["veterans"] as Record<string,unknown>|undefined)?.["resolved"]);
  const t=locale==="es"?{title:"Veteranos Disponibles",resolved:"Reserva de Experiencia Veterana",shared:"Se comparte entre contrataciones veteranas posteriores.",first:"Resuelve primero la venta de piedra bruja.",roll:"Tira 2D6. El resultado crea la reserva compartida; aún no se contrata ningún recluta.",dice:"Reserva de Experiencia Veterana"}:{title:"Available Veterans",resolved:"Veteran Experience Pool",shared:"Shared across later veteran hires.",first:"Resolve wyrdstone sale first.",roll:"Roll 2D6. Result creates shared XP pool; no recruit is hired yet.",dice:"Veteran Experience Pool"};
  return <section aria-label={t.title}><h3>05 · {t.title}</h3>{resolved?<p role="status">{t.resolved}: {post.veteran_pool??0} XP. {t.shared}</p>:!post.sale_resolved?<p role="status">{t.first}</p>:<><p>{t.roll}</p><DiceResolver locale={locale} count={2} sides={6} label={t.dice} onResolve={(dice)=>void app.runAction("applyVeteranPool",{dice})}/></>}</section>;
}

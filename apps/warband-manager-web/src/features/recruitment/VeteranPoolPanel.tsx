import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { DiceResolver } from "../dice/DiceResolver";

export function VeteranPoolPanel({document}:{readonly document:CampaignDocument}) {
  const app=useCampaignApp(); const post=document.campaign.post_battles.find((row)=>!row.complete); if(!post)return null; const resolved=Boolean((post.step_state?.["veterans"] as Record<string,unknown>|undefined)?.["resolved"]);
  return <section aria-label="Available veterans"><h3>05 · Available veterans</h3>{resolved?<p role="status">Veteran experience pool: {post.veteran_pool??0} XP. Shared across later veteran hires.</p>:!post.sale_resolved?<p role="status">Resolve wyrdstone sale first.</p>:<><p>Roll 2D6. Result creates shared XP pool; no recruit is hired yet.</p><DiceResolver count={2} sides={6} label="Veteran experience pool" onResolve={(dice)=>void app.runAction("applyVeteranPool",{dice})}/></>}</section>;
}

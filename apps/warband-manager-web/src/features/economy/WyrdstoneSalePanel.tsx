import { useMemo, useState } from "react";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { quoteWyrdstoneSale } from "@app/campaign/features/economy/wyrdstone-sale-workflow";
import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";

export function WyrdstoneSalePanel({document,knowledge}:{readonly document:CampaignDocument;readonly knowledge:ArtefactKnowledgeReader}) {
  const app=useCampaignApp(); const post=document.campaign.post_battles.find((row)=>!row.complete); const [quantity,setQuantity]=useState(0); const quote=useMemo(()=>quoteWyrdstoneSale(document,knowledge,quantity),[document,knowledge,quantity]); if(!post)return null;
  const exploration=Boolean(post.step_state?.["exploration"]); const followup=(post.pending_follow_ups??[]).some((row)=>row["type"]==="exploration_followup");
  return <section aria-label="Sell wyrdstone"><h3>04 · Sell wyrdstone</h3>{post.sale_resolved?<p role="status">Sale resolved: {post.wyrdstone_sold??0} shard(s) sold. Gold gained: {quoteWyrdstoneSale(document,knowledge,post.wyrdstone_sold??0).profit} gc.</p>:!exploration||followup?<p role="status">Complete exploration and its special result first.</p>:<><dl className="campaign-metrics"><div><dt>Available</dt><dd>{quote.available}</dd></div><div><dt>Warband size</dt><dd>{quote.warband_size}</dd></div><div><dt>Sale value</dt><dd>{quote.profit} gc</dd></div></dl><label>Shards to sell<input type="number" min={0} max={quote.available} step={1} value={quantity} onChange={(event)=>setQuantity(Math.max(0,Math.trunc(event.target.valueAsNumber||0)))}/></label><button className="primary" disabled={quantity>quote.available} onClick={()=>void app.runAction("sellWyrdstone",{quantity})}>Confirm sale once</button></>}</section>;
}

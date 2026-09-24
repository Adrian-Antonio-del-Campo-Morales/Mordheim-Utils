import { presentationOutput } from "../campaign/presentation-output";
import { textJoin, textNumber } from "../campaign/presentation-values";
import { translate } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
import { useMemo, useState } from "react";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { quoteWyrdstoneSale } from "@app/campaign/features/economy/wyrdstone-sale-workflow";
import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { NumberStepper } from "../common/NumberStepper";

export function WyrdstoneSalePanel({document,knowledge,locale: requestedLocale}:{readonly document:CampaignDocument;readonly knowledge:ArtefactKnowledgeReader;readonly locale?:"es"|"en"}) {
  const locale = useLocale(requestedLocale);
  const app=useCampaignApp(); const post=document.campaign.post_battles.find((row)=>!row.complete); const [quantity,setQuantity]=useState(0); const quote=useMemo(()=>quoteWyrdstoneSale(document,knowledge,quantity),[document,knowledge,quantity]); if(!post)return null;
  const t=({ title: translate({ key: "ui.0d6104a753fe" }, locale), resolved: translate({ key: "ui.0554f08e2cb5" }, locale), sold: translate({ key: "ui.a7f4af6e7a9b" }, locale), gained: translate({ key: "ui.1f8279053eaf" }, locale), first: translate({ key: "ui.2ba7e10279be" }, locale), available: translate({ key: "ui.9f9dfc216f33" }, locale), size: translate({ key: "ui.8d8af7acc6c8" }, locale), value: translate({ key: "ui.bbad853837ce" }, locale), shards: translate({ key: "ui.cf8c2dd3149a" }, locale), confirm: translate({ key: "ui.2a81bddb35f6" }, locale) });
  const exploration=Boolean(post.step_state?.["exploration"]); const followup=(post.pending_follow_ups??[]).some((row)=>row["type"]==="exploration_followup");
  return <section aria-label={presentationOutput(t.title)}><h3>{presentationOutput(textJoin([textNumber(4, locale, 2), t.title], " · "))}</h3>{post.sale_resolved?<p role="status">{presentationOutput(translate({ key: "history.sale", args: { quantity: post.wyrdstone_sold ?? 0, gold: quoteWyrdstoneSale(document, knowledge, post.wyrdstone_sold ?? 0).profit } }, locale))}</p>:!exploration||followup?<p role="status">{presentationOutput(t.first)}</p>:<><div className="warrior-control-row"><span>{presentationOutput(t.shards)}</span><NumberStepper locale={locale} label={translate({ key: "number.shards" }, locale)} value={quantity} min={0} max={quote.available} onChange={setQuantity}/></div><dl className="campaign-metrics"><div><dt>{presentationOutput(t.available)}</dt><dd>{presentationOutput(textNumber(quote.available, locale))}</dd></div><div><dt>{presentationOutput(t.size)}</dt><dd>{presentationOutput(textNumber(quote.warband_size, locale))}</dd></div><div><dt>{presentationOutput(t.value)}</dt><dd>{presentationOutput(textJoin([textNumber(quote.profit, locale), translate({ key: "unit.gold" }, locale)], " "))}</dd></div></dl><button className="primary" disabled={quantity>quote.available} data-disabled-reason={(quantity>quote.available ? (translate({ key: "disabled.f06f606352" }, locale)) : undefined) === undefined ? undefined : presentationOutput((quantity>quote.available ? (translate({ key: "disabled.f06f606352" }, locale)) : undefined)!)} onClick={()=>void app.runAction("sellWyrdstone",{quantity})}>{presentationOutput(t.confirm)}</button></>}</section>;
}

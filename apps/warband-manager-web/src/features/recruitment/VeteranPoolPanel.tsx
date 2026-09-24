import { textSymbol } from "../campaign/presentation-values";
import { textJoin, textNumber } from "../campaign/presentation-values";
import { presentationOutput } from "../campaign/presentation-output";
import { translate } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { DiceResolver } from "../dice/DiceResolver";

export function VeteranPoolPanel({document,locale: requestedLocale}:{readonly document:CampaignDocument;readonly locale?:"es"|"en"}) {
  const locale = useLocale(requestedLocale);
  const app=useCampaignApp(); const post=document.campaign.post_battles.find((row)=>!row.complete); if(!post)return null; const resolved=Boolean((post.step_state?.["veterans"] as Record<string,unknown>|undefined)?.["resolved"]);
  const t=({ title: translate({ key: "ui.29fbd27cb77a" }, locale), resolved: translate({ key: "ui.948987f44148" }, locale), shared: translate({ key: "ui.15bec251afe5" }, locale), first: translate({ key: "ui.e47e74e303c7" }, locale), roll: translate({ key: "ui.f84992f1cc30" }, locale), dice: translate({ key: "ui.948987f44148" }, locale) });
  return <section aria-label={presentationOutput(t.title)}><h3>{presentationOutput(textJoin([textNumber(5, locale, 2), t.title], " · "))}</h3>{resolved?<p role="status">{presentationOutput(t.resolved)} {presentationOutput(textSymbol(":"))} {presentationOutput(textNumber(post.veteran_pool??0, locale))} {presentationOutput(translate({ key: "unit.experience" }, locale))} {presentationOutput(t.shared)}</p>:!post.sale_resolved?<p role="status">{presentationOutput(t.first)}</p>:<><p>{presentationOutput(t.roll)}</p><DiceResolver locale={locale} count={2} sides={6} label={t.dice} onResolve={(dice)=>void app.runAction("applyVeteranPool",{dice})}/></>}</section>;
}

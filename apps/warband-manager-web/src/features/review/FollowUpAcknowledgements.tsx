import { translate } from "../campaign/i18n-core";
import { presentationOutput } from "../campaign/presentation-output";
import { useLocale } from "../campaign/i18n-context";
import { followUpNeedsResolution } from "@app/campaign/features/review/follow-up-acknowledgement-workflow";
import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { localizedLabel, persistedSystemText } from "../campaign/displayText";

const HANDLED=new Set(["injury_roll","injury_followup","exploration_followup","prisoner","relationship","eye_injury","hireling_upkeep","scenario_spell_reward","scenario_encampment","encounter"]);
export function FollowUpAcknowledgements({document,knowledge,locale: requestedLocale}:{readonly document:CampaignDocument; readonly knowledge?: import("@adapters/knowledge-reader/index").ArtefactKnowledgeReader;readonly locale?:"es"|"en"}){
  const locale = useLocale(requestedLocale);const app=useCampaignApp(),post=document.campaign.post_battles.find((row)=>!row.complete);if(!post)return null;const rows=(post.pending_follow_ups??[]).filter((row)=>!HANDLED.has(String(row["type"]))&&followUpNeedsResolution(row,post.acknowledgements??{}));if(!rows.length)return null;const t=({ title: translate({ key: "ui.defb949ba51f" }, locale), done: translate({ key: "ui.aa6c20bfb443" }, locale) });return <section aria-label={presentationOutput(translate({ key: "ui.defb949ba51f" }, locale))}><h3>{presentationOutput(t.title)}</h3>{rows.map((row)=><article key={String(row["id"])}><p>{presentationOutput(typeof row["description"] === "string" ? persistedSystemText(row["description"], knowledge, locale) : localizedLabel(row["type"], locale))}</p><button onClick={()=>void app.runAction("acknowledgeFollowUp",{follow_up_id:row["id"]})}>{presentationOutput(t.done)}</button></article>)}</section>;}

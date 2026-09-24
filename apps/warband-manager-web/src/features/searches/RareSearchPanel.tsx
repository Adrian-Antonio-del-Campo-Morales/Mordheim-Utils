import { presentationOutput } from "../campaign/presentation-output";
import { textJoin, textNumber, textSymbol, warriorPersonalName } from "../campaign/presentation-values";
import { translate } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { dramatisOffers, rareOffers } from "@app/campaign/features/searches/search-workflow";
import { useState } from "react";

import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { DiceResolver } from "../dice/DiceResolver";
import { knowledgeName, resourceAmount } from "../campaign/displayText";
import { KnowledgeHint } from "../campaign/KnowledgeHint";

function RarePurchase({ heroId, offer, document, knowledge, locale }: { heroId: string; offer: ReturnType<typeof rareOffers>[number]; document: CampaignDocument; knowledge: ArtefactKnowledgeReader; locale:"es"|"en" }) {
  const app = useCampaignApp();
  const [price, setPrice] = useState<number | null>(null);
  const [base, setBase] = useState("");
  const t=({ base: translate({ key: "ui.0a5477765a4e" }, locale), select: translate({ key: "ui.9f79f4628ec5" }, locale), upgrade: translate({ key: "ui.e8054e5f3695" }, locale), cost: translate({ key: "ui.d6779f3bd440" }, locale), buy: translate({ key: "ui.5a741d976891" }, locale) });
  if (offer.upgrade_multiplier) { const multiplier=offer.upgrade_multiplier; const weapons=document.campaign.inventory.filter((item)=>item.stash>0&&/weapon/i.test(item.category)).sort((a,b)=>knowledgeName(knowledge,"item",a.id,locale).localeCompare(knowledgeName(knowledge,"item",b.id,locale),locale)); const selected=weapons.find((item)=>item.id===base); return <><label>{presentationOutput(t.base)}<select value={base} onChange={(event)=>setBase(event.target.value)}><option value="">{presentationOutput(t.select)}</option>{weapons.map((item)=><option value={item.id} key={item.id}>{presentationOutput(textJoin([knowledgeName(knowledge,"item",item.id,locale), textJoin([textNumber((item.value??0)*multiplier, locale), translate({ key: "unit.gold" }, locale)])], " · "))}</option>)}</select></label><button className="primary" disabled={!selected} data-disabled-reason={(!selected ? (translate({ key: "disabled.a3f31bad59" }, locale)) : undefined) === undefined ? undefined : presentationOutput((!selected ? (translate({ key: "disabled.a3f31bad59" }, locale)) : undefined)!)} onClick={() => void app.runAction("upgradeRareSearch", { hero_id: heroId, base_item_id: base })}>{presentationOutput(textJoin([t.upgrade, selected ? textNumber((selected.value??0) * multiplier, locale) : textSymbol("—"), translate({ key: "unit.gold" }, locale)]))}</button></> }
  if (offer.price_dice && price === null) return <DiceResolver locale={locale} count={offer.price_dice[0]} sides={offer.price_dice[1]} label={<><KnowledgeHint knowledge={knowledge} kind="item" id={String(offer.item_id)} locale={locale}>{presentationOutput(knowledgeName(knowledge,"item",offer.item_id,locale))}</KnowledgeHint> {presentationOutput(t.cost)}</>} onResolve={(dice) => setPrice(offer.price_base + dice.reduce((sum, item) => sum + item, 0) * offer.price_multiplier)} />;
  const resolved = price ?? offer.price;
  return <button className="primary" disabled={resolved === null} data-disabled-reason={(resolved === null ? (translate({ key: "disabled.c09c040348" }, locale)) : undefined) === undefined ? undefined : presentationOutput((resolved === null ? (translate({ key: "disabled.c09c040348" }, locale)) : undefined)!)} onClick={() => void app.runAction("buyRareSearch", { hero_id: heroId, unit_price: resolved })}>{presentationOutput(textJoin([t.buy, textNumber(resolved, locale), translate({ key: "unit.gold" }, locale)]))}</button>;
}

function DramatisHire({ heroId, offer, locale }: { heroId: string; offer: ReturnType<typeof dramatisOffers>[number]; locale:"es"|"en" }) {
  const app = useCampaignApp();
  const label = (resources: typeof offer.fee_resources) => textJoin(resources.map(([resource, amount]) => resourceAmount(resource,amount,locale)), " + ");
  if (offer.fee_resources.length === 0) return <p role="status">{presentationOutput(translate({ key: "ui.3f55e1880f3b" }, locale))}</p>;
  return <button className="primary" onClick={() => void app.runAction("hireDramatisSearch", { hero_id: heroId })}>{presentationOutput(translate({ key: "ui.bd7aeef9804c" }, locale))} {presentationOutput(label(offer.fee_resources))}{presentationOutput(offer.upkeep_resources.length ? textJoin([translate({ key: "ui.c3da210ee5d7" }, locale), label(offer.upkeep_resources)]) : textSymbol(""))}</button>;
}

export function RareSearchPanel({ document, knowledge, locale: requestedLocale }: { readonly document: CampaignDocument; readonly knowledge: ArtefactKnowledgeReader; readonly locale?:"es"|"en" }) {
  const locale = useLocale(requestedLocale);
  const app = useCampaignApp();
  const post = document.campaign.post_battles.find((row) => !row.complete);
  if (!post) return null;
  const ready = Boolean((post.step_state?.["veterans"] as Record<string, unknown> | undefined)?.["resolved"]);
  const rare = [...rareOffers(knowledge)].map((offer)=>({...offer,name:knowledgeName(knowledge,"item",offer.item_id,locale)})).sort((a,b)=>a.name.localeCompare(b.name,locale));
  const dramatis = [...dramatisOffers(document, knowledge)].map((offer)=>({...offer,name:knowledgeName(knowledge,"hireling",offer.profile_id,locale)})).sort((a,b)=>a.name.localeCompare(b.name,locale));
  const heroes = document.campaign.warriors.filter((row) => row.kind === "hero").sort((a,b)=>a.name.localeCompare(b.name,locale));
  const t=({ title: translate({ key: "ui.d6458c18ae36" }, locale), first: translate({ key: "ui.73ce2dd9595c" }, locale), none: translate({ key: "ui.0f6ba7d44676" }, locale), consumed: translate({ key: "ui.8f94ae2b0665" }, locale), available: translate({ key: "ui.9f9dfc216f33" }, locale), notFound: translate({ key: "ui.d1dbf72ca9dc" }, locale), one: translate({ key: "ui.1af56ad4a772" }, locale), target: translate({ key: "ui.d03a618dab36" }, locale), no: translate({ key: "ui.e4638af521b1" }, locale), rare: translate({ key: "ui.6c336718821e" }, locale), persona: translate({ key: "ui.da4e57ef3beb" }, locale), special: translate({ key: "ui.bfc55d17248e" }, locale), unavailable: translate({ key: "ui.3011fc48a6a3" }, locale), search: translate({ key: "ui.d0988a9b0523" }, locale) });
  return <section aria-label={presentationOutput(t.title)}>
    <h3>{presentationOutput(textJoin([textNumber(6, locale, 2), t.title], " · "))}</h3>
    {!ready ? <p role="status">{presentationOutput(t.first)}</p> : heroes.length === 0 ? <p>{presentationOutput(t.none)}</p> : heroes.map((hero) => {
      const search = post.searches?.[hero.id];
      const rareOffer = rare.find((row) => row.item_id === search?.["item_id"]);
      const dramatisOffer = dramatis.find((row) => row.profile_id === search?.["profile_id"]);
      return <article className="warrior-card" key={hero.id}>
        <header><strong>{presentationOutput(warriorPersonalName(hero, locale))}</strong><b>{presentationOutput(search?.["dice"] ? search["success"] ? search["used"] ? t.consumed : t.available : t.notFound : t.one)}</b></header>
        <label>{presentationOutput(t.target)}
          <select value={String(search?.["target_id"] ?? "")} disabled={Boolean(search?.["dice"])} data-disabled-reason={(search?.["dice"] ? (translate({ key: "disabled.17091e66ce" }, locale)) : undefined) === undefined ? undefined : presentationOutput((search?.["dice"] ? (translate({ key: "disabled.17091e66ce" }, locale)) : undefined)!)} onChange={(event) => {
            const value = event.target.value;
            if (!value) void app.runAction("assignRareSearch", { hero_id: hero.id, item_id: null });
            else if (value.startsWith("rare:")) void app.runAction("assignRareSearch", { hero_id: hero.id, item_id: value.slice(5) });
            else void app.runAction("assignDramatisSearch", { hero_id: hero.id, profile_id: value.slice(9) });
          }}>
            <option value="">{presentationOutput(t.no)}</option>
            <optgroup label={presentationOutput(t.rare)}>{rare.map((offer) => <option key={offer.item_id} value={`rare:${offer.item_id}`}>{presentationOutput(textJoin([offer.name, textJoin([t.rare, textNumber(offer.rarity, locale)])], " · "))}</option>)}</optgroup>
            <optgroup label={presentationOutput(t.persona)}>{dramatis.map((offer) => <option key={offer.profile_id} value={`dramatis:${offer.profile_id}`} disabled={!offer.eligible}>{presentationOutput(textJoin([offer.name, offer.fee === null ? t.special : textJoin([textNumber(offer.fee, locale), translate({ key: "unit.gold" }, locale)]), ...(!offer.eligible ? [textJoin([t.unavailable, translate({ key: "ui.2144283c674c" }, locale)])] : [])], " · "))}</option>)}</optgroup>
          </select>
        </label>
        {search && !search["dice"] && search["kind"] === "rare" && <DiceResolver locale={locale} count={2} sides={6} label={rareOffer ? <><KnowledgeHint knowledge={knowledge} kind="item" id={String(rareOffer.item_id)} locale={locale}>{presentationOutput(rareOffer.name)}</KnowledgeHint> {presentationOutput(t.search)}</> : textJoin([t.rare, t.search])} onResolve={(dice) => void app.runAction("resolveRareSearch", { hero_id: hero.id, dice })} />}
        {search && !search["dice"] && search["kind"] === "dramatis" && <DiceResolver locale={locale} count={1} sides={6} label={textJoin([dramatisOffer ? knowledgeName(knowledge, "hireling", dramatisOffer.profile_id, locale) : t.persona, t.search])} onResolve={(dice) => void app.runAction("resolveDramatisSearch", { hero_id: hero.id, die: dice[0] })} />}
        {Boolean(search?.["success"] && !search?.["used"] && rareOffer) && rareOffer && <RarePurchase heroId={hero.id} offer={rareOffer} document={document} knowledge={knowledge} locale={locale} />}
        {Boolean(search?.["success"] && !search?.["used"] && dramatisOffer) && dramatisOffer && <DramatisHire heroId={hero.id} offer={dramatisOffer} locale={locale} />}
      </article>;
    })}
  </section>;
}

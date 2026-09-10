import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { dramatisOffers, rareOffers } from "@app/campaign/features/searches/search-workflow";
import { useState } from "react";

import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { DiceResolver } from "../dice/DiceResolver";

function RarePurchase({ heroId, offer }: { heroId: string; offer: ReturnType<typeof rareOffers>[number] }) {
  const app = useCampaignApp();
  const [price, setPrice] = useState<number | null>(null);
  if (offer.upgrade_multiplier) return <p role="status">Weapon upgrade needs base-record selection; search remains available.</p>;
  if (offer.price_dice && price === null) return <DiceResolver count={offer.price_dice[0]} sides={offer.price_dice[1]} label={`${offer.name} cost roll`} onResolve={(dice) => setPrice(offer.price_base + dice.reduce((sum, item) => sum + item, 0) * offer.price_multiplier)} />;
  const resolved = price ?? offer.price;
  return <button className="primary" disabled={resolved === null} onClick={() => void app.runAction("buyRareSearch", { hero_id: heroId, unit_price: resolved })}>Buy for {resolved} gc</button>;
}

export function RareSearchPanel({ document, knowledge }: { readonly document: CampaignDocument; readonly knowledge: ArtefactKnowledgeReader }) {
  const app = useCampaignApp();
  const post = document.campaign.post_battles.find((row) => !row.complete);
  if (!post) return null;
  const ready = Boolean((post.step_state?.["veterans"] as Record<string, unknown> | undefined)?.["resolved"]);
  const rare = rareOffers(knowledge);
  const dramatis = dramatisOffers(document, knowledge);
  const heroes = document.campaign.warriors.filter((row) => row.kind === "hero");
  return <section aria-label="Rare searches">
    <h3>06 · Rare items and Dramatis</h3>
    {!ready ? <p role="status">Resolve veteran availability first.</p> : heroes.length === 0 ? <p>No Heroes available to search.</p> : heroes.map((hero) => {
      const search = post.searches?.[hero.id];
      const rareOffer = rare.find((row) => row.item_id === search?.["item_id"]);
      const dramatisOffer = dramatis.find((row) => row.profile_id === search?.["profile_id"]);
      return <article className="warrior-card" key={hero.id}>
        <header><strong>{hero.name}</strong><b>{search?.["dice"] ? search["success"] ? search["used"] ? "Consumed" : "Available" : "Not found" : "One search"}</b></header>
        <label>Search target
          <select value={String(search?.["target_id"] ?? "")} disabled={Boolean(search?.["dice"])} onChange={(event) => {
            const value = event.target.value;
            if (!value) void app.runAction("assignRareSearch", { hero_id: hero.id, item_id: null });
            else if (value.startsWith("rare:")) void app.runAction("assignRareSearch", { hero_id: hero.id, item_id: value.slice(5) });
            else void app.runAction("assignDramatisSearch", { hero_id: hero.id, profile_id: value.slice(9) });
          }}>
            <option value="">No search</option>
            <optgroup label="Rare items">{rare.map((offer) => <option key={offer.item_id} value={`rare:${offer.item_id}`}>{offer.name} · Rare {offer.rarity}</option>)}</optgroup>
            <optgroup label="Dramatis Personae">{dramatis.map((offer) => <option key={offer.profile_id} value={`dramatis:${offer.profile_id}`} disabled={!offer.eligible}>{offer.name} · {offer.fee === null ? "special fee" : `${offer.fee} gc`}{!offer.eligible ? " · unavailable" : ""}</option>)}</optgroup>
          </select>
        </label>
        {search && !search["dice"] && search["kind"] === "rare" && <DiceResolver count={2} sides={6} label={`${rareOffer?.name ?? "Rare item"} search`} onResolve={(dice) => void app.runAction("resolveRareSearch", { hero_id: hero.id, dice })} />}
        {search && !search["dice"] && search["kind"] === "dramatis" && <DiceResolver count={1} sides={6} label={`${dramatisOffer?.name ?? "Dramatis Persona"} search`} onResolve={(dice) => void app.runAction("resolveDramatisSearch", { hero_id: hero.id, die: dice[0] })} />}
        {Boolean(search?.["success"] && !search?.["used"] && rareOffer) && rareOffer && <RarePurchase heroId={hero.id} offer={rareOffer} />}
        {Boolean(search?.["success"] && !search?.["used"] && dramatisOffer) && dramatisOffer && (dramatisOffer.fee === null ? <p role="status">This hiring fee needs a desktop rule not yet represented in web.</p> : <button className="primary" onClick={() => void app.runAction("hireDramatisSearch", { hero_id: hero.id })}>Hire for {dramatisOffer.fee} gc{dramatisOffer.upkeep > 0 ? ` · upkeep ${dramatisOffer.upkeep} gc` : ""}</button>)}
      </article>;
    })}
  </section>;
}

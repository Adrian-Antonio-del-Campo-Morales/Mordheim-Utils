/**
 * Web migration hirelings surface: hirelings, exploration and
 * trading UI.
 *
 * Shows the hireable offers (hired swords / dramatis personae) with their
 * resolved eligibility verdict, fee, upkeep and rating contribution; a
 * hire button dispatches `hireHireling` through the app service. The
 * trading section lists the trading post's common offers with buy actions
 * (`buyTradingItem`) and stash sells (`sellStashItem`). Rejections surface
 * through the shell's error seam, never thrown.
 *
 * The read model lives in the application feature; this file only exports
 * components (react-refresh).
 */
import { useState } from "react";

import { useCampaignApp } from "../campaign/useCampaignApp";
import type { CampaignDocument } from "../campaign/types";
import { useHirelingsWorkflow } from "./useHirelingsWorkflow";
import type { KnowledgeListings, TradingOfferRow } from "@app/campaign/features/hirelings/hirelings-workflow";
import { DiceResolver } from "../dice/DiceResolver";
import { KnowledgeHint } from "../campaign/KnowledgeHint";

interface HirelingsPanelProps {
  readonly document: CampaignDocument;
  /** Listing-capable reader override (tests inject a fake). */
  readonly listings?: KnowledgeListings;
  readonly locale?: "es" | "en";
  readonly mode?: "all" | "hirelings" | "trading";
}

function VariableFeeHire({ offer, name, busy, locale, onHire }: { offer: ReturnType<ReturnType<typeof useHirelingsWorkflow>["hiredSwordOffers"]>[number]; name: string; busy: boolean; locale: "es" | "en"; onHire: (fee: number) => void }) {
  const [fee, setFee] = useState<number | null>(null);
  if (offer.fee_dice && fee === null) return <DiceResolver locale={locale} count={offer.fee_dice[0]} sides={offer.fee_dice[1]} label={`${name} ${locale === "es" ? "tarifa de contratación" : "hiring fee"}`} onResolve={(dice) => setFee(offer.fee_base + dice.reduce((total, die) => total + die, 0))} />;
  return <button type="button" disabled={busy || fee === null} aria-label={`${locale === "es" ? "Contratar" : "Hire"} ${name}`} onClick={() => fee !== null && onHire(fee)}>{locale === "es" ? "Contratar por" : "Hire for"} {fee} gc</button>;
}

function VariableTradingPurchase({ offer, quantity, busy, locale, onBuy }: { offer: TradingOfferRow; quantity: number; busy: boolean; locale: "es" | "en"; onBuy: (price: number) => void }) {
  const [price, setPrice] = useState<number | null>(null);
  if (offer.price_dice && price === null) return <DiceResolver locale={locale} count={offer.price_dice[0]} sides={offer.price_dice[1]} label={`${offer.name} ${locale === "es" ? "precio" : "price"}`} onResolve={(dice) => setPrice(offer.price_base + dice.reduce((total, die) => total + die, 0) * offer.price_multiplier)} />;
  return <button type="button" disabled={busy || price === null} onClick={() => price !== null && onBuy(price)}>{locale === "es" ? "Comprar" : "Buy"} {quantity} {locale === "es" ? "por" : "for"} {(price ?? 0) * quantity} gc</button>;
}

export function HirelingsPanel({ document, listings, locale = "en", mode = "all" }: HirelingsPanelProps) {
  const app = useCampaignApp();
  const workflow = useHirelingsWorkflow(listings);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [quantities, setQuantities] = useState<Record<string, number>>({});

  const offers = workflow.hiredSwordOffers(document);
  const goods = workflow.tradingOffers(document);
  const stashRows = document.campaign.inventory.filter((row) => row.stash > 0);
  const hired = document.campaign.warriors.filter((row) => row.kind === "hireling");
  const displayName = (id: string, fallback: string) => listings?.itemName(id, locale) ?? fallback;
  const resourceLabel = (rows: readonly (readonly [string, number])[]) => rows.map(([key, value]) => `${value} ${key === "gold_crowns" ? "gc" : key === "wyrdstone_fragments" ? (locale === "es" ? "piedra bruja" : "wyrdstone") : key === "treasures" ? (locale === "es" ? "tesoros" : "treasures") : locale === "es" ? "puntos de campaña" : "campaign points"}`).join(" + ");
  const t = locale === "es" ? { hired:"Espadas de alquiler",hiredOk:"Contratado",already:"Ya contratado",profiles:"PERFILES CONTRATADOS",equipment:"Equipo",skills:"Habilidades / reglas",none:"No hay mercenarios disponibles.",available:"Mercenarios disponibles",name:"Nombre",fee:"Tarifa",upkeep:"Mantenimiento",rating:"Valoración",action:"Acción",dice:"dados",hire:"Contratar",ineligible:"No disponible",excluded:"excluido por las reglas de la banda",trading:"Puesto de comercio",goods:"Objetos en venta",item:"Objeto",price:"Precio",availability:"Disponibilidad",buy:"Comprar",sales:"Vender reserva",nothing:"No hay objetos en la reserva para vender.",stash:"Reserva (una unidad por acción)",inStash:"En reserva",sell:"Vender 1",special:"precio especial" } : { hired:"Hired Swords",hiredOk:"Hired",already:"Already hired",profiles:"HIRED PROFILES",equipment:"Equipment",skills:"Skills / rules",none:"No hireling offers available.",available:"Available hired swords",name:"Name",fee:"Fee",upkeep:"Upkeep",rating:"Rating",action:"Action",dice:"dice",hire:"Hire",ineligible:"Not eligible",excluded:"excluded by warband rules",trading:"Trading Post",goods:"Goods for sale",item:"Item",price:"Price",availability:"Availability",buy:"Buy",sales:"Stash sales",nothing:"Nothing in the stash to sell.",stash:"Stash (sell one unit per action)",inStash:"In stash",sell:"Sell 1",special:"special price" };

  const hire = async (profileId: string, resolvedFee?: number) => {
    const offer = offers.find((o) => o.profile_id === profileId);
    if (!offer || !offer.eligible) return;
    setBusy(true);
    setNotice("");
    const hired = await app.runAction("hireHireling", { profile_id: profileId, fee: resolvedFee ?? offer.fee, fee_resources: offer.fee_resources, upkeep_resources: offer.upkeep_resources });
    if (hired) setNotice(`${t.hiredOk}: ${displayName(offer.profile_id, offer.name)}.`);
    setBusy(false);
  };

  const amount = (id: string, maximum = Infinity) => Math.min(maximum, Math.max(1, quantities[id] ?? 1));
  const buy = async (itemId: string, basePrice: number | null) => {
    if (basePrice === null) return;
    setBusy(true);
    await app.runAction("buyTradingItem", {
      item_id: itemId,
      name: goods.find((g) => g.item_id === itemId)?.name ?? itemId,
      unit_price: basePrice,
      quantity: amount(`buy:${itemId}`),
    });
    setBusy(false);
  };

  const sell = async (itemId: string) => {
    setBusy(true);
    await app.runAction("sellStashItem", { item_id: itemId, quantity: amount(`sell:${itemId}`, document.campaign.inventory.find((row) => row.id === itemId)?.stash ?? 1) });
    setBusy(false);
  };

  return (
    <section aria-label={locale === "es" ? "Mercenarios y comercio" : "Hirelings and Trading"} aria-busy={busy}>
      {mode !== "trading" && <><h3>{t.hired}</h3>
      {notice && <output className="success-notice" role="status">✓ {notice}</output>}
      {offers.length === 0 ? (
        <p role="status">{t.none}</p>
      ) : (
        <table>
          <caption>{t.available}</caption>
          <thead>
            <tr>
              <th scope="col">{t.name}</th><th scope="col">{t.fee}</th><th scope="col">{t.upkeep}</th><th scope="col">{t.rating}</th><th scope="col">{t.action}</th>
            </tr>
          </thead>
          <tbody>
            {offers.map((offer) => (
              <tr key={offer.offer_id}>
                <td>{displayName(offer.profile_id, offer.name)}</td>
                <td>{offer.fee_dice ? `${offer.fee_base}+${offer.fee_dice[0]}D${offer.fee_dice[1]} gc` : offer.fee_resources.length ? resourceLabel(offer.fee_resources) : t.special}</td>
                <td>{offer.upkeep_resources.length ? resourceLabel(offer.upkeep_resources) : "—"}</td>
                <td>{offer.rating}</td>
                <td>
                  {hired.some((row) => row.profile_id === offer.profile_id) ? <button type="button" disabled data-disabled-reason={t.already}>✓ {t.already}</button> : offer.eligible && offer.fee_dice ? <VariableFeeHire offer={offer} name={displayName(offer.profile_id, offer.name)} busy={busy} locale={locale} onHire={(fee) => void hire(offer.profile_id, fee)} /> : offer.eligible ? (
                    <button
                      type="button"
                      disabled={busy || (offer.fee === null && offer.fee_resources.length === 0)}
                      aria-label={`${t.hire} ${displayName(offer.profile_id, offer.name)}`}
                      onClick={() => hire(offer.profile_id)}
                    >
                      {offer.fee === null && offer.fee_resources.length === 0 ? t.special : t.hire}
                    </button>
                  ) : (
                    <span role="note">
                      {t.ineligible}: {offer.ineligible_reason ?? t.excluded}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}</>}

      {mode !== "hirelings" && <><h3>{t.trading}</h3>
      <table>
        <caption>{t.goods}</caption>
        <thead>
          <tr>
            <th scope="col">{t.item}</th><th scope="col">{t.price}</th><th scope="col">{t.availability}</th><th scope="col">{t.action}</th>
          </tr>
        </thead>
        <tbody>
          {goods.map((good) => (
            <tr key={good.offer_id}>
                <td><KnowledgeHint knowledge={listings as never} kind="item" id={good.item_id} locale={locale}>{displayName(good.item_id, good.name)}</KnowledgeHint>{good.restriction_notes.length > 0 && <small className="restriction-note">{good.restriction_notes.join(" · ")}</small>}</td>
              <td>{good.price_dice ? `${good.price_base}+${good.price_dice[0]}D${good.price_dice[1]} gc` : good.base_price === null ? t.dice : `${good.base_price} gc`}</td>
              <td>{good.availability}</td>
              <td><input aria-label={`${locale === "es" ? "Cantidad" : "Quantity"} ${displayName(good.item_id, good.name)}`} type="number" min="1" value={amount(`buy:${good.item_id}`)} onChange={(event)=>setQuantities((current)=>({...current,[`buy:${good.item_id}`]:Math.max(1,Math.trunc(event.target.valueAsNumber||1))}))} />
                {good.price_dice ? <VariableTradingPurchase offer={good} quantity={amount(`buy:${good.item_id}`)} busy={busy} locale={locale} onBuy={(price) => void buy(good.item_id, price)} /> : <button
                  type="button"
                  disabled={busy || good.base_price === null || (good.limit_per_warband !== null && (document.campaign.inventory.find((row) => row.id === good.item_id)?.owned ?? 0) >= good.limit_per_warband)}
                  aria-label={`${t.buy} ${displayName(good.item_id, good.name)}`}
                  onClick={() => buy(good.item_id, good.base_price)}
                >
                  {t.buy} {amount(`buy:${good.item_id}`)}
                </button>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>{t.sales}</h3>
      {stashRows.length === 0 ? (
        <p role="status">{t.nothing}</p>
      ) : (
        <table>
          <caption>{t.stash}</caption>
          <thead>
            <tr>
              <th scope="col">{t.item}</th><th scope="col">{t.inStash}</th><th scope="col">{t.action}</th>
            </tr>
          </thead>
          <tbody>
            {stashRows.map((row) => (
              <tr key={row.id}>
                <td><KnowledgeHint knowledge={listings as never} kind="item" id={row.id} locale={locale}>{displayName(row.id, row.name)}</KnowledgeHint></td>
                <td>{row.stash}<input aria-label={`${locale === "es" ? "Cantidad" : "Quantity"} ${displayName(row.id, row.name)} ${locale === "es" ? "de la reserva" : "from stash"}`} type="number" min="1" max={row.stash} value={amount(`sell:${row.id}`,row.stash)} onChange={(event)=>setQuantities((current)=>({...current,[`sell:${row.id}`]:Math.min(row.stash,Math.max(1,Math.trunc(event.target.valueAsNumber||1)))}))} /></td>
                <td>
                  <button
                    type="button"
                    disabled={busy}
                    aria-label={`${t.sell} ${displayName(row.id, row.name)} ${locale === "es" ? "de la reserva" : "from stash"}`}
                    onClick={() => sell(row.id)}
                  >
                  {t.sell} {amount(`sell:${row.id}`,row.stash)} · {Math.max(0, Math.floor((row.value ?? 0) / 2))*amount(`sell:${row.id}`,row.stash)} gc
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}</>}
    </section>
  );
}

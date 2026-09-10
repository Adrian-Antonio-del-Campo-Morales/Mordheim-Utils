/**
 * P6.7 (web-migration-parallel-plan.md §P6.7): hirelings, exploration and
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
import type { KnowledgeListings } from "@app/campaign/features/hirelings/hirelings-workflow";

interface HirelingsPanelProps {
  readonly document: CampaignDocument;
  /** Listing-capable reader override (tests inject a fake). */
  readonly listings?: KnowledgeListings;
  readonly locale?: "es" | "en";
}

export function HirelingsPanel({ document, listings, locale = "en" }: HirelingsPanelProps) {
  const app = useCampaignApp();
  const workflow = useHirelingsWorkflow(listings);
  const [busy, setBusy] = useState(false);

  const offers = workflow.hiredSwordOffers(document);
  const goods = workflow.tradingOffers(document);
  const stashRows = document.campaign.inventory.filter((row) => row.stash > 0);
  const displayName = (id: string, fallback: string) => listings?.itemName(id, locale) ?? fallback;
  const t = locale === "es" ? { hired:"Espadas de alquiler",none:"No hay mercenarios disponibles.",available:"Mercenarios disponibles",name:"Nombre",fee:"Tarifa",upkeep:"Mantenimiento",rating:"Valoración",action:"Acción",dice:"dados",hire:"Contratar",ineligible:"No disponible",excluded:"excluido por las reglas de la banda",trading:"Puesto de comercio",goods:"Objetos en venta",item:"Objeto",price:"Precio",availability:"Disponibilidad",buy:"Comprar",sales:"Vender reserva",nothing:"No hay objetos en la reserva para vender.",stash:"Reserva (una unidad por acción)",inStash:"En reserva",sell:"Vender 1",special:"precio especial" } : { hired:"Hired Swords",none:"No hireling offers available.",available:"Available hired swords",name:"Name",fee:"Fee",upkeep:"Upkeep",rating:"Rating",action:"Action",dice:"dice",hire:"Hire",ineligible:"Not eligible",excluded:"excluded by warband rules",trading:"Trading Post",goods:"Goods for sale",item:"Item",price:"Price",availability:"Availability",buy:"Buy",sales:"Stash sales",nothing:"Nothing in the stash to sell.",stash:"Stash (sell one unit per action)",inStash:"In stash",sell:"Sell 1",special:"special price" };

  const hire = async (profileId: string) => {
    const offer = offers.find((o) => o.profile_id === profileId);
    if (!offer || !offer.eligible) return;
    setBusy(true);
    await app.runAction("hireHireling", { profile_id: profileId, fee: offer.fee, upkeep_resources: offer.upkeep ? [["gold_crowns", offer.upkeep]] : [] });
    setBusy(false);
  };

  const buy = async (itemId: string, basePrice: number | null) => {
    if (basePrice === null) return;
    setBusy(true);
    await app.runAction("buyTradingItem", {
      item_id: itemId,
      name: goods.find((g) => g.item_id === itemId)?.name ?? itemId,
      unit_price: basePrice,
      quantity: 1,
    });
    setBusy(false);
  };

  const sell = async (itemId: string) => {
    setBusy(true);
    await app.runAction("sellStashItem", { item_id: itemId, quantity: 1 });
    setBusy(false);
  };

  return (
    <section aria-label="Hirelings and Trading" aria-busy={busy}>
      <h3>{t.hired}</h3>
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
                <td>{offer.fee === null ? t.special : `${offer.fee} gc`}</td>
                <td>{offer.upkeep === null ? "—" : `${offer.upkeep} gc`}</td>
                <td>{offer.rating}</td>
                <td>
                  {offer.eligible ? (
                    <button
                      type="button"
                      disabled={busy || offer.fee === null}
                      aria-label={`${t.hire} ${displayName(offer.profile_id, offer.name)}`}
                      onClick={() => hire(offer.profile_id)}
                    >
                      {offer.fee === null ? t.special : t.hire}
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
      )}

      <h3>{t.trading}</h3>
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
              <td>{displayName(good.item_id, good.name)}{good.restriction_notes.length > 0 && <small className="restriction-note">{good.restriction_notes.join(" · ")}</small>}</td>
              <td>{good.base_price === null ? t.dice : `${good.base_price} gc`}</td>
              <td>{good.availability}</td>
              <td>
                <button
                  type="button"
                  disabled={busy || good.base_price === null || (good.limit_per_warband !== null && (document.campaign.inventory.find((row) => row.id === good.item_id)?.owned ?? 0) >= good.limit_per_warband)}
                  aria-label={`Buy ${good.name}`}
                  onClick={() => buy(good.item_id, good.base_price)}
                >
                  {t.buy}
                </button>
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
                <td>{row.name}</td>
                <td>{row.stash}</td>
                <td>
                  <button
                    type="button"
                    disabled={busy}
                    aria-label={`Sell 1 ${row.name} from stash`}
                    onClick={() => sell(row.id)}
                  >
                  {t.sell} · {Math.max(0, Math.floor((row.value ?? 0) / 2))} gc
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

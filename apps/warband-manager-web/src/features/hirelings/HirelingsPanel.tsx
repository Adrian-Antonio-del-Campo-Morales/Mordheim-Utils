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
}

export function HirelingsPanel({ document, listings }: HirelingsPanelProps) {
  const app = useCampaignApp();
  const workflow = useHirelingsWorkflow(listings);
  const [busy, setBusy] = useState(false);

  const offers = workflow.hiredSwordOffers(document);
  const goods = workflow.tradingOffers(document);
  const stashRows = document.campaign.inventory.filter((row) => row.stash > 0);

  const hire = async (profileId: string) => {
    const offer = offers.find((o) => o.profile_id === profileId);
    if (!offer || !offer.eligible) return;
    setBusy(true);
    await app.runAction("hireHireling", { profile_id: profileId });
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
    await app.runAction("sellStashItem", { item_id: itemId, quantity: 1, unit_price: 1 });
    setBusy(false);
  };

  return (
    <section aria-label="Hirelings and Trading" aria-busy={busy}>
      <h3>Hired Swords</h3>
      {offers.length === 0 ? (
        <p role="status">No hireling offers available.</p>
      ) : (
        <table>
          <caption>Available hired swords</caption>
          <thead>
            <tr>
              <th scope="col">Name</th>
              <th scope="col">Fee</th>
              <th scope="col">Upkeep</th>
              <th scope="col">Rating</th>
              <th scope="col">Action</th>
            </tr>
          </thead>
          <tbody>
            {offers.map((offer) => (
              <tr key={offer.offer_id}>
                <td>{offer.name}</td>
                <td>{offer.fee === null ? "dice" : `${offer.fee} gc`}</td>
                <td>{offer.upkeep === null ? "—" : `${offer.upkeep} gc`}</td>
                <td>{offer.rating}</td>
                <td>
                  {offer.eligible ? (
                    <button
                      type="button"
                      disabled={busy}
                      aria-label={`Hire ${offer.name}`}
                      onClick={() => hire(offer.profile_id)}
                    >
                      Hire
                    </button>
                  ) : (
                    <span role="note">
                      Not eligible: {offer.ineligible_reason ?? "excluded by warband rules"}
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <h3>Trading Post</h3>
      <table>
        <caption>Goods for sale</caption>
        <thead>
          <tr>
            <th scope="col">Item</th>
            <th scope="col">Price</th>
            <th scope="col">Availability</th>
            <th scope="col">Action</th>
          </tr>
        </thead>
        <tbody>
          {goods.map((good) => (
            <tr key={good.offer_id}>
              <td>{good.name}</td>
              <td>{good.base_price === null ? "dice" : `${good.base_price} gc`}</td>
              <td>{good.availability}</td>
              <td>
                <button
                  type="button"
                  disabled={busy || good.base_price === null}
                  aria-label={`Buy ${good.name}`}
                  onClick={() => buy(good.item_id, good.base_price)}
                >
                  Buy
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>Stash sales</h3>
      {stashRows.length === 0 ? (
        <p role="status">Nothing in the stash to sell.</p>
      ) : (
        <table>
          <caption>Stash (sell one unit per action)</caption>
          <thead>
            <tr>
              <th scope="col">Item</th>
              <th scope="col">In stash</th>
              <th scope="col">Action</th>
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
                    Sell 1
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

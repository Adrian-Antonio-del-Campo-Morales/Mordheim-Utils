import { textDice, textJoin, textNumber, textSymbol, type PresentationValue } from "../campaign/presentation-values";
import { presentationOutput } from "../campaign/presentation-output";
import { resourceAmount } from "../campaign/displayText";
import { translate } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
import { unavailableText } from "@adapters/knowledge-reader/presentation";
/**
 * Hireling, exploration and trading presentation.
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
import type { HirelingOfferRow, KnowledgeListings, TradingOfferRow } from "@app/campaign/features/hirelings/hirelings-workflow";
import { DiceResolver } from "../dice/DiceResolver";
import { KnowledgeHint } from "../campaign/KnowledgeHint";
import { NumberStepper } from "../common/NumberStepper";

interface HirelingsPanelProps {
  readonly document: CampaignDocument;
  /** Listing-capable reader override (tests inject a fake). */
  readonly listings?: KnowledgeListings;
  readonly locale?: "es" | "en";
  readonly mode?: "all" | "hirelings" | "trading";
  readonly showTradingTitle?: boolean;
}

function eligibilityReason(offer: HirelingOfferRow, listings: KnowledgeListings | undefined, locale: "es" | "en"): PresentationValue {
  if (offer.ineligible_rule_id === "static") return translate({ key: "ui.e3da81ebd3f3" }, locale);
  if (offer.ineligible_kind === "needs_variant") return translate({ key: "ui.3c070fd48f40" }, locale);
  if (!offer.ineligible_rule_id) return translate({ key: "ui.2aa6b5a863cc" }, locale);
  const result = listings?.resolveKbText?.({ kind: "rule", id: offer.ineligible_rule_id, profileId: offer.profile_id }, "effect", locale);
  return result?.ok ? result.text : unavailableText(locale);
}

function VariableFeeHire({ offer, name, busy, locale, onHire }: { offer: ReturnType<ReturnType<typeof useHirelingsWorkflow>["hiredSwordOffers"]>[number]; name: PresentationValue; busy: boolean; locale: "es" | "en"; onHire: (fee: number) => void }) {
  const [fee, setFee] = useState<number | null>(null);
  if (offer.fee_dice && fee === null) return <DiceResolver locale={locale} count={offer.fee_dice[0]} sides={offer.fee_dice[1]} label={textJoin([name, translate({ key: "ui.60e491668715" }, locale)])} onResolve={(dice) => setFee(offer.fee_base + dice.reduce((total, die) => total + die, 0))} />;
  return <button type="button" disabled={busy || fee === null} data-disabled-reason={busy ? presentationOutput(translate({ key: "disabled.23ccf48766" }, locale)) : fee === null ? presentationOutput(translate({ key: "disabled.06bdd7e9c4" }, locale)) : undefined} aria-label={presentationOutput(textJoin([translate({ key: "ui.aa663a910be2" }, locale), name]))} onClick={() => fee !== null && onHire(fee)}>{presentationOutput(textJoin([translate({ key: "ui.bd7aeef9804c" }, locale), textNumber(fee, locale), translate({ key: "unit.gold" }, locale)]))}</button>;
}

function VariableTradingPurchase({ offer, name, quantity, busy, locale, onBuy }: { offer: TradingOfferRow; name: PresentationValue; quantity: number; busy: boolean; locale: "es" | "en"; onBuy: (price: number) => void }) {
  const [price, setPrice] = useState<number | null>(null);
  if (offer.price_dice && price === null) return <DiceResolver locale={locale} count={offer.price_dice[0]} sides={offer.price_dice[1]} label={textJoin([name, translate({ key: "ui.324065ab2794" }, locale)])} onResolve={(dice) => setPrice(offer.price_base + dice.reduce((total, die) => total + die, 0) * offer.price_multiplier)} />;
  return <button type="button" disabled={busy || price === null} data-disabled-reason={busy ? presentationOutput(translate({ key: "disabled.23ccf48766" }, locale)) : price === null ? presentationOutput(translate({ key: "disabled.c09c040348" }, locale)) : undefined} onClick={() => price !== null && onBuy(price)}>{presentationOutput(textJoin([translate({ key: "ui.ee094da2d5dd" }, locale), textNumber(quantity, locale), translate({ key: "ui.ad3d0d47b7f4" }, locale), textNumber((price ?? 0) * quantity, locale), translate({ key: "unit.gold" }, locale)]))}</button>;
}

type EquipmentOption = { readonly items?: readonly string[]; readonly from?: readonly string[]; readonly count?: number };

function equipmentOptions(listings: KnowledgeListings | undefined, profileId: string): readonly EquipmentOption[] {
  const profiles = listings?.campaignSection("hirelings")["profiles"];
  const profile = Array.isArray(profiles) ? profiles.find((row) => row && typeof row === "object" && (row as Record<string, unknown>)["id"] === profileId) as Record<string, unknown> | undefined : undefined;
  const equipment = profile?.["equipment"] as Record<string, unknown> | undefined;
  const choice = Array.isArray(equipment?.["choices"]) ? equipment?.["choices"][0] as Record<string, unknown> : undefined;
  if (choice?.["choose"] !== 1 || !Array.isArray(choice["options"])) return [];
  return choice["options"].flatMap((option): EquipmentOption[] => {
    if (!option || typeof option !== "object") return [];
    const row = option as Record<string, unknown>;
    if (Array.isArray(row["items"])) {
      const items = row["items"].flatMap((item) => {
        const entry = item as Record<string, unknown>;
        const id = typeof entry["item_id"] === "string" ? entry["item_id"] : null;
        const count = Number((entry["quantity"] as Record<string, unknown> | undefined)?.["value"] ?? 1);
        return id ? Array.from({ length: count }, () => id) : [];
      });
      return items.length ? [{ items }] : [];
    }
    const from = Array.isArray(row["from_item_ids"]) ? row["from_item_ids"].filter((id): id is string => typeof id === "string") : [];
    return Number.isInteger(row["choose_items"]) && from.length ? [{ from, count: Number(row["choose_items"])}] : [];
  });
}

function sameItems(left: readonly string[], right: readonly string[]): boolean {
  return left.length === right.length && left.every((id) => left.filter((value) => value === id).length === right.filter((value) => value === id).length);
}

export function HirelingsPanel({ document, listings, locale: requestedLocale, mode = "all", showTradingTitle = true }: HirelingsPanelProps) {
  const locale = useLocale(requestedLocale);
  const app = useCampaignApp();
  const workflow = useHirelingsWorkflow(listings);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [quantities, setQuantities] = useState<Record<string, number>>({});
  const [chosenEquipment, setChosenEquipment] = useState<Record<string, readonly string[]>>({});

  const displayName = (id: string, kind: "item" | "hireling" = "item") => { const result = listings?.resolveKbText?.({ kind, id }, "name", locale); return result?.ok ? result.text : unavailableText(locale); };
  const itemLabel = (id: string) => displayName(id);
  const offers = workflow.hiredSwordOffers(document).sort((a, b) => presentationOutput(displayName(a.profile_id, "hireling")).localeCompare(presentationOutput(displayName(b.profile_id, "hireling")), locale));
  const goods = workflow.tradingOffers(document, locale);
  const stashRows = document.campaign.inventory.filter((row) => row.stash > 0);
  const hired = document.campaign.warriors.filter((row) => row.kind === "hireling");
  const resourceLabel = (rows: readonly (readonly [string, number])[]) => textJoin(rows.map(([key, value]) => resourceAmount(key, value, locale)), " + ");
  const t = ({ hired: translate({ key: "ui.48496343c02a" }, locale), hiredOk: translate({ key: "ui.68f2b63b80e4" }, locale), already: translate({ key: "ui.6223e37fde3f" }, locale), profiles: translate({ key: "ui.bfa52c4c3f02" }, locale), equipment: translate({ key: "ui.9cd4c565ba6e" }, locale), skills: translate({ key: "ui.c966b4bf55d0" }, locale), none: translate({ key: "ui.7c192fc04c99" }, locale), available: translate({ key: "ui.a30bb9292d66" }, locale), name: translate({ key: "ui.9b9a13d3e4d1" }, locale), fee: translate({ key: "ui.e42d3a9bafa9" }, locale), upkeep: translate({ key: "ui.15e8bb635504" }, locale), rating: translate({ key: "ui.f60eeb2b86e6" }, locale), action: translate({ key: "ui.b9a0db2ec300" }, locale), dice: translate({ key: "ui.1d13e4a9ecdf" }, locale), hire: translate({ key: "ui.aa663a910be2" }, locale), ineligible: translate({ key: "ui.df8a970d0e74" }, locale), excluded: translate({ key: "ui.2aa6b5a863cc" }, locale), trading: translate({ key: "ui.284b5047984a" }, locale), goods: translate({ key: "ui.34de3f8b053c" }, locale), item: translate({ key: "ui.cf471eb26f03" }, locale), price: translate({ key: "ui.158f43d31fa9" }, locale), availability: translate({ key: "ui.a282488fda52" }, locale), buy: translate({ key: "ui.ee094da2d5dd" }, locale), sales: translate({ key: "ui.082c2e0f0e0e" }, locale), nothing: translate({ key: "ui.333a612b3b95" }, locale), stash: translate({ key: "ui.4b81c9d8a339" }, locale), inStash: translate({ key: "ui.8188fac068b5" }, locale), sell: translate({ key: "ui.2c999464170e" }, locale), special: translate({ key: "ui.25309059953e" }, locale) });

  const hire = async (profileId: string, resolvedFee?: number) => {
    const offer = offers.find((o) => o.profile_id === profileId);
    if (!offer || !offer.eligible) return;
    setBusy(true);
    setNotice(null);
    const hired = await app.runAction("hireHireling", { profile_id: profileId, fee: resolvedFee ?? offer.fee, fee_resources: offer.fee_resources, upkeep_resources: offer.upkeep_resources, chosen_item_ids: chosenEquipment[profileId], locale });
    if (hired) setNotice(offer.profile_id);
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
    <section aria-label={presentationOutput(translate({ key: "ui.056cadd6741d" }, locale))} aria-busy={busy}>
      {mode !== "trading" && <><h3>{presentationOutput(t.hired)}</h3>
      {notice && <output className="success-notice" role="status">{presentationOutput(textJoin([textSymbol("✓"), textJoin([t.hiredOk, textSymbol(":")], ""), displayName(notice, "hireling")]))}</output>}
      {offers.length === 0 ? (
        <p role="status">{presentationOutput(t.none)}</p>
      ) : (
          <table className="mobile-cards">
          <caption>{presentationOutput(t.available)}</caption>
          <thead>
            <tr>
              <th scope="col">{presentationOutput(t.name)}</th><th scope="col">{presentationOutput(t.fee)}</th><th scope="col">{presentationOutput(t.upkeep)}</th><th scope="col">{presentationOutput(t.rating)}</th><th scope="col">{presentationOutput(t.action)}</th>
            </tr>
          </thead>
          <tbody>
            {offers.map((offer) => (
              <tr key={offer.offer_id}>{(() => {
                const options = equipmentOptions(listings, offer.profile_id);
                const selected = chosenEquipment[offer.profile_id] ?? [];
                const selectionReady = options.length === 0 || options.some((option) => option.items ? sameItems(selected, option.items) : selected.length === option.count && selected.every((id) => option.from?.includes(id)));
                const setSelected = (items: readonly string[]) => setChosenEquipment((current) => ({ ...current, [offer.profile_id]: items }));
                return <>
                <td data-label={presentationOutput(t.name)}>{presentationOutput(displayName(offer.profile_id, "hireling"))}</td>
                <td data-label={presentationOutput(t.fee)}>{presentationOutput(offer.fee_dice ? textJoin([textJoin([textNumber(offer.fee_base, locale), textSymbol("+"), textDice(...offer.fee_dice, locale)], ""), translate({ key: "unit.gold" }, locale)]) : offer.fee_resources.length ? resourceLabel(offer.fee_resources) : t.special)}</td>
                <td data-label={presentationOutput(t.upkeep)}>{presentationOutput(offer.upkeep_resources.length ? resourceLabel(offer.upkeep_resources) : textSymbol("—"))}</td>
                <td data-label={presentationOutput(t.rating)}>{presentationOutput(textNumber(offer.rating, locale))}</td>
                <td data-label={presentationOutput(t.action)}>
                  {options.length > 0 && <fieldset className="hireling-equipment-choice"><legend>{presentationOutput(translate({ key: "ui.6e167b0c85f2" }, locale))}</legend>{options.map((option, index) => option.items ? <label key={index}><input type="radio" name={`hireling-equipment-${offer.profile_id}`} checked={sameItems(selected, option.items)} onChange={() => setSelected(option.items ?? [])} />{presentationOutput(textJoin(option.items.map((id) => displayName(id)), " + "))}</label> : <label key={index}><input type="radio" name={`hireling-equipment-${offer.profile_id}`} checked={selected.length === option.count && selected.every((id) => option.from?.includes(id))} onChange={() => setSelected(Array.from({ length: option.count ?? 0 }, () => option.from?.[0] ?? ""))} />{presentationOutput(translate({ key: "hireling.choose-count", args: { count: option.count ?? 0 } }, locale))}{Array.from({ length: option.count ?? 0 }, (_, slot) => <select key={slot} value={selected[slot] ?? option.from?.[0] ?? ""} onChange={(event) => { const next = selected.length === option.count ? [...selected] : Array.from({ length: option.count ?? 0 }, () => option.from?.[0] ?? ""); next[slot] = event.target.value; setSelected(next); }}>{option.from?.map((id) => <option key={id} value={id}>{presentationOutput(displayName(id))}</option>)}</select>)}</label>)}</fieldset>}
                  {hired.some((row) => row.profile_id === offer.profile_id) ? <button type="button" disabled data-disabled-reason={presentationOutput(t.already)}>{presentationOutput(textJoin([textSymbol("✓"), t.already]))}</button> : offer.eligible && offer.fee_dice ? <VariableFeeHire offer={offer} name={displayName(offer.profile_id, "hireling")} busy={busy} locale={locale} onHire={(fee) => void hire(offer.profile_id, fee)} /> : offer.eligible ? (
                    <button
                      type="button"
                      disabled={busy || !selectionReady || (offer.fee === null && offer.fee_resources.length === 0)}
                      data-disabled-reason={busy ? presentationOutput(translate({ key: "disabled.23ccf48766" }, locale)) : !selectionReady ? presentationOutput(translate({ key: "disabled.00b2460585" }, locale)) : offer.fee === null && offer.fee_resources.length === 0 ? presentationOutput(translate({ key: "disabled.bc4ab7c2d2" }, locale)) : undefined}
                      aria-label={presentationOutput(textJoin([t.hire, displayName(offer.profile_id, "hireling")]))}
                      onClick={() => hire(offer.profile_id)}
                    >
                      {presentationOutput(offer.fee === null && offer.fee_resources.length === 0 ? t.special : t.hire)}
                    </button>
                  ) : (
                    <span role="note">
                      {presentationOutput(textJoin([textJoin([t.ineligible, textSymbol(":")], ""), eligibilityReason(offer, listings, locale)]))}
                    </span>
                  )}
                </td>
                </>})()}</tr>
            ))}
          </tbody>
        </table>
      )}</>}

      {mode !== "hirelings" && <>{showTradingTitle && <h3>{presentationOutput(t.trading)}</h3>}
      <table className="mobile-cards">
        <caption>{presentationOutput(t.goods)}</caption>
        <thead>
          <tr>
            <th scope="col">{presentationOutput(t.item)}</th><th scope="col">{presentationOutput(t.price)}</th><th scope="col">{presentationOutput(t.availability)}</th><th scope="col">{presentationOutput(t.action)}</th>
          </tr>
        </thead>
        <tbody>
          {goods.map((good) => (
            <tr key={good.offer_id}>
                <td data-label={presentationOutput(t.item)}><KnowledgeHint knowledge={listings} kind="item" id={good.item_id} locale={locale}>{presentationOutput(displayName(good.item_id))}</KnowledgeHint>{good.restriction_notes.length > 0 && <small className="restriction-note">{presentationOutput(textJoin(good.restriction_notes, " · "))}</small>}</td>
              <td data-label={presentationOutput(t.price)}>{presentationOutput(good.price_dice ? textJoin([textJoin([textNumber(good.price_base, locale), textSymbol("+"), textDice(...good.price_dice, locale)], ""), translate({ key: "unit.gold" }, locale)]) : good.base_price === null ? t.dice : textJoin([textNumber(good.base_price, locale), translate({ key: "unit.gold" }, locale)]))}</td>
              <td data-label={presentationOutput(t.availability)}>{presentationOutput(good.availability === "common" ? translate({ key: "availability.common" }, locale) : unavailableText(locale))}</td>
              <td data-label={presentationOutput(t.action)}><NumberStepper locale={locale} label={textJoin([translate({ key: "number.quantity" }, locale), itemLabel(good.item_id)])} value={amount(`buy:${good.item_id}`)} min={1} onChange={(value)=>setQuantities((current)=>({...current,[`buy:${good.item_id}`]:value}))} />
                {good.price_dice ? <VariableTradingPurchase offer={good} name={displayName(good.item_id)} quantity={amount(`buy:${good.item_id}`)} busy={busy} locale={locale} onBuy={(price) => void buy(good.item_id, price)} /> : <button
                  type="button"
                  disabled={busy || good.base_price === null || (good.limit_per_warband !== null && (document.campaign.inventory.find((row) => row.id === good.item_id)?.owned ?? 0) >= good.limit_per_warband)}
                  data-disabled-reason={busy ? presentationOutput(translate({ key: "disabled.23ccf48766" }, locale)) : good.base_price === null ? presentationOutput(translate({ key: "disabled.c09c040348" }, locale)) : good.limit_per_warband !== null && (document.campaign.inventory.find((row) => row.id === good.item_id)?.owned ?? 0) >= good.limit_per_warband ? presentationOutput(translate({ key: "disabled.4f2131c121" }, locale)) : undefined}
                  aria-label={presentationOutput(textJoin([t.buy, displayName(good.item_id)]))}
                  onClick={() => buy(good.item_id, good.base_price)}
                >
                  {presentationOutput(textJoin([t.buy, textNumber(amount(`buy:${good.item_id}`), locale)]))}
                </button>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3>{presentationOutput(t.sales)}</h3>
      {stashRows.length === 0 ? (
        <p role="status">{presentationOutput(t.nothing)}</p>
      ) : (
        <table className="mobile-cards">
          <caption>{presentationOutput(t.stash)}</caption>
          <thead>
            <tr>
              <th scope="col">{presentationOutput(t.item)}</th><th scope="col">{presentationOutput(t.inStash)}</th><th scope="col">{presentationOutput(t.action)}</th>
            </tr>
          </thead>
          <tbody>
            {stashRows.map((row) => (
              <tr key={row.id}>
                <td data-label={presentationOutput(t.item)}><KnowledgeHint knowledge={listings} kind="item" id={row.id} locale={locale}>{presentationOutput(displayName(row.id))}</KnowledgeHint></td>
                <td data-label={presentationOutput(t.inStash)}>{presentationOutput(textNumber(row.stash, locale))}<NumberStepper locale={locale} label={textJoin([translate({ key: "number.quantity" }, locale), itemLabel(row.id), translate({ key: "number.stash" }, locale)])} value={amount(`sell:${row.id}`,row.stash)} min={1} max={row.stash} onChange={(value)=>setQuantities((current)=>({...current,[`sell:${row.id}`]:value}))} /></td>
                <td data-label={presentationOutput(t.action)}>
                  <button
                    type="button"
                    disabled={busy}
                    data-disabled-reason={busy ? presentationOutput(translate({ key: "disabled.23ccf48766" }, locale)) : undefined}
                    aria-label={presentationOutput(textJoin([t.sell, displayName(row.id), translate({ key: "ui.bf565444ee3a" }, locale)]))}
                    onClick={() => sell(row.id)}
                  >
                  {presentationOutput(textJoin([t.sell, textNumber(amount(`sell:${row.id}`,row.stash), locale), textSymbol("—"), textNumber(Math.max(0, Math.floor((row.value ?? 0) / 2))*amount(`sell:${row.id}`,row.stash), locale), translate({ key: "unit.gold" }, locale)]))}
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

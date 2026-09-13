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

const spanishEligibilityReasons: Readonly<Record<string, string>> = {
  "hireling.hired-sword.dwarf-troll-slayer.rule.campaign-eligibility": "Solo los Mercenarios, los Cazadores de Brujas o una banda que incluya Elfos pueden contratarlo.",
  "hireling.hired-sword.dwarf-treasure-hunter.rule.campaign-eligibility": "Solo los Mercenarios, los Cazadores de Brujas o una banda que incluya Elfos pueden contratarlo.",
  "hireling.hired-sword.runesmith-journeyman.rule.campaign-eligibility": "Solo los Mercenarios, los Cazadores de Brujas o una banda que incluya Elfos pueden contratarlo.",
  "hireling.hired-sword.elf-ranger.rule.campaign-eligibility": "Solo los Mercenarios, los Cazadores de Brujas o una banda que incluya Enanos pueden contratarlo.",
  "hireling.hired-sword.cathayan-merchant.rule.campaign-eligibility": "La banda debe incluir Humanos o Enanos.",
  "hireling.hired-sword.grave-robber.rule.campaign-eligibility": "La banda debe incluir un Vampiro, Nigromante o Liche.",
  "hireling.hired-sword.ninja-gnoblar.rule.campaign-eligibility": "No se unirá a una banda que contenga criaturas que causen miedo.",
  "hireling.hired-sword.witch-hunter.rule.campaign-eligibility": "No trabajará para una banda con un hechicero; se exceptúan los sacerdotes de Sigmar, Ulric, Taal y Morr.",
  "hireling.hired-sword.highwayman.rule.campaign-eligibility": "No puede ser contratado por una banda que tenga un Guardacaminos.",
  "hireling.hired-sword.roadwarden.rule.campaign-eligibility": "No puede ser contratado por una banda que tenga un Salteador de Caminos.",
  "hireling.hired-sword.knight-of-the-white-wolf.rule.campaign-eligibility": "No se unirá a una banda que contenga un Sacerdote Guerrero.",
  "hireling.hired-sword.shadow-warrior.rule.campaign-eligibility": "No puede ser contratado por una banda que tenga una Espada de Alquiler malvada.",
  "hireling.dramatis.dijin-katal-the-renegade-assassin.rule.campaign-eligibility": "No puede ser contratado por una banda que tenga alguna Espada de Alquiler élfica.",
  "hireling.dramatis.william-schakestange-master-bard.rule.campaign-eligibility": "Solo se unirá a bandas de alineamiento bueno.",
  "hireling.dramatis.grand-master-ippan-shu.rule.campaign-eligibility": "La banda debe incluir Humanos o Elfos.",
};

function eligibilityReason(offer: HirelingOfferRow, locale: "es" | "en", fallback: string): string {
  if (locale === "en") return offer.ineligible_reason ?? fallback;
  if (offer.ineligible_rule_id === "static") return "La banda o su grupo están excluidos por las reglas de contratación.";
  if (offer.ineligible_kind === "needs_variant") return "Selecciona la variante de Mercenarios de la banda para comprobar esta contratación.";
  if (offer.ineligible_rule_id === "hireling.dramatis.maximilian-the-mad.rule.campaign-eligibility" || offer.ineligible_rule_id === "hireling.hired-sword.warrior-priest-of-sigmar.rule.campaign-eligibility") {
    return "Los Mercenarios de Middenheim no pueden contratarlo.";
  }
  if (offer.ineligible_rule_id === "hireling.hired-sword.wolf-priest-of-ulric.rule.campaign-eligibility") {
    return "Solo los Mercenarios de Middenheim pueden contratarlo.";
  }
  return (offer.ineligible_rule_id && spanishEligibilityReasons[offer.ineligible_rule_id]) ?? fallback;
}

function VariableFeeHire({ offer, name, busy, locale, onHire }: { offer: ReturnType<ReturnType<typeof useHirelingsWorkflow>["hiredSwordOffers"]>[number]; name: string; busy: boolean; locale: "es" | "en"; onHire: (fee: number) => void }) {
  const [fee, setFee] = useState<number | null>(null);
  if (offer.fee_dice && fee === null) return <DiceResolver locale={locale} count={offer.fee_dice[0]} sides={offer.fee_dice[1]} label={`${name} ${locale === "es" ? "tarifa de contratación" : "hiring fee"}`} onResolve={(dice) => setFee(offer.fee_base + dice.reduce((total, die) => total + die, 0))} />;
  return <button type="button" disabled={busy || fee === null} data-disabled-reason={busy ? (locale === "es" ? "Espera a que termine la operación en curso." : "Wait for the current operation to finish.") : fee === null ? (locale === "es" ? "Resuelve primero la tarifa de contratación." : "Resolve the hiring fee first.") : undefined} aria-label={`${locale === "es" ? "Contratar" : "Hire"} ${name}`} onClick={() => fee !== null && onHire(fee)}>{locale === "es" ? "Contratar por" : "Hire for"} {fee} gc</button>;
}

function VariableTradingPurchase({ offer, quantity, busy, locale, onBuy }: { offer: TradingOfferRow; quantity: number; busy: boolean; locale: "es" | "en"; onBuy: (price: number) => void }) {
  const [price, setPrice] = useState<number | null>(null);
  if (offer.price_dice && price === null) return <DiceResolver locale={locale} count={offer.price_dice[0]} sides={offer.price_dice[1]} label={`${offer.name} ${locale === "es" ? "precio" : "price"}`} onResolve={(dice) => setPrice(offer.price_base + dice.reduce((total, die) => total + die, 0) * offer.price_multiplier)} />;
  return <button type="button" disabled={busy || price === null} data-disabled-reason={busy ? (locale === "es" ? "Espera a que termine la operación en curso." : "Wait for the current operation to finish.") : price === null ? (locale === "es" ? "Resuelve primero el precio del objeto." : "Resolve the item price first.") : undefined} onClick={() => price !== null && onBuy(price)}>{locale === "es" ? "Comprar" : "Buy"} {quantity} {locale === "es" ? "por" : "for"} {(price ?? 0) * quantity} gc</button>;
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

export function HirelingsPanel({ document, listings, locale = "en", mode = "all", showTradingTitle = true }: HirelingsPanelProps) {
  const app = useCampaignApp();
  const workflow = useHirelingsWorkflow(listings);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [quantities, setQuantities] = useState<Record<string, number>>({});
  const [chosenEquipment, setChosenEquipment] = useState<Record<string, readonly string[]>>({});

  const displayName = (id: string, fallback: string) => listings?.itemName(id, locale) ?? fallback;
  const offers = workflow.hiredSwordOffers(document).sort((a, b) => displayName(a.profile_id, a.name).localeCompare(displayName(b.profile_id, b.name), locale));
  const goods = workflow.tradingOffers(document);
  const stashRows = document.campaign.inventory.filter((row) => row.stash > 0);
  const hired = document.campaign.warriors.filter((row) => row.kind === "hireling");
  const resourceLabel = (rows: readonly (readonly [string, number])[]) => rows.map(([key, value]) => `${value} ${key === "gold_crowns" ? "gc" : key === "wyrdstone_fragments" ? (locale === "es" ? "piedra bruja" : "wyrdstone") : key === "treasures" ? (locale === "es" ? "tesoros" : "treasures") : locale === "es" ? "puntos de campaña" : "campaign points"}`).join(" + ");
  const t = locale === "es" ? { hired:"Espadas de alquiler",hiredOk:"Contratado",already:"Ya contratado",profiles:"PERFILES CONTRATADOS",equipment:"Equipo",skills:"Habilidades / reglas",none:"No hay mercenarios disponibles.",available:"Mercenarios disponibles",name:"Nombre",fee:"Tarifa",upkeep:"Mantenimiento",rating:"Valoración",action:"Acción",dice:"dados",hire:"Contratar",ineligible:"No disponible",excluded:"excluido por las reglas de la banda",trading:"Puesto de comercio",goods:"Objetos en venta",item:"Objeto",price:"Precio",availability:"Disponibilidad",buy:"Comprar",sales:"Vender reserva",nothing:"No hay objetos en la reserva para vender.",stash:"Reserva (una unidad por acción)",inStash:"En reserva",sell:"Vender 1",special:"precio especial" } : { hired:"Hired Swords",hiredOk:"Hired",already:"Already hired",profiles:"HIRED PROFILES",equipment:"Equipment",skills:"Skills / rules",none:"No hireling offers available.",available:"Available hired swords",name:"Name",fee:"Fee",upkeep:"Upkeep",rating:"Rating",action:"Action",dice:"dice",hire:"Hire",ineligible:"Not eligible",excluded:"excluded by warband rules",trading:"Trading Post",goods:"Goods for sale",item:"Item",price:"Price",availability:"Availability",buy:"Buy",sales:"Stash sales",nothing:"Nothing in the stash to sell.",stash:"Stash (sell one unit per action)",inStash:"In stash",sell:"Sell 1",special:"special price" };

  const hire = async (profileId: string, resolvedFee?: number) => {
    const offer = offers.find((o) => o.profile_id === profileId);
    if (!offer || !offer.eligible) return;
    setBusy(true);
    setNotice("");
    const hired = await app.runAction("hireHireling", { profile_id: profileId, fee: resolvedFee ?? offer.fee, fee_resources: offer.fee_resources, upkeep_resources: offer.upkeep_resources, chosen_item_ids: chosenEquipment[profileId] });
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
          <table className="mobile-cards">
          <caption>{t.available}</caption>
          <thead>
            <tr>
              <th scope="col">{t.name}</th><th scope="col">{t.fee}</th><th scope="col">{t.upkeep}</th><th scope="col">{t.rating}</th><th scope="col">{t.action}</th>
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
                <td data-label={t.name}>{displayName(offer.profile_id, offer.name)}</td>
                <td data-label={t.fee}>{offer.fee_dice ? `${offer.fee_base}+${offer.fee_dice[0]}D${offer.fee_dice[1]} gc` : offer.fee_resources.length ? resourceLabel(offer.fee_resources) : t.special}</td>
                <td data-label={t.upkeep}>{offer.upkeep_resources.length ? resourceLabel(offer.upkeep_resources) : "—"}</td>
                <td data-label={t.rating}>{offer.rating}</td>
                <td data-label={t.action}>
                  {options.length > 0 && <fieldset className="hireling-equipment-choice"><legend>{locale === "es" ? "Equipo inicial" : "Starting equipment"}</legend>{options.map((option, index) => option.items ? <label key={index}><input type="radio" name={`hireling-equipment-${offer.profile_id}`} checked={sameItems(selected, option.items)} onChange={() => setSelected(option.items ?? [])} />{option.items.map((id) => displayName(id, id)).join(" + ")}</label> : <label key={index}><input type="radio" name={`hireling-equipment-${offer.profile_id}`} checked={selected.length === option.count && selected.every((id) => option.from?.includes(id))} onChange={() => setSelected(Array.from({ length: option.count ?? 0 }, () => option.from?.[0] ?? ""))} />{locale === "es" ? `Elige ${option.count}: ` : `Choose ${option.count}: `}{Array.from({ length: option.count ?? 0 }, (_, slot) => <select key={slot} value={selected[slot] ?? option.from?.[0] ?? ""} onChange={(event) => { const next = selected.length === option.count ? [...selected] : Array.from({ length: option.count ?? 0 }, () => option.from?.[0] ?? ""); next[slot] = event.target.value; setSelected(next); }}>{option.from?.map((id) => <option key={id} value={id}>{displayName(id, id)}</option>)}</select>)}</label>)}</fieldset>}
                  {hired.some((row) => row.profile_id === offer.profile_id) ? <button type="button" disabled data-disabled-reason={t.already}>✓ {t.already}</button> : offer.eligible && offer.fee_dice ? <VariableFeeHire offer={offer} name={displayName(offer.profile_id, offer.name)} busy={busy} locale={locale} onHire={(fee) => void hire(offer.profile_id, fee)} /> : offer.eligible ? (
                    <button
                      type="button"
                      disabled={busy || !selectionReady || (offer.fee === null && offer.fee_resources.length === 0)}
                      data-disabled-reason={busy ? (locale === "es" ? "Espera a que termine la operación en curso." : "Wait for the current operation to finish.") : !selectionReady ? (locale === "es" ? "Elige primero el equipo inicial." : "Choose starting equipment first.") : offer.fee === null && offer.fee_resources.length === 0 ? (locale === "es" ? "Esta contratación exige una resolución especial." : "This hire requires a special resolution.") : undefined}
                      aria-label={`${t.hire} ${displayName(offer.profile_id, offer.name)}`}
                      onClick={() => hire(offer.profile_id)}
                    >
                      {offer.fee === null && offer.fee_resources.length === 0 ? t.special : t.hire}
                    </button>
                  ) : (
                    <span role="note">
                      {t.ineligible}: {eligibilityReason(offer, locale, t.excluded)}
                    </span>
                  )}
                </td>
                </>})()}</tr>
            ))}
          </tbody>
        </table>
      )}</>}

      {mode !== "hirelings" && <>{showTradingTitle && <h3>{t.trading}</h3>}
      <table className="mobile-cards">
        <caption>{t.goods}</caption>
        <thead>
          <tr>
            <th scope="col">{t.item}</th><th scope="col">{t.price}</th><th scope="col">{t.availability}</th><th scope="col">{t.action}</th>
          </tr>
        </thead>
        <tbody>
          {goods.map((good) => (
            <tr key={good.offer_id}>
                <td data-label={t.item}><KnowledgeHint knowledge={listings as never} kind="item" id={good.item_id} locale={locale}>{displayName(good.item_id, good.name)}</KnowledgeHint>{good.restriction_notes.length > 0 && <small className="restriction-note">{good.restriction_notes.join(" · ")}</small>}</td>
              <td data-label={t.price}>{good.price_dice ? `${good.price_base}+${good.price_dice[0]}D${good.price_dice[1]} gc` : good.base_price === null ? t.dice : `${good.base_price} gc`}</td>
              <td data-label={t.availability}>{good.availability}</td>
              <td data-label={t.action}><NumberStepper label={`${locale === "es" ? "Cantidad" : "Quantity"} ${displayName(good.item_id, good.name)}`} value={amount(`buy:${good.item_id}`)} min={1} onChange={(value)=>setQuantities((current)=>({...current,[`buy:${good.item_id}`]:value}))} />
                {good.price_dice ? <VariableTradingPurchase offer={good} quantity={amount(`buy:${good.item_id}`)} busy={busy} locale={locale} onBuy={(price) => void buy(good.item_id, price)} /> : <button
                  type="button"
                  disabled={busy || good.base_price === null || (good.limit_per_warband !== null && (document.campaign.inventory.find((row) => row.id === good.item_id)?.owned ?? 0) >= good.limit_per_warband)}
                  data-disabled-reason={busy ? (locale === "es" ? "Espera a que termine la operación en curso." : "Wait for the current operation to finish.") : good.base_price === null ? (locale === "es" ? "Resuelve primero el precio del objeto." : "Resolve the item price first.") : good.limit_per_warband !== null && (document.campaign.inventory.find((row) => row.id === good.item_id)?.owned ?? 0) >= good.limit_per_warband ? (locale === "es" ? "La banda ya ha alcanzado el límite de este objeto." : "The warband has reached this item's limit.") : undefined}
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
        <table className="mobile-cards">
          <caption>{t.stash}</caption>
          <thead>
            <tr>
              <th scope="col">{t.item}</th><th scope="col">{t.inStash}</th><th scope="col">{t.action}</th>
            </tr>
          </thead>
          <tbody>
            {stashRows.map((row) => (
              <tr key={row.id}>
                <td data-label={t.item}><KnowledgeHint knowledge={listings as never} kind="item" id={row.id} locale={locale}>{displayName(row.id, row.name)}</KnowledgeHint></td>
                <td data-label={t.inStash}>{row.stash}<NumberStepper label={`${locale === "es" ? "Cantidad" : "Quantity"} ${displayName(row.id, row.name)} ${locale === "es" ? "de la reserva" : "from stash"}`} value={amount(`sell:${row.id}`,row.stash)} min={1} max={row.stash} onChange={(value)=>setQuantities((current)=>({...current,[`sell:${row.id}`]:value}))} /></td>
                <td data-label={t.action}>
                  <button
                    type="button"
                    disabled={busy}
                    data-disabled-reason={busy ? (locale === "es" ? "Espera a que termine la operación en curso." : "Wait for the current operation to finish.") : undefined}
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

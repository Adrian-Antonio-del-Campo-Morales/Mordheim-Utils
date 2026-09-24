import type { CampaignDocument } from "../campaign/types";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { knowledgeName } from "../campaign/displayText";
import { translate, type Locale } from "../campaign/i18n-core";
import { localizedLabel, enumReadableValue } from "../campaign/presentation-enums";
import { textJoin, textNumber, historicalWarriorName, manualCorrectionReason, type PresentationValue } from "../campaign/presentation-values";

type Event = Readonly<Record<string, unknown>>;

// Isolated v5 compatibility. Match complete known sentences, never fragments.
function legacyFacts(event: Event): Event {
  if (event.type === undefined && (event.action === "exploration" || event.action === "sell_wyrdstone")) event = { ...event, type: event.action };
  const value = event.description ?? event.message;
  if (typeof value !== "string") return event;
  const found = /^Found (\d+) wyrdstone shards\.$/.exec(value);
  if (event.type === "exploration" && found && event.shards === undefined) return { ...event, shards: Number(found[1]) };
  const sale = /^Sold (\d+) shard\(s\) for (\d+) gc\.$/.exec(value);
  if (event.type === "sell_wyrdstone" && sale) return { ...event, quantity: event.quantity ?? Number(sale[1]), gold: event.gold ?? Number(sale[2]) };
  return event;
}

/** Saved descriptions are persistence only. No raw string can leave here. */
export function historyEventText(input: Event, document: CampaignDocument, locale: Locale, knowledge?: ArtefactKnowledgeReader): PresentationValue {
  const event = legacyFacts(input);
  const missing = () => translate({ key: "knowledge.unavailable" }, locale);
  const number = (key: string) => typeof event[key] === "number" && Number.isFinite(event[key]) ? event[key] : undefined;
  const key = event.message_key;
  if (key === "knowledge.unavailable" || key === "knowledge.description-unavailable" || key === "error.action-failed") return translate({ key }, locale);
  switch (event.type) {
    case "recruit_member": {
      const gold = number("gold");
      return gold === undefined ? missing() : translate({ key: "history.recruit-member", args: { name: historicalWarriorName(document, event, locale), gold } }, locale);
    }
    case "scenario_spell_reward": {
      if (!Array.isArray(event.spell_ids) || event.spell_ids.length !== 2 || event.spell_ids.some((id) => typeof id !== "string")) return missing();
      const spells = textJoin(event.spell_ids.map((id) => knowledgeName(knowledge, "skill", id, locale)), ", ");
      return translate({ key: "history.spell-reward", args: { name: historicalWarriorName(document, event, locale), spells } }, locale);
    }
    case "recruit": {
      const quantity = number("quantity"), gold = number("gold");
      if (quantity === undefined || gold === undefined) return missing();
      return translate({ key: "history.recruit", args: { name: historicalWarriorName(document, event, locale), profile: knowledgeName(knowledge, "profile", event.profile_id, locale), quantity, gold } }, locale);
    }
    case "upgrade_weapon": {
      const gold = number("gold");
      if (gold === undefined) return missing();
      return translate({ key: "history.upgrade", args: { name: knowledgeName(knowledge, "item", event.item_id, locale), base: knowledgeName(knowledge, "item", event.base_item_id, locale), gold } }, locale);
    }
    case "buy_item": case "buy_rare_item": case "sell_item": {
      const quantity = number("quantity"), gold = number("gold");
      if (quantity === undefined || gold === undefined) return missing();
      const name = knowledgeName(knowledge, "item", event.item_id, locale);
      return translate({ key: event.type === "sell_item" ? "history.item-sale" : "history.purchase", args: { name, quantity, gold } }, locale);
    }
    case "hire": {
      if (!Array.isArray(event.costs) || !event.costs.length) return missing();
      const name = knowledgeName(knowledge, "hireling", event.profile_id, locale);
      const costs = textJoin(event.costs.map((row) => Array.isArray(row) && row.length === 2 ? textJoin([textNumber(row[1], locale), enumReadableValue(row[0], locale)]) : missing()), " + ");
      return translate({ key: "history.hire", args: { name, costs } }, locale);
    }
    case "dismiss_member": case "dismiss_warrior": {
      const quantity = number("quantity");
      return quantity === undefined ? missing() : translate({ key: "history.dismiss", args: { name: historicalWarriorName(document, event, locale), quantity } }, locale);
    }
    case "manual_resource_correction": return textJoin([localizedLabel(event.resource, locale), textNumber(event.delta, locale), manualCorrectionReason(event, locale)]);
    case "manual_item_correction": return textJoin([knowledgeName(knowledge, "item", event.item_id, locale), textNumber(event.quantity, locale), manualCorrectionReason(event, locale)]);
    case "experience": return translate({ key: "ui.9849f41939ae" }, locale);
    case "exploration": {
      const amount = number("shards");
      return amount === undefined ? missing() : translate({ key: "history.exploration", args: { amount } }, locale);
    }
    case "sell_wyrdstone": {
      const quantity = number("quantity"), gold = number("gold");
      return quantity === undefined || gold === undefined ? missing() : translate({ key: "history.sale", args: { quantity, gold } }, locale);
    }
    case "veteran_pool": {
      const amount = number("pool");
      return amount === undefined ? missing() : translate({ key: "history.veterans", args: { amount } }, locale);
    }
    case "hireling_upkeep": {
      const name = historicalWarriorName(document, event, locale);
      if (event.pay === false) return translate({ key: "history.upkeep-unpaid", args: { name } }, locale);
      if (event.pay !== true || !Array.isArray(event.costs) || !event.costs.length) return missing();
      const costs = textJoin(event.costs.map((row) => Array.isArray(row) && row.length === 2
        ? textJoin([textNumber(row[1], locale), enumReadableValue(row[0], locale)]) : missing()), " + ");
      return translate({ key: "history.upkeep-paid", args: { name, costs } }, locale);
    }
    default: return localizedLabel(event.type ?? "event", locale);
  }
}

export function historyStepLabels(locale: Locale) {
  return (["history.step.0", "history.step.1", "history.step.2", "history.step.3", "history.step.4", "history.step.5", "history.step.6", "history.step.7"] as const).map((key) => translate({ key }, locale));
}

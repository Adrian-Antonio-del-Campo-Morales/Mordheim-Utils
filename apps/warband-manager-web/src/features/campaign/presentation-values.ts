import type { Battle, CampaignDocument, Warrior } from "./types";
import type { ResolvedKbText } from "@adapters/knowledge-reader/presentation";
import { translate, type Locale, type UiText } from "./i18n-core";
import type { EnumText } from "./presentation-enums";
import type { CatalogueText } from "@app/rules/catalogue-text";
import { adaptCharacteristicValue } from "@app/rules/distance-display";

declare const formattedTextBrand: unique symbol;
export type FormattedText = string & { readonly [formattedTextBrand]: true };
export type PresentationValue = ResolvedKbText | UiText | FormattedText | EnumText | CatalogueText;
export type PresentationSeparator = "" | " " | "\n" | ", " | " · " | " - " | " + ";

export function textJoin(values: readonly PresentationValue[], separator: PresentationSeparator = " "): FormattedText {
  return values.join(separator) as FormattedText;
}

export function textNumber(value: unknown, locale: Locale, minimumIntegerDigits: 1 | 2 = 1): FormattedText | UiText {
  return typeof value === "number" && Number.isFinite(value)
    ? new Intl.NumberFormat(locale, { useGrouping: false, maximumFractionDigits: 10, minimumIntegerDigits }).format(value) as FormattedText
    : translate({ key: "knowledge.unavailable" }, locale);
}

export function textSymbol(symbol: "" | "+" | "−" | "x" | "XP" | "(" | ")" | ":" | "—" | "vs." | "#" | "/" | "✓" | "→" | "×" | "＋" | "•••" | "·" | "◆" | "☰" | "⚙" | "▣" | "↥" | "↓" | "↶" | "▤" | "▥"): FormattedText {
  return symbol as FormattedText;
}

export function textHeading(value: PresentationValue): FormattedText {
  return value.toUpperCase().split("").join(" ") as FormattedText;
}
export function textDice(count: unknown, sides: unknown, locale: Locale): FormattedText | UiText {
  return typeof count === "number" && Number.isSafeInteger(count) && count > 0 && typeof sides === "number" && Number.isSafeInteger(sides) && sides > 0
    ? `${count === 1 ? "" : count}D${sides}` as FormattedText : translate({ key: "knowledge.unavailable" }, locale);
}

export function textDieIndex(index: unknown, locale: Locale): FormattedText | UiText {
  return typeof index === "number" && Number.isSafeInteger(index) && index > 0
    ? `D${index}` as FormattedText : translate({ key: "knowledge.unavailable" }, locale);
}

export function textDate(value: unknown, locale: Locale): FormattedText | UiText {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return translate({ key: "knowledge.unavailable" }, locale);
  const date = new Date(`${value}T00:00:00Z`);
  if (!Number.isFinite(date.valueOf()) || date.toISOString().slice(0, 10) !== value) return translate({ key: "knowledge.unavailable" }, locale);
  return new Intl.DateTimeFormat(locale, { timeZone: "UTC" }).format(date) as FormattedText;
}

// These adapters are deliberately field-specific: no arbitrary-string personal
// text constructor is exported. System snapshots never enter through them.
export function warriorPersonalName(warrior: Warrior | undefined, locale: Locale): FormattedText | UiText {
  return typeof warrior?.name === "string" ? warrior.name as FormattedText : translate({ key: "knowledge.unavailable" }, locale);
}
export function warbandPersonalName(campaign: CampaignDocument["campaign"], locale: Locale): FormattedText | UiText {
  return typeof campaign.identity?.warband_name === "string" ? campaign.identity.warband_name as FormattedText : translate({ key: "knowledge.unavailable" }, locale);
}
export function opponentPersonalName(battle: Battle, locale: Locale): FormattedText | UiText {
  return typeof battle.opponent === "string" ? battle.opponent as FormattedText : translate({ key: "knowledge.unavailable" }, locale);
}
export function campaignPersonalName(campaign: CampaignDocument["campaign"], locale: Locale): FormattedText | UiText {
  return typeof campaign.identity?.campaign_name === "string" ? campaign.identity.campaign_name as FormattedText : translate({ key: "knowledge.unavailable" }, locale);
}
export function battlePersonalNotes(battle: Battle, locale: Locale): FormattedText | UiText {
  return typeof battle.notes === "string" ? battle.notes as FormattedText : translate({ key: "knowledge.unavailable" }, locale);
}
export function battleParticipantName(battle: Battle, id: unknown, locale: Locale): FormattedText | UiText {
  const row = [...(battle.participants ?? []), ...(battle.absentees ?? [])].find((row) => row.id === id);
  return typeof row?.name === "string" ? row.name as FormattedText : translate({ key: "knowledge.unavailable" }, locale);
}
export function historicalWarriorName(document: CampaignDocument, event: Readonly<Record<string, unknown>>, locale: Locale): FormattedText | UiText {
  if (["hireling_upkeep", "recruit", "recruit_member", "scenario_spell_reward", "dismiss_member", "dismiss_warrior"].includes(String(event.type)) && typeof event.warrior_personal_name === "string") return event.warrior_personal_name as FormattedText;
  const current = document.campaign.warriors?.find((row) => row.id === event.warrior_id);
  if (current) return warriorPersonalName(current, locale);
  const historical = [...(document.campaign.states ?? [])].sort((a, b) => b.number - a.number).flatMap((state) => state.roster ?? []).find((row) => row.id === event.warrior_id);
  return warriorPersonalName(historical, locale);
}
export function manualCorrectionReason(entry: CampaignDocument["campaign"]["manual_log"][number], locale: Locale): FormattedText | UiText {
  return (entry.type === "manual_resource_correction" || entry.type === "manual_item_correction") && typeof entry.reason === "string"
    ? entry.reason as FormattedText : translate({ key: "knowledge.unavailable" }, locale);
}

export function warriorCharacteristic(warrior: Warrior, key: "M" | "WS" | "BS" | "S" | "T" | "W" | "I" | "A" | "Ld", locale: Locale): FormattedText | UiText {
  const value = warrior.stats[key];
  const modifier = warrior.stat_modifiers?.[key] ?? 0;
  if (value === undefined || value === null) return textSymbol("");
  if (typeof modifier !== "number" || !Number.isFinite(modifier)) return translate({ key: "knowledge.unavailable" }, locale);
  if (!(typeof value === "number" && Number.isFinite(value)) && !(typeof value === "string" && /^(?:\d+(?:\.\d+)?|\d*D\d+(?:[+-]\d+)?|[-*])$/.test(value))) return translate({ key: "knowledge.unavailable" }, locale);
  return adaptCharacteristicValue(key, value, locale, modifier) as FormattedText;
}

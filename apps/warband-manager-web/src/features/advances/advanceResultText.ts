import { textJoin, textNumber, textSymbol, type PresentationValue } from "../campaign/presentation-values";
import { unavailableText, type ResolvedKbText } from "@adapters/knowledge-reader/presentation";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

import { knowledgeName, knowledgeRows, localizedLabel } from "../campaign/displayText";
import { translate } from "../campaign/i18n-core";

type Locale = "es" | "en";

function skill(knowledge: ArtefactKnowledgeReader, raw: string): Readonly<Record<string, unknown>> | undefined {
  const rows = knowledgeRows(knowledge, "skill").filter((entry) => {
    const names = entry["names"] as Record<string, unknown> | undefined;
    return entry["name"] === raw || names?.en === raw;
  });
  return rows.length === 1 ? rows[0] : undefined;
}

function localizedSkillName(knowledge: ArtefactKnowledgeReader, raw: string, locale: Locale): ResolvedKbText {
  const row = skill(knowledge, raw);
  return row ? knowledgeName(knowledge, "skill", row["id"], locale) : unavailableText(locale);
}

export type AdvanceResultDetails = { readonly text: PresentationValue; readonly skillId?: string };


function structuredResult(value: unknown, knowledge: ArtefactKnowledgeReader, locale: Locale): AdvanceResultDetails | undefined {
  if (!value || typeof value !== "object") return undefined;
  const result = value as Readonly<Record<string, unknown>>;
  if (result.kind === "legacy") return { text: typeof result.text === "string" ? advanceResultText(result.text, knowledge, locale) : localizedLabel(undefined, locale) };
  if (result.kind === "advance-cap" && typeof result.characteristic === "string" && typeof result.cap === "number" && Number.isFinite(result.cap)) return { text: translate({ key: "advance.cap", args: { characteristic: localizedLabel(result.characteristic, locale), cap: result.cap } }, locale) };
  if (result.kind === "henchmen-reroll" && typeof result.total === "number" && Number.isInteger(result.total) && result.total >= 10 && result.total <= 12) return { text: translate({ key: "advance.reroll", args: { total: result.total } }, locale) };
  if (result.kind === "hero-limit" && typeof result.limit === "number" && Number.isInteger(result.limit) && result.limit >= 0) return { text: translate({ key: "advance.hero-limit", args: { limit: result.limit } }, locale) };
  if (result.kind === "group-promoted") return { text: translate({ key: "ui.247b9977b863" }, locale) };
  if (result.kind === "characteristic" && typeof result.characteristic === "string" && typeof result.amount === "number" && Number.isFinite(result.amount)) {
    return { text: textJoin([textJoin([textSymbol(result.amount > 0 ? "+" : ""), textNumber(result.amount, locale)], ""), localizedLabel(result.characteristic, locale)]) };
  }
  if (["skill", "spell", "duplicate-spell"].includes(String(result.kind)) && typeof result.id === "string") {
    const name = knowledgeName(knowledge, "skill", result.id, locale);
    if (result.kind === "duplicate-spell") {
      if (typeof result.modifier !== "number" || !Number.isFinite(result.modifier)) return { text: translate({ key: "knowledge.unavailable" }, locale) };
      return { text: translate({ key: "advance.duplicate-spell", args: { name, modifier: result.modifier } }, locale), skillId: result.id };
    }
    return { text: translate({ key: result.kind === "skill" ? "advance.skill" : "advance.spell", args: { name } }, locale), skillId: result.id };
  }
  if (result.kind === "external") return { text: translate({ key: "ui.45f2d1b58f21" }, locale) };
  return { text: localizedLabel(undefined, locale) };
}

/** Present legacy English advance outcomes in the active UI language. */
export function advanceResultText(value: unknown, knowledge: ArtefactKnowledgeReader, locale: Locale): PresentationValue {
  const structured = structuredResult(value, knowledge, locale);
  if (structured) return structured.text;
  const raw = String(value ?? "").trim();
  if (!raw) return localizedLabel(undefined, locale);
  const stat = raw.match(/^\+(\d+)\s+(.+)$/);
  if (stat) return advanceResultText({ kind: "characteristic", amount: Number(stat[1]), characteristic: stat[2] }, knowledge, locale);
  const skill = raw.match(/^Skill:\s+(.+)$/);
  if (skill) return translate({ key: "advance.skill", args: { name: localizedSkillName(knowledge, skill[1], locale) } }, locale);
  const spell = raw.match(/^Spell:\s+(.+)$/);
  if (spell) return translate({ key: "advance.spell", args: { name: localizedSkillName(knowledge, spell[1], locale) } }, locale);
  const duplicate = raw.match(/^Duplicated spell:\s+(.+)\s+\(difficulty -1\)$/);
  if (duplicate) return translate({ key: "advance.duplicate-spell", args: { name: localizedSkillName(knowledge, duplicate[1], locale), modifier: -1 } }, locale);
  if (raw === "Resolved outside the application") return translate({ key: "ui.45f2d1b58f21" }, locale);
  const rejected = raw.match(/^Result rejected:\s+(.+) is at its advance cap \((\d+)\)\.$/);
  if (rejected) return advanceResultText({ kind: "advance-cap", characteristic: rejected[1], cap: Number(rejected[2]) }, knowledge, locale);
  const reroll = raw.match(/^Rolled (\d+): the remaining Henchmen must reroll results 10-12\.$/);
  if (reroll) return advanceResultText({ kind: "henchmen-reroll", total: Number(reroll[1]) }, knowledge, locale);
  const maximum = raw.match(/^Hero maximum reached \((\d+)\); reroll this advance\.$/);
  if (maximum) return advanceResultText({ kind: "hero-limit", limit: Number(maximum[1]) }, knowledge, locale);
  if (raw === "Rolled 10-12: one member became a Hero; remaining group rerolls.") return translate({ key: "ui.247b9977b863" }, locale);
  return localizedLabel(undefined, locale);
}

/** The visible result plus a KB reference when the outcome is a skill or spell. */
export function advanceResultDetails(value: unknown, knowledge: ArtefactKnowledgeReader, locale: Locale): AdvanceResultDetails {
  const structured = structuredResult(value, knowledge, locale);
  if (structured) return structured;
  const raw = String(value ?? "").trim();
  const match = raw.match(/^(?:Skill|Spell):\s+(.+)$/) ?? raw.match(/^Duplicated spell:\s+(.+)\s+\(difficulty -1\)$/);
  const row = match ? skill(knowledge, match[1]) : undefined;
  return { text: advanceResultText(raw, knowledge, locale), ...(row && typeof row["id"] === "string" ? { skillId: row["id"] } : {}) };
}

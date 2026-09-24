import { enumReadableValue } from "./presentation-enums";
import { titleCaseDisplay, type ArtefactKnowledgeReader, type DisplayRef, type LocalizedText } from "@adapters/knowledge-reader/index";
import { unavailableText, type ResolvedKbText } from "@adapters/knowledge-reader/presentation";
import type { Warrior } from "./types";
import { translate, uiMessageForText, type UiText, type Locale } from "./i18n-core";
import { textJoin, textNumber, textSymbol, type PresentationValue } from "./presentation-values";

export { titleCaseDisplay };

export type { Locale } from "./i18n";
type DisplayKind = "band" | "profile" | "item" | "skill" | "rule" | "scenario" | "injury" | "hireling" | "lore";

const unavailableLabels: Record<Locale, string> = {
  es: translate({ key: "knowledge.unavailable" }, "es"),
  en: translate({ key: "knowledge.unavailable" }, "en"),
};

export type { DisplayRef, LocalizedText };

/** Only an explicitly resolved translation can reach a presentation surface. */
export function displayText(text: LocalizedText, locale: Locale): string {
  return text.status === "translated" && text.sourceLocale === locale ? text.text : unavailableLabels[locale];
}



export { localizedLabel } from "./presentation-enums";

const ruleDocuments = ["special-rules", "profile-special-rules", "core-combat", "conditions", "resolution", "localized-labels"];
const rowsCache = new WeakMap<ArtefactKnowledgeReader, Map<DisplayKind, readonly Readonly<Record<string, unknown>>[]>>();

export function knowledgeRows(knowledge: ArtefactKnowledgeReader | undefined, kind: DisplayKind): readonly Readonly<Record<string, unknown>>[] {
  const cached = knowledge ? rowsCache.get(knowledge)?.get(kind) : undefined;
  if (cached) return cached;
  const listed = kind !== "rule" && typeof knowledge?.list === "function" ? knowledge.list(kind) : [];
  if (kind !== "rule" && kind !== "skill") {
    if (knowledge) {
      const values = rowsCache.get(knowledge) ?? new Map();
      values.set(kind, listed);
      rowsCache.set(knowledge, values);
    }
    return listed;
  }
  const generalRules = typeof knowledge?.rulesDocument === "function"
    ? ruleDocuments.flatMap((section) => knowledge.rulesDocument(section))
    : [];
  const hirelings = typeof knowledge?.campaignSection === "function" ? knowledge.campaignSection("hirelings") : undefined;
  const hirelingRules = Array.isArray(hirelings?.rules) ? hirelings.rules as readonly Readonly<Record<string, unknown>>[] : [];
  const rules = [...generalRules, ...hirelingRules];
  const result = kind === "rule" ? rules : [...listed, ...rules];
  if (knowledge) {
    const values = rowsCache.get(knowledge) ?? new Map();
    values.set(kind, result);
    rowsCache.set(knowledge, values);
  }
  return result;
}



export function readableValue(value: unknown, locale: Locale): PresentationValue {
  if (typeof value === "number") return textNumber(value, locale);
  if (value && typeof value === "object") {
    return unavailableText(locale);
  }
  const raw = String(value ?? "").trim();
  if (!raw) return textSymbol("—");
  const key = raw.toLocaleLowerCase().replace(/[ -]+/g, "_");
  return enumReadableValue(key, locale);
}

export function knowledgeText(knowledge: ArtefactKnowledgeReader | undefined, kind: DisplayKind, id: unknown, locale: Locale, profileId?: string, bandId?: string): LocalizedText {
  if (typeof knowledge?.resolveKbText === "function") {
    const result = knowledge.resolveKbText({ kind, id: String(id ?? ""), ...(profileId ? { profileId } : {}), ...(bandId ? { bandId } : {}) }, "name", locale);
    if (result.ok) return { text: result.text, sourceLocale: locale, status: "translated" };
  }
  return { text: unavailableLabels[locale], sourceLocale: null, status: "missing" };
}

export function knowledgeName(knowledge: Partial<Pick<ArtefactKnowledgeReader, "resolveKbText">> | undefined, kind: DisplayKind, id: unknown, locale: Locale, profileId?: string, bandId?: string): ResolvedKbText {
  const result = knowledge?.resolveKbText?.({ kind, id: String(id ?? ""), ...(profileId ? { profileId } : {}), ...(bandId ? { bandId } : {}) }, "name", locale);
  return result?.ok ? result.text : unavailableText(locale);
}

export function knowledgeDescription(knowledge: Partial<Pick<ArtefactKnowledgeReader, "resolveKbText">> | undefined, ref: DisplayRef, locale: Locale): { readonly text: ResolvedKbText; readonly sourceLocale: Locale; readonly status: "translated" } | { readonly text: UiText; readonly sourceLocale: null; readonly status: "missing" } {
  for (const field of ["effect", "description", "text", "note"] as const) {
    const result = knowledge?.resolveKbText?.(ref, field, locale);
    if (result?.ok) return { text: result.text, sourceLocale: locale, status: "translated" };
    // Optional fields may be undeclared. A declared field missing its translation
    // must not be hidden by switching to a different piece of prose.
    if (!result || result.reason !== "missing-field") break;
  }
  return { text: translate({ key: "knowledge.description-unavailable" }, locale), sourceLocale: null, status: "missing" };
}

export function warriorName(_knowledge: ArtefactKnowledgeReader | undefined, warrior: { readonly name: string; readonly profile_id?: string; readonly profile_name: string }, _locale?: Locale): string {
  void _knowledge;
  void _locale;
  return warrior.name;
}

/** Abilities stored on the warrior plus profile rules missing from older saves. */
export function warriorAbilities(knowledge: ArtefactKnowledgeReader | undefined, warrior: Warrior): readonly string[] {
  const stored = warrior.skills ?? [];
  if (warrior.kind !== "hireling" || !warrior.profile_id) return stored;
  const profile = knowledge?.list("hireling").find((row) => String(row.id) === warrior.profile_id);
  const starting = Array.isArray(profile?.starting_skill_ids) ? profile.starting_skill_ids.map(String) : [];
  const rules = Array.isArray(profile?.rule_ids)
    ? profile.rule_ids.map(String).filter((id) => !id.endsWith(".rule.campaign-eligibility"))
    : [];
  return [...new Set([...stored, ...starting, ...rules])];
}

/** Convert captured v5 ability labels only at this compatibility boundary. */
export function warriorAbilityRef(knowledge: ArtefactKnowledgeReader | undefined, value: string, profileId?: string, bandId?: string): DisplayRef & { readonly kind: "skill" | "rule" } {
  const ref = knowledge?.legacyAbilityRef?.(value, profileId, bandId);
  if (ref && (ref.kind === "skill" || ref.kind === "rule")) return { ...ref, kind: ref.kind };
  return { kind: value.startsWith("skill.") || value.startsWith("spell.") ? "skill" : "rule", id: value, ...(profileId ? { profileId } : {}), ...(bandId ? { bandId } : {}) };
}

export function resourceAmount(resource: unknown, amount: unknown, locale: Locale): PresentationValue {
  return textJoin([numberText(amount, locale), enumReadableValue(resource, locale)]);
}

export function numberText(value: unknown, locale: Locale): PresentationValue {
  return textNumber(value, locale);
}

/** Isolated v5 compatibility: only exact known messages or KB captures. */
export function persistedSystemText(value: unknown, knowledge: ArtefactKnowledgeReader | undefined, locale: Locale): PresentationValue {
  const message = typeof value === "string" ? uiMessageForText(value) : undefined;
  if (message) return translate(message, locale);
  return knowledge?.legacyText(value, locale) ?? unavailableText(locale);
}

/** Resolve a variant only inside its owning original band row. */
export function variantName(knowledge: ArtefactKnowledgeReader | undefined, bandId: string, variantId: string, locale: Locale): ResolvedKbText {
  const band = knowledge?.list("band").find((row) => row.id === bandId);
  const variants = Array.isArray(band?.variants) ? band.variants : [];
  const matches = variants.filter((row: unknown) => row && typeof row === "object" && "id" in row && row.id === variantId);
  return matches.length === 1 ? knowledge!.recordText(matches[0], "name", locale) : unavailableText(locale);
}

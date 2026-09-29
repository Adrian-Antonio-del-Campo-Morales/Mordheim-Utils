import { enumReadableValue } from "./presentation-enums";
import { fieldValues, isTranslatedText, titleCaseDisplay, type ArtefactKnowledgeReader, type DisplayRef, type LocalizedText } from "@adapters/knowledge-reader/index";
import { sourceReferenceUnavailableText, unavailableText, type ResolvedKbText } from "@adapters/knowledge-reader/presentation";
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

/**
 * Battle scenario presentation. The web writer stores the canonical scenario id
 * (`scenario.skirmish`); the desktop reference writer stores the display label
 * it captured at battle time (`Skirmish`). Both resolve against the KB — the id
 * directly, the captured label by exact, unique match on the published scenario
 * names, never by parsing prose. An unresolved reference yields a specific
 * localized absence notice, never the generic one and never the raw id.
 */
export function scenarioText(knowledge: ArtefactKnowledgeReader | undefined, value: unknown, locale: Locale): PresentationValue {
  const raw = typeof value === "string" ? value.trim() : "";
  if (!raw) return translate({ key: "scenario.unavailable" }, locale);
  const direct = knowledge?.resolveKbText?.({ kind: "scenario", id: raw }, "name", locale);
  if (direct?.ok) return direct.text;
  const matches = (knowledge?.list?.("scenario") ?? []).filter((row) => Object.values(fieldValues(row, "name")).includes(raw));
  if (matches.length === 1 && knowledge?.recordText) return knowledge.recordText(matches[0], "name", locale);
  return translate({ key: "scenario.unavailable" }, locale);
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

/**
 * The published name of an ability reference, or the specific notice for a
 * reference the KB does not recognize. The generic unavailable text is never a
 * correct answer here: an ability the reader cannot resolve is an unknown
 * stored reference, not published prose.
 */
export function abilityNameText(knowledge: Partial<Pick<ArtefactKnowledgeReader, "resolveKbText">> | undefined, ref: DisplayRef, locale: Locale): ResolvedKbText {
  const result = knowledge?.resolveKbText?.(ref, "name", locale);
  return result?.ok ? result.text : sourceReferenceUnavailableText(locale);
}

/** Name of a captured ability label, resolved inside the warrior's owner context. */
export function warriorAbilityName(knowledge: ArtefactKnowledgeReader | undefined, value: string, profileId: string | undefined, bandId: string | undefined, locale: Locale): ResolvedKbText {
  return abilityNameText(knowledge, warriorAbilityRef(knowledge, value, profileId, bandId), locale);
}

/**
 * The condition detail a warrior carries. Current records persist an injury
 * result id; older campaign files captured the desktop's result label, which the
 * recognized legacy shape still names. Anything else is an unknown stored
 * reference: it shows the specific notice, never the generic unavailable text.
 */
type ConditionDetailKnowledge = Partial<Pick<ArtefactKnowledgeReader, "resolveKbText" | "list" | "isCatalogueLoaded">>;

export function conditionDetailText(knowledge: ConditionDetailKnowledge | undefined, value: unknown, locale: Locale): ResolvedKbText {
  const detail = typeof value === "string" ? value.trim() : "";
  if (!detail) return sourceReferenceUnavailableText(locale);
  const direct = knowledge?.resolveKbText?.({ kind: "injury", id: detail }, "name", locale);
  if (direct?.ok) return direct.text;
  return legacyInjuryLabel(knowledge, detail, locale) ?? sourceReferenceUnavailableText(locale);
}

/**
 * The unique published injury result a captured legacy detail names. The
 * desktop kept the mechanical suffix in the capture (`Leg Wound (M -1)`); the
 * result label is the published content, and the modifier it repeats already
 * lives in the warrior's characteristics, so the label alone is resolved.
 */
function legacyInjuryLabel(knowledge: ConditionDetailKnowledge | undefined, detail: string, locale: Locale): ResolvedKbText | undefined {
  if (!knowledge || typeof knowledge.list !== "function" || typeof knowledge.isCatalogueLoaded !== "function" || typeof knowledge.resolveKbText !== "function") return undefined;
  if (!knowledge.isCatalogueLoaded("campaign")) return undefined;
  const matches = knowledge.list("injury").filter((row) => {
    // Injury rows publish their label as `result` (the generated name mirrors
    // it); the requested locale must be published before the row can be shown.
    if (!isTranslatedText(fieldValues(row, "result")[locale])) return false;
    return (["result", "name"] as const).some((field) => Object.values(fieldValues(row, field)).some(
      (value) => Boolean(value) && (detail === value || detail.startsWith(`${value} (`)),
    ));
  });
  if (matches.length !== 1) return undefined;
  const resolved = knowledge.resolveKbText({ kind: "injury", id: String(matches[0].id ?? "") }, "name", locale);
  return resolved.ok ? resolved.text : undefined;
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

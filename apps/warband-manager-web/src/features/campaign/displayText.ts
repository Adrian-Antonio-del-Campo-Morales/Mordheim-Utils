import { resolveNameText, titleCaseDisplay, type ArtefactKnowledgeReader, type DisplayRef, type LocalizedText } from "@adapters/knowledge-reader/index";
import type { Warrior } from "./types";
import { translate, type Locale } from "./i18n-core";

export { titleCaseDisplay };

export type { Locale } from "./i18n";
type DisplayKind = "band" | "profile" | "item" | "skill" | "rule" | "scenario" | "injury" | "hireling" | "lore";

const unavailableLabels: Record<Locale, string> = {
  es: translate({ key: "knowledge.unavailable" }, "es"),
  en: translate({ key: "knowledge.unavailable" }, "en"),
};

export type { DisplayRef, LocalizedText };

/** Marks the exceptional English fallback without leaking a technical id. */
export function displayText(text: LocalizedText, locale: Locale): string {
  return text.status === "canonical-fallback" ? translate({ key: "knowledge.english-fallback", args: { text: text.text } }, locale) : text.text;
}

const labelTranslations: Record<Locale, Record<string, string>> = {
  es: {
    hero: "Héroe", henchman: "Secuaces", hireling: "Espada de alquiler", warrior: "Guerrero",
    combat: "Combate", shooting: "Disparo", academic: "Académicas", strength: "Fuerza", speed: "Velocidad", special: "Especiales",
    movement: "Movimiento", weapon_skill: "Habilidad de Armas", ballistic_skill: "Habilidad de Proyectiles", strength_stat: "Fuerza", toughness: "Resistencia", wounds: "Heridas", initiative: "Iniciativa", attacks: "Ataques", leadership: "Liderazgo", ws: "HA", bs: "HP", s: "F", t: "R", w: "H", i: "I", a: "A", ld: "L", m: "M",
    event: "Evento", exploration: "Exploración", scenario: "Escenario", roll: "Tirada", result: "Resultado",
    experience: "Experiencia", sell_wyrdstone: "Venta de piedra bruja", veteran_pool: "Reserva de veteranos", hireling_upkeep: "Mantenimiento de Espada de alquiler",
  },
  en: {
    hero: "Hero", henchman: "Henchman", hireling: "Hired Sword", warrior: "Warrior",
    combat: "Combat", shooting: "Shooting", academic: "Academic", strength: "Strength", speed: "Speed", special: "Special",
    movement: "Movement", weapon_skill: "Weapon Skill", ballistic_skill: "Ballistic Skill", toughness: "Toughness", wounds: "Wounds", initiative: "Initiative", attacks: "Attacks", leadership: "Leadership",
    event: "Event", exploration: "Exploration", scenario: "Scenario", roll: "Roll", result: "Result",
  },
};

/** Localizes stable enum/field labels without ever exposing their technical key. */
export function localizedLabel(value: unknown, locale: Locale): string {
  const raw = String(value ?? "").trim();
  if (!raw) return unavailableLabels[locale];
  const key = raw.toLocaleLowerCase().replace(/[ -]+/g, "_").replace(/[^a-z0-9_]/g, "");
  if (raw.includes(".") && !labelTranslations[locale][key]) return unavailableLabels[locale];
  return labelTranslations[locale][key] ?? titleCaseDisplay(raw.replace(/[._-]+/g, " "));
}

const ruleDocuments = ["special-rules", "profile-special-rules", "core-combat", "conditions", "resolution", "localized-labels"];
const rowsCache = new WeakMap<ArtefactKnowledgeReader, Map<DisplayKind, readonly Readonly<Record<string, unknown>>[]>>();
const rowIndexCache = new WeakMap<ArtefactKnowledgeReader, Map<DisplayKind, ReadonlyMap<string, readonly Readonly<Record<string, unknown>>[]>>>();

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

export function matchesKnowledgeId(entry: Readonly<Record<string, unknown>>, id: string): boolean {
  const stableIds = [entry.id, entry.item_id, entry.profile_id]
    .filter((value): value is string => typeof value === "string");
  if (stableIds.some((stableId) => stableId.localeCompare(id, "en", { sensitivity: "accent" }) === 0)) return true;
  const names = entry.names as Readonly<Record<string, unknown>> | undefined;
  return [entry.name, names?.en].some((name) => typeof name === "string" && name.localeCompare(id, "en", { sensitivity: "accent" }) === 0);
}

function matchingRows(knowledge: ArtefactKnowledgeReader | undefined, kind: DisplayKind, id: string, profileId?: string, bandId?: string): readonly Readonly<Record<string, unknown>>[] {
  if (!knowledge) return [];
  let byKind = rowIndexCache.get(knowledge);
  let index = byKind?.get(kind);
  if (!index) {
    const values = new Map<string, Readonly<Record<string, unknown>>[]>();
    for (const row of knowledgeRows(knowledge, kind)) {
      for (const value of [row.id, row.item_id, row.profile_id]) {
        if (typeof value === "string") values.set(value, [...(values.get(value) ?? []), row]);
      }
    }
    index = values;
    byKind ??= new Map();
    byKind.set(kind, index);
    rowIndexCache.set(knowledge, byKind);
  }
  // Injury ids identify a result inside a table, not the table itself.
  // Index those nested rows before falling back to a generic catalogue entry.
  const injuryTables = typeof knowledge.campaignSection === "function"
    ? knowledge.campaignSection("serious-injuries").tables as readonly Readonly<Record<string, unknown>>[] | undefined
    : undefined;
  const injuryRows = kind === "injury"
    ? (injuryTables ?? [])
      .flatMap((table) => Array.isArray(table.results) ? table.results as readonly Readonly<Record<string, unknown>>[] : [])
      .filter((entry) => matchesKnowledgeId(entry, id))
    : [];
  const candidates = injuryRows.length ? injuryRows : index.get(id) ?? knowledgeRows(knowledge, kind).filter((entry) => matchesKnowledgeId(entry, id));
  if (!profileId && !bandId) return candidates;
  return [...candidates].sort((left, right) => {
    const score = (row: Readonly<Record<string, unknown>>) => {
      const applies = row.applies_to as Readonly<Record<string, unknown>> | undefined;
      const profiles = Array.isArray(applies?.profile_ids) ? applies.profile_ids.map(String) : [];
      return (profileId && profiles.includes(profileId) ? 2 : 0) + (bandId && row.band_id === bandId ? 1 : 0);
    };
    return score(right) - score(left);
  });
}

const translations: Record<Locale, Record<string, string>> = {
  es: {
    win: "Victoria", victory: "Victoria", loss: "Derrota", defeat: "Derrota", draw: "Empate",
    injured: "Herido", recovered: "Recuperado", dead: "Muerto", unavailable: "No disponible",
    gold_crowns: "Coronas de Oro", wyrdstone_fragments: "Fragmentos de Piedra Bruja",
    treasures: "Tesoros", campaign_points: "Puntos de Campaña",
    eye_injury: "Herida En el Ojo", smashed_hand: "Mano Aplastada", old_battle_wound: "Vieja Herida de Guerra",
    multiple_injuries: "Heridas Múltiples", leg_wound: "Herida En la Pierna",
    arm_wound: "Herida En el Brazo", madness: "Locura", smashed_leg: "Pierna Aplastada",
    chest_wound: "Herida En el Pecho", blinded_in_one_eye: "Tuerto", nervous_condition: "Problema Nervioso",
    hand_injury: "Herida En la Mano", deep_wound: "Herida Profunda", robbed: "Robado",
    full_recovery: "Recuperación Completa", bitter_enmity: "Enemistad Acérrima", captured: "Capturado",
    hardened: "Curtido", horrible_scars: "Cicatrices Horribles", sold_to_the_pits: "Vendido a los Pozos",
    survives_against_the_odds: "Sobrevive Contra Todo Pronóstico", removed: "Eliminado",
  },
  en: {
    win: "Victory", victory: "Victory", loss: "Defeat", defeat: "Defeat", draw: "Draw",
    injured: "Injured", recovered: "Recovered", dead: "Dead", unavailable: "Unavailable",
    gold_crowns: "Gold Crowns", wyrdstone_fragments: "Wyrdstone Fragments",
    treasures: "Treasures", campaign_points: "Campaign Points",
    eye_injury: "Eye Injury", smashed_hand: "Smashed Hand", old_battle_wound: "Old Battle Wound",
  },
};

export function readableValue(value: unknown, locale: Locale): string {
  if (value && typeof value === "object") {
    const row = value as Readonly<Record<string, unknown>>;
    const localized = row[locale] ?? row["en"] ?? row["name"] ?? row["label"] ?? row["text"] ?? row["description"] ?? row["id"];
    if (typeof localized !== "string" && typeof localized !== "number") return "—";
    value = localized;
  }
  const raw = String(value ?? "").trim();
  if (!raw) return "—";
  const key = raw.toLocaleLowerCase().replace(/[ -]+/g, "_");
  const translated = translations[locale][key];
  return titleCaseDisplay(translated ?? raw);
}

export function knowledgeText(knowledge: ArtefactKnowledgeReader | undefined, kind: DisplayKind, id: unknown, locale: Locale, fallback?: unknown, profileId?: string, bandId?: string): LocalizedText {
  const stableId = String(id ?? "");
  const row = matchingRows(knowledge, kind, stableId, profileId, bandId)[0];
  if (row) {
    if (kind === "injury" && typeof row.result === "string") return { text: readableValue(row.result, locale), sourceLocale: locale, status: "translated" };
    return resolveNameText(row, locale, fallback);
  }
  if (typeof knowledge?.displayNameText === "function") return knowledge.displayNameText({ kind, id: stableId, profileId, bandId }, locale, fallback);
  const safeFallback = typeof fallback === "string" && fallback !== stableId && !/^[a-z0-9]+(?:[._:-][a-z0-9]+)+$/i.test(fallback)
    ? fallback : undefined;
  return safeFallback
    ? { text: safeFallback, sourceLocale: "en", status: locale === "en" ? "translated" : "canonical-fallback" }
    : { text: unavailableLabels[locale], sourceLocale: null, status: "missing" };
}

export function knowledgeName(knowledge: ArtefactKnowledgeReader | undefined, kind: DisplayKind, id: unknown, locale: Locale, fallback?: unknown, profileId?: string, bandId?: string): string {
  return displayText(knowledgeText(knowledge, kind, id, locale, fallback, profileId, bandId), locale);
}

export function knowledgeDescription(knowledge: ArtefactKnowledgeReader | undefined, ref: DisplayRef, locale: Locale): LocalizedText {
  const indexed = typeof knowledge?.displayDescriptionText === "function" ? knowledge.displayDescriptionText(ref, locale) : undefined;
  const row = matchingRows(knowledge, ref.kind as DisplayKind, ref.id, ref.profileId, ref.bandId)[0];
  if (row) {
    const effects = row.effects as Readonly<Record<string, unknown>> | undefined;
    const translated = [row.effect_i18n, row.description_i18n, row.text_i18n, row.note_i18n]
      .find((value): value is Readonly<Record<string, unknown>> => Boolean(value) && typeof value === "object");
    const requested = effects?.[locale] ?? translated?.[locale];
    if (typeof requested === "string" && requested.trim()) return { text: requested, sourceLocale: locale, status: "translated" };
    const canonical = effects?.en ?? row.effect ?? row.description ?? row.text ?? row.note;
    if (typeof canonical === "string" && canonical.trim()) return { text: canonical, sourceLocale: "en", status: locale === "en" ? "translated" : "canonical-fallback" };
  }
  if (indexed && indexed.status !== "missing") return indexed;
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

export function resourceAmount(resource: unknown, amount: unknown, locale: Locale): string {
  return `${Number(amount)} ${titleCaseDisplay(readableValue(resource, locale))}`;
}

import { resolveName, titleCaseDisplay, type ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { Warrior } from "./types";

export { titleCaseDisplay };

export type Locale = "es" | "en";
type DisplayKind = "band" | "profile" | "item" | "skill" | "rule" | "scenario" | "injury" | "hireling" | "lore";

const unavailableLabels: Record<Locale, string> = {
  es: "Información no disponible",
  en: "Information unavailable",
};

const labelTranslations: Record<Locale, Record<string, string>> = {
  es: {
    hero: "Héroe", henchman: "Secuaces", hireling: "Espada de alquiler", warrior: "Guerrero",
    combat: "Combate", shooting: "Disparo", academic: "Académicas", strength: "Fuerza", speed: "Velocidad", special: "Especiales",
    movement: "Movimiento", weapon_skill: "Habilidad de Armas", ballistic_skill: "Habilidad de Proyectiles", strength_stat: "Fuerza", toughness: "Resistencia", wounds: "Heridas", initiative: "Iniciativa", attacks: "Ataques", leadership: "Liderazgo",
    event: "Evento", exploration: "Exploración", scenario: "Escenario", roll: "Tirada", result: "Resultado",
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

export function knowledgeRows(knowledge: ArtefactKnowledgeReader | undefined, kind: DisplayKind): readonly Readonly<Record<string, unknown>>[] {
  const listed = kind !== "rule" && typeof knowledge?.list === "function" ? knowledge.list(kind) : [];
  if (kind !== "rule" && kind !== "skill") return listed;
  const generalRules = typeof knowledge?.rulesDocument === "function"
    ? ruleDocuments.flatMap((section) => knowledge.rulesDocument(section))
    : [];
  const hirelings = typeof knowledge?.campaignSection === "function" ? knowledge.campaignSection("hirelings") : undefined;
  const hirelingRules = Array.isArray(hirelings?.rules) ? hirelings.rules as readonly Readonly<Record<string, unknown>>[] : [];
  const rules = [...generalRules, ...hirelingRules];
  return kind === "rule" ? rules : [...listed, ...rules];
}

export function matchesKnowledgeId(entry: Readonly<Record<string, unknown>>, id: string): boolean {
  const stableId = String(entry.id ?? entry.item_id ?? entry.profile_id ?? "");
  if (stableId.localeCompare(id, "en", { sensitivity: "accent" }) === 0) return true;
  const names = entry.names as Readonly<Record<string, unknown>> | undefined;
  return [entry.name, names?.en].some((name) => typeof name === "string" && name.localeCompare(id, "en", { sensitivity: "accent" }) === 0);
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

export function knowledgeName(knowledge: ArtefactKnowledgeReader | undefined, kind: DisplayKind, id: unknown, locale: Locale, fallback?: unknown, profileId?: string, bandId?: string): string {
  const stableId = String(id ?? "");
  const row = knowledgeRows(knowledge, kind).find((entry) => matchesKnowledgeId(entry, stableId));
  if (row) {
    if (kind === "injury" && typeof row.result === "string") return readableValue(row.result, locale);
    return resolveName(row, locale);
  }
  if (typeof knowledge?.displayName === "function") return knowledge.displayName(stableId, locale, fallback ?? stableId, profileId, bandId);
  return readableValue(String(fallback ?? stableId).replace(/[._-]+/g, " "), locale);
}

export function warriorName(knowledge: ArtefactKnowledgeReader | undefined, warrior: { readonly name: string; readonly profile_id?: string; readonly profile_name: string }, locale: Locale): string {
  const localized = knowledgeName(knowledge, "profile", warrior.profile_id, locale, warrior.profile_name);
  const escaped = warrior.profile_name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const automatic = new RegExp(`^${escaped}( Group)?( [IVXLCDM]+)?$`, "i").exec(warrior.name);
  if (!automatic) return warrior.name;
  const group = automatic[1] ? (locale === "es" ? `Grupo de ${localized}` : `${localized} Group`) : localized;
  return `${group}${automatic[2] ?? ""}`;
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

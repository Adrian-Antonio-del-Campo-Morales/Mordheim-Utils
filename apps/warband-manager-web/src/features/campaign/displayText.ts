import { resolveName, titleCaseDisplay, type ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

export { titleCaseDisplay };

type Locale = "es" | "en";
type DisplayKind = "band" | "profile" | "item" | "skill" | "rule" | "scenario" | "injury" | "hireling";

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

export function knowledgeName(knowledge: ArtefactKnowledgeReader | undefined, kind: DisplayKind, id: unknown, locale: Locale, fallback?: unknown): string {
  const stableId = String(id ?? "");
  const ruleDocuments = ["special-rules", "profile-special-rules", "core-combat", "conditions", "resolution", "localized-labels"];
  const catalogue = kind === "rule"
    ? ruleDocuments.flatMap((section) => knowledge?.rulesDocument(section) ?? [])
    : knowledge?.list(kind) ?? [];
  const matches = (entry: Readonly<Record<string, unknown>>) => {
    if (String(entry.id ?? entry.item_id ?? entry.profile_id ?? "") === stableId) return true;
    const names = entry.names as Readonly<Record<string, unknown>> | undefined;
    return [entry.name, names?.en].some((name) => typeof name === "string" && name.localeCompare(stableId, "en", { sensitivity: "accent" }) === 0);
  };
  let row = catalogue.find(matches);
  if (!row && kind === "skill") {
    row = ruleDocuments
      .flatMap((section) => knowledge?.rulesDocument(section) ?? [])
      .find(matches);
  }
  if (row) {
    if (kind === "injury" && typeof row.result === "string") return readableValue(row.result, locale);
    return resolveName(row, locale);
  }
  return readableValue(fallback || stableId, locale);
}

export function warriorName(knowledge: ArtefactKnowledgeReader | undefined, warrior: { readonly name: string; readonly profile_id?: string; readonly profile_name: string }, locale: Locale): string {
  const localized = knowledgeName(knowledge, "profile", warrior.profile_id, locale, warrior.profile_name);
  const escaped = warrior.profile_name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const automatic = new RegExp(`^${escaped}( Group)?( [IVXLCDM]+)?$`, "i").exec(warrior.name);
  if (!automatic) return warrior.name;
  const group = automatic[1] ? (locale === "es" ? `Grupo de ${localized}` : `${localized} Group`) : localized;
  return `${group}${automatic[2] ?? ""}`;
}

export function resourceAmount(resource: unknown, amount: unknown, locale: Locale): string {
  return `${Number(amount)} ${titleCaseDisplay(readableValue(resource, locale))}`;
}

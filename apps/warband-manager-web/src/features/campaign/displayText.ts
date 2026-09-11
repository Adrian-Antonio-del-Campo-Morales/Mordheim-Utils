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
  const catalogue = kind === "rule"
    ? ["special-rules", "core-combat", "conditions", "resolution"].flatMap((section) => knowledge?.rulesDocument(section) ?? [])
    : knowledge?.list(kind) ?? [];
  let row = catalogue.find((entry) => String(entry.id ?? entry.item_id ?? entry.profile_id ?? "") === stableId);
  if (!row && kind === "skill") {
    row = ["special-rules", "core-combat", "conditions", "resolution"]
      .flatMap((section) => knowledge?.rulesDocument(section) ?? [])
      .find((entry) => String(entry.id ?? "") === stableId);
  }
  if (row) return resolveName(row, locale);
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

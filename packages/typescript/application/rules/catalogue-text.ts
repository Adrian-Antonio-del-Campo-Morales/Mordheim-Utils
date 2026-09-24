import type { ResolvedKbText } from "../../adapters/knowledge-reader/presentation";

declare const catalogueTextBrand: unique symbol;
/** Text assembled by the rules catalogue from resolved KB text and fixed UI vocabulary. */
export type CatalogueText = string & { readonly [catalogueTextBrand]: true };
export type CataloguePart = CatalogueText | ResolvedKbText;
export type CatalogueLocale = "en" | "es";

const labels = {
  "special-rules": ["Shared Rules", "Reglas compartidas"],
  "band-rules": ["Warband Rules", "Reglas de banda"],
  conditions: ["Conditions", "Estados"],
  "core-rules": ["Core Rules", "Reglas básicas"],
  skills: ["Skills", "Habilidades"],
  equipment: ["Equipment", "Equipo"],
  spells: ["Spells", "Hechizos"],
  scenarios: ["Scenarios", "Escenarios"],
  injuries: ["Serious Injuries", "Heridas graves"],
  Speed: ["Speed", "Velocidad"], Combat: ["Combat", "Combate"], Shooting: ["Shooting", "Disparo"],
  Academic: ["Academic", "Académicas"], Strength: ["Strength", "Fuerza"], Special: ["Special", "Especiales"],
  "Close Combat Weapon": ["Close Combat Weapon", "Arma de combate cuerpo a cuerpo"],
  "Ranged Weapon": ["Ranged Weapon", "Arma a distancia"], Armour: ["Armour", "Armadura"],
  "Shield Or Defence": ["Shield Or Defence", "Escudo o defensa"],
  "Combat Equipment": ["Combat Equipment", "Equipo de combate"],
  "Material Or Upgrade": ["Material Or Upgrade", "Material o mejora"],
  Hero: ["Hero", "Héroe"], Henchman: ["Henchman", "Secuaz"], Multiplayer: ["Multiplayer", "Multijugador"],
  "starting skill": ["starting skill", "habilidad inicial"],
  "skill table": ["skill table", "tabla de habilidades"],
  "starting equipment": ["starting equipment", "equipo inicial"],
  "permitted equipment": ["permitted equipment", "equipo permitido"],
  "package rule": ["package rule", "regla de banda"],
  "special rule": ["special rule", "regla especial"],
  "spell lore": ["spell lore", "saber mágico"],
  difficulty: ["difficulty", "Dificultad"],
  setting: ["Setting", "Ambientación"], mode: ["Mode", "Modalidad"], author: ["Author", "Autor"],
  experience: ["Experience", "Experiencia"], loot: ["Loot", "Botín"],
  wyrdstone: ["Wyrdstone", "Piedra bruja"], notes: ["Notes", "Notas"],
  results: ["Results:", "Resultados:"],
  "table-of": ["Table:", "Tabla de"],
  Albion: ["Albion", "Albion"], Khemri: ["Khemri", "Khemri"], Lustria: ["Lustria", "Lustria"],
  Mordheim: ["Mordheim", "Mordheim"], "The Empire": ["The Empire", "El Imperio"],
  "1v1": ["One versus one", "Uno contra uno"], multiplayer: ["Multiplayer", "Multijugador"],
} as const;

export type CatalogueLabel = keyof typeof labels;
export function catalogueLabel(key: CatalogueLabel, locale: CatalogueLocale): CatalogueText {
  return (Object.hasOwn(labels, key) ? labels[key] : ["Information unavailable", "Información no disponible"])[locale === "es" ? 1 : 0] as CatalogueText;
}
export function isCatalogueLabel(value: string): value is CatalogueLabel {
  return Object.hasOwn(labels, value);
}
export function catalogueJoin(parts: readonly CataloguePart[], separator: "" | " " | "\n" | "\n\n" | " · " | ": " | " — " = " "): CatalogueText {
  return parts.join(separator) as CatalogueText;
}
export function catalogueNumber(value: unknown): CatalogueText | null {
  if (typeof value === "number" && Number.isFinite(value)) return String(value) as CatalogueText;
  if (typeof value === "string" && /^\d+(?:-\d+)?$/.test(value)) return value as CatalogueText;
  return null;
}
export function cataloguePunctuation(value: "• " | ":" | "D"): CatalogueText {
  return value as CatalogueText;
}

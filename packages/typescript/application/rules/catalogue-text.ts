import type { ResolvedKbText } from "../../adapters/knowledge-reader/presentation";
import { unavailableText } from "../../adapters/knowledge-reader/presentation";
import { adaptCharacteristicValue } from "./distance-display";

declare const catalogueTextBrand: unique symbol;
/** Text assembled by the rules catalogue from resolved KB text and fixed UI vocabulary. */
export type CatalogueText = string & { readonly [catalogueTextBrand]: true };
export type CataloguePart = CatalogueText | ResolvedKbText;
export type CatalogueLocale = "en" | "es";

const labels = {
  "special-rules": ["Shared Rules", "Reglas compartidas"],
  "band-rules": ["Warbands", "Bandas"],
  "warband-search": ["Search warbands", "Buscar bandas"],
  "warband-empty": ["No warbands match this name.", "Ninguna banda coincide con este nombre."],
  "warband-back": ["Back to warbands", "Volver a bandas"],
  "warband-index": ["On this sheet", "En esta ficha"],
  composition: ["Composition", "Composición"], warriors: ["Warriors", "Guerreros"],
  "starting-gold": ["Starting gold", "Oro inicial"],
  "model-limits": ["Warband size", "Tamaño de banda"],
  recruitment: ["Recruitment limit", "Límite de reclutamiento"],
  "group-size": ["Group size", "Tamaño de grupo"],
  cost: ["Cost", "Coste"], crowns: ["gc", "co"],
  "starting-equipment-not-published": ["No starting equipment declared", "Sin equipo inicial declarado"],
  "no-profile-maximum": ["Up to the warband limit", "Hasta el límite de la banda"],
  "variant-only": ["Available through a variant", "Disponible mediante una variante"],
  "skill-table": ["Skill table", "Tabla de habilidades"],
  "special-abilities": ["Special abilities", "Habilidades especiales"],
  "band-special-rules": ["Warband special rules", "Reglas especiales de la banda"],
  "magic-prayers": ["Magic and prayers", "Magia y plegarias"],
  variants: ["Variants", "Variantes"], sources: ["Sources", "Fuentes"],
  recipients: ["Profiles using this list", "Perfiles que usan esta lista"],
  "recruitment-equipment": ["Recruitment equipment", "Equipo de reclutamiento"],
  "list-metadata-missing": ["The published data does not yet include full list names and notes.", "Los datos publicados aún no incluyen los nombres y notas completos de las listas."],
  "equipment-restrictions": ["Equipment restrictions", "Restricciones de equipo"],
  "restriction-text-missing": ["Restriction text is not available in this language.", "El texto de las restricciones no está disponible en este idioma."],
  "profile-rules": ["Warrior special rules", "Reglas especiales del guerrero"],
  "other-warriors": ["Other warriors", "Otros guerreros"],
  heroes: ["Heroes", "Héroes"], henchmen: ["Henchmen", "Secuaces"],
  animal: ["Animals", "Animales"], summoned: ["Summoned warriors", "Guerreros invocados"],
  "profile-bonuses": ["Characteristic bonuses", "Bonificaciones de características"],
  "equipment-access-note": ["List access remains subject to each warrior's equipment restrictions.", "El acceso a las listas está sujeto a las restricciones de equipo de cada guerrero."],
  "access-yes": ["✓", "✓"], "access-no": ["—", "—"],
  "characteristic-not-published": ["Not published", "No publicada"],
  "item-not-published": ["Item absent from the published catalogue", "Objeto ausente del catálogo publicado"],
  "racial-maximum-not-published": ["Racial maximums not published in the catalogue", "Máximos raciales no publicados en el catálogo"],
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
  "Miscellaneous Equipment": ["Miscellaneous Equipment", "Equipo diverso"],
  "armour-defences": ["Armour and defences", "Armaduras y defensas"],
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
  // A spell whose difficulty is not a number publishes the semantic value
  // `auto` (it always succeeds): it is a published meaning, never an absence.
  Automatic: ["Automatic", "Automática"],
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
export function catalogueJoin(parts: readonly CataloguePart[], separator: "" | " " | ", " | "\n" | "\n\n" | " · " | ": " | " — " = " "): CatalogueText {
  return parts.join(separator) as CatalogueText;
}
/**
 * Compose one resolved KB text with the catalogue phrases that replace its
 * canonical citations. The citation grammar and the phrase of each match come
 * from the catalogue resolver; the composition only rewrites resolved text
 * with catalogue vocabulary, so — exactly like `adaptDistanceText` — the
 * public contract returns text of the same provenance the input carried: a
 * text the grammar does not match is the resolved text itself. The
 * implementation signature stays plain `string` on purpose: neither the
 * resolved source nor the catalogue phrases pass through an `as` assertion.
 */
export function catalogueCitationText(
  text: ResolvedKbText,
  citation: RegExp,
  phraseFor: (key: string) => CatalogueText,
): ResolvedKbText | CatalogueText;
export function catalogueCitationText(
  text: ResolvedKbText,
  citation: RegExp,
  phraseFor: (key: string) => string,
): string {
  citation.lastIndex = 0;
  const matched = citation.test(text);
  citation.lastIndex = 0;
  if (!matched) return text;
  return text.replace(citation, (_match: string, key: string) => phraseFor(key));
}
export function catalogueNumber(value: unknown): CatalogueText | null {
  if (typeof value === "number" && Number.isFinite(value)) return String(value) as CatalogueText;
  if (typeof value === "string" && /^\d+(?:-\d+)?$/.test(value)) return value as CatalogueText;
  return null;
}
/**
 * Localized abbreviation of a profile characteristic. English prints the
 * canonical keys (`M`, `WS`, …, `Ld`); Spanish uses the printed abbreviations
 * (`M`, `HA`, `HP`, `F`, `R`, `H`, `I`, `A`, `L`). The overload keeps the
 * `CatalogueText` contract for callers while the body stays plain strings, as
 * `adaptDistanceText` does: no `as` assertion brands a lookup result.
 */
const characteristicLabels = {
  M: ["M", "M"], WS: ["WS", "HA"], BS: ["BS", "HP"], S: ["S", "F"],
  T: ["T", "R"], W: ["W", "H"], I: ["I", "I"], A: ["A", "A"], Ld: ["Ld", "L"],
} as const;
export type CharacteristicDisplayKey = keyof typeof characteristicLabels;
export function catalogueCharacteristicKey(key: CharacteristicDisplayKey, locale: CatalogueLocale): CatalogueText;
export function catalogueCharacteristicKey(key: CharacteristicDisplayKey, locale: CatalogueLocale): string {
  return characteristicLabels[key][locale === "es" ? 1 : 0];
}
/** Published profile value, validated before adapting the Movement unit. */
export function catalogueCharacteristic(key: string, value: unknown, locale: CatalogueLocale): CatalogueText | ResolvedKbText {
  if (value === null || value === undefined) return catalogueLabel("characteristic-not-published", locale);
  if (!(typeof value === "number" && Number.isFinite(value)) && !(typeof value === "string" && /^(?:\d+(?:\.\d+)?|\d*D\d+(?:[+-]\d+)?|[-*])$/.test(value))) return unavailableText(locale);
  return adaptCharacteristicValue(key, value, locale) as CatalogueText;
}
/**
 * A published spell difficulty: a numeric value, or the fixed semantic token
 * `auto` (the spell always succeeds) resolved through the localized label
 * vocabulary. Anything else is not a difficulty the source publishes.
 */
export function catalogueDifficulty(value: unknown, locale: CatalogueLocale): CatalogueText | null {
  const numeric = catalogueNumber(value);
  if (numeric) return numeric;
  if (typeof value === "string" && value.trim().toLocaleLowerCase() === "auto") return catalogueLabel("Automatic", locale);
  return null;
}
export function cataloguePunctuation(value: "• " | ":" | "D" | "(" | ")"): CatalogueText {
  return value as CatalogueText;
}

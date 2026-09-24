import { titleCaseDisplay } from "@adapters/knowledge-reader/index";
import { translate, type Locale, type UiText } from "./i18n-core";
declare const enumTextBrand: unique symbol;
export type EnumText = string & { readonly [enumTextBrand]: true };

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
    ws: "WS", bs: "BS", s: "S", t: "T", w: "W", i: "I", a: "A", ld: "Ld", m: "M",
    movement: "Movement", weapon_skill: "Weapon Skill", ballistic_skill: "Ballistic Skill", toughness: "Toughness", wounds: "Wounds", initiative: "Initiative", attacks: "Attacks", leadership: "Leadership",
    event: "Event", exploration: "Exploration", scenario: "Scenario", roll: "Roll", result: "Result",
  },
};

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

export function localizedLabel(value: unknown, locale: Locale): EnumText | UiText {
  if (typeof value !== "string") return translate({ key: "knowledge.unavailable" }, locale);
  const raw = value.trim();
  const key = raw.toLocaleLowerCase().replace(/[ -]+/g, "_").replace(/[^a-z0-9_]/g, "");
  const primary = labelTranslations[locale];
  const secondary = translations[locale];
  if (raw.includes(".") && !Object.hasOwn(primary, key)) return translate({ key: "knowledge.unavailable" }, locale);
  const text = Object.hasOwn(primary, key) ? primary[key] : Object.hasOwn(secondary, key) ? secondary[key] : undefined;
  return text ? text as EnumText : translate({ key: "knowledge.unavailable" }, locale);
}

export function enumReadableValue(value: unknown, locale: Locale): EnumText {
  return titleCaseDisplay(localizedLabel(value, locale)) as EnumText;
}

/**
 * Adapts Mordheim's imperial distance notation to the Spanish editorial
 * convention. The KB remains canonical in inches; this only changes text
 * presented to a Spanish reader.
 */

import type { ResolvedKbText } from "../../adapters/knowledge-reader/presentation";
export type DistanceLocale = "en" | "es";

const FIXED_DISTANCE_CM: Readonly<Record<string, string>> = {
  "0.4": "1",
  "1": "2,5",
  "2": "5",
  "3": "8",
  "4": "10",
  "5": "12",
  "6": "15",
  "7": "18",
  "8": "20",
  "9": "23",
  "10": "25",
  "12": "30",
  "16": "40",
  "18": "45",
  "20": "50",
  "24": "60",
  "30": "75",
  "36": "90",
  "48": "120",
};

const D6_DISTANCE_CM: Readonly<Record<string, string>> = {
  "": "3",
  "1": "3",
  "2": "5",
  "3": "8",
};

const BLACK_HUNGER_IDS = new Set([
  "band--clan-pestilens-special-skills-black-hunger",
  "band--skaven-special-skills-black-hunger",
  "mechanic.black-hunger",
]);

const IMPETUOUS_KNIGHT_IDS = new Set([
  "band--virtue-of-impetuous",
  "band--virtue-of-the-impetuous-knight",
]);

const DISTANCE_UNIT = '(?:"|″|”|inches?\\b)';

function adaptSpecialCase(text: string, recordId: string): string {
  if (BLACK_HUNGER_IDS.has(recordId)) {
    return text
      .replace(/1D6\s*[x×]\s*0[.,]4\s*(?:"|″|”)(?:\s*\+\s*1\s*(?:"|″|”))?/gi, "1D6+2 cm")
      .replace(/\+(?:1)?D3\s*(?:"|″|”)/gi, "+1D6+2 cm");
  }
  if (recordId === "shared-rule.waaagh") {
    return text.replace(/\+D3\s*(?:"|″|”)/gi, "+1D6+2 cm");
  }
  if (IMPETUOUS_KNIGHT_IDS.has(recordId)) {
    return text
      .replace(/1D6\s*[x×]\s*0[.,]4\s*(?:"|″|”)/gi, "1D6 cm")
      .replace(/\+(?:1)?D3\s*(?:"|″|”)/gi, "+1D6 cm");
  }
  return text;
}

/** Convert display text for the requested locale without changing English. */
export function adaptDistanceText(text: ResolvedKbText, locale: DistanceLocale, recordId?: string): ResolvedKbText;
export function adaptDistanceText(text: string, locale: DistanceLocale, recordId?: string): string;
export function adaptDistanceText(
  text: string,
  locale: DistanceLocale,
  recordId = "",
): string {
  if (locale !== "es" || text.length === 0) return text;

  let adapted = adaptSpecialCase(text, recordId);

  // This composite must be handled before the generic D6 replacement.
  adapted = adapted.replace(
    new RegExp(`\\b12\\s*\\+\\s*D6\\s*${DISTANCE_UNIT}`, "gi"),
    "30+3D6 cm",
  );

  adapted = adapted.replace(
    new RegExp(`\\b(\\d*)D6\\s*${DISTANCE_UNIT}`, "gi"),
    (match: string, count: string) => {
      const convertedCount = D6_DISTANCE_CM[count];
      return convertedCount ? `${convertedCount}D6 cm` : match;
    },
  );

  const fixedPattern = new RegExp(
    `(?<![A-Za-z0-9])((?:0[.,]4|48|36|30|24|20|18|16|12|10|9|8|7|6|5|4|3|2|1))\\s*${DISTANCE_UNIT}`,
    "gi",
  );
  adapted = adapted.replace(
    fixedPattern,
    (match: string, value: string) => {
      const converted = FIXED_DISTANCE_CM[value.replace(",", ".")];
      return converted ? `${converted} cm` : match;
    },
  );

  // Covers wording such as “Initiative in inches” after token replacements.
  return adapted.replace(/\b(?:inches?|pulgadas?)\b/gi, "cm");
}

/**
 * Render a profile characteristic. Spanish Mordheim profiles express M in
 * centimetres implicitly (M 4 becomes M 10), while storage stays canonical.
 */
export function adaptCharacteristicValue(
  characteristic: string,
  value: unknown,
  locale: DistanceLocale,
  modifier = 0,
): string {
  const numeric = Number(value);
  const adjusted = Number.isFinite(numeric)
    ? String(numeric + modifier)
    : String(value ?? "");
  if (characteristic !== "M" || locale !== "es" || adjusted.length === 0) {
    return adjusted;
  }
  return adaptDistanceText(adjusted + '"', locale).replace(/ cm$/, "");
}

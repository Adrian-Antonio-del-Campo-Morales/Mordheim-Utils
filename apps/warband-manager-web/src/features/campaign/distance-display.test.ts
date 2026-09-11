import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

import { adaptCharacteristicValue, adaptDistanceText } from "@app/rules/distance-display";

const FIXED_CASES = [
  ["0.4\"", "1 cm"],
  ["0,4\"", "1 cm"],
  ["1\"", "2,5 cm"],
  ["2\"", "5 cm"],
  ["3\"", "8 cm"],
  ["4\"", "10 cm"],
  ["6\"", "15 cm"],
  ["8\"", "20 cm"],
  ["9\"", "23 cm"],
  ["10\"", "25 cm"],
  ["12\"", "30 cm"],
  ["16\"", "40 cm"],
  ["18\"", "45 cm"],
  ["20\"", "50 cm"],
  ["24\"", "60 cm"],
  ["36\"", "90 cm"],
] as const;

const UNADAPTED_DISTANCE = /(?:\b(?:\d+(?:[.,]\d+)?|(?:\d*)D[36])\s*(?:"|″|”|inches?\b)|\b(?:inches?|pulgadas?)\b)/i;

describe("adaptDistanceText", () => {
  it.each(FIXED_CASES)("adapts %s to %s", (source, expected) => {
    expect(adaptDistanceText(source, "es")).toBe(expected);
  });

  it("adapts decimal wording, dice and composite expressions", () => {
    expect(adaptDistanceText("D6\" / 2D6\" / 3D6\" / D6 inches", "es"))
      .toBe("3D6 cm / 5D6 cm / 8D6 cm / 3D6 cm");
    expect(adaptDistanceText("Move 12+D6\" and roll +D6\".", "es"))
      .toBe("Move 30+3D6 cm and roll +3D6 cm.");
    expect(adaptDistanceText("twice their Initiative value in inches", "es"))
      .toBe("twice their Initiative value in cm");
  });

  it("applies the documented special adaptations by KB id", () => {
    expect(adaptDistanceText("May add +D3\" to his charge range.", "es", "shared-rule.waaagh"))
      .toBe("May add +1D6+2 cm to his charge range.");
    expect(adaptDistanceText("The warrior suffers 1D6 x 0,4\" + 1\".", "es", "mechanic.black-hunger"))
      .toBe("The warrior suffers 1D6+2 cm.");
    expect(adaptDistanceText("Add +1D3\" to the charge.", "es", "band--virtue-of-impetuous"))
      .toBe("Add +1D6 cm to the charge.");
    expect(adaptDistanceText("The distance is 1D6 × 0.4\".", "es", "band--virtue-of-the-impetuous-knight"))
      .toBe("The distance is 1D6 cm.");
  });

  it("leaves English text byte-for-byte unchanged", () => {
    const source = "Range 18\", D6 inches, 1D6 x 0.4\" + 1\".";
    expect(adaptDistanceText(source, "en")).toBe(source);
  });

  it("adapts M while leaving other characteristics untouched", () => {
    const cases = [
      [2, "5"], [3, "8"], [4, "10"], [5, "12"],
      [6, "15"], [7, "18"], [8, "20"], [9, "23"],
    ] as const;
    for (const [movement, expected] of cases) {
      expect(adaptCharacteristicValue("M", movement, "es")).toBe(expected);
    }
    expect(adaptCharacteristicValue("M", "2D6", "es")).toBe("5D6");
    expect(adaptCharacteristicValue("M", "3D6", "es")).toBe("8D6");
    expect(adaptCharacteristicValue("M", 4, "es", -1)).toBe("8");
    expect(adaptCharacteristicValue("M", 4, "en")).toBe("4");
    expect(adaptCharacteristicValue("WS", 4, "es")).toBe("4");
  });

  it("finds no unadapted imperial distances in KB effect text", () => {
    const artefact = JSON.parse(
      readFileSync(resolve(process.cwd(), "public/knowledge/knowledge-web.json"), "utf-8"),
    ) as unknown;
    const texts = collectEffectTexts(artefact);
    const failures = texts
      .map(({ recordId, text }) => ({
        recordId,
        source: text,
        adapted: adaptDistanceText(text, "es", recordId),
      }))
      .filter(({ adapted }) => UNADAPTED_DISTANCE.test(adapted));

    expect(failures).toEqual([]);
  });
});

function collectEffectTexts(
  value: unknown,
  inheritedId = "",
): Array<{ readonly recordId: string; readonly text: string }> {
  if (Array.isArray(value)) {
    return value.flatMap((entry) => collectEffectTexts(entry, inheritedId));
  }
  if (!value || typeof value !== "object") return [];

  const row = value as Record<string, unknown>;
  const recordId = String(row.id ?? row.item_id ?? inheritedId);
  const texts: Array<{ readonly recordId: string; readonly text: string }> = [];
  for (const [key, child] of Object.entries(row)) {
    if (["effect", "description", "text", "note"].includes(key) && typeof child === "string") {
      texts.push({ recordId, text: child });
      continue;
    }
    if ((key === "effects" || key.endsWith("_i18n")) && child && typeof child === "object") {
      for (const text of Object.values(child as Record<string, unknown>)) {
        if (typeof text === "string") texts.push({ recordId, text });
      }
      continue;
    }
    if (child && typeof child === "object") {
      texts.push(...collectEffectTexts(child, recordId));
    }
  }
  return texts;
}

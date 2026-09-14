import { describe, expect, it } from "vitest";

import { advanceResultText } from "./advanceResultText";

const knowledge = {
  list: () => [],
  rulesDocument: () => [],
  campaignSection: () => ({}),
} as never;

describe("advanceResultText", () => {
  it("localizes stored advance results and history in Spanish", () => {
    expect(advanceResultText("+1 WS", knowledge, "es")).toBe("+1 HA");
    expect(advanceResultText("Skill: Swordmaster", knowledge, "es")).toBe("Habilidad: Swordmaster");
    expect(advanceResultText("Result rejected: WS is at its advance cap (5).", knowledge, "es")).toBe("Resultado rechazado: HA ha alcanzado su límite de avance (5).");
  });
});

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
    expect(advanceResultText("Skill: Swordmaster", knowledge, "es")).toBe("Habilidad: Información no disponible");
    expect(advanceResultText("Result rejected: WS is at its advance cap (5).", knowledge, "es")).toBe("Resultado rechazado: HA ha alcanzado su límite de avance (5).");
  });
  it("renders structured history in the current language without captured prose", () => {
    const event = { kind: "advance-cap", characteristic: "WS", cap: 5, message: "internal_tag" };
    expect(advanceResultText(event, knowledge, "es")).toBe("Resultado rechazado: HA ha alcanzado su límite de avance (5).");
    expect(advanceResultText(event, knowledge, "en")).toBe("Result rejected: WS is at its advance cap (5).");
    expect(advanceResultText({ kind: "hero-limit", limit: "internal_tag" }, knowledge, "es")).toBe("Información no disponible");
    expect(advanceResultText({ kind: "legacy", text: "internal_tag" }, knowledge, "en")).toBe("Information unavailable");
  });
});

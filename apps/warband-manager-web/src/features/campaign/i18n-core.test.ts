import { describe, expect, it } from "vitest";
import { PresentationIndex } from "@adapters/knowledge-reader/presentation";
import { translate } from "./i18n-core";
import { presentationOutput } from "./presentation-output";

describe("typed presentation messages", () => {
  const index = new PresentationIndex([{ ref: { kind: "skill", id: "private.skill" }, source: "skills/0", fields: { name: { es: "Luz", en: "Light" } } }]);
  it.each(["es", "en", "es"] as const)("composes resolved names and numeric arguments in %s", (locale) => {
    const result = index.resolve({ kind: "skill", id: "private.skill" }, "name", locale);
    if (!result.ok) throw new Error("Fixture resolution failed");
    const text = presentationOutput(translate({ key: "advance.duplicate-spell", args: { name: result.text, modifier: -1 } }, locale));
    expect(text).toBe(locale === "es" ? "Hechizo duplicado: Luz (dificultad -1)" : "Duplicated spell: Light (difficulty -1)");
    expect(text).not.toContain("private.skill");
  });
  it("does not render non-finite numeric message parameters", () => {
    const result = index.resolve({ kind: "skill", id: "private.skill" }, "name", "es");
    if (!result.ok) throw new Error("Fixture resolution failed");
    expect(translate({ key: "knowledge.quantity", args: { name: result.text, quantity: NaN } }, "es")).toBe("Información no disponible");
  });
});

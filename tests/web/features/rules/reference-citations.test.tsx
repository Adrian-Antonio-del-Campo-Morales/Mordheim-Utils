/**
 * F050 — rendered regression for canonical `campaign.limit.racial-maximum.*`
 * citations: the real reference sheet shows the linked maximum profile in both
 * locales and never the catalogue id, including multi-citation and repeated
 * references. The exact rendered sentence is pinned, so a future change cannot
 * remove the id by weakening the prose instead of resolving it.
 */
import { resolve } from "node:path";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { describe, expect, it } from "vitest";
import { WarbandReferences } from "@app/rules/warband-reference";
import { WarbandReferenceTemplate } from "@src/features/rules/WarbandReferenceTemplate";
import { readArtefactReader } from "../../../support/kb-artefact";

const realReader = () => readArtefactReader(resolve(process.cwd(), "../../outputs/web-public/knowledge/knowledge-web.json"));

/** Resolved statlines of the real published rows (EN / ES). */
const HUMAN = {
  en: "M 4, WS 6, BS 6, S 4, T 4, W 3, I 6, A 4, Ld 9",
  es: "M 10, HA 6, HP 6, F 4, R 4, H 3, I 6, A 4, L 9",
} as const;
const DWARF = {
  en: "M 3, WS 7, BS 6, S 4, T 5, W 3, I 5, A 4, Ld 10",
  es: "M 8, HA 7, HP 6, F 4, R 5, H 3, I 5, A 4, L 10",
} as const;
const BULL_CENTAUR = {
  en: "M 8, WS 7, BS 6, S 5, T 5, W 4, I 6, A 5, Ld 10",
  es: "M 20, HA 7, HP 6, F 5, R 5, H 4, I 6, A 5, L 10",
} as const;
const GRAVE_GUARD = {
  en: "M 5, WS 5, BS 5, S 4, T 4, W 4, I 5, A 4, Ld 10",
  es: "M 12, HA 5, HP 5, F 4, R 4, H 4, I 5, A 4, L 10",
} as const;

describe("reference citations in the rendered sheet", () => {
  it.each(["es", "en"] as const)("renders the resolved Sisters maximum profile exactly in %s", (locale) => {
    const sheet = new WarbandReferences(realReader()).sheet("sisters-of-sigmar", locale)!;
    const { container } = render(<WarbandReferenceTemplate sheet={sheet} locale={locale} />);
    expect(container).not.toHaveTextContent("campaign.limit.");
    const prose = screen.getByText(locale === "es" ? /Las Hermanas de Sigmar son Humanas/ : /Sisters of Sigmar are Humans/, { selector: "p.rule-prose" });
    expect(prose.textContent).toBe(locale === "es"
      ? `Las Hermanas de Sigmar son Humanas y usan el perfil máximo racial humano (${HUMAN.es}).`
      : `Sisters of Sigmar are Humans and use the Human racial maximum profile (${HUMAN.en}).`);
  });

  it.each(["es", "en"] as const)("renders every linked profile of a multi-citation rule in %s", (locale) => {
    const sheet = new WarbandReferences(realReader()).sheet("black-dwarfs", locale)!;
    const { container } = render(<WarbandReferenceTemplate sheet={sheet} locale={locale} />);
    expect(container).not.toHaveTextContent("campaign.limit.");
    const prose = screen.getByText(/maximum characteristic profile|perfil de características máximas/, { selector: "p.rule-prose" });
    expect(prose).toHaveTextContent(`(${DWARF[locale]})`);
    expect(prose).toHaveTextContent(`(${BULL_CENTAUR[locale]})`);
    expect(prose).toHaveTextContent(`(${HUMAN[locale]})`);
  });

  it("renders a repeated citation for both of its occurrences", () => {
    const sheet = new WarbandReferences(realReader()).sheet("restless-dead", "es")!;
    const { container } = render(<WarbandReferenceTemplate sheet={sheet} locale="es" />);
    expect(container).not.toHaveTextContent("campaign.limit.");
    const prose = screen.getByText(/El Liche usa el perfil racial máximo/, { selector: "p.rule-prose" });
    // Grave Guard is cited by both the Grave Guard and the Wights clause.
    expect(prose.textContent!.split(GRAVE_GUARD.es)).toHaveLength(3);
  });
});

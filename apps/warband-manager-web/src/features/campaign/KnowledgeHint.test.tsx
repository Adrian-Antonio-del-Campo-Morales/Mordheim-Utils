/**
 * Regression for the knowledge tooltips: the hint must show the artefact
 * description in the active locale, a readable sentence when the row has
 * none, and never a native browser `title` next to the app's own tooltip.
 */
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

import { KnowledgeHint } from "./KnowledgeHint";

const knowledge = {
  list: (kind: string) =>
    kind === "item"
      ? [
          { item_id: "sword", names: { en: "Sword", es: "Espada" }, effects: { en: "A fine blade.", es: "Una hoja fina." } },
          { item_id: "rope", names: { en: "Rope" } },
        ]
      : [],
  rulesDocument: () => [],
} as never;

describe("KnowledgeHint", () => {
  it("shows the localized description, the fallback, and no native title", () => {
    const { container } = render(
      <>
        <KnowledgeHint knowledge={knowledge} kind="item" id="sword" locale="es">Espada</KnowledgeHint>
        <KnowledgeHint knowledge={knowledge} kind="item" id="rope" locale="es">Cuerda</KnowledgeHint>
        <KnowledgeHint kind="item" id="missing" locale="en">Missing</KnowledgeHint>
      </>,
    );

    expect(screen.getByText("Espada")).toHaveAttribute("data-tooltip", "Una hoja fina.");
    expect(screen.getByText("Cuerda")).toHaveAttribute("data-tooltip", "No hay una descripción disponible para este elemento.");
    expect(screen.getByText("Missing")).toHaveAttribute("data-tooltip", "No description is available for this entry.");
    expect(container.querySelectorAll("[title]")).toHaveLength(0);
  });

  it("adapts Spanish tooltip distances while preserving English", () => {
    const distanceKnowledge = {
      list: () => [
        { item_id: "distance", effects: { en: "Range 6\"", es: "Alcance 6\"" } },
      ],
      rulesDocument: () => [],
    } as never;
    render(
      <>
        <KnowledgeHint knowledge={distanceKnowledge} kind="item" id="distance" locale="es">Español</KnowledgeHint>
        <KnowledgeHint knowledge={distanceKnowledge} kind="item" id="distance" locale="en">English</KnowledgeHint>
      </>,
    );

    expect(screen.getByText("Español")).toHaveAttribute("data-tooltip", "Alcance 15 cm");
    expect(screen.getByText("English")).toHaveAttribute("data-tooltip", "Range 6\"");
  });

  it("resolves real artefact descriptions for items, skills and rules", () => {
    const artefactPath = resolve(process.cwd(), "public/knowledge/knowledge-web.json");
    const artefact = JSON.parse(readFileSync(artefactPath, "utf-8"));
    artefact.rules_prose = JSON.parse(
      readFileSync(resolve(artefactPath, "..", artefact.rules_prose_url), "utf-8"),
    );
    const knowledge = ArtefactKnowledgeReader.from(artefact);
    const cases = [
      { kind: "item" as const, id: "sword" },
      { kind: "skill" as const, id: "skill.acrobat" },
      { kind: "rule" as const, id: "campaign.condition.cannot-run" },
    ];
    render(
      <>
        {cases.map((entry) => (
          <KnowledgeHint key={entry.id} knowledge={knowledge} kind={entry.kind} id={entry.id} locale="es">{entry.id}</KnowledgeHint>
        ))}
      </>,
    );
    for (const entry of cases) {
      const tooltip = screen.getByText(entry.id).getAttribute("data-tooltip") ?? "";
      expect(tooltip, entry.id).not.toBe("");
      expect(tooltip, entry.id).not.toContain("No hay una descripción");
    }
  });
});

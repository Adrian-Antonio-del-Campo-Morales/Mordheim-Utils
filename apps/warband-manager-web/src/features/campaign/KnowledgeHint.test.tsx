import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

import { KnowledgeHint } from "./KnowledgeHint";
import { knowledgeName, readableValue } from "./displayText";

const knowledge = ArtefactKnowledgeReader.from({
  schema_version: 1, ruleset: "test", bands: [], profiles: [], skills: [], items: [
    { item_id: "sword", names: { en: "Sword", es: "Espada" }, effects: { en: "A fine blade.", es: "Una hoja fina." } },
    { item_id: "rope", names: { en: "Rope" } },
  ],
});

function loadReader() {
  const artefactPath = resolve(process.cwd(), "public/knowledge/knowledge-web.json");
  const artefact = JSON.parse(readFileSync(artefactPath, "utf-8"));
  artefact.rules_prose = JSON.parse(readFileSync(resolve(artefactPath, "..", artefact.rules_prose_url), "utf-8"));
  Object.assign(artefact, JSON.parse(readFileSync(resolve(artefactPath, "..", artefact.display_text_url), "utf-8")));
  return ArtefactKnowledgeReader.from(artefact);
}

describe("KnowledgeHint", () => {
  it("provides a native dismissible popover without submitting the surrounding form", () => {
    const submit = vi.fn((event: React.FormEvent) => event.preventDefault());
    render(<form onSubmit={submit}><KnowledgeHint knowledge={knowledge} kind="item" id="sword" locale="es">Espada</KnowledgeHint></form>);
    const trigger = screen.getByRole("button", { name: "Espada" });
    fireEvent.click(trigger);
    expect(submit).not.toHaveBeenCalled();
    const popover = document.getElementById(trigger.getAttribute("popovertarget")!);
    expect(popover).toHaveAttribute("popover", "auto");
    expect(popover).toHaveTextContent("Una hoja fina.");
    const close = popover!.querySelector("button")!;
    expect(close).toHaveAttribute("popovertarget", popover!.id);
    expect(close).toHaveAttribute("popovertargetaction", "hide");
    fireEvent.click(close);
    expect(submit).not.toHaveBeenCalled();
  });

  it("shows the localized description, the fallback, and no native title", () => {
    const { container } = render(<><KnowledgeHint knowledge={knowledge} kind="item" id="sword" locale="es">Espada</KnowledgeHint><KnowledgeHint knowledge={knowledge} kind="item" id="rope" locale="es">Cuerda</KnowledgeHint><KnowledgeHint kind="item" id="missing" locale="en">Missing</KnowledgeHint></>);
    expect(screen.getByText("Espada")).toHaveAttribute("data-tooltip", "Una hoja fina.");
    expect(screen.getByRole("button", { name: "Información no disponible" })).toHaveAttribute("data-tooltip", "No hay una descripción disponible para este elemento.");
    expect(screen.getByRole("button", { name: "Information unavailable" })).toHaveAttribute("data-tooltip", "No description is available for this entry.");
    expect(container.querySelectorAll("[title]")).toHaveLength(0);
  });

  it("adapts Spanish tooltip distances while preserving English", () => {
    const distanceKnowledge = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [], skills: [], items: [{ item_id: "distance", names: { es: "Español", en: "English" }, effects: { en: "Range 6\"", es: "Alcance 6\"" } }] });
    render(<><KnowledgeHint knowledge={distanceKnowledge} kind="item" id="distance" locale="es">Español</KnowledgeHint><KnowledgeHint knowledge={distanceKnowledge} kind="item" id="distance" locale="en">English</KnowledgeHint></>);
    expect(screen.getByText("Español")).toHaveAttribute("data-tooltip", "Alcance 15 cm");
    expect(screen.getByText("English")).toHaveAttribute("data-tooltip", "Range 6\"");
  });

  it("resolves real artefact descriptions for items, skills and rules", () => {
    const reader = loadReader();
    const cases = [{ kind: "item" as const, id: "sword" }, { kind: "skill" as const, id: "skill.acrobat" }, { kind: "rule" as const, id: "campaign.condition.cannot-run" }];
    render(<>{cases.map((entry) => <KnowledgeHint key={entry.id} knowledge={reader} kind={entry.kind} id={entry.id} locale="es">{entry.id}</KnowledgeHint>)}</>);
    for (const entry of cases) {
      expect(screen.getByRole("button", { name: knowledgeName(reader, entry.kind, entry.id, "es") }).getAttribute("data-tooltip")).not.toBe("");
      expect(screen.queryByText(entry.id)).not.toBeInTheDocument();
    }
  });

  it("resolves a mechanic tooltip through the central display index", () => {
    const reader = loadReader();
    render(<KnowledgeHint knowledge={reader} kind="skill" id="skill.blessed-sight" locale="es">Vista Bendecida</KnowledgeHint>);
    expect(screen.getByText("Vista Bendecida")).toHaveAttribute("data-tooltip", expect.stringContaining("La Augur puede repetir"));
  });

  it("localizes campaign-only equipment and gives common weapons a tooltip", () => {
    const reader = loadReader();
    render(<>{["rope_hook", "healing_herbs", "long_bow", "elf_bow", "elven_cloak"].map((id) => <KnowledgeHint key={id} knowledge={reader} kind="item" id={id} locale="es">{reader.itemName(id, "es")}</KnowledgeHint>)}</>);
    expect(screen.getByText("Gancho de Cuerda")).toHaveAttribute("data-tooltip", expect.stringContaining("Iniciativa"));
    expect(screen.getByText("Hierbas Curativas")).toHaveAttribute("data-tooltip", expect.stringContaining("Heridas perdidas"));
    expect(screen.getByText("Arco Largo")).toHaveAttribute("data-tooltip", expect.stringContaining("75 cm"));
    expect(screen.getByText("Arco Élfico")).toHaveAttribute("data-tooltip", expect.stringContaining("90 cm"));
    expect(screen.getByText("Capa Élfica")).toHaveAttribute("data-tooltip", expect.stringContaining("-1"));
  });

  it("localizes and explains magical artefacts stored as inventory items", () => {
    const reader = loadReader();
    const id = "magical_artefact.executioners-hood";
    render(<KnowledgeHint knowledge={reader} kind="item" id={id} locale="es">{knowledgeName(reader, "item", id, "es")}</KnowledgeHint>);
    expect(screen.getByText("Capucha del Verdugo")).toHaveAttribute("data-tooltip", expect.stringContaining("siempre frenético"));
  });

  it("resolves legacy rule names with the profile-specific Spanish description", () => {
    const reader = loadReader();
    render(<KnowledgeHint knowledge={reader} kind="rule" id="dwarf-troll-slayers--no-armour" profileId="dwarf-troll-slayers" bandId="dwarf-treasure-hunters" locale="es">Sin Armadura</KnowledgeHint>);
    expect(screen.getByText("Sin Armadura")).toHaveAttribute("data-tooltip", "Los Matatrolles Enanos jamás pueden llevar ningún tipo de armadura.");
  });

  it("resolves names and tooltips for every hireling ability in the artefact", () => {
    const reader = loadReader();
    const profiles = reader.campaignSection("hirelings").profiles as Readonly<Record<string, unknown>>[];
    const ids = [...new Set(profiles.flatMap((profile) => ["starting_skill_ids", "rule_ids", "special_skill_rule_ids"].flatMap((field) => Array.isArray(profile[field]) ? profile[field].map(String) : [])))].filter((id) => !id.endsWith(".rule.campaign-eligibility"));
    render(<>{ids.map((id) => <KnowledgeHint key={id} knowledge={reader} kind={id.includes(".skill.") || id.startsWith("skill.") ? "skill" : "rule"} id={id} locale="es">{id}</KnowledgeHint>)}</>);
    for (const id of ids) expect(knowledgeName(reader, id.includes(".skill.") || id.startsWith("skill.") ? "skill" : "rule", id, "es")).not.toBe(readableValue(id, "es"));
  }, 10000);

  it("shows the localized serious-injury description from the knowledge base", () => {
    const reader = loadReader();
    render(<KnowledgeHint knowledge={reader} kind="injury" id="campaign.serious-injury.hero.34-hand-injury" locale="es">Herida en la Mano</KnowledgeHint>);
    expect(screen.getByRole("button", { name: "Información no disponible" })).toHaveAttribute("data-tooltip", "La mano herida reduce permanentemente en 1 la Habilidad de Armas del guerrero.");
  });
});

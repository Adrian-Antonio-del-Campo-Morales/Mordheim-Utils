import { resolve } from "node:path";
import { fireEvent, render, screen, within } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { describe, expect, it, vi } from "vitest";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { WarbandReferences } from "@app/rules/warband-reference";
import { WarbandsBrowser } from "@src/features/rules/WarbandsBrowser";
import { WarbandReferenceTemplate } from "@src/features/rules/WarbandReferenceTemplate";
import { readArtefactReader } from "../support/kb-artefact";

const realReader = () => readArtefactReader(resolve(__dirname, "../../outputs/web-public/knowledge/knowledge-web.json"));
const emptyReader = () => ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [{ id: "empty", name: "Empty", name_i18n: { es: "Vacía" }, grade: "core" }], profiles: [], items: [], skills: [], campaign: {} });

describe("common warband template", () => {
  it("groups Underworld armour and defences and resolves translated equipment notes", () => {
    const sheet = new WarbandReferences(realReader()).sheet("underworld-alliance-mim", "es")!;
    const { container } = render(<WarbandReferenceTemplate sheet={sheet} locale="es" />);
    const greenskins = screen.getByRole("heading", { name: "Lista de Equipo de los Pielesverdes" }).closest("section")!;
    const armour = within(greenskins).getByRole("table", { name: "Armaduras y defensas" });
    expect(within(armour).getByRole("button", { name: "Armadura Ligera" })).toBeInTheDocument();
    expect(within(armour).getByRole("button", { name: "Escudo" })).toBeInTheDocument();
    expect(within(greenskins).getAllByRole("table", { name: "Equipo" })).toHaveLength(1);
    expect(within(greenskins).getByRole("button", { name: "Cerbatana" })).toHaveAttribute("data-tooltip");
    expect(container).not.toHaveTextContent(/Información no disponible|Objeto ausente|El texto de las restricciones no está disponible/);
  });
  it.each(["es", "en"] as const)("renders the real Sisters data and localized characteristics in %s", (locale) => {
    const sheet = new WarbandReferences(realReader()).sheet("sisters-of-sigmar", locale)!;
    render(<WarbandReferenceTemplate sheet={sheet} locale={locale} />);
    expect(screen.getByRole("heading", { level: 2, name: locale === "es" ? "Hermanas de Sigmar" : "Sisters of Sigmar" })).toBeInTheDocument();
    expect(screen.getByText(locale === "es" ? "500 co" : "500 gc")).toBeInTheDocument();
    const card = screen.getByRole("heading", { name: locale === "es" ? "Matriarca Sigmarita" : "Sigmarite Matriarch" }).closest(".warband-warrior")!;
    expect(card.querySelector(".stats span")).toHaveTextContent(locale === "es" ? "M10" : "M4");
    expect(screen.getByRole("table", { name: locale === "es" ? "Tabla de habilidades" : "Skill table" })).toBeInTheDocument();
    const specialSkill = screen.getByText(locale === "es" ? "Signo de Sigmar" : "Sign of Sigmar", { selector: "summary" });
    expect(specialSkill.closest(".warband-skill-list")?.querySelector(":scope > summary")).toHaveTextContent(locale === "es" ? "Especiales" : "Special");
    // F050: the canonical racial-maximum citation is rendered as its profile.
    const maximumRule = screen.getByText(locale === "es" ? /Las Hermanas de Sigmar son Humanas/ : /Sisters of Sigmar are Humans/, { selector: "p.rule-prose" });
    expect(maximumRule.textContent).toBe(locale === "es"
      ? "Las Hermanas de Sigmar son Humanas y usan el perfil máximo racial humano (M 10, HA 6, HP 6, F 4, R 4, H 3, I 6, A 4, L 9)."
      : "Sisters of Sigmar are Humans and use the Human racial maximum profile (M 4, WS 6, BS 6, S 4, T 4, W 3, I 6, A 4, Ld 9).");
    expect(maximumRule).not.toHaveTextContent("campaign.limit.");
    expect(screen.getByRole("button", { name: locale === "es" ? "Martillo Sigmarita" : "Sigmarite Hammer" })).toHaveAttribute("data-tooltip");
    expect(screen.getByRole("heading", { name: locale === "es" ? "Lista de Equipo de las Hermanas de Sigmar" : "Sisters of Sigmar Equipment List" })).toBeInTheDocument();
    expect(screen.getByText(locale === "es" ? "Primera daga gratis; las siguientes cuestan 2 co." : "1st free/2 gc")).toBeInTheDocument();
    expect(screen.queryByText(/Los datos publicados aún no incluyen|The published data does not yet include/)).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: locale === "es" ? "Magia y plegarias" : "Magic and prayers" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: locale === "es" ? "Variantes" : "Variants" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: locale === "es" ? "Sin Armadura" : "No Armour" })).toHaveAttribute("data-tooltip");
  });

  it("uses name-only search and includes bands without rules", () => {
    const reader = emptyReader();
    const { rerender } = render(<WarbandsBrowser knowledge={reader} locale="es" query="vacia" />);
    expect(screen.getByRole("button", { name: /Vacía/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Composición" })).toBeInTheDocument();
    rerender(<WarbandsBrowser knowledge={reader} locale="es" query="no matches" />);
    expect(screen.getByText("Ninguna banda coincide con este nombre.")).toBeInTheDocument();
    expect(screen.queryByRole("article")).not.toBeInTheDocument();
  });

  it("restores the mobile result focus and scroll and keeps the chosen band across locales", () => {
    vi.stubGlobal("matchMedia", vi.fn(() => ({ matches: true })));
    const scrollTo = vi.spyOn(window, "scrollTo").mockImplementation(() => {});
    const original = HTMLElement.prototype.scrollIntoView;
    HTMLElement.prototype.scrollIntoView = vi.fn();
    try {
      const reader = emptyReader();
      const { rerender } = render(<WarbandsBrowser knowledge={reader} locale="es" query="" />);
      const button = screen.getByRole("button", { name: /Vacía/ });
      fireEvent.click(button);
      expect(screen.getByRole("article", { name: "Vacía" })).toHaveFocus();
      rerender(<WarbandsBrowser knowledge={reader} locale="en" query="" />);
      expect(screen.getByRole("article", { name: "Empty" })).toHaveFocus();
      fireEvent.click(screen.getByRole("button", { name: "Back to warbands" }));
      expect(button).toHaveFocus();
      expect(scrollTo).toHaveBeenCalledWith({ top: 0 });
      expect(screen.getByRole("article").parentElement).toHaveClass("show-band-list");
    } finally { scrollTo.mockRestore(); HTMLElement.prototype.scrollIntoView = original; }
  });
});

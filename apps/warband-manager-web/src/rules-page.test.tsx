import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProductApp } from "./ProductApp";
import { loadKnowledge } from "./features/campaign/default-deps";

vi.mock("./features/campaign/default-deps", () => ({
  createService: vi.fn(),
  loadKnowledge: vi.fn(),
}));

describe("RulesPage magic groups", () => {
  beforeEach(() => {
    vi.mocked(loadKnowledge).mockResolvedValue({
      campaignSection: (section: string) => section === "magic" ? { lores: [
        { id: "lore.prayers", name: "Prayers", name_i18n: { es: "Plegarias" }, spells: [{ id: "spell.prayers.blessing", name: "Blessing", name_i18n: { es: "Bendición" }, effect: "Bless." }] },
        { id: "lore.magic", name: "Magic Lore", name_i18n: { es: "Saber Mágico" }, spells: [{ id: "spell.magic.fire", name: "Fire", name_i18n: { es: "Fuego" }, effect: "Burn." }] },
      ] } : {},
      list: (kind: string) => kind === "band" ? [
        { id: "reiklanders", name: "Reiklanders", name_i18n: { es: "Reiklandeses" } },
        { id: "sisters", name: "Sisters", name_i18n: { es: "Hermanas de Sigmar" } },
      ] : [],
      rulesDocument: (document: string) => document === "profile-special-rules" ? [
        { id: "captain--leader", band_id: "reiklanders", name: "Leader", name_i18n: { es: "Jefe" }, effect: "Leads." },
        { id: "matriarch--leader", band_id: "sisters", name: "Leader", name_i18n: { es: "Jefe" }, effect: "Leads." },
      ] : [],
    } as never);
  });

  it("groups localized spells under their lore in the single Spells tab", async () => {
    render(<ProductApp />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Reglas" })).toBeEnabled());
    fireEvent.click(screen.getByRole("button", { name: "Reglas" }));
    expect(screen.getByRole("button", { name: "Reglas Generales" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Reglas de Banda" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Hechizos" }));

    expect(within(screen.getByRole("region", { name: "Plegarias" })).getByRole("button", { name: "Bendición" })).toBeInTheDocument();
    expect(within(screen.getByRole("region", { name: "Saber Mágico" })).getByRole("button", { name: "Fuego" })).toBeInTheDocument();

    fireEvent.change(screen.getByRole("textbox", { name: "Buscar Reglas" }), { target: { value: "Plegarias" } });
    expect(screen.getByRole("button", { name: /Bendición/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Fuego/ })).not.toBeInTheDocument();
  });

  it("nests warband rules under their localized warband", async () => {
    render(<ProductApp />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Reglas" })).toBeEnabled());
    fireEvent.click(screen.getByRole("button", { name: "Reglas" }));
    fireEvent.click(screen.getByRole("button", { name: "Reglas de Banda" }));

    const reiklandersSummary = screen.getByText("Reiklandeses", { selector: "summary" });
    const reiklanders = reiklandersSummary.closest("details");
    const sisters = screen.getByText("Hermanas de Sigmar", { selector: "summary" }).closest("details");
    expect(reiklanders).not.toHaveAttribute("open");
    expect(sisters).not.toHaveAttribute("open");
    fireEvent.click(reiklandersSummary);
    expect(reiklanders).toHaveAttribute("open");
    expect(within(reiklanders!).getByRole("button", { name: "Jefe" })).toBeInTheDocument();
  });

  it("returns to the same filtered result and restores mobile focus and scroll", async () => {
    vi.stubGlobal("matchMedia", vi.fn(() => ({ matches: true })));
    const scrollTo = vi.spyOn(window, "scrollTo").mockImplementation(() => {});
    const originalScrollIntoView = HTMLElement.prototype.scrollIntoView;
    HTMLElement.prototype.scrollIntoView = vi.fn();
    try {
      render(<ProductApp />);
      await waitFor(() => expect(screen.getByRole("button", { name: "Reglas" })).toBeEnabled());
      fireEvent.click(screen.getByRole("button", { name: "Reglas" }));
      const search = screen.getByRole("textbox", { name: "Buscar Reglas" });
      fireEvent.change(search, { target: { value: "Bendición" } });
      const result = screen.getByRole("button", { name: /Bendición/ });
      fireEvent.click(result);
      expect(document.activeElement).toHaveClass("rule-detail");
      fireEvent.click(screen.getByRole("button", { name: /Volver a resultados/ }));
      expect(search).toHaveValue("Bendición");
      expect(result).toHaveFocus();
      expect(scrollTo).toHaveBeenCalledWith({ top: 0 });
    } finally {
      HTMLElement.prototype.scrollIntoView = originalScrollIntoView;
      scrollTo.mockRestore();
      vi.unstubAllGlobals();
    }
  });
});

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
      list: () => [],
      rulesDocument: () => [],
    } as never);
  });

  it("groups localized spells under their lore in the single Spells tab", async () => {
    render(<ProductApp />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Reglas" })).toBeEnabled());
    fireEvent.click(screen.getByRole("button", { name: "Reglas" }));
    fireEvent.click(screen.getByRole("button", { name: "Hechizos" }));

    expect(within(screen.getByRole("region", { name: "Plegarias" })).getByRole("button", { name: "Bendición" })).toBeInTheDocument();
    expect(within(screen.getByRole("region", { name: "Saber Mágico" })).getByRole("button", { name: "Fuego" })).toBeInTheDocument();

    fireEvent.change(screen.getByRole("textbox", { name: "Buscar Reglas" }), { target: { value: "Plegarias" } });
    expect(screen.getByRole("button", { name: /Bendición/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Fuego/ })).not.toBeInTheDocument();
  });
});

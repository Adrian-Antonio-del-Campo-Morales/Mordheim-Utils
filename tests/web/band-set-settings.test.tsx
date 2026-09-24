import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProductApp } from "@src/ProductApp";
import { loadKnowledge } from "@src/features/campaign/default-deps";

vi.mock("@src/features/campaign/default-deps", () => ({
  createService: vi.fn(),
  loadKnowledge: vi.fn(),
}));

const bands = [
  { id: "mercenaries", names: { en: "Mercenaries", es: "Mercenarios" }, collection: "mordheim", grade: "core", variants: [{ id: "reikland", names: { en: "Reikland", es: "Reikland" }, rule_ids: [] }] },
  { id: "grade-1a-band", names: { en: "Grade 1A Band", es: "Banda 1A" }, collection: "mordheim", grade: "1a" },
  { id: "tileans", names: { en: "Tileans", es: "Tileanos" }, collection: "mordheim", grade: "1b", variants: [{ id: "trantios", names: { en: "Trantios", es: "Trantinos" }, rule_ids: [] }] },
  { id: "trollheim-band", names: { en: "Trollheim Band", es: "Banda de Trollheim" }, collection: "trollheim", grade: null },
];

describe("warband set settings", () => {
  beforeEach(() => {
    vi.mocked(loadKnowledge).mockResolvedValue({
      list: () => bands,
      recordText: (row: { names: { es: string } }) => row.names.es,
      queryKnowledge: ({ id }: { id: { value: string } }) => {
        const band = bands.find((row) => row.id === id.value);
        return band ? { ok: true, record: { data: band } } : { ok: false, reason: "not_found" };
      },
    } as never);
  });

  it("filters the new campaign picker using the enabled sets", async () => {
    const user = userEvent.setup();
    render(<ProductApp />);
    await waitFor(() => expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]).toBeEnabled());

    await user.click(screen.getByRole("button", { name: "Ajustes" }));
    const settings = screen.getByRole("group", { name: "Conjuntos de bandas disponibles" });
    expect(within(settings).getAllByRole("checkbox")).toHaveLength(5);
    await user.click(within(settings).getByRole("checkbox", { name: "1A" }));

    await user.click(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]);
    const picker = screen.getByRole("group", { name: "Lista de Banda" });
    expect(within(picker).queryByRole("radio", { name: /Banda 1A/ })).not.toBeInTheDocument();
    expect(within(picker).getByRole("radio", { name: /Mercenarios.*Básicas/ })).toBeInTheDocument();
    expect(within(picker).getByRole("radio", { name: /Banda de Trollheim.*Trollheim/ })).toBeInTheDocument();
    await user.click(within(picker).getByRole("radio", { name: /Mercenarios.*Básicas/ }));
    expect(screen.getByRole("combobox", { name: "Variante de banda" })).toHaveValue("");
    expect(screen.getByRole("button", { name: "Crear" })).toBeDisabled();
    await user.selectOptions(screen.getByRole("combobox", { name: "Variante de banda" }), "reikland");
    expect(screen.getByRole("button", { name: "Crear" })).toBeEnabled();
    await user.click(within(picker).getByRole("radio", { name: /Tileanos.*1B/ }));
    expect(screen.getByRole("combobox", { name: "Variante de banda" })).toHaveValue("");
    expect(screen.getByRole("button", { name: "Crear" })).toBeDisabled();
    await user.click(within(picker).getByRole("radio", { name: /Banda de Trollheim.*Trollheim/ }));
    expect(screen.queryByRole("combobox", { name: "Variante de banda" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Crear" })).toBeEnabled();
  });
});

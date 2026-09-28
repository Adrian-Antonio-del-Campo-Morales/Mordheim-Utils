import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProductApp } from "@src/ProductApp";
import { loadKnowledge } from "@src/features/campaign/default-deps";
import { bandCategoriesOf, bandCategoryKey, bandPickerState } from "@src/features/campaign/band-categories";
import { translate } from "@src/features/campaign/i18n-core";

// T12 fase D: only the composition functions are stubbed; the real
// `ensureCampaignCatalogue` is kept so the deferred-catalogue gate runs as in
// the product.
vi.mock("@src/features/campaign/default-deps", async (importOriginal) => ({
  ...(await importOriginal<typeof import("@src/features/campaign/default-deps")>()),
  createService: vi.fn(),
  loadKnowledge: vi.fn(),
}));

/**
 * Categories come from the artefact rows, so the fixture publishes the same
 * shape the generator writes: `collection` plus `grade` (2A/2B included).
 */
const bands = [
  { id: "mercenaries", names: { en: "Mercenaries", es: "Mercenarios" }, collection: "mordheim", grade: "core", variants: [{ id: "reikland", names: { en: "Reikland", es: "Reikland" }, rule_ids: [] }] },
  { id: "grade-1a-band", names: { en: "Grade 1A Band", es: "Banda 1A" }, collection: "mordheim", grade: "1a" },
  { id: "grade-2a-band", names: { en: "Grade 2A Band", es: "Banda 2A" }, collection: "mordheim", grade: "2a" },
  { id: "grade-2b-band", names: { en: "Grade 2B Band", es: "Banda 2B" }, collection: "mordheim", grade: "2b" },
  { id: "tileans", names: { en: "Tileans", es: "Tileanos" }, collection: "mordheim", grade: "1b", variants: [{ id: "trantios", names: { en: "Trantios", es: "Trantinos" }, rule_ids: [] }] },
  { id: "trollheim-band", names: { en: "Trollheim Band", es: "Banda de Trollheim" }, collection: "trollheim", grade: null },
];

function mockKnowledge(rows: readonly unknown[]) {
  vi.mocked(loadKnowledge).mockResolvedValue({
    list: () => rows,
    recordText: (row: { names: { es: string } }) => row.names.es,
    queryKnowledge: ({ id }: { id: { value: string } }) => {
      const band = rows.find((row) => (row as { id: string }).id === id.value);
      return band ? { ok: true, record: { data: band } } : { ok: false, reason: "not_found" };
    },
    // T12 fase D: the stand-in reader publishes both catalogue families.
    isCatalogueLoaded: () => true,
    ensureCatalogue: async () => {},
  } as never);
}

describe("warband categories", () => {
  beforeEach(() => {
    mockKnowledge(bands);
  });

  it("derives the published categories from the artefact, 2A/2B included", () => {
    expect(bandCategoriesOf(bands, "es").map((category) => category.key).sort()).toEqual(["1a", "1b", "2a", "2b", "core", "trollheim"]);
    const core = bandCategoriesOf(bands, "en").find((category) => category.key === "core");
    const coreEs = bandCategoriesOf(bands, "es").find((category) => category.key === "core");
    expect(core && String(translate(core.label, "en"))).toBe("Core");
    expect(coreEs && String(translate(coreEs.label, "es"))).toBe("Básicas");
    // A Mordheim band is grouped by grade; another collection is its own group.
    expect(bandCategoryKey(bands[2])).toBe("2a");
    expect(bandCategoryKey(bands[5])).toBe("trollheim");
    // A row with no grade and no collection keeps its own group, never `null`.
    expect(bandCategoryKey({})).toBe("");
    expect(bandPickerState(0, 0)).toBe("no-data");
    expect(bandPickerState(6, 0)).toBe("no-match");
    expect(bandPickerState(6, 6)).toBe("ready");
  });

  it("filters the new campaign picker using the enabled sets", async () => {
    const user = userEvent.setup();
    render(<ProductApp />);
    await waitFor(() => expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]).toBeEnabled());

    await user.click(screen.getByRole("button", { name: "Ajustes" }));
    const settings = screen.getByRole("group", { name: "Conjuntos de bandas disponibles" });
    expect(within(settings).getAllByRole("checkbox")).toHaveLength(6);
    await user.click(within(settings).getByRole("checkbox", { name: "1A" }));
    await user.click(within(settings).getByRole("checkbox", { name: "2B" }));

    await user.click(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]);
    const picker = screen.getByRole("group", { name: "Lista de Banda" });
    expect(within(picker).queryByRole("radio", { name: /Banda 1A/ })).not.toBeInTheDocument();
    expect(within(picker).queryByRole("radio", { name: /Banda 2B/ })).not.toBeInTheDocument();
    expect(within(picker).getByRole("radio", { name: /Banda 2A/ })).toBeInTheDocument();
    expect(within(picker).getByRole("radio", { name: /Mercenarios.*Básicas/ })).toBeInTheDocument();
    expect(within(picker).getByRole("radio", { name: /Banda de Trollheim.*Trollheim/ })).toBeInTheDocument();

    // The domain keeps demanding the variant the selected band publishes.
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

  it("enables and disables 2A and 2B again, and translates the labels", async () => {
    const user = userEvent.setup();
    render(<ProductApp />);
    await waitFor(() => expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]).toBeEnabled());
    await user.click(screen.getByRole("button", { name: "Ajustes" }));
    const settings = screen.getByRole("group", { name: "Conjuntos de bandas disponibles" });

    await user.selectOptions(screen.getByRole("combobox", { name: "Idioma" }), "en");
    expect(within(settings).getByRole("checkbox", { name: "Core" })).toBeChecked();
    expect(within(settings).getByRole("checkbox", { name: "2A" })).toBeChecked();
    expect(within(settings).getByRole("checkbox", { name: "2B" })).toBeChecked();

    await user.click(within(settings).getByRole("checkbox", { name: "2A" }));
    await user.click(screen.getAllByRole("button", { name: "New Campaign" })[0]);
    const picker = screen.getByRole("group", { name: "Warband List" });
    expect(within(picker).queryByRole("radio", { name: /Banda 2A/ })).not.toBeInTheDocument();
    expect(within(picker).getByRole("radio", { name: /Banda 2B/ })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Close" }));

    await user.click(within(settings).getByRole("checkbox", { name: "2A" }));
    await user.click(screen.getAllByRole("button", { name: "New Campaign" })[0]);
    expect(within(screen.getByRole("group", { name: "Warband List" })).getByRole("radio", { name: /Banda 2A/ })).toBeInTheDocument();
  });

  it("separates 'no band matches the filter' from 'the artefact has no data'", async () => {
    const user = userEvent.setup();
    render(<ProductApp />);
    await waitFor(() => expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]).toBeEnabled());
    await user.click(screen.getByRole("button", { name: "Ajustes" }));
    const settings = screen.getByRole("group", { name: "Conjuntos de bandas disponibles" });
    for (const box of within(settings).getAllByRole("checkbox")) await user.click(box);
    await user.click(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]);
    const picker = screen.getByRole("group", { name: "Lista de Banda" });
    expect(within(picker).queryAllByRole("radio")).toHaveLength(0);
    expect(within(picker).getByRole("status")).toHaveTextContent("Ninguna banda publicada pertenece a las categorías activadas");
    expect(screen.getByRole("button", { name: "Crear" })).toBeDisabled();
  });

  it("reports an artefact without bands instead of an empty filter", async () => {
    mockKnowledge([]);
    const user = userEvent.setup();
    render(<ProductApp />);
    await waitFor(() => expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]).toBeEnabled());
    await user.click(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]);
    const picker = screen.getByRole("group", { name: "Lista de Banda" });
    expect(within(picker).getByRole("status")).toHaveTextContent("El artefacto de conocimiento no publica ninguna banda");
    expect(within(picker).queryByRole("radio")).not.toBeInTheDocument();
  });
});

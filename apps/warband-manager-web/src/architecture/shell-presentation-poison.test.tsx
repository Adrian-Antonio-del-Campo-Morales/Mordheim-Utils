import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { ProductApp } from "../ProductApp";
import { loadKnowledge, createService } from "../features/campaign/default-deps";

vi.mock("../features/campaign/default-deps", () => ({ loadKnowledge: vi.fn(), createService: vi.fn() }));
const marker = "RAW_KB_POISON_";
const labels = { es: "Banda de prueba", en: "Test warband" };
function assertSafe(container: HTMLElement) {
  expect(container.textContent).not.toContain(marker);
  for (const node of container.querySelectorAll("*")) {
    for (const attr of ["title", "alt", "placeholder", "aria-label", "aria-description", "data-tooltip", "data-title", "data-status"]) expect(node.getAttribute(attr) ?? "").not.toContain(marker);
    if (node instanceof HTMLTextAreaElement || (node instanceof HTMLInputElement && !["hidden", "checkbox", "radio", "file"].includes(node.type))) expect(node.value).not.toContain(marker);
  }
}
beforeEach(() => {
  vi.mocked(loadKnowledge).mockReset();
  vi.mocked(createService).mockReset();
  vi.mocked(loadKnowledge).mockResolvedValue(ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", profiles: [], skills: [],
    bands: [{ id: marker + "BAND", name: marker + "NAME", names: labels, collection: "mordheim", grade: "core", roster: { members: [] } }],
    items: [{ item_id: marker + "ITEM", name: marker + "NAME", names: { es: "Espada prueba", en: "Test sword" }, effect: marker + "DESCRIPTION", effect_i18n: { es: "Texto prueba", en: "Test text" } }],
  }));
});

describe("real shell menus, catalogue, forms and errors with poisoned sources", () => {
  it("checks menus, category lists and creation form in es/en/es", async () => {
    const view = render(<ProductApp/>);
    await waitFor(() => expect(screen.getByRole("button", { name: "Reglas" }).hasAttribute("disabled")).toBe(false));
    for (const locale of ["es", "en", "es"] as const) {
      const settings = screen.queryByRole("button", { name: "Ajustes" }) ?? screen.getByRole("button", { name: "Settings" });
      fireEvent.click(settings);
      fireEvent.change(screen.getByRole("combobox"), { target: { value: locale } });
      assertSafe(view.container);
      fireEvent.click(screen.getByRole("button", { name: locale === "es" ? "Reglas" : "Rules" }));
      const categories = [...view.container.querySelectorAll<HTMLButtonElement>(".rules-toolbar .tabs button")];
      expect(categories.length).toBeGreaterThan(0);
      for (const category of categories) { fireEvent.click(category); assertSafe(view.container); }
      fireEvent.click(screen.getAllByRole("button", { name: locale === "es" ? "Nueva Campaña" : "New Campaign" })[0]);
      expect(screen.getByRole("dialog")).toBeTruthy();
      expect(screen.getByRole("radio", { name: new RegExp(labels[locale]) })).toBeTruthy();
      assertSafe(view.container);
      fireEvent.click(screen.getByRole("button", { name: locale === "es" ? "Cancelar" : "Cancel" }));
    }
  });

  it("keeps a technical load exception out of the error dialog and survives retry", async () => {
    const good = await vi.mocked(loadKnowledge)();
    vi.mocked(loadKnowledge).mockReset().mockRejectedValueOnce(new Error(marker + "TECHNICAL_PATH")).mockResolvedValue(good);
    const view = render(<ProductApp/>);
    await screen.findByRole("alert");
    assertSafe(view.container);
    fireEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
    assertSafe(view.container);
  });
});

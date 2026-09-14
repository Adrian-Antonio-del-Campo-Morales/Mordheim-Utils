import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { ProductApp } from "../ProductApp";
import { createService, loadKnowledge } from "../features/campaign/default-deps";

vi.mock("../features/campaign/default-deps", () => ({
  createService: vi.fn(),
  loadKnowledge: vi.fn(),
}));

vi.mock("../features/campaign/CampaignSlice", () => ({
  CampaignSlice: () => <p>Campaign workspace</p>,
}));

const document = {
  campaign: {
    identity: {
      campaign_name: "Campaña de prueba",
      warband_name: "Banda de prueba",
      warband_type: "mercenaries",
    },
  },
  view: {},
};
const importedDocument = {
  ...document,
  campaign: {
    ...document.campaign,
    identity: { ...document.campaign.identity, campaign_name: "Campaña importada", warband_name: "Banda importada" },
  },
};
const run = vi.fn().mockResolvedValue({ ok: true });
const prepareExport = vi.fn();
const markExported = vi.fn();

describe("ProductApp session removal", () => {
  beforeEach(() => {
    run.mockClear();
    prepareExport.mockReset();
    markExported.mockClear();
    prepareExport.mockResolvedValue({ ok: false, message: "Export failed" });
    vi.mocked(loadKnowledge).mockResolvedValue({
      list: () => [{ id: "mercenaries", names: { es: "Mercenarios" }, collection: "mordheim", grade: "core" }],
    } as never);
    vi.mocked(createService).mockReturnValue({
      createCampaign: vi.fn().mockResolvedValue({ ok: true }),
      subscribe: () => () => {},
      run,
      prepareExport,
      markExported,
      isDirty: () => true,
      canUndo: () => false,
      current: () => document,
    } as never);
  });

  it("does not block closing the page when no campaign is loaded", () => {
    render(<ProductApp />);

    const beforeUnload = new Event("beforeunload", { cancelable: true });
    expect(window.dispatchEvent(beforeUnload)).toBe(true);
  });

  it("keeps the active session when an imported file is rejected", async () => {
    const rejectImport = vi.fn().mockResolvedValue({ ok: false, message: "Invalid campaign" });
    vi.mocked(createService)
      .mockReset()
      .mockReturnValueOnce({
        createCampaign: vi.fn().mockResolvedValue({ ok: true }),
        subscribe: () => () => {}, run, prepareExport, markExported,
        isDirty: () => true, canUndo: () => false, current: () => document,
      } as never)
      .mockReturnValueOnce({ importCampaign: rejectImport } as never);

    const { container } = render(<ProductApp />);
    await waitFor(() =>
      expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0].hasAttribute("disabled")).toBe(false),
    );
    fireEvent.click(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]);
    fireEvent.change(screen.getByLabelText("Nombre de Campaña"), { target: { value: "Campaña de prueba" } });
    fireEvent.click(screen.getByRole("button", { name: "Crear" }));
    await screen.findByText("Campaign workspace");

    const input = container.querySelector<HTMLInputElement>('input[type="file"]')!;
    const file = new File(["not a campaign"], "broken.mordheim", { type: "application/json" });
    Object.defineProperty(file, "text", { value: async () => "not a campaign" });
    fireEvent.change(input, { target: { files: [file] } });

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo importar broken.mordheim: la campaña no es válida.");
    expect(rejectImport).toHaveBeenCalledTimes(1);
    expect(screen.getByText("Campaign workspace")).toBeInTheDocument();
  });

  it("adds a valid import as the active session without replacing the current one", async () => {
    const importCampaign = vi.fn().mockResolvedValue({ ok: true, document: importedDocument });
    vi.mocked(createService)
      .mockReset()
      .mockReturnValueOnce({
        createCampaign: vi.fn().mockResolvedValue({ ok: true }),
        subscribe: () => () => {}, run, prepareExport, markExported,
        isDirty: () => true, canUndo: () => false, current: () => document,
      } as never)
      .mockReturnValueOnce({ importCampaign, subscribe: () => () => {}, isDirty: () => false, canUndo: () => false, current: () => importedDocument } as never);

    const { container } = render(<ProductApp />);
    await waitFor(() =>
      expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0].hasAttribute("disabled")).toBe(false),
    );
    fireEvent.click(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]);
    fireEvent.change(screen.getByLabelText("Nombre de Campaña"), { target: { value: "Campaña de prueba" } });
    fireEvent.click(screen.getByRole("button", { name: "Crear" }));
    await screen.findByText("Campaign workspace");

    const input = container.querySelector<HTMLInputElement>('input[type="file"]')!;
    const file = new File(["campaign"], "imported.mordheim", { type: "application/json" });
    Object.defineProperty(file, "text", { value: async () => "campaign" });
    fireEvent.change(input, { target: { files: [file] } });
    await waitFor(() => expect(importCampaign).toHaveBeenCalledTimes(1));

    fireEvent.click(screen.getByRole("button", { name: "Campañas" }));
    expect(screen.getByText("Banda de prueba")).toBeInTheDocument();
    const importedCard = screen.getByText("Banda importada").closest("article");
    expect(importedCard).toHaveClass("active");
  });

  it("reads a newly selected version of the same file name", async () => {
    const firstImport = vi.fn().mockResolvedValue({ ok: true, document: importedDocument });
    const updatedDocument = { ...importedDocument, campaign: { ...importedDocument.campaign, identity: { ...importedDocument.campaign.identity, warband_name: "Banda actualizada" } } };
    const updatedImport = vi.fn().mockResolvedValue({ ok: true, document: updatedDocument });
    vi.mocked(createService).mockReset()
      .mockReturnValueOnce({ createCampaign: vi.fn().mockResolvedValue({ ok: true }), subscribe: () => () => {}, run, prepareExport, markExported, isDirty: () => true, canUndo: () => false, current: () => document } as never)
      .mockReturnValueOnce({ importCampaign: firstImport, subscribe: () => () => {}, isDirty: () => false, canUndo: () => false, current: () => importedDocument } as never)
      .mockReturnValueOnce({ importCampaign: updatedImport, subscribe: () => () => {}, isDirty: () => false, canUndo: () => false, current: () => updatedDocument } as never);

    const { container } = render(<ProductApp />);
    await waitFor(() => expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]).not.toBeDisabled());
    fireEvent.click(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]);
    fireEvent.change(screen.getByLabelText("Nombre de Campaña"), { target: { value: "Campaña de prueba" } });
    fireEvent.click(screen.getByRole("button", { name: "Crear" }));
    await screen.findByText("Campaign workspace");

    const input = container.querySelector<HTMLInputElement>('input[type="file"]')!;
    for (const [text, file] of [["first", new File(["first"], "campaign.mordheim")], ["updated", new File(["updated"], "campaign.mordheim")]] as const) {
      Object.defineProperty(file, "text", { value: async () => text });
      fireEvent.change(input, { target: { files: [file] } });
    }
    await waitFor(() => expect(updatedImport).toHaveBeenCalledWith({ text: "updated", confirm_replace: true }));
    fireEvent.click(screen.getByRole("button", { name: "Campañas" }));
    expect(screen.getByText("Banda actualizada")).toBeInTheDocument();
  });

  it("warns on reload and asks before discarding an unexported campaign", async () => {
    render(<ProductApp />);
    await waitFor(() =>
      expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0].hasAttribute("disabled")).toBe(false),
    );

    fireEvent.click(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]);
    fireEvent.change(screen.getByLabelText("Nombre de Campaña"), { target: { value: "Campaña de prueba" } });
    fireEvent.click(screen.getByRole("button", { name: "Crear" }));

    expect(await screen.findByText("Campaign workspace")).toBeInTheDocument();
    const beforeUnload = new Event("beforeunload", { cancelable: true });
    expect(window.dispatchEvent(beforeUnload)).toBe(false);

    fireEvent.click(screen.getByRole("button", { name: "Campañas" }));
    fireEvent.click(screen.getByRole("button", { name: "Retirar" }));

    expect(screen.getByRole("dialog", { name: "Cambios Sin Exportar" })).toHaveTextContent("Cambios Sin Exportar");
    expect(screen.getByText("Banda de prueba")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Descartar" }));

    expect(screen.queryByText("Banda de prueba")).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Campaña" })).toBeInTheDocument();
  });

  it("keeps an unexported session when removal is cancelled", async () => {
    render(<ProductApp />);
    await waitFor(() =>
      expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0].hasAttribute("disabled")).toBe(false),
    );

    fireEvent.click(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]);
    fireEvent.change(screen.getByLabelText("Nombre de Campaña"), { target: { value: "Campaña de prueba" } });
    fireEvent.click(screen.getByRole("button", { name: "Crear" }));
    await screen.findByText("Campaign workspace");

    fireEvent.click(screen.getByRole("button", { name: "Campañas" }));
    fireEvent.click(screen.getByRole("button", { name: "Retirar" }));
    fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));

    expect(screen.queryByRole("dialog", { name: "Cambios Sin Exportar" })).not.toBeInTheDocument();
    expect(screen.getByText("Banda de prueba")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retirar" })).toBeInTheDocument();
  });

  it("keeps a dirty session loaded when export fails", async () => {
    render(<ProductApp />);
    await waitFor(() =>
      expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0].hasAttribute("disabled")).toBe(false),
    );

    fireEvent.click(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]);
    fireEvent.change(screen.getByLabelText("Nombre de Campaña"), { target: { value: "Campaña de prueba" } });
    fireEvent.click(screen.getByRole("button", { name: "Crear" }));
    await screen.findByText("Campaign workspace");

    fireEvent.click(screen.getByRole("button", { name: "Guardar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo exportar la campaña.");
    expect(markExported).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Campañas" }));
    expect(screen.getByText("Banda de prueba")).toBeInTheDocument();
    expect(screen.getByText("Cambios Sin Exportar")).toBeInTheDocument();
  });

  it("exports before removing a dirty session", async () => {
    const createObjectURL = vi.fn(() => "blob:mock");
    const revokeObjectURL = vi.fn();
    const anchorClick = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => undefined);
    vi.stubGlobal("URL", { createObjectURL, revokeObjectURL });
    prepareExport.mockResolvedValue({
      ok: true,
      payload: { filename: "campaign.mordheim", text: "{}" },
      document,
    });

    render(<ProductApp />);
    await waitFor(() =>
      expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0].hasAttribute("disabled")).toBe(false),
    );
    fireEvent.click(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]);
    fireEvent.change(screen.getByLabelText("Nombre de Campaña"), { target: { value: "Campaña de prueba" } });
    fireEvent.click(screen.getByRole("button", { name: "Crear" }));
    await screen.findByText("Campaign workspace");

    fireEvent.click(screen.getByRole("button", { name: "Campañas" }));
    fireEvent.click(screen.getByRole("button", { name: "Retirar" }));
    fireEvent.click(screen.getByRole("button", { name: "Exportar y retirar" }));

    await waitFor(() => expect(markExported).toHaveBeenCalledWith(document));
    expect(screen.queryByText("Banda de prueba")).not.toBeInTheDocument();
    anchorClick.mockRestore();
    vi.unstubAllGlobals();
  });

  it("renames a session through the campaign service", async () => {
    render(<ProductApp />);
    await waitFor(() =>
      expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0].hasAttribute("disabled")).toBe(false),
    );

    fireEvent.click(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]);
    fireEvent.change(screen.getByLabelText("Nombre de Campaña"), { target: { value: "Campaña de prueba" } });
    fireEvent.click(screen.getByRole("button", { name: "Crear" }));
    await screen.findByText("Campaign workspace");

    fireEvent.click(screen.getByRole("button", { name: "Campañas" }));
    fireEvent.click(screen.getByRole("button", { name: "Renombrar" }));
    fireEvent.change(screen.getByLabelText("Nombre de Campaña"), { target: { value: "Renombrada" } });
    fireEvent.click(screen.getByRole("button", { name: "OK" }));

    await waitFor(() => expect(run).toHaveBeenCalledWith("renameCampaign", { name: "Renombrada" }));
    await waitFor(() => expect(screen.queryByRole("button", { name: "OK" })).not.toBeInTheDocument());
  });

  it("keeps the rename form open and announces a rejected action", async () => {
    run.mockResolvedValueOnce({ ok: false, message: "Rename rejected" });
    render(<ProductApp />);
    await waitFor(() => expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]).not.toBeDisabled());
    fireEvent.click(screen.getAllByRole("button", { name: "Nueva Campaña" })[0]);
    fireEvent.click(screen.getByRole("button", { name: "Crear" }));
    await screen.findByText("Campaign workspace");

    fireEvent.click(screen.getByRole("button", { name: "Campañas" }));
    fireEvent.click(screen.getByRole("button", { name: "Renombrar" }));
    fireEvent.change(screen.getByLabelText("Nombre de Campaña"), { target: { value: "Renombrada" } });
    fireEvent.click(screen.getByRole("button", { name: "OK" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo cambiar el nombre.");
    expect(screen.getByRole("button", { name: "OK" })).toBeInTheDocument();
  });
});

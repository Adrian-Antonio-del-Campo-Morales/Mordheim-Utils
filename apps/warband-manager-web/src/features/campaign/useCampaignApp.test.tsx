import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom/vitest";

import { CampaignAppProvider, localizeErrorMessage, useCampaignApp } from "./useCampaignApp";

function Notice() {
  const app = useCampaignApp();
  return app.error ? <output role="alert">{app.error}</output> : null;
}

function Recruit() {
  const app = useCampaignApp();
  return <button onClick={() => void app.runAction("recruitBandProfile", { profile_id: "matriarch" })}>Reclutar</button>;
}

describe("shared campaign action errors", () => {
  it.each([
    ["Resolve exploration and its follow-ups before continuing.", "Falta resolver el paso «Exploración» y sus seguimientos."],
    ["Not enough gold: 35 gc needed, 20 available.", "No hay suficientes CO: se necesitan 35 y hay 20 disponibles."],
    ["Not enough gold: 35 gc needed, 20 gc available.", "No hay suficientes CO: se necesitan 35 y hay 20 disponibles."],
    ["Not enough gold: 35 gc needed.", "No hay suficientes CO: se necesitan 35."],
    ["Not enough wyrdstone shard(s): 3 needed, 1 available.", "No hay suficientes fragmentos de piedra bruja: se necesitan 3 y hay 1 disponibles."],
    ["Unknown warrior id: hero-7.", "No se encuentra el identificador de guerrero: hero-7."],
    ["Profile \"captain\" is not available to this warband.", "El perfil «captain» no está disponible para esta banda."],
    ["Groups of \"swordsman\" hold at most 5 models.", "Los grupos de «swordsman» pueden tener como máximo 5 miniaturas."],
    ["Only 2 unassigned copy/copies are available.", "Solo hay 2 copia(s) sin asignar disponible(s)."],
    ["Battle numbers must be unique.", "Los números de batalla deben ser únicos."],
    ["A future engine error.", "No se pudo completar la acción: A future engine error."],
  ])("translates known error %s", (message, expected) => {
    expect(localizeErrorMessage(message, "es")).toBe(expected);
  });

  it("shows a rejection raised by a nested action in the visible campaign notice", async () => {
    const service = {
      current: () => null,
      isDirty: () => false,
      subscribe: () => () => undefined,
      run: vi.fn().mockResolvedValue({ ok: false, reason: "limit_reached", message: "Roster limit reached (1/1)." }),
    } as never;
    render(<CampaignAppProvider service={service} locale="es"><Notice /><Recruit /></CampaignAppProvider>);

    await userEvent.click(screen.getByRole("button", { name: "Reclutar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Se ha alcanzado el límite de la lista (1/1).");
  });
});

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { knowledgeName } from "./displayText";
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
    ["Unknown warrior id: hero-7.", "No se pudo completar la acción."],
    ["Only 2 unassigned copy/copies are available.", "Solo hay 2 copia(s) sin asignar disponible(s)."],
    ["Battle numbers must be unique.", "Los números de batalla deben ser únicos."],
    ["A future engine error.", "No se pudo completar la acción."],
  ])("translates known error %s", (message, expected) => {
    expect(localizeErrorMessage(message, "es")).toBe(expected);
  });

  it.each([
    ["Profile \"captain\" is not available to this warband.", "captain", "Capitán"],
    ["Groups of \"swordsman\" hold at most 5 models.", "swordsman", "Espadachín"],
    ["Roster limit for \"great-headhunter\" is 1 models.", "great-headhunter", "Gran Cazacabezas"],
  ])("never exposes the known profile id in %s", (message, id, name) => {
    const reader = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "mordheim", bands: [], profiles: [{ id, names: { es: name, en: name } }], items: [], skills: [] });
    const localized = localizeErrorMessage(message, "es", (candidate) => knowledgeName(reader, "profile", candidate, "es"));
    expect(localized).toContain(name);
    expect(localized).not.toContain(id);
  });

  it("re-resolves an existing error when the active language changes", async () => {
    const service = { current: () => null, isDirty: () => false, subscribe: () => () => undefined,
      run: vi.fn().mockResolvedValue({ ok: false, reason: "invalid_input", message: "Battle numbers must be unique." }),
    } as never;
    const view = (locale: "es" | "en") => <CampaignAppProvider service={service} locale={locale}><Notice /><Recruit /></CampaignAppProvider>;
    const { rerender } = render(view("es"));
    await userEvent.click(screen.getByRole("button", { name: "Reclutar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Los números de batalla deben ser únicos.");
    rerender(view("en"));
    expect(screen.getByRole("alert")).toHaveTextContent("Battle numbers must be unique.");
    rerender(view("es"));
    expect(screen.getByRole("alert")).toHaveTextContent("Los números de batalla deben ser únicos.");
  });

  it.each(["knowledge.english-fallback", "toString"])("rejects injected message keys and raw arguments: %s", async (message_key) => {
    const service = { current: () => null, isDirty: () => false, subscribe: () => () => undefined,
      run: vi.fn().mockResolvedValue({ ok: false, reason: "invalid_input", message: "internal_tag", message_key, message_args: { text: "internal_tag" } }),
    } as never;
    render(<CampaignAppProvider service={service} locale="es"><Notice /><Recruit /></CampaignAppProvider>);
    await userEvent.click(screen.getByRole("button", { name: "Reclutar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("No se pudo completar la acción.");
  });

  it("shows a rejection raised by a nested action in the visible campaign notice", async () => {
    const service = {
      current: () => null,
      isDirty: () => false,
      subscribe: () => () => undefined,
      run: vi.fn().mockResolvedValue({ ok: false, reason: "limit_reached", message: "Roster limit for \"great-headhunter\" is 1 models." }),
    } as never;
    render(<CampaignAppProvider service={service} locale="es" profileName={(id) => knowledgeName(ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "mordheim", bands: [], profiles: [{ id: "great-headhunter", names: { es: "Gran Cazacabezas", en: "Great Headhunter" } }], items: [], skills: [] }), "profile", id, "es")}><Notice /><Recruit /></CampaignAppProvider>);

    await userEvent.click(screen.getByRole("button", { name: "Reclutar" }));

    const notice = await screen.findByRole("alert");
    expect(notice).toHaveTextContent("El límite de lista para «Gran Cazacabezas» es de 1 miniaturas.");
    expect(notice).not.toHaveTextContent("great-headhunter");
  });
});

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";

import { App } from "./App";

describe("App shell (P3.1)", () => {
  it("renders the empty shell without importing domain code", async () => {
    render(<App />);
    await screen.findByRole("alert");
    expect(screen.getByRole("heading", { level: 1 })).toHaveTextContent(
      "Campaña",
    );
    const navigation = screen.getByRole("navigation", { name: /Navegación Principal|Primary/ });
    expect(navigation).toContainElement(screen.getByRole("button", { name: "Campaña" }));
    expect(navigation).toContainElement(screen.getByRole("button", { name: "Reglas" }));
    expect(navigation).toContainElement(screen.getByRole("button", { name: "Ajustes" }));
  });

  it("navigates to settings from the primary navigation", async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole("button", { name: "Ajustes" }));
    expect(screen.getByRole("heading", { name: "Ajustes" })).toBeInTheDocument();
  });

  it("offers mobile navigation and the compact actions menu", async () => {
    const user = userEvent.setup();
    render(<App />);

    const mobileNavigation = screen.getByRole("navigation", { name: "Navegación móvil" });
    expect(mobileNavigation).toContainElement(screen.getByRole("button", { name: "Campaña · móvil" }));
    await user.click(screen.getByRole("button", { name: "Más acciones" }));

    const menu = screen.getByRole("dialog", { name: "Más acciones" });
    expect(menu).toHaveTextContent("Campañas");
    expect(menu).toHaveTextContent("Exportar PDF");
  });
});

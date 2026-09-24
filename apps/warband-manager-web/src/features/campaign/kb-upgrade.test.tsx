/**
 * P5.2 final acceptance (KB bundling decision): the shell upgrades from the
 * synchronous fake composition to the real P4.3 reader once
 * `knowledge/knowledge-web.json` fetches and validates. Degradation on
 * fetch failure is a *status notice*, never an alert in the user-action
 * error seam.
 */
import { describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { ProductApp } from "../../ProductApp";

/** Artefact subset big enough to prove real ids resolve (sisters band). */
const artefact = {
  schema_version: 1,
  ruleset: "mordheim",
  collections: ["mordheim"],
  bands: [
    {
      id: "sisters-of-sigmar",
      name: "Sisters of Sigmar",
      names: { en: "Sisters of Sigmar", es: "Hermanas de Sigmar" },
      collection: "mordheim",
      roster: { minimum_models: 3, maximum_models: 15, starting_gold: 500, members: [] },
    },
  ],
  profiles: [],
  items: [],
  skills: [],
};

function stubFetchWith(body: unknown, status = 200): void {
  vi.stubGlobal(
    "fetch",
    vi.fn(() =>
      Promise.resolve(
        status === 200
          ? new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } })
          : new Response("nope", { status }),
      ),
    ),
  );
}

describe("P5.2 acceptance — real KB loading", () => {
  it("fetches the artefact URL and enables the shell", async () => {
    stubFetchWith(artefact);
    render(<ProductApp />);
    await waitFor(() =>
      expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0].hasAttribute("disabled")).toBe(false),
    );
    expect(fetch).toHaveBeenCalledWith("knowledge/knowledge-web.json", { cache: "no-cache" });
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("announces a network error instead of silently using sample data", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("offline"))),
    );
    render(<ProductApp />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("No se pudo cargar la base de conocimiento.");
    });
    expect(screen.getByRole("alert")).not.toHaveTextContent("offline");
  });

  it("announces an HTTP failure", async () => {
    stubFetchWith({ error: "nope" }, 404);
    render(<ProductApp />);
    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent("No se pudo cargar la base de conocimiento.");
    });
    expect(screen.getByRole("alert")).not.toHaveTextContent("HTTP 404");
  });

  it("retries a transient KB failure and restores the shell", async () => {
    let attempts = 0;
    vi.stubGlobal("fetch", vi.fn(() => {
      attempts += 1;
      return attempts === 1
        ? Promise.reject(new TypeError("offline"))
        : Promise.resolve(new Response(JSON.stringify(artefact), { status: 200, headers: { "content-type": "application/json" } }));
    }));
    render(<ProductApp />);
    const alert = await screen.findByRole("alert");
    expect(alert).not.toHaveTextContent("offline");
    fireEvent.click(screen.getByRole("button", { name: "Reintentar" }));
    await waitFor(() =>
      expect(screen.getAllByRole("button", { name: "Nueva Campaña" })[0].hasAttribute("disabled")).toBe(false),
    );
    expect(screen.queryByRole("alert")).toBeNull();
  });
});

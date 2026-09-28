/**
 * T12 fase D — the shell downloads the campaign catalogue on demand.
 *
 * Product-level proof over the **published** artefact (the same files
 * `outputs/web-public/knowledge` serves, read through a counting fetch stub):
 *
 * 1. opening the application and choosing a warband pays only the initial
 *    document (plus the prose and presentation fragments it already loaded) —
 *    the catalogue fragment is never requested at startup;
 * 2. the first flow that needs it (the rules catalogue page, construction)
 *    requests it exactly once, and the flow then behaves as before;
 * 3. a missing fragment produces a visible, localized error instead of an
 *    empty catalogue or a technical identifier.
 */
import { describe, expect, it, vi } from "vitest";
import { existsSync, readFileSync } from "node:fs";
import { basename, resolve } from "node:path";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { ProductApp } from "@src/ProductApp";
import { translate } from "@src/features/campaign/i18n-core";

const KNOWLEDGE_DIR = resolve(process.cwd(), "../../outputs/web-public/knowledge");
const CATALOGUE_NAME = "knowledge-catalogue.json";
const hasArtefact = existsSync(resolve(KNOWLEDGE_DIR, CATALOGUE_NAME));

/** Serves the published knowledge directory and counts every request. */
function publishedArtefactServer(options: { catalogue?: "ok" | "missing" } = {}) {
  const requested: string[] = [];
  const fetchFn = vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input);
    requested.push(url);
    const name = basename(new URL(url, "http://localhost/").pathname);
    if (name === CATALOGUE_NAME && options.catalogue === "missing") {
      return new Response("missing", { status: 404 });
    }
    const file = resolve(KNOWLEDGE_DIR, name);
    if (!existsSync(file)) return new Response("missing", { status: 404 });
    return new Response(readFileSync(file, "utf-8"), {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  });
  return {
    fetchFn: fetchFn as unknown as typeof fetch,
    requested,
    catalogueRequests: (): number => requested.filter((url) => url.endsWith(CATALOGUE_NAME)).length,
  };
}

const labels = {
  newCampaign: translate({ key: "ui.d325957ad08f" }, "es"),
  campaignName: translate({ key: "ui.dc16c1d56cf1" }, "es"),
  create: translate({ key: "ui.f4c21e1ded7f" }, "es"),
  rules: translate({ key: "ui.bf1282ddb578" }, "es"),
  searchRules: translate({ key: "ui.a608c2f61aa0" }, "es"),
  loadingCatalogue: translate({ key: "shell.loading-catalogue" }, "es"),
  pdf: translate({ key: "ui.4a2705e83df4" }, "es"),
};

describe.skipIf(!hasArtefact)("T12 fase D — lazy campaign catalogue in the shell", () => {
  it(
    "loads only the initial document at startup and the catalogue on the first flow that needs it",
    async () => {
      const server = publishedArtefactServer();
      vi.stubGlobal("fetch", server.fetchFn);

      render(<ProductApp />);
      await waitFor(
        () => expect(screen.getAllByRole("button", { name: labels.newCampaign })[0]).not.toBeDisabled(),
        { timeout: 15_000 },
      );

      // Startup: the initial document plus the fragments it has always loaded
      // eagerly (prose and presentation). The campaign catalogue is not among
      // them.
      expect(server.requested.map((url) => basename(new URL(url, "http://localhost/").pathname)).sort()).toEqual([
        "display-text.json",
        "knowledge-web.json",
        "rules-prose.json",
      ]);
      expect(server.catalogueRequests()).toBe(0);

      // First flow that needs the catalogue: the rules catalogue page.
      fireEvent.click(screen.getByRole("button", { name: labels.rules }));
      await waitFor(() => expect(server.catalogueRequests()).toBe(1));
      await screen.findByLabelText(labels.searchRules);

      // Construction and starting equipment: the same catalogue, already loaded.
      fireEvent.click(screen.getByRole("button", { name: labels.newCampaign }));
      fireEvent.click(await screen.findByRole("radio", { name: /Hermanas de Sigmar/ }));
      fireEvent.change(screen.getByLabelText(labels.campaignName), { target: { value: "Campaña perezosa" } });
      fireEvent.click(screen.getByRole("button", { name: labels.create }));

      // The draft workspace is the construction flow: it opened with the loaded
      // catalogue (no loading notice, export/PDF available) and the whole run
      // paid for the catalogue exactly once.
      await waitFor(() => {
        const alert = screen.queryByRole("alert");
        if (alert) throw new Error(`create failed: ${alert.textContent ?? ""}`);
        expect(screen.getByRole("button", { name: labels.pdf })).not.toBeDisabled();
      }, { timeout: 15_000 });
      expect(server.catalogueRequests()).toBe(1);
      expect(screen.queryByText(labels.loadingCatalogue)).toBeNull();
    },
    30_000,
  );

  it(
    "announces a missing catalogue instead of showing an empty catalogue",
    async () => {
      const server = publishedArtefactServer({ catalogue: "missing" });
      vi.stubGlobal("fetch", server.fetchFn);

      render(<ProductApp />);
      await waitFor(
        () => expect(screen.getAllByRole("button", { name: labels.newCampaign })[0]).not.toBeDisabled(),
        { timeout: 15_000 },
      );
      expect(server.catalogueRequests()).toBe(0);

      fireEvent.click(screen.getByRole("button", { name: labels.rules }));

      const alert = await screen.findByRole("alert");
      // Localized, actionable notice: never a raw URL or a technical id.
      expect(alert).toHaveTextContent(translate({ key: "ui.3d733bbc4609" }, "es"));
      expect(alert.textContent ?? "").not.toMatch(/knowledge-catalogue|HTTP 404/);
      expect(screen.queryByLabelText(labels.searchRules)).toBeNull();
    },
    30_000,
  );
});

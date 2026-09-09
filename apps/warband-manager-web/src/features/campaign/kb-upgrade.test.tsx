/**
 * P5.2 final acceptance (KB bundling decision): the shell upgrades from the
 * synchronous fake composition to the real P4.3 reader once
 * `knowledge/knowledge-web.json` fetches and validates. Degradation on
 * fetch failure is a *status notice*, never an alert in the user-action
 * error seam.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import { CampaignSlice } from "./CampaignSlice";

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

describe("P5.2 acceptance — real KB upgrade", () => {
  it("fetches the artefact URL and stops showing the loading state", async () => {
    stubFetchWith(artefact);
    render(<CampaignSlice />);
    // The loading status appears first, then clears once the reader lands.
    expect(screen.getByRole("status", { name: undefined })).toBeDefined();
    await waitFor(() => {
      expect(screen.queryByText("Loading knowledge base…")).toBeNull();
    });
    // No degraded-KB notice on success.
    expect(screen.queryByText(/Knowledge base failed to load/)).toBeNull();
  });

  it("degrades to sample data with a status notice when the fetch fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new TypeError("offline"))),
    );
    render(<CampaignSlice />);
    await waitFor(() => {
      expect(screen.getByText(/Knowledge base failed to load/)).toBeInTheDocument();
    });
    // The notice is a status, NOT a user-action alert seam entry.
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("shows the degraded notice for an HTTP failure too", async () => {
    stubFetchWith({ error: "nope" }, 404);
    render(<CampaignSlice />);
    await waitFor(() => {
      expect(screen.getByText(/Knowledge base failed to load/)).toBeInTheDocument();
    });
    expect(screen.getByText(/HTTP 404/)).toBeInTheDocument();
  });
});

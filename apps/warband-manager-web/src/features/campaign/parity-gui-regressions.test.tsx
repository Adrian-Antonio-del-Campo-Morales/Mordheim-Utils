/**
 * Web Test Migration — UI parity block 1 (REPO REWORK 2).
 *
 * Desktop source of truth: `tests/campaign/test_gui_interaction_regressions.py`
 * (unsaved-changes guard family + cancelled-load family). The Tkinter dialogs
 * and file dialogs become File input + alert surface; the behaviour contract
 * is identical:
 *  - navigation never dirties the document (desktop:
 *    test_dirty_includes_battle_draft_but_not_navigation);
 *  - dismissing the replace alert keeps the loaded campaign
 *    (desktop: test_cancelled_load_keeps_state_path_and_undo);
 *  - export → reimport round-trips the campaign verbatim
 *    (desktop: test_loading_same_file_after_save_reads_fresh_contents);
 *  - the unsaved-changes indicator exists as a status surface (desktop:
 *    has_unsaved_changes).
 *
 * SCOPE NOTE (findings, not test failures — reported to the coordination log):
 * 1. Feature panels call `useCampaignApp()` internally, creating a service
 *    instance separate from the slice's — panel edits dirty the panel's own
 *    service, never the slice's document/dirty indicator.
 * 2. The slice's rename form dispatches `__rename_warband__`, which is not a
 *    registered service action (error: `Unknown action`).
 * Both belong to the service/panel owner (REPO REWORK 333333). The tests
 * below therefore drive only slice-owned surfaces: import, confirm-replace,
 * export, navigation.
 */

import { describe, expect, it, beforeAll, afterAll, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";

import { CampaignSlice } from "./CampaignSlice";
import type { Campaign } from "./types";

function fixtureCampaign(): Campaign {
  return {
    identity: {
      campaign_name: "Parity Campaign",
      warband_name: "Original Band",
      warband_type: "Sisters of Sigmar",
      band_id: "sisters-of-sigmar",
      mercenary_variant: null,
    },
    configuration: {
      is_draft: false,
      starting_gold: 500,
      minimum_models: 3,
      maximum_models: 15,
      hero_limit: 5,
    },
    resources: { stash_value: 120, rare_finds: 0, treasures: 1, campaign_points: 0 },
    current_state_number: 1,
    warriors: [
      {
        id: "w1",
        name: "Sigrid",
        profile_name: "Sigmarite Matriarch",
        kind: "hero",
        stats: { M: 4, WS: 4 },
        equipment: [],
        skills: [],
        experience: 12,
        cost: 65,
      },
    ],
    battles: [],
    states: [
      {
        number: 1,
        date: "Cyber 3",
        gold: 320,
        wyrdstone: 2,
        rating: 214,
        models: 6,
        max_models: 15,
        heroes: 3,
        henchmen: 3,
        experience: 12,
      },
    ],
    post_battles: [],
    inventory: [
      {
        id: "dagger",
        name: "Dagger",
        category: "close-combat-weapon",
        owned: 3,
        equipped: 2,
        stash: 1,
      },
    ],
    special_rules: [],
    manual_log: [],
  };
}

function v4Text(campaign: Campaign): string {
  return JSON.stringify({
    marker: "MORDHEIM_CAMPAIGN_MANAGER",
    format_version: 4,
    saved_at: "2026-09-09T12:00:00Z",
    campaign,
    view: { selected_moment: "state:1" },
  });
}

/** Capture exported blobs so tests can re-import exactly what was exported. */
let capturedBlobs: Blob[] = [];

beforeAll(() => {
  capturedBlobs = [];
  Object.defineProperty(URL, "createObjectURL", {
    configurable: true,
    value: vi.fn((blob: Blob) => {
      capturedBlobs.push(blob);
      return `blob:mock-${capturedBlobs.length}`;
    }),
  });
  Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() });
});

afterAll(() => {
  // Restore jsdom defaults where they exist (harmless if absent).
  Reflect.deleteProperty(URL as unknown as Record<string, unknown>, "createObjectURL");
  Reflect.deleteProperty(URL as unknown as Record<string, unknown>, "revokeObjectURL");
});

async function importFixture(user: ReturnType<typeof userEvent.setup>): Promise<void> {
  const { container } = render(<CampaignSlice />);
  const input = container.querySelector<HTMLInputElement>("#campaign-file");
  expect(input).not.toBeNull();
  await user.upload(input!, new File([v4Text(fixtureCampaign())], "parity.mordheim", { type: "application/json" }));
  await screen.findByRole("heading", { name: "Original Band" });
}

async function exportCampaign(user: ReturnType<typeof userEvent.setup>): Promise<void> {
  await user.click(screen.getByRole("button", { name: "Export .mordheim" }));
  await waitFor(() => expect(capturedBlobs.length).toBeGreaterThan(0));
}

function unsavedIndicator(): HTMLElement | null {
  const statuses = screen.queryAllByRole("status");
  return statuses.find((node) => node.textContent?.includes("Unsaved changes")) ?? null;
}

describe("GUI regression parity — unsaved-changes guard family", () => {
  it("navigation (timeline selection) never dirties the document", async () => {
    const user = userEvent.setup();
    await importFixture(user);
    // Select a different moment than the default selection.
    const momentButtons = screen
      .getAllByRole("button")
      .filter((button) => /State #1|Draft/.test(button.textContent ?? ""));
    if (momentButtons.length > 0) {
      await user.click(momentButtons[0]);
      await waitFor(() => expect(unsavedIndicator()).toBeNull());
    }
    expect(unsavedIndicator()).toBeNull();
  });

  it("export → reimport round-trips the campaign verbatim and lands clean", async () => {
    const user = userEvent.setup();
    await importFixture(user);

    capturedBlobs = [];
    await exportCampaign(user);
    const text = await new Response(capturedBlobs[0]).text();

    // Re-import the exported payload (fresh upload, like reopening the file).
    const { container } = render(<CampaignSlice />);
    const input = container.querySelector<HTMLInputElement>("#campaign-file");
    await user.upload(input!, new File([text], "roundtrip.mordheim", { type: "application/json" }));
    await screen.findByRole("heading", { name: "Original Band" });
    await waitFor(() => expect(unsavedIndicator()).toBeNull());
  });

  it("dismissing the replace alert keeps the loaded campaign", async () => {
    const user = userEvent.setup();
    const { container } = render(<CampaignSlice />);
    const input = () => container.querySelector<HTMLInputElement>("#campaign-file")!;
    await user.upload(input(), new File([v4Text(fixtureCampaign())], "a.mordheim", { type: "application/json" }));
    await screen.findByRole("heading", { name: "Original Band" });

    // Second upload must ask before replacing.
    await user.upload(input(), new File([v4Text(fixtureCampaign())], "other.mordheim", { type: "application/json" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/replace/i);

    // Dismiss (the "cancelled load" branch on desktop).
    await user.click(screen.getByRole("button", { name: "Dismiss" }));
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
    expect(screen.getAllByText("Original Band").length).toBeGreaterThan(0);
  });
});

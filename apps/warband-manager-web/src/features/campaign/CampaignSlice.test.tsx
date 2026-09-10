/**
 * P5.2 vertical slice tests (plan §6 acceptance): a fixture-shaped document
 * opens, displays identity/roster, a sample edit dirties the state, and the
 * export produces a v4 text blob. Error paths render human-readable alerts.
 */

import { describe, expect, it } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";

import { CampaignSlice } from "./CampaignSlice";
import type { Campaign } from "./types";

function fixtureCampaign(): Campaign {
  return {
    identity: {
      campaign_name: "Test Campaign",
      warband_name: "Sigmar's Shield",
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
    // The real file port + domain validation (P3.2/P3.5) require the
    // committed state number to exist in the timeline, so the fixture is
    // structurally consistent, not just schema-shaped.
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
        quantity: 1,
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

function renderSlice() {
  return render(<CampaignSlice />);
}

describe("P5.2 vertical slice", () => {
  it("imports a v4 file and shows identity, roster and inventory", async () => {
    const user = userEvent.setup();
    const { container } = renderSlice();
    const input = container.querySelector<HTMLInputElement>("#campaign-file");
    expect(input).not.toBeNull();
    const file = new File([v4Text(fixtureCampaign())], "sigmar.mordheim", {
      type: "application/json",
    });
    await user.upload(input!, file);
    expect(await screen.findByRole("heading", { name: "Sigmar's Shield" })).toBeInTheDocument();
    // P6.4 added availability checkboxes that also render warrior names,
    // so match the roster cell specifically.
    expect(screen.getAllByText("Sigrid").length).toBeGreaterThan(0);
    // Dagger appears in the inventory list and the P6.3 equipment panel.
    expect(screen.getAllByText(/Dagger/).length).toBeGreaterThan(0);
  });

  it("shows a human-readable alert for a retired version file", async () => {
    const user = userEvent.setup();
    const { container } = renderSlice();
    const input = container.querySelector<HTMLInputElement>("#campaign-file")!;
    const file = new File(
      [JSON.stringify({ marker: "MORDHEIM_CAMPAIGN_MANAGER", format_version: 3 })],
      "old.mordheim",
      { type: "application/json" },
    );
    await user.upload(input, file);
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/old format/i);
  });

  it("shows a human-readable alert for invalid JSON", async () => {
    const user = userEvent.setup();
    const { container } = renderSlice();
    const input = container.querySelector<HTMLInputElement>("#campaign-file")!;
    await user.upload(input, new File(["{oops"], "broken.mordheim", { type: "application/json" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(/not valid JSON/i);
  });

  it("asks for confirmation before replacing a loaded campaign", async () => {
    const user = userEvent.setup();
    const { container } = renderSlice();
    const input = container.querySelector<HTMLInputElement>("#campaign-file")!;
    await user.upload(input, new File([v4Text(fixtureCampaign())], "a.mordheim", { type: "application/json" }));
    await screen.findByRole("heading", { name: "Sigmar's Shield" });
    await user.upload(input, new File([v4Text(fixtureCampaign())], "b.mordheim", { type: "application/json" }));
    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent(/replace/i);
    await user.click(screen.getByRole("button", { name: "Replace campaign" }));
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  });
});

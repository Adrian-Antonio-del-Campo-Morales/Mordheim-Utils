/**
 * P6.5 component tests: the injuries panel renders the read model and
 * dispatches recovery/follow-up actions through the shared CampaignAppView
 * seam (mocked here; the default-deps composition is covered by the slice
 * tests). Rejections surface via the seam's error, never thrown.
 */
import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";

import type { CampaignDocument } from "../campaign/types";
import { InjuriesPanel } from "./InjuriesPanel";
import { useCampaignApp } from "../campaign/useCampaignApp";

vi.mock("../campaign/useCampaignApp", () => ({
  useCampaignApp: vi.fn(),
}));

const useCampaignAppMock = vi.mocked(useCampaignApp);

const document = {
  campaign: {
    identity: { band_id: "witch_hunters", name: "Sigmar's Shield", is_draft: false },
    configuration: {
      band_id: "witch_hunters",
      band_name: "Witch Hunters",
      is_draft: false,
      starting_gold: 500,
      minimum_models: 3,
      maximum_models: 15,
      hero_limit: 4,
    },
    resources: { gold: 100, wyrdstone_shards: 0 },
    current_state_number: 1,
    warriors: [
      {
        id: "w1",
        name: "Sigrid",
        profile_name: "Captain",
        kind: "hero",
        stats: { M: 4, WS: 4 },
        equipment: [],
        skills: [],
        experience: 5,
        cost: 35,
        games_to_miss: 2,
        absence_reason: "Smashed hand",
        manual_log: [],
      },
      {
        id: "w2",
        name: "Wilhelm",
        profile_name: "Warrior",
        kind: "hero",
        stats: { M: 4, WS: 3 },
        equipment: [],
        skills: [],
        experience: 2,
        cost: 25,
        condition: "Injured",
        condition_detail: "eye_injury",
        manual_log: [],
      },
    ],
    battles: [],
    states: [],
    post_battles: [
      {
        battle_number: 1,
        complete: false,
        active_step: 4,
        completed_steps: [0, 1, 2, 3],
        review_open: false,
        pending_follow_ups: [
          {
            id: "injury:w1:mangled_leg",
            type: "injury_roll",
            warrior_id: "w1",
            result_id: "mangled_leg",
            description: "Roll",
          },
        ],
      },
    ],
    inventory: [],
    special_rules: [],
    manual_log: [],
  },
  view: {},
} as unknown as CampaignDocument;

function harness(overrides: Partial<ReturnType<typeof defaultView>> = {}) {
  useCampaignAppMock.mockReturnValue({ ...defaultView(), ...overrides });
}

function defaultView() {
  return {
    document: null,
    error: null as string | null,
    dirty: false,
    kbLoading: false,
    kbError: null,
    importFile: vi.fn().mockResolvedValue(undefined),
    confirmReplace: vi.fn().mockResolvedValue(undefined),
    exportFile: vi.fn().mockResolvedValue(undefined),
    runAction: vi.fn().mockResolvedValue(undefined),
    selectMoment: vi.fn(),
    clearError: vi.fn(),
  };
}

describe("InjuriesPanel", () => {
  it("shows condition, missed games and the pending roll count", () => {
    harness();
    render(<InjuriesPanel document={document} />);
    expect(screen.getByRole("heading", { name: "Injuries & Recovery" })).toBeInTheDocument();
    expect(screen.getByText("2 (Smashed Hand)")).toBeInTheDocument();
    expect(screen.getByText("Injured", { exact: false })).toBeInTheDocument();
    expect(screen.getByText(/1 unresolved injury roll/)).toBeInTheDocument();
    // Wilhelm has no absence: recovery is disabled for him.
    expect(screen.getByLabelText("Recover Wilhelm")).toBeDisabled();
    expect(screen.getByLabelText("Recover Sigrid")).toBeEnabled();
  });

  it("serves a missed game through the service", async () => {
    const view = defaultView();
    harness({ ...view });
    render(<InjuriesPanel document={document} />);
    fireEvent.click(screen.getByLabelText("Recover Sigrid"));
    await vi.waitFor(() => {
      expect(view.runAction).toHaveBeenCalledWith("recoverWarrior", { warrior_id: "w1" });
    });
  });

  it("resolves a parked follow-up through the service", async () => {
    const view = defaultView();
    harness({ ...view });
    render(<InjuriesPanel document={document} />);
    fireEvent.click(screen.getByLabelText("Resolve injury roll injury:w1:mangled_leg"));
    await vi.waitFor(() => {
      expect(view.runAction).toHaveBeenCalledWith(
        "resolveInjuryFollowUp",
        expect.objectContaining({ follow_up_id: "injury:w1:mangled_leg" }),
      );
    });
  });

  it("surfaces the seam error instead of throwing", () => {
    harness({ error: "Recovery rejected: not missing any games." });
    render(<InjuriesPanel document={document} />);
    expect(screen.getByRole("alert")).toHaveTextContent("Recovery rejected");
  });
});

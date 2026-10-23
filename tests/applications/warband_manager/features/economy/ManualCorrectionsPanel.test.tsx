import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import type { CampaignDocument } from "@src/features/campaign/types";
import type { CampaignAppService } from "@src/features/campaign/types";
import { CampaignAppProvider } from "@src/features/campaign/useCampaignApp";
import { ManualCorrectionsPanel } from "@src/features/economy/ManualCorrectionsPanel";

const document = {} as CampaignDocument;
const knowledge = { list: () => [{ item_id: "dagger", names: { en: "Dagger" } }] } as never;
const run = vi.fn().mockResolvedValue({ ok: true, document });
const service = { current: () => document, isDirty: () => false, subscribe: () => () => {}, run } as unknown as CampaignAppService;

async function setAdjustment(user: ReturnType<typeof userEvent.setup>, amount: number) {
  const button = screen.getByRole("button", { name: `Adjustment ${amount < 0 ? "−" : "+"}` });
  for (let index = 0; index < Math.abs(amount); index += 1) await user.click(button);
}

function renderPanel() {
  render(<CampaignAppProvider service={service}><ManualCorrectionsPanel document={document} knowledge={knowledge} /></CampaignAppProvider>);
}

describe("ManualCorrectionsPanel", () => {
  it("requires a reason and non-zero adjustment", () => {
    renderPanel();
    expect(screen.getByRole("button", { name: "Apply resource" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Add to stash" })).toBeDisabled();
  });

  it("dispatches a resource correction with the entered reason", async () => {
    renderPanel();
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText("Resource"), "gold_crowns");
    await user.type(screen.getByLabelText("Reason"), "Table correction");
    await setAdjustment(user, 5);
    await user.click(screen.getByRole("button", { name: "Apply resource" }));
    expect(run).toHaveBeenCalledWith("correctResource", { resource: "gold_crowns", delta: 5, reason: "Table correction" });
  });

  // Desktop parity: tests/python/campaign/test_gui_interaction_regressions.py
  //   test_numeric_input_accepts_integers, test_numeric_input_rejects_invalid_raw_values,
  //   test_resource_form_reports_invalid_input_without_mutation.

  it("treats a zero adjustment as a no-op", async () => {
    // test_numeric_input_accepts_integers: 0 -> 0, valid integer but no-op adjustment.
    run.mockClear();
    renderPanel();
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText("Resource"), "gold_crowns");
    await user.type(screen.getByLabelText("Reason"), "Zero");
    expect(screen.getByRole("button", { name: "Apply resource" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Apply resource" }));
    expect(run).not.toHaveBeenCalled();
  });

  it("dispatches a negative integer correction", async () => {
    renderPanel();
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText("Resource"), "gold_crowns");
    await user.type(screen.getByLabelText("Reason"), "Take three");
    await setAdjustment(user, -3);
    await user.click(screen.getByRole("button", { name: "Apply resource" }));
    expect(run).toHaveBeenCalledWith("correctResource", { resource: "gold_crowns", delta: -3, reason: "Take three" });
  });

});

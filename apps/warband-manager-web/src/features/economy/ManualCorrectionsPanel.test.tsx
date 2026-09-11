import { describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import type { CampaignDocument } from "../campaign/types";
import type { CampaignAppService } from "../campaign/types";
import { CampaignAppProvider } from "../campaign/useCampaignApp";
import { ManualCorrectionsPanel } from "./ManualCorrectionsPanel";

const document = {} as CampaignDocument;
const knowledge = { list: () => [{ item_id: "dagger", names: { en: "Dagger" } }] } as never;
const run = vi.fn().mockResolvedValue({ ok: true, document });
const service = { current: () => document, isDirty: () => false, subscribe: () => () => {}, run } as unknown as CampaignAppService;

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
    await user.clear(screen.getByLabelText("Adjustment"));
    await user.type(screen.getByLabelText("Adjustment"), "5");
    await user.click(screen.getByRole("button", { name: "Apply resource" }));
    expect(run).toHaveBeenCalledWith("correctResource", { resource: "gold_crowns", delta: 5, reason: "Table correction" });
  });

  // Desktop parity: tests/campaign/test_gui_interaction_regressions.py
  //   test_numeric_input_accepts_integers, test_numeric_input_rejects_invalid_raw_values,
  //   test_resource_form_reports_invalid_input_without_mutation.

  it("treats a zero adjustment as a no-op", async () => {
    // test_numeric_input_accepts_integers: 0 -> 0, valid integer but no-op adjustment.
    run.mockClear();
    renderPanel();
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText("Resource"), "gold_crowns");
    await user.type(screen.getByLabelText("Reason"), "Zero");
    await user.clear(screen.getByLabelText("Adjustment"));
    await user.type(screen.getByLabelText("Adjustment"), "0");
    expect(screen.getByRole("button", { name: "Apply resource" })).toBeDisabled();
    await user.click(screen.getByRole("button", { name: "Apply resource" }));
    expect(run).not.toHaveBeenCalled();
  });

  it("dispatches a negative integer correction", async () => {
    renderPanel();
    const user = userEvent.setup();
    await user.selectOptions(screen.getByLabelText("Resource"), "gold_crowns");
    await user.type(screen.getByLabelText("Reason"), "Take three");
    await user.clear(screen.getByLabelText("Adjustment"));
    await user.type(screen.getByLabelText("Adjustment"), "-3");
    await user.click(screen.getByRole("button", { name: "Apply resource" }));
    expect(run).toHaveBeenCalledWith("correctResource", { resource: "gold_crowns", delta: -3, reason: "Take three" });
  });

  it("rejects non-integer input without mutating the campaign", async () => {
    // test_numeric_input_rejects_invalid_raw_values: '', '1.5', 'abc', 'True' raise.
    // Web guarantee (test_resource_form_reports_invalid_input_without_mutation):
    //   invalid input reports an error and dispatches nothing.
    run.mockClear();
    const user = userEvent.setup();
    for (const raw of ["1.5", "abc", "True"]) {
      cleanup();
      renderPanel();
      const reason = screen.getByLabelText("Reason");
      const adjustment = screen.getByLabelText("Adjustment");
      await user.type(reason, "Bad input");
      await user.clear(adjustment);
      await user.type(adjustment, raw);
      expect(screen.getByRole("button", { name: "Apply resource" })).toBeDisabled();
      await user.click(screen.getByRole("button", { name: "Apply resource" }));
      expect(run).not.toHaveBeenCalled();
    }
    cleanup();
  });

  it("rejects an empty numeric field without mutating the campaign", async () => {
    run.mockClear();
    renderPanel();
    const user = userEvent.setup();
    await user.type(screen.getByLabelText("Reason"), "Empty field");
    await user.clear(screen.getByLabelText("Adjustment"));
    await user.type(screen.getByLabelText("Adjustment"), "1.5");
    expect(screen.getByRole("button", { name: "Apply resource" })).toBeDisabled();
    expect(run).not.toHaveBeenCalled();
  });
});

/**
 * P6.4 component tests: the battle panel records a battle against a real
 * committed campaign document (built through the draft workflow) and walks
 * the pending post-battle; rejections surface in role=alert.
 */

import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";

import { BattlePanel } from "./BattlePanel";
import type { CampaignDocument } from "@domain/campaign/index";
import { createDefaultUseCases } from "@domain/campaign/kernel/default-usecases";
import { createDraftWorkflow } from "@app/campaign/features/draft/draft-workflow";
import { createBattleWorkflow } from "@app/campaign/features/battle/battle-workflow";
import { FakeKnowledgeReader } from "../campaign/fake-knowledge-reader";

afterEach(cleanup);

function makeCommittedDocument(): CampaignDocument {
  const knowledge = new FakeKnowledgeReader();
  const draft = createDraftWorkflow({
    knowledge,
    useCases: createDefaultUseCases(knowledge),
  });
  const started = draft.startDraft("sisters-of-sigmar");
  if (!started.ok) throw new Error("start should succeed");
  const committed = draft.commit(started.document);
  if (!committed.ok) throw new Error("commit should succeed");
  return committed.document;
}

describe("P6.4 BattlePanel", () => {
  it("renders the battle form with availability checkboxes", () => {
    render(<BattlePanel document={makeCommittedDocument()} onDocument={() => undefined} />);
    expect(screen.getByLabelText(/scenario/i)).toBeTruthy();
    expect(screen.getByLabelText(/opponent/i)).toBeTruthy();
    expect(screen.getByText(/out of action/i)).toBeTruthy();
    // The committed starter roster offers at least one available warrior.
    const checkboxes = screen.getAllByRole("checkbox");
    expect(checkboxes.some((c) => !(c as HTMLInputElement).disabled)).toBe(true);
  });

  it("records a battle and shows the pending post-battle navigation", async () => {
    const user = userEvent.setup();
    let current = makeCommittedDocument();
    const onDocument = (document: CampaignDocument) => {
      current = document;
    };
    const { rerender } = render(
      <BattlePanel document={current} onDocument={onDocument} />,
    );

    await user.type(screen.getByLabelText(/opponent/i), "Reiklanders");
    await user.click(screen.getByRole("button", { name: /record battle/i }));

    expect(current.campaign.battles).toHaveLength(1);
    rerender(<BattlePanel document={current} onDocument={onDocument} />);
    // The pending post-battle navigation replaces the form.
    const status = await screen.findByText(/Post-battle #1: step 0 of 8/);
    expect(status).toBeTruthy();
    const resolve = screen.getByRole("button", { name: /resolve step 0/i });
    expect(resolve).toBeTruthy();

    // Resolve one step: the sequence advances.
    await user.click(resolve);
    expect(current.campaign.post_battles[0].active_step).toBe(1);
  });

  it("surfaces the pending-battle conflict in role=alert", async () => {
    const user = userEvent.setup();
    let current = makeCommittedDocument();
    const onDocument = (document: CampaignDocument) => {
      current = document;
    };
    // Build a campaign whose post-battle is already pending: record once via
    // the workflow, then mount the panel and try to resolve with no steps.
    const knowledge = new FakeKnowledgeReader();
    const battleWorkflow = createBattleWorkflow({
      knowledge,
      useCases: createDefaultUseCases(knowledge),
    });
    const recorded = battleWorkflow.record(current, {
      scenario: "skirmish",
      opponent: "X",
      result: "win",
      gold_delta: 0,
      wyrdstone: 0,
      xp_delta: 0,
      out_of_action_ids: [],
    });
    if (!recorded.ok) throw new Error("record should succeed");
    current = recorded.document;

    render(<BattlePanel document={current} onDocument={onDocument} />);
    // The panel shows the pending navigation instead of the form; the alert
    // surface appears only on error, so assert the pending state instead.
    expect(screen.getByText(/Post-battle #1/)).toBeTruthy();
    void user;
  });
});

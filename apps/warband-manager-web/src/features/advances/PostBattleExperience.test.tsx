import { render, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CampaignAppProvider } from "../campaign/useCampaignApp";
import { PostBattleExperience } from "./PostBattleExperience";
import type { CampaignDocument } from "../campaign/types";

describe("PostBattleExperience", () => {
  it("applies calculated experience automatically when the phase opens", async () => {
    const document = { campaign: { warriors: [], battles: [{ number: 1, out_of_action_ids: [] }], post_battles: [{ battle_number: 1, complete: false, experience_applied: false, pending_follow_ups: [] }] }, view: {} } as unknown as CampaignDocument;
    const run = vi.fn().mockResolvedValue({ ok: true, document });
    const service = { current: () => document, isDirty: () => false, subscribe: () => () => undefined, run } as never;

    render(<CampaignAppProvider service={service}><PostBattleExperience document={document} knowledge={{} as never} locale="es" /></CampaignAppProvider>);

    await waitFor(() => expect(run).toHaveBeenCalledTimes(1));
    expect(run).toHaveBeenCalledWith("applyBattleExperience", {});
  });

  it("does not leave a removed casualty permanently pending", async () => {
    const document = { campaign: {
      warriors: [],
      battles: [{ number: 1, out_of_action_ids: ["dead-hero"] }],
      post_battles: [{
        battle_number: 1,
        complete: false,
        experience_applied: false,
        pending_follow_ups: [{ id: "later", step: 3, warrior_id: "dead-hero" }],
        step_state: { injuries: { "dead-hero:1": { resolved: true, result: "Dead" } } },
      }],
    }, view: {} } as unknown as CampaignDocument;
    const run = vi.fn().mockResolvedValue({ ok: true, document });
    const service = { current: () => document, isDirty: () => false, subscribe: () => () => undefined, run } as never;

    render(<CampaignAppProvider service={service}><PostBattleExperience document={document} knowledge={{} as never} locale="es" /></CampaignAppProvider>);

    await waitFor(() => expect(run).toHaveBeenCalledWith("applyBattleExperience", {}));
  });
});

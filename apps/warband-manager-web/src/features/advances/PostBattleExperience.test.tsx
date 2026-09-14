import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import { CampaignAppProvider } from "../campaign/useCampaignApp";
import { PostBattleExperience } from "./PostBattleExperience";
import { AdvancesPanel } from "./AdvancesPanel";
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

  it("shows and locks processing feedback while an advance roll is resolving", async () => {
    let finish!: (value: { ok: boolean; document: CampaignDocument }) => void;
    const pending = new Promise<{ ok: boolean; document: CampaignDocument }>((resolve) => { finish = resolve; });
    const document = { campaign: {
      identity: { band_id: "test" }, warriors: [{ id: "hero", name: "Sigrid", kind: "hero", profile_name: "Captain", stats: {}, equipment: [], skills: [], experience: 2 }],
      post_battles: [{ battle_number: 1, complete: false, pending_advances: [{ warrior_id: "hero", table: "hero", threshold: 2, roll_total: null, committed: false }] }],
    }, view: {} } as unknown as CampaignDocument;
    const run = vi.fn(() => pending);
    const service = { current: () => document, isDirty: () => false, subscribe: () => () => undefined, run } as never;
    const knowledge = { list: () => [], queryKnowledge: () => ({ ok: false }), campaignSection: () => ({}) } as never;
    render(<CampaignAppProvider service={service}><AdvancesPanel document={document} knowledge={knowledge} locale="es" /></CampaignAppProvider>);

    const roll = screen.getByRole("button", { name: "Tirar 2D6" });
    fireEvent.click(roll);
    expect(screen.getByText(/Procesando la tirada/)).toHaveAttribute("role", "status");
    expect(roll).toBeDisabled();
    await waitFor(() => expect(run).toHaveBeenCalledWith("resolveAdvanceRoll", expect.objectContaining({ warrior_id: "hero" })));
    finish({ ok: true, document });
    await waitFor(() => expect(screen.queryByText(/Procesando la tirada/)).not.toBeInTheDocument());
  });

  it("localizes saved English advance outcomes in the Result column", () => {
    const document = { campaign: {
      warriors: [{ id: "hero", name: "Sigrid", kind: "hero", profile_name: "Captain", stats: { WS: 4 }, equipment: [], skills: [], experience: 20 }],
      post_battles: [{ battle_number: 1, complete: false, pending_advances: [{ warrior_id: "hero", table: "hero", threshold: 20, roll_total: 9, committed: true, applied_label: "+1 WS", roll_history: ["Result rejected: WS is at its advance cap (5)."] }] }],
    }, view: {} } as unknown as CampaignDocument;
    const service = { current: () => document, isDirty: () => false, subscribe: () => () => undefined, run: vi.fn() } as never;
    const knowledge = { list: () => [], queryKnowledge: () => ({ ok: false }), campaignSection: () => ({}) } as never;

    render(<CampaignAppProvider service={service}><AdvancesPanel document={document} knowledge={knowledge} locale="es" /></CampaignAppProvider>);

    expect(screen.getByText("+1 HA")).toBeInTheDocument();
    expect(screen.getByText("Resultado rechazado: HA ha alcanzado su límite de avance (5).")).toBeInTheDocument();
    expect(screen.queryByText("+1 WS")).not.toBeInTheDocument();
  });

  it("localizes characteristic decisions in the pending decisions column", () => {
    const document = { campaign: {
      warriors: [{ id: "hero", name: "Sigrid", kind: "hero", profile_name: "Captain", stats: { WS: 4 }, equipment: [], skills: [], experience: 20 }],
      post_battles: [{ battle_number: 1, complete: false, pending_advances: [{ warrior_id: "hero", table: "hero", threshold: 20, roll_total: 9, committed: false, advance_options: [{ kind: "characteristic_increase", characteristic: "WS", amount: 1 }] }] }],
    }, view: {} } as unknown as CampaignDocument;
    const service = { current: () => document, isDirty: () => false, subscribe: () => () => undefined, run: vi.fn() } as never;
    const knowledge = { list: () => [], queryKnowledge: () => ({ ok: false }), campaignSection: () => ({}) } as never;

    render(<CampaignAppProvider service={service}><AdvancesPanel document={document} knowledge={knowledge} locale="es" /></CampaignAppProvider>);

    expect(screen.getByRole("button", { name: "+1 HA" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "+1 WS" })).not.toBeInTheDocument();
  });
});

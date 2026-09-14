import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom/vitest";

import type { CampaignDocument } from "../campaign/types";
import { CampaignAppProvider } from "../campaign/useCampaignApp";
import { PostBattleInjuries } from "./PostBattleInjuries";

describe("PostBattleInjuries", () => {
  it("resolves a Hired Sword on the hero D66 table and applies the outcome", async () => {
    const user = userEvent.setup();
    const document = {
      campaign: {
        warriors: [{ id: "ranger#1", name: "Explorador Elfo", profile_name: "Explorador Elfo", kind: "hireling", stats: {}, equipment: [], skills: [], experience: 0, cost: 40 }],
        battles: [{ number: 1, out_of_action_ids: ["ranger#1"], participants: [] }],
        post_battles: [{ battle_number: 1, complete: false, pending_follow_ups: [{ id: "upkeep:1:ranger#1", step: 6, type: "hireling_upkeep", warrior_id: "ranger#1", costs: [["gold_crowns", 15]] }], step_state: {} }],
      },
      view: {},
    } as unknown as CampaignDocument;
    const run = vi.fn().mockResolvedValue({ ok: true });
    const service = { current: () => document, isDirty: () => false, subscribe: () => () => undefined, run } as never;
    const knowledge = { list: (kind: string) => kind === "injury" ? [{ id: "dead", applies_to: "hero", roll: "11", result: "Dead", effects: [{ type: "warrior.remove" }] }] : [] } as never;

    render(<CampaignAppProvider service={service}><PostBattleInjuries document={document} knowledge={knowledge} locale="es" /></CampaignAppProvider>);
    expect(screen.getByRole("button", { name: "Tirar 2D6" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Resolver seguimiento" })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Introducir Dados Físicos" }));
    await user.click(screen.getByRole("button", { name: "Usar Resultado" }));

    expect(run).toHaveBeenCalledWith("applyInjuryOutcome", expect.objectContaining({
      warrior_id: "ranger#1",
      result_id: "dead",
      casualty_index: 1,
      rolled_dice: [1, 1],
      roll: 11,
    }));
  });

  it("shows the saved dice instead of a generic completed message", () => {
    const document = {
      campaign: {
        warriors: [{ id: "hero-1", name: "Marta", profile_name: "Heroína", kind: "hero", stats: {}, equipment: [], skills: [], experience: 0, cost: 40, injury_records: [{ battle_number: 1, casualty_index: 1, result_id: "recovery", result: "Full recovery", rolled_dice: [4, 6], roll: 46 }] }],
        battles: [{ number: 1, out_of_action_ids: ["hero-1"], participants: [] }],
        post_battles: [{ battle_number: 1, complete: false, pending_follow_ups: [], step_state: { injuries: { "hero-1:1": { follow_up_rolls: [{ phase: "subtable", dice: [2, 5], roll: 25 }] } } } }],
      }, view: {},
    } as unknown as CampaignDocument;
    const service = { current: () => document, isDirty: () => false, subscribe: () => () => undefined, run: vi.fn() } as never;
    const knowledge = { list: () => [] } as never;
    render(<CampaignAppProvider service={service}><PostBattleInjuries document={document} knowledge={knowledge} locale="es" /></CampaignAppProvider>);

    expect(screen.getByText("Tirada: 4, 6 → 46")).toBeInTheDocument();
    expect(screen.getByText("Resultado secundario de la herida: Tirada 2, 5 → 25")).toBeInTheDocument();
    expect(screen.queryByText("Sin acciones pendientes")).not.toBeInTheDocument();
  });

  it("keeps a removed warrior in the table with the resolved injury", () => {
    const document = {
      campaign: {
        warriors: [],
        battles: [{
          number: 1,
          out_of_action_ids: ["hero-1"],
          participants: [{ id: "hero-1", name: "Gotrek", profile_name: "Matatrolles", kind: "hero" }],
        }],
        post_battles: [{
          battle_number: 1,
          complete: false,
          pending_follow_ups: [],
          step_state: { injuries: { "hero-1:1": { resolved: true, result_id: "dead", result: "Dead" } } },
        }],
      },
      view: {},
    } as unknown as CampaignDocument;
    const service = {
      current: () => document,
      isDirty: () => false,
      subscribe: () => () => undefined,
      run: vi.fn(),
    } as never;
    const knowledge = {
      list: (kind: string) => kind === "injury" ? [{ id: "dead", result: "Dead", names: { es: "Muerto" }, note_i18n: { es: "El guerrero muere." } }] : [],
    } as never;

    render(
      <CampaignAppProvider service={service}>
        <PostBattleInjuries document={document} knowledge={knowledge} locale="es" />
      </CampaignAppProvider>,
    );

    expect(screen.getByText("Gotrek")).toBeInTheDocument();
    expect(screen.getByText("Muerto")).toBeInTheDocument();
    expect(screen.getByText("Sin acciones pendientes")).toBeInTheDocument();
  });
});

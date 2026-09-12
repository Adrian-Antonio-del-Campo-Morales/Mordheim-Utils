import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom/vitest";

import type { CampaignDocument } from "../campaign/types";
import { CampaignAppProvider } from "../campaign/useCampaignApp";
import { PostBattleInjuries } from "./PostBattleInjuries";

describe("PostBattleInjuries", () => {
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

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";

import type { CampaignAppService, CampaignDocument } from "@src/features/campaign/types";
import { CampaignAppProvider } from "@src/features/campaign/useCampaignApp";
import { PostBattleInventory } from "@src/features/equipment/PostBattleInventory";

vi.mock("@src/features/hirelings/HirelingsPanel", () => ({ HirelingsPanel: () => <p>Contenido de comercio</p> }));
vi.mock("@src/features/economy/ManualCorrectionsPanel", () => ({ ManualCorrectionsPanel: () => <p>Ajustes manuales</p> }));

const document = { campaign: { inventory: [], warriors: [] } } as unknown as CampaignDocument;
const service = { current: () => document, isDirty: () => false, subscribe: () => () => {}, run: vi.fn() } as unknown as CampaignAppService;
const knowledge = {} as never;

describe("PostBattleInventory", () => {
  it("uses the creation inventory layout and keeps trading in its dialog", async () => {
    const user = userEvent.setup();
    render(<CampaignAppProvider service={service}><PostBattleInventory document={document} knowledge={knowledge} locale="es" /></CampaignAppProvider>);

    expect(screen.getByRole("region", { name: "Inventario" })).toHaveClass("draft-inventory");
    expect(screen.queryByText("Contenido de comercio")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "COMPRAR Y VENDER" }));
    expect(screen.getByRole("dialog", { name: "COMPRAR Y VENDER" })).toHaveTextContent("Contenido de comercio");
  });
});

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import { describe, expect, it } from "vitest";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { createDefaultUseCases } from "@domain/campaign/kernel/default-usecases";
import { memberCount } from "@domain/campaign/kernel/document";
import { CampaignAppProvider } from "@src/features/campaign/useCampaignApp";
import type { CampaignDocument } from "@src/features/campaign/types";
import { DraftWorkspace } from "@src/features/draft/DraftWorkspace";

describe("DraftWorkspace", () => {
  it("does not count a Hired Sword against the initial warband limit", () => {
    const knowledge = ArtefactKnowledgeReader.from(JSON.parse(readFileSync(resolve(process.cwd(), "../../outputs/web-public/knowledge/knowledge-web.json"), "utf-8")));
    const created = createDefaultUseCases(knowledge).createDraft("sisters-of-sigmar", knowledge);
    if (!created.ok) throw new Error("draft should succeed");
    const ownModels = memberCount(created.state.campaign.warriors);
    const document: CampaignDocument = {
      ...created.state,
      campaign: {
        ...created.state.campaign,
        configuration: { ...created.state.campaign.configuration, maximum_models: ownModels },
        warriors: [...created.state.campaign.warriors, { id: "hireling:test", name: "Test Hired Sword", profile_name: "Hired Sword", kind: "hireling", stats: {}, equipment: [], skills: [], experience: 0, cost: 0 }],
      },
    };
    const service = { current: () => document, isDirty: () => false, subscribe: () => () => {} } as never;

    render(<CampaignAppProvider service={service}><DraftWorkspace document={document} knowledge={knowledge} locale="en" /></CampaignAppProvider>);

    expect(screen.getByText((_, element) => element?.textContent?.startsWith(`${ownModels}/${ownModels} models`) ?? false)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Commit initial warband" })).toBeEnabled();
  });

  it("closes the add-hero dialog when the action is rejected", async () => {
    const user = userEvent.setup();
    const knowledge = ArtefactKnowledgeReader.from(JSON.parse(readFileSync(resolve(process.cwd(), "../../outputs/web-public/knowledge/knowledge-web.json"), "utf-8")));
    const created = createDefaultUseCases(knowledge).createDraft("sisters-of-sigmar", knowledge);
    if (!created.ok) throw new Error("draft should succeed");
    const service = { current: () => created.state, isDirty: () => false, subscribe: () => () => {}, run: async () => ({ ok: false, reason: "rejected", message: "Roster limit reached (1/1)." }) } as never;

    render(<CampaignAppProvider service={service}><DraftWorkspace document={created.state} knowledge={knowledge} locale="en" /></CampaignAppProvider>);
    await user.click(screen.getByRole("button", { name: /ADD HERO/ }));
    const dialog = screen.getByRole("dialog", { name: "Add warriors" });
    await user.click(screen.getAllByRole("radio")[0]);
    await user.click(within(dialog).getByRole("button", { name: "Add to roster" }));

    await waitFor(() => expect(screen.queryByRole("dialog", { name: "Add warriors" })).not.toBeInTheDocument());
  });
});

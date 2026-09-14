import { describe, expect, it } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

import { createService } from "./default-deps";
import { CampaignAppProvider } from "./useCampaignApp";
import { CampaignSlice } from "./CampaignSlice";
import type { CampaignDocument } from "./types";

describe("CampaignSlice", () => {
  it("opens the mobile step list and closes it after returning to a completed step", () => {
    const fixture = JSON.parse(readFileSync(resolve(process.cwd(), "../../contracts/campaign-file-v5/fixtures/pending-post-battle.json"), "utf-8")) as CampaignDocument;
    const post = fixture.campaign.post_battles.find((entry) => !entry.complete)!;
    const document = { ...fixture, view: { ...fixture.view, selected_moment: `post:${post.battle_number}` } };
    const service = { current: () => document, isDirty: () => false, subscribe: () => () => {} } as never;
    render(<CampaignAppProvider service={service}><CampaignSlice locale="es" /></CampaignAppProvider>);
    const phase = within(screen.getByRole("region", { name: "Fase post-batalla" }));
    expect(phase.getByRole("button", { name: /Continuar a/ }).parentElement?.tagName).toBe("HEADER");
    const toggle = phase.getByRole("button", { name: "Ver todos los pasos" });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
    fireEvent.click(phase.getByRole("button", { name: "✓ Heridas" }));
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(phase.getByRole("heading", { name: "Heridas" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Continuar a/ })).not.toBeInTheDocument();
    expect(phase.getByRole("button", { name: "✓ Heridas" })).toHaveAttribute("aria-current", "step");
  });

  it("keeps the campaign timeline beside the initial-warband draft", async () => {
    const raw = JSON.parse(readFileSync(resolve(process.cwd(), "public/knowledge/knowledge-web.json"), "utf-8"));
    const knowledge = ArtefactKnowledgeReader.from(raw);
    const service = createService(knowledge);
    await service.createCampaign({
      band_id: "sisters-of-sigmar",
      campaign_name: "Layout campaign",
      warband_name: "Layout band",
    });

    const { container } = render(
      <CampaignAppProvider service={service}>
        <CampaignSlice knowledge={knowledge} locale="en" />
      </CampaignAppProvider>,
    );

    expect(screen.getByRole("navigation", { name: "Timeline" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Layout band" })).toBeInTheDocument();
    expect(container.querySelector(".campaign-layout > nav + .moment-detail")).not.toBeNull();
  });
});

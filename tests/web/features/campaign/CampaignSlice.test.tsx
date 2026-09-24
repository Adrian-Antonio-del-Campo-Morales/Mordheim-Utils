import { describe, expect, it } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

import { createService } from "@src/features/campaign/default-deps";
import { CampaignAppProvider } from "@src/features/campaign/useCampaignApp";
import { CampaignSlice } from "@src/features/campaign/CampaignSlice";
import type { CampaignDocument } from "@src/features/campaign/types";

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

  it("re-resolves historical roster references while preserving personal names", () => {
    const fixture = JSON.parse(readFileSync(resolve(process.cwd(), "../../contracts/campaign-file-v5/fixtures/active-campaign.json"), "utf-8")) as CampaignDocument;
    const snapshot = fixture.campaign.states[0];
    const warrior = { ...fixture.campaign.warriors[0], id: "internal_warrior", name: "My_personal_name", profile_id: "internal_profile", profile_name: "STALE_PROFILE", kind: "hero" as const, stats: { M: 4 }, skills: [], special_rules: [], equipment: [{ item_id: "internal_item", name: "STALE_ITEM", quantity: 1 }] };
    const document = { ...fixture, campaign: { ...fixture.campaign, states: [{ ...snapshot, roster: [warrior] }] }, view: { ...fixture.view, selected_moment: `state:${snapshot.number}` } } as CampaignDocument;
    const service = { current: () => document, isDirty: () => false, subscribe: () => () => {} } as never;
    const knowledge = ArtefactKnowledgeReader.from({ schema_version: 1, ruleset: "test", bands: [], profiles: [{ id: "internal_profile", names: { es: "Capitana", en: "Captain" } }], items: [{ item_id: "internal_item", names: { es: "Espada", en: "Sword" } }], skills: [] });
    const view = (locale: "es" | "en") => <CampaignAppProvider service={service} locale={locale}><CampaignSlice knowledge={knowledge} locale={locale} /></CampaignAppProvider>;
    const { container, rerender } = render(view("es"));
    fireEvent.click(screen.getByRole("button", { name: "GUERREROS" }));
    expect(screen.getByText("Capitana")).toBeInTheDocument();
    expect(screen.getByText("My_personal_name")).toBeInTheDocument();
    rerender(view("en"));
    expect(screen.getByText("Captain")).toBeInTheDocument();
    expect(screen.queryByText("Capitana")).not.toBeInTheDocument();
    rerender(view("es"));
    expect(screen.getByText("Capitana")).toBeInTheDocument();
    expect(container.textContent).not.toMatch(/internal_|STALE_/);
  });

  it("keeps the campaign timeline beside the initial-warband draft", async () => {
    const raw = JSON.parse(readFileSync(resolve(process.cwd(), "../../outputs/web-public/knowledge/knowledge-web.json"), "utf-8"));
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

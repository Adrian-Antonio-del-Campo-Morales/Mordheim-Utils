import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

import { createService } from "./default-deps";
import { CampaignAppProvider } from "./useCampaignApp";
import { CampaignSlice } from "./CampaignSlice";

describe("CampaignSlice", () => {
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

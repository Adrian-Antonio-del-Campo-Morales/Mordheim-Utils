import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import type { CampaignDocument } from "../campaign/types";
import { CampaignAppProvider } from "../campaign/useCampaignApp";
import { ExplorationPanel } from "./ExplorationPanel";

const base = { campaign: { special_rules: [], warriors: [], battles: [], states: [], post_battles: [{ complete: false, experience_applied: false, pending_advances: [], pending_follow_ups: [], step_state: {} }] } } as unknown as CampaignDocument;
const knowledge = { list: () => [], queryKnowledge: () => ({ ok: false, reason: "not_found" }), queryMany: (queries: unknown[]) => queries.map(() => ({ ok: false, reason: "not_found" })) } as never;
const service = { current: () => base, isDirty: () => false, subscribe: () => () => {}, run: vi.fn() } as never;

describe("ExplorationPanel", () => {
  it("blocks exploration until experience and advances are applied", () => {
    render(<CampaignAppProvider service={service}><ExplorationPanel document={base} knowledge={knowledge} locale="en" /></CampaignAppProvider>);
    expect(screen.getByRole("status")).toHaveTextContent("Resolve experience and all advances first.");
  });

  it("shows the resolved dice and wyrdstone result", () => {
    const resolved = structuredClone(base) as CampaignDocument;
    const post = resolved.campaign.post_battles[0] as unknown as { experience_applied: boolean; step_state: Record<string, unknown> };
    post.experience_applied = true;
    post.step_state = { exploration: { resolved: true, dice_count: 2, total: 8, shards: 3 } };
    render(<CampaignAppProvider service={service}><ExplorationPanel document={resolved} knowledge={knowledge} locale="en" /></CampaignAppProvider>);
    expect(screen.getByRole("status")).toHaveTextContent("2 dice");
    expect(screen.getByRole("status")).toHaveTextContent("total 8");
  });
});

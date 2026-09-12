import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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
    expect(screen.getByText("3 wyrdstone shards")).toBeInTheDocument();
    expect(screen.getByText("2 dice · total 8")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Exploration resolved");
  });

  it("applies the initial roll directly without a Resolve exploration step", async () => {
    const user=userEvent.setup();
    const document=structuredClone(base) as CampaignDocument;
    Object.assign(document.campaign, {
      identity: { band_id: "test" },
      warriors: [{ id:"hero-1",name:"Hero",profile_name:"Hero",kind:"hero",stats:{},equipment:[],skills:[],experience:0,cost:0 }],
      battles: [{ number:1,result:"loss",out_of_action_ids:[],participants:[{id:"hero-1"}] }],
    });
    Object.assign(document.campaign.post_battles[0], { battle_number:1,experience_applied:true });
    const run=vi.fn().mockResolvedValue({ok:true,document});
    const localService={current:()=>document,isDirty:()=>false,subscribe:()=>()=>{},run} as never;
    const localKnowledge={list:()=>[],queryKnowledge:()=>({ok:false,reason:"not_found"}),queryMany:()=>[],campaignSection:()=>({exploration:{max_dice:6,dice_allocation:[{eligible_warrior:"hero",condition:"survived_battle",dice:1}]}})} as never;
    render(<CampaignAppProvider service={localService}><ExplorationPanel document={document} knowledge={localKnowledge} locale="en" /></CampaignAppProvider>);

    await user.click(screen.getByRole("button", {name:"Roll 1D6"}));

    expect(run).toHaveBeenCalledWith("applyExploration", {dice:[expect.any(Number)]});
    expect(screen.queryByRole("button", {name:"Resolve exploration"})).not.toBeInTheDocument();
  });
});

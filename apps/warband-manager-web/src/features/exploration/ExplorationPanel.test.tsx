import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor, within } from "@testing-library/react";
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
    post.step_state = { exploration: { resolved: true, dice: [4, 4], dice_count: 2, total: 8, shards: 3 } };
    render(<CampaignAppProvider service={service}><ExplorationPanel document={resolved} knowledge={knowledge} locale="en" /></CampaignAppProvider>);
    expect(screen.getByText("3 wyrdstone shards")).toBeInTheDocument();
    expect(screen.getByText("2 dice · total 8")).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent("Exploration roll: 4, 4 → 8");
  });

  it("shows every subsequent exploration roll beneath the main result", () => {
    const resolved = structuredClone(base) as CampaignDocument;
    const post = resolved.campaign.post_battles[0] as unknown as { experience_applied: boolean; step_state: Record<string, unknown> };
    post.experience_applied = true;
    post.step_state = { exploration: { resolved: true, dice: [5, 4, 5, 2, 1, 5], dice_count: 6, total: 22, shards: 4, follow_up_rolls: [{ label: { es: "Cantidad de coronas" }, dice: [4, 3], total: 7 }, { label: { es: "Tabla de artefactos" }, dice: [6], total: 6 }] } };
    render(<CampaignAppProvider service={service}><ExplorationPanel document={resolved} knowledge={knowledge} locale="es" /></CampaignAppProvider>);
    const history = screen.getByRole("region", { name: "Tiradas posteriores" });
    expect(history).toHaveTextContent("Cantidad de Coronas4, 3 → 7");
    expect(history).toHaveTextContent("Tabla de Artefactos6 → 6");
  });

  it("rejects technical identifiers in the next roll or decision column", () => {
    const resolved = structuredClone(base) as CampaignDocument;
    const post = resolved.campaign.post_battles[0] as unknown as { experience_applied: boolean; pending_follow_ups: unknown[]; step_state: Record<string, unknown> };
    post.experience_applied = true;
    post.step_state = { exploration: { resolved: true, dice: [4], dice_count: 1, total: 4, shards: 1 } };
    post.pending_follow_ups = [{ type: "exploration_followup", messages: [], pending: { kind: "roll", label: "gold_crowns reward", dice_count: 1, dice_sides: 6 } }];
    render(<CampaignAppProvider service={service}><ExplorationPanel document={resolved} knowledge={knowledge} locale="es" /></CampaignAppProvider>);
    expect(screen.getByText("Recompensa de Coronas de Oro")).toBeInTheDocument();
  });

  it("shows every die and highlights the combination that triggered the special event", () => {
    const resolved = structuredClone(base) as CampaignDocument;
    const post = resolved.campaign.post_battles[0] as unknown as { experience_applied: boolean; step_state: Record<string, unknown> };
    post.experience_applied = true;
    post.step_state = { exploration: { resolved: true, dice: [4, 4, 4, 2], dice_count: 4, total: 14, shards: 3, special: "Fletcher" } };
    const localKnowledge = { list: () => [], queryKnowledge: () => ({ ok: false, reason: "not_found" }), queryMany: () => [], campaignSection: () => ({ exploration: { results: [{ dice_pattern: "4,4,4", outcome: "Fletcher", outcome_i18n: { es: "Flechero" }, description: "Roll for bows.", description_i18n: { es: "Tira para determinar qué arcos encuentras." } }] } }) } as never;
    render(<CampaignAppProvider service={service}><ExplorationPanel document={resolved} knowledge={localKnowledge} locale="es" /></CampaignAppProvider>);

    const dice = screen.getByRole("list", { name: "Resultados individuales de los dados" });
    expect(dice).toHaveTextContent("D1");
    expect(dice).toHaveTextContent("D4");
    expect(within(dice).getAllByRole("listitem").map((row) => row.querySelector("strong")?.textContent)).toEqual(["4", "4", "4", "2"]);
    expect(screen.getByText("Triple de 4")).toBeInTheDocument();
    expect(screen.getByText("Flechero")).toHaveAttribute("data-tooltip", "Tira para determinar qué arcos encuentras.");
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

    await waitFor(() => expect(run).toHaveBeenCalledWith("applyExploration", {dice:[expect.any(Number)]}));
    expect(screen.queryByRole("button", {name:"Resolve exploration"})).not.toBeInTheDocument();
  });

  it("shows the source and extra choose-one die granted by an Augur", () => {
    const document=structuredClone(base) as CampaignDocument;
    Object.assign(document.campaign, {
      identity: { band_id: "sisters-of-sigmar" },
      warriors: [{ id:"augur-1",name:"Augur",profile_id:"augur",profile_name:"Augur",kind:"hero",stats:{},equipment:[],skills:[],experience:0,cost:0 }],
      battles: [{ number:1,result:"loss",out_of_action_ids:[],participants:[{id:"augur-1"}] }],
    });
    Object.assign(document.campaign.post_battles[0], { battle_number:1,experience_applied:true });
    const localKnowledge={
      list:(kind:string)=>kind==="profile"?[{id:"augur",rule_ids:["augur--blessed-sight"]}]:[],
      queryKnowledge:()=>({ok:false,reason:"not_found"}), queryMany:()=>[],
      rulesDocument:()=>[{id:"augur--blessed-sight",names:{en:"Blessed Sight",es:"Vista Bendita"}}],
      campaignSection:()=>({exploration:{max_dice:6,dice_allocation:[{eligible_warrior:"hero",condition:"survived_battle",dice:1}]}}),
    } as never;
    render(<CampaignAppProvider service={service}><ExplorationPanel document={document} knowledge={localKnowledge} locale="es" /></CampaignAppProvider>);
    expect(screen.getByText("Modificadores activos").parentElement).toHaveTextContent("Vista Bendita");
    expect(screen.getByRole("button", { name: "Tirar 2D6" })).toBeInTheDocument();
  });
});

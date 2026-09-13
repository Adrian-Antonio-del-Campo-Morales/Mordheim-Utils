import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CampaignAppProvider } from "../campaign/useCampaignApp";
import type { CampaignDocument } from "../campaign/types";
import { GroupRecruitmentPanel } from "./GroupRecruitmentPanel";

describe("GroupRecruitmentPanel", () => {
  it("manages groups, heroes and hired sword upkeep in one table", async () => {
    const user=userEvent.setup();
    const document={campaign:{warriors:[
      {id:"hero",name:"Captain",kind:"hero",experience:12,equipment:[],skills:[],stats:{},cost:60},
      {id:"group",name:"Marksmen",kind:"henchman",quantity:2,experience:4,equipment:[],skills:[],stats:{},cost:25},
      {id:"hireling",name:"Elf Ranger",kind:"hireling",experience:0,equipment:[],skills:[],stats:{},cost:0},
    ],post_battles:[{complete:false,veteran_pool:3,step_state:{veterans:{resolved:true}},pending_follow_ups:[{id:"upkeep:elf",type:"hireling_upkeep",warrior_id:"hireling",costs:[["gold_crowns",20]]}]}]}} as unknown as CampaignDocument;
    const run=vi.fn().mockResolvedValue({ok:true});
    const service={current:()=>document,isDirty:()=>false,subscribe:()=>()=>{},run} as never;
    render(<CampaignAppProvider service={service}><GroupRecruitmentPanel document={document} locale="en" /></CampaignAppProvider>);

    expect(screen.getByRole("table",{name:"Warband members"})).toBeTruthy();
    expect(screen.getAllByRole("row")).toHaveLength(4);
    expect(screen.getByText("20 Gold Crowns")).toBeTruthy();
    expect(screen.getByRole("button",{name:"Recruit one member"})).toBeTruthy();
    await user.click(screen.getByRole("button",{name:"Pay"}));
    expect(run).toHaveBeenCalledWith("resolveHirelingUpkeep",{follow_up_id:"upkeep:elf",pay:true});
  });
});

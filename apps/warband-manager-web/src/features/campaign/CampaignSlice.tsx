import { useState } from "react";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { useCampaignApp } from "./useCampaignApp";
import { TimelinePanel } from "../timeline/TimelinePanel";
import { EquipmentPanel } from "../equipment/EquipmentPanel";
import { PostBattleExperience } from "../advances/PostBattleExperience";
import { HirelingsPanel } from "../hirelings/HirelingsPanel";
import { BattlePanel } from "../battle/BattlePanel";
import { InjuriesPanel } from "../injuries/InjuriesPanel";
import { ReviewPanel } from "../review/ReviewPanel";
import { DraftWorkspace } from "../draft/DraftWorkspace";
import { PostBattleInjuries } from "../injuries/PostBattleInjuries";
import type { CampaignDocument } from "./types";

function RosterOverview({ document }: { document: CampaignDocument }) {
  const app = useCampaignApp(); const [name, setName] = useState("");
  const { campaign } = document;
  return <section aria-label="Warband overview"><dl className="campaign-metrics"><div><dt>Campaign</dt><dd>{campaign.identity.campaign_name}</dd></div><div><dt>Warband</dt><dd>{campaign.identity.warband_type}</dd></div><div><dt>Models</dt><dd>{campaign.warriors.reduce((sum, warrior) => sum + (warrior.quantity ?? 1), 0)}</dd></div><div><dt>Battles</dt><dd>{campaign.battles.length}</dd></div></dl>
    <h3>Roster</h3><div className="warrior-grid">{campaign.warriors.map((warrior) => <article className="warrior-card" key={warrior.id}><header><div><strong>{warrior.name}</strong><span>{warrior.profile_name}</span></div><b>{warrior.experience} XP</b></header><div className="stats">{Object.entries(warrior.stats).map(([key,value]) => <span key={key}><small>{key}</small>{value}</span>)}</div><p>{warrior.equipment.map((entry) => `${entry.quantity}× ${entry.name}`).join(", ") || "No equipment"}</p>{warrior.skills.length > 0 && <p>{warrior.skills.join(", ")}</p>}</article>)}</div>
    <form className="inline-form" onSubmit={(event) => { event.preventDefault(); if(name.trim()) void app.runAction("renameWarband", { name: name.trim() }); setName(""); }}><label>Rename warband<input value={name} onChange={(event) => setName(event.target.value)} /></label><button disabled={!name.trim()}>Apply</button></form>
  </section>;
}

export function CampaignSlice({ knowledge, locale = "en" }: { knowledge?: ArtefactKnowledgeReader; locale?: "es" | "en" }) {
  const app = useCampaignApp(); const doc = app.document;
  if (!doc) return null;
  const selected = String(doc.view.selected_moment ?? `state:${doc.campaign.current_state_number}`);
  const battleNumber = Number(selected.split(":")[1] ?? 0);
  const battle = doc.campaign.battles.find((row) => row.number === battleNumber);
  const currentState = selected === `state:${doc.campaign.current_state_number}`;
  return <section aria-label="Campaign">
    {app.error && <output className="global-error" role="alert">{app.error} <button onClick={app.clearError}>Dismiss</button></output>}
    {app.dirty && <output className="dirty" role="status">Unsaved changes</output>}
    {doc.campaign.configuration.is_draft && knowledge ? <DraftWorkspace document={doc} knowledge={knowledge} locale={locale} /> : <div className="campaign-layout">
      <TimelinePanel document={doc} onSelect={app.selectMoment} />
      <div className="moment-detail">
        {selected.startsWith("state:") && <><RosterOverview document={doc} /><EquipmentPanel document={doc} />{currentState && <BattlePanel document={doc} knowledge={knowledge} locale={locale} />}</>}
        {selected.startsWith("battle:") && <section className="page"><div className="page-title"><p>BATTLE #{battleNumber}</p><h2>{battle?.scenario ?? "Battle"}</h2></div>{battle ? <dl className="campaign-metrics"><div><dt>Opponent</dt><dd>{battle.opponent}</dd></div><div><dt>Result</dt><dd>{battle.result}</dd></div><div><dt>Gold</dt><dd>{battle.gold_delta}</dd></div><div><dt>Wyrdstone</dt><dd>{battle.wyrdstone}</dd></div></dl> : <p>Battle not found.</p>}</section>}
        {selected.startsWith("post:") && <><BattlePanel document={doc} knowledge={knowledge} locale={locale} />{knowledge && <PostBattleInjuries document={doc} knowledge={knowledge} />}<InjuriesPanel document={doc} />{knowledge && <PostBattleExperience document={doc} knowledge={knowledge} />}<HirelingsPanel document={doc} listings={knowledge} /><ReviewPanel document={doc} /></>}
      </div></div>}
  </section>;
}

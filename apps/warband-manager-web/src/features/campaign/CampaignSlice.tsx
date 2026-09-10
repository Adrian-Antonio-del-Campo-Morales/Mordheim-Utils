import { useState } from "react";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { useCampaignApp } from "./useCampaignApp";
import { TimelinePanel } from "../timeline/TimelinePanel";
import { EquipmentPanel } from "../equipment/EquipmentPanel";
import { PostBattleExperience } from "../advances/PostBattleExperience";
import { HirelingsPanel } from "../hirelings/HirelingsPanel";
import { HirelingUpkeepPanel } from "../hirelings/HirelingUpkeepPanel";
import { BattlePanel } from "../battle/BattlePanel";
import { BattleHistory } from "../battle/BattleHistory";
import { InjuriesPanel } from "../injuries/InjuriesPanel";
import { ReviewPanel } from "../review/ReviewPanel";
import { PostBattleHistory } from "../review/PostBattleHistory";
import { FollowUpAcknowledgements } from "../review/FollowUpAcknowledgements";
import { DraftWorkspace } from "../draft/DraftWorkspace";
import { PostBattleInjuries } from "../injuries/PostBattleInjuries";
import { ExplorationPanel } from "../exploration/ExplorationPanel";
import { ScenarioFollowupsPanel } from "../exploration/ScenarioFollowupsPanel";
import { WyrdstoneSalePanel } from "../economy/WyrdstoneSalePanel";
import { VeteranPoolPanel } from "../recruitment/VeteranPoolPanel";
import { GroupRecruitmentPanel } from "../recruitment/GroupRecruitmentPanel";
import { RecruitProfilePanel } from "../recruitment/RecruitProfilePanel";
import { ManualSkillPanel } from "../advances/ManualSkillPanel";
import { ManualCorrectionsPanel } from "../economy/ManualCorrectionsPanel";
import { RareSearchPanel } from "../searches/RareSearchPanel";
import type { CampaignDocument } from "./types";

function RosterOverview({ document, stateNumber, editable, locale }: { document: CampaignDocument; stateNumber: number; editable: boolean; locale: "es" | "en" }) {
  const app = useCampaignApp(); const [name, setName] = useState("");
  const { campaign } = document;
  const snapshot = campaign.states.find((state) => state.number === stateNumber);
  const warriors = snapshot?.roster ?? (editable ? campaign.warriors : []);
  const t = locale === "es" ? { campaign:"Campaña",warband:"Banda",models:"Miniaturas",rating:"Valoración",treasury:"Tesorería",wyrdstone:"Piedra bruja",historical:"Histórico · solo lectura",roster:"Guerreros",effects:"Efectos activos",missing:"Este estado no contiene una instantánea de guerreros.",members:"miembros",equipment:"Equipo",skills:"Habilidades / heridas",none:"Ninguno",recovery:"Recuperación",misses:"se pierde",battles:"batalla(s)",upkeep:"Mantenimiento",rename:"Renombrar banda",apply:"Aplicar" } : { campaign:"Campaign",warband:"Warband",models:"Models",rating:"Rating",treasury:"Treasury",wyrdstone:"Wyrdstone",historical:"Historical · read only",roster:"Roster",effects:"Active effects",missing:"No roster snapshot is stored for this state.",members:"members",equipment:"Equipment",skills:"Skills / injuries",none:"None",recovery:"Recovery",misses:"misses",battles:"battle(s)",upkeep:"Upkeep",rename:"Rename warband",apply:"Apply" };
  return <section aria-label="Warband overview"><dl className="campaign-metrics"><div><dt>{t.campaign}</dt><dd>{campaign.identity.campaign_name}</dd></div><div><dt>{t.warband}</dt><dd>{campaign.identity.warband_type}</dd></div><div><dt>{t.models}</dt><dd>{snapshot?.models ?? warriors.reduce((sum, warrior) => sum + (warrior.quantity ?? 1), 0)}</dd></div><div><dt>{t.rating}</dt><dd>{snapshot?.rating ?? 0}</dd></div><div><dt>{t.treasury}</dt><dd>{snapshot?.gold ?? 0} gc</dd></div><div><dt>{t.wyrdstone}</dt><dd>{snapshot?.wyrdstone ?? 0}</dd></div></dl>
    {!editable && <p role="status">{t.historical}</p>}
    {editable&&campaign.special_rules.length>0&&<><h3>{t.effects}</h3><ul>{campaign.special_rules.map((rule)=><li key={`${rule.source}:${rule.text}`}>{rule.text}{rule.expires_after_battles!=null?` · ${rule.expires_after_battles} ${t.battles}`:""}</li>)}</ul></>}
    <h3>{t.roster}</h3>{warriors.length === 0 ? <p>{t.missing}</p> : <div className="warrior-grid">{warriors.map((warrior) => <article className="warrior-card" key={warrior.id}><header><div><strong>{warrior.name}</strong><span>{warrior.profile_name}{warrior.kind !== "hero" ? ` · ${warrior.quantity ?? 1} ${t.members}` : ""}</span></div><b>{warrior.experience} XP</b></header>{warrior.condition && <p className="condition">{warrior.condition}{warrior.condition_detail ? ` · ${warrior.condition_detail}` : ""}</p>}<div className="stats">{Object.entries(warrior.stats).map(([key,value]) => { const modifier=warrior.stat_modifiers?.[key] ?? 0; return <span key={key}><small>{key}</small>{value + modifier}</span>; })}</div><h4>{t.equipment}</h4><p>{warrior.equipment.map((entry) => `${entry.quantity}× ${entry.name}`).join(", ") || t.none}</p><h4>{t.skills}</h4><p>{[...warrior.skills, ...(warrior.special_rules ?? [])].join(", ") || t.none}</p>{warrior.games_to_miss ? <p className="condition">{warrior.absence_reason ?? t.recovery} · {t.misses} {warrior.games_to_miss} {t.battles}</p> : null}{warrior.kind === "hireling" && <p>{t.rating} {warrior.hireling_rating ?? 0}{warrior.upkeep_resources?.length ? ` · ${t.upkeep} ${warrior.upkeep_resources.map(([resource, amount]) => `${amount} ${resource}`).join(" + ")}` : ""}</p>}</article>)}</div>}
    {editable && <form className="inline-form" onSubmit={(event) => { event.preventDefault(); if(name.trim()) void app.runAction("renameWarband", { name: name.trim() }); setName(""); }}><label>{t.rename}<input value={name} onChange={(event) => setName(event.target.value)} /></label><button disabled={!name.trim()}>{t.apply}</button></form>}
  </section>;
}

export function CampaignSlice({ knowledge, locale = "en" }: { knowledge?: ArtefactKnowledgeReader; locale?: "es" | "en" }) {
  const app = useCampaignApp(); const doc = app.document;
  if (!doc) return null;
  const selected = String(doc.view.selected_moment ?? `state:${doc.campaign.current_state_number}`);
  const battleNumber = Number(selected.split(":")[1] ?? 0);
  const battle = doc.campaign.battles.find((row) => row.number === battleNumber);
  const selectedPost = doc.campaign.post_battles.find((row) => row.battle_number === battleNumber);
  const currentState = selected === `state:${doc.campaign.current_state_number}`;
  const selectedState = doc.campaign.states.find((state) => state.number === battleNumber);
  const stateDocument = selectedState ? { ...doc, campaign: { ...doc.campaign, warriors: selectedState.roster ?? [], inventory: selectedState.inventory ?? [] } } : doc;
  return <section aria-label="Campaign">
    {app.error && <output className="global-error" role="alert">{app.error} <button onClick={app.clearError}>{locale === "es" ? "Cerrar" : "Dismiss"}</button></output>}
    {app.dirty && <output className="dirty" role="status">{locale === "es" ? "Cambios sin exportar" : "Unsaved changes"}</output>}
    {doc.campaign.configuration.is_draft && knowledge ? <DraftWorkspace document={doc} knowledge={knowledge} locale={locale} /> : <div className="campaign-layout">
      <TimelinePanel document={doc} onSelect={app.selectMoment} locale={locale} />
      <div className="moment-detail">
        {selected.startsWith("state:") && <><RosterOverview document={doc} stateNumber={battleNumber} editable={currentState} locale={locale} /><EquipmentPanel document={stateDocument} readOnly={!currentState} locale={locale} />{currentState && <BattlePanel document={doc} knowledge={knowledge} locale={locale} />}</>}
        {selected.startsWith("battle:") && <BattleHistory battle={battle} locale={locale} />}
        {selected.startsWith("post:") && (selectedPost?.complete ? <PostBattleHistory document={doc} battleNumber={battleNumber} locale={locale} /> : <><BattlePanel document={doc} knowledge={knowledge} locale={locale} />{knowledge && <PostBattleInjuries document={doc} knowledge={knowledge} locale={locale} />}<InjuriesPanel document={doc} knowledge={knowledge} />{knowledge && <PostBattleExperience document={doc} knowledge={knowledge} locale={locale} />}{knowledge && <ExplorationPanel document={doc} knowledge={knowledge} locale={locale} />}{knowledge && <ScenarioFollowupsPanel document={doc} knowledge={knowledge} locale={locale} />}<FollowUpAcknowledgements document={doc} locale={locale}/>{knowledge && <WyrdstoneSalePanel document={doc} knowledge={knowledge} locale={locale} />}<VeteranPoolPanel document={doc} locale={locale} />{knowledge && <RecruitProfilePanel document={doc} knowledge={knowledge} locale={locale} />}<GroupRecruitmentPanel document={doc} locale={locale} />{knowledge && <RareSearchPanel document={doc} knowledge={knowledge} locale={locale} />}<HirelingsPanel document={doc} listings={knowledge} locale={locale} /><HirelingUpkeepPanel document={doc} locale={locale} /><EquipmentPanel document={doc} locale={locale} />{knowledge && <ManualSkillPanel document={doc} knowledge={knowledge} locale={locale} />}{knowledge && <ManualCorrectionsPanel document={doc} knowledge={knowledge} locale={locale} />}<ReviewPanel document={doc} locale={locale} /></>)}
      </div></div>}
  </section>;
}

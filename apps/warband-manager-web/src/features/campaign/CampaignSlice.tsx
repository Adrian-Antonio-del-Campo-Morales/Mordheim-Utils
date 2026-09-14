import { useEffect, useState } from "react";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { useCampaignApp } from "./useCampaignApp";
import { TimelinePanel } from "../timeline/TimelinePanel";
import { EquipmentPanel } from "../equipment/EquipmentPanel";
import { PostBattleInventory } from "../equipment/PostBattleInventory";
import { PostBattleExperience } from "../advances/PostBattleExperience";
import { HirelingsPanel } from "../hirelings/HirelingsPanel";
import { BattlePanel } from "../battle/BattlePanel";
import { BattleHistory } from "../battle/BattleHistory";
import { ReviewPanel } from "../review/ReviewPanel";
import { PostBattleHistory } from "../review/PostBattleHistory";
import { FollowUpAcknowledgements } from "../review/FollowUpAcknowledgements";
import { DraftWorkspace, ExperienceTrack } from "../draft/DraftWorkspace";
import { PostBattleInjuries } from "../injuries/PostBattleInjuries";
import { ExplorationPanel } from "../exploration/ExplorationPanel";
import { ScenarioFollowupsPanel } from "../exploration/ScenarioFollowupsPanel";
import { WyrdstoneSalePanel } from "../economy/WyrdstoneSalePanel";
import { VeteranPoolPanel } from "../recruitment/VeteranPoolPanel";
import { GroupRecruitmentPanel } from "../recruitment/GroupRecruitmentPanel";
import { RecruitProfilePanel } from "../recruitment/RecruitProfilePanel";
import { ManualSkillPanel } from "../advances/ManualSkillPanel";
import { RareSearchPanel } from "../searches/RareSearchPanel";
import type { CampaignDocument } from "./types";
import { warbandVariants } from "@domain/campaign/band-variants";
import { knowledgeName, localizedLabel, readableValue, resourceAmount } from "./displayText";
import { KnowledgeHint } from "./KnowledgeHint";
import { adaptCharacteristicValue } from "@app/rules/distance-display";
import { WarriorCard } from "./WarriorCard";

function RosterOverview({ document, stateNumber, editable, locale, section, knowledge }: { document: CampaignDocument; stateNumber: number; editable: boolean; locale: "es" | "en"; section: "overview" | "warriors"; knowledge?: ArtefactKnowledgeReader }) {
  const app = useCampaignApp(); const [name, setName] = useState("");
  const { campaign } = document;
  const snapshot = campaign.states.find((state) => state.number === stateNumber);
  const warriors = snapshot?.roster ?? (editable ? campaign.warriors : []);
  const t = locale === "es" ? { campaign:"Campaña",warband:"Banda",models:"Miniaturas",rating:"Valoración",treasury:"Tesorería",wyrdstone:"Piedra bruja",historical:"Histórico · solo lectura",roster:"Guerreros",effects:"Efectos activos",missing:"Este estado no contiene una instantánea de guerreros.",members:"miembros",equipment:"Equipo",skills:"Habilidades / heridas",none:"Ninguno",recovery:"Recuperación",misses:"se pierde",battles:"batalla(s)",upkeep:"Mantenimiento",rename:"Renombrar banda",apply:"Aplicar" } : { campaign:"Campaign",warband:"Warband",models:"Models",rating:"Rating",treasury:"Treasury",wyrdstone:"Wyrdstone",historical:"Historical · read only",roster:"Roster",effects:"Active effects",missing:"No roster snapshot is stored for this state.",members:"members",equipment:"Equipment",skills:"Skills / injuries",none:"None",recovery:"Recovery",misses:"misses",battles:"battle(s)",upkeep:"Upkeep",rename:"Rename warband",apply:"Apply" };
  if ((section as string) === "warriors") return <section aria-label={locale === "es" ? "Guerreros" : "Warriors"}>{warriors.length === 0 ? <p>{t.missing}</p> : <div className="warrior-grid">{warriors.map((warrior) => <WarriorCard key={warrior.id} warrior={warrior} knowledge={knowledge} locale={locale} bandId={campaign.identity.band_id} />)}</div>}</section>;
  return <section aria-label={section === "overview" ? (locale === "es" ? "Resumen de la banda" : "Warband overview") : locale === "es" ? "Guerreros" : "Warriors"}>
    {section === "overview" && <><dl className="campaign-metrics"><div><dt>{t.rating}</dt><dd>{snapshot?.rating ?? 0}</dd></div><div><dt>{t.models}</dt><dd>{snapshot?.models ?? warriors.reduce((sum, warrior) => sum + (warrior.quantity ?? 1), 0)}/{snapshot?.max_models ?? campaign.configuration.maximum_models}</dd></div><div><dt>{t.treasury}</dt><dd>{snapshot?.gold ?? 0} gc</dd></div><div><dt>{t.wyrdstone}</dt><dd>{snapshot?.wyrdstone ?? 0}</dd></div></dl>
      <div className="overview-columns"><article><span>{locale === "es" ? "BANDA EN ESTE MOMENTO" : "WARBAND AT THIS POINT"}</span><h3>{campaign.identity.warband_name}</h3><p>{knowledgeName(knowledge, "band", campaign.identity.band_id, locale, campaign.identity.warband_type)} · {warriors.length} {t.roster.toLowerCase()}</p></article><article><span>{locale === "es" ? "POSICIÓN EN LA CAMPAÑA" : "CAMPAIGN POSITION"}</span><h3>{editable ? (locale === "es" ? "Banda actual" : "Current warband") : t.historical}</h3><p>{campaign.identity.campaign_name}</p></article></div>
      {editable&&campaign.special_rules.length>0&&<><h3>{t.effects}</h3><ul>{campaign.special_rules.map((rule)=><li key={`${String(rule.source)}:${String(rule.text)}`}>{String(rule.text)}{rule.expires_after_battles!=null?` · ${rule.expires_after_battles} ${t.battles}`:""}</li>)}</ul></>}
      {editable && <form className="inline-form" onSubmit={(event) => { event.preventDefault(); if(name.trim()) void app.runAction("renameWarband", { name: name.trim() }); setName(""); }}><label>{t.rename}<input value={name} onChange={(event) => setName(event.target.value)} /></label><button disabled={!name.trim()} data-disabled-reason={!name.trim() ? (locale === "es" ? "Introduce un nombre para la banda." : "Enter a warband name.") : undefined}>{t.apply}</button></form>}</>}
    {section === "warriors" && <>{warriors.length === 0 ? <p>{t.missing}</p> : <div className="warrior-grid">{warriors.map((warrior) => <article className="warrior-card" key={warrior.id}><header><div><strong>{warrior.name}</strong><span>{knowledgeName(knowledge, "profile", warrior.profile_id, locale, warrior.profile_name)}{warrior.kind !== "hero" ? ` · ${warrior.quantity ?? 1} ${t.members}` : ""}</span></div><b>{warrior.experience} XP</b></header>{warrior.condition && <p className="condition">{readableValue(warrior.condition, locale)}{warrior.condition_detail ? ` · ${knowledgeName(knowledge, "injury", warrior.condition_detail, locale, warrior.condition_detail)}` : ""}</p>}<div className="stats">{Object.entries(warrior.stats).map(([key,value]) => <span key={key}><small>{localizedLabel(key, locale)}</small>{adaptCharacteristicValue(key, value, locale, warrior.stat_modifiers?.[key] ?? 0)}</span>)}</div><ExperienceTrack experience={warrior.experience} kind={warrior.kind} locale={locale} /><h4>{t.equipment}</h4><p>{warrior.equipment.length === 0 ? t.none : warrior.equipment.map((entry, index) => <span key={`${String(entry.item_id)}:${index}`}>{index > 0 ? ", " : ""}<KnowledgeHint knowledge={knowledge} kind="item" id={String(entry.item_id)} locale={locale}>{entry.quantity}× {knowledgeName(knowledge, "item", entry.item_id, locale, entry.name)}</KnowledgeHint></span>)}</p><h4>{t.skills}</h4><p>{warrior.skills.length === 0 && (warrior.special_rules ?? []).length === 0 ? t.none : <>{warrior.skills.map((skill, index) => <span key={`${String(skill)}:${index}`}>{index > 0 ? ", " : ""}<KnowledgeHint knowledge={knowledge} kind={String(skill).startsWith("skill.") ? "skill" : "rule"} id={String(skill)} locale={locale}>{knowledgeName(knowledge, "skill", skill, locale, skill)}</KnowledgeHint></span>)}{(warrior.special_rules ?? []).map((rule, index) => <span key={`rule:${index}`}>{warrior.skills.length + index > 0 ? ", " : ""}{readableValue(rule, locale)}</span>)}</>}</p>{warrior.games_to_miss ? <p className="condition">{readableValue(warrior.absence_reason ?? t.recovery, locale)} · {t.misses} {warrior.games_to_miss} {t.battles}</p> : null}{warrior.kind === "hireling" && <p>{t.rating} {warrior.hireling_rating ?? 0}{warrior.upkeep_resources?.length ? ` · ${t.upkeep} ${warrior.upkeep_resources.map(([resource, amount]) => resourceAmount(resource, amount, locale)).join(" + ")}` : ""}</p>}</article>)}</div>}</>}
  </section>;
}

function StateWorkspace({ document, stateDocument, stateNumber, editable, locale, knowledge }: { document: CampaignDocument; stateDocument: CampaignDocument; stateNumber: number; editable: boolean; locale: "es" | "en"; knowledge?: ArtefactKnowledgeReader }) {
  const [section, setSection] = useState<"overview" | "warriors" | "inventory">("overview");
  const snapshot = document.campaign.states.find((state) => state.number === stateNumber);
  const labels = locale === "es" ? { current:"BANDA ACTUAL", initial:"BANDA INICIAL", state:"ESTADO DE BANDA", historical:"HISTÓRICO · SOLO LECTURA", overview:"RESUMEN", warriors:"GUERREROS", inventory:"INVENTARIO", start:"Inicio de la campaña", after:"Después de la batalla" } : { current:"CURRENT WARBAND", initial:"INITIAL WARBAND", state:"WARBAND STATE", historical:"HISTORICAL · READ ONLY", overview:"OVERVIEW", warriors:"WARRIORS", inventory:"INVENTORY", start:"Campaign starting point", after:"After battle" };
  const title = editable ? labels.current : stateNumber === 0 ? labels.initial : `${labels.state} #${stateNumber}`;
  return <div className="state-workspace"><header className="moment-heading"><div><h2>{title}</h2><p>{stateNumber === 0 ? labels.start : `${labels.after} #${stateNumber}${snapshot?.date ? ` · ${snapshot.date}` : ""}`}</p></div>{!editable && <span>{labels.historical}</span>}</header>
    <nav className="segmented-tabs" aria-label={locale === "es" ? "Secciones de la banda" : "Warband sections"}>{(["overview","warriors","inventory"] as const).map((key)=><button key={key} className={section===key ? "active" : ""} aria-pressed={section===key} onClick={()=>setSection(key)}>{labels[key]}</button>)}</nav>
    {section !== "inventory" ? <RosterOverview document={document} stateNumber={stateNumber} editable={editable} locale={locale} section={section} knowledge={knowledge} /> : <EquipmentPanel document={stateDocument} readOnly={!editable} locale={locale} knowledge={knowledge} />}
  </div>;
}

function PostBattleWorkspace({ document, knowledge, locale }: { document: CampaignDocument; knowledge?: ArtefactKnowledgeReader; locale: "es" | "en" }) {
  const app = useCampaignApp();
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const [selectedStep, setSelectedStep] = useState(post?.active_step ?? 0);
  const [reviewOpen, setReviewOpen] = useState(Boolean(post?.review_open));
  useEffect(() => { if (post) { setSelectedStep(post.active_step); setReviewOpen(Boolean(post.review_open)); } }, [post]);
  if (!post) return null;
  const labels = locale === "es"
    ? ["Heridas", "Experiencia", "Exploración", "Vender piedra bruja", "Veteranos", "Objetos raros y Dramatis", "Reclutamiento", "Equipo"]
    : ["Injuries", "Experience", "Exploration", "Sell wyrdstone", "Veterans", "Rare items & Dramatis", "Recruitment", "Equipment"];
  const step = selectedStep;
  const next = () => void app.runAction("resolvePostBattleStep", { battle_number: post.battle_number });
  const selectStep = (index: number) => { setSelectedStep(index); setReviewOpen(false); };
  const chapters = locale === "es" ? ["Recuperación", "Exploración e ingresos", "Búsquedas", "Banda"] : ["Recovery", "Exploration & income", "Searches", "Warband"];
  const review = reviewOpen;
  return <>
    <header className="moment-heading post-battle-heading"><div><h2>{locale === "es" ? `POSTBATALLA #${post.battle_number}` : `POST-BATTLE #${post.battle_number}`}</h2><p>{locale === "es" ? "Resuelve la secuencia para crear el siguiente estado de banda." : "Resolve the sequence to create the next warband state."}</p></div><div className="post-battle-heading-actions"><span>{review ? (locale === "es" ? "REVISIÓN FINAL" : "FINAL REVIEW") : (locale === "es" ? "EN CURSO" : "IN PROGRESS")}</span><button type="button" onClick={() => void app.exportFile()}>{locale === "es" ? "GUARDAR Y CERRAR" : "SAVE & CLOSE"}</button></div></header>
    <p className="post-battle-intro">{locale === "es" ? "Resuelve Batalla #" + post.battle_number + " en orden. Las ocho acciones crean el siguiente estado; la valoración se recalcula automáticamente." : "Resolve Battle #" + post.battle_number + " in order. The eight actions create the next warband state; rating is recalculated automatically."}</p>
    <section aria-label={locale === "es" ? "Fase post-batalla" : "Post-battle phase"} className="post-battle-sequence"><header><div><span>{review ? (locale === "es" ? "SECUENCIA COMPLETA" : "SEQUENCE COMPLETE") : (locale === "es" ? `PASO ${Math.min(step + 1, 8)} DE 8` : `STEP ${Math.min(step + 1, 8)} OF 8`)}</span><h2>{review ? (locale === "es" ? "REVISIÓN FINAL" : "FINAL REVIEW") : labels[step]}</h2></div><b>{review ? (locale === "es" ? "8 ACCIONES COMPLETADAS" : "8 ACTIONS COMPLETE") : (locale === "es" ? `${7-post.active_step} ACCIONES RESTANTES` : `${7-post.active_step} ACTIONS REMAIN`)}</b></header><div className="post-battle-chapters">{chapters.map((chapter,index)=><div key={chapter}><strong>{chapter}</strong>{labels.slice(index*2,index*2+2).map((label,offset)=>{const position=index*2+offset;const complete=review || position<post.active_step;const active=!review && position===step;return <button type="button" key={label} className={active ? "active" : complete ? "complete" : ""} disabled={position>post.active_step} data-disabled-reason={position>post.active_step ? (locale === "es" ? "Completa primero los pasos anteriores." : "Complete the previous steps first.") : undefined} onClick={() => position<=post.active_step && selectStep(position)}>{complete ? "✓ " : ""}{label}</button>;})}</div>)}</div>{!review && step === post.active_step && step < 7 && <button className="primary" type="button" onClick={next}>{locale === "es" ? `Continuar a ${labels[step + 1]}` : `Continue to ${labels[step + 1]}`}</button>}</section>
    {!review && step === 0 && <>{knowledge && <PostBattleInjuries document={document} knowledge={knowledge} locale={locale} />}<FollowUpAcknowledgements document={document} locale={locale} /></>}
    {!review && step === 1 && <>{knowledge && <PostBattleExperience document={document} knowledge={knowledge} locale={locale} />}{knowledge && <ManualSkillPanel document={document} knowledge={knowledge} locale={locale} />}<FollowUpAcknowledgements document={document} locale={locale} /></>}
    {!review && step === 2 && <>{knowledge && <ExplorationPanel document={document} knowledge={knowledge} locale={locale} />}{knowledge && <ScenarioFollowupsPanel document={document} knowledge={knowledge} locale={locale} />}<FollowUpAcknowledgements document={document} locale={locale} /></>}
    {!review && step === 3 && knowledge && <WyrdstoneSalePanel document={document} knowledge={knowledge} locale={locale} />}
    {!review && step === 4 && <VeteranPoolPanel document={document} locale={locale} />}
    {!review && step === 5 && knowledge && <RareSearchPanel document={document} knowledge={knowledge} locale={locale} />}
    {!review && step === 6 && <>{knowledge && <RecruitProfilePanel document={document} knowledge={knowledge} locale={locale} />}<GroupRecruitmentPanel document={document} locale={locale} />{knowledge && <HirelingsPanel document={document} listings={knowledge} locale={locale} mode="hirelings" />}</>}
    {!review && step === 7 && <><PostBattleInventory document={document} locale={locale} knowledge={knowledge} />{step === post.active_step && <button type="button" className="primary review-button" onClick={() => setReviewOpen(true)}>{locale === "es" ? "ABRIR REVISIÓN FINAL" : "OPEN FINAL REVIEW"}</button>}</>}
    {review && <ReviewPanel document={document} locale={locale} knowledge={knowledge} onReturnToStep={selectStep} />}
  </>;
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
  const variants = knowledge ? warbandVariants(knowledge, doc.campaign.identity.band_id) : [];
  const selectedVariant = variants.find((variant) => variant.id === doc.campaign.identity.mercenary_variant);
  return <section aria-label={locale === "es" ? "Campaña" : "Campaign"}>
    {app.error && <output className="global-error" role="alert">{app.error} <button onClick={app.clearError}>{locale === "es" ? "Cerrar" : "Dismiss"}</button></output>}
    {app.dirty && <output className="dirty" role="status">{locale === "es" ? "Cambios sin exportar" : "Unsaved changes"}</output>}
    {variants.length > 0 && (selectedVariant ? <p className="variant-selector"><span>{locale === "es" ? "VARIANTE DE BANDA" : "WARBAND VARIANT"}</span><strong>{selectedVariant.names[locale]??selectedVariant.names.en??selectedVariant.id}</strong></p> : doc.campaign.configuration.is_draft ? <label className="variant-selector">{locale === "es" ? "VARIANTE DE BANDA" : "WARBAND VARIANT"}<select value="" onChange={(event)=>event.target.value&&void app.runAction("setMercenaryVariant",{variant:event.target.value})}><option value="">{locale === "es" ? "Selecciona una variante…" : "Select a variant…"}</option>{variants.map((variant)=><option key={variant.id} value={variant.id}>{variant.names[locale]??variant.names.en??variant.id}</option>)}</select></label> : <p className="variant-selector"><span>{locale === "es" ? "VARIANTE DE BANDA" : "WARBAND VARIANT"}</span><strong>{locale === "es" ? "No registrada" : "Not recorded"}</strong></p>)}
    <div className="campaign-layout">
      <TimelinePanel document={doc} onSelect={app.selectMoment} locale={locale} knowledge={knowledge} />
      <div className="moment-detail">
        {doc.campaign.configuration.is_draft && knowledge
          ? <DraftWorkspace document={doc} knowledge={knowledge} locale={locale} />
          : <>
            {selected.startsWith("state:") && <StateWorkspace document={doc} stateDocument={stateDocument} stateNumber={battleNumber} editable={currentState} locale={locale} knowledge={knowledge} />}
            {selected.startsWith("battle:") && <BattleHistory battle={battle} locale={locale} knowledge={knowledge} />}
            {selected.startsWith("post:") && (selectedPost?.complete ? <PostBattleHistory document={doc} battleNumber={battleNumber} locale={locale} /> : <PostBattleWorkspace document={doc} knowledge={knowledge} locale={locale} />)}
            {selected.startsWith("new-battle:") && <BattlePanel document={doc} knowledge={knowledge} locale={locale} />}
          </>}
      </div>
    </div>
  </section>;
}

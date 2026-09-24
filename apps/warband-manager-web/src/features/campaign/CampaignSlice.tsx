import { presentationOutput } from "./presentation-output";
import { textJoin, textNumber, textSymbol, textDate, warriorPersonalName, warbandPersonalName, campaignPersonalName, warriorCharacteristic } from "./presentation-values";
import { translate } from "./i18n-core";
import { useLocale } from "./i18n-context";
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
import { variantName, warriorAbilityRef, knowledgeName, localizedLabel, readableValue, resourceAmount, persistedSystemText, numberText } from "./displayText";
import { KnowledgeHint } from "./KnowledgeHint";
import { WarriorCard } from "./WarriorCard";

function RosterOverview({ document, stateNumber, editable, locale, section, knowledge }: { document: CampaignDocument; stateNumber: number; editable: boolean; locale: "es" | "en"; section: "overview" | "warriors"; knowledge?: ArtefactKnowledgeReader }) {
  const app = useCampaignApp(); const [name, setName] = useState("");
  const { campaign } = document;
  const snapshot = campaign.states.find((state) => state.number === stateNumber);
  const warriors = snapshot?.roster ?? (editable ? campaign.warriors : []);
  const t = ({ campaign: translate({ key: "ui.13624dd6f3e9" }, locale), warband: translate({ key: "ui.e64208a1bf43" }, locale), models: translate({ key: "ui.c0aa3b1775b4" }, locale), rating: translate({ key: "ui.f60eeb2b86e6" }, locale), treasury: translate({ key: "ui.29be415cf396" }, locale), wyrdstone: translate({ key: "ui.e71905bfd3f8" }, locale), historical: translate({ key: "ui.054aac3b0e58" }, locale), roster: translate({ key: "ui.3087408dfd27" }, locale), effects: translate({ key: "ui.2dcceac3888b" }, locale), missing: translate({ key: "ui.db2d9b7100c7" }, locale), members: translate({ key: "ui.9abf0cda8484" }, locale), equipment: translate({ key: "ui.9cd4c565ba6e" }, locale), skills: translate({ key: "ui.4681df7bfdab" }, locale), none: translate({ key: "ui.6a8d295b694b" }, locale), recovery: translate({ key: "ui.9de7c707a1b0" }, locale), misses: translate({ key: "ui.121a506a3e31" }, locale), battles: translate({ key: "ui.b7f848785b92" }, locale), upkeep: translate({ key: "ui.15e8bb635504" }, locale), rename: translate({ key: "ui.328ffdd25e14" }, locale), apply: translate({ key: "ui.1c75188ca8d2" }, locale) });
  if ((section as string) === "warriors") return <section aria-label={presentationOutput(translate({ key: "ui.0353ddc7f0d9" }, locale))}>{warriors.length === 0 ? <p>{presentationOutput(t.missing)}</p> : <div className="warrior-grid">{warriors.map((warrior) => <WarriorCard key={warrior.id} warrior={warrior} knowledge={knowledge} locale={locale} bandId={campaign.identity.band_id} />)}</div>}</section>;
  return <section aria-label={presentationOutput(section === "overview" ? (translate({ key: "ui.411133d2954f" }, locale)) : translate({ key: "ui.0353ddc7f0d9" }, locale))}>
    {section === "overview" && <><dl className="campaign-metrics"><div><dt>{presentationOutput(t.rating)}</dt><dd>{presentationOutput(textNumber(snapshot?.rating ?? 0, locale))}</dd></div><div><dt>{presentationOutput(t.models)}</dt><dd>{presentationOutput(textNumber(snapshot?.models ?? warriors.reduce((sum, warrior) => sum + (warrior.quantity ?? 1), 0), locale))}{presentationOutput(textSymbol("/"))}{presentationOutput(textNumber(snapshot?.max_models ?? campaign.configuration.maximum_models, locale))}</dd></div><div><dt>{presentationOutput(t.treasury)}</dt><dd>{presentationOutput(textJoin([textNumber(snapshot?.gold ?? 0, locale), translate({ key: "unit.gold" }, locale)]))}</dd></div><div><dt>{presentationOutput(t.wyrdstone)}</dt><dd>{presentationOutput(textNumber(snapshot?.wyrdstone ?? 0, locale))}</dd></div></dl>
      <div className="overview-columns"><article><span>{presentationOutput(translate({ key: "ui.799b655b2fc6" }, locale))}</span><h3>{presentationOutput(warbandPersonalName(campaign, locale))}</h3><p>{presentationOutput(knowledgeName(knowledge, "band", campaign.identity.band_id, locale))} {presentationOutput(textSymbol("·"))} {presentationOutput(textNumber(warriors.length, locale))} {presentationOutput(t.roster)}</p></article><article><span>{presentationOutput(translate({ key: "ui.8feeaf34ba00" }, locale))}</span><h3>{presentationOutput(editable ? (translate({ key: "ui.ab308749f6e0" }, locale)) : t.historical)}</h3><p>{presentationOutput(campaignPersonalName(campaign, locale))}</p></article></div>
      {editable&&campaign.special_rules.length>0&&<><h3>{presentationOutput(t.effects)}</h3><ul>{campaign.special_rules.map((rule)=><li key={`${String(rule.source)}:${persistedSystemText(rule.text, knowledge, locale)}`}>{presentationOutput(persistedSystemText(rule.text, knowledge, locale))}{presentationOutput(rule.expires_after_battles!=null?textJoin([textSymbol("·"), numberText(rule.expires_after_battles, locale), t.battles]):textSymbol(""))}</li>)}</ul></>}
      {editable && <form className="inline-form" onSubmit={(event) => { event.preventDefault(); if(name.trim()) void app.runAction("renameWarband", { name: name.trim() }); setName(""); }}><label>{presentationOutput(t.rename)}<input value={name} onChange={(event) => setName(event.target.value)} /></label><button disabled={!name.trim()} data-disabled-reason={(!name.trim() ? (translate({ key: "disabled.2631ab5bb6" }, locale)) : undefined) === undefined ? undefined : presentationOutput((!name.trim() ? (translate({ key: "disabled.2631ab5bb6" }, locale)) : undefined)!)}>{presentationOutput(t.apply)}</button></form>}</>}
    {section === "warriors" && <>{warriors.length === 0 ? <p>{presentationOutput(t.missing)}</p> : <div className="warrior-grid">{warriors.map((warrior) => <article className="warrior-card" key={warrior.id}><header><div><strong>{presentationOutput(warriorPersonalName(warrior, locale))}</strong><span>{presentationOutput(knowledgeName(knowledge, warrior.kind === "hireling" ? "hireling" : "profile", warrior.profile_id, locale))}{presentationOutput(warrior.kind !== "hero" ? textJoin([textSymbol("·"), textNumber(warrior.quantity ?? 1, locale), t.members]) : textSymbol(""))}</span></div><b>{presentationOutput(textJoin([textNumber(warrior.experience, locale), translate({ key: "unit.experience" }, locale)]))}</b></header>{warrior.condition && <p className="condition">{presentationOutput(readableValue(warrior.condition, locale))}{presentationOutput(warrior.condition_detail ? textJoin([textSymbol("·"), knowledgeName(knowledge, "injury", warrior.condition_detail, locale)]) : textSymbol(""))}</p>}<div className="stats">{(["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld"] as const).filter((key) => Object.hasOwn(warrior.stats, key)).map((key) => <span key={key}><small>{presentationOutput(localizedLabel(key, locale))}</small>{presentationOutput(warriorCharacteristic(warrior, key, locale))}</span>)}</div><ExperienceTrack experience={warrior.experience} kind={warrior.kind} locale={locale} /><h4>{presentationOutput(t.equipment)}</h4><p>{warrior.equipment.length === 0 ? presentationOutput(t.none) : warrior.equipment.map((entry, index) => <span key={`${String(entry.item_id)}:${index}`}>{presentationOutput(index > 0 ? textJoin([textSymbol(""), textSymbol("")], ", ") : textSymbol(""))}<KnowledgeHint knowledge={knowledge} kind="item" id={String(entry.item_id)} locale={locale} quantity={entry.quantity} /></span>)}</p><h4>{presentationOutput(t.skills)}</h4><p>{warrior.skills.length === 0 && (warrior.special_rules ?? []).length === 0 ? presentationOutput(t.none) : <>{warrior.skills.map((skill, index) => <span key={`${String(skill)}:${index}`}>{presentationOutput(index > 0 ? textJoin([textSymbol(""), textSymbol("")], ", ") : textSymbol(""))}<KnowledgeHint knowledge={knowledge} {...warriorAbilityRef(knowledge, skill, warrior.profile_id, campaign.identity.band_id)} locale={locale} /></span>)}{(warrior.special_rules ?? []).map((rule, index) => <span key={`rule:${index}`}>{presentationOutput(warrior.skills.length + index > 0 ? textJoin([textSymbol(""), textSymbol("")], ", ") : textSymbol(""))}<KnowledgeHint knowledge={knowledge} {...warriorAbilityRef(knowledge, rule, warrior.profile_id, campaign.identity.band_id)} locale={locale} /></span>)}</>}</p>{warrior.games_to_miss ? <p className="condition">{presentationOutput(readableValue(warrior.absence_reason ?? t.recovery, locale))} {presentationOutput(textSymbol("·"))} {presentationOutput(t.misses)} {presentationOutput(textNumber(warrior.games_to_miss, locale))} {presentationOutput(t.battles)}</p> : null}{warrior.kind === "hireling" && <p>{presentationOutput(t.rating)} {presentationOutput(textNumber(warrior.hireling_rating ?? 0, locale))}{presentationOutput(warrior.upkeep_resources?.length ? textJoin([textSymbol("·"), t.upkeep, textJoin(warrior.upkeep_resources.map(([resource, amount]) => resourceAmount(resource, amount, locale)), " + ")]) : textSymbol(""))}</p>}</article>)}</div>}</>}
  </section>;
}

function StateWorkspace({ document, stateDocument, stateNumber, editable, locale, knowledge }: { document: CampaignDocument; stateDocument: CampaignDocument; stateNumber: number; editable: boolean; locale: "es" | "en"; knowledge?: ArtefactKnowledgeReader }) {
  const [section, setSection] = useState<"overview" | "warriors" | "inventory">("overview");
  const snapshot = document.campaign.states.find((state) => state.number === stateNumber);
  const labels = ({ current: translate({ key: "ui.8ecebcd3674d" }, locale), initial: translate({ key: "ui.9a8120609a70" }, locale), state: translate({ key: "ui.e17273d2c651" }, locale), historical: translate({ key: "ui.a3f44355ebb1" }, locale), overview: translate({ key: "ui.8334ecd1c008" }, locale), warriors: translate({ key: "ui.93979f125f4d" }, locale), inventory: translate({ key: "ui.07bf0f8e6179" }, locale), start: translate({ key: "ui.69ed62ca66ad" }, locale), after: translate({ key: "ui.d6268fdb89b0" }, locale) });
  const title = editable ? labels.current : stateNumber === 0 ? labels.initial : textJoin([labels.state, textJoin([textSymbol("#"), textNumber(stateNumber, locale)], "")]);
  return <div className="state-workspace"><header className="moment-heading"><div><h2>{presentationOutput(title)}</h2><p>{presentationOutput(stateNumber === 0 ? labels.start : textJoin([labels.after, textJoin([textSymbol("#"), textNumber(stateNumber, locale)], ""), ...(snapshot?.date ? [textSymbol("·"), textDate(snapshot.date, locale)] : [])]))}</p></div>{!editable && <span>{presentationOutput(labels.historical)}</span>}</header>
    <nav className="segmented-tabs" aria-label={presentationOutput(translate({ key: "ui.162d648fe627" }, locale))}>{(["overview","warriors","inventory"] as const).map((key)=><button key={key} className={section===key ? "active" : ""} aria-pressed={section===key} onClick={()=>setSection(key)}>{presentationOutput(labels[key])}</button>)}</nav>
    {section !== "inventory" ? <RosterOverview document={document} stateNumber={stateNumber} editable={editable} locale={locale} section={section} knowledge={knowledge} /> : <EquipmentPanel document={stateDocument} readOnly={!editable} locale={locale} knowledge={knowledge} />}
  </div>;
}

function PostBattleWorkspace({ document, knowledge, locale }: { document: CampaignDocument; knowledge?: ArtefactKnowledgeReader; locale: "es" | "en" }) {
  const app = useCampaignApp();
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const [selectedStep, setSelectedStep] = useState(post?.active_step ?? 0);
  const [reviewOpen, setReviewOpen] = useState(Boolean(post?.review_open));
  const [showSteps, setShowSteps] = useState(false);
  useEffect(() => { if (post) { setSelectedStep(post.active_step); setReviewOpen(Boolean(post.review_open)); } }, [post]);
  if (!post) return null;
  const labels = (["post.step.0", "post.step.1", "post.step.2", "post.step.3", "post.step.4", "post.step.5", "post.step.6", "post.step.7"] as const).map((key) => translate({ key }, locale));
  const step = selectedStep;
  const next = () => void app.runAction("resolvePostBattleStep", { battle_number: post.battle_number });
  const selectStep = (index: number) => { setSelectedStep(index); setReviewOpen(false); setShowSteps(false); };
  const chapters = (["post.chapter.recovery", "post.chapter.income", "post.chapter.searches", "post.chapter.warband"] as const).map((key) => translate({ key }, locale));
  const review = reviewOpen;
  return <>
    <header className="moment-heading post-battle-heading"><div><h2>{presentationOutput(translate({ key: "post.heading", args: { number: post.battle_number } }, locale))}</h2><p>{presentationOutput(translate({ key: "ui.47cb848ffe78" }, locale))}</p></div><div className="post-battle-heading-actions"><span>{presentationOutput(review ? (translate({ key: "ui.aabfe3740206" }, locale)) : (translate({ key: "ui.476818ee97b0" }, locale)))}</span><button type="button" onClick={() => void app.exportFile()}>{presentationOutput(translate({ key: "ui.f69e0bcbc5b6" }, locale))}</button></div></header>
    <p className="post-battle-intro">{presentationOutput(translate({ key: "post.intro", args: { number: post.battle_number } }, locale))}</p>
    <section aria-label={presentationOutput(translate({ key: "ui.1e17b2c3e474" }, locale))} className="post-battle-sequence"><header><div><span>{presentationOutput(review ? (translate({ key: "ui.c80fc9052a9b" }, locale)) : (translate({ key: "post.step", args: { number: Math.min(step + 1, 8) } }, locale)))}</span><h2>{presentationOutput(review ? (translate({ key: "ui.aabfe3740206" }, locale)) : labels[step])}</h2></div>{!review && step === post.active_step && step < 7 && <button className="primary post-battle-continue" type="button" onClick={next}>{presentationOutput(translate({ key: "post.continue", args: { name: labels[step + 1] ?? translate({ key: "knowledge.unavailable" }, locale) } }, locale))}</button>}<b>{presentationOutput(review ? (translate({ key: "ui.a2ff55344da5" }, locale)) : (translate({ key: "post.remaining", args: { count: 7-post.active_step } }, locale)))}</b></header><button type="button" className="mobile-steps-toggle" aria-expanded={showSteps} aria-controls="post-battle-steps" onClick={() => setShowSteps(!showSteps)}>{presentationOutput(translate({ key: showSteps ? "post.hide-steps" : "post.show-steps" }, locale))}</button><div id="post-battle-steps" className={`post-battle-chapters ${showSteps ? "steps-expanded" : ""}`}>{chapters.map((chapter,index)=><div key={chapter}><strong>{presentationOutput(chapter)}</strong>{labels.slice(index*2,index*2+2).map((label,offset)=>{const position=index*2+offset;const complete=review || position<post.active_step;const active=!review && position===step;return <button type="button" key={label} className={active ? "active" : complete ? "complete" : ""} aria-current={active ? "step" : undefined} disabled={position>post.active_step} data-disabled-reason={(position>post.active_step ? (translate({ key: "disabled.f894850cd4" }, locale)) : undefined) === undefined ? undefined : presentationOutput((position>post.active_step ? (translate({ key: "disabled.f894850cd4" }, locale)) : undefined)!)} onClick={() => position<=post.active_step && selectStep(position)}>{presentationOutput(complete ? textJoin([textSymbol("✓"), label]) : label)}</button>;})}</div>)}</div></section>
    {!review && step === 0 && <>{knowledge && <PostBattleInjuries document={document} knowledge={knowledge} locale={locale} />}<FollowUpAcknowledgements document={document} knowledge={knowledge} locale={locale} /></>}
    {!review && step === 1 && <>{knowledge && <PostBattleExperience document={document} knowledge={knowledge} locale={locale} />}{knowledge && <ManualSkillPanel document={document} knowledge={knowledge} locale={locale} />}<FollowUpAcknowledgements document={document} knowledge={knowledge} locale={locale} /></>}
    {!review && step === 2 && <>{knowledge && <ExplorationPanel document={document} knowledge={knowledge} locale={locale} />}{knowledge && <ScenarioFollowupsPanel document={document} knowledge={knowledge} locale={locale} />}<FollowUpAcknowledgements document={document} knowledge={knowledge} locale={locale} /></>}
    {!review && step === 3 && knowledge && <WyrdstoneSalePanel document={document} knowledge={knowledge} locale={locale} />}
    {!review && step === 4 && <VeteranPoolPanel document={document} locale={locale} />}
    {!review && step === 5 && knowledge && <RareSearchPanel document={document} knowledge={knowledge} locale={locale} />}
    {!review && step === 6 && <>{knowledge && <RecruitProfilePanel document={document} knowledge={knowledge} locale={locale} />}<GroupRecruitmentPanel document={document} locale={locale} />{knowledge && <HirelingsPanel document={document} listings={knowledge} locale={locale} mode="hirelings" />}</>}
    {!review && step === 7 && <><PostBattleInventory document={document} locale={locale} knowledge={knowledge} />{step === post.active_step && <button type="button" className="primary review-button" onClick={() => setReviewOpen(true)}>{presentationOutput(translate({ key: "ui.907742abe541" }, locale))}</button>}</>}
    {review && <ReviewPanel document={document} locale={locale} knowledge={knowledge} onReturnToStep={selectStep} />}
  </>;
}

export function CampaignSlice({ knowledge, locale: requestedLocale }: { knowledge?: ArtefactKnowledgeReader; locale?: "es" | "en" }) {
  const locale = useLocale(requestedLocale);
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
  return <section aria-label={presentationOutput(translate({ key: "ui.13624dd6f3e9" }, locale))}>
    {app.error && <output className="global-error" role="alert">{presentationOutput(app.error)} <button onClick={app.clearError}>{presentationOutput(translate({ key: "ui.0c99ad9060fa" }, locale))}</button></output>}
    {app.dirty && <output className="dirty" role="status">{presentationOutput(translate({ key: "ui.1a29a258de18" }, locale))}</output>}
    {variants.length > 0 && (selectedVariant ? <p className="variant-selector"><span>{presentationOutput(translate({ key: "ui.10d94770cc2b" }, locale))}</span><strong>{presentationOutput(variantName(knowledge, doc.campaign.identity.band_id, selectedVariant.id, locale))}</strong></p> : doc.campaign.configuration.is_draft ? <label className="variant-selector">{presentationOutput(translate({ key: "ui.10d94770cc2b" }, locale))}<select value="" onChange={(event)=>event.target.value&&void app.runAction("setMercenaryVariant",{variant:event.target.value})}><option value="">{presentationOutput(translate({ key: "ui.0333b61e34a6" }, locale))}</option>{variants.map((variant)=><option key={variant.id} value={variant.id}>{presentationOutput(variantName(knowledge, doc.campaign.identity.band_id, variant.id, locale))}</option>)}</select></label> : <p className="variant-selector"><span>{presentationOutput(translate({ key: "ui.10d94770cc2b" }, locale))}</span><strong>{presentationOutput(translate({ key: "ui.44ffe1fec69b" }, locale))}</strong></p>)}
    <div className="campaign-layout">
      <TimelinePanel document={doc} onSelect={app.selectMoment} locale={locale} knowledge={knowledge} />
      <div className="moment-detail">
        {doc.campaign.configuration.is_draft && knowledge
          ? <DraftWorkspace document={doc} knowledge={knowledge} locale={locale} />
          : <>
            {selected.startsWith("state:") && <StateWorkspace document={doc} stateDocument={stateDocument} stateNumber={battleNumber} editable={currentState} locale={locale} knowledge={knowledge} />}
            {selected.startsWith("battle:") && <BattleHistory battle={battle} locale={locale} knowledge={knowledge} />}
            {selected.startsWith("post:") && (selectedPost?.complete ? <PostBattleHistory document={doc} battleNumber={battleNumber} locale={locale} knowledge={knowledge} /> : <PostBattleWorkspace document={doc} knowledge={knowledge} locale={locale} />)}
            {selected.startsWith("new-battle:") && <BattlePanel document={doc} knowledge={knowledge} locale={locale} />}
          </>}
      </div>
    </div>
  </section>;
}

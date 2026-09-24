import { presentationOutput } from "../campaign/presentation-output";
import { textJoin, textNumber, textSymbol, textDate, battleParticipantName, opponentPersonalName, battlePersonalNotes, type PresentationValue } from "../campaign/presentation-values";
import { translate } from "../campaign/i18n-core";
import { useState } from "react";
import type { CampaignDocument } from "../campaign/types";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { knowledgeName, localizedLabel } from "../campaign/displayText";

type Battle = CampaignDocument["campaign"]["battles"][number];
function highlightsFor(battle: Battle, locale: "es" | "en", knowledge?: ArtefactKnowledgeReader): PresentationValue[] {
  const results = battle.scenario_results ?? {};
  const lines: PresentationValue[] = [];
  const enemyOoa = results["enemy_out_of_action_by_warrior"];
  const numeric = (value: unknown) => typeof value === "number" ? value : NaN;
  if (enemyOoa && typeof enemyOoa === "object") for (const [id, amount] of Object.entries(enemyOoa)) {
    if (amount) lines.push(translate({ key: "battle.enemy-ooa", args: { name: battleParticipantName(battle, id, locale), amount: numeric(amount) } }, locale));
  }
  const objectives = results["objectives"];
  if (objectives && typeof objectives === "object") for (const value of Object.values(objectives)) {
    if (!value || typeof value !== "object") { lines.push(translate({ key: "knowledge.unavailable" }, locale)); continue; }
    const row = value as Record<string, unknown>;
    if (row.recipient && row.amount) lines.push(translate({ key: "battle.objective", args: { name: battleParticipantName(battle, row.recipient, locale), amount: numeric(row.amount) } }, locale));
    if (row.recipients && typeof row.recipients === "object") for (const [id, amount] of Object.entries(row.recipients)) {
      if (amount) lines.push(translate({ key: "battle.objective", args: { name: battleParticipantName(battle, id, locale), amount: numeric(amount) } }, locale));
    }
  }
  if (Array.isArray(results.additional_rewards)) for (const value of results.additional_rewards) {
    if (!value || typeof value !== "object") { lines.push(translate({ key: "knowledge.unavailable" }, locale)); continue; }
    const row = value as Record<string, unknown>;
    const amount = numeric(row.quantity);
    if (row.kind === "exploration") lines.push(translate({ key: "ui.d81adea8fa8a" }, locale));
    else if (row.resource === "gold_crowns") lines.push(translate({ key: "battle.gold-reward", args: { amount } }, locale));
    else if (row.resource === "wyrdstone_fragments") lines.push(translate({ key: "battle.shard-reward", args: { amount } }, locale));
    else if (row.kind === "item" || row.kind === "special") lines.push(translate({ key: "knowledge.quantity", args: { quantity: amount, name: knowledgeName(knowledge, "item", row.item_id, locale) } }, locale));
  }
  return lines;
}

export function BattleHistory({ battle, locale, knowledge }: { readonly battle: Battle | undefined; readonly locale: "es" | "en"; readonly knowledge?: ArtefactKnowledgeReader }) {
  const [section, setSection] = useState<"overview" | "participants" | "notes">("overview");
  const t = ({ battle: translate({ key: "ui.6d671ae2fc33" }, locale), missing: translate({ key: "ui.b00ee19e071c" }, locale), result: translate({ key: "ui.0a91171a8d9f" }, locale), casualties: translate({ key: "ui.9c349387bc0c" }, locale), ooa: translate({ key: "ui.17db87d2b37d" }, locale), participants: translate({ key: "ui.0b53a0179789" }, locale), participated: translate({ key: "ui.3a91bc23dbc6" }, locale), absent: translate({ key: "ui.fe761e3b6394" }, locale), remaining: translate({ key: "ui.a536b12f558d" }, locale), consequences: translate({ key: "ui.42eb1ccc47d7" }, locale), xp: translate({ key: "ui.06e25290fd23" }, locale), gold: translate({ key: "ui.7c1aa61463c4" }, locale), wyrdstone: translate({ key: "ui.e71905bfd3f8" }, locale), advances: translate({ key: "ui.01bf66ea165f" }, locale), models: translate({ key: "ui.8d8af7acc6c8" }, locale), rating: translate({ key: "ui.f60eeb2b86e6" }, locale), objectives: translate({ key: "ui.90f3bdb4a942" }, locale), notes: translate({ key: "ui.28f6d9a82fb0" }, locale), noNotes: translate({ key: "ui.471758f9da8d" }, locale), story: translate({ key: "ui.24ebf16f400c" }, locale), noHighlights: translate({ key: "ui.6bf1f15f118a" }, locale), survived: translate({ key: "ui.f9360b718aa4" }, locale), unknownCasualties: translate({ key: "ui.0134cd64da44" }, locale), xpBreakdown: translate({ key: "ui.b378ee1510e3" }, locale) });
  if (!battle) return <section className="page"><p>{presentationOutput(t.missing)}</p></section>;
  const participants = battle.participants ?? [];
  const ooa = new Set(battle.out_of_action_ids ?? []);
  const casualties = participants.filter((row) => Number(battle.per_group_casualties?.[String(row.id)] ?? (ooa.has(String(row.id)) ? 1 : 0)) > 0);
  const highlights = highlightsFor(battle, locale, knowledge);
  const outcome = localizedLabel(battle.result, locale);
  const resultKey = String(battle.result).toLowerCase();
  const resultTone = resultKey === "win" || resultKey === "victory" ? "victory" : resultKey === "loss" || resultKey === "defeat" ? "defeat" : "draw";
  const casualtySummary = casualties.length ? textJoin(casualties.map((row) => battleParticipantName(battle, row.id, locale)), " · ") : battle.casualties ? t.unknownCasualties : t.survived;
  const xpRows = participants.filter((row) => Number(battle.xp_awards?.[String(row.id)] ?? 0) > 0);
  return <section className="page battle-history" aria-label={presentationOutput(translate({ key: "pdf.battle", args: { number: battle.number } }, locale))}>
    <header className={`battle-hero ${resultTone}`}><div><span>{presentationOutput(textJoin([translate({ key: "pdf.battle", args: { number: battle.number } }, locale), textDate(battle.date, locale)], " · "))}</span><h2>{presentationOutput(knowledgeName(knowledge, "scenario", battle.scenario, locale))}</h2><p>{presentationOutput(translate({ key: "battle.against", args: { opponent: opponentPersonalName(battle, locale) } }, locale))}</p></div><strong>{presentationOutput(outcome)}</strong></header>
    <nav aria-label={presentationOutput(translate({ key: "ui.9e09b7814634" }, locale))} className="segmented-tabs">{(["overview","participants","notes"] as const).map((key)=><button key={key} className={section===key ? "active" : ""} aria-pressed={section===key} onClick={()=>setSection(key)}>{presentationOutput(key === "overview" ? (translate({ key: "ui.8334ecd1c008" }, locale)) : key === "participants" ? t.participants : t.notes)}</button>)}</nav>
    {section === "overview" && <div className="battle-report">
      <section className="battle-story" aria-labelledby="battle-story-title"><span>{presentationOutput(t.story)}</span><h3 id="battle-story-title">{presentationOutput(translate({ key: "battle.outcome", args: { outcome, opponent: opponentPersonalName(battle, locale) } }, locale))}</h3><p>{presentationOutput(battle.opponent_rating ? translate({ key: "battle.deployment-opponent", args: { models: battle.models_before, rating: battle.rating_before, opponent: battle.opponent_rating } }, locale) : translate({ key: "battle.deployment", args: { models: battle.models_before, rating: battle.rating_before } }, locale))}</p></section>
      <dl className="battle-scoreboard"><div><dt>{presentationOutput(t.result)}</dt><dd>{presentationOutput(outcome)}</dd></div><div><dt>{presentationOutput(t.casualties)}</dt><dd>{presentationOutput(textNumber(battle.casualties, locale))}</dd></div><div><dt>{presentationOutput(t.xp)}</dt><dd>{presentationOutput(textJoin([textSymbol("+"), textNumber(battle.xp_delta, locale)], ""))}</dd></div><div><dt>{presentationOutput(t.gold)}</dt><dd className={battle.gold_delta < 0 ? "negative" : ""}>{presentationOutput(textJoin([textSymbol(battle.gold_delta > 0 ? "+" : ""), textNumber(battle.gold_delta, locale)], ""))}</dd></div><div><dt>{presentationOutput(t.wyrdstone)}</dt><dd>{presentationOutput(textJoin([textSymbol("+"), textNumber(battle.wyrdstone, locale)], ""))}</dd></div></dl>
      <div className="battle-report-grid"><article className="battle-report-card"><span>{presentationOutput(t.casualties)}</span><h3>{presentationOutput(casualtySummary)}</h3>{battle.casualties > 0 && casualties.length > 0 && <ul>{casualties.map((row) => { const amount=Number(battle.per_group_casualties?.[String(row.id)] ?? 1); return <li key={String(row.id)}><b>{presentationOutput(battleParticipantName(battle, row.id, locale))}</b><small>{presentationOutput(textJoin([textNumber(amount, locale), t.ooa]))}</small></li>; })}</ul>}</article><article className="battle-report-card"><span>{presentationOutput(t.consequences)}</span><div className="battle-change"><p><small>{presentationOutput(t.rating)}</small><b>{presentationOutput(textNumber(battle.rating_before, locale))}</b><i>{presentationOutput(textSymbol("→"))}</i><b>{presentationOutput(textNumber(battle.rating_after, locale))}</b></p><p><small>{presentationOutput(t.models)}</small><b>{presentationOutput(textNumber(battle.models_before, locale))}</b><i>{presentationOutput(textSymbol("→"))}</i><b>{presentationOutput(textNumber(battle.models_after, locale))}</b></p><p><small>{presentationOutput(t.advances)}</small><b>{presentationOutput(textJoin([textSymbol("+"), textNumber(battle.advances, locale)], ""))}</b></p></div></article></div>
      <article className="battle-report-card battle-highlights"><span>{presentationOutput(t.objectives)}</span>{highlights.length ? <ul>{highlights.map((line, index) => <li key={`${index}:${line}`}>{presentationOutput(line)}</li>)}</ul> : <p>{presentationOutput(t.noHighlights)}</p>}</article>
      {xpRows.length > 0 && <article className="battle-report-card"><span>{presentationOutput(t.xpBreakdown)}</span><ul>{xpRows.map((row) => <li key={String(row.id)}><b>{presentationOutput(battleParticipantName(battle, row.id, locale))}</b><small>{presentationOutput(textJoin([textJoin([textSymbol("+"), textNumber(battle.xp_awards?.[String(row.id)], locale)], ""), translate({ key: "unit.experience" }, locale)]))}</small></li>)}</ul></article>}
    </div>}
    {section === "participants" && <article className="battle-report-card participant-report"><span>{presentationOutput(t.participants)}</span>{participants.map((row) => { const id=String(row.id ?? ""); const amount=Number(battle.per_group_casualties?.[id] ?? (ooa.has(id) ? 1 : 0)); return <div key={id}><b>{presentationOutput(battleParticipantName(battle, row.id, locale))}{presentationOutput(Number(row.quantity ?? 1)>1 ? textJoin([textSymbol("×"), textNumber(row.quantity, locale)]) : textSymbol(""))}</b><small className={amount > 0 ? "danger" : ""}>{presentationOutput(amount>0 ? textJoin([textNumber(amount, locale), t.ooa]) : t.participated)}</small></div>; })}{(battle.absentees ?? []).map((row) => <div className="absent" key={String(row.id)}><b>{presentationOutput(battleParticipantName(battle, row.id, locale))}</b><small>{presentationOutput(textJoin([t.absent, localizedLabel(row.reason, locale), ...(Number(row.remaining_before ?? 0)>0 ? [textJoin([textNumber(row.remaining_before, locale), t.remaining])] : [])], " · "))}</small></div>)}</article>}
    {section === "notes" && <article className="battle-report-card battle-notes"><span>{presentationOutput(t.notes)}</span><p>{presentationOutput(battle.notes ? battlePersonalNotes(battle, locale) : t.noNotes)}</p></article>}
  </section>;
}

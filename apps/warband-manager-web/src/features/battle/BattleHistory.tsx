import { useState } from "react";
import type { CampaignDocument } from "../campaign/types";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { knowledgeName, readableValue } from "../campaign/displayText";

type Battle = CampaignDocument["campaign"]["battles"][number];
type Participant = Readonly<Record<string, unknown>>;
const nameOf = (row: Participant, locale: "es" | "en") => String(row.name ?? readableValue(row.id, locale));

function highlightsFor(battle: Battle, locale: "es" | "en", knowledge?: ArtefactKnowledgeReader): string[] {
  const results = battle.scenario_results ?? {};
  const names = new Map((battle.participants ?? []).map((row) => [String(row.id), nameOf(row, locale)]));
  const lines: string[] = [];
  const enemyOoa = results["enemy_out_of_action_by_warrior"];
  if (enemyOoa && typeof enemyOoa === "object") for (const [id, amount] of Object.entries(enemyOoa)) if (Number(amount)) lines.push(locale === "es" ? `${names.get(id) ?? "Guerrero"} dejó fuera de combate a ${Number(amount)} miniatura(s) enemigas.` : `${names.get(id) ?? "Warrior"} put ${Number(amount)} enemy model(s) Out of Action.`);
  const objectives = results["objectives"];
  if (objectives && typeof objectives === "object") for (const value of Object.values(objectives)) { const row=value as Record<string,unknown>; const recipient=String(row["recipient"]??""); const amount=Number(row["amount"]??0); if(recipient&&amount) lines.push(locale === "es" ? `${names.get(recipient)??recipient} recibió +${amount} EXP por un objetivo.` : `${names.get(recipient)??recipient} received +${amount} XP for an objective.`); const recipients=row["recipients"]; if(recipients&&typeof recipients==="object")for(const [id,award] of Object.entries(recipients))if(Number(award)>0)lines.push(locale === "es"?`${names.get(id)??id} recibió +${Number(award)} EXP por un objetivo.`:`${names.get(id)??id} received +${Number(award)} XP for an objective.`); }
  const rewards = results["additional_rewards"];
  if (Array.isArray(rewards)) for (const value of rewards) { const row=value as Record<string,unknown>; const quantity=Number(row["quantity"]??0); if(row["kind"]==="exploration") lines.push(locale === "es"?"Se obtuvo una ventaja adicional durante la exploración.":"An additional exploration benefit was earned."); else if(row["resource"]==="gold_crowns") lines.push(locale === "es"?`${quantity} co obtenidas como recompensa del escenario.`:`${quantity} gc awarded by the scenario.`); else if(row["resource"]==="wyrdstone_fragments") lines.push(locale === "es"?`${quantity} fragmento(s) de piedra bruja obtenidos como recompensa.`:`${quantity} wyrdstone shard(s) awarded.`); else if(["item","special"].includes(String(row["kind"]))) lines.push(`${quantity} × ${knowledgeName(knowledge, "item", row["item_id"], locale, row["label"] ?? (locale === "es" ? "Objeto" : "Item"))}`); }
  return lines;
}

export function BattleHistory({ battle, locale, knowledge }: { readonly battle: Battle | undefined; readonly locale: "es" | "en"; readonly knowledge?: ArtefactKnowledgeReader }) {
  const [section, setSection] = useState<"overview" | "participants" | "notes">("overview");
  const t = locale === "es" ? { battle:"BATALLA",missing:"No se encontró la batalla.",result:"Resultado",casualties:"Bajas propias",ooa:"fuera de combate",participants:"PARTICIPANTES",participated:"Sin bajas",absent:"No participó",remaining:"batalla(s) pendientes antes de esta batalla",consequences:"BALANCE DE LA BATALLA",xp:"EXP obtenida",gold:"Coronas",wyrdstone:"Piedra bruja",advances:"Avances",models:"Tamaño de banda",rating:"Valoración",objectives:"MOMENTOS DESTACADOS",notes:"NOTAS",noNotes:"No se registraron notas.",story:"CRÓNICA",noHighlights:"No se registraron objetivos ni recompensas especiales.",survived:"La banda salió intacta",unknownCasualties:"No se registró quién sufrió las bajas",xpBreakdown:"EXPERIENCIA POR GUERRERO" } : { battle:"BATTLE",missing:"Battle not found.",result:"Result",casualties:"Own casualties",ooa:"Out of Action",participants:"PARTICIPANTS",participated:"No casualties",absent:"Did not participate",remaining:"game(s) remaining before this battle",consequences:"BATTLE OUTCOME",xp:"XP gained",gold:"Gold crowns",wyrdstone:"Wyrdstone",advances:"Advances",models:"Warband size",rating:"Rating",objectives:"BATTLE HIGHLIGHTS",notes:"NOTES",noNotes:"No notes were recorded.",story:"BATTLE REPORT",noHighlights:"No special objectives or rewards were recorded.",survived:"The warband emerged intact",unknownCasualties:"The casualties were not identified",xpBreakdown:"EXPERIENCE BY WARRIOR" };
  if (!battle) return <section className="page"><p>{t.missing}</p></section>;
  const participants = battle.participants ?? [];
  const ooa = new Set(battle.out_of_action_ids ?? []);
  const casualties = participants.filter((row) => Number(battle.per_group_casualties?.[String(row.id)] ?? (ooa.has(String(row.id)) ? 1 : 0)) > 0);
  const highlights = highlightsFor(battle, locale, knowledge);
  const outcome = readableValue(battle.result, locale);
  const resultKey = String(battle.result).toLowerCase();
  const resultTone = resultKey === "win" || resultKey === "victory" ? "victory" : resultKey === "loss" || resultKey === "defeat" ? "defeat" : "draw";
  const casualtySummary = casualties.length ? casualties.map((row) => nameOf(row, locale)).join(" · ") : battle.casualties ? t.unknownCasualties : t.survived;
  const xpRows = participants.filter((row) => Number(battle.xp_awards?.[String(row.id)] ?? 0) > 0);
  return <section className="page battle-history" aria-label={`${t.battle} #${battle.number}`}>
    <header className={`battle-hero ${resultTone}`}><div><span>{t.battle} #{battle.number} · {battle.date}</span><h2>{knowledgeName(knowledge, "scenario", battle.scenario, locale, battle.scenario)}</h2><p>{locale === "es" ? `Contra ${battle.opponent}` : `Against ${battle.opponent}`}</p></div><strong>{outcome}</strong></header>
    <nav aria-label={locale === "es" ? "Secciones de batalla" : "Battle sections"} className="segmented-tabs">{(["overview","participants","notes"] as const).map((key)=><button key={key} className={section===key ? "active" : ""} aria-pressed={section===key} onClick={()=>setSection(key)}>{key === "overview" ? (locale === "es" ? "RESUMEN" : "OVERVIEW") : key === "participants" ? t.participants : t.notes}</button>)}</nav>
    {section === "overview" && <div className="battle-report">
      <section className="battle-story" aria-labelledby="battle-story-title"><span>{t.story}</span><h3 id="battle-story-title">{locale === "es" ? `${outcome} frente a ${battle.opponent}` : `${outcome} against ${battle.opponent}`}</h3><p>{locale === "es" ? `La banda desplegó ${battle.models_before} miniaturas con valoración ${battle.rating_before}${battle.opponent_rating ? ` frente a una banda de valoración ${battle.opponent_rating}` : ""}.` : `The warband deployed ${battle.models_before} models at rating ${battle.rating_before}${battle.opponent_rating ? ` against a warband rated ${battle.opponent_rating}` : ""}.`}</p></section>
      <dl className="battle-scoreboard"><div><dt>{t.result}</dt><dd>{outcome}</dd></div><div><dt>{t.casualties}</dt><dd>{battle.casualties}</dd></div><div><dt>{t.xp}</dt><dd>+{battle.xp_delta}</dd></div><div><dt>{t.gold}</dt><dd className={battle.gold_delta < 0 ? "negative" : ""}>{battle.gold_delta > 0 ? "+" : ""}{battle.gold_delta}</dd></div><div><dt>{t.wyrdstone}</dt><dd>+{battle.wyrdstone}</dd></div></dl>
      <div className="battle-report-grid"><article className="battle-report-card"><span>{t.casualties}</span><h3>{casualtySummary}</h3>{battle.casualties > 0 && casualties.length > 0 && <ul>{casualties.map((row) => { const amount=Number(battle.per_group_casualties?.[String(row.id)] ?? 1); return <li key={String(row.id)}><b>{nameOf(row, locale)}</b><small>{amount} {t.ooa}</small></li>; })}</ul>}</article><article className="battle-report-card"><span>{t.consequences}</span><div className="battle-change"><p><small>{t.rating}</small><b>{battle.rating_before}</b><i>→</i><b>{battle.rating_after}</b></p><p><small>{t.models}</small><b>{battle.models_before}</b><i>→</i><b>{battle.models_after}</b></p><p><small>{t.advances}</small><b>+{battle.advances}</b></p></div></article></div>
      <article className="battle-report-card battle-highlights"><span>{t.objectives}</span>{highlights.length ? <ul>{highlights.map((line, index) => <li key={`${index}:${line}`}>{line}</li>)}</ul> : <p>{t.noHighlights}</p>}</article>
      {xpRows.length > 0 && <article className="battle-report-card"><span>{t.xpBreakdown}</span><ul>{xpRows.map((row) => <li key={String(row.id)}><b>{nameOf(row, locale)}</b><small>+{battle.xp_awards?.[String(row.id)]} EXP</small></li>)}</ul></article>}
    </div>}
    {section === "participants" && <article className="battle-report-card participant-report"><span>{t.participants}</span>{participants.map((row) => { const id=String(row.id ?? ""); const amount=Number(battle.per_group_casualties?.[id] ?? (ooa.has(id) ? 1 : 0)); return <div key={id}><b>{nameOf(row, locale)}{Number(row.quantity ?? 1)>1?` · ×${Number(row.quantity)}`:""}</b><small className={amount > 0 ? "danger" : ""}>{amount>0?`${amount} ${t.ooa}`:t.participated}</small></div>; })}{(battle.absentees ?? []).map((row) => <div className="absent" key={String(row.id)}><b>{nameOf(row, locale)}</b><small>{t.absent} · {readableValue(row.reason, locale)}{Number(row.remaining_before ?? 0)>0 ? ` · ${Number(row.remaining_before)} ${t.remaining}` : ""}</small></div>)}</article>}
    {section === "notes" && <article className="battle-report-card battle-notes"><span>{t.notes}</span><p>{battle.notes || t.noNotes}</p></article>}
  </section>;
}

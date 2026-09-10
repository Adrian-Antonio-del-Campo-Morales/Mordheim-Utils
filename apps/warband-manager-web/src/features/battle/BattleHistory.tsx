import type { CampaignDocument } from "../campaign/types";

type Battle = CampaignDocument["campaign"]["battles"][number];

function scenarioLines(battle: Battle, locale: "es" | "en"): string[] {
  const results = battle.scenario_results ?? {};
  const names = new Map((battle.participants ?? []).map((row) => [String(row.id), String(row.name ?? row.id)]));
  const lines: string[] = [];
  const enemyOoa = results["enemy_out_of_action_by_warrior"];
  if (enemyOoa && typeof enemyOoa === "object") for (const [id, amount] of Object.entries(enemyOoa)) if (Number(amount)) lines.push(locale === "es" ? `${names.get(id) ?? id} dejó fuera de combate a ${Number(amount)} miniatura(s) enemigas.` : `${names.get(id) ?? id} put ${Number(amount)} enemy model(s) Out of Action.`);
  const objectives = results["objectives"];
  if (objectives && typeof objectives === "object") for (const value of Object.values(objectives)) { const row=value as Record<string,unknown>; const recipient=String(row["recipient"]??""); const amount=Number(row["amount"]??0); if(recipient&&amount) lines.push(locale === "es" ? `${names.get(recipient)??recipient} recibió +${amount} EXP por un objetivo.` : `${names.get(recipient)??recipient} received +${amount} XP for an objective.`); const recipients=row["recipients"]; if(recipients&&typeof recipients==="object")for(const [id,award] of Object.entries(recipients))if(Number(award)>0)lines.push(locale === "es"?`${names.get(id)??id} recibió +${Number(award)} EXP por un objetivo.`:`${names.get(id)??id} received +${Number(award)} XP for an objective.`); }
  const rewards = results["additional_rewards"];
  if (Array.isArray(rewards)) for (const value of rewards) { const row=value as Record<string,unknown>; const quantity=Number(row["quantity"]??0); if(row["kind"]==="exploration") lines.push(locale === "es"?"Se aplicó la regla de exploración del escenario.":"Scenario exploration rule applied."); else if(row["resource"]==="gold_crowns") lines.push(locale === "es"?`${quantity} co obtenidas.`:`${quantity} gc awarded.`); else if(row["resource"]==="wyrdstone_fragments") lines.push(locale === "es"?`${quantity} fragmento(s) de piedra bruja obtenidos.`:`${quantity} wyrdstone shard(s) awarded.`); else if(["item","special"].includes(String(row["kind"]))) lines.push(`${quantity} × ${String(row["label"]??row["item_id"]??row["special_id"]??"")}`); }
  return lines;
}

export function BattleHistory({ battle, locale }: { readonly battle: Battle | undefined; readonly locale: "es" | "en" }) {
  const t = locale === "es" ? { battle:"BATALLA",missing:"No se encontró la batalla.",opponent:"Oponente",opponentRating:"Valoración rival",result:"Resultado",deployed:"Miniaturas desplegadas",casualties:"BAJAS",ooa:"Fuera de combate",participants:"PARTICIPANTES",participated:"Participó",absent:"No participó",consequences:"CONSECUENCIAS REGISTRADAS",xp:"Experiencia",gold:"Oro",wyrdstone:"Piedra bruja",advances:"Avances",models:"Miniaturas",rating:"Valoración",objectives:"OBJETIVOS DEL ESCENARIO",notes:"NOTAS",noNotes:"No se registraron notas." } : { battle:"BATTLE",missing:"Battle not found.",opponent:"Opponent",opponentRating:"Opponent rating",result:"Result",deployed:"Models deployed",casualties:"CASUALTIES",ooa:"Out of Action",participants:"PARTICIPANTS",participated:"Participated",absent:"Did not participate",consequences:"RECORDED CONSEQUENCES",xp:"Experience",gold:"Gold",wyrdstone:"Wyrdstone",advances:"Advances",models:"Models",rating:"Rating",objectives:"SCENARIO OBJECTIVES",notes:"NOTES",noNotes:"No notes were recorded." };
  if (!battle) return <section className="page"><p>{t.missing}</p></section>;
  const ooa = new Set(battle.out_of_action_ids ?? []);
  const objectives = scenarioLines(battle, locale);
  return <section className="page" aria-label={`${t.battle} #${battle.number}`}>
    <div className="page-title"><p>{t.battle} #{battle.number}</p><h2>{battle.scenario}</h2><span>{battle.date} · {t.opponent}: {battle.opponent}</span></div>
    <dl className="campaign-metrics"><div><dt>{t.result}</dt><dd>{battle.result}</dd></div><div><dt>{t.rating}</dt><dd>{battle.rating_before}</dd></div><div><dt>{t.opponentRating}</dt><dd>{battle.opponent_rating ?? "—"}</dd></div><div><dt>{t.deployed}</dt><dd>{battle.models_before}</dd></div></dl>
    <article className="rule-detail"><h3>{t.casualties}</h3><p>{battle.casualties} {t.ooa}</p></article>
    <article className="rule-detail"><h3>{t.participants}</h3>{(battle.participants ?? []).map((participant) => { const id=String(participant.id ?? ""); const amount=Number(battle.per_group_casualties?.[id] ?? (ooa.has(id) ? 1 : 0)); return <p key={id}>{String(participant.name ?? id)}{Number(participant.quantity ?? 1)>1?` · ×${Number(participant.quantity)}`:""} — {amount>0?`${amount} ${t.ooa}`:t.participated}</p>; })}{(battle.absentees ?? []).map((participant) => <p className="condition" key={String(participant.id)}>{String(participant.name ?? participant.id)} — {t.absent} · {String(participant.reason ?? "")}</p>)}</article>
    <article className="rule-detail"><h3>{t.consequences}</h3><ul><li>{t.xp}: +{battle.xp_delta}</li><li>{t.gold}: {battle.gold_delta} gc</li><li>{t.wyrdstone}: {battle.wyrdstone}</li><li>{t.advances}: {battle.advances}</li><li>{t.models}: {battle.models_before} → {battle.models_after}</li><li>{t.rating}: {battle.rating_before} → {battle.rating_after}</li></ul></article>
    {battle.scenario_results && <article className="rule-detail"><h3>{t.objectives}</h3>{objectives.length > 0 ? <ul>{objectives.map((line, index) => <li key={`${index}:${line}`}>{line}</li>)}</ul> : <p>—</p>}</article>}
    <article className="rule-detail"><h3>{t.notes}</h3><p>{battle.notes || t.noNotes}</p></article>
  </section>;
}

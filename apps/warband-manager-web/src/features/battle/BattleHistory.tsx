import type { CampaignDocument } from "../campaign/types";

type Battle = CampaignDocument["campaign"]["battles"][number];

export function BattleHistory({ battle, locale }: { readonly battle: Battle | undefined; readonly locale: "es" | "en" }) {
  const t = locale === "es" ? { battle:"BATALLA",missing:"No se encontró la batalla.",opponent:"Oponente",opponentRating:"Valoración rival",result:"Resultado",deployed:"Miniaturas desplegadas",casualties:"BAJAS",ooa:"Fuera de combate",participants:"PARTICIPANTES",participated:"Participó",absent:"No participó",consequences:"CONSECUENCIAS REGISTRADAS",xp:"Experiencia",gold:"Oro",wyrdstone:"Piedra bruja",advances:"Avances",models:"Miniaturas",rating:"Valoración",objectives:"OBJETIVOS DEL ESCENARIO",notes:"NOTAS",noNotes:"No se registraron notas." } : { battle:"BATTLE",missing:"Battle not found.",opponent:"Opponent",opponentRating:"Opponent rating",result:"Result",deployed:"Models deployed",casualties:"CASUALTIES",ooa:"Out of Action",participants:"PARTICIPANTS",participated:"Participated",absent:"Did not participate",consequences:"RECORDED CONSEQUENCES",xp:"Experience",gold:"Gold",wyrdstone:"Wyrdstone",advances:"Advances",models:"Models",rating:"Rating",objectives:"SCENARIO OBJECTIVES",notes:"NOTES",noNotes:"No notes were recorded." };
  if (!battle) return <section className="page"><p>{t.missing}</p></section>;
  const ooa = new Set(battle.out_of_action_ids ?? []);
  return <section className="page" aria-label={`${t.battle} #${battle.number}`}>
    <div className="page-title"><p>{t.battle} #{battle.number}</p><h2>{battle.scenario}</h2><span>{battle.date} · {t.opponent}: {battle.opponent}</span></div>
    <dl className="campaign-metrics"><div><dt>{t.result}</dt><dd>{battle.result}</dd></div><div><dt>{t.rating}</dt><dd>{battle.rating_before}</dd></div><div><dt>{t.opponentRating}</dt><dd>{battle.opponent_rating ?? "—"}</dd></div><div><dt>{t.deployed}</dt><dd>{battle.models_before}</dd></div></dl>
    <article className="rule-detail"><h3>{t.casualties}</h3><p>{battle.casualties} {t.ooa}</p></article>
    <article className="rule-detail"><h3>{t.participants}</h3>{(battle.participants ?? []).map((participant) => { const id=String(participant.id ?? ""); const amount=Number(battle.per_group_casualties?.[id] ?? 0); return <p key={id}>{String(participant.name ?? id)}{Number(participant.quantity ?? 1)>1?` · ×${Number(participant.quantity)}`:""} — {ooa.has(id)||amount>0?t.ooa:t.participated}</p>; })}{(battle.absentees ?? []).map((participant) => <p className="condition" key={String(participant.id)}>{String(participant.name ?? participant.id)} — {t.absent} · {String(participant.reason ?? "")}</p>)}</article>
    <article className="rule-detail"><h3>{t.consequences}</h3><ul><li>{t.xp}: +{battle.xp_delta}</li><li>{t.gold}: {battle.gold_delta} gc</li><li>{t.wyrdstone}: {battle.wyrdstone}</li><li>{t.advances}: {battle.advances}</li><li>{t.models}: {battle.models_before} → {battle.models_after}</li><li>{t.rating}: {battle.rating_before} → {battle.rating_after}</li></ul></article>
    {battle.scenario_results && <article className="rule-detail"><h3>{t.objectives}</h3><pre>{JSON.stringify(battle.scenario_results, null, 2)}</pre></article>}
    <article className="rule-detail"><h3>{t.notes}</h3><p>{battle.notes || t.noNotes}</p></article>
  </section>;
}

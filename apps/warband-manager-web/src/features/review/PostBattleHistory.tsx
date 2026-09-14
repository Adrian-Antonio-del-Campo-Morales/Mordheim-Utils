import type { CampaignDocument } from "../campaign/types";
import { localizedLabel } from "../campaign/displayText";

type Event = Readonly<Record<string, unknown>>;

export function PostBattleHistory({ document, battleNumber, locale }: { readonly document: CampaignDocument; readonly battleNumber: number; readonly locale: "es" | "en" }) {
  const post = document.campaign.post_battles.find((row) => row.battle_number === battleNumber);
  const t = locale === "es" ? {
    title:"POSTBATALLA", missing:"No se encontró el postbatalla.", complete:"Secuencia completada", story:"RESULTADO DE LA SECUENCIA", summary:"La banda resolvió las consecuencias de la batalla y quedó preparada para el siguiente encuentro.", steps:"Acciones resueltas", gold:"Balance de coronas", wyrdstone:"Balance de piedra bruja", sold:"Fragmentos vendidos", veterans:"Reserva de veteranos", events:"LO QUE OCURRIÓ", empty:"Este paso se completó sin cambios registrados.", noEvents:"La secuencia terminó sin eventos adicionales registrados."
  } : {
    title:"POST-BATTLE", missing:"Post-battle not found.", complete:"Sequence complete", story:"SEQUENCE OUTCOME", summary:"The warband resolved the battle's consequences and is ready for its next encounter.", steps:"Actions resolved", gold:"Gold balance", wyrdstone:"Wyrdstone balance", sold:"Shards sold", veterans:"Veteran pool", events:"WHAT HAPPENED", empty:"This step completed with no recorded changes.", noEvents:"The sequence ended with no additional events recorded."
  };
  if (!post) return <section className="page"><p>{t.missing}</p></section>;
  const labels = locale === "es"
    ? ["Heridas y recuperación", "Experiencia y avances", "Exploración", "Venta de piedra bruja", "Veteranos disponibles", "Búsquedas y hallazgos", "Reclutamiento", "Equipo y comercio"]
    : ["Injuries and recovery", "Experience and advances", "Exploration", "Wyrdstone sale", "Available veterans", "Searches and finds", "Recruitment", "Equipment and trading"];
  const events = (post.event_log ?? []) as readonly Event[];
  const eventsByStep = labels.map((_, step) => events.filter((event) => Number(event.step) === step));
  const unassigned = events.filter((event) => !Number.isInteger(Number(event.step)) || Number(event.step) < 0 || Number(event.step) > 7);
  const completed = new Set(post.completed_steps);
  const signed = (value: number, suffix = "") => `${value > 0 ? "+" : ""}${value}${suffix}`;
  const eventText = (event: Event) => String(event.description ?? event.message ?? localizedLabel(event.type ?? "event", locale));
  return <section className="page post-battle-history" aria-label={`${t.title} #${battleNumber}`}>
    <header className="post-battle-hero"><div><span>{t.title} #{battleNumber}</span><h2>{t.complete}</h2><p>{t.summary}</p></div><strong>8/8</strong></header>
    <dl className="post-battle-scoreboard"><div><dt>{t.steps}</dt><dd>{post.completed_steps.length}/8</dd></div><div><dt>{t.gold}</dt><dd className={(post.gold_delta ?? 0) < 0 ? "negative" : ""}>{signed(post.gold_delta ?? 0, " gc")}</dd></div><div><dt>{t.wyrdstone}</dt><dd className={(post.wyrdstone_delta ?? 0) < 0 ? "negative" : ""}>{signed(post.wyrdstone_delta ?? 0)}</dd></div>{post.wyrdstone_sold !== undefined && <div><dt>{t.sold}</dt><dd>{post.wyrdstone_sold}</dd></div>}{post.veteran_pool !== undefined && <div><dt>{t.veterans}</dt><dd>{post.veteran_pool} EXP</dd></div>}</dl>
    <section className="post-battle-ledger" aria-labelledby="post-battle-events"><span>{t.story}</span><h3 id="post-battle-events">{t.events}</h3>
      {events.length === 0 && <p className="post-battle-empty">{t.noEvents}</p>}
      <ol>{labels.map((label, step) => <li className={completed.has(step) ? "complete" : ""} key={label}><div className="post-battle-step-marker"><b>{step + 1}</b><span>{completed.has(step) ? "✓" : "—"}</span></div><article><h4>{label}</h4>{eventsByStep[step].length ? <ul>{eventsByStep[step].map((event, index) => <li key={`${index}:${String(event.type)}`}><small>{localizedLabel(event.type ?? "event", locale)}</small><p>{eventText(event)}</p></li>)}</ul> : <p>{t.empty}</p>}</article></li>)}</ol>
      {unassigned.length > 0 && <article className="post-battle-other"><h4>{locale === "es" ? "Otros cambios" : "Other changes"}</h4>{unassigned.map((event, index) => <p key={index}>{eventText(event)}</p>)}</article>}
    </section>
  </section>;
}

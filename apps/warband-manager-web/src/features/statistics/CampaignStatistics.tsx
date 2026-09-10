import type { CampaignDocument } from "../campaign/types";

export function CampaignStatistics({ document, locale }: { readonly document: CampaignDocument; readonly locale: "es" | "en" }) {
  const campaign = document.campaign;
  const committed = campaign.battles.filter((battle) => battle.number <= campaign.current_state_number);
  const current = campaign.states.find((state) => state.number === campaign.current_state_number) ?? campaign.states.at(-1);
  const victories = committed.filter((battle) => ["win", "victory"].includes(battle.result.toLowerCase())).length;
  const labels = locale === "es"
    ? { eyebrow: "CAMPAÑA", title: "Estadísticas de campaña", help: "Los agregados resumen la campaña; la cronología conserva el detalle de qué ocurrió y cuándo.", battles: "Batallas", victories: "Victorias", rating: "Valoración actual", models: "Miniaturas actuales", progression: "PROGRESIÓN DE VALORACIÓN", empty: "Todavía no hay estados confirmados." }
    : { eyebrow: "CAMPAIGN", title: "Campaign statistics", help: "Aggregates summarize the campaign; the timeline preserves what happened and when.", battles: "Battles", victories: "Victories", rating: "Current rating", models: "Current models", progression: "RATING PROGRESSION", empty: "No committed states yet." };
  return <section className="page" aria-label={labels.title}>
    <div className="page-title"><p>{labels.eyebrow}</p><h1>{labels.title}</h1><span>{labels.help}</span></div>
    <dl className="campaign-metrics"><div><dt>{labels.battles}</dt><dd>{committed.length}</dd></div><div><dt>{labels.victories}</dt><dd>{victories}</dd></div><div><dt>{labels.rating}</dt><dd>{current?.rating ?? 0}</dd></div><div><dt>{labels.models}</dt><dd>{current?.models ?? 0}</dd></div></dl>
    <article className="rule-detail"><h2>{labels.progression}</h2>{campaign.states.length === 0 ? <p>{labels.empty}</p> : <ol className="rating-progression">{campaign.states.map((state) => <li key={state.number}><small>#{state.number}</small><strong>{state.rating}</strong></li>)}</ol>}</article>
  </section>;
}

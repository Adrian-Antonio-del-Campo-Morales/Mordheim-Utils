import { textSymbol } from "../campaign/presentation-values";
import { textNumber } from "../campaign/presentation-values";
import { presentationOutput } from "../campaign/presentation-output";
import { translate } from "../campaign/i18n-core";
import type { CampaignDocument } from "../campaign/types";

export function CampaignStatistics({ document, locale }: { readonly document: CampaignDocument; readonly locale: "es" | "en" }) {
  const campaign = document.campaign;
  const committed = campaign.battles.filter((battle) => battle.number <= campaign.current_state_number);
  const current = campaign.states.find((state) => state.number === campaign.current_state_number) ?? campaign.states.at(-1);
  const victories = committed.filter((battle) => ["win", "victory"].includes(battle.result.toLowerCase())).length;
  const labels = ({ eyebrow: translate({ key: "ui.4102263a44ea" }, locale), title: translate({ key: "ui.16c1b47d0156" }, locale), help: translate({ key: "ui.ec3b681a8911" }, locale), battles: translate({ key: "ui.6052147241f3" }, locale), victories: translate({ key: "ui.f154c82f6f6b" }, locale), rating: translate({ key: "ui.2ab2f3e6da00" }, locale), models: translate({ key: "ui.291fffed10d0" }, locale), progression: translate({ key: "ui.48bdd749975f" }, locale), empty: translate({ key: "ui.48d573441e9f" }, locale) });
  return <section className="page" aria-label={presentationOutput(labels.title)}>
    <div className="page-title"><p>{presentationOutput(labels.eyebrow)}</p><h1>{presentationOutput(labels.title)}</h1><span>{presentationOutput(labels.help)}</span></div>
    <dl className="campaign-metrics"><div><dt>{presentationOutput(labels.battles)}</dt><dd>{presentationOutput(textNumber(committed.length, locale))}</dd></div><div><dt>{presentationOutput(labels.victories)}</dt><dd>{presentationOutput(textNumber(victories, locale))}</dd></div><div><dt>{presentationOutput(labels.rating)}</dt><dd>{presentationOutput(textNumber(current?.rating ?? 0, locale))}</dd></div><div><dt>{presentationOutput(labels.models)}</dt><dd>{presentationOutput(textNumber(current?.models ?? 0, locale))}</dd></div></dl>
    <article className="rule-detail"><h2>{presentationOutput(labels.progression)}</h2>{campaign.states.length === 0 ? <p>{presentationOutput(labels.empty)}</p> : <ol className="rating-progression">{campaign.states.map((state) => <li key={state.number}><small> {presentationOutput(textSymbol("#"))} {presentationOutput(textNumber(state.number, locale))}</small><strong>{presentationOutput(textNumber(state.rating, locale))}</strong></li>)}</ol>}</article>
  </section>;
}

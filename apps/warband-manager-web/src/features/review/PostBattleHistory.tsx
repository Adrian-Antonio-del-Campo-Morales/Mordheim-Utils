import { presentationOutput } from "../campaign/presentation-output";
import { textJoin, textNumber, textSymbol, type PresentationValue } from "../campaign/presentation-values";
import { historyEventText, historyStepLabels } from "./history-presentation";
import type { CampaignDocument } from "../campaign/types";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { localizedLabel } from "../campaign/displayText";
import { translate } from "../campaign/i18n-core";

type Event = Readonly<Record<string, unknown>>;

export function PostBattleHistory({ document, battleNumber, locale, knowledge }: { readonly document: CampaignDocument; readonly battleNumber: number; readonly locale: "es" | "en"; readonly knowledge?: ArtefactKnowledgeReader }) {
  const post = document.campaign.post_battles.find((row) => row.battle_number === battleNumber);
  const t = ({ title: translate({ key: "ui.14293491f9ff" }, locale), missing: translate({ key: "ui.c58b97f91898" }, locale), complete: translate({ key: "ui.9a1540872e1e" }, locale), story: translate({ key: "ui.4cd8f897e903" }, locale), summary: translate({ key: "ui.7cc14a6d2a54" }, locale), steps: translate({ key: "ui.6421ce8b8f42" }, locale), gold: translate({ key: "ui.b86b8fcd1fb1" }, locale), wyrdstone: translate({ key: "ui.d1e40f3aec12" }, locale), sold: translate({ key: "ui.6b99698a094f" }, locale), veterans: translate({ key: "ui.cf8a4f1b23fc" }, locale), events: translate({ key: "ui.acdb2be6aea0" }, locale), empty: translate({ key: "ui.8da7a5de58a8" }, locale), noEvents: translate({ key: "ui.924b96b3f826" }, locale) });
  if (!post) return <section className="page"><p>{presentationOutput(t.missing)}</p></section>;
  const labels = historyStepLabels(locale);
  const events = (post.event_log ?? []) as readonly Event[];
  const eventsByStep = labels.map((_, step) => events.filter((event) => Number(event.step) === step));
  const unassigned = events.filter((event) => !Number.isInteger(Number(event.step)) || Number(event.step) < 0 || Number(event.step) > 7);
  const completed = new Set(post.completed_steps);
  const signed = (value: number, suffix?: PresentationValue) => textJoin([textSymbol(value > 0 ? "+" : ""), textNumber(value, locale), ...(suffix ? [suffix] : [])], "");
  const eventText = (event: Event) => historyEventText(event, document, locale, knowledge);
  const title = textJoin([t.title, textJoin([textSymbol("#"), textNumber(battleNumber, locale)], "")]);
  return <section className="page post-battle-history" aria-label={presentationOutput(title)}>
    <header className="post-battle-hero"><div><span>{presentationOutput(title)}</span><h2>{presentationOutput(t.complete)}</h2><p>{presentationOutput(t.summary)}</p></div><strong>{presentationOutput(textJoin([textNumber(8, locale), textSymbol("/"), textNumber(8, locale)], ""))}</strong></header>
    <dl className="post-battle-scoreboard"><div><dt>{presentationOutput(t.steps)}</dt><dd>{presentationOutput(textJoin([textNumber(post.completed_steps.length, locale), textSymbol("/"), textNumber(8, locale)], ""))}</dd></div><div><dt>{presentationOutput(t.gold)}</dt><dd className={(post.gold_delta ?? 0) < 0 ? "negative" : ""}>{presentationOutput(signed(post.gold_delta ?? 0, translate({ key: "ui.cb8fa67082cb" }, locale)))}</dd></div><div><dt>{presentationOutput(t.wyrdstone)}</dt><dd className={(post.wyrdstone_delta ?? 0) < 0 ? "negative" : ""}>{presentationOutput(signed(post.wyrdstone_delta ?? 0))}</dd></div>{post.wyrdstone_sold !== undefined && <div><dt>{presentationOutput(t.sold)}</dt><dd>{presentationOutput(textNumber(post.wyrdstone_sold, locale))}</dd></div>}{post.veteran_pool !== undefined && <div><dt>{presentationOutput(t.veterans)}</dt><dd>{presentationOutput(textJoin([textNumber(post.veteran_pool, locale), translate({ key: "ui.06e25290fd23" }, locale)]))}</dd></div>}</dl>
    <section className="post-battle-ledger" aria-labelledby="post-battle-events"><span>{presentationOutput(t.story)}</span><h3 id="post-battle-events">{presentationOutput(t.events)}</h3>
      {events.length === 0 && <p className="post-battle-empty">{presentationOutput(t.noEvents)}</p>}
      <ol>{labels.map((label, step) => <li className={completed.has(step) ? "complete" : ""} key={label}><div className="post-battle-step-marker"><b>{presentationOutput(textNumber(step + 1, locale))}</b><span>{presentationOutput(textSymbol(completed.has(step) ? "✓" : "—"))}</span></div><article><h4>{presentationOutput(label)}</h4>{eventsByStep[step].length ? <ul>{eventsByStep[step].map((event, index) => <li key={`${index}:${String(event.type)}`}><small>{presentationOutput(localizedLabel(event.type ?? "event", locale))}</small><p>{presentationOutput(eventText(event))}</p></li>)}</ul> : <p>{presentationOutput(t.empty)}</p>}</article></li>)}</ol>
      {unassigned.length > 0 && <article className="post-battle-other"><h4>{presentationOutput(translate({ key: "ui.6a0a7a7f6fb5" }, locale))}</h4>{unassigned.map((event, index) => <p key={index}>{presentationOutput(eventText(event))}</p>)}</article>}
    </section>
  </section>;
}

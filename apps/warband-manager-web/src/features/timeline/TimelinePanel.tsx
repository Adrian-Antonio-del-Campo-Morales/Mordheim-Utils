import { presentationOutput } from "../campaign/presentation-output";
import { textJoin, textNumber, textSymbol, opponentPersonalName } from "../campaign/presentation-values";
import { translate } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
/**
 * Campaign timeline navigation UI.
 *
 * Enumerates the document's moments (draft, committed states, battles,
 * pending post-battles) in timeline order, highlights the selected moment,
 * and navigates through the application service's `selectMoment` — which
 * never mutates the campaign and never dirties the document.
 *
 * Pure view over the CampaignAppView seam; no direct service calls, no
 * domain imports beyond display types. Helpers live in `./moments.ts` so
 * this file only exports components (react-refresh).
 */
import type { CampaignDocument, MomentSelection } from "../campaign/types";
import { enumerateMoments, momentLabel } from "./moments";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { knowledgeName } from "../campaign/displayText";

interface TimelinePanelProps {
  readonly document: CampaignDocument;
  readonly onSelect: (moment: MomentSelection) => void;
  readonly locale?: "es" | "en";
  readonly knowledge?: ArtefactKnowledgeReader;
}

export function TimelinePanel({ document, onSelect, locale: requestedLocale, knowledge }: TimelinePanelProps) {
  const locale = useLocale(requestedLocale);
  const { campaign, view } = document;
  const moments = enumerateMoments(campaign);
  const selected = (view.selected_moment ?? "draft:0") as string;
  const selectedMoment = moments.find((moment) => moment === selected) ?? moments[0];
  const completed = Math.max(0, campaign.states.length - (campaign.configuration.is_draft ? 0 : 1));

  return (
    <nav aria-label={presentationOutput(translate({ key: "ui.d77ec83a8d1d" }, locale))} className="campaign-timeline">
      <header><h3>{presentationOutput(translate({ key: "ui.5402e494dc86" }, locale))}</h3><p>{presentationOutput(campaign.configuration.is_draft ? (translate({ key: "ui.19d4ed8b537c" }, locale)) : translate({ key: "timeline.completed", args: { count: completed } }, locale))}</p></header>
      <label className="mobile-timeline-picker"><span>{presentationOutput(translate({ key: "ui.4507edf1d4e1" }, locale))}</span><select aria-label={presentationOutput(translate({ key: "ui.b51e84524689" }, locale))} value={selectedMoment} onChange={(event) => onSelect(event.target.value as MomentSelection)}>{moments.map((moment) => <option key={moment} value={moment}>{presentationOutput(momentLabel(moment, campaign, locale, knowledgeName(knowledge, "scenario", campaign.battles.find((battle) => `battle:${battle.number}` === moment)?.scenario, locale)))}</option>)}</select></label>
      <ol>
        {moments.map((moment) => {
          const isCurrent = moment === selected;
          const [kind, rawNumber] = moment.split(":");
          const number = Number(rawNumber);
          const state = kind === "state" ? campaign.states.find((row) => row.number === number) : undefined;
          const battle = kind === "battle" ? campaign.battles.find((row) => row.number === number) : undefined;
          const post = kind === "post" ? campaign.post_battles.find((row) => row.battle_number === number) : undefined;
          const scenarioName = battle ? knowledgeName(knowledge, "scenario", battle.scenario, locale) : undefined;
          const detail = state ? textJoin([translate({ key: "ui.f60eeb2b86e6" }, locale), textNumber(state.rating, locale), textJoin([textNumber(state.models, locale), textSymbol("/"), textNumber(state.max_models, locale)], ""), translate({ key: "ui.e9882ce840bb" }, locale)])
            : battle ? textJoin([scenarioName ?? translate({ key: "knowledge.unavailable" }, locale), textSymbol("vs."), opponentPersonalName(battle, locale)])
            : post && !post.complete ? textJoin([translate({ key: "ui.b3b55860db42" }, locale), textJoin([textNumber(post.active_step + 1, locale), textSymbol("/"), textNumber(8, locale)], "")])
            : kind === "new-battle" ? translate({ key: "ui.1defb9c60306" }, locale) : undefined;
          return (
            <li key={moment} data-kind={kind}>
              <button
                type="button"
                aria-current={isCurrent ? "true" : undefined}
                style={isCurrent ? { fontWeight: "bold" } : undefined}
                onClick={() => onSelect(moment)}
              >
                <span>{presentationOutput(momentLabel(moment, campaign, locale, scenarioName))}</span>{detail && <small>{presentationOutput(detail)}</small>}{kind === "new-battle" && <b className="timeline-action">{presentationOutput(translate({ key: "ui.1daf9ad17eec" }, locale))}</b>}
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

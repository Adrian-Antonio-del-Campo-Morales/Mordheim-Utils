/**
 * Web migration timeline surface: timeline navigation UI.
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

interface TimelinePanelProps {
  readonly document: CampaignDocument;
  readonly onSelect: (moment: MomentSelection) => void;
  readonly locale?: "es" | "en";
}

export function TimelinePanel({ document, onSelect, locale = "en" }: TimelinePanelProps) {
  const { campaign, view } = document;
  const moments = enumerateMoments(campaign);
  const selected = (view.selected_moment ?? "draft:0") as string;
  const completed = Math.max(0, campaign.states.length - 1);

  return (
    <nav aria-label="Timeline" className="campaign-timeline">
      <header><h3>{locale === "es" ? "CRONOLOGÍA DE CAMPAÑA" : "CAMPAIGN TIMELINE"}</h3><p>{campaign.configuration.is_draft ? (locale === "es" ? "La campaña todavía no ha comenzado" : "Campaign has not started yet") : locale === "es" ? `${completed} estados de batalla completados` : `${completed} completed battle states`}</p></header>
      <ol>
        {moments.map((moment) => {
          const isCurrent = moment === selected;
          const [kind, rawNumber] = moment.split(":");
          const number = Number(rawNumber);
          const state = kind === "state" ? campaign.states.find((row) => row.number === number) : undefined;
          const battle = kind === "battle" ? campaign.battles.find((row) => row.number === number) : undefined;
          const post = kind === "post" ? campaign.post_battles.find((row) => row.battle_number === number) : undefined;
          const detail = state ? `${locale === "es" ? "Valoración" : "Rating"} ${state.rating} · ${state.models}/${state.max_models} ${locale === "es" ? "miniaturas" : "models"}` : battle ? `${battle.scenario} vs. ${battle.opponent}` : post && !post.complete ? `${locale === "es" ? "Paso" : "Step"} ${post.active_step + 1}/8` : "";
          return (
            <li key={moment} data-kind={kind}>
              <button
                type="button"
                aria-current={isCurrent ? "true" : undefined}
                style={isCurrent ? { fontWeight: "bold" } : undefined}
                onClick={() => onSelect(moment)}
              >
                <span>{momentLabel(moment, campaign, locale)}</span>{detail && <small>{detail}</small>}
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

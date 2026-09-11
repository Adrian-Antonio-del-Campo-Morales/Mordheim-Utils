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

  return (
    <nav aria-label="Timeline">
      <h3>{locale === "es" ? "Cronología" : "Timeline"}</h3>
      <ol>
        {moments.map((moment) => {
          const isCurrent = moment === selected;
          return (
            <li key={moment}>
              <button
                type="button"
                aria-current={isCurrent ? "true" : undefined}
                style={isCurrent ? { fontWeight: "bold" } : undefined}
                onClick={() => onSelect(moment)}
              >
                {momentLabel(moment, campaign, locale)}
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

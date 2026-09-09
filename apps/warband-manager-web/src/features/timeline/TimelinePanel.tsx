/**
 * P6.1 (web-migration-parallel-plan.md §P6.1): timeline navigation UI.
 *
 * Enumerates the document's moments (draft, committed states, battles,
 * pending post-battles) in timeline order, highlights the selected moment,
 * and navigates through the application service's `selectMoment` — which
 * never mutates the campaign and never dirties the document.
 *
 * Pure view over the CampaignAppView seam; no direct service calls, no
 * domain imports beyond display types.
 */
import type { CampaignDocument, MomentSelection } from "../campaign/types";

/** The plan's moment enumeration, in timeline order. */
export function enumerateMoments(campaign: CampaignDocument["campaign"]): MomentSelection[] {
  const moments: MomentSelection[] = ["draft:0"];
  for (const state of campaign.states) {
    moments.push(`state:${state.number}` as MomentSelection);
  }
  for (const battle of campaign.battles) {
    moments.push(`battle:${battle.number}` as MomentSelection);
  }
  for (const post of campaign.post_battles) {
    if (!post.complete) {
      moments.push(`post:${post.battle_number}` as MomentSelection);
    }
  }
  return moments;
}

export function momentLabel(moment: MomentSelection, campaign: CampaignDocument["campaign"]): string {
  const [kind, raw] = moment.split(":");
  const number = Number(raw);
  if (kind === "draft") return "Draft";
  if (kind === "state") {
    const state = campaign.states.find((s) => s.number === number);
    return `State #${number}${state?.date ? ` — ${state.date}` : ""}`;
  }
  if (kind === "battle") {
    const battle = campaign.battles.find((b) => b.number === number);
    return `Battle #${number}${battle ? ` — ${battle.scenario}` : ""}`;
  }
  return `Post-battle #${number} (pending)`;
}

interface TimelinePanelProps {
  readonly document: CampaignDocument;
  readonly onSelect: (moment: MomentSelection) => void;
}

export function TimelinePanel({ document, onSelect }: TimelinePanelProps) {
  const { campaign, view } = document;
  const moments = enumerateMoments(campaign);
  const selected = (view.selected_moment ?? "draft:0") as string;

  return (
    <nav aria-label="Timeline">
      <h3>Timeline</h3>
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
                {momentLabel(moment, campaign)}
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

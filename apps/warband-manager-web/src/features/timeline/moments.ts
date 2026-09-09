/**
 * P6.1 timeline moment helpers — pure functions over the campaign document,
 * kept out of the component file so fast refresh can work on the tsx.
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

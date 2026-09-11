/**
 * P6.1 timeline moment helpers — pure functions over the campaign document,
 * kept out of the component file so fast refresh can work on the tsx.
 */
import type { CampaignDocument, MomentSelection } from "../campaign/types";

/** The plan's moment enumeration, in timeline order. */
export function enumerateMoments(campaign: CampaignDocument["campaign"]): MomentSelection[] {
  if (campaign.configuration.is_draft) return ["draft:0"];
  const moments: MomentSelection[] = ["draft:0"];
  for (const state of [...campaign.states].sort((left, right) => left.number - right.number)) {
    moments.push(`state:${state.number}` as MomentSelection);
  }
  for (const battle of [...campaign.battles].sort((left, right) => left.number - right.number)) {
    moments.push(`battle:${battle.number}` as MomentSelection);
    const post = campaign.post_battles.find((row) => row.battle_number === battle.number);
    if (post) moments.push(`post:${post.battle_number}` as MomentSelection);
  }
  return moments;
}

export function momentLabel(moment: MomentSelection, campaign: CampaignDocument["campaign"], locale: "es" | "en" = "en"): string {
  const [kind, raw] = moment.split(":");
  const number = Number(raw);
  if (kind === "draft") return locale === "es" ? "Banda inicial · borrador" : "Initial warband · draft";
  if (kind === "state") {
    const state = campaign.states.find((s) => s.number === number);
    const title = number === 0 ? locale === "es" ? "Estado inicial" : "Initial state" : `${locale === "es" ? "Estado" : "State"} #${number}`;
    return `${title}${state?.date ? ` — ${state.date}` : ""}`;
  }
  if (kind === "battle") {
    const battle = campaign.battles.find((b) => b.number === number);
    return `${locale === "es" ? "Batalla" : "Battle"} #${number}${battle ? ` — ${battle.scenario}` : ""}`;
  }
  const post = campaign.post_battles.find((row) => row.battle_number === number);
  const status = post?.complete ? locale === "es" ? "completo" : "complete" : locale === "es" ? "en curso" : "in progress";
  return `${locale === "es" ? "Post-batalla" : "Post-battle"} #${number} (${status})`;
}

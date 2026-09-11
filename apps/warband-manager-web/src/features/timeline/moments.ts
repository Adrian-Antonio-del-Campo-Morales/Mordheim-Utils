/**
 * Web migration timeline moment helpers — kept separate from the component so
 * the timeline remains a pure projection of the campaign document.
 */
import type { CampaignDocument, MomentSelection } from "../campaign/types";

/**
 * Mirrors the desktop order: initial state, then Battle → Post-Battle → the
 * resulting state for every completed transition, followed by the next battle
 * entry when no transition is pending.
 */
export function enumerateMoments(campaign: CampaignDocument["campaign"]): MomentSelection[] {
  if (campaign.configuration.is_draft) return ["draft:0"];

  const moments: MomentSelection[] = [];
  const states = [...campaign.states].sort((left, right) => left.number - right.number);
  const battles = [...campaign.battles].sort((left, right) => left.number - right.number);
  const initial = states.find((state) => state.number === 0);
  if (!initial) {
    return ["draft:0", ...states.map((state) => `state:${state.number}` as MomentSelection), ...battles.map((battle) => `battle:${battle.number}` as MomentSelection)];
  }
  moments.push("state:0");

  for (const battle of battles) {
    moments.push(`battle:${battle.number}` as MomentSelection);
    const post = campaign.post_battles.find((row) => row.battle_number === battle.number);
    if (post) moments.push(`post:${post.battle_number}` as MomentSelection);
    if (post?.complete && states.some((state) => state.number === battle.number)) {
      moments.push(`state:${battle.number}` as MomentSelection);
    }
  }

  if (!campaign.post_battles.some((post) => !post.complete)) {
    moments.push(`new-battle:${Math.max(...battles.map((battle) => battle.number), 0) + 1}` as MomentSelection);
  }
  return moments;
}

export function momentLabel(moment: MomentSelection, campaign: CampaignDocument["campaign"], locale: "es" | "en" = "en", scenarioName?: string): string {
  const [kind, raw] = moment.split(":");
  const number = Number(raw);
  if (kind === "draft") return locale === "es" ? "Banda inicial · borrador" : "Initial warband · draft";
  if (kind === "new-battle") return locale === "es" ? `Batalla #${number} · en curso` : `Battle #${number} · in progress`;
  if (kind === "state") {
    const state = campaign.states.find((item) => item.number === number);
    const title = number === 0 ? locale === "es" ? "Estado inicial" : "Initial state" : `${locale === "es" ? "Estado" : "State"} #${number}`;
    return `${title}${state?.date ? ` — ${state.date}` : ""}`;
  }
  if (kind === "battle") {
    const battle = campaign.battles.find((item) => item.number === number);
    return `${locale === "es" ? "Batalla" : "Battle"} #${number}${battle ? ` — ${scenarioName ?? battle.scenario}` : ""}`;
  }
  const post = campaign.post_battles.find((row) => row.battle_number === number);
  const status = post?.complete ? locale === "es" ? "completo" : "complete" : locale === "es" ? "en curso" : "in progress";
  return `${locale === "es" ? "Post-batalla" : "Post-battle"} #${number} (${status})`;
}

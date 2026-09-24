import { textJoin, textNumber, textSymbol, textDate, type PresentationValue } from "../campaign/presentation-values";
import type { ResolvedKbText } from "@adapters/knowledge-reader/presentation";
import { translate } from "../campaign/i18n-core";
/**
 * Campaign timeline moment helpers — kept separate from the component so
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

export function momentLabel(moment: MomentSelection, campaign: CampaignDocument["campaign"], locale: "es" | "en", scenarioName?: ResolvedKbText): PresentationValue {
  const [kind, raw] = moment.split(":");
  const number = Number(raw);
  const numbered = textJoin([textSymbol("#"), textNumber(number, locale)], "");
  if (kind === "draft") return translate({ key: "ui.c0b9b18d14e6" }, locale);
  if (kind === "new-battle") return translate({ key: "timeline.new-battle", args: { number } }, locale);
  if (kind === "state") {
    const state = campaign.states.find((item) => item.number === number);
    const title = number === 0 ? translate({ key: "ui.34ec26f0a73c" }, locale) : textJoin([translate({ key: "ui.edfcc40a3b5d" }, locale), numbered]);
    return state?.date ? textJoin([title, textSymbol("—"), textDate(state.date, locale)]) : title;
  }
  if (kind === "battle") {
    const battle = campaign.battles.find((item) => item.number === number);
    const title = textJoin([translate({ key: "ui.8731a48db4a4" }, locale), numbered]);
    return battle ? textJoin([title, textSymbol("—"), scenarioName ?? translate({ key: "ui.eab86554d72e" }, locale)]) : title;
  }
  const post = campaign.post_battles.find((row) => row.battle_number === number);
  const status = post?.complete ? translate({ key: "ui.bfe16a390bab" }, locale) : translate({ key: "ui.4f5ab93e035b" }, locale);
  return textJoin([translate({ key: "ui.6d07c6511d84" }, locale), numbered, textJoin([textSymbol("("), status, textSymbol(")")], "")]);
}

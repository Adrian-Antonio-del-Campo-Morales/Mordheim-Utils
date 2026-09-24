import { textJoin, textNumber } from "../campaign/presentation-values";
import { presentationOutput } from "../campaign/presentation-output";
import { translate } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
import { useEffect, useRef } from "react";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { AdvancesPanel } from "./AdvancesPanel";

export function PostBattleExperience({ document, knowledge, locale: requestedLocale }: { readonly document: CampaignDocument; readonly knowledge: ArtefactKnowledgeReader; readonly locale?: "es" | "en" }) {
  const locale = useLocale(requestedLocale);
  const app = useCampaignApp();
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const battle = post && document.campaign.battles.find((row) => row.number === post.battle_number);
  const startedForBattle = useRef<number | null>(null);
  const injuryCounts = new Map<string, number>();
  const resolvedInjuries = (post?.step_state?.["injuries"] ?? {}) as Record<string, unknown>;
  const unresolvedInjuries = (battle?.out_of_action_ids ?? []).filter((warriorId) => {
    const casualtyIndex = (injuryCounts.get(warriorId) ?? 0) + 1;
    injuryCounts.set(warriorId, casualtyIndex);
    const warrior = document.campaign.warriors.find((row) => row.id === warriorId);
    const recorded = Boolean(resolvedInjuries[`${warriorId}:${casualtyIndex}`]) || (warrior?.injury_records ?? []).some((row) => Number(row["battle_number"]) === post?.battle_number && Number(row["casualty_index"] ?? 1) === casualtyIndex);
    const followUp = (post?.pending_follow_ups ?? []).some((row) => row["warrior_id"] === warriorId && Number(row["casualty_index"] ?? 1) === casualtyIndex && (row["step"] === "injuries" || String(row["step"] ?? "") === "0"));
    return !recorded || followUp;
  }).length;

  useEffect(() => {
    if (!post || post.experience_applied || unresolvedInjuries > 0 || startedForBattle.current === post.battle_number) return;
    startedForBattle.current = post.battle_number;
    void app.runAction("applyBattleExperience", {});
  }, [app, post, unresolvedInjuries]);

  if (!post) return null;
  const title = translate({ key: "ui.64536a40f6e1" }, locale);
  if (unresolvedInjuries > 0) return <section aria-label={presentationOutput(title)}><h3>{presentationOutput(textJoin([textNumber(2, locale, 2), title], " · "))}</h3><p role="status">{presentationOutput(translate({ key: "injury.remaining", args: { count: unresolvedInjuries } }, locale))}</p></section>;
  if (!post.experience_applied) return <section aria-label={presentationOutput(title)}><h3>{presentationOutput(textJoin([textNumber(2, locale, 2), title], " · "))}</h3><p role="status">{presentationOutput(translate({ key: "ui.a8adbaa1f2a5" }, locale))}</p></section>;
  return <section aria-label={presentationOutput(title)}><h3>{presentationOutput(textJoin([textNumber(2, locale, 2), title], " · "))}</h3><AdvancesPanel document={document} knowledge={knowledge} locale={locale} /></section>;
}

import { useEffect, useRef } from "react";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { AdvancesPanel } from "./AdvancesPanel";

export function PostBattleExperience({ document, knowledge, locale="en" }: { readonly document: CampaignDocument; readonly knowledge: ArtefactKnowledgeReader; readonly locale?: "es" | "en" }) {
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
  const title = locale === "es" ? "Experiencia y avances" : "Experience and advances";
  if (unresolvedInjuries > 0) return <section aria-label={title}><h3>02 · {title}</h3><p role="status">{locale === "es" ? `Resuelve primero todas las heridas graves (${unresolvedInjuries} pendientes).` : `Resolve all serious injuries first (${unresolvedInjuries} remaining).`}</p></section>;
  if (!post.experience_applied) return <section aria-label={title}><h3>02 · {title}</h3><p role="status">{locale === "es" ? "Aplicando automáticamente la experiencia de batalla…" : "Applying battle experience automatically…"}</p></section>;
  return <section aria-label={title}><h3>02 · {title}</h3><AdvancesPanel document={document} knowledge={knowledge} locale={locale} /></section>;
}

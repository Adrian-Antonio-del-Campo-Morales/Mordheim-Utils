import type { CampaignDocument } from "../campaign/types";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { translate, type Locale } from "../campaign/i18n-core";
import { knowledgeName, warriorAbilityRef } from "../campaign/displayText";
import { localizedLabel } from "../campaign/presentation-enums";
import { textJoin, textNumber, textDate, textSymbol, campaignPersonalName, warbandPersonalName, warriorPersonalName, opponentPersonalName, battlePersonalNotes, manualCorrectionReason, type PresentationValue } from "../campaign/presentation-values";
import { historyEventText } from "./history-presentation";

function header(document: CampaignDocument, locale: Locale, knowledge?: ArtefactKnowledgeReader): PresentationValue[] {
  const campaign = document.campaign;
  return [
    textJoin([translate({ key: "ui.13624dd6f3e9" }, locale), campaignPersonalName(campaign, locale)]),
    textJoin([translate({ key: "ui.e64208a1bf43" }, locale), warbandPersonalName(campaign, locale), knowledgeName(knowledge, "band", campaign.identity.band_id, locale)]),
    textJoin([translate({ key: "ui.37b55afd1403" }, locale), textNumber(campaign.current_state_number, locale)]),
  ];
}

export function localizedLedger(document: CampaignDocument, locale: Locale, knowledge?: ArtefactKnowledgeReader): PresentationValue {
  const rows = header(document, locale, knowledge);
  for (const battle of document.campaign.battles) {
    rows.push(textJoin([translate({ key: "pdf.battle", args: { number: battle.number } }, locale), textDate(battle.date, locale), knowledgeName(knowledge, "scenario", battle.scenario, locale), textSymbol("vs."), opponentPersonalName(battle, locale), localizedLabel(battle.result, locale)], " · "));
    rows.push(textJoin([localizedLabel("gold_crowns", locale), textNumber(battle.gold_delta, locale), localizedLabel("experience", locale), textNumber(battle.xp_delta, locale)], " · "));
    if (battle.notes) rows.push(battlePersonalNotes(battle, locale));
  }
  for (const post of document.campaign.post_battles) {
    rows.push(textJoin([translate({ key: "ui.14293491f9ff" }, locale), textNumber(post.battle_number, locale)]));
    for (const event of post.event_log ?? []) rows.push(historyEventText(event, document, locale, knowledge));
  }
  for (const entry of document.campaign.manual_log) {
    const detail = entry.type === "manual_resource_correction"
      ? textJoin([localizedLabel(entry.resource, locale), textNumber(entry.delta, locale), manualCorrectionReason(entry, locale)])
      : entry.type === "manual_item_correction"
        ? textJoin([knowledgeName(knowledge, "item", entry.item_id, locale), textNumber(entry.quantity, locale), manualCorrectionReason(entry, locale)])
        : translate({ key: "knowledge.unavailable" }, locale);
    rows.push(detail);
  }
  return textJoin(rows, "\n");
}

export function localizedRoster(document: CampaignDocument, locale: Locale, knowledge?: ArtefactKnowledgeReader): PresentationValue {
  const rows = header(document, locale, knowledge);
  for (const warrior of document.campaign.warriors) {
    rows.push(textJoin([
      warriorPersonalName(warrior, locale),
      knowledgeName(knowledge, warrior.kind === "hireling" ? "hireling" : "profile", warrior.profile_id, locale),
      localizedLabel(warrior.kind, locale),
      textJoin([translate({ key: "ui.06e25290fd23" }, locale), textNumber(warrior.experience, locale)]),
      textJoin([translate({ key: "ui.8d8af7acc6c8" }, locale), textNumber(warrior.quantity ?? 1, locale)]),
    ], " · "));
    if (warrior.condition) rows.push(localizedLabel(warrior.condition, locale));
    if ((warrior.games_to_miss ?? 0) > 0) rows.push(textJoin([translate({ key: "ui.fe761e3b6394" }, locale), textNumber(warrior.games_to_miss, locale), localizedLabel(warrior.absence_reason, locale)]));
    for (const item of warrior.equipment) rows.push(textJoin([textNumber(item.quantity, locale), knowledgeName(knowledge, "item", item.item_id, locale)]));
    for (const id of warrior.skills) {
      const ref = warriorAbilityRef(knowledge, id, warrior.profile_id, document.campaign.identity.band_id);
      const value = knowledge?.resolveKbText(ref, "name", locale);
      rows.push(value?.ok ? value.text : translate({ key: "knowledge.unavailable" }, locale));
    }
  }
  return textJoin(rows, "\n");
}

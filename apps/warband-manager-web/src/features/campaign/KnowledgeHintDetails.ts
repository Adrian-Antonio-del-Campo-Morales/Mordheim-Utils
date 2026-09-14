import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { adaptDistanceText } from "@app/rules/distance-display";

import { displayText, knowledgeDescription, knowledgeText } from "./displayText";
import type { Locale } from "./i18n-core";

export type KnowledgeHintInput = { knowledge?: ArtefactKnowledgeReader; kind: "item" | "skill" | "rule" | "injury"; id: string; profileId?: string; bandId?: string; locale: Locale };

/** Shared non-React tooltip contract; exhaustive KB checks use this exact path. */
export function knowledgeHintDetails({ knowledge, kind, id, profileId, bandId, locale }: KnowledgeHintInput): { readonly name: string; readonly tooltip: string } {
  const indexed = knowledgeDescription(knowledge, { kind, id, ...(profileId ? { profileId } : {}), ...(bandId ? { bandId } : {}) }, locale);
  return {
    name: displayText(knowledgeText(knowledge, kind, id, locale, undefined, profileId, bandId), locale),
    tooltip: adaptDistanceText(indexed.text, locale, id),
  };
}

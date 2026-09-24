import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { adaptDistanceText } from "@app/rules/distance-display";

import { knowledgeName, knowledgeDescription } from "./displayText";
import type { ResolvedKbText } from "@adapters/knowledge-reader/presentation";
import type { Locale } from "./i18n-core";
import type { PresentationText } from "./presentation-output";

export type KnowledgeHintInput = { knowledge?: Partial<Pick<ArtefactKnowledgeReader, "resolveKbText">>; kind: "item" | "skill" | "rule" | "injury"; id: string; profileId?: string; bandId?: string; locale: Locale };

/** Shared non-React tooltip contract; exhaustive KB checks use this exact path. */
export function knowledgeHintDetails({ knowledge, kind, id, profileId, bandId, locale }: KnowledgeHintInput): { readonly name: ResolvedKbText; readonly tooltip: PresentationText } {
  const ref = { kind, id, ...(profileId ? { profileId } : {}), ...(bandId ? { bandId } : {}) };
  const description = knowledgeDescription(knowledge, ref, locale);
  const tooltip = description.status === "translated" ? adaptDistanceText(description.text, locale, id) : description.text;
  return {
    name: knowledgeName(knowledge, kind, id, locale, profileId, bandId),
    tooltip,
  };
}

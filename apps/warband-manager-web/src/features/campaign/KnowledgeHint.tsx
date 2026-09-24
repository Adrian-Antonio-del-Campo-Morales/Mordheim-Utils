import { useId, type ReactNode } from "react";
import { knowledgeHintDetails, type KnowledgeHintInput } from "./KnowledgeHintDetails";
import { translate } from "./i18n-core";
import { presentationOutput } from "./presentation-output";

export function KnowledgeHint({ knowledge, kind, id, profileId, bandId, locale, quantity, compact = false, children: _children }: KnowledgeHintInput & { quantity?: number; compact?: boolean; children?: ReactNode }) {
  void _children;
  const hintId = useId();
  const { name, tooltip } = knowledgeHintDetails({ knowledge, kind, id, ...(profileId ? { profileId } : {}), ...(bandId ? { bandId } : {}), locale });
  const label = compact ? translate({ key: "knowledge.info-symbol" }, locale) : quantity === undefined ? name : translate({ key: "knowledge.quantity", args: { name, quantity } }, locale);
  return <><button type="button" className="knowledge-hint" data-tooltip={presentationOutput(tooltip)} popoverTarget={hintId} aria-describedby={hintId} aria-label={presentationOutput(name)}>{presentationOutput(label)}</button><span id={hintId} popover="auto" className="knowledge-popover" role="dialog" aria-label={presentationOutput(translate({ key: "knowledge.description-title", args: { name } }, locale))}><button type="button" className="knowledge-popover-close" popoverTarget={hintId} popoverTargetAction="hide">{presentationOutput(translate({ key: "action.close" }, locale))}</button><span className="knowledge-popover-text">{presentationOutput(tooltip)}</span></span></>;
}

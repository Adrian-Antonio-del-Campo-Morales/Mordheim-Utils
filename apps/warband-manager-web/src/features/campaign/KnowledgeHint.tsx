import { useId, type ReactNode } from "react";
import { knowledgeHintDetails, type KnowledgeHintInput } from "./KnowledgeHintDetails";

export function KnowledgeHint({ knowledge, kind, id, profileId, bandId, locale, children }: KnowledgeHintInput & { children: ReactNode }) {
  const hintId = useId();
  const { name, tooltip } = knowledgeHintDetails({ knowledge, kind, id, ...(profileId ? { profileId } : {}), ...(bandId ? { bandId } : {}), locale });
  return <><button type="button" className="knowledge-hint" data-tooltip={tooltip} popoverTarget={hintId} aria-describedby={hintId} aria-label={name}>{children}</button><span id={hintId} popover="auto" className="knowledge-popover" role="dialog" aria-label={locale === "es" ? `Descripción: ${name}` : `Description: ${name}`}><button type="button" className="knowledge-popover-close" popoverTarget={hintId} popoverTargetAction="hide">{locale === "es" ? "Cerrar" : "Close"}</button><span className="knowledge-popover-text">{tooltip}</span></span></>;
}

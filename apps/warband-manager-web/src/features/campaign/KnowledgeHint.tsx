import type { ReactNode } from "react";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { adaptDistanceText } from "@app/rules/distance-display";

export function KnowledgeHint({ knowledge, kind, id, locale, children }: { knowledge?: ArtefactKnowledgeReader; kind: "item" | "skill" | "rule"; id: string; locale: "es" | "en"; children: ReactNode }) {
  const rows = kind === "rule"
    ? ["special-rules", "core-combat", "conditions", "resolution"].flatMap((section) => knowledge?.rulesDocument(section) ?? [])
    : (typeof knowledge?.list === "function" ? knowledge.list(kind) : []);
  const row = rows.find((entry) => String(entry.id ?? entry.item_id ?? "") === id);
  const localizedEffects = row?.effect_i18n && typeof row.effect_i18n === "object" ? row.effect_i18n as Record<string, unknown> : null;
  const translated = localizedEffects?.[locale] ?? (row?.effects && typeof row.effects === "object" ? (row.effects as Record<string, unknown>)[locale] : undefined);
  const description = typeof translated === "string" ? translated : [row?.effect, row?.description, row?.text, row?.note].find((value) => typeof value === "string");
  const fallback = locale === "es" ? "No hay una descripción disponible para este elemento." : "No description is available for this entry.";
  const recordId = String(row?.id ?? row?.item_id ?? id);
  const tooltip = typeof description === "string"
    ? adaptDistanceText(description, locale, recordId)
    : fallback;
  return <span className="knowledge-hint" tabIndex={0} data-tooltip={tooltip}>{children}</span>;
}

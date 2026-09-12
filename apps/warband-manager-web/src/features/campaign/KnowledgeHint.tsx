import type { ReactNode } from "react";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { adaptDistanceText } from "@app/rules/distance-display";

export function KnowledgeHint({ knowledge, kind, id, profileId, locale, children }: { knowledge?: ArtefactKnowledgeReader; kind: "item" | "skill" | "rule" | "injury"; id: string; profileId?: string; locale: "es" | "en"; children: ReactNode }) {
  const rows = kind === "rule"
    ? ["special-rules", "profile-special-rules", "core-combat", "conditions", "resolution", "localized-labels"].flatMap((section) => knowledge?.rulesDocument(section) ?? [])
    : (typeof knowledge?.list === "function" ? knowledge.list(kind) : []);
  const matches = rows.filter((entry) => {
    if (String(entry.id ?? entry.item_id ?? "") === id) return true;
    const names = entry.names as Readonly<Record<string, unknown>> | undefined;
    return [entry.name, names?.en].some((name) => typeof name === "string" && name.localeCompare(id, "en", { sensitivity: "accent" }) === 0);
  });
  const row = matches.find((entry) => {
    const appliesTo = entry.applies_to as Readonly<Record<string, unknown>> | undefined;
    return profileId && Array.isArray(appliesTo?.profile_ids) && appliesTo.profile_ids.includes(profileId);
  }) ?? matches.find((entry) => entry.effect || entry.description || entry.text || entry.note) ?? matches[0];
  const localizedEffects = row?.effect_i18n && typeof row.effect_i18n === "object" ? row.effect_i18n as Record<string, unknown> : null;
  const localizedNotes = row?.note_i18n && typeof row.note_i18n === "object" ? row.note_i18n as Record<string, unknown> : null;
  const translated = localizedEffects?.[locale] ?? localizedNotes?.[locale] ?? (row?.effects && !Array.isArray(row.effects) && typeof row.effects === "object" ? (row.effects as Record<string, unknown>)[locale] : undefined);
  const description = typeof translated === "string" ? translated : [row?.effect, row?.description, row?.text, row?.note].find((value) => typeof value === "string");
  const fallback = locale === "es" ? "No hay una descripción disponible para este elemento." : "No description is available for this entry.";
  const recordId = String(row?.id ?? row?.item_id ?? id);
  const tooltip = typeof description === "string"
    ? adaptDistanceText(description, locale, recordId)
    : fallback;
  return <span className="knowledge-hint" tabIndex={0} data-tooltip={tooltip}>{children}</span>;
}

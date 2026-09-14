import type { CampaignDocument } from "./kernel/state";
import type { KnowledgeReader } from "./kernel/ports";

export interface WarbandVariant {
  readonly id: string;
  readonly names: Readonly<Record<string, string>>;
  readonly rule_ids: readonly string[];
  readonly starting_gold?: number;
  readonly profile_bonuses?: Readonly<Record<string, Readonly<Record<string, number>>>>;
}

export function warbandVariants(reader: KnowledgeReader, bandId: string): readonly WarbandVariant[] {
  if (typeof reader.queryKnowledge !== "function") return [];
  const result = reader.queryKnowledge({ id: { kind: "band_id", value: bandId } });
  if (!result.ok || !Array.isArray(result.record.data["variants"])) return [];
  return (result.record.data["variants"] as readonly unknown[]).flatMap((value) => {
    if (!value || typeof value !== "object") return [];
    const row = value as Readonly<Record<string, unknown>>;
    if (typeof row["id"] !== "string" || !row["id"]) return [];
    return [{
      id: row["id"],
      names: row["names"] && typeof row["names"] === "object" ? row["names"] as Readonly<Record<string, string>> : { en: row["id"] },
      rule_ids: Array.isArray(row["rule_ids"]) ? row["rule_ids"].map(String) : [],
      ...(typeof row["starting_gold"] === "number" ? { starting_gold: row["starting_gold"] } : {}),
      ...(row["profile_bonuses"] && typeof row["profile_bonuses"] === "object" ? { profile_bonuses: row["profile_bonuses"] as NonNullable<WarbandVariant["profile_bonuses"]> } : {}),
    }];
  });
}

export function selectedWarbandVariant(reader: KnowledgeReader, bandId: string, variantId: string | null | undefined): WarbandVariant | null {
  const id = String(variantId ?? "").trim().toLowerCase();
  return warbandVariants(reader, bandId).find((variant) => variant.id === id) ?? null;
}

export function activeBandRuleIds(reader: KnowledgeReader, document: CampaignDocument): readonly string[] {
  const identity = document.campaign.identity;
  const bandId = identity?.band_id;
  if (!bandId) return [];
  const result = typeof reader.queryKnowledge === "function"
    ? reader.queryKnowledge({ id: { kind: "band_id", value: bandId } })
    : { ok: false as const };
  const common = result.ok && Array.isArray(result.record.data["rule_ids"]) ? result.record.data["rule_ids"].map(String) : [];
  const selected = selectedWarbandVariant(reader, bandId, identity.mercenary_variant);
  return [...new Set([...common, ...(selected?.rule_ids ?? [])])];
}

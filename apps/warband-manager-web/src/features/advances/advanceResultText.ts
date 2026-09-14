import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

import { displayText, knowledgeName, knowledgeRows, localizedLabel } from "../campaign/displayText";

type Locale = "es" | "en";

function skill(knowledge: ArtefactKnowledgeReader, raw: string): Readonly<Record<string, unknown>> | undefined {
  return knowledgeRows(knowledge, "skill").find((entry) => {
    const names = entry["names"] as Record<string, unknown> | undefined;
    return entry["name"] === raw || names?.en === raw;
  });
}

function localizedSkillName(knowledge: ArtefactKnowledgeReader, raw: string, locale: Locale): string {
  const row = skill(knowledge, raw);
  return row ? knowledgeName(knowledge, "skill", row["id"], locale, raw) : raw;
}

export type AdvanceResultDetails = { readonly text: string; readonly skillId?: string };

/** Present legacy English advance outcomes in the active UI language. */
export function advanceResultText(value: unknown, knowledge: ArtefactKnowledgeReader, locale: Locale): string {
  const raw = String(value ?? "").trim();
  if (!raw || locale === "en") return raw;
  const stat = raw.match(/^\+(\d+)\s+(.+)$/);
  if (stat) return `+${stat[1]} ${localizedLabel(stat[2], locale)}`;
  const skill = raw.match(/^Skill:\s+(.+)$/);
  if (skill) return `Habilidad: ${localizedSkillName(knowledge, skill[1], locale)}`;
  const spell = raw.match(/^Spell:\s+(.+)$/);
  if (spell) return `Hechizo: ${localizedSkillName(knowledge, spell[1], locale)}`;
  const duplicate = raw.match(/^Duplicated spell:\s+(.+)\s+\(difficulty -1\)$/);
  if (duplicate) return `Hechizo duplicado: ${localizedSkillName(knowledge, duplicate[1], locale)} (dificultad −1)`;
  if (raw === "Resolved outside the application") return "Resuelto fuera de la aplicación";
  const rejected = raw.match(/^Result rejected:\s+(.+) is at its advance cap \((\d+)\)\.$/);
  if (rejected) return `Resultado rechazado: ${localizedLabel(rejected[1], locale)} ha alcanzado su límite de avance (${rejected[2]}).`;
  const rerollHenchmen = raw.match(/^Rolled (\d+): the remaining Henchmen must reroll results 10-12\.$/);
  if (rerollHenchmen) return `Se obtuvo ${rerollHenchmen[1]}: los secuaces restantes deben repetir los resultados 10-12.`;
  const heroMaximum = raw.match(/^Hero maximum reached \((\d+)\); reroll this advance\.$/);
  if (heroMaximum) return `Se ha alcanzado el máximo de héroes (${heroMaximum[1]}); repite este avance.`;
  if (raw === "Rolled 10-12: one member became a Hero; remaining group rerolls.") return "Se obtuvo 10-12: un miembro se convirtió en héroe; el grupo restante repite la tirada.";
  return displayText({ text: raw, sourceLocale: "en", status: "canonical-fallback" }, locale);
}

/** The visible result plus a KB reference when the outcome is a skill or spell. */
export function advanceResultDetails(value: unknown, knowledge: ArtefactKnowledgeReader, locale: Locale): AdvanceResultDetails {
  const raw = String(value ?? "").trim();
  const match = raw.match(/^(?:Skill|Spell):\s+(.+)$/) ?? raw.match(/^Duplicated spell:\s+(.+)\s+\(difficulty -1\)$/);
  const row = match ? skill(knowledge, match[1]) : undefined;
  return { text: advanceResultText(raw, knowledge, locale), ...(row && typeof row["id"] === "string" ? { skillId: row["id"] } : {}) };
}

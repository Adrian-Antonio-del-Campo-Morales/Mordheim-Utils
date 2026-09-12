import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { Warrior } from "./types";
import { knowledgeName, resourceAmount, warriorName } from "./displayText";
import { KnowledgeHint } from "./KnowledgeHint";
import { ExperienceTrack } from "../draft/DraftWorkspace";
import { adaptCharacteristicValue } from "@app/rules/distance-display";

export function WarriorCard({ warrior, knowledge, locale }: { warrior: Warrior; knowledge?: ArtefactKnowledgeReader; locale: "es" | "en" }) {
  const displayName = warriorName(knowledge, warrior, locale);
  const rules = [...new Map((warrior.skills ?? []).map((id) => {
    const kind = id.startsWith("skill.") ? "skill" : "rule";
    return [knowledgeName(knowledge, kind, id, locale, id), { id, kind, label: knowledgeName(knowledge, kind, id, locale, id) }] as const;
  })).values()];
  return <article className="draft-warrior-card">
    <div className="draft-card-body">
      <section className="draft-card-identity"><header><div><strong>{displayName}</strong><span>{knowledgeName(knowledge, "profile", warrior.profile_id, locale, warrior.profile_name)}</span></div><span className="draft-card-cost"><b>{warrior.kind === "hireling" ? `${locale === "es" ? "Contratación" : "Hiring fee"}: ` : ""}{warrior.quantity ?? 1} × {warrior.cost} gc</b>{warrior.kind === "hireling" && <small>{locale === "es" ? "Mantenimiento" : "Upkeep"}: {warrior.upkeep_resources?.length ? warrior.upkeep_resources.map(([resource, amount]) => resourceAmount(resource, amount, locale)).join(" + ") : "—"}</small>}</span></header><div className="stats">{Object.entries(warrior.stats).map(([key, value]) => <span key={key}><small>{key}</small>{adaptCharacteristicValue(key, value, locale, warrior.stat_modifiers?.[key] ?? 0)}</span>)}</div></section>
      <section className="draft-card-box"><h4>{locale === "es" ? "EQUIPAMIENTO" : "EQUIPMENT"}</h4>{warrior.equipment.map((entry) => <p key={entry.item_id}><KnowledgeHint knowledge={knowledge} kind="item" id={entry.item_id} locale={locale}>{entry.quantity}× {knowledgeName(knowledge, "item", entry.item_id, locale, entry.name)}</KnowledgeHint></p>)}{warrior.equipment.length === 0 && <p>—</p>}</section>
      <section className="draft-card-box"><h4>{locale === "es" ? "HABILIDADES / REGLAS" : "SKILLS / RULES"}</h4>{rules.map((entry) => <p key={entry.id}><KnowledgeHint knowledge={knowledge} kind={entry.kind} id={entry.id} profileId={warrior.profile_id} locale={locale}>{entry.label}</KnowledgeHint></p>)}{rules.length === 0 && <p>—</p>}</section>
    </div>
    <footer><div className="skill-access"><small>{locale === "es" ? "ACCESO A HABILIDADES" : "SKILL ACCESS"}</small><span>{(warrior.skill_access ?? []).join(" · ") || "—"}</span></div><ExperienceTrack experience={warrior.experience} kind={warrior.kind} locale={locale}/></footer>
  </article>;
}

import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { Warrior } from "./types";
import { knowledgeName, localizedLabel, resourceAmount, warriorAbilities, warriorName } from "./displayText";
import { KnowledgeHint } from "./KnowledgeHint";
import { ExperienceTrack } from "../draft/DraftWorkspace";
import { adaptCharacteristicValue } from "@app/rules/distance-display";

export function WarriorCard({ warrior, knowledge, locale, bandId }: { warrior: Warrior; knowledge?: ArtefactKnowledgeReader; locale: "es" | "en"; bandId?: string }) {
  const displayName = warriorName(knowledge, warrior, locale);
  const rules = [...new Map(warriorAbilities(knowledge, warrior).map((id) => {
    const kind = id.startsWith("skill.") ? "skill" : "rule";
    return [knowledgeName(knowledge, kind, id, locale, id, warrior.profile_id, bandId), { id, kind, label: knowledgeName(knowledge, kind, id, locale, id, warrior.profile_id, bandId) }] as const;
  })).values()];
  return <article className="draft-warrior-card">
    <div className="draft-card-body">
      <section className="draft-card-identity"><header><div><strong>{displayName}</strong><span>{knowledgeName(knowledge, "profile", warrior.profile_id, locale, warrior.profile_name)}</span></div><span className="draft-card-cost"><b>{warrior.kind === "hireling" ? `${locale === "es" ? "Contratación" : "Hiring fee"}: ` : ""}{warrior.quantity ?? 1} × {warrior.cost} gc</b>{warrior.kind === "hireling" && <small>{locale === "es" ? "Mantenimiento" : "Upkeep"}: {warrior.upkeep_resources?.length ? warrior.upkeep_resources.map(([resource, amount]) => resourceAmount(resource, amount, locale)).join(" + ") : "—"}</small>}</span></header><div className="stats">{Object.entries(warrior.stats).map(([key, value]) => <span key={key}><small>{localizedLabel(key, locale)}</small>{adaptCharacteristicValue(key, value, locale, warrior.stat_modifiers?.[key] ?? 0)}</span>)}</div></section>
      <section className="draft-card-box"><h4>{locale === "es" ? "EQUIPAMIENTO" : "EQUIPMENT"}</h4>{warrior.equipment.map((entry) => <p key={entry.item_id}><KnowledgeHint knowledge={knowledge} kind="item" id={entry.item_id} locale={locale}>{entry.quantity}× {knowledgeName(knowledge, "item", entry.item_id, locale, entry.name)}</KnowledgeHint></p>)}{warrior.equipment.length === 0 && <p>—</p>}</section>
      <section className="draft-card-box"><h4>{locale === "es" ? "HABILIDADES / REGLAS" : "SKILLS / RULES"}</h4>{rules.map((entry) => <p key={entry.id}><KnowledgeHint knowledge={knowledge} kind={entry.kind} id={entry.id} profileId={warrior.profile_id} bandId={bandId} locale={locale}>{entry.label}</KnowledgeHint></p>)}{rules.length === 0 && <p>—</p>}</section>
      {(warrior.games_to_miss ?? 0) > 0 && <section className="draft-card-box"><h4>{locale === "es" ? "AUSENCIA" : "ABSENCE"}</h4><p>{locale === "es" ? `${warrior.absence_reason || "Lesión"} · se pierde ${warrior.games_to_miss} batalla(s) más` : `${warrior.absence_reason || "Injury"} · misses ${warrior.games_to_miss} more game(s)`}</p></section>}
    </div>
    <footer><div className="skill-access"><small>{locale === "es" ? "ACCESO A HABILIDADES" : "SKILL ACCESS"}</small><span>{(warrior.skill_access ?? []).map((key) => localizedLabel(key, locale)).join(" · ") || "—"}</span></div><ExperienceTrack experience={warrior.experience} kind={warrior.kind} locale={locale}/></footer>
  </article>;
}

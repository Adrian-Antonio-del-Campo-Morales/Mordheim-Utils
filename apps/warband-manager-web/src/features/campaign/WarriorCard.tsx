import { presentationOutput } from "./presentation-output";
import { textJoin, textNumber, textSymbol, warriorPersonalName, warriorCharacteristic } from "./presentation-values";
import { translate } from "./i18n-core";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { Warrior } from "./types";
import { knowledgeName, localizedLabel, readableValue, resourceAmount, warriorAbilities, warriorAbilityRef } from "./displayText";
import { KnowledgeHint } from "./KnowledgeHint";
import { ExperienceTrack } from "../draft/DraftWorkspace";

export function WarriorCard({ warrior, knowledge, locale, bandId }: { warrior: Warrior; knowledge?: ArtefactKnowledgeReader; locale: "es" | "en"; bandId?: string }) {
  const displayName = warriorPersonalName(warrior, locale);
  const profileKind = warrior.kind === "hireling" ? "hireling" : "profile";
  const rules = [...new Map(warriorAbilities(knowledge, warrior).map((id) => {
    const ref = warriorAbilityRef(knowledge, id, warrior.profile_id, bandId);
    const label = knowledgeName(knowledge, ref.kind, ref.id, locale, ref.profileId, ref.bandId);
    return [label, { ...ref, kind: ref.kind === "skill" ? "skill" as const : "rule" as const, label }] as const;
  })).values()];
  return <article className="draft-warrior-card">
    <div className="draft-card-body">
      <section className="draft-card-identity"><header><div><strong>{presentationOutput(displayName)}</strong><span>{presentationOutput(knowledgeName(knowledge, profileKind, warrior.profile_id, locale))}</span></div><span className="draft-card-cost"><b>{presentationOutput(warrior.kind === "hireling" ? textJoin([translate({ key: "ui.38a17e3eb9cc" }, locale), textSymbol(":")], "") : textSymbol(""))}{presentationOutput(textNumber(warrior.quantity ?? 1, locale))}  {presentationOutput(textSymbol("×"))} {presentationOutput(textJoin([textNumber(warrior.cost, locale), translate({ key: "unit.gold" }, locale)]))}</b>{warrior.kind === "hireling" && <small>{presentationOutput(translate({ key: "ui.15e8bb635504" }, locale))} {presentationOutput(textSymbol(":"))} {presentationOutput(warrior.upkeep_resources?.length ? textJoin(warrior.upkeep_resources.map(([resource, amount]) => resourceAmount(resource, amount, locale)), " + ") : textSymbol("—"))}</small>}</span></header><div className="stats">{(["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld"] as const).filter((key) => Object.hasOwn(warrior.stats, key)).map((key) => <span key={key}><small>{presentationOutput(localizedLabel(key, locale))}</small>{presentationOutput(warriorCharacteristic(warrior, key, locale))}</span>)}</div></section>
      <section className="draft-card-box"><h4>{presentationOutput(translate({ key: "ui.c0081f2540bc" }, locale))}</h4>{warrior.equipment.map((entry) => <p key={entry.item_id}><KnowledgeHint knowledge={knowledge} kind="item" id={entry.item_id} locale={locale} quantity={entry.quantity} /></p>)}{warrior.equipment.length === 0 && <p>{presentationOutput(textSymbol("—"))}</p>}</section>
      <section className="draft-card-box"><h4>{presentationOutput(translate({ key: "ui.bee89842c456" }, locale))}</h4>{rules.map((entry) => <p key={entry.id}><KnowledgeHint knowledge={knowledge} kind={entry.kind} id={entry.id} profileId={entry.profileId} bandId={entry.bandId} locale={locale}>{presentationOutput(entry.label)}</KnowledgeHint></p>)}{rules.length === 0 && <p>{presentationOutput(textSymbol("—"))}</p>}</section>
      {(warrior.games_to_miss ?? 0) > 0 && <section className="draft-card-box"><h4>{presentationOutput(translate({ key: "ui.c0ada5ed3044" }, locale))}</h4><p>{presentationOutput(translate({ key: "warrior.absence", args: { reason: readableValue(warrior.absence_reason ?? "injured", locale), count: warrior.games_to_miss ?? 0 } }, locale))}</p></section>}
    </div>
    <footer><div className="skill-access"><small>{presentationOutput(translate({ key: "ui.7644f4e6a00f" }, locale))}</small><span>{presentationOutput(warrior.skill_access?.length ? textJoin(warrior.skill_access.map((key) => localizedLabel(key, locale)), " · ") : textSymbol("—"))}</span></div><ExperienceTrack experience={warrior.experience} kind={warrior.kind} locale={locale}/></footer>
  </article>;
}

import { useMemo, useState } from "react";
import { experienceAwards } from "@app/campaign/features/advances/experience-workflow";
import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { AdvancesPanel } from "./AdvancesPanel";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

export function PostBattleExperience({ document, knowledge, locale="en" }: { readonly document: CampaignDocument; readonly knowledge: ArtefactKnowledgeReader; readonly locale?: "es" | "en" }) {
  const app = useCampaignApp();
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const battle = post && document.campaign.battles.find((row) => row.number === post.battle_number);
  const calculated = useMemo(() => experienceAwards(document, knowledge), [document, knowledge]);
  const [editing, setEditing] = useState(false);
  const [awards, setAwards] = useState<Record<string, number>>({});
  if (!post) return null;
  const injuryCounts = new Map<string, number>();
  const unresolvedInjuries = (battle?.out_of_action_ids ?? []).filter((warriorId) => {
    const casualtyIndex = (injuryCounts.get(warriorId) ?? 0) + 1;
    injuryCounts.set(warriorId, casualtyIndex);
    const warrior = document.campaign.warriors.find((row) => row.id === warriorId);
    const recorded = (warrior?.injury_records ?? []).some((row) => Number(row["battle_number"]) === post.battle_number && Number(row["casualty_index"] ?? 1) === casualtyIndex);
    const followUp = (post.pending_follow_ups ?? []).some((row) => row["warrior_id"] === warriorId);
    return !recorded || followUp;
  }).length;

  const t=locale==="es"?{title:"Experiencia y avances",applied:"Experiencia de batalla aplicada.",locked:"Las recompensas calculadas quedan bloqueadas hasta que actives la edición manual.",lock:"Bloquear recompensas",edit:"Editar recompensas",warrior:"Guerrero",status:"Estado",award:"EXP",absent:"Ausente",eligible:"Elegible",none:"Sin avances",injuries:"Resuelve todas las heridas graves antes de aplicar experiencia",remaining:"pendientes",apply:"Aplicar experiencia una vez",xp:"EXP para"}:{title:"Experience and advances",applied:"Battle experience applied.",locked:"Calculated awards are locked unless manual editing is enabled.",lock:"Lock awards",edit:"Edit awards",warrior:"Warrior",status:"Status",award:"XP award",absent:"Absent",eligible:"Eligible",none:"No advances",injuries:"Resolve all serious injuries before applying experience",remaining:"remaining",apply:"Apply experience once",xp:"XP for"};
  if (post.experience_applied) return <section aria-label={t.title}><h3>02 · {t.title}</h3><p role="status">{t.applied}</p><AdvancesPanel document={document} knowledge={knowledge} locale={locale} /></section>;

  return <section aria-label={t.title}>
    <div className="section-heading"><div><h3>02 · {t.title}</h3><p>{t.locked}</p></div><button type="button" onClick={() => setEditing((value) => !value)}>{editing ? t.lock : t.edit}</button></div>
    <div className="table-scroll"><table><thead><tr><th>{t.warrior}</th><th>{t.status}</th><th>{t.award}</th></tr></thead><tbody>{calculated.map((row) => <tr key={row.warrior_id}><td>{row.warrior_name}</td><td>{row.absent ? t.absent : row.eligible ? t.eligible : t.none}</td><td>{editing && row.eligible && !row.absent ? <input aria-label={`${t.xp} ${row.warrior_name}`} type="number" min={0} step={1} value={awards[row.warrior_id] ?? row.amount} onChange={(event) => setAwards((current) => ({ ...current, [row.warrior_id]: Math.max(0, Math.trunc(event.target.valueAsNumber || 0)) }))} /> : row.amount}</td></tr>)}</tbody></table></div>
    {unresolvedInjuries > 0 && <p role="status">{t.injuries} ({unresolvedInjuries} {t.remaining}).</p>}
    <button className="primary" type="button" disabled={unresolvedInjuries > 0} data-disabled-reason={unresolvedInjuries > 0 ? (locale === "es" ? "Resuelve primero todas las heridas graves." : "Resolve all serious injuries first.") : undefined} onClick={() => void app.runAction("applyBattleExperience", editing ? { awards: Object.fromEntries(calculated.map((row) => [row.warrior_id, awards[row.warrior_id] ?? row.amount])) } : {})}>{t.apply}</button>
  </section>;
}

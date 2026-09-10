import { useMemo, useState } from "react";
import { experienceAwards } from "@app/campaign/features/advances/experience-workflow";
import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { AdvancesPanel } from "./AdvancesPanel";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";

export function PostBattleExperience({ document, knowledge }: { readonly document: CampaignDocument; readonly knowledge: ArtefactKnowledgeReader }) {
  const app = useCampaignApp();
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const battle = post && document.campaign.battles.find((row) => row.number === post.battle_number);
  const calculated = useMemo(() => experienceAwards(document, knowledge), [document, knowledge]);
  const [editing, setEditing] = useState(false);
  const [awards, setAwards] = useState<Record<string, number>>({});
  if (!post) return null;
  const unresolvedInjuries = (battle?.out_of_action_ids ?? []).filter((warriorId) => {
    const warrior = document.campaign.warriors.find((row) => row.id === warriorId);
    const recorded = (warrior?.injury_records ?? []).some((row) => Number(row["battle_number"]) === post.battle_number);
    const followUp = (post.pending_follow_ups ?? []).some((row) => row["warrior_id"] === warriorId);
    return !recorded || followUp;
  }).length;

  if (post.experience_applied) {
    return <section aria-label="Experience and advances"><h3>02 · Experience and advances</h3><p role="status">Battle experience applied.</p><AdvancesPanel document={document} /></section>;
  }

  return <section aria-label="Experience and advances">
    <div className="section-heading"><div><h3>02 · Experience and advances</h3><p>Calculated awards are locked unless manual editing is enabled.</p></div><button type="button" onClick={() => setEditing((value) => !value)}>{editing ? "Lock awards" : "Edit awards"}</button></div>
    <div className="table-scroll"><table><thead><tr><th>Warrior</th><th>Status</th><th>XP award</th></tr></thead><tbody>{calculated.map((row) => <tr key={row.warrior_id}><td>{row.warrior_name}</td><td>{row.absent ? "Absent" : row.eligible ? "Eligible" : "No advances"}</td><td>{editing && row.eligible && !row.absent ? <input aria-label={`XP for ${row.warrior_name}`} type="number" min={0} step={1} value={awards[row.warrior_id] ?? row.amount} onChange={(event) => setAwards((current) => ({ ...current, [row.warrior_id]: Math.max(0, Math.trunc(event.target.valueAsNumber || 0)) }))} /> : row.amount}</td></tr>)}</tbody></table></div>
    {unresolvedInjuries > 0 && <p role="status">Resolve all serious injuries before applying experience ({unresolvedInjuries} remaining).</p>}
    <button className="primary" type="button" disabled={unresolvedInjuries > 0} onClick={() => void app.runAction("applyBattleExperience", editing ? { awards: Object.fromEntries(calculated.map((row) => [row.warrior_id, awards[row.warrior_id] ?? row.amount])) } : {})}>Apply experience once</button>
  </section>;
}

import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { OpenPayload } from "@domain/campaign/index";
import { DiceResolver } from "../dice/DiceResolver";
import { useCampaignApp } from "../campaign/useCampaignApp";
import type { CampaignDocument } from "../campaign/types";

export function AdvancesPanel({ document, knowledge }: { readonly document: CampaignDocument; readonly knowledge: ArtefactKnowledgeReader }) {
  const app = useCampaignApp();
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const rows = (post?.pending_advances ?? []) as readonly OpenPayload[];
  if (rows.length === 0) return <section aria-label="Advances"><h4>Advance rolls earned</h4><p role="status">No warrior crossed an experience threshold.</p></section>;
  return <section aria-label="Advances"><h4>Advance rolls earned this sequence</h4>{rows.map((row, index) => {
    const id = String(row["warrior_id"]); const threshold = row["threshold"] == null ? null : Number(row["threshold"]); const warrior = document.campaign.warriors.find((item) => item.id === id);
    const committed = Boolean(row["committed"]); const total = row["roll_total"] == null ? null : Number(row["roll_total"]); const choices = (row["advance_options"] ?? []) as OpenPayload[];
    const needsSubroll = total !== null && !committed && choices.length === 0;
    const skills = knowledge.list("skill").filter((skill) => !warrior?.skill_access?.length || warrior.skill_access.includes(String(skill["category"] ?? "")));
    return <article className="warrior-card" key={`${id}:${String(threshold)}:${index}`}><header><div><strong>{warrior?.name ?? String(row["warrior_name"])}</strong><span>{String(row["table"] ?? "hero")} · {threshold === null ? "immediate advance" : `${threshold} XP threshold`}</span></div><b>{committed ? String(row["applied_label"] ?? "Committed") : "Pending"}</b></header>
      {((row["roll_history"] ?? []) as string[]).map((message) => <p className="global-error" key={message}>{message}</p>)}
      {!committed && total === null && <DiceResolver count={2} sides={6} label="Advance roll · 2D6" onResolve={(dice) => void app.runAction("resolveAdvanceRoll", { warrior_id: id, threshold, roll_total: dice[0] + dice[1] })} />}
      {needsSubroll && <DiceResolver count={1} sides={6} label={`Characteristic sub-roll after ${total} · D6`} onResolve={(dice) => void app.runAction("resolveAdvanceRoll", { warrior_id: id, threshold, roll_total: total, subroll: dice[0] })} />}
      {!committed && choices.some((choice) => choice["kind"] === "characteristic_increase") && <div className="button-row">{choices.filter((choice) => choice["kind"] === "characteristic_increase").map((choice) => <button key={String(choice["characteristic"])} onClick={() => void app.runAction("commitAdvanceChoice", { warrior_id: id, threshold, kind: "characteristic_increase", characteristic: choice["characteristic"] })}>+{String(choice["amount"] ?? 1)} {String(choice["characteristic"])}</button>)}</div>}
      {!committed && choices.some((choice) => choice["kind"] === "choose_skill") && <label>Choose skill<select defaultValue="" onChange={(event) => { if (event.target.value) void app.runAction("commitAdvanceChoice", { warrior_id: id, threshold, kind: "choose_skill", skill_id: event.target.value }); }}><option value="" disabled>Select a permitted skill…</option>{skills.map((skill) => <option value={String(skill["id"])} key={String(skill["id"])}>{String((skill["names"] as Record<string, string>)?.["en"] ?? skill["name"] ?? skill["id"])}</option>)}</select></label>}
      {!committed && choices.some((choice) => choice["kind"] === "promote_henchman") && <p role="status">The Lad's Got Talent requires the desktop-equivalent promotion flow; this advance remains pending.</p>}
      {!committed && choices.some((choice) => choice["kind"] === "generate_spell") && <p role="status">Spell generation requires the desktop lore picker; this advance remains pending.</p>}
    </article>;
  })}</section>;
}

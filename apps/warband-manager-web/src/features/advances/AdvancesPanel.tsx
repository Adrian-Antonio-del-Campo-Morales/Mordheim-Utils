import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import type { OpenPayload } from "@domain/campaign/index";
import { DiceResolver } from "../dice/DiceResolver";
import { useCampaignApp } from "../campaign/useCampaignApp";
import type { CampaignDocument } from "../campaign/types";
import { promotionHeroTables, wizardLore } from "@app/campaign/features/advances/advance-resolution-workflow";
import { useState } from "react";

function PromotionOffer({ warriorId, threshold }: { warriorId: string; threshold: number | null }) {
  const app=useCampaignApp(); const [name,setName]=useState("");
  return <form className="inline-form" onSubmit={(event)=>{event.preventDefault();void app.runAction("promoteHenchman",{warrior_id:warriorId,threshold,member_name:name.trim()});}}><label>New Hero name<input required value={name} onChange={(event)=>setName(event.target.value)}/></label><button className="primary" disabled={!name.trim()}>Promote member</button></form>;
}

function PromotionSetup({ document, knowledge, warriorId }: { document: CampaignDocument; knowledge: ArtefactKnowledgeReader; warriorId: string }) {
  const app=useCampaignApp(); const [selected,setSelected]=useState<string[]>([]); const tables=promotionHeroTables(document,knowledge);
  return <fieldset><legend>Choose exactly two future Hero skill lists</legend>{tables.map((table)=><label key={table}><input type="checkbox" checked={selected.includes(table)} disabled={!selected.includes(table)&&selected.length>=2} onChange={(event)=>setSelected((current)=>event.target.checked?[...current,table]:current.filter((item)=>item!==table))}/>{table}</label>)}<button className="primary" disabled={selected.length!==2} onClick={()=>void app.runAction("setPromotionSkillTables",{warrior_id:warriorId,tables:selected})}>Confirm skill lists</button></fieldset>;
}

export function AdvancesPanel({ document, knowledge }: { readonly document: CampaignDocument; readonly knowledge: ArtefactKnowledgeReader }) {
  const app = useCampaignApp();
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const rows = (post?.pending_advances ?? []) as readonly OpenPayload[];
  if (rows.length === 0) return <section aria-label="Advances"><h4>Advance rolls earned</h4><p role="status">No warrior crossed an experience threshold.</p></section>;
  return <section aria-label="Advances"><h4>Advance rolls earned this sequence</h4>{rows.map((row, index) => {
    const id = String(row["warrior_id"]); const threshold = row["threshold"] == null ? null : Number(row["threshold"]); const warrior = document.campaign.warriors.find((item) => item.id === id);
    const committed = Boolean(row["committed"]); const total = row["roll_total"] == null ? null : Number(row["roll_total"]); const choices = (row["advance_options"] ?? []) as OpenPayload[];
    const promotionSetup=Boolean(row["promotion_setup_pending"]);
    const needsSubroll = total !== null && !committed && choices.length === 0;
    const skills = knowledge.list("skill").filter((skill) => !warrior?.skill_access?.length || warrior.skill_access.includes(String(skill["category"] ?? "")));
    const loreId = warrior ? wizardLore(knowledge, document, warrior) : null; const lore = loreId ? knowledge.queryKnowledge({ id: { kind: "lore_id", value: loreId } }) : null; const spells = lore?.ok ? (lore.record.data["spells"] ?? []) as readonly Record<string, unknown>[] : [];
    return <article className="warrior-card" key={`${id}:${String(threshold)}:${index}`}><header><div><strong>{warrior?.name ?? String(row["warrior_name"])}</strong><span>{String(row["table"] ?? "hero")} · {threshold === null ? "immediate advance" : `${threshold} XP threshold`}</span></div><b>{committed ? String(row["applied_label"] ?? "Committed") : "Pending"}</b></header>
      {((row["roll_history"] ?? []) as string[]).map((message) => <p className="global-error" key={message}>{message}</p>)}
      {promotionSetup && <PromotionSetup document={document} knowledge={knowledge} warriorId={id}/>}
      {!promotionSetup && !committed && total === null && <DiceResolver count={2} sides={6} label="Advance roll · 2D6" onResolve={(dice) => void app.runAction("resolveAdvanceRoll", { warrior_id: id, threshold, roll_total: dice[0] + dice[1] })} />}
      {needsSubroll && <DiceResolver count={1} sides={6} label={`Characteristic sub-roll after ${total} · D6`} onResolve={(dice) => void app.runAction("resolveAdvanceRoll", { warrior_id: id, threshold, roll_total: total, subroll: dice[0] })} />}
      {!committed && choices.some((choice) => choice["kind"] === "characteristic_increase") && <div className="button-row">{choices.filter((choice) => choice["kind"] === "characteristic_increase").map((choice) => <button key={String(choice["characteristic"])} onClick={() => void app.runAction("commitAdvanceChoice", { warrior_id: id, threshold, kind: "characteristic_increase", characteristic: choice["characteristic"] })}>+{String(choice["amount"] ?? 1)} {String(choice["characteristic"])}</button>)}</div>}
      {!committed && choices.some((choice) => choice["kind"] === "choose_skill") && <label>Choose skill<select defaultValue="" onChange={(event) => { if (event.target.value) void app.runAction("commitAdvanceChoice", { warrior_id: id, threshold, kind: "choose_skill", skill_id: event.target.value }); }}><option value="" disabled>Select a permitted skill…</option>{skills.map((skill) => <option value={String(skill["id"])} key={String(skill["id"])}>{String((skill["names"] as Record<string, string>)?.["en"] ?? skill["name"] ?? skill["id"])}</option>)}</select></label>}
      {!committed && choices.some((choice) => choice["kind"] === "promote_henchman") && <PromotionOffer warriorId={id} threshold={threshold}/>}
      {!committed && choices.some((choice) => choice["kind"] === "generate_spell") && <label>Generate spell<select defaultValue="" onChange={(event) => { const spell=spells.find((item)=>item["id"]===event.target.value); const duplicate=warrior?.skills.includes(String(spell?.["name"]??"")); if(event.target.value) void app.runAction("commitAdvanceChoice", { warrior_id:id,threshold,kind:duplicate?"duplicate_spell":"generate_spell",skill_id:event.target.value }); }}><option value="" disabled>Select a spell from {loreId}…</option>{spells.map((spell)=><option value={String(spell["id"])} key={String(spell["id"])}>{String(spell["name"]??spell["id"])}{warrior?.skills.includes(String(spell["name"]))?" · already known: −1 difficulty":""}</option>)}</select></label>}
      {!committed && choices.some((choice) => choice["kind"] === "external_resolution") && <button onClick={() => void app.runAction("commitAdvanceChoice", { warrior_id:id, threshold, kind:"external_resolution" })}>Record external resolution</button>}
    </article>;
  })}</section>;
}

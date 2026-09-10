import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { DiceResolver } from "../dice/DiceResolver";
import { useCampaignApp } from "../campaign/useCampaignApp";
import type { CampaignDocument } from "../campaign/types";

function inRange(spec: unknown, value: number): boolean {
  const text = String(spec ?? ""); const [a, b] = text.split("-").map(Number); return Number.isFinite(a) && value >= a && value <= (Number.isFinite(b) ? b : a);
}

export function PostBattleInjuries({ document, knowledge }: { document: CampaignDocument; knowledge: ArtefactKnowledgeReader }) {
  const app = useCampaignApp(); const post=document.campaign.post_battles.find((row) => !row.complete); const battle=post && document.campaign.battles.find((row) => row.number===post.battle_number);
  if (!post || !battle) return null;
  const warriors=(battle.out_of_action_ids ?? []).map((id) => document.campaign.warriors.find((warrior) => warrior.id===id)).filter((warrior): warrior is NonNullable<typeof warrior> => Boolean(warrior));
  const injuries=knowledge.list("injury");
  const pits=(post.pending_follow_ups??[]).filter((row)=>row["type"]==="encounter"&&row["encounter_id"]==="campaign.encounter.sold-to-the-pits");
  return <section aria-label="Serious injuries"><h3>01 · Serious injuries</h3>{warriors.length===0 && <p role="status">No warriors were recorded out of action.</p>}{warriors.map((warrior) => { const unresolved=(post.pending_follow_ups ?? []).some((row) => row.warrior_id===warrior.id); const resolved=!unresolved && (warrior.injury_records ?? []).some((record) => Number(record.battle_number)===battle.number); const hero=warrior.kind==="hero"; return <article className="injury-card" key={warrior.id}><h4>{warrior.name}</h4>{resolved ? <p>Resolved for Battle #{battle.number}.</p> : unresolved ? <p role="status">Follow-up resolution required.</p> : <DiceResolver count={hero ? 2 : 1} sides={6} label={hero ? "D66 serious injury" : "D6 henchman injury"} onResolve={(dice) => { const roll=hero ? dice[0] * 10 + dice[1] : dice[0]; const outcome=injuries.find((row) => row.applies_to===warrior.kind && inRange(row.roll, roll)); if (!outcome) return; const effects=Array.isArray(outcome.effects) ? outcome.effects.map((effect) => { const raw=effect as Record<string, unknown>; if(raw.type==="warrior.miss_games" && typeof raw.games==="object") return { kind:"miss_games", value:Number((raw.games as Record<string,unknown>).value ?? 1) }; if(raw.type==="warrior.characteristic_modifier") return { kind:"stat_modifier", stat:statKey(String(raw.characteristic)), value:Number(raw.modifier) }; if(raw.type==="warrior.add_condition") return { kind:"add_condition", condition_id:String(raw.condition_id) }; return { ...raw, kind:String(raw.type ?? "uninterpreted") }; }) : []; void app.runAction("applyInjuryOutcome", { warrior_id:warrior.id, battle_number:battle.number, result_id:String(outcome.id), result:String(outcome.result), effects }); }} />}</article>; })}{pits.map((follow)=>{const warrior=document.campaign.warriors.find((item)=>item.id===follow["warrior_id"]);return <article className="injury-card" key={String(follow["id"])}><h4>{warrior?.name??"Warrior"} · Sold to the Pits</h4><button className="primary" onClick={()=>void app.runAction("resolveSoldToPits",{follow_up_id:follow["id"],won:true})}>Won</button><DiceResolver count={2} sides={6} label="Lost · D66 serious injury" onResolve={(dice)=>void app.runAction("resolveSoldToPits",{follow_up_id:follow["id"],won:false,injury_roll:dice[0]*10+dice[1]})}/></article>;})}</section>;
}

function statKey(value: string): string {
  return ({ movement:"M", weapon_skill:"WS", ballistic_skill:"BS", strength:"S", toughness:"T", wounds:"W", initiative:"I", attacks:"A", leadership:"Ld" } as Record<string,string>)[value] ?? value;
}

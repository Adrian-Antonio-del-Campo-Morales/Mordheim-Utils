import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { DiceResolver } from "../dice/DiceResolver";
import { useCampaignApp } from "../campaign/useCampaignApp";
import type { CampaignDocument } from "../campaign/types";
import { injuryEffects } from "@app/campaign/features/injuries/injury-followup-workflow";

function inRange(spec: unknown, value: number): boolean {
  const text = String(spec ?? ""); const [a, b] = text.split("-").map(Number); return Number.isFinite(a) && value >= a && value <= (Number.isFinite(b) ? b : a);
}

export function PostBattleInjuries({ document, knowledge, locale="en" }: { document: CampaignDocument; knowledge: ArtefactKnowledgeReader; locale?:"es"|"en" }) {
  const app = useCampaignApp(); const post=document.campaign.post_battles.find((row) => !row.complete); const battle=post && document.campaign.battles.find((row) => row.number===post.battle_number);
  if (!post || !battle) return null;
  const t=locale==="es"?{title:"Heridas graves",none:"No se registraron guerreros fuera de combate.",resolved:"Resuelto para batalla",follow:"Requiere resolver seguimiento.",hero:"Herida grave D66",henchman:"Herida de secuaz D6",warrior:"Guerrero",pits:"Vendido a los pozos",won:"Ganó",lost:"Perdió · herida grave D66"}:{title:"Serious injuries",none:"No warriors were recorded out of action.",resolved:"Resolved for Battle",follow:"Follow-up resolution required.",hero:"D66 serious injury",henchman:"D6 henchman injury",warrior:"Warrior",pits:"Sold to the Pits",won:"Won",lost:"Lost · D66 serious injury"};
  const seen = new Map<string, number>();
  const warriors=(battle.out_of_action_ids ?? []).flatMap((id) => { const warrior=document.campaign.warriors.find((row) => row.id===id); if(!warrior)return []; const casualtyIndex=(seen.get(id)??0)+1; seen.set(id,casualtyIndex); return [{ warrior, casualtyIndex }]; });
  const injuries=knowledge.list("injury");
  const pits=(post.pending_follow_ups??[]).filter((row)=>row["type"]==="encounter"&&row["encounter_id"]==="campaign.encounter.sold-to-the-pits");
  return <section aria-label={t.title}><h3>01 · {t.title}</h3>{warriors.length===0 && <p role="status">{t.none}</p>}{warriors.map(({ warrior, casualtyIndex }) => { const unresolved=(post.pending_follow_ups ?? []).some((row) => row.warrior_id===warrior.id && Number(row.casualty_index??1)===casualtyIndex); const resolved=!unresolved && (warrior.injury_records ?? []).some((record) => Number(record.battle_number)===battle.number && Number(record.casualty_index??1)===casualtyIndex); const hero=warrior.kind==="hero"; return <article className="injury-card" key={`${warrior.id}:${casualtyIndex}`}><h4>{warrior.name}{casualtyIndex>1?` · ${casualtyIndex}`:""}</h4>{resolved ? <p>{t.resolved} #{battle.number}.</p> : unresolved ? <p role="status">{t.follow}</p> : <DiceResolver count={hero ? 2 : 1} sides={6} label={hero ? t.hero : t.henchman} locale={locale} onResolve={(dice) => { const roll=hero ? dice[0] * 10 + dice[1] : dice[0]; const outcome=injuries.find((row) => row.applies_to===warrior.kind && inRange(row.roll, roll)); if (!outcome) return; void app.runAction("applyInjuryOutcome", { warrior_id:warrior.id, battle_number:battle.number, casualty_index:casualtyIndex, result_id:String(outcome.id), result:String(outcome.result), effects:injuryEffects(outcome) }); }} />}</article>; })}{pits.map((follow)=>{const warrior=document.campaign.warriors.find((item)=>item.id===follow["warrior_id"]);return <article className="injury-card" key={String(follow["id"])}><h4>{warrior?.name??t.warrior} · {t.pits}</h4><button className="primary" onClick={()=>void app.runAction("resolveSoldToPits",{follow_up_id:follow["id"],won:true})}>{t.won}</button><DiceResolver count={2} sides={6} label={t.lost} locale={locale} onResolve={(dice)=>void app.runAction("resolveSoldToPits",{follow_up_id:follow["id"],won:false,injury_roll:dice[0]*10+dice[1]})}/></article>;})}</section>;
}

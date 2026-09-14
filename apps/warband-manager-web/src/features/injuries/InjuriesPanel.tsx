/**
 * Injuries and recovery presentation.
 *
 * Renders the injuries read model (condition, missed games, pending rolls,
 * injury history per warrior) and dispatches through the campaign app
 * service (`applyInjuryOutcome`, `resolveInjuryFollowUp`, `recoverWarrior`
 * actions) — rejections surface via the error seam, never thrown.
 *
 * Pure view over the CampaignAppView seam; read-model helpers live in the
 * application feature so this file only exports components (react-refresh).
 */
import { useState } from "react";

import { useCampaignApp } from "../campaign/useCampaignApp";
import type { CampaignDocument } from "../campaign/types";
import { NumberStepper } from "../common/NumberStepper";
import { injuryOverview } from "@app/campaign/features/injuries/injuries-workflow";
import { injuryFollowUpDice } from "@app/campaign/features/injuries/injury-followup-workflow";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { DiceResolver } from "../dice/DiceResolver";
import { knowledgeName, readableValue } from "../campaign/displayText";

interface InjuriesPanelProps {
  readonly document: CampaignDocument;
  readonly knowledge?: ArtefactKnowledgeReader;
  readonly locale?: "es" | "en";
}

export function InjuriesPanel({ document, knowledge, locale = "en" }: InjuriesPanelProps) {
  const app = useCampaignApp();
  const [busy, setBusy] = useState(false);
  const [targets, setTargets] = useState<Record<string,string>>({});
  const [ransoms, setRansoms] = useState<Record<string,number>>({});
  const overview = injuryOverview(document);
  const t = locale === "es" ? { title: "Heridas", recoveryTitle: "Heridas y Recuperación", warrior: "Guerrero", condition: "Estado", missingGames: "Batallas que se Pierde", recovery: "Recuperación", pendingRolls: "Tiradas Pendientes", serve: "Hacer Perder 1 Batalla", chooseEye: "Elige Ojo", left: "Izquierdo", right: "Derecho", hatredTarget: "Objetivo del Odio", setHatred: "Establecer Odio", ransom: "Rescate", exchange: "Intercambiar", lost: "Perdido", followUp: "Resolver Seguimiento", resolve: "Resolver" } : { title: "Injuries", recoveryTitle: "Injuries & Recovery", warrior: "Warrior", condition: "Condition", missingGames: "Missing Games", recovery: "Recovery", pendingRolls: "Pending Rolls", serve: "Miss 1 Game", chooseEye: "Choose Eye", left: "Left", right: "Right", hatredTarget: "Hatred Target", setHatred: "Set Hatred", ransom: "Ransom", exchange: "Exchange", lost: "Lost", followUp: "Resolve Injury Follow-up", resolve: "Resolve" };

  const run = async (action: string, input: Record<string, unknown>) => {
    setBusy(true);
    // Rejections surface through the shell's shared error seam (app.error);
    // the document stays intact, so this component only blocks re-entry.
    await app.runAction(action, input);
    setBusy(false);
  };

  return (
    <section aria-label={t.title}>
      <h3>{t.recoveryTitle}</h3>

      {app.error && (
        <output role="alert" style={{ color: "crimson", display: "block" }}>
          {app.error}
        </output>
      )}

      {overview.open_rolls.length > 0 && (
        <p>
          {overview.open_rolls.length} {locale === "es" ? "tirada(s) de heridas sin resolver en el post-batalla pendiente." : `unresolved injury roll${overview.open_rolls.length === 1 ? "" : "s"} on the pending post-battle.`}
        </p>
      )}

        <table className="mobile-cards">
          <caption>{locale === "es" ? "Estado de heridas de la banda" : "Warband injury status"}</caption>
        <thead>
          <tr>
            <th scope="col">{t.warrior}</th>
            <th scope="col">{t.condition}</th>
            <th scope="col">{t.missingGames}</th>
            <th scope="col">{t.recovery}</th>
            <th scope="col">{t.pendingRolls}</th>
          </tr>
        </thead>
        <tbody>
          {overview.warriors.map((row) => (
            <tr key={row.warrior_id} data-restricted={row.restricted || undefined}>
              <td data-label={t.warrior}>{row.name}</td>
              <td data-label={t.condition}>
                {row.condition
                  ? `${readableValue(row.condition, locale)}${row.condition_detail ? ` (${knowledgeName(knowledge, "injury", row.condition_detail, locale, row.condition_detail)})` : ""}`
                  : "—"}
              </td>
              <td data-label={t.missingGames}>{row.games_to_miss > 0 ? `${row.games_to_miss} (${readableValue(row.absence_reason ?? (locale === "es" ? "Lesión" : "Injury"), locale)})` : "0"}</td>
              <td data-label={t.recovery}>
                <button
                  type="button"
                  disabled={busy || row.games_to_miss === 0}
                  data-disabled-reason={busy ? (locale === "es" ? "Se está resolviendo otra herida." : "Another injury is being resolved.") : row.games_to_miss === 0 ? (locale === "es" ? "Este guerrero no tiene batallas pendientes que perder." : "This warrior has no missed games remaining.") : undefined}
                  aria-label={`${locale === "es" ? "Recuperar" : "Recover"} ${row.name}`}
                  onClick={() => run("recoverWarrior", { warrior_id: row.warrior_id })}
                >
                  {t.serve}
                </button>
              </td>
              <td data-label={t.pendingRolls}>
                {row.pending_follow_ups.length === 0
                  ? "—"
                  : row.pending_follow_ups.map((followUp) => {
                      const id = String((followUp as { id?: unknown }).id ?? "");
                      const type=String((followUp as { type?: unknown }).type??"");
                      if(type==="eye_injury")return <span key={id}>{t.chooseEye}: <button disabled={busy} data-disabled-reason={busy ? (locale==="es"?"Se está resolviendo otra herida.":"Another injury is being resolved.") : undefined} onClick={()=>run("resolveEyeInjury",{follow_up_id:id,eye:"left"})}>{t.left}</button><button disabled={busy} data-disabled-reason={busy ? (locale==="es"?"Se está resolviendo otra herida.":"Another injury is being resolved.") : undefined} onClick={()=>run("resolveEyeInjury",{follow_up_id:id,eye:"right"})}>{t.right}</button></span>;
                      if(type==="relationship")return <span key={id}><input aria-label={`${t.hatredTarget} ${id}`} value={targets[id]??""} onChange={(event)=>setTargets((current)=>({...current,[id]:event.target.value}))}/><button disabled={busy||!(targets[id]??"").trim()} data-disabled-reason={busy ? (locale==="es"?"Se está resolviendo otra herida.":"Another injury is being resolved.") : !(targets[id]??"").trim() ? (locale==="es"?"Introduce el objetivo del odio.":"Enter the hatred target.") : undefined} onClick={()=>run("resolveHatred",{follow_up_id:id,target:targets[id]})}>{t.setHatred}</button></span>;
                      if(type==="prisoner")return <span key={id}><NumberStepper label={`${t.ransom} ${id}`} value={ransoms[id]??0} onChange={(value)=>setRansoms((current)=>({...current,[id]:value}))}/>{([['ransom',t.ransom],['exchange',t.exchange],['lost',t.lost]] as const).map(([resolution,label])=><button key={resolution} disabled={busy} data-disabled-reason={busy ? (locale==="es"?"Se está resolviendo otra herida.":"Another injury is being resolved.") : undefined} onClick={()=>run("resolvePrisoner",{follow_up_id:id,resolution,...(resolution==='ransom'?{ransom:ransoms[id]??0}:resolution==='lost'?{disposition:'other'}:{})})}>{label}</button>)}</span>;
                      const dice=knowledge&&injuryFollowUpDice(knowledge,followUp as Record<string,unknown>);
                      if(dice)return <DiceResolver locale={locale} count={dice[0]} sides={dice[1]} label={t.followUp} onResolve={(rolls)=>void run("resolveInjuryTableFollowUp",{follow_up_id:id,dice:rolls,roll:dice[0]===2&&dice[1]===6?rolls[0]*10+rolls[1]:rolls.reduce((total,value)=>total+value,0)})}/>;
                      return (
                        <button
                          key={id}
                          type="button"
                          disabled={busy}
                          data-disabled-reason={busy ? (locale === "es" ? "Se está resolviendo otra herida." : "Another injury is being resolved.") : undefined}
                          aria-label={`Resolve injury roll ${id}`}
                          onClick={() =>
                            run("resolveInjuryFollowUp", {
                              follow_up_id: id,
                              outcome: {
                                warrior_id: row.warrior_id,
                                result_id: (followUp as { result_id?: unknown }).result_id ?? "",
                                result: "Resolved",
                                effects: [],
                              },
                            })
                          }
                        >
                          {t.resolve}
                        </button>
                      );
                    })}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

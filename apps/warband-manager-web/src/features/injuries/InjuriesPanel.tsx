import { presentationOutput } from "../campaign/presentation-output";
import { textJoin, textNumber, textSymbol, warriorPersonalName } from "../campaign/presentation-values";
import { translate } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
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
import { KnowledgeHint } from "../campaign/KnowledgeHint";

interface InjuriesPanelProps {
  readonly document: CampaignDocument;
  readonly knowledge?: ArtefactKnowledgeReader;
  readonly locale?: "es" | "en";
}

export function InjuriesPanel({ document, knowledge, locale: requestedLocale }: InjuriesPanelProps) {
  const locale = useLocale(requestedLocale);
  const app = useCampaignApp();
  const [busy, setBusy] = useState(false);
  const [targets, setTargets] = useState<Record<string,string>>({});
  const [ransoms, setRansoms] = useState<Record<string,number>>({});
  const overview = injuryOverview(document);
  const t = ({ title: translate({ key: "ui.1a912f623fd1" }, locale), recoveryTitle: translate({ key: "ui.28b237ff01f2" }, locale), warrior: translate({ key: "ui.dca4e7aa700c" }, locale), condition: translate({ key: "ui.3c1f26265e4f" }, locale), missingGames: translate({ key: "ui.f01dd46162ef" }, locale), recovery: translate({ key: "ui.9de7c707a1b0" }, locale), pendingRolls: translate({ key: "ui.b2ec6fed01d8" }, locale), serve: translate({ key: "ui.f9b82be20812" }, locale), chooseEye: translate({ key: "ui.5b42bdddc796" }, locale), left: translate({ key: "ui.36adf04d7f2b" }, locale), right: translate({ key: "ui.0a2ae3aa3354" }, locale), hatredTarget: translate({ key: "ui.95300c69a379" }, locale), setHatred: translate({ key: "ui.2c2d07c20359" }, locale), ransom: translate({ key: "ui.7e7a8b47c298" }, locale), exchange: translate({ key: "ui.81c7a226f100" }, locale), lost: translate({ key: "ui.0d3818cf8a9c" }, locale), followUp: translate({ key: "ui.c48d30bc8e34" }, locale), resolve: translate({ key: "ui.8b045a3c4cec" }, locale) });

  const run = async (action: string, input: Record<string, unknown>) => {
    setBusy(true);
    // Rejections surface through the shell's shared error seam (app.error);
    // the document stays intact, so this component only blocks re-entry.
    await app.runAction(action, input);
    setBusy(false);
  };

  return (
    <section aria-label={presentationOutput(t.title)}>
      <h3>{presentationOutput(t.recoveryTitle)}</h3>

      {app.error && (
        <output role="alert" style={{ color: "crimson", display: "block" }}>
          {presentationOutput(app.error)}
        </output>
      )}

      {overview.open_rolls.length > 0 && (
        <p>
          {presentationOutput(translate({ key: "injury.pending-rolls", args: { count: overview.open_rolls.length } }, locale))}
        </p>
      )}

        <table className="mobile-cards">
          <caption>{presentationOutput(translate({ key: "ui.180d5a2c716b" }, locale))}</caption>
        <thead>
          <tr>
            <th scope="col">{presentationOutput(t.warrior)}</th>
            <th scope="col">{presentationOutput(t.condition)}</th>
            <th scope="col">{presentationOutput(t.missingGames)}</th>
            <th scope="col">{presentationOutput(t.recovery)}</th>
            <th scope="col">{presentationOutput(t.pendingRolls)}</th>
          </tr>
        </thead>
        <tbody>
          {overview.warriors.map((row) => (
            <tr key={row.warrior_id} data-restricted={row.restricted || undefined}>
              <td data-label={presentationOutput(t.warrior)}>{presentationOutput(warriorPersonalName(document.campaign.warriors.find((warrior) => warrior.id === row.warrior_id), locale))}</td>
              <td data-label={presentationOutput(t.condition)}>
                {row.condition ? <>{presentationOutput(readableValue(row.condition, locale))}{row.condition_detail ? <>{presentationOutput(textSymbol("("))}{knowledge ? <KnowledgeHint knowledge={knowledge} kind="injury" id={row.condition_detail} locale={locale}>{presentationOutput(knowledgeName(knowledge, "injury", row.condition_detail, locale))}</KnowledgeHint> : presentationOutput(knowledgeName(knowledge, "injury", row.condition_detail, locale))}{presentationOutput(textSymbol(")"))}</> : presentationOutput(textSymbol(""))}</> : presentationOutput(textSymbol("—"))}
              </td>
              <td data-label={presentationOutput(t.missingGames)}>{presentationOutput(row.games_to_miss > 0 ? textJoin([textNumber(row.games_to_miss, locale), textJoin([textSymbol("("), row.absence_reason ? readableValue(row.absence_reason, locale) : translate({ key: "ui.5655edebe128" }, locale), textSymbol(")")], "")], " ") : textNumber(0, locale))}</td>
              <td data-label={presentationOutput(t.recovery)}>
                <button
                  type="button"
                  disabled={busy || row.games_to_miss === 0}
                  data-disabled-reason={(busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : row.games_to_miss === 0 ? (translate({ key: "disabled.208f3a2933" }, locale)) : undefined) === undefined ? undefined : presentationOutput((busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : row.games_to_miss === 0 ? (translate({ key: "disabled.208f3a2933" }, locale)) : undefined)!)}
                  aria-label={presentationOutput(textJoin([translate({ key: "ui.45beba95d821" }, locale), warriorPersonalName(document.campaign.warriors.find((warrior) => warrior.id === row.warrior_id), locale)]))}
                  onClick={() => run("recoverWarrior", { warrior_id: row.warrior_id })}
                >
                  {presentationOutput(t.serve)}
                </button>
              </td>
              <td data-label={presentationOutput(t.pendingRolls)}>
                {row.pending_follow_ups.length === 0
                  ? presentationOutput(textSymbol("—"))
                  : row.pending_follow_ups.map((followUp) => {
                      const id = String((followUp as { id?: unknown }).id ?? "");
                      const type=String((followUp as { type?: unknown }).type??"");
                      if(type==="eye_injury")return <span key={id}>{presentationOutput(t.chooseEye)} {presentationOutput(textSymbol(":"))} <button disabled={busy} data-disabled-reason={(busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined) === undefined ? undefined : presentationOutput((busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined)!)} onClick={()=>run("resolveEyeInjury",{follow_up_id:id,eye:"left"})}>{presentationOutput(t.left)}</button><button disabled={busy} data-disabled-reason={(busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined) === undefined ? undefined : presentationOutput((busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined)!)} onClick={()=>run("resolveEyeInjury",{follow_up_id:id,eye:"right"})}>{presentationOutput(t.right)}</button></span>;
                      if(type==="relationship")return <span key={id}><input aria-label={presentationOutput(textJoin([t.hatredTarget, warriorPersonalName(document.campaign.warriors.find((warrior) => warrior.id === row.warrior_id), locale)]))} value={targets[id]??""} onChange={(event)=>setTargets((current)=>({...current,[id]:event.target.value}))}/><button disabled={busy||!(targets[id]??"").trim()} data-disabled-reason={(busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : !(targets[id]??"").trim() ? (translate({ key: "disabled.a6625ba624" }, locale)) : undefined) === undefined ? undefined : presentationOutput((busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : !(targets[id]??"").trim() ? (translate({ key: "disabled.a6625ba624" }, locale)) : undefined)!)} onClick={()=>run("resolveHatred",{follow_up_id:id,target:targets[id]})}>{presentationOutput(t.setHatred)}</button></span>;
                      if(type==="prisoner")return <span key={id}><NumberStepper locale={locale} label={textJoin([translate({ key: "number.ransom" }, locale), warriorPersonalName(document.campaign.warriors.find((warrior) => warrior.id === row.warrior_id), locale)])} value={ransoms[id]??0} onChange={(value)=>setRansoms((current)=>({...current,[id]:value}))}/>{([['ransom',t.ransom],['exchange',t.exchange],['lost',t.lost]] as const).map(([resolution,label])=><button key={resolution} disabled={busy} data-disabled-reason={(busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined) === undefined ? undefined : presentationOutput((busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined)!)} onClick={()=>run("resolvePrisoner",{follow_up_id:id,resolution,...(resolution==='ransom'?{ransom:ransoms[id]??0}:resolution==='lost'?{disposition:'other'}:{})})}>{presentationOutput(label)}</button>)}</span>;
                      const dice=knowledge&&injuryFollowUpDice(knowledge,followUp as Record<string,unknown>);
                      if(dice)return <DiceResolver locale={locale} count={dice[0]} sides={dice[1]} label={t.followUp} onResolve={(rolls)=>void run("resolveInjuryTableFollowUp",{follow_up_id:id,dice:rolls,roll:dice[0]===2&&dice[1]===6?rolls[0]*10+rolls[1]:rolls.reduce((total,value)=>total+value,0)})}/>;
                      return (
                        <button
                          key={id}
                          type="button"
                          disabled={busy}
                          data-disabled-reason={(busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined) === undefined ? undefined : presentationOutput((busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined)!)}
                          aria-label={presentationOutput(textJoin([t.resolve, warriorPersonalName(document.campaign.warriors.find((warrior) => warrior.id === row.warrior_id), locale)]))}
                          onClick={() =>
                            run("resolveInjuryFollowUp", {
                              follow_up_id: id,
                              outcome: {
                                warrior_id: row.warrior_id,
                                result_id: (followUp as { result_id?: unknown }).result_id ?? "",
                                result: t.resolve,
                                effects: [],
                              },
                            })
                          }
                        >
                          {presentationOutput(t.resolve)}
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

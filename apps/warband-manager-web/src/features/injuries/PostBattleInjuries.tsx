import { presentationOutput } from "../campaign/presentation-output";
import { textJoin, textNumber, textSymbol, warriorPersonalName, battleParticipantName } from "../campaign/presentation-values";
import { translate } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { useState } from "react";
import { DiceResolver } from "../dice/DiceResolver";
import { useCampaignApp } from "../campaign/useCampaignApp";
import type { CampaignDocument } from "../campaign/types";
import {
  injuryEffects,
  injuryFollowUpDice,
} from "@app/campaign/features/injuries/injury-followup-workflow";
import { knowledgeName, knowledgeDescription } from "../campaign/displayText";
import { KnowledgeHint } from "../campaign/KnowledgeHint";
import { NumberStepper } from "../common/NumberStepper";

function inRange(spec: unknown, value: number): boolean {
  const text = String(spec ?? "");
  const [a, b] = text.split("-").map(Number);
  return (
    Number.isFinite(a) && value >= a && value <= (Number.isFinite(b) ? b : a)
  );
}

function followUpLabel(follow: Record<string, unknown>, locale: "es" | "en") {
  const phase = follow.resolution_phase;
  if (phase === "effect_roll") return translate({ key: "injury.effect-roll" }, locale);
  if (phase === "repeat_count") return translate({ key: "injury.repeat-count" }, locale);
  if (phase === "repeat_result") return translate({ key: "injury.repeat-result", args: { number: typeof follow.repeat_index === "number" ? follow.repeat_index + 1 : NaN } }, locale);
  if (phase === "subtable") return translate({ key: "injury.subtable" }, locale);
  return translate({ key: "injury.followup" }, locale);
}

const injuryFollowUpTypes = new Set([
  "injury_roll",
  "injury_followup",
  "eye_injury",
  "prisoner",
  "relationship",
  "encounter",
]);

export function PostBattleInjuries({
  document,
  knowledge,
  locale: requestedLocale,
}: {
  document: CampaignDocument;
  knowledge: ArtefactKnowledgeReader;
  locale?: "es" | "en";
}) {
  const locale = useLocale(requestedLocale);
  const app = useCampaignApp();
  const post = document.campaign.post_battles.find((row) => !row.complete);
  const battle =
    post &&
    document.campaign.battles.find((row) => row.number === post.battle_number);
  const [busy, setBusy] = useState(false);
  const [targets, setTargets] = useState<Record<string, string>>({});
  const [ransoms, setRansoms] = useState<Record<string, number>>({});
  const run = async (action: string, input: Record<string, unknown>) => {
    setBusy(true);
    await app.runAction(action, input);
    setBusy(false);
  };
  if (!post || !battle) return null;
  const t =
    ({ title: translate({ key: "ui.a85e541108d0" }, locale), none: translate({ key: "ui.ba72332d810c" }, locale), hero: translate({ key: "ui.4caea46c1c58" }, locale), henchman: translate({ key: "ui.57eda620bad4" }, locale), warrior: translate({ key: "ui.dca4e7aa700c" }, locale), result: translate({ key: "ui.3c7693f6bfc5" }, locale), action: translate({ key: "ui.e9906fb3a302" }, locale), pits: translate({ key: "ui.b8186d7b387a" }, locale), won: translate({ key: "ui.b18621baa101" }, locale), lost: translate({ key: "ui.7d24c8a2c0c3" }, locale), chooseEye: translate({ key: "ui.17e3fa4785d9" }, locale), left: translate({ key: "ui.36adf04d7f2b" }, locale), right: translate({ key: "ui.0a2ae3aa3354" }, locale), hatred: translate({ key: "ui.3c53af8123bf" }, locale), setHatred: translate({ key: "ui.7469a45bc53f" }, locale), ransom: translate({ key: "ui.7e7a8b47c298" }, locale), exchange: translate({ key: "ui.81c7a226f100" }, locale), lostPrisoner: translate({ key: "ui.0d3818cf8a9c" }, locale), follow: translate({ key: "ui.9e22865da3ed" }, locale), resolved: translate({ key: "ui.d28ca6d8d54c" }, locale), roll: translate({ key: "ui.9a5040b02281" }, locale) });
  const seen = new Map<string, number>();
  const participants = new Map(
    (battle.participants ?? []).map((row) => [String(row.id), row]),
  );
  const resolvedInjuries = (post.step_state?.injuries ?? {}) as Record<
    string,
    Record<string, unknown>
  >;
  const warriors = (battle.out_of_action_ids ?? []).flatMap((id) => {
    const casualtyIndex = (seen.get(id) ?? 0) + 1;
    seen.set(id, casualtyIndex);
    const live = document.campaign.warriors.find((row) => row.id === id);
    const participant = participants.get(id);
    const warrior =
      live ??
      ({
        id,
        name: String(participant?.name ?? (translate({ key: "ui.85ac9cd8b1b8" }, locale))),
        profile_name: String(participant?.profile_name ?? id),
        kind: participant?.kind === "henchman" ? "henchman" : "hero",
        stats: {},
        equipment: [],
        skills: [],
        experience: 0,
        cost: 0,
      } as CampaignDocument["campaign"]["warriors"][number]);
    return [{ warrior, casualtyIndex, live: Boolean(live) }];
  });
  const injuries = knowledge.list("injury");
  return (
    <section aria-label={presentationOutput(t.title)}>
      <h3>{presentationOutput(textJoin([textNumber(1, locale, 2), t.title], " · "))}</h3>
      {warriors.length === 0 ? (
        <p role="status">{presentationOutput(t.none)}</p>
      ) : (
        <table className="mobile-cards injury-results">
          <caption>{presentationOutput(t.title)}</caption>
          <thead>
            <tr>
              <th>{presentationOutput(t.warrior)}</th>
              <th>{presentationOutput(t.result)}</th>
              <th>{presentationOutput(t.action)}</th>
            </tr>
          </thead>
          <tbody>
            {warriors.map(({ warrior, casualtyIndex, live }) => {
              const storedRecord = (warrior.injury_records ?? []).find(
                (row) =>
                  Number(row.battle_number) === battle.number &&
                  Number(row.casualty_index ?? 1) === casualtyIndex,
              );
              const resolved = resolvedInjuries[`${warrior.id}:${casualtyIndex}`];
              const followUpRolls = Array.isArray(resolved?.follow_up_rolls) ? resolved.follow_up_rolls as Record<string, unknown>[] : [];
              const record = storedRecord ?? resolved;
              const followUps = (post.pending_follow_ups ?? []).filter(
                (row) =>
                  injuryFollowUpTypes.has(String(row.type ?? "")) &&
                  row.warrior_id === warrior.id &&
                  Number(row.casualty_index ?? 1) === casualtyIndex,
              );
              const usesHeroTable = warrior.kind !== "henchman";
              const resultId = String(record?.result_id ?? "");
              const effect = knowledgeDescription(knowledge, { kind: "injury", id: resultId }, locale).text;
              return (
                <tr key={`${warrior.id}:${casualtyIndex}`}>
                  <td data-label={presentationOutput(t.warrior)}>
                    {presentationOutput(live ? warriorPersonalName(warrior, locale) : battleParticipantName(battle, warrior.id, locale))}
                    {presentationOutput(casualtyIndex > 1 ? textJoin([textSymbol(""), textNumber(casualtyIndex, locale)], " · ") : textSymbol(""))}
                  </td>
                  <td data-label={presentationOutput(t.result)}>
                    {record ? (
                      <>
                        <strong>
                          <KnowledgeHint knowledge={knowledge} kind="injury" id={resultId} locale={locale}>
                            {presentationOutput(knowledgeName(knowledge, "injury", resultId, locale))}
                          </KnowledgeHint>
                        </strong>
                        {effect && <small>{presentationOutput(effect)}</small>}
                        {warrior.games_to_miss ? (
                          <small>
                            {presentationOutput(translate({ key: "ui.0346a4b9846d" }, locale))}{presentationOutput(textJoin([textSymbol(""), textSymbol("")], " "))}
                            {presentationOutput(textNumber(warrior.games_to_miss, locale))}{presentationOutput(textJoin([textSymbol(""), textSymbol("")], " "))}
                            {presentationOutput(translate({ key: "ui.d30ff704135d" }, locale))}
                          </small>
                        ) : null}
                        {warrior.condition_detail && (
                          <small>
                            {presentationOutput(knowledgeName(knowledge, "injury", warrior.condition_detail, locale))}
                          </small>
                        )}
                      </>
                    ) : presentationOutput((
                      textSymbol("—")
                    ))}
                  </td>
                  <td data-label={presentationOutput(t.action)}>
                    {!record && !followUps.length && live ? (
                      <DiceResolver
                        key={`initial:${warrior.id}:${casualtyIndex}`}
                        count={usesHeroTable ? 2 : 1}
                        sides={6}
                        label={usesHeroTable ? t.hero : t.henchman}
                        locale={locale}
                        onResolve={(dice) => {
                          const roll = usesHeroTable ? dice[0] * 10 + dice[1] : dice[0];
                          const outcome = injuries.find(
                            (row) =>
                              row.applies_to === (usesHeroTable ? "hero" : "henchman") &&
                              inRange(row.roll, roll),
                          );
                          if (outcome)
                            void run("applyInjuryOutcome", {
                              warrior_id: warrior.id,
                              battle_number: battle.number,
                              casualty_index: casualtyIndex,
                              result_id: String(outcome.id),
                              result: String(outcome.result),
                              rolled_dice: dice,
                              roll,
                              effects: injuryEffects(outcome),
                            });
                        }}
                      />
                    ) : followUps.length && live ? (
                      followUps.map((follow) => {
                        const id = String(follow.id ?? "");
                        const type = String(follow.type ?? "");
                        if (
                          type === "encounter" &&
                          follow.encounter_id ===
                            "campaign.encounter.sold-to-the-pits"
                        )
                          return (
                            <span key={id}>
                              <b>{presentationOutput(t.pits)}</b>
                              <button
                                className="primary"
                                disabled={busy}
                                data-disabled-reason={(busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined) === undefined ? undefined : presentationOutput((busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined)!)}
                                onClick={() =>
                                  void run("resolveSoldToPits", {
                                    follow_up_id: id,
                                    won: true,
                                  })
                                }
                              >
                                {presentationOutput(t.won)}
                              </button>
                              <DiceResolver
                                count={2}
                                sides={6}
                                label={t.lost}
                                locale={locale}
                                onResolve={(dice) =>
                                  void run("resolveSoldToPits", {
                                    follow_up_id: id,
                                    won: false,
                                    dice,
                                    injury_roll: dice[0] * 10 + dice[1],
                                  })
                                }
                              />
                            </span>
                          );
                        if (type === "eye_injury")
                          return (
                            <span key={id}>
                              {presentationOutput(t.chooseEye)} {presentationOutput(textSymbol(":"))} {presentationOutput(textJoin([textSymbol(""), textSymbol("")], " "))}
                              <button
                                disabled={busy}
                                data-disabled-reason={(busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined) === undefined ? undefined : presentationOutput((busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined)!)}
                                onClick={() =>
                                  void run("resolveEyeInjury", {
                                    follow_up_id: id,
                                    eye: "left",
                                  })
                                }
                              >
                                {presentationOutput(t.left)}
                              </button>
                              <button
                                disabled={busy}
                                data-disabled-reason={(busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined) === undefined ? undefined : presentationOutput((busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined)!)}
                                onClick={() =>
                                  void run("resolveEyeInjury", {
                                    follow_up_id: id,
                                    eye: "right",
                                  })
                                }
                              >
                                {presentationOutput(t.right)}
                              </button>
                            </span>
                          );
                        if (type === "relationship")
                          return (
                            <span key={id}>
                              <input
                                aria-label={presentationOutput(t.hatred)}
                                value={targets[id] ?? ""}
                                onChange={(event) =>
                                  setTargets((current) => ({
                                    ...current,
                                    [id]: event.target.value,
                                  }))
                                }
                              />
                              <button
                                disabled={busy || !(targets[id] ?? "").trim()}
                                data-disabled-reason={(busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : !(targets[id] ?? "").trim() ? (translate({ key: "disabled.3662b59095" }, locale)) : undefined) === undefined ? undefined : presentationOutput((busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : !(targets[id] ?? "").trim() ? (translate({ key: "disabled.3662b59095" }, locale)) : undefined)!)}
                                onClick={() =>
                                  void run("resolveHatred", {
                                    follow_up_id: id,
                                    target: targets[id],
                                  })
                                }
                              >
                                {presentationOutput(t.setHatred)}
                              </button>
                            </span>
                          );
                        if (type === "prisoner")
                          return (
                            <span key={id}>
                              <NumberStepper locale={locale} label={translate({ key: "number.ransom" }, locale)} value={ransoms[id] ?? 0} onChange={(value) => setRansoms((current) => ({ ...current, [id]: value }))} />
                              {(
                                [
                                  ["ransom", t.ransom],
                                  ["exchange", t.exchange],
                                  ["lost", t.lostPrisoner],
                                ] as const
                              ).map(([resolution, label]) => (
                                <button
                                  key={resolution}
                                  disabled={busy}
                                  data-disabled-reason={(busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined) === undefined ? undefined : presentationOutput((busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined)!)}
                                  onClick={() =>
                                    void run("resolvePrisoner", {
                                      follow_up_id: id,
                                      resolution,
                                      ...(resolution === "ransom"
                                        ? { ransom: ransoms[id] ?? 0 }
                                        : resolution === "lost"
                                          ? { disposition: "other" }
                                          : {}),
                                    })
                                  }
                                >
                                  {presentationOutput(label)}
                                </button>
                              ))}
                            </span>
                          );
                        const dice = injuryFollowUpDice(knowledge, follow);
                        return dice ? (
                          <DiceResolver
                            key={`${id}:${String(follow.resolution_phase ?? follow.type ?? "follow-up")}`}
                            locale={locale}
                            count={dice[0]}
                            sides={dice[1]}
                            label={followUpLabel(follow, locale)}
                            onResolve={(rolls) =>
                              void run("resolveInjuryTableFollowUp", {
                                follow_up_id: id,
                                dice: rolls,
                                roll:
                                  dice[0] === 2 && dice[1] === 6
                                    ? rolls[0] * 10 + rolls[1]
                                    : rolls.reduce(
                                        (sum, value) => sum + value,
                                        0,
                                      ),
                              })
                            }
                          />
                        ) : (
                          <button
                            key={id}
                            disabled={busy}
                            data-disabled-reason={(busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined) === undefined ? undefined : presentationOutput((busy ? (translate({ key: "disabled.1b31e1c693" }, locale)) : undefined)!)}
                            onClick={() =>
                              void run("resolveInjuryFollowUp", {
                                follow_up_id: id,
                                outcome: {
                                  warrior_id: warrior.id,
                                  result_id: follow.result_id ?? "",
                                  result: "Resolved",
                                  effects: [],
                                },
                              })
                            }
                          >
                            {presentationOutput(t.follow)}
                          </button>
                        );
                      })
                    ) : (
                      <>{<span>{presentationOutput(Array.isArray(record?.rolled_dice) && record.rolled_dice.length > 0
                        ? textJoin([textJoin([t.roll, textSymbol(":")], ""), textJoin(record.rolled_dice.map((die) => textNumber(die, locale)), ", "), ...(Number.isInteger(record.roll) && record.rolled_dice.length > 1 ? [textSymbol("→"), textNumber(record.roll, locale)] : [])])
                        : t.resolved)}</span>}{followUpRolls.map((entry,index)=>{const dice=Array.isArray(entry.dice)?entry.dice:[];return <small key={index}>{presentationOutput(textJoin([textJoin([followUpLabel({resolution_phase:entry.phase},locale), textSymbol(":")], ""), t.roll, textJoin(dice.map((die) => textNumber(die, locale)), ", "), ...(Number.isInteger(entry.roll)&&dice.length>1 ? [textSymbol("→"), textNumber(entry.roll, locale)] : [])]))}</small>})}</>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </section>
  );
}

import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import { useState } from "react";
import { DiceResolver } from "../dice/DiceResolver";
import { useCampaignApp } from "../campaign/useCampaignApp";
import type { CampaignDocument } from "../campaign/types";
import {
  injuryEffects,
  injuryFollowUpDice,
} from "@app/campaign/features/injuries/injury-followup-workflow";
import { knowledgeName, readableValue } from "../campaign/displayText";
import { KnowledgeHint } from "../campaign/KnowledgeHint";
import { NumberStepper } from "../common/NumberStepper";

function inRange(spec: unknown, value: number): boolean {
  const text = String(spec ?? "");
  const [a, b] = text.split("-").map(Number);
  return (
    Number.isFinite(a) && value >= a && value <= (Number.isFinite(b) ? b : a)
  );
}

function followUpLabel(follow: Record<string, unknown>, locale: "es" | "en"): string {
  const phase = String(follow.resolution_phase ?? "");
  const number = Number(follow.repeat_index ?? 0) + 1;
  if (locale === "es") {
    if (phase === "effect_roll") return "Duración o intensidad del efecto";
    if (phase === "repeat_count") return "Cuántas heridas adicionales sufre";
    if (phase === "repeat_result") return `Herida adicional ${number} · D66`;
    if (phase === "subtable") return "Resultado secundario de la herida";
    return "Tirada necesaria para completar la herida";
  }
  if (phase === "effect_roll") return "Effect duration or severity";
  if (phase === "repeat_count") return "Number of additional injuries";
  if (phase === "repeat_result") return `Additional injury ${number} · D66`;
  if (phase === "subtable") return "Secondary injury result";
  return "Roll required to complete the injury";
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
  locale = "en",
}: {
  document: CampaignDocument;
  knowledge: ArtefactKnowledgeReader;
  locale?: "es" | "en";
}) {
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
    locale === "es"
      ? {
          title: "Heridas graves",
          none: "No se registraron guerreros fuera de combate.",
          hero: "Herida grave D66",
          henchman: "Herida de secuaz D6",
          warrior: "Guerrero",
          result: "Resultado y efectos",
          action: "Tiradas y decisiones pendientes",
          pits: "Vendido a los pozos",
          won: "Ganó",
          lost: "Perdió · herida grave D66",
          chooseEye: "Elige ojo",
          left: "Izquierdo",
          right: "Derecho",
          hatred: "Objetivo del odio",
          setHatred: "Establecer odio",
          ransom: "Rescate",
          exchange: "Intercambiar",
          lostPrisoner: "Perdido",
          follow: "Resolver seguimiento",
          resolved: "Sin acciones pendientes",
          roll: "Tirada",
        }
      : {
          title: "Serious injuries",
          none: "No warriors were recorded out of action.",
          hero: "D66 serious injury",
          henchman: "D6 henchman injury",
          warrior: "Warrior",
          result: "Result and effects",
          action: "Pending rolls and decisions",
          pits: "Sold to the Pits",
          won: "Won",
          lost: "Lost · D66 serious injury",
          chooseEye: "Choose eye",
          left: "Left",
          right: "Right",
          hatred: "Hatred target",
          setHatred: "Set hatred",
          ransom: "Ransom",
          exchange: "Exchange",
          lostPrisoner: "Lost",
          follow: "Resolve follow-up",
          resolved: "No pending actions",
          roll: "Roll",
        };
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
        name: String(participant?.name ?? id),
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
    <section aria-label={t.title}>
      <h3>01 · {t.title}</h3>
      {warriors.length === 0 ? (
        <p role="status">{t.none}</p>
      ) : (
        <table className="mobile-cards injury-results">
          <caption>{t.title}</caption>
          <thead>
            <tr>
              <th>{t.warrior}</th>
              <th>{t.result}</th>
              <th>{t.action}</th>
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
              const injury = injuries.find(
                (row) => String(row.id) === resultId,
              );
              const effect =
                (injury?.effects as Record<string, unknown> | undefined)?.[
                  locale
                ] ?? injury?.effect;
              return (
                <tr key={`${warrior.id}:${casualtyIndex}`}>
                  <td data-label={t.warrior}>
                    {warrior.name}
                    {casualtyIndex > 1 ? ` · ${casualtyIndex}` : ""}
                  </td>
                  <td data-label={t.result}>
                    {record ? (
                      <>
                        <strong>
                          <KnowledgeHint knowledge={knowledge} kind="injury" id={resultId} locale={locale}>
                            {knowledgeName(knowledge, "injury", resultId, locale, record.result)}
                          </KnowledgeHint>
                        </strong>
                        {effect && <small>{String(effect)}</small>}
                        {warrior.games_to_miss ? (
                          <small>
                            {locale === "es" ? "Pierde" : "Misses"}{" "}
                            {warrior.games_to_miss}{" "}
                            {locale === "es" ? "batalla(s)" : "game(s)"}
                          </small>
                        ) : null}
                        {warrior.condition_detail && (
                          <small>
                            {knowledgeName(knowledge, "injury", warrior.condition_detail, locale, readableValue(warrior.condition_detail, locale))}
                          </small>
                        )}
                      </>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td data-label={t.action}>
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
                              <b>{t.pits}</b>
                              <button
                                className="primary"
                                disabled={busy}
                                data-disabled-reason={busy ? (locale === "es" ? "Se está resolviendo otra herida." : "Another injury is being resolved.") : undefined}
                                onClick={() =>
                                  void run("resolveSoldToPits", {
                                    follow_up_id: id,
                                    won: true,
                                  })
                                }
                              >
                                {t.won}
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
                              {t.chooseEye}:{" "}
                              <button
                                disabled={busy}
                                data-disabled-reason={busy ? (locale === "es" ? "Se está resolviendo otra herida." : "Another injury is being resolved.") : undefined}
                                onClick={() =>
                                  void run("resolveEyeInjury", {
                                    follow_up_id: id,
                                    eye: "left",
                                  })
                                }
                              >
                                {t.left}
                              </button>
                              <button
                                disabled={busy}
                                data-disabled-reason={busy ? (locale === "es" ? "Se está resolviendo otra herida." : "Another injury is being resolved.") : undefined}
                                onClick={() =>
                                  void run("resolveEyeInjury", {
                                    follow_up_id: id,
                                    eye: "right",
                                  })
                                }
                              >
                                {t.right}
                              </button>
                            </span>
                          );
                        if (type === "relationship")
                          return (
                            <span key={id}>
                              <input
                                aria-label={`${t.hatred} ${id}`}
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
                                data-disabled-reason={busy ? (locale === "es" ? "Se está resolviendo otra herida." : "Another injury is being resolved.") : !(targets[id] ?? "").trim() ? (locale === "es" ? "Introduce primero el objetivo del odio." : "Enter the hatred target first.") : undefined}
                                onClick={() =>
                                  void run("resolveHatred", {
                                    follow_up_id: id,
                                    target: targets[id],
                                  })
                                }
                              >
                                {t.setHatred}
                              </button>
                            </span>
                          );
                        if (type === "prisoner")
                          return (
                            <span key={id}>
                              <NumberStepper label={`${t.ransom} ${id}`} value={ransoms[id] ?? 0} onChange={(value) => setRansoms((current) => ({ ...current, [id]: value }))} />
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
                                  data-disabled-reason={busy ? (locale === "es" ? "Se está resolviendo otra herida." : "Another injury is being resolved.") : undefined}
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
                                  {label}
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
                            data-disabled-reason={busy ? (locale === "es" ? "Se está resolviendo otra herida." : "Another injury is being resolved.") : undefined}
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
                            {t.follow}
                          </button>
                        );
                      })
                    ) : (
                      <>{<span>{Array.isArray(record?.rolled_dice) && record.rolled_dice.length > 0
                        ? `${t.roll}: ${record.rolled_dice.join(", ")}${Number.isInteger(record.roll) && record.rolled_dice.length > 1 ? ` → ${record.roll}` : ""}`
                        : t.resolved}</span>}{followUpRolls.map((entry,index)=>{const dice=Array.isArray(entry.dice)?entry.dice.map(Number):[];return <small key={index}>{followUpLabel({resolution_phase:entry.phase},locale)}: {t.roll} {dice.join(", ")}{Number.isInteger(entry.roll)&&dice.length>1?` → ${entry.roll}`:""}</small>})}</>
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

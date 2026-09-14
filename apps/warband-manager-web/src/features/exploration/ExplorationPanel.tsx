import { useState, type ReactNode } from "react";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import {
  explorationDiceCount,
  explorationDiscardCount,
  explorationModifiers,
} from "@app/campaign/features/exploration/exploration-workflow";
import type { OpenPayload } from "@domain/campaign/index";
import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { DiceResolver } from "../dice/DiceResolver";
import { knowledgeName, localizedLabel, readableValue } from "../campaign/displayText";

function visibleText(value: unknown, locale: "en" | "es", fallback: string): string {
  if (!value) return fallback;
  if (typeof value === "object") return readableValue(value, locale);
  const text = String(value);
  const es: Record<string, string> = { "Choose a Henchman group": "Elige un grupo de Secuaces", "Choose equipment": "Elige equipo", "Choose warriors": "Elige guerreros", "Do not recruit the prisoner": "No reclutar al prisionero" };
  return locale === "es" ? es[text] ?? (text.includes(".") ? localizedLabel(text, locale) : readableValue(text, locale)) : (text.includes(".") ? localizedLabel(text, locale) : readableValue(text, locale));
}

function matchingDice(dice: readonly number[]): readonly [number, number] | undefined {
  const counts = new Map<number, number>();
  for (const die of dice) counts.set(die, (counts.get(die) ?? 0) + 1);
  return [...counts].filter(([, count]) => count >= 2).sort((a, b) => b[1] - a[1] || b[0] - a[0])[0];
}

function describeCombination(dice: readonly number[], locale: "en" | "es"): string {
  const match = matchingDice(dice);
  if (!match) return locale === "es" ? "Sin resultados repetidos" : "No matching dice";
  const names = locale === "es"
    ? ["", "", "Doble", "Triple", "Cuádruple", "Quíntuple", "Séxtuple"]
    : ["", "", "Double", "Triple", "Quadruple", "Quintuple", "Sextuple"];
  return `${names[match[1]] ?? `${match[1]} iguales`} ${locale === "es" ? "de" : "of"} ${match[0]}`;
}

function eventDescription(knowledge: ArtefactKnowledgeReader, dice: readonly number[], locale: "en" | "es"): string {
  const match = matchingDice(dice);
  const rows = (knowledge.campaignSection("exploration-and-income")["exploration"] as OpenPayload | undefined)?.["results"] as OpenPayload[] | undefined;
  const row = match && rows?.find((entry) => entry["dice_pattern"] === Array.from({ length: match[1] }, () => match[0]).join(","));
  const translated = (row?.["description_i18n"] as OpenPayload | undefined)?.[locale];
  const description = translated ?? row?.["description"];
  return typeof description === "string" ? description : locale === "es" ? "No hay una descripción disponible para este evento." : "No description is available for this event.";
}

function eventLabel(knowledge: ArtefactKnowledgeReader, dice: readonly number[], locale: "en" | "es", fallback: string): string {
  const match = matchingDice(dice);
  const rows = (knowledge.campaignSection("exploration-and-income")["exploration"] as OpenPayload | undefined)?.["results"] as OpenPayload[] | undefined;
  const row = match && rows?.find((entry) => entry["dice_pattern"] === Array.from({ length: match[1] }, () => match[0]).join(","));
  return String((row?.["outcome_i18n"] as OpenPayload | undefined)?.[locale] ?? row?.["outcome"] ?? fallback);
}

function ExplorationDice({ dice, label, onSelect, controls }: { dice: readonly number[]; label: string; onSelect?: (index: number) => void; controls?: (index: number, die: number) => ReactNode }) {
  return <ol className="exploration-dice" aria-label={label}>{dice.map((die, index) => <li key={`${index}:${die}`}>{onSelect ? <button type="button" className="exploration-die-button" aria-label={`${label} D${index + 1}: ${die}`} onClick={() => onSelect(index)}><small>D{index + 1}</small><strong>{die}</strong></button> : <><small>D{index + 1}</small><strong>{die}</strong></>}{controls?.(index, die)}</li>)}</ol>;
}

export function ExplorationPanel({
  document,
  knowledge,
  locale = "en",
}: {
  readonly document: CampaignDocument;
  readonly knowledge: ArtefactKnowledgeReader;
  readonly locale?: "en" | "es";
}) {
  const app = useCampaignApp();
  const [warriorIds, setWarriorIds] = useState<string[]>([]);
  const [rolled, setRolled] = useState<number[] | null>(null);
  const [discarded, setDiscarded] = useState(0);
  const [fullReroll, setFullReroll] = useState(false);
  const [dieReroll, setDieReroll] = useState(0);
  const [adjusted, setAdjusted] = useState(0);
  const [rerollIndex, setRerollIndex] = useState<number | null>(null);
  const post = document.campaign.post_battles.find((row) => !row.complete);
  if (!post) return null;
  const t =
    locale === "es"
      ? {
          title: "Exploración",
          resolved: "Exploración resuelta",
          total: "total",
          special: "Resultado especial",
          result: "Resultado acumulado",
          action: "Siguiente tirada o decisión",
          first: "Resuelve antes la experiencia y todos los avances.",
          without: "Resolver exploración sin dados",
          discard: "Descarta un dado de exploración.",
          scenario: "El escenario permite repetir la tirada completa una vez.",
          catacombs: "Las catacumbas permiten repetir un dado una vez.",
          keep: "Conservar tirada",
          dice: "un dado por cada Héroe superviviente, más uno por victoria, limitado por la base de conocimiento.",
          roll: "Tirada de exploración",
          hero: "Elige un Héroe",
          select: "Selecciona…",
          outcome: "Elige un resultado",
          warriors: "Elige guerreros",
          confirm: "Confirmar",
          external: "Confirmar resolución de mesa",
          rerollAll: "Repetir todos los dados de exploración",
          rerollDie: "Repetir dado",
          discardDie: "Descartar D",
          followUpRoll: "Tirada de seguimiento",
          individualDice: "Resultados individuales de los dados",
          event: "Evento especial",
          modifiers: "Modificadores activos",
          adjust: "Modifica un dado en 1",
          consequence: "Consecuencia",
          subsequentRolls: "Tiradas posteriores",
          resolveFollowUp: "Resolver seguimiento de exploración",
        }
      : {
          title: "Exploration",
          resolved: "Exploration resolved",
          total: "total",
          special: "Special result",
          result: "Accumulated result",
          action: "Next roll or decision",
          first: "Resolve experience and all advances first.",
          without: "Resolve exploration without dice",
          discard: "Discard one exploration die.",
          scenario: "Scenario permits one complete reroll.",
          catacombs: "Catacombs permits one die reroll.",
          keep: "Keep original roll",
          dice: "one die per surviving Hero, plus one for winning, capped by KB.",
          roll: "Exploration roll",
          hero: "Choose a Hero",
          select: "Select…",
          outcome: "Choose an outcome",
          warriors: "Choose warriors",
          confirm: "Confirm",
          external: "Confirm table-side resolution",
          rerollAll: "Reroll all exploration dice",
          rerollDie: "Reroll exploration die",
          discardDie: "Discard D",
          followUpRoll: "Follow-up roll",
          individualDice: "Individual dice results",
          event: "Special event",
          modifiers: "Active modifiers",
          adjust: "Modify one die by 1",
          consequence: "Consequence",
          subsequentRolls: "Subsequent rolls",
          resolveFollowUp: "Resolve exploration follow-up",
        };
  const advances = (post.pending_advances ?? []).some(
    (row) => !row["committed"],
  );
  const state = post.step_state?.["exploration"] as OpenPayload | undefined;
  const count = explorationDiceCount(document, knowledge);
  const modifiers = explorationModifiers(document, knowledge);
  const discard = explorationDiscardCount(document, knowledge);
  const scenario = post.step_state?.["scenario_exploration"] as
    | OpenPayload
    | undefined;
  const full = Boolean(scenario?.["reroll_all"]);
  const legacyReroll = document.campaign.special_rules.some((row) =>
    /re-roll one die|repite un dado/i.test(String(row["text"] ?? "")),
  );
  const rerolls = modifiers.rerolls + (legacyReroll ? 1 : 0);
  const followup = post.pending_follow_ups?.find(
    (row) => row["type"] === "exploration_followup",
  );
  const pending = followup?.["pending"] as OpenPayload | undefined;
  const resolvedDice = Array.isArray(state?.["dice"])
    ? (state["dice"] as unknown[]).map(Number)
    : [];
  const specialEffects = Array.isArray(state?.["special_effects"])
    ? (state["special_effects"] as unknown[]).filter((effect): effect is string => typeof effect === "string")
    : [];
  const followUpRolls = Array.isArray(state?.["follow_up_rolls"])
    ? state["follow_up_rolls"] as OpenPayload[]
    : [];
  const apply = (dice: readonly number[]) => {
    void app.runAction("applyExploration", { dice });
    setRolled(null);
    setDiscarded(0);
    setFullReroll(false);
    setDieReroll(0);
    setAdjusted(0);
    setRerollIndex(null);
  };
  return (
    <section aria-label={t.title}>
      <h3>03 · {t.title}</h3>
      {modifiers.sources.length > 0 && <aside className="exploration-modifiers"><strong>{t.modifiers}</strong><ul>{modifiers.sources.map((source) => <li key={source.id}><b>{knowledgeName(knowledge, "rule", source.id, locale, locale === "es" ? source.label_es ?? source.label : source.label)}</b>{(locale === "es" ? source.effect_es ?? source.effect : source.effect) && <small>{locale === "es" ? source.effect_es ?? source.effect : source.effect}</small>}</li>)}</ul></aside>}
      <table className="mobile-cards exploration-results">
        <caption>{t.title}</caption>
        <thead>
          <tr>
            <th>{t.result}</th>
            <th>{t.action}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td data-label={t.result}>
              {state?.["resolved"] ? (
                <>
                  <strong>
                    {String(state["shards"])}{" "}
                    {locale === "es"
                      ? "fragmentos de piedra bruja"
                      : "wyrdstone shards"}
                  </strong>
                  <small>
                    {String(state["dice_count"])}{" "}
                    {locale === "es" ? "dados" : "dice"} · {t.total}{" "}
                    {String(state["total"])}
                  </small>
                  {resolvedDice.length > 0 && <ExplorationDice dice={resolvedDice} label={t.individualDice} />}
                  {resolvedDice.length > 0 && <div className={`exploration-combination${state["special"] ? " special" : ""}`}><strong>{describeCombination(resolvedDice, locale)}</strong><span>{state["special"] ? <>{t.event}: <span className="knowledge-hint" tabIndex={0} data-tooltip={eventDescription(knowledge, resolvedDice, locale)}>{eventLabel(knowledge, resolvedDice, locale, String(state["special"]))}</span></> : t.special + ": —"}</span>{specialEffects.length > 0 && <ul className="exploration-effects">{specialEffects.map((effect, index) => <li key={`${index}:${effect}`}>{effect}</li>)}</ul>}</div>}
                </>
              ) : (
                <span>—</span>
              )}
              {followup &&
                Array.isArray(followup["messages"]) &&
                (followup["messages"] as string[]).map((message) => (
                  <small key={message}>{message}</small>
                ))}
            </td>
            <td data-label={t.action}>
              {state?.["resolved"] ? (
                !followup && <><span role="status">{resolvedDice.length ? `${t.roll}: ${resolvedDice.join(", ")} → ${state["total"]}` : t.resolved}</span>{followUpRolls.length > 0 && <section className="exploration-roll-history" aria-label={t.subsequentRolls}>{followUpRolls.map((row, index) => { const dice=Array.isArray(row["dice"]) ? (row["dice"] as unknown[]).map(Number) : []; return <div key={`${index}:${String(row["total"])}`}><strong>{visibleText(row["label"], locale, `${t.followUpRoll} ${index + 1}`)}</strong><span>{dice.length ? `${dice.join(", ")} → ` : ""}{String(row["total"] ?? "—")}</span></div>; })}</section>}</>
              ) : !post.experience_applied || advances ? (
                <p role="status">{t.first}</p>
              ) : count === 0 ? (
                <button className="primary" onClick={() => apply([])}>
                  {t.without}
                </button>
              ) : rolled && discarded < discard ? (
                <div>
                  <p>{t.discard}</p>
                  <ExplorationDice dice={rolled} label={t.discardDie} onSelect={(index) => {
                        const kept = rolled.filter((_, item) => item !== index);
                        if (discarded + 1 < discard || full || rerolls || modifiers.adjustments) {
                          setRolled(kept);
                          setDiscarded((value) => value + 1);
                        } else apply(kept);
                      }} />
                </div>
              ) : rolled && full && !fullReroll ? (
                <div>
                  <p>{t.scenario}</p>
                  <ExplorationDice dice={rolled} label={t.individualDice} />
                  <DiceResolver
                    locale={locale}
                    count={rolled.length}
                    sides={6}
                    label={t.rerollAll}
                    onResolve={(dice) => {
                      if (rerolls || modifiers.adjustments) {
                        setRolled(dice);
                        setFullReroll(true);
                      } else apply(dice);
                    }}
                  />
                  <button
                    onClick={() =>
                      rerolls || modifiers.adjustments ? setFullReroll(true) : apply(rolled)
                    }
                  >
                    {t.keep}
                  </button>
                </div>
              ) : rolled && dieReroll < rerolls ? (
                <div>
                  <p>{t.catacombs}</p>
                  {rerollIndex === null ? (
                    <ExplorationDice dice={rolled} label={t.rerollDie} onSelect={setRerollIndex} />
                  ) : (
                    <DiceResolver
                      locale={locale}
                      count={1}
                      sides={6}
                      label={t.rerollDie}
                      onResolve={(dice) => {
                        const next = rolled.map((die, index) => index === rerollIndex ? dice[0] : die);
                        if (dieReroll + 1 >= rerolls && !modifiers.adjustments) apply(next);
                        else { setRolled(next); setDieReroll((value) => value + 1); }
                        setRerollIndex(null);
                      }}
                    />
                  )}
                  <button onClick={() => modifiers.adjustments ? setDieReroll(rerolls) : apply(rolled)}>{t.keep}</button>
                </div>
              ) : rolled && adjusted < modifiers.adjustments ? (
                <div className="exploration-adjustment">
                  <p>{t.adjust} ({adjusted + 1}/{modifiers.adjustments})</p>
                  <ExplorationDice dice={rolled} label={t.adjust} controls={(index, die) => <span className="exploration-die-controls">{([-1, 1] as const).map((delta) => { const blocked = delta < 0 ? die <= 1 : die >= 6; return <button key={delta} className="stepper-button" aria-label={`${delta < 0 ? (locale === "es" ? "Restar uno al dado" : "Subtract one from die") : (locale === "es" ? "Sumar uno al dado" : "Add one to die")} ${index + 1}`} disabled={blocked} data-disabled-reason={blocked ? delta < 0 ? (locale === "es" ? "El dado ya tiene el valor mínimo de 1." : "The die is already at the minimum value of 1.") : (locale === "es" ? "El dado ya tiene el valor máximo de 6." : "The die is already at the maximum value of 6.") : undefined} onClick={() => { const next = rolled.map((value, position) => position === index ? value + delta : value); if (adjusted + 1 >= modifiers.adjustments) apply(next); else { setRolled(next); setAdjusted((value) => value + 1); } }}>{delta < 0 ? "−" : "+"}</button>; })}</span>} />
                  <button onClick={() => apply(rolled)}>{t.keep}</button>
                </div>
              ) : rolled ? null : (
                <>
                  <p>
                    {count}D6: {t.dice}
                  </p>
                  <DiceResolver
                    locale={locale}
                    count={count}
                    sides={6}
                    label={t.roll}
                    onResolve={(dice) =>
                      discard || full || rerolls || modifiers.adjustments ? setRolled(dice) : apply(dice)
                    }
                  />
                </>
              )}
              {pending?.["kind"] === "roll" && (
                <DiceResolver
                  locale={locale}
                  count={Number(pending["dice_count"] ?? 1)}
                  sides={Number(pending["dice_sides"] ?? 6)}
                  label={visibleText(pending["label"], locale, t.followUpRoll)}
                  onResolve={(dice) =>
                    void app.runAction("continueExploration", {
                      roll: dice.reduce((sum, item) => sum + item, 0),
                      dice,
                    })
                  }
                />
              )}
              {followup && !pending && Boolean(state?.["resolved"]) && (
                <button type="button" onClick={() => void app.runAction("continueExploration", {})}>{t.resolveFollowUp}</button>
              )}
              {pending?.["kind"] === "choose_hero" && (
                <label>
                  {visibleText(pending["label"], locale, t.hero)}
                  <select
                    defaultValue=""
                    onChange={(event) => {
                      if (event.target.value)
                        void app.runAction("continueExploration", {
                          hero_id: event.target.value,
                        });
                    }}
                  >
                    <option value="" disabled>
                      {t.select}
                    </option>
                    {document.campaign.warriors
                      .filter((row) => row.kind === "hero")
                      .sort((a, b) => a.name.localeCompare(b.name, locale))
                      .map((row) => (
                        <option key={row.id} value={row.id}>
                          {row.name}
                        </option>
                      ))}
                  </select>
                </label>
              )}
              {pending?.["kind"] === "choose_option" && (
                <div>
                  <p><strong>{t.consequence}:</strong> {visibleText(pending["label"], locale, t.outcome)}</p>
                  {((pending["options"] ?? []) as OpenPayload[]).map(
                    (option) => (
                      <button
                        key={String(option["id"])}
                        onClick={() =>
                          void app.runAction("continueExploration", {
                            option_id: option["id"],
                          })
                        }
                      >
                        {visibleText(option["label"] ?? option["id"], locale, t.outcome)}
                      </button>
                    ),
                  )}
                </div>
              )}
              {pending?.["kind"] === "choose_warriors" && (
                <fieldset>
                  <legend>{visibleText(pending["label"], locale, t.warriors)}</legend>
                  {((pending["options"] ?? []) as OpenPayload[]).map(
                    (option) => {
                      const id = String(option["id"]),
                        checked = warriorIds.includes(id),
                        maximum = Number(pending["maximum"] ?? 1);
                      return (
                        <label key={id}>
                          <input
                            type="checkbox"
                            checked={checked}
                            disabled={!checked && warriorIds.length >= maximum}
                            data-disabled-reason={
                              !checked && warriorIds.length >= maximum
                                ? locale === "es"
                                  ? `Solo puedes seleccionar ${maximum} guerrero(s).`
                                  : `You can only select ${maximum} warrior(s).`
                                : undefined
                            }
                            onChange={() =>
                              setWarriorIds((current) =>
                                checked
                                  ? current.filter((value) => value !== id)
                                  : [...current, id],
                              )
                            }
                          />
                          {visibleText(option["label"] ?? id, locale, id)}
                        </label>
                      );
                    },
                  )}
                  <button
                    type="button"
                    onClick={() => {
                      void app.runAction("continueExploration", {
                        warrior_ids: warriorIds,
                      });
                      setWarriorIds([]);
                    }}
                  >
                    {t.confirm}
                  </button>
                </fieldset>
              )}
              {pending?.["kind"] === "external" && (
                <button
                  onClick={() =>
                    void app.runAction("continueExploration", {
                      confirm_external: true,
                    })
                  }
                >
                  {visibleText(pending["label"], locale, t.external)}
                </button>
              )}
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}

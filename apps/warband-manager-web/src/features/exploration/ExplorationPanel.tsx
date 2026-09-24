import { textDice, textDieIndex, textJoin, textNumber, textSymbol, warriorPersonalName, type PresentationValue } from "../campaign/presentation-values";
import { presentationOutput } from "../campaign/presentation-output";
import { translate, uiMessageForText } from "../campaign/i18n-core";
import { useLocale } from "../campaign/i18n-context";
import { useState, type ReactElement } from "react";
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
import { knowledgeName, knowledgeDescription, warriorAbilityRef, localizedLabel, readableValue, numberText } from "../campaign/displayText";

function legacyVisibleText(value: unknown, locale: "en" | "es", fallback: PresentationValue, knowledge: ArtefactKnowledgeReader): PresentationValue {
  if (!value) return fallback;
  if (typeof value !== "string") return translate({ key: "knowledge.unavailable" }, locale);
  const resourceReward = /^(gold_crowns|wyrdstone_fragments) reward$/.exec(value)?.[1];
  if (resourceReward) return translate({ key: "exploration.resource-reward", args: { resource: readableValue(resourceReward, locale) } }, locale);
  const message = uiMessageForText(value);
  return message ? translate(message, locale) : knowledge.legacyText(value, locale);
}

function matchingDice(dice: readonly number[]): readonly [number, number] | undefined {
  const counts = new Map<number, number>();
  for (const die of dice) counts.set(die, (counts.get(die) ?? 0) + 1);
  return [...counts].filter(([, count]) => count >= 2).sort((a, b) => b[1] - a[1] || b[0] - a[0])[0];
}

function describeCombination(dice: readonly number[], locale: "en" | "es"): PresentationValue {
  const match = matchingDice(dice);
  if (!match) return translate({ key: "ui.692fe81fbd98" }, locale);
  const count = match[1] === 2 ? translate({ key: "exploration.match-2" }, locale)
    : match[1] === 3 ? translate({ key: "exploration.match-3" }, locale)
    : match[1] === 4 ? translate({ key: "exploration.match-4" }, locale)
    : match[1] === 5 ? translate({ key: "exploration.match-5" }, locale)
    : match[1] === 6 ? translate({ key: "exploration.match-6" }, locale)
    : translate({ key: "knowledge.unavailable" }, locale);
  return textJoin([count, translate({ key: "ui.efeae3b09c13" }, locale), textNumber(match[0], locale)]);
}

function eventDescription(knowledge: ArtefactKnowledgeReader, dice: readonly number[], locale: "en" | "es"): PresentationValue {
  const match = matchingDice(dice);
  const rows = (knowledge.campaignSection("exploration-and-income")["exploration"] as OpenPayload | undefined)?.["results"] as OpenPayload[] | undefined;
  const row = match && rows?.find((entry) => entry["dice_pattern"] === Array.from({ length: match[1] }, () => match[0]).join(","));
  return row ? knowledge.recordText(row, "description", locale) : translate({ key: "ui.ecba50eadf0e" }, locale);
}

function eventLabel(knowledge: ArtefactKnowledgeReader, dice: readonly number[], locale: "en" | "es"): PresentationValue {
  const match = matchingDice(dice);
  const rows = (knowledge.campaignSection("exploration-and-income")["exploration"] as OpenPayload | undefined)?.["results"] as OpenPayload[] | undefined;
  const row = match && rows?.find((entry) => entry["dice_pattern"] === Array.from({ length: match[1] }, () => match[0]).join(","));
  return row ? knowledge.recordText(row, "outcome", locale) : localizedLabel(undefined, locale);
}

function ExplorationDice({ dice, diceLabel, locale, onSelect, controls }: { dice: readonly number[]; diceLabel: PresentationValue; locale: "en" | "es"; onSelect?: (index: number) => void; controls?: (index: number, die: number) => ReactElement }) {
  return <ol className="exploration-dice" aria-label={presentationOutput(diceLabel)}>{dice.map((die, index) => <li key={`${index}:${die}`}>{onSelect ? <button type="button" className="exploration-die-button" aria-label={presentationOutput(textJoin([diceLabel, textJoin([textDieIndex(index + 1, locale), textSymbol(":")], ""), textNumber(die, locale)]))} onClick={() => onSelect(index)}><small>{presentationOutput(textDieIndex(index + 1, locale))}</small><strong>{presentationOutput(textNumber(die, locale))}</strong></button> : <><small>{presentationOutput(textDieIndex(index + 1, locale))}</small><strong>{presentationOutput(textNumber(die, locale))}</strong></>}{controls?.(index, die)}</li>)}</ol>;
}

export function ExplorationPanel({
  document,
  knowledge,
  locale: requestedLocale,
}: {
  readonly document: CampaignDocument;
  readonly knowledge: ArtefactKnowledgeReader;
  readonly locale?: "en" | "es";
}) {
  const locale = useLocale(requestedLocale);
  const app = useCampaignApp();
  const visibleText = (value: unknown, language: "es" | "en", fallback: PresentationValue) => legacyVisibleText(value, language, fallback, knowledge);
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
    ({ title: translate({ key: "ui.5bf1692aa621" }, locale), resolved: translate({ key: "ui.cdd14047d5f6" }, locale), total: translate({ key: "ui.f551182ae6a0" }, locale), special: translate({ key: "ui.743a8177f02b" }, locale), result: translate({ key: "ui.a5127d058a48" }, locale), action: translate({ key: "ui.c956f9541ce5" }, locale), first: translate({ key: "ui.4e85c8f409de" }, locale), without: translate({ key: "ui.30bb22d50583" }, locale), discard: translate({ key: "ui.bc42956ad806" }, locale), scenario: translate({ key: "ui.2c8b621aea7d" }, locale), catacombs: translate({ key: "ui.7b51dacc55c7" }, locale), keep: translate({ key: "ui.f59bbbadd021" }, locale), dice: translate({ key: "ui.52d50aa13cef" }, locale), roll: translate({ key: "ui.23892575ed27" }, locale), hero: translate({ key: "ui.ebb717ab42ca" }, locale), select: translate({ key: "ui.9f79f4628ec5" }, locale), outcome: translate({ key: "ui.50ee2cd039b4" }, locale), warriors: translate({ key: "ui.f4f95e43f6a6" }, locale), confirm: translate({ key: "ui.bfc76e0e56e3" }, locale), external: translate({ key: "ui.61b365765bf6" }, locale), rerollAll: translate({ key: "ui.645311e03ef0" }, locale), rerollDie: translate({ key: "ui.690b587d68fc" }, locale), discardDie: translate({ key: "ui.1629187bed22" }, locale), followUpRoll: translate({ key: "ui.4543309924a6" }, locale), individualDice: translate({ key: "ui.353c21c9a9a0" }, locale), event: translate({ key: "ui.06e887c866e0" }, locale), modifiers: translate({ key: "ui.9da5a0182084" }, locale), adjust: translate({ key: "ui.fa790028af6c" }, locale), consequence: translate({ key: "ui.1f106c252cb7" }, locale), subsequentRolls: translate({ key: "ui.5ec01329bf1e" }, locale), resolveFollowUp: translate({ key: "ui.32d95dd4b003" }, locale) });
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
    <section aria-label={presentationOutput(t.title)}>
      <h3>{presentationOutput(textJoin([textNumber(3, locale, 2), t.title], " · "))}</h3>
      {modifiers.sources.length > 0 && <aside className="exploration-modifiers"><strong>{presentationOutput(t.modifiers)}</strong><ul>{modifiers.sources.map((source) => { const ref = warriorAbilityRef(knowledge, source.id, source.profileId, source.bandId); return <li key={source.id}><b>{presentationOutput(knowledgeName(knowledge, ref.kind, ref.id, locale, ref.profileId, ref.bandId))}</b><small>{presentationOutput(knowledgeDescription(knowledge, ref, locale).text)}</small></li>; })}</ul></aside>}
      <table className="mobile-cards exploration-results">
        <caption>{presentationOutput(t.title)}</caption>
        <thead>
          <tr>
            <th>{presentationOutput(t.result)}</th>
            <th>{presentationOutput(t.action)}</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td data-label={presentationOutput(t.result)}>
              {state?.["resolved"] ? (
                <>
                  <strong>{presentationOutput(textJoin([numberText(state["shards"], locale), translate({ key: "ui.7772bcce444d" }, locale)]))}</strong>
                  <small>{presentationOutput(textJoin([numberText(state["dice_count"], locale), translate({ key: "ui.1d13e4a9ecdf" }, locale), textSymbol("·"), t.total, numberText(state["total"], locale)]))}</small>
                  {resolvedDice.length > 0 && <ExplorationDice dice={resolvedDice} diceLabel={t.individualDice} locale={locale} />}
                  {resolvedDice.length > 0 && <div className={`exploration-combination${state["special"] ? " special" : ""}`}><strong>{presentationOutput(describeCombination(resolvedDice, locale))}</strong><span>{state["special"] ? <>{presentationOutput(t.event)} {presentationOutput(textSymbol(":"))} <span className="knowledge-hint" tabIndex={0} data-tooltip={presentationOutput(eventDescription(knowledge, resolvedDice, locale))}>{presentationOutput(eventLabel(knowledge, resolvedDice, locale))}</span></> : presentationOutput(textJoin([t.special, textSymbol(":"), textSymbol("—")]))}</span>{specialEffects.length > 0 && <ul className="exploration-effects">{specialEffects.map((effect, index) => <li key={`${index}:${effect}`}>{presentationOutput(visibleText(effect, locale, translate({ key: "knowledge.unavailable" }, locale)))}</li>)}</ul>}</div>}
                </>
              ) : (
                <span>{presentationOutput(textSymbol("—"))}</span>
              )}
              {followup &&
                Array.isArray(followup["messages"]) &&
                (followup["messages"] as string[]).map((message) => (
                  <small key={message}>{presentationOutput(visibleText(message, locale, translate({ key: "knowledge.unavailable" }, locale)))}</small>
                ))}
            </td>
            <td data-label={presentationOutput(t.action)}>
              {state?.["resolved"] ? (
                !followup && <><span role="status">{presentationOutput(resolvedDice.length ? textJoin([textJoin([t.roll, textSymbol(":")], ""), textJoin(resolvedDice.map((die) => textNumber(die, locale)), ", "), textSymbol("→"), textNumber(state["total"], locale)]) : t.resolved)}</span>{followUpRolls.length > 0 && <section className="exploration-roll-history" aria-label={presentationOutput(t.subsequentRolls)}>{followUpRolls.map((row, index) => { const dice=Array.isArray(row["dice"]) ? (row["dice"] as unknown[]).map(Number) : []; return <div key={`${index}:${String(row["total"])}`}><strong>{presentationOutput(visibleText(row["label"], locale, textJoin([t.followUpRoll, textNumber(index + 1, locale)])))}</strong><span>{presentationOutput(textJoin([...(dice.length ? [textJoin(dice.map((die) => textNumber(die, locale)), ", "), textSymbol("→")] : []), textNumber(row["total"], locale)]))}</span></div>; })}</section>}</>
              ) : !post.experience_applied || advances ? (
                <p role="status">{presentationOutput(t.first)}</p>
              ) : count === 0 ? (
                <button className="primary" onClick={() => apply([])}>
                  {presentationOutput(t.without)}
                </button>
              ) : rolled && discarded < discard ? (
                <div>
                  <p>{presentationOutput(t.discard)}</p>
                  <ExplorationDice dice={rolled} diceLabel={t.discardDie} locale={locale} onSelect={(index) => {
                        const kept = rolled.filter((_, item) => item !== index);
                        if (discarded + 1 < discard || full || rerolls || modifiers.adjustments) {
                          setRolled(kept);
                          setDiscarded((value) => value + 1);
                        } else apply(kept);
                      }} />
                </div>
              ) : rolled && full && !fullReroll ? (
                <div>
                  <p>{presentationOutput(t.scenario)}</p>
                  <ExplorationDice dice={rolled} diceLabel={t.individualDice} locale={locale} />
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
                    {presentationOutput(t.keep)}
                  </button>
                </div>
              ) : rolled && dieReroll < rerolls ? (
                <div>
                  <p>{presentationOutput(t.catacombs)}</p>
                  {rerollIndex === null ? (
                    <ExplorationDice dice={rolled} diceLabel={t.rerollDie} locale={locale} onSelect={setRerollIndex} />
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
                  <button onClick={() => modifiers.adjustments ? setDieReroll(rerolls) : apply(rolled)}>{presentationOutput(t.keep)}</button>
                </div>
              ) : rolled && adjusted < modifiers.adjustments ? (
                <div className="exploration-adjustment">
                  <p>{presentationOutput(t.adjust)} {presentationOutput(textSymbol("("))}{presentationOutput(textNumber(adjusted + 1, locale))}{presentationOutput(textSymbol("/"))}{presentationOutput(textNumber(modifiers.adjustments, locale))}{presentationOutput(textSymbol(")"))}</p>
                  <ExplorationDice dice={rolled} diceLabel={t.adjust} locale={locale} controls={(index, die) => <span className="exploration-die-controls">{([-1, 1] as const).map((delta) => { const blocked = delta < 0 ? die <= 1 : die >= 6; const actionLabel = delta < 0 ? translate({ key: "ui.019b837428b3" }, locale) : translate({ key: "ui.a253df792358" }, locale); const reason = delta < 0 ? translate({ key: "disabled.996512b73d" }, locale) : translate({ key: "disabled.49d66fa8cf" }, locale); return <button key={delta} className="stepper-button" aria-label={presentationOutput(textJoin([actionLabel, textNumber(index + 1, locale)]))} disabled={blocked} data-disabled-reason={blocked ? presentationOutput(reason) : undefined} onClick={() => { const next = rolled.map((value, position) => position === index ? value + delta : value); if (adjusted + 1 >= modifiers.adjustments) apply(next); else { setRolled(next); setAdjusted((value) => value + 1); } }}>{presentationOutput(textSymbol(delta < 0 ? "−" : "+"))}</button>; })}</span>} />
                  <button onClick={() => apply(rolled)}>{presentationOutput(t.keep)}</button>
                </div>
              ) : rolled ? null : (
                <>
                  <p>
                    {presentationOutput(textDice(count, 6, locale))}{presentationOutput(textSymbol(":"))} {presentationOutput(t.dice)}
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
                <button type="button" onClick={() => void app.runAction("continueExploration", {})}>{presentationOutput(t.resolveFollowUp)}</button>
              )}
              {pending?.["kind"] === "choose_hero" && (
                <label>
                  {presentationOutput(visibleText(pending["label"], locale, t.hero))}
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
                      {presentationOutput(t.select)}
                    </option>
                    {document.campaign.warriors
                      .filter((row) => row.kind === "hero")
                      .sort((a, b) => a.name.localeCompare(b.name, locale))
                      .map((row) => (
                        <option key={row.id} value={row.id}>
                          {presentationOutput(warriorPersonalName(row, locale))}
                        </option>
                      ))}
                  </select>
                </label>
              )}
              {pending?.["kind"] === "choose_option" && (
                <div>
                  <p><strong>{presentationOutput(t.consequence)} {presentationOutput(textSymbol(":"))} </strong> {presentationOutput(visibleText(pending["label"], locale, t.outcome))}</p>
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
                        {presentationOutput(visibleText(option["label"], locale, t.outcome))}
                      </button>
                    ),
                  )}
                </div>
              )}
              {pending?.["kind"] === "choose_warriors" && (
                <fieldset>
                  <legend>{presentationOutput(visibleText(pending["label"], locale, t.warriors))}</legend>
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
                            data-disabled-reason={!checked && warriorIds.length >= maximum ? presentationOutput(translate({ key: "exploration.maximum-warriors", args: { maximum } }, locale)) : undefined}
                            onChange={() =>
                              setWarriorIds((current) =>
                                checked
                                  ? current.filter((value) => value !== id)
                                  : [...current, id],
                              )
                            }
                          />
                          {presentationOutput(warriorPersonalName(document.campaign.warriors.find((warrior) => warrior.id === id), locale))}
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
                    {presentationOutput(t.confirm)}
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
                  {presentationOutput(visibleText(pending["label"], locale, t.external))}
                </button>
              )}
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}

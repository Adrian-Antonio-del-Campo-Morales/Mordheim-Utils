import { useState } from "react";
import type { ArtefactKnowledgeReader } from "@adapters/knowledge-reader/index";
import {
  explorationDiceCount,
  explorationDiscardRequired,
} from "@app/campaign/features/exploration/exploration-workflow";
import type { OpenPayload } from "@domain/campaign/index";
import type { CampaignDocument } from "../campaign/types";
import { useCampaignApp } from "../campaign/useCampaignApp";
import { DiceResolver } from "../dice/DiceResolver";

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
  const [discarded, setDiscarded] = useState(false);
  const [fullReroll, setFullReroll] = useState(false);
  const [dieReroll, setDieReroll] = useState(false);
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
        };
  const advances = (post.pending_advances ?? []).some(
    (row) => !row["committed"],
  );
  const state = post.step_state?.["exploration"] as OpenPayload | undefined;
  const count = explorationDiceCount(document, knowledge);
  const discard = explorationDiscardRequired(document);
  const scenario = post.step_state?.["scenario_exploration"] as
    | OpenPayload
    | undefined;
  const full = Boolean(scenario?.["reroll_all"]);
  const reroll = document.campaign.special_rules.some((row) =>
    /re-roll one die|repite un dado/i.test(String(row["text"] ?? "")),
  );
  const followup = post.pending_follow_ups?.find(
    (row) => row["type"] === "exploration_followup",
  );
  const pending = followup?.["pending"] as OpenPayload | undefined;
  const apply = (dice: readonly number[]) => {
    void app.runAction("applyExploration", { dice });
    setRolled(null);
    setDiscarded(false);
    setFullReroll(false);
    setDieReroll(false);
    setRerollIndex(null);
  };
  return (
    <section aria-label={t.title}>
      <h3>03 · {t.title}</h3>
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
                  {state["special"] && (
                    <small>
                      {t.special}: {String(state["special"])}
                    </small>
                  )}
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
                !followup && <span role="status">{t.resolved}</span>
              ) : !post.experience_applied || advances ? (
                <p role="status">{t.first}</p>
              ) : count === 0 ? (
                <button className="primary" onClick={() => apply([])}>
                  {t.without}
                </button>
              ) : rolled && discard && !discarded ? (
                <div>
                  <p>{t.discard}</p>
                  {rolled.map((die, index) => (
                    <button
                      key={`${index}:${die}`}
                      onClick={() => {
                        const kept = rolled.filter((_, item) => item !== index);
                        if (full || reroll) {
                          setRolled(kept);
                          setDiscarded(true);
                        } else apply(kept);
                      }}
                    >
                      {t.discardDie} D{index + 1}: {die}
                    </button>
                  ))}
                </div>
              ) : rolled && full && !fullReroll ? (
                <div>
                  <p>{t.scenario}</p>
                  <DiceResolver
                    locale={locale}
                    count={rolled.length}
                    sides={6}
                    label={t.rerollAll}
                    onResolve={(dice) => {
                      if (reroll) {
                        setRolled(dice);
                        setFullReroll(true);
                      } else apply(dice);
                    }}
                  />
                  <button
                    onClick={() =>
                      reroll ? setFullReroll(true) : apply(rolled)
                    }
                  >
                    {t.keep}
                  </button>
                </div>
              ) : rolled && reroll && !dieReroll ? (
                <div>
                  <p>{t.catacombs}</p>
                  {rerollIndex === null ? (
                    rolled.map((die, index) => (
                      <button
                        key={`${index}:${die}`}
                        onClick={() => setRerollIndex(index)}
                      >
                        {t.rerollDie} D{index + 1}: {die}
                      </button>
                    ))
                  ) : (
                    <DiceResolver
                      locale={locale}
                      count={1}
                      sides={6}
                      label={t.rerollDie}
                      onResolve={(dice) => {
                        apply(
                          rolled.map((die, index) =>
                            index === rerollIndex ? dice[0] : die,
                          ),
                        );
                      }}
                    />
                  )}
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
                      discard || full || reroll ? setRolled(dice) : apply(dice)
                    }
                  />
                </>
              )}
              {pending?.["kind"] === "roll" && (
                <DiceResolver
                  locale={locale}
                  count={Number(pending["dice_count"] ?? 1)}
                  sides={Number(pending["dice_sides"] ?? 6)}
                  label={String(pending["label"] ?? t.followUpRoll)}
                  onResolve={(dice) =>
                    void app.runAction("continueExploration", {
                      roll: dice.reduce((sum, item) => sum + item, 0),
                    })
                  }
                />
              )}
              {pending?.["kind"] === "choose_hero" && (
                <label>
                  {String(pending["label"] ?? t.hero)}
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
                  <p>{String(pending["label"] ?? t.outcome)}</p>
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
                        {String(option["label"] ?? option["id"])}
                      </button>
                    ),
                  )}
                </div>
              )}
              {pending?.["kind"] === "choose_warriors" && (
                <fieldset>
                  <legend>{String(pending["label"] ?? t.warriors)}</legend>
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
                          {String(option["label"] ?? id)}
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
                  {String(pending["label"] ?? t.external)}
                </button>
              )}
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}

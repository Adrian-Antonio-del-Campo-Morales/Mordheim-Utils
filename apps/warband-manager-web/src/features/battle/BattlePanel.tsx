/**
 * P6.4 (plan §7): battle recording UI. Shown for committed campaigns: the
 * scenario/opponent/loot form, availability-driven out-of-action selection,
 * and the pending post-battle step navigation.
 *
 * Accessibility: labelled inputs, `role=alert` error surface, `role=status`
 * for the readiness summary, checkboxes grouped by fieldset/legend.
 */

import { useState } from "react";

import { createBattleWorkflow } from "@app/campaign/features/battle/battle-workflow";
import { createDefaultUseCases } from "@domain/campaign/kernel/default-usecases";
import type { CampaignDocument, IdString } from "@domain/campaign/index";
import { FakeKnowledgeReader } from "../campaign/fake-knowledge-reader";

export interface BattlePanelProps {
  document: CampaignDocument;
  /** Receives the document after every successful workflow step. */
  onDocument: (document: CampaignDocument) => void;
}

export function BattlePanel({ document, onDocument }: BattlePanelProps) {
  const knowledge = new FakeKnowledgeReader();
  const battle = createBattleWorkflow({
    knowledge,
    useCases: createDefaultUseCases(knowledge),
  });

  const [scenario, setScenario] = useState<string>(battle.scenarioOptions()[0]?.id ?? "");
  const [opponent, setOpponent] = useState("");
  const [result, setResult] = useState<"win" | "loss" | "draw">("win");
  const [gold, setGold] = useState("0");
  const [wyrdstone, setWyrdstone] = useState("0");
  const [xp, setXp] = useState("0");
  const [outOfAction, setOutOfAction] = useState<IdString[]>([]);
  const [error, setError] = useState<string | null>(null);

  const readiness = battle.readiness(document);
  const available = readiness.filter((row) => row.available);
  const pending = battle.pendingPostBattle(document);

  const record = async (): Promise<void> => {
    const result2 = await battle.record(document, {
      scenario: scenario as IdString,
      opponent,
      result,
      gold_delta: Number(gold) || 0,
      wyrdstone: Number(wyrdstone) || 0,
      xp_delta: Number(xp) || 0,
      out_of_action_ids: outOfAction,
    });
    if (!result2.ok) {
      setError(result2.message);
      return;
    }
    setError(null);
    setOutOfAction([]);
    onDocument(result2.document);
  };

  const resolveStep = async (): Promise<void> => {
    const result = battle.resolveStep(document, {});
    if (!result.ok) {
      setError(result.message);
      return;
    }
    setError(null);
    onDocument(result.document);
  };

  return (
    <section aria-label="Battle">
      <h2>Record a battle</h2>

      {error && (
        <output role="alert" style={{ color: "crimson", display: "block" }}>
          {error}{" "}
          <button type="button" onClick={() => setError(null)}>
            Dismiss
          </button>
        </output>
      )}

      {pending ? (
        <>
          <output role="status" style={{ display: "block" }}>
            Post-battle #{pending.battle_number}: step {pending.active_step} of 8.
          </output>
          <button type="button" onClick={() => void resolveStep()}>
            Resolve step {pending.active_step}
          </button>
        </>
      ) : (
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void record();
          }}
        >
          <label htmlFor="battle-scenario">Scenario</label>
          <select
            id="battle-scenario"
            value={scenario}
            onChange={(event) => setScenario(event.target.value)}
          >
            {battle.scenarioOptions().map((option) => (
              <option key={option.id} value={option.id}>
                {option.name}
              </option>
            ))}
          </select>

          <label htmlFor="battle-opponent">Opponent</label>
          <input
            id="battle-opponent"
            type="text"
            value={opponent}
            onChange={(event) => setOpponent(event.target.value)}
            required
          />

          <label htmlFor="battle-result">Result</label>
          <select
            id="battle-result"
            value={result}
            onChange={(event) => setResult(event.target.value as "win" | "loss" | "draw")}
          >
            <option value="win">Victory</option>
            <option value="loss">Defeat</option>
            <option value="draw">Draw</option>
          </select>

          <label htmlFor="battle-gold">Gold delta</label>
          <input
            id="battle-gold"
            type="number"
            min={0}
            value={gold}
            onChange={(event) => setGold(event.target.value)}
          />

          <label htmlFor="battle-wyrdstone">Wyrdstone shards</label>
          <input
            id="battle-wyrdstone"
            type="number"
            min={0}
            value={wyrdstone}
            onChange={(event) => setWyrdstone(event.target.value)}
          />

          <label htmlFor="battle-xp">Experience gained</label>
          <input
            id="battle-xp"
            type="number"
            min={0}
            value={xp}
            onChange={(event) => setXp(event.target.value)}
          />

          <fieldset>
            <legend>Out of action</legend>
            {readiness.map((row) => (
              <label key={row.warrior_id}>
                <input
                  type="checkbox"
                  disabled={!row.available}
                  checked={outOfAction.includes(row.warrior_id)}
                  onChange={(event) => {
                    setOutOfAction((current) =>
                      event.target.checked
                        ? [...current, row.warrior_id]
                        : current.filter((id) => id !== row.warrior_id),
                    );
                  }}
                />{" "}
                {row.name}
                {row.reason ? ` (${row.reason})` : ""}
              </label>
            ))}
            {available.length === 0 && <p>No warriors available.</p>}
          </fieldset>

          <button type="submit" disabled={available.length === 0 || opponent.trim().length === 0}>
            Record battle
          </button>
        </form>
      )}
    </section>
  );
}

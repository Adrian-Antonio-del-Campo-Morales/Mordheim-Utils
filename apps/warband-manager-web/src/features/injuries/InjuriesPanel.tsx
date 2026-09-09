/**
 * P6.5 (web-migration-parallel-plan.md §P6.5): injuries & recovery UI.
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
import { injuryOverview } from "@app/campaign/features/injuries/injuries-workflow";

interface InjuriesPanelProps {
  readonly document: CampaignDocument;
}

export function InjuriesPanel({ document }: InjuriesPanelProps) {
  const app = useCampaignApp();
  const [busy, setBusy] = useState(false);
  const overview = injuryOverview(document);

  const run = async (action: string, input: Record<string, unknown>) => {
    setBusy(true);
    // Rejections surface through the shell's shared error seam (app.error);
    // the document stays intact, so this component only blocks re-entry.
    await app.runAction(action, input);
    setBusy(false);
  };

  return (
    <section aria-label="Injuries">
      <h3>Injuries &amp; Recovery</h3>

      {app.error && (
        <output role="alert" style={{ color: "crimson", display: "block" }}>
          {app.error}
        </output>
      )}

      {overview.open_rolls.length > 0 && (
        <p>
          {overview.open_rolls.length} unresolved injury roll
          {overview.open_rolls.length === 1 ? "" : "s"} on the pending post-battle.
        </p>
      )}

      <table>
        <caption>Warband injury status</caption>
        <thead>
          <tr>
            <th scope="col">Warrior</th>
            <th scope="col">Condition</th>
            <th scope="col">Missing games</th>
            <th scope="col">Recovery</th>
            <th scope="col">Pending rolls</th>
          </tr>
        </thead>
        <tbody>
          {overview.warriors.map((row) => (
            <tr key={row.warrior_id} data-restricted={row.restricted || undefined}>
              <td>{row.name}</td>
              <td>
                {row.condition
                  ? `${row.condition}${row.condition_detail ? ` (${row.condition_detail})` : ""}`
                  : "—"}
              </td>
              <td>{row.games_to_miss > 0 ? `${row.games_to_miss} (${row.absence_reason ?? "Injury"})` : "0"}</td>
              <td>
                <button
                  type="button"
                  disabled={busy || row.games_to_miss === 0}
                  aria-label={`Recover ${row.name}`}
                  onClick={() => run("recoverWarrior", { warrior_id: row.warrior_id })}
                >
                  Serve 1 game
                </button>
              </td>
              <td>
                {row.pending_follow_ups.length === 0
                  ? "—"
                  : row.pending_follow_ups.map((followUp) => {
                      const id = String((followUp as { id?: unknown }).id ?? "");
                      return (
                        <button
                          key={id}
                          type="button"
                          disabled={busy}
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
                          Resolve
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

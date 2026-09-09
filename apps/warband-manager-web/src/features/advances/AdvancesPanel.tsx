/**
 * P6.6 (web-migration-parallel-plan.md §P6.6): experience & advances UI.
 *
 * Renders the per-warrior advance ledger (earned/taken/pending from the
 * application read model) and a choice picker for pending advances
 * (`stat:<KEY>` characteristic or a learned skill name). Actions dispatch
 * through the campaign app service (`applyAdvance`); rejections surface via
 * the shell's error seam, never thrown.
 *
 * The read model lives in the application feature; this file only exports
 * components (react-refresh).
 */
import { useState } from "react";

import { useCampaignApp } from "../campaign/useCampaignApp";
import type { CampaignDocument } from "../campaign/types";
import { advancesOverview } from "@app/campaign/features/advances/advances-workflow";

const STAT_KEYS = ["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld"] as const;

interface AdvancesPanelProps {
  readonly document: CampaignDocument;
}

export function AdvancesPanel({ document }: AdvancesPanelProps) {
  const app = useCampaignApp();
  const [busy, setBusy] = useState(false);
  const [customSkill, setCustomSkill] = useState("");
  const overview = advancesOverview(document);
  const pendingWarriors = overview.warriors.filter((w) => w.eligible);

  const apply = async (warriorId: string, choice: string) => {
    setBusy(true);
    await app.runAction("applyAdvance", { warrior_id: warriorId, table: "common", choice });
    setBusy(false);
  };

  return (
    <section aria-label="Advances">
      <h3>Advances</h3>
      {overview.total_pending === 0 ? (
        <p role="status">No pending advances.</p>
      ) : (
        <table>
          <caption>Pending advances ({overview.total_pending})</caption>
          <thead>
            <tr>
              <th scope="col">Warrior</th>
              <th scope="col">XP</th>
              <th scope="col">Pending</th>
              <th scope="col">Choose</th>
            </tr>
          </thead>
          <tbody>
            {pendingWarriors
              .filter((w) => w.pending > 0)
              .map((warrior) => (
                <tr key={warrior.warrior_id}>
                  <td>{warrior.warrior_name}</td>
                  <td>{warrior.experience}</td>
                  <td>{warrior.pending}</td>
                  <td>
                    <select
                      aria-label={`Advance choice for ${warrior.warrior_name}`}
                      defaultValue=""
                      disabled={busy}
                      onChange={(event) => {
                        const choice = event.target.value;
                        if (choice) {
                          void apply(warrior.warrior_id, choice);
                          event.target.value = "";
                        }
                      }}
                    >
                      <option value="" disabled>
                        Choose advance…
                      </option>
                      {STAT_KEYS.map((key) => (
                        <option key={key} value={`stat:${key}`}>
                          +1 {key}
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      )}

      <h4>Learn a new skill</h4>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          const name = customSkill.trim();
          if (name.length === 0 || pendingWarriors.length === 0) return;
          const firstPending = pendingWarriors.find((w) => w.pending > 0);
          if (firstPending) {
            void apply(firstPending.warrior_id, `skill:${name}`);
            setCustomSkill("");
          }
        }}
      >
        <label htmlFor="advance-skill">Skill name</label>
        <input
          id="advance-skill"
          value={customSkill}
          onChange={(event) => setCustomSkill(event.target.value)}
        />
        <button type="submit" disabled={busy || customSkill.trim().length === 0}>
          Learn (first pending warrior)
        </button>
      </form>
    </section>
  );
}
